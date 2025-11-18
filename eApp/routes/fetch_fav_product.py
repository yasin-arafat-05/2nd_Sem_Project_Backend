from eApp import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from eApp.database import get_db

router = APIRouter(
    tags=["show favourite product"]
)


@router.get('/get/fav/product')
async def get_favourite_product(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Product).where(models.Product.is_favourite.is_(True))
    )
    products = result.scalars().all()
    return {
        "User All Product": [{
            "id": product.id,
            "Product Name": product.name,
            "Category": product.category,
            "Original Price": float(product.original_price),
            "New Price": float(product.new_price),
            "Percentage Discount": product.percentage_discount,
            "Offer Expiration Date": product.offer_expiration_date,
            "Product Details": product.product_details,
            "Product Image": product.product_image,
            "Cart": product.add_to_cart,
            "Favourite": product.is_favourite,
        } for product in products]
    }