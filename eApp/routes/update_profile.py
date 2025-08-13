from pydantic import BaseModel
from eApp import schemas,models
from eApp.database import db_get
from sqlalchemy.orm import Session
from eApp.passHasing import get_current_user
from fastapi import APIRouter,Depends,HTTPException,status


router = APIRouter(tags=["upload profile"])


# for pydandic model for request data: 

class uploadProfile(BaseModel):
    business_name : str 
    city : str 
    region : str 
    business_description : str
    

@router.put("/update/profile")
async def Upload_profile(update: uploadProfile ,user : schemas.User =Depends(get_current_user),db : Session = Depends(db_get)):
    try:
        business_profile = db.query(models.Business).filter(models.Business.owner==user).first()
        if not business_profile:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="User is not Authenticate")
        
        business_profile.city = update.city
        business_profile.region = update.region
        business_profile.business_name = update.business_name
        business_profile.business_description = update.business_description
        db.commit()
        return "Profile Upadate Successfully"
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Profile update failed")
    