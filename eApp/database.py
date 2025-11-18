from fastapi import Depends
from eApp.config import CONFIG
from typing import AsyncGenerator, Annotated
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


connection_string = CONFIG.DATABASE_URL
print(f"{connection_string}")

async_engine = create_async_engine(
    url=connection_string,
     # Connection Pool Settings
    pool_size=20,      # Maximum connections in pool
    max_overflow=10,   # Temporary connections beyond pool_size
    pool_timeout=30,   # Seconds to wait for a connection
    pool_recycle=1800, # Recycle connections after 30 minutes
    pool_pre_ping=True,# Check connection health before use
    echo=False # Set to False in production
)


asyncSession = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


#create db utility:
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with asyncSession() as session:
        try: 
            yield session
        finally:
            await session.close()
        

#create db dependency
db_dependency = Annotated[AsyncSession,Depends(get_db)]
