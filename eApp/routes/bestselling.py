from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
import models

router = APIRouter(
    tags=['BestSelling']
)

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

@router.get('/bestSelling')
async def bestSelling(db: Session = Depends(get_db)):
    all_data = db.query(models.Product.id,models.Product.name,models.Product.product_image,models.Product.new_price,models.Product.percentage_discount,models.Product.offer_expiration_date,models.Product.product_details).order_by(func.random()).all()
    data_into_list = [{"id":id,"name":name,"image":image,"newPrice":new_price,"dis":discount,"date":date,"decription":details} for id,name,image,new_price,discount,date,details in all_data]
    return {"Categories" : data_into_list}
