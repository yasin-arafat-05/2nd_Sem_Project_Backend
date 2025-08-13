
from eApp import schemas,models
from sqlalchemy.orm import Session
from fastapi import APIRouter,Depends
from eApp.database import SessionLocal
from eApp.passHasing import get_current_user

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
async def addToCart(id:int,db : Session = Depends(get_db)):
    product = db.query(models.Product).filter((models.Product.id==id)).first()
    if not product:
        return "product not exist."
    product.is_favourite = True
    db.add(product)
    db.commit()
    db.refresh(product)
    return "Successfully added to favourite list"