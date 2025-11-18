from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eApp.database import get_db
from eApp.passHasing import get_current_user
from eApp import models

router = APIRouter(tags=["Chat History"])


@router.get("/chatHistory")
async def chat_history(user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user_id = int(user)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid user context")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user_record = result.scalar_one_or_none()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(models.Conversation)
            .where(models.Conversation.user_id == user_id)
            .order_by(models.Conversation.created_at.desc())
    )
    conversations = result.scalars().all()

    history = []
    for conv in conversations:
        result = await db.execute(
            select(models.MessageHistory)
                .where(models.MessageHistory.conversation_id == conv.id)
                .order_by(models.MessageHistory.created_at.asc())
        )
        messages = result.scalars().all()
        history.append({
            "conversation_id": conv.id,
            "thread_id": conv.thread_id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "last_updated": conv.last_updated.isoformat() if conv.last_updated else None,
            "messages": [
                {
                    "message_id": msg.id,
                    "sender_role": msg.sender_role,
                    "message": msg.message,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        })

    return history

