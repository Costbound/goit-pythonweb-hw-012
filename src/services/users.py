"""
User service layer.

This module provides business logic for user management operations including
user creation, retrieval, email verification, avatar updates, password management,
and Redis caching functionality.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sqlalchemy_inspect
from redis.asyncio import Redis

from src.repository.users import UserRepository
from src.schemas import UserCreate, UserModel
from src.database.models import User
from src.conf.config import settings


class UserService:
    """
    Service class for user management operations.

    Provides business logic for user CRUD operations, email verification,
    password management, and Redis caching. Acts as an intermediary between
    API endpoints and the user repository.

    :param db: Database session for repository operations.
    :type db: AsyncSession
    :param redis_client: Redis client for caching user data.
    :type redis_client: Redis
    """

    def __init__(self, db: AsyncSession, redis_client: Redis):
        """
        Initialize user service with database session and Redis client.

        :param db: Database session for repository operations.
        :type db: AsyncSession
        :param redis_client: Redis client for caching.
        :type redis_client: Redis
        """
        self.repository = UserRepository(db)
        self.redis_client = redis_client

    async def create_user(self, body: UserCreate) -> User:
        """
        Create a new user and cache the result.

        :param body: User creation data containing email and password.
        :type body: UserCreate
        :return: Newly created user object.
        :rtype: User
        """
        user = await self.repository.create_user(body, avatar_url=None)
        await self.cache_user(user)
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their ID and cache the result.

        :param user_id: User's unique identifier.
        :type user_id: int
        :return: User object if found, None otherwise.
        :rtype: User | None
        """
        user = await self.repository.get_user_by_id(user_id)
        if user:
            await self.cache_user(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address and cache the result.

        :param email: User's email address.
        :type email: str
        :return: User object if found, None otherwise.
        :rtype: User | None
        """
        user = await self.repository.get_user_by_email(email)
        if user:
            await self.cache_user(user)
        return user

    async def get_cached_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user from Redis cache by email address.

        Returns cached user data without querying the database.
        If user is not in cache, returns None.

        :param email: User's email address.
        :type email: str
        :return: User object from cache if found, None otherwise.
        :rtype: User | None
        """
        cache_key = f"user:email:{email}"
        cached_user = await self.redis_client.get(cache_key)
        if not cached_user:
            return None
        user_data = UserModel.model_validate_json(cached_user)
        user = User(**user_data.model_dump())
        return user

    async def confirm_user_email(self, user: User) -> User:
        """
        Mark user's email as verified and update cache.

        :param user: User object to verify.
        :type user: User
        :return: Updated user object with email_verified=True.
        :rtype: User
        """
        user = await self._ensure_user_managed(user)
        user = await self.repository.set_email_verified(user)
        await self.cache_user(user)
        return user

    async def update_avatar(self, user: User, avatar_url: str) -> User:
        """
        Update user's avatar URL and refresh cache.

        :param user: User object to update.
        :type user: User
        :param avatar_url: New avatar image URL.
        :type avatar_url: str
        :return: Updated user object with new avatar URL.
        :rtype: User
        """
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_user_avatar(user, avatar_url)
        await self.cache_user(user)
        return user

    async def _ensure_user_managed(self, user: User) -> User:
        """
        Ensure user is managed by the database session.

        If the user object is detached from the session, merges it back
        and refreshes the object state.

        :param user: User object to check and manage.
        :type user: User
        :return: Managed user object.
        :rtype: User
        """
        state = sqlalchemy_inspect(user)
        if not state.persistent:
            user = await self.repository.db.merge(user)
            await self.repository.db.refresh(user)
        return user

    async def update_user_password(self, user: User, new_hashed_password: str) -> User:
        """
        Update user's password hash and invalidate cache.

        :param user: User object to update.
        :type user: User
        :param new_hashed_password: New hashed password.
        :type new_hashed_password: str
        :return: Updated user object with new password hash.
        :rtype: User
        """
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_user_password(user, new_hashed_password)
        await self.invalidate_user_cache(user.email)
        return user

    async def update_reset_password_token(self, user: User, token: str | None) -> User:
        """
        Update user's password reset token and manage cache.

        Sets or clears the reset password token. Invalidates cache when
        a new token is set.

        :param user: User object to update.
        :type user: User
        :param token: Password reset token, or None to clear it.
        :type token: str | None
        :return: Updated user object.
        :rtype: User
        """
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_reset_password_token(user, token)
        if token is not None:
            await self.invalidate_user_cache(user.email)
        return user

    async def update_multiple_user_fields(self, user: User, **fields) -> User:
        """
        Update multiple user fields at once and refresh cache.

        :param user: User object to update.
        :type user: User
        :param fields: Keyword arguments of field names and values to update.
        :return: Updated user object.
        :rtype: User
        """
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_multiple_fields(user, **fields)
        await self.cache_user(user)
        return user

    async def cache_user(self, user: User) -> None:
        """
        Store user data in Redis cache.

        Serializes user object to JSON and stores it in Redis with
        an expiration time defined in settings.

        :param user: User object to cache.
        :type user: User
        :return: None
        """
        cache_key = f"user:email:{user.email}"
        user_data = UserModel.model_validate(user).model_dump_json()
        await self.redis_client.set(
            cache_key, user_data, ex=settings.REDIS_CACHE_EXPIRE_SECONDS
        )

    async def invalidate_user_cache(self, email: str) -> None:
        """
        Remove user data from Redis cache.

        Deletes cached user data by email key, forcing next retrieval
        to query the database.

        :param email: User's email address.
        :type email: str
        :return: None
        """
        cache_key = f"user:email:{email}"
        await self.redis_client.delete(cache_key)
