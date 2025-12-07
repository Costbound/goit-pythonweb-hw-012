"""
Redis connection and client management.

This module provides Redis client singleton for managing Redis connections
with connection pooling and proper lifecycle management.
"""

import redis.asyncio as aioredis
from src.conf.config import settings


class RedisClient:
    """
    Redis client singleton for connection pooling.

    Implements a singleton pattern to ensure only one Redis connection
    is maintained throughout the application lifecycle.

    :cvar _instance: Singleton instance of Redis client.
    :type _instance: aioredis.Redis | None
    """

    _instance: aioredis.Redis | None = None

    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        """
        Get or create Redis client instance.

        Returns the existing Redis client or creates a new one if it doesn't exist.
        Uses connection pooling for efficient resource management.

        :return: Redis client instance.
        :rtype: aioredis.Redis
        """
        if cls._instance is None:
            cls._instance = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._instance

    @classmethod
    async def close(cls):
        """
        Close Redis connection.

        Properly closes the Redis connection and resets the singleton instance.
        Should be called during application shutdown.

        :return: None
        """
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


# Helper function to get Redis client
async def get_redis() -> aioredis.Redis:
    """
    Get Redis client instance.

    Dependency function to retrieve the Redis client for use in
    FastAPI route handlers and other async contexts.

    :return: Redis client instance.
    :rtype: aioredis.Redis
    """
    return await RedisClient.get_client()
