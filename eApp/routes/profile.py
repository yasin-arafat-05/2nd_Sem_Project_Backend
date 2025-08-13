from eApp import models,schemas
from sqlalchemy.orm import Session
from fastapi import APIRouter,Depends
from eApp.database import SessionLocal
from eApp.passHasing import get_current_user

router = APIRouter(
    tags=['Profile']
)


#db dependency
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()


#------------------------------------ User login information ----------------------------------------
       

@router.post("/user/me")
async def user_login(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user = db.query(models.User).filter(models.User.id == user).first()
    business = db.query(models.Business).filter(models.Business.owner==current_user.id).first()
    product_all =  db.query(models.Product).filter(models.Product.business_id==business.owner).all()
    return {
        "Current User Information": {
            "User Name": current_user.username,
            "User Email": current_user.email,
            "User id": current_user.id
        },
        "Business Information": {
            "Business Name": business.business_name,
            "Business Image": business.logo,
            "Business Description" : business.business_description,
            "City" : business.city,
            "region" : business.region
        },
        "User All Product": [{
            "id" : product.id,
            "Product Name": product.name,
            "Category": product.category,
            "Original Price": float(product.original_price),
            "New Price": float(product.new_price),
            "Percentage Discount": product.percentage_discount,
            "Offer Expiration Date": product.offer_expiration_date,
            "Product Details": product.product_details,
            "Product Image": product.product_image,
        } for product in product_all] 
    }

