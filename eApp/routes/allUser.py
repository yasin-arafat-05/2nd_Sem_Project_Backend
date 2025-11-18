from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eApp import models
from eApp.database import get_db

app = APIRouter(tags=['all user'])

@app.get('/all/user')
async def get_all_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return users