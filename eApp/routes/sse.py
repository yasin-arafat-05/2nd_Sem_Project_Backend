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

ACTIVE_KEY = "active_chat_users"
MAX_CONCURRENT = 2


@router.post("/chat")
async def chat_stream(input_data: InputMessage, request: Request, user = Depends(get_current_user), db = Depends(get_db)):
    if not input_data.message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    user_message = input_data.message
    checkpoint_id = input_data.checkpoint_id
    user_id = user.id
    free_trial = user.free_count
    paid_ = user.paid_status
    
    #print(f"User: {user}, Input: {input_data}")
    
    if free_trial > 3 and not paid_:
        raise HTTPException(status_code=402, detail="Payment required")

    # Generate unique channel ID
    channel_id = f"chat_{user_id}_{str(uuid4())}"

    # <-------------real active user count----------->
    active_count = int(await redis_async.get(ACTIVE_KEY) or 0)
    is_queued = active_count>=MAX_CONCURRENT
    #increase count:
    await redis_async.incr(ACTIVE_KEY)


    # <------- Call the Celery task id for fetch api-key------------->
    task = process_llm_request_task.apply_async(
        args=(user_message, checkpoint_id, user_id, channel_id)
    )


    # ==========Dubugging printing the total task ==========
    # total task length:
    print("*"*10)
    print("*"*10)
    print(active_count,MAX_CONCURRENT)
    print("*"*10)
    print("*"*10)

    # <-------- SSE streaming with Redis Pub/Sub------------------->
    async def event_generator():
        pubsub = redis_async.pubsub()
        await pubsub.subscribe(channel_id)

        # Send initial queue status
        if is_queued:
            yield f"data: {json.dumps({'type': 'queue_status', 'position': active_count, 'message': f'You are #{MAX_CONCURRENT} in queue. Please wait...\n'})}\n\n"

        try:
            async for msg in pubsub.listen():

                # if user get out from the app then terminate:
                if await request.is_disconnected():
                    task.revoke(terminate=True)
                    break 

                if msg["type"] == "message":
                    data = json.loads(msg["data"])
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("type") in ["end", "error"]:
                        break
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Streaming failed'})}\n\n"
        finally:
            # decremnt user:
            await redis_async.decr(ACTIVE_KEY)
            try:
                await pubsub.unsubscribe(channel_id)
            except :
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

