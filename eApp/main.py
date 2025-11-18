from eApp import models
from eApp import lifespan
from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import AsyncSession
from eApp.database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, status, HTTPException, Request, Query,Depends
from eApp.passHasing import get_password_hash, very_token,get_current_user
from eApp.routes import curdOperation, login,imageUpload,profile,singup,productImageUpload,categories,bestselling,allUser,update_profile
from eApp.routes import fetch_cart_product, add_to_cart,remove_from_cart,add_to_favourite,remove_from_favourite
from eApp.routes import fetch_fav_product, social_media, sse, chatHistory

#jinja2Templates -> For showing html in verification.
template = Jinja2Templates(directory="eApp/templates")

#from .env file get EMAIL,PASSWORD, SECRET KEY
config_crediential = dotenv_values('.env')

#Instance of Fastapi
app = FastAPI(lifespan=lifespan.lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



#_________________________________ VERIFICATION ENDPOINT _________________________________

@app.get('/verification')
async def email_verification(request: Request, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    user = await very_token(token,db)
    if user and not user.is_verified:
        user.is_verified = True
        await db.commit()
        return template.TemplateResponse("verification.html", {"request": request, "USER_NAME": user.username})
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token or token expired",
        headers={"WWW-Authenticate": "Bearer"}
    )

#______________________________ Sign UP ENDPOINT _____________________________
app.include_router(singup.router)

#______________________________ LOGIN ENDPOINT ________________________________
app.include_router(login.router)

#________________ Profile -> Information of login user ________________________
app.include_router(profile.router)

#______________ API Router For Uplod Profile Image ____________________________
app.include_router(imageUpload.router)

app.include_router(productImageUpload.router)

#______________ API Router For Uplod Product ____________________________
app.include_router(curdOperation.router)

app.include_router(categories.router)

app.include_router(bestselling.router)

app.include_router(allUser.app)

app.include_router(update_profile.router)

app.include_router(fetch_cart_product.router)

app.include_router(add_to_cart.router)

app.include_router(remove_from_cart.router)

app.include_router(add_to_favourite.router)

app.include_router(remove_from_favourite.router)

app.include_router(fetch_fav_product.router)

# ==================== Social Media Integration Routes ====================
app.include_router(social_media.router)
app.include_router(sse.router)
app.include_router(chatHistory.router)

#
#tmux new -s worker
#crl+b then d 
#Run separately for production:
# Worker: concurrency-1 would be best i think.
#celery -A eApp.worker.celery_task_payment.celery_app_payment worker --loglevel=info --concurrency=1
# Beat
#tmux new -s beat
#celery -A eApp.worker.celery_task_payment.celery_app_payment beat --loglevel=info
#"""
#
#
#tmux new -s chatbot
#celery -A eApp.worker.celery_task_llm.celery_app_llm worker --loglevel=info --pool=solo 
#

# see all tmux:
# tmux ls 
# tmux kill-session -t celery
# cnt + b, d -> in detach mood
# tmux attach -t logs
# 13.60.245.240
