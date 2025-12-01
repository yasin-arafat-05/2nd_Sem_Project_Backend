from fastapi import Depends
from eApp.config import CONFIG
from typing import AsyncGenerator, Annotated
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


connection_string = CONFIG.DATABASE_URL
print(f"{connection_string}")


#============Why connection_args??=================
#1st connection establishement takes times
#Sometimes can be occur TimeError:
#To solve keep the connection alive 
connection_args = {
    "server_settings": {
        "jit": "off", #Optimization: Disable JIT for simple queries
        "tcp_keepalives_idle": "60",  # Send keepalive after 60s
        "tcp_keepalives_interval": "10",  #Retry every 10s
        "tcp_keepalives_count": "3", ## Fail fast after 3 retries
        "statement_timeout": "30000"  # 30 seconds query timeout
    }
}

async_engine = create_async_engine(
    url=connection_string,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True,
    echo=False,
    connect_args=connection_args,
    # Additional performance settings
    echo_pool=False,  # Set to True for debugging pool issues
    hide_parameters=True  # Hide parameters in logs for security
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
