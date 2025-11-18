import redis
import redis.asyncio as aioredis
from eApp.config import CONFIG

# Redis client for Celery Task / streaming (sync)
redis_sync = redis.Redis(
    host=CONFIG.REDIS_HOST,
    port=CONFIG.REDIS_PORT,
    password=CONFIG.REDIS_PASSWORD or None,
    db=CONFIG.REDIS_DB_LLM,
    decode_responses=True
)

# Redis client for async SSE streaming
redis_async = aioredis.from_url(
    CONFIG.REDIS_DB_LLM_URL,
    password=CONFIG.REDIS_PASSWORD or None,
    decode_responses=True,
    encoding="utf-8"
)

