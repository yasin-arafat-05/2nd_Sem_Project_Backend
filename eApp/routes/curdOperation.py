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
    if current_user and current_user.is_verified:
        product_data['business_id'] = current_user.id
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
        return {"status": "First verify your account."}

#-----------------------------------Get All the Product information-------------------------------

@router.get("/get/product")
async def get_all_product(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Product))
    all_product = result.scalars().all()
    return all_product

#------------------------------Get A the Product information---------------------------------
@router.get("/get/single/product/{id}")
async def get_a_single_product(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product_with_business = result.scalar_one_or_none()

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
    result = await db.execute(select(models.Product).where(models.Product.business_id == user))
    product_valid = result.scalar_one_or_none()
    if not product_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="This is not your product.")
    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product = result.scalar_one_or_none()
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

