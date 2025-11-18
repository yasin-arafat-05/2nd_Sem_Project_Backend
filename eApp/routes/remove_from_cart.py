
from eApp import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from eApp.database import get_db

router = APIRouter(
    tags=["remove from  cart"]
)


@router.post('/remove/from/cart')
async def remove_from_cart(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not exist."
        )
    product.add_to_cart = False
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return {"detail": "Successfully removed from cart list"}
