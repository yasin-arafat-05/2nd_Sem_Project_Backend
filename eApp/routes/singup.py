from eApp import models,schemas
from sqlalchemy import select
from eApp.database import db_dependency
from eApp.passHasing import get_password_hash
from fastapi import status,APIRouter,HTTPException
from eApp.email_verification import EmailSchema,send_email


router = APIRouter(tags=['SignUP'])

#_________________________________ REGISTRATION ENDPOINT _________________________________

@router.post('/registration', status_code=status.HTTP_201_CREATED)
async def user_registration(user: schemas.User, db: db_dependency):
    user_data = user.model_dump(exclude_unset=True)
    user_data["password"] = get_password_hash(user_data["password"])
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    fnd = result.scalar_one_or_none()
    if fnd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email already exists.")
    try:
        new_user = models.User(**user_data)
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)

        email_schema = EmailSchema(email=[new_user.email])
        await send_email(email_schema, new_user)

        new_business = models.Business(
            business_name=f"{user_data['username']}'s Business",
            owner=new_user.id
        )
        db.add(new_business)
        await db.commit()
        await db.refresh(new_business)

    except Exception as e:
        await db.rollback()
        print(f"error while signup: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    return {"detail":"User Created Successfully. Please Check Your Email To Verify."}
