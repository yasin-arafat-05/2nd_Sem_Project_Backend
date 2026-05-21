from pydantic import BaseModel
from eApp import schemas, models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eApp.passHasing import get_current_user
from eApp.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter(tags=["upload profile"])


class UploadProfile(BaseModel):
    business_name : str 
    city : str 
    region : str 
    business_description : str
    lat : str 
    longi : str
    

@router.put("/update/profile")
async def upload_profile(
    update: UploadProfile,
    user: schemas.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(update)
    if user.is_verified==False:
        raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You need to Verify Your Account To Update Business Profile")
    try:
        result = await db.execute(select(models.Business).where(models.Business.owner==user.id))
        business_profile = result.scalar_one_or_none()
        if not business_profile:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="User is not Authenticate")
        
        business_profile.city = update.city
        business_profile.region = update.region
        business_profile.business_name = update.business_name
        business_profile.business_description = update.business_description
        business_profile.lat = float(update.lat)
        business_profile.longi = float(update.longi)
        await db.commit()
        return {"detail": "Profile Update Successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Profile update failed")
