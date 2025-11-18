import json
import logging
from uuid import uuid4
from eApp import models
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Request

from eApp.schemas import InputMessage
from eApp.database import asyncSession
from eApp.redis_setup import redis_async
from eApp.passHasing import get_current_user
from eApp.worker.celery_task_llm import process_llm_request_task,celery_app_llm


logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with asyncSession() as session:
        yield session

router = APIRouter(tags=["chatbot"])

@router.post("/chat")
async def chat_stream(input_data: InputMessage, request: Request, user = Depends(get_current_user), db = Depends(get_db)):
    if not input_data.message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    message = input_data.message
    checkpoint_id = input_data.checkpoint_id
    user_id = user.id
    free_trial = user.free_count
    paid_ = user.paid_status
    
    #print(f"User: {user}, Input: {input_data}")
    
    if free_trial > 3 and not paid_:
        raise HTTPException(status_code=402, detail="Payment required")

    # Generate unique channel ID
    channel_id = f"chat_{user_id}_{str(uuid4())}"

    # Check queue status before starting:is queue is full then w8 other user:
    inspect = celery_app_llm.control.inspect()
    active_tasks = inspect.active()
    reserved_tasks = inspect.reserved()
    
    # Count total tasks in queue
    total_tasks = 0
    if active_tasks:
        for worker_tasks in active_tasks.values():
            total_tasks += len(worker_tasks)
    if reserved_tasks:
        for worker_tasks in reserved_tasks.values():
            total_tasks += len(worker_tasks)
    
    # <------- Call the Celery task id for fetch api-key------------->
    task = process_llm_request_task.apply_async(
        args=(message, checkpoint_id, user_id, channel_id)
    )
    

    # <-------- SSE streaming with Redis Pub/Sub------------------->
    async def event_generator():
        pubsub = redis_async.pubsub()
        await pubsub.subscribe(channel_id)

        # Send initial queue status
        if total_tasks > 0:
            yield f"data: {json.dumps({'type': 'queue_status', 'position': total_tasks, 'message': f'You are #{total_tasks} in queue. Please wait...'})}\n\n"

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    if data.get("type") in ["end", "error"]:
                        break
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Streaming failed'})}\n\n"
        finally:
            try:
                await pubsub.unsubscribe(channel_id)
            except:
                pass

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no' # for nginx
        }
    )

