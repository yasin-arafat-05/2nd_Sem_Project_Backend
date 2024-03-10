from fastapi import APIRouter,Depends,HTTPException,status
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from passHasing import verify_password
from datetime import timedelta,datetime
from jose import jwt
from typing import Annotated
from sqlalchemy.orm import Session
from dotenv import dotenv_values
import schemas,models


router = APIRouter(tags=['login'])


# Token generation endpoint/login endpoint
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    print(user)
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
def authenticate_user(username: str, password: str):
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=180)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,config_crediential['SECRET'], algorithm='HS256')
    return encoded_jwt
