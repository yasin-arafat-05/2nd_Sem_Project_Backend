from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eApp.database import get_db
from eApp.passHasing import verify_password
from datetime import timedelta, datetime
from jose import jwt
from eApp.config import CONFIG
from dotenv import dotenv_values
from eApp import schemas, models

router = APIRouter(tags=['login'])


# Token generation endpoint/login endpoint
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"id": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


#-------------------------------Necessary function------------------------------------


#from .env file get EMAIL,PASSWORD, SECRET KEY
config_crediential = dotenv_values('eApp/.env')


#authenticate user
async def authenticate_user(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(models.User).where(models.User.email == username))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=180)
    to_encode.update({"exp": expire})
    print(config_crediential)
    encoded_jwt = jwt.encode(to_encode,CONFIG.SECRET_KEY, algorithm=CONFIG.ALGORITHM)
    return encoded_jwt


