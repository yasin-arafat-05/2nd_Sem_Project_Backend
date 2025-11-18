import jwt 
from eApp import models
from jose import JWTError
from fastapi import Depends
from sqlalchemy import select
from eApp.config import CONFIG
from pwdlib import PasswordHash
from eApp.database import get_db
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer



'''
schemes: This parameter specifies the list of password hashing schemes to be used. 
In this case, it's set to ["bcrypt"], indicating that only the bcrypt hashing algorithm 
should be used.


deprecated: This parameter controls the behavior for deprecated hashing algorithms. 
In this case, it's set to "auto", which means that the CryptContext instance will 
automatically manage the deprecation of old hashing schemes

'''
password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

'''
Check-> When we send mail (While Registation Endpoint) we create a token by the help of token_data[username,id] and 
SECRET Key and Algorithms by the help of jwt.decode() method we decode the token and in 
payload variable we get -> username,id
'''
async def very_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token,CONFIG.SECRET_KEY, algorithms=CONFIG.ALGORITHM)
        print(f"Decoded payload: {payload}")
        user_id = payload.get("id")
        if user_id:
            result = await db.execute(select(models.User).where(models.User.id == user_id))
            user = result.scalar_one_or_none()
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
async def get_current_user(token: str = Depends(oauth2_scheme),db: AsyncSession = Depends(get_db)):
    print("token: in get current user: "+ token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = await very_token(token,db)
        output = {
                        "id": user.id,
                        "username":user.username,
                        "email": user.email,
                        "trail_remain": user.free_count,
                        "paid": user.paid_status,
                        "role":user.role,
                        
                        }
        print(output)
        
        return user
    except JWTError:
        raise credentials_exception
    return id




