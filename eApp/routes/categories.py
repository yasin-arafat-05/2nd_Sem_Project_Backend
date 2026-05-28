from eApp import models
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from eApp.database import get_db

router = APIRouter(tags=["Categories"])

async def fetch_categories_from_db(db: AsyncSession)->list:
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
    return category_info


# sperate beacue of langgrph needs categorics and 
# langgraph does not call the async funtion cause it's 
# depends on fastapi cyles.
@router.get('/Categories')
async def get_categories(db: AsyncSession = Depends(get_db)):
    return {
        "Categories": await fetch_categories_from_db(db)
    }
