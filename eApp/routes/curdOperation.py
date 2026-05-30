import uuid
from eApp import models, schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eApp.database import get_db
from eApp.passHasing import get_current_user
from fastapi import APIRouter, Depends, HTTPException,status

router = APIRouter(tags=["CRUD->Create,Read,Update,Delete"])

# ------------------------------------------- Add New Product ------------------------------
@router.post("/upload/product")
async def add_new_product(product: schemas.UploadProduct,user: schemas.User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    product_data = product.model_dump(exclude_unset=True)
    
    result = await db.execute(select(models.User).where(models.User.id == user.id))
    current_user = result.scalar_one_or_none()
    
    if not current_user or not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="First verify your account.")
    
    
    business_result = await db.execute(
        select(models.Business).where(models.Business.owner == current_user.id)
    )
    current_business = business_result.scalar_one_or_none()
    
    if not current_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found for this user.")
    
    if current_user and current_user.is_verified:
        product_data['business_id'] = current_business.id
        new_product = models.Product(**product_data)
        new_product.percentage_discount = ((new_product.original_price - new_product.new_price) / new_product.original_price) * 100
        
        # Generate unique chatbot_product_id for LLM integration
        new_product.chatbot_product_id = f"PROD-{uuid.uuid4().hex[:12].upper()}"
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return {
            "message": "Product Uploaded Successfully.",
            "product_id": new_product.id,
            "chatbot_product_id": new_product.chatbot_product_id
        }
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="First verify your account.")

#-----------------------------------Get All the Product information-------------------------------

@router.get("/get/product")
async def get_all_product(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Product))
    all_product = result.scalars().all()
    return all_product

#------------------------------Get A the Product information---------------------------------
async def single_product_info_for_llms(db: AsyncSession,id):
    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product_with_business = result.scalar_one_or_none()
    if product_with_business:
        return {
            "Product Information": {
                "id": product_with_business.id,
                "product_name": product_with_business.name,
                "product_details" : product_with_business.product_details,
                "original_price" : product_with_business.original_price,
                "new_price" : product_with_business.new_price,
                "percentage_discount" : product_with_business.percentage_discount,
                "offer_expiration_date" : product_with_business.offer_expiration_date,
                "product_image" :  product_with_business.product_image
            },

        }
    else:
        raise HTTPException(status_code=404, detail="Product not found")
    

@router.get("/get/single/product/{id}")
async def get_a_single_product(id: int, db: AsyncSession = Depends(get_db)):
    product_with_business = await single_product_info_for_llms(db,id)
    info = product_with_business["Product Information"]
    return {
            "Product Information": {
                "id": info.id,
                "name": info.name,
            }
        }
        

#--------------------------------------Delete A the Product --------------------------
@router.delete("/delete/product/{id}")
async def delete_product(id: int, user: schemas.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        # Query for the specific product owned by the user
        result = await db.execute(
            select(models.Product).where(
                models.Product.id == id,
                models.Product.business_id == user.id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # Or 401 if you prefer unauthorized
                detail="Product not found or not owned by you"
            )
        
        await db.delete(product)
        await db.commit()
        return {"message": "Product deleted successfully"}
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete product")
    
#--------------------------------------Update A the Product --------------------------
@router.put("/update/product/{id}")
async def update_product(id: int, update: schemas.UpdatedProduct, db: AsyncSession = Depends(get_db), user: schemas.User = Depends(get_current_user)):
    print("user is verified!")
    result = await db.execute(select(models.Product).where(models.Product.business_id == user.id))
    product_valid = result.scalars().first()
    if not product_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="This is not your product.")
    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product = result.scalars().first()
    if product:
        product.name = update.name
        product.category = update.category
        product.original_price = update.original_price
        product.new_price = update.new_price
        product.product_details = update.product_details
        product.offer_expiration_date = update.offer_expiration_date
        product.percentage_discount = ((product.original_price - product.new_price) / product.original_price) * 100
        await db.commit()
        return {"message": "Product Updated Successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

