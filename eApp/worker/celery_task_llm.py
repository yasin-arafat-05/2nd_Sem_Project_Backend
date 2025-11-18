import json
import logging 
import nest_asyncio 
from uuid import uuid4
from eApp import models
from celery import Celery
from celery import shared_task
from eApp.config import CONFIG
from sqlalchemy import select, func 
from eApp.database import asyncSession
from eApp.redis_setup import redis_sync
from asgiref.sync import async_to_sync
from langchain_core.messages import AIMessage
from eApp.workflows.workflow import workflow
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)  

celery_app_llm = Celery(
    'ai_agent',
    broker=CONFIG.REDIS_DB_LLM_URL,
    backend=CONFIG.REDIS_DB_LLM_URL
)

celery_app_llm.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=360,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    task_default_queue='llm_tasks',
    task_queues={
        'llm_tasks': {
            'exchange': 'llm_tasks',
            'routing_key': 'llm_tasks',
        }
    },
    # Queue management
    task_soft_time_limit=600,  
    task_reject_on_worker_lost=True,
    worker_disable_rate_limits=True,
    # Priority queues for different user types
    task_routes={
        'app.worker.celery_task_llm.process_llm_request_task': {'queue': 'llm_tasks', 'priority': 5}
    }
)


# Async version of chunking_message
async def chunking_message(chunk):
    if isinstance(chunk, AIMessage):
        return chunk.content
    else:
        raise TypeError(
            f"Object of type: {type(chunk).__name__} is not correctly formatted for serialization"
        )

# Async processing function
async def process_llm_request_internal(user_question: str, checkpoint_id: str, user_id: int, channel_id: str):
    try:
        async with asyncSession() as db:
            # Check current checkpoint
            is_new_conversation = (checkpoint_id == "")
            user_checkpoint_id = str(checkpoint_id) if not is_new_conversation else str(uuid4())

            # 1.<--- Conversation title ---->
            conversation = None
            if is_new_conversation:
                conversation = models.Conversation(
                    user_id=user_id,
                    thread_id=user_checkpoint_id,
                    title=user_question[:50] + "...." if len(user_question) > 50 else user_question
                )
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
            else:
                result = await db.execute(
                    select(models.Conversation).where(
                        models.Conversation.thread_id == checkpoint_id
                    ).where(
                        models.Conversation.user_id == user_id
                    )
                )
                conversation = result.scalar_one_or_none()
                if not conversation:
                    redis_sync.publish(channel_id, json.dumps({"type": "error", "content": "Checkpoint not found"}))
                    return
                conversation.last_updated = func.now()
                db.add(conversation)
                await db.commit()


            # 2. Save User Message
            user_msg = models.MessageHistory(
                user_id=user_id,
                conversation_id=conversation.id,
                thread_id=conversation.thread_id,
                message=user_question,
                sender_role="human",
            )
            db.add(user_msg)
            await db.commit()
            logger.info(f"Saved user message for conversation {conversation.id}")

            # 3. Stream Events
            ai_content = ""
            config = {"configurable": {"thread_id": conversation.thread_id}}

            # Publish checkpoint if new
            if is_new_conversation:
                print("pulishing new checkpiont---> for user ")
                redis_sync.publish(channel_id, json.dumps({"type": "checkpoint", "checkpoint_id": user_checkpoint_id}))

            # Stream LangGraph events - This will work because it's inside async context
            string = CONFIG.DATABASE_URL_CELERY_TASK
            async with AsyncPostgresSaver.from_conn_string(string) as memory:
                graph = workflow.compile(checkpointer=memory)
                events =  graph.astream_events(
                    input={"user_question": user_question,"current_user_id":int(user_id)},
                    version="v2",
                    config=config
                )
                async for event in events:
                    event_type = event["event"]
                    if isinstance(event, dict) and event.get("type") == "function_error":
                        logger.error("Function call failed, payload was: %r", event.get("failed_generation"))
                        redis_sync.publish(channel_id, json.dumps({"type": "error", "content": "Function call failed"}))
                        await db.rollback()
                        return

                    # Chat Model Output
                    if event_type == "on_chat_model_stream":
                        chunk_content = await chunking_message(event["data"]["chunk"])
                        ai_content += chunk_content
                        safe_content = json.dumps(chunk_content)[1:-1]
                        redis_sync.publish(channel_id, json.dumps({"type": "content", "content": safe_content}))

                        # Delayed Event Stream
                    elif event_type == "on_chain_start":
                        node_name = event["name"]
                        if node_name == "Analyze_Requirements":
                            redis_sync.publish(channel_id, json.dumps({"type": "analyzing_requirements"}))
                        elif node_name == "Clarify_Requirements":
                            redis_sync.publish(channel_id, json.dumps({"type": "clarifying_requirements"}))
                        elif node_name == "Research_Content":
                            redis_sync.publish(channel_id, json.dumps({"type": "researching_content"}))
                        elif node_name == "Generate_Media":
                            redis_sync.publish(channel_id, json.dumps({"type": "generating_media"}))
                        elif node_name == "Create_Content":
                            redis_sync.publish(channel_id, json.dumps({"type": "creating_content"}))
                        elif node_name == "Quality_Check":
                            redis_sync.publish(channel_id, json.dumps({"type": "checking_quality"}))
                        elif node_name == "Post_Content":
                            redis_sync.publish(channel_id, json.dumps({"type": "posting_content"}))
                        elif "research" in node_name.lower():
                            redis_sync.publish(channel_id, json.dumps({"type": "searching_information"}))
                        elif "media" in node_name.lower():
                            redis_sync.publish(channel_id, json.dumps({"type": "generating_media_content"}))
                        elif "quality" in node_name.lower():
                            redis_sync.publish(channel_id, json.dumps({"type": "quality_check"}))
                        else:
                            redis_sync.publish(channel_id, json.dumps({"type": "processing", "node": node_name}))
                
            # Send the end event
            if ai_content:
                ai_msg = models.MessageHistory(
                    user_id=user_id,
                    conversation_id=conversation.id,
                    thread_id=conversation.thread_id,
                    message=ai_content,
                    sender_role="ai"
                )
                db.add(ai_msg)
                try:
                    await db.commit()
                    logger.info(f"Saved AI response for user_id {user_id}")
                except Exception as e:
                    await db.rollback()
                    logger.error(f"Failed to save AI message: {e}")
                    redis_sync.publish(channel_id, json.dumps({"type": "error", "content": "Failed to save response"}))
            else:
                logger.warning("No AI content generated")
                
            redis_sync.publish(channel_id, json.dumps({"type": "end"}))

    except Exception as e:
        logger.error(f"Error in Celery task: {e}")
        redis_sync.publish(channel_id, json.dumps({"type": "error", "content": str(e)}))


# Celery task
@celery_app_llm.task(bind=True, name="app.worker.celery_task_llm.process_llm_request_task")
def process_llm_request_task(self, user_question: str, checkpoint_id: str, user_id: int, channel_id: str):
    """Celery task that runs the async LLM processing"""
    try:
        import asyncio
        #<---For event loop close error---->
        nest_asyncio.apply()
        # (celery task->sync-->asyncio.run-->help to run-->async function from sync)
        return asyncio.run(process_llm_request_internal(user_question, checkpoint_id, user_id, channel_id))
        
    except Exception as e:
        print(f"error in celery task: {e} ")
        logger.error(f"Celery task error: {e}")
        redis_sync.publish(channel_id, json.dumps({"type": "error", "content": str(e)}))
        
# celery -A eApp.worker.celery_task_llm.celery_app_llm worker --loglevel=info --pool=solo 

