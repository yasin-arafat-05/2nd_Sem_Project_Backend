import secrets # python-inbuild to generate hex token -> use to store our image files
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from eApp import schemas,models,passHasing
from eApp.database import get_db
from fastapi import APIRouter,File,UploadFile,Depends,HTTPException,status

router = APIRouter(tags=['Image-Upload'])

#---------------------------------------product Picture Uplod---------------------------------------

'''
Mount is going to tell the fastapi that in this directory will save static files
likes images.
'''
router.mount("/static", StaticFiles(directory="eApp/static"), name="static")

@router.post("/product/picture/{id}")
async def create_product_picture(
    id:int,
    file: UploadFile = File(...),
    user : schemas.User = Depends(passHasing.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Business).where(models.Business.owner == user))
    user_business = result.scalar_one_or_none()
    if not user_business:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authorized To Perform This Task."
        )

    result = await db.execute(select(models.Product).where(models.Product.business_id == user_business.owner))
    product_valid = result.scalar_one_or_none()
    if not product_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This is not your product."
        )

    result = await db.execute(select(models.Product).where(models.Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    PATH = 'eApp/static/images'
    filename = file.filename
    extention = filename.split('.')[1]

    if extention not in ['png','jpg','jpeg']:
        return {"status" : 'File extention should in .png .jpg and .jpeg'}
    token_name = secrets.token_hex(10)+'.'+extention
    generatePath = f"{PATH}/{token_name}"
    file_content = await file.read()

    # wb -> write in binary 
    with open(generatePath,"wb") as fille:
        fille.write(file_content)

    owner = user_business
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authenticated User",
            headers={"WWW-Authenticate": "Bearer"}
        )
    product.product_image = token_name
    await db.commit()
    file_url = f"static/images/{token_name}"
    return FileResponse(path=file_url)


# router.mount("/static", StaticFiles(directory="static"), name="static")

# @router.post("product/picture/{id}")
# async def create_upload_file(id:int,file: UploadFile = File(...),user : schemas.User = Depends(passHasing.get_current_user),db: Session=Depends(database.db_get)):
#     PATH = 'static/images'
#     filename = file.filename
#     extention = filename.split('.')[1]

#     if extention not in ['png','jpg','jpeg']:
#         return {"status" : 'File extention should in .png .jpg and .jpeg'}
#     token_name = secrets.token_hex(10)+'.'+extention
#     generatePath = f"{PATH}/{token_name}"
#     file_content = await file.read()

#     # wb -> write in binary 
#     with open(generatePath,"wb") as fille:
#         fille.write(file_content)
        
    
#     # Pillow -> to reduce file resolution size etc.
#     # img = Image.open(generatePath)
#     # img = img.resize(size=(200,200))
#     # img.save(generatePath)
#     # await file.close()

#     #user:
#     owner = db.query(models.Business).filter(models.Business.owner==user).first()
#     if not owner:
#        raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Not Authenticated User",
#         headers={"WWW-Authenticate": "Bearer"}
#     )
#     owner.logo = token_name
#     db.commit()
#     file_url = f"static/images/{token_name}"
#     print(token_name)
#     return token_name

# #--------------------------get the image-------------------------
# from fastapi.responses import FileResponse

# @router.get("/images/{filename}")
# async def get_uploaded_image(filename: str):
#     # Assuming your images are stored in a directory named "static/images"
#     image_path = f"static/images/{filename}"
#     return FileResponse(image_path)








