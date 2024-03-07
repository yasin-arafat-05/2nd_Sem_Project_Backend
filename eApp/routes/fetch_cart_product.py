from fastapi import APIRouter,Depends
from passHasing import get_current_user
from sqlalchemy.orm import Session
from database import SessionLocal
import models,schemas

router = APIRouter(
    tags=["show cart product"]
)


# db utilites: 
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       



@router.get('/get/cart/product')
async def getCartProduct(user : schemas.Product = Depends(get_current_user), db : Session = Depends(get_db)):
    product = db.query(models.Product).filter((models.Product.business_id==user) & (models.Product.add_to_cart)).all()
    return {
        "User All Product": [{
            "id" : product.id,
            "Product Name": product.name,
            "Category": product.category,
            "Original Price": float(product.original_price),
            "New Price": float(product.new_price),
            "Percentage Discount": product.percentage_discount,
            "Offer Expiration Date": product.offer_expiration_date,
            "Product Details": product.product_details,
            "Product Image": product.product_image,
        } for product in product] 
    }