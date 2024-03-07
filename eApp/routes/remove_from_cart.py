
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from passHasing import get_current_user
from database import SessionLocal
import schemas,models

router = APIRouter(
    tags=["remove from  cart"]
)

# db utilites:

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       
       

@router.post('/remove/from/cart')
async def remove_from_cart(id:int,user : schemas.User = Depends(get_current_user),db : Session = Depends(get_db)):
    product = db.query(models.Product).filter((models.Product.business_id==user) & (models.Product.id==id)).first()
    if not product:
        return "This is not your product."
    product.add_to_cart = False
    db.add(product)
    db.commit()
    db.refresh(product)
    return "Successfully remove from cart list"
