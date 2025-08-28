from fastapi import Depends
from typing import Generator
from src.core.redis_client import get_redis_client, RedisClient

def get_redis() -> Generator[RedisClient, None, None]:
    """
    FastAPI dependency for Redis client.
    
    This dependency provides a Redis client instance to FastAPI endpoints.
    The client is automatically managed and will be properly closed after use.
    
    Yields:
        RedisClient: Redis client instance
        
    Example:
        @app.get("/cache/{key}")
        def get_cached_data(key: str, redis: RedisClient = Depends(get_redis)):
            return redis.get(key)
    """
    redis_client = get_redis_client()
    try:
        yield redis_client
    finally:
        # Note: We don't close the client here as it's a global instance
        # The client will be closed when the application shuts down
        pass
