# eApp/services/product_service.py
from eApp import schemas,models
from eApp.database import get_db
from eApp.passHasing import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text,func,cast, Numeric, select 
from fastapi import HTTPException, APIRouter,Depends,status

async def fetch_nearby_products( db: AsyncSession, categories: list[str], user_lat: float,user_long: float,radius_km: float = 5.0) -> list[dict]:

    raw_distance = 6371 * func.acos(
        func.least(1.0, func.greatest(-1.0,
            func.cos(func.radians(user_lat)) * func.cos(func.radians(models.Business.lat)) *
            func.cos(func.radians(models.Business.longi) - func.radians(user_long)) +
            func.sin(func.radians(user_lat)) * func.sin(func.radians(models.Business.lat))
        ))
    )
    
    distance_km_expr = func.round(cast(raw_distance, Numeric), 2).label("distance_km")
    stmt = (
        select(
            models.Product.id,
            models.Product.name,
            models.Product.category,
            models.Product.original_price,
            models.Product.new_price,
            models.Product.product_image,
            models.Business.id.label("business_id"),
            models.Business.business_name,
            models.Business.city,
            models.Business.region,
            models.Business.owner.label("user_id"),  
            distance_km_expr
        )
        .join(models.Business, models.Product.business_id == models.Business.id)
        .where(
            models.Product.category.in_(categories),     # SQL-এর ANY(:categories) এর বদলে .in_()
            models.Business.lat.is_not(None),
            models.Business.longi.is_not(None),
            raw_distance <= radius_km             
        )
        .order_by(distance_km_expr.asc(), models.Product.original_price.asc())
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [
        {
            "product_id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": float(row["new_price"]),
            #"discount_price": float(row["discount_price"]) if row["discount_price"] else None,
            "shop": row["business_name"],
            "address": f"{row['city']}, {row['region']}", 
            "distance_km": float(row["distance_km"]),
            "image": row["product_image"],
        }
        for row in rows
    ]


# for llms 
def local_search_llm_context(db:AsyncSession,categories: list[str], user_lat: float,user_long: float,radius_km: float = 5.0):
    products = fetch_nearby_products(
        db,
        categories=categories,
        user_lat=user_lat,
        user_long=user_long,
        radius_km=radius_km
        )
    return products



router = APIRouter(tags=["Near by search"])
# for ui: 
@router.post('/local/search')
async def local_search_prod(intput_data : schemas.LocalSearch ,user: schemas.User = Depends(get_current_user),db:AsyncSession = Depends(get_db)):
    print(intput_data)
    print()
    if not user:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    near_by_prod  = await fetch_nearby_products(db,intput_data.categories,intput_data.lat,intput_data.long,intput_data.rad)
    return near_by_prod


