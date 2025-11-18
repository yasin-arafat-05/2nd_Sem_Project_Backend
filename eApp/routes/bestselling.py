from eApp import models
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from eApp.database import get_db

router = APIRouter(
    tags=['BestSelling']
)


@router.get('/bestSelling')
async def best_selling(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            models.Product.id,
            models.Product.name,
            models.Product.product_image,
            models.Product.new_price,
            models.Product.percentage_discount,
            models.Product.offer_expiration_date,
            models.Product.is_favourite,
            models.Product.add_to_cart,
            models.Product.product_details,
        )
        .order_by(func.random())
    )
    result = await db.execute(stmt)
    all_data = result.all()
    
    data_into_list = [{
        "id": id_,
        "name": name,
        "image": image,
        "newPrice": new_price,
        "dis": discount,
        "date": date,
        "favourite": is_favourite,
        "cart": add_to_cart,
        "decription": details
    } for id_, name, image, new_price, discount, date, is_favourite, add_to_cart, details in all_data]
    return {"Categories" : data_into_list}

