from fastapi import APIRouter,Depends
from database import SessionLocal
from sqlalchemy.orm import Session
import models
router = APIRouter(tags=["Categories"])

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

@router.get('/Categorie')
async def Categories(db: Session = Depends(get_db)):
    unique_categories = db.query(models.Product.category,models.Product.product_image).distinct().all()
    
   # -------------------- convert the categories into list ------------
    category_info = [{"category":category , "image": image} for category,image in unique_categories]
    
    return{
        "Categories": category_info
    }
