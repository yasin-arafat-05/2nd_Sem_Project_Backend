
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from passHasing import get_current_user
from database import SessionLocal
import schemas,models

router = APIRouter(
    tags=["add to favourite list"]
)

# db utilites:

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       
       

@router.post('/add/to/favourite')
async def addToCart(id:int,user : schemas.User = Depends(get_current_user),db : Session = Depends(get_db)):
    product = db.query(models.Product).filter((models.Product.id==id)).first()
    if not product:
        return "product not exist."
    product.is_favourite = True
    db.add(product)
    db.commit()
    db.refresh(product)
    return "Successfully added to favourite list"