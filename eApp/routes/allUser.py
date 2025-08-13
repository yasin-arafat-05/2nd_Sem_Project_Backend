from fastapi import APIRouter
from eApp import database,models,schemas

app = APIRouter(tags=['all user'])

@app.get('/all/user')
async def get_all_user(db:database.db_dependency):
    user = db.query(models.User).all()
    return user