from eApp import models
from sqlalchemy import func
from sqlalchemy.orm import Session
from eApp.database import SessionLocal
from fastapi import APIRouter,Depends

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
    all_data = db.query(models.Product.id,
                        models.Product.name,
                        models.Product.product_image,
                        models.Product.new_price,
                        models.Product.percentage_discount,
                        models.Product.offer_expiration_date,
                        models.Product.is_favourite,
                        models.Product.add_to_cart,
                        models.Product.product_details).order_by(func.random()).all()
    
    data_into_list = [{"id":id,
                       "name":name,
                       "image":image,
                       "newPrice":new_price,
                       "dis":discount,
                       "date":date,
                       "favourite":is_favourite,
                       "cart":add_to_cart,
                       "decription":details} for id,name,image,new_price,discount,date,is_favourite,add_to_cart,details in all_data]
    return {"Categories" : data_into_list}

