# eApp/services/product_service.py
from sqlalchemy import text
from eApp import schemas,models
from eApp.database import get_db
from eApp.passHasing import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, APIRouter,Depends,status

async def fetch_nearby_products(
    db: AsyncSession,
    categories: list[str],
    user_lat: float,
    user_long: float,
    radius_km: float = 5.0
) -> list[dict]:
    
    query = text("""
        SELECT 
            p.id,
            p.product_name,
            p.category,
            p.price,
            p.discount_price,
            p.product_image,
            b.id as business_id,
            b.business_name,
            b.address,
            ROUND(CAST(
                6371 * acos(
                    LEAST(1.0, GREATEST(-1.0,
                        cos(radians(:lat)) * cos(radians(b.latitude)) *
                        cos(radians(b.longitude) - radians(:lng)) +
                        sin(radians(:lat)) * sin(radians(b.latitude))
                    ))
                ) AS NUMERIC
            ), 2) AS distance_km
        FROM products p
        JOIN business b ON p.business_id = b.id
        WHERE 
            p.category = ANY(:categories)
            AND b.latitude IS NOT NULL
            AND b.longitude IS NOT NULL
            AND (
                6371 * acos(
                    LEAST(1.0, GREATEST(-1.0,
                        cos(radians(:lat)) * cos(radians(b.latitude)) *
                        cos(radians(b.longitude) - radians(:lng)) +
                        sin(radians(:lat)) * sin(radians(b.latitude))
                    ))
                )
            ) <= :radius
        ORDER BY distance_km ASC, p.price ASC
        LIMIT 20
    """)
    
    result = await db.execute(query, {
        "lat": user_lat,
        "lng": user_long,
        "categories": categories,
        "radius": radius_km
    })
    rows = result.mappings().all()

    return [
        {
            "product_id": row["id"],
            "name": row["product_name"],
            "category": row["category"],
            "price": float(row["price"]),
            "discount_price": float(row["discount_price"]) if row["discount_price"] else None,
            "shop": row["business_name"],
            "address": row["address"],
            "distance_km": float(row["distance_km"]),
            "image": row["product_image"],
        }
        for row in rows
    ]


# for llms 
def local_search_llm_convtext(products: list[dict]) -> list[str]:
    return [
        f"{p['name']} | {p['shop']} | ৳{p['discount_price'] or p['price']} | {p['distance_km']}km"
        for p in products
    ]



router = APIRouter(tags=["Near by search"])
# for ui: 
@router.get('/local/search')
async def local_search_prod(intput_data : schemas.LocalSearch ,user: schemas.User = Depends(get_current_user),db:AsyncSession = Depends(get_db)):
    print(intput_data)
    if not user:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    near_by_prod  = await fetch_nearby_products(db,intput_data.categories,intput_data.lat,intput_data.long,intput_data.rad)
    return near_by_prod







