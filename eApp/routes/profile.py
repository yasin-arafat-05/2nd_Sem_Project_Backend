from eApp.config import CONFIG
from eApp import models, schemas
from sqlalchemy import select
from hashids import Hashids
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from eApp.database import get_db
from eApp.passHasing import get_current_user

router = APIRouter(
    tags=['Profile']    
)

SECRET_SALT = CONFIG.SECRET_KEY
PREFIX = "Galacti_"
hashids = Hashids(salt=SECRET_SALT, min_length=8)

def encrypt_product_id(product_id: int) -> str:
    hashed_str = hashids.encode(product_id)
    return f"{PREFIX}{hashed_str}"

def decrypt_product_id(token_str: str) -> int:
    if not token_str.startswith(PREFIX):
        raise ValueError("Invalid Token Format! Must start with 'Galacti_'.")
    #remove the prefix-part
    hashed_part = token_str.replace(PREFIX, "")
    decoded = hashids.decode(hashed_part)
    if not decoded:
        raise ValueError("Invalid Product Token!")
    return decoded[0]


@router.post("/user/me")
async def user_login(user: schemas.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user.id))
    current_user = result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(models.Business).where(models.Business.owner == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    result = await db.execute(select(models.Product).where(models.Product.business_id == business.id))
    product_all = result.scalars().all()
    # print(business.lat)
    # print(business.longi)
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
            "region" : business.region,
            "lat": business.lat,
            "long":business.longi
        },
        "User All Product": [{
            "id" : product.id,
            "chatbot_product_id": encrypt_product_id(product.id),
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

