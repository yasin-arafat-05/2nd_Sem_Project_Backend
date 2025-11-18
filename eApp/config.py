from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import dotenv_values
from pydantic import SecretStr

class Settings(BaseSettings):
    # LLM Configuration
    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    
    # FastAPI Configuration
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 200
    
    # Database Configuration
    DATABASE_URL: str = ""  # Async URL (postgresql+asyncpg)
    DATABASE_URL_CELERY_TASK: str = ""  # Sync URL (postgresql)
    DB_ROLE_NAME: str 
    DB_PASSWORD: str 
    DB_HOST: str 
    DATABASE: str 
    DB_PORT: int 
    
    # Redis Configuration
    REDIS_HOST:str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB_CELERY: int = 0  # For payment celery tasks
    REDIS_DB_LLM: int = 1  # For LLM celery tasks
    REDIS_DB_CACHE: int = 2  # For cache
    REDIS_DB_LLM_URL: str = ""
    REDIS_URL: str = ""  # For payment celery (db 0)
    REDIS_CACHE_URL: str = ""  # For cache (db 2)
    
    
    #Mail Configuration:
    MAIL_USERNAME: str 
    MAIL_PASSWORD: SecretStr 
    MAIL_FROM: str 
    MAIL_PORT: int 
    MAIL_SERVER: str 
    MAIL_FROM_NAME : str 
    
    model_config = SettingsConfigDict(env_file="eApp/.env", extra="ignore")

CONFIG = Settings()

CONFIG.DATABASE_URL = (
    f"postgresql+asyncpg://{CONFIG.DB_ROLE_NAME}:{CONFIG.DB_PASSWORD}"
    f"@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/{CONFIG.DATABASE}"
)
CONFIG.DATABASE_URL_CELERY_TASK = (
    f"postgresql://{CONFIG.DB_ROLE_NAME}:{CONFIG.DB_PASSWORD}@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/{CONFIG.DATABASE}"
)
CONFIG.REDIS_URL = f"redis://{CONFIG.REDIS_HOST}:{CONFIG.REDIS_PORT}/{CONFIG.REDIS_DB_CELERY}"
CONFIG.REDIS_CACHE_URL = f"redis://{CONFIG.REDIS_HOST}:{CONFIG.REDIS_PORT}/{CONFIG.REDIS_DB_CACHE}"
CONFIG.REDIS_DB_LLM_URL = f"redis://{CONFIG.REDIS_HOST}:{CONFIG.REDIS_PORT}/{CONFIG.REDIS_DB_LLM}"

