from eApp.passHasing import get_password_hash, very_token,get_current_user
from fastapi import FastAPI, status, HTTPException, Request, Query,Depends
from fastapi.middleware.cors import CORSMiddleware
from eApp.database import engine,SessionLocal
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import dotenv_values
from eApp import models
from eApp.routes import curdOperation, login,imageUpload,profile,singup,productImageUpload,categories,bestselling,allUser,update_profile
from eApp.routes import fetch_cart_product, add_to_cart,remove_from_cart,add_to_favourite,remove_from_favourite
from eApp.routes import fetch_fav_product

#jinja2Templates -> For showing html in verification.
template = Jinja2Templates(directory="eApp/templates")

#from .env file get EMAIL,PASSWORD, SECRET KEY
config_crediential = dotenv_values('.env')

#Instance of Fastapi
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#_________________________________ VERIFICATION ENDPOINT _________________________________

@app.get('/verification')
async def email_verification(request: Request, token: str = Query(...), db : Session=Depends(get_db)):
    user = await very_token(token,db)
    
    if user and not user.is_verified:
        user.is_verified = True
        db.commit()
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

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app",host="127.0.0.1:8000",reload=True,port=8000)
