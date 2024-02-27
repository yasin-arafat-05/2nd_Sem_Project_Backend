from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from database import SessionLocal
from passHasing import get_current_user
import models, schemas

router = APIRouter(tags=["CRUD->Create,Read,Update,Delete"])

# db dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------- Add New Product ------------------------------
@router.post("/upload/product")
async def add_new_product(
    product: schemas.UploadProduct,
    user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_data = product.dict(exclude_unset=True)
    to_upload_discount : schemas.Product
    # Retrieve the current user from the database
    current_user = db.query(models.User).filter(models.User.id == user).first()
    # Check if the user has a business
    if current_user.is_verified:
        # If the user has a business, associate the product with that business
        product_data['business_id'] = current_user.id
        new_product = models.Product(**product_data)
        new_product.percentage_discount = ((new_product.original_price - new_product.new_price) / new_product.original_price) * 100
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return "Product Uploaded Successfully."
    else:
        return {"status": "First verify your account."}

#-----------------------------------Get All the Product information-------------------------------

@router.get("/get/product")
async def get_all_product(db: Session = Depends(get_db)):
    all_product = db.query(models.Product).all()
    return all_product

#------------------------------Get A the Product information---------------------------------
@router.get("/get/single/product/{id}")
async def get_a_single_product(id: int, db: Session = Depends(get_db)):
    product_with_business = db.query(models.Product).filter(models.Product.id == id).first()

    if product_with_business:
        return {
            "Product Information": {
                "id": product_with_business.id,
                "name": product_with_business.name,
            },

        }
    else:
        raise HTTPException(status_code=404, detail="Product not found")

#--------------------------------------Delete A the Product --------------------------
@router.delete("/delete/product/{id}")
async def delete_product(product_id: int,user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)): 
    product_valid = db.query(models.Product).filter(models.Product.business_id==user).first()
    print(product_id)
    if not product_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="This is not your product.")
    try:
        product =  db.query(models.Product).filter(models.Product.id==product_id).first()
        db.delete(product)
        db.commit()
        return {"message": "Product deleted successfully"}
    except Exception as e:
        print(e)

#--------------------------------------Update A the Product --------------------------
@router.put("/update/product/{id}")
async def update_product(id: int, update: schemas.UpdatedProduct, db: Session = Depends(get_db), user: schemas.User = Depends(get_current_user)):
    product_valid = db.query(models.Product).filter(models.Product.business_id == user).first()
    if not product_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="This is not your product.")
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product:
        product.name = update.name
        product.category = update.category
        product.original_price = update.original_price
        product.new_price = update.new_price
        product.product_details = update.product_details
        product.offer_expiration_date = update.offer_expiration_date
        product.percentage_discount = ((product.original_price - product.new_price) / product.original_price) * 100
        db.commit()
        return {"message": "Product Updated Successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

