from eApp import models
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from eApp.database import SessionLocal

router = APIRouter(tags=["Categories"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/Categories')
async def get_categories(db: Session = Depends(get_db)):
    # Get distinct categories and their associated images
    subquery = (
        db.query(models.Product.category, func.min(models.Product.product_image).label("product_image"))
        .group_by(models.Product.category)
        .subquery()
    )

    unique_categories = db.query(subquery).all()

    # Convert the categories into a list of dictionaries
    category_info = [{"category": category, "image": image} for category, image in unique_categories]

    return {
        "Categories": category_info
    }
