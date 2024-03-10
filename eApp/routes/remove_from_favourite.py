
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from passHasing import get_current_user
from database import SessionLocal
import schemas,models

router = APIRouter(
    tags=["Remove From Favourite"]
)

# db utilites:

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       
       

@router.post('/remove/from/favourite')
async def addToCart(id:int,db : Session = Depends(get_db)):
    product = db.query(models.Product).filter((models.Product.id==id)).first()
    if not product:
        return "Product not exist."
    product.is_favourite = False
    db.add(product)
    db.commit()
    db.refresh(product)
    return "Successfully removed from favourite list"