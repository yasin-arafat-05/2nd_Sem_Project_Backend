from fastapi import status,APIRouter,HTTPException
from email_verification import EmailSchema,send_email
from passHasing import get_password_hash
from database import db_dependency
import models,schemas


router = APIRouter(tags=['SignUP'])

#_________________________________ REGISTRATION ENDPOINT _________________________________

@router.post('/registration', status_code=status.HTTP_201_CREATED)
async def user_registration(user: schemas.User, db: db_dependency):
    # exclude_unset=True if user don't give any value of any filed then create new user 
    # By the default given when we create schema in database in models.py files.

    user_data = user.dict(exclude_unset=True)
    user_data["password"] = get_password_hash(user_data["password"])
    fnd = db.query(models.User).filter(models.User.email == user.email).first()
    if fnd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email already exists.")
    try:
        new_user = models.User(**user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        email_schema = EmailSchema(email=[new_user.email])
        await send_email(email_schema, new_user)

        new_business = models.Business(
            business_name=f"{user_data['username']}'s Business",
            owner=new_user.id
        )
        db.add(new_business)
        db.commit()
        db.refresh(new_business)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {"detail":"User Created Successfully. Please Check Your Email To Verify."}
