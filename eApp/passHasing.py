from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from dotenv import dotenv_values
from database import db_get
from typing import Annotated
from fastapi import Depends
from jose import JWTError,jwt 
import models


#create db dependency
db  = Annotated[Session,Depends(db_get)]


#from .env file get EMAIL,PASSWORD, SECRET KEY
config_crediential = dotenv_values('eApp/.env')

'''
schemes: This parameter specifies the list of password hashing schemes to be used. 
In this case, it's set to ["bcrypt"], indicating that only the bcrypt hashing algorithm 
should be used.


deprecated: This parameter controls the behavior for deprecated hashing algorithms. 
In this case, it's set to "auto", which means that the CryptContext instance will 
automatically manage the deprecation of old hashing schemes

'''
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

'''
Check-> When we send mail (While Registation Endpoint) we create a token by the help of token_data[username,id] and 
SECRET Key and Algorithms by the help of jwt.decode() method we decode the token and in 
payload variable we get -> username,id
'''
async def very_token(token: str,db:Session):
    try:
        payload = jwt.decode(token, config_crediential['SECRET'], algorithms=['HS256'])
        print(f"Decoded payload: {payload}")
        user_id = payload.get("id")
        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                return user
            else:
                print(f"User with id {user_id} not found in the database.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: User not found.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Missing user ID.",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    
#oauth2 scheme:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


#get the current user: when a user authorized:
async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("token: in get current user: "+ token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,config_crediential['SECRET'], algorithms=['HS256'])
        print(payload)
        id: str = payload.get("id")
        if id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return id




