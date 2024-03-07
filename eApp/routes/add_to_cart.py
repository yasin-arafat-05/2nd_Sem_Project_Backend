
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from passHasing import get_current_user
from database import SessionLocal
import schemas,models

router = APIRouter(
    tags=["add to cart"]
)

# db utilites:

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       
       

@router.post('/add/to/cart')
async def addToCart(id:int,user : schemas.User = Depends(get_current_user),db : Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.business_id==user & models.Product.id==id).first()
    if not product:
        return "This is not your product."
    product.add_to_cart = True
    return "Successfully added to cart list"