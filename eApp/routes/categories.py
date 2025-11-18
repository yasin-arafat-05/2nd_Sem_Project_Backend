from eApp import models
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from eApp.database import get_db

router = APIRouter(tags=["Categories"])


@router.get('/Categories')
async def get_categories(db: AsyncSession = Depends(get_db)):
    subquery = (
        select(
            models.Product.category,
            func.min(models.Product.product_image).label("product_image"),
        )
        .group_by(models.Product.category)
        .subquery()
    )

    result = await db.execute(select(subquery.c.category, subquery.c.product_image))
    unique_categories = result.all()

    category_info = [{"category": category, "image": image} for category, image in unique_categories]

    return {
        "Categories": category_info
    }
