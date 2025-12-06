import redis.asyncio as aioredis
from src.conf.config import settings


class RedisClient:
    """Redis client singleton for connection pooling."""

    _instance: aioredis.Redis | None = None

    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        """Get or create Redis client instance."""
        if cls._instance is None:
            cls._instance = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._instance

    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


# Helper function to get Redis client
async def get_redis() -> aioredis.Redis:
    """Get Redis client instance."""
    return await RedisClient.get_client()
