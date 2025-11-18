from eApp import models, schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from eApp.database import get_db
from eApp.passHasing import get_current_user

router = APIRouter(
    tags=['Profile']
)


@router.post("/user/me")
async def user_login(user: schemas.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user))
    current_user = result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(models.Business).where(models.Business.owner == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    result = await db.execute(select(models.Product).where(models.Product.business_id == business.owner))
    product_all = result.scalars().all()

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
            "chatbot_product_id": product.chatbot_product_id,  # ID for LLM/chatbot integration
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

