from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sqlalchemy_inspect

from src.repository.users import UserRepository
from src.schemas import UserCreate, UserModel
from src.database.models import User
from src.database.redis import get_redis
from src.conf.config import settings


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate) -> User:
        user = await self.repository.create_user(body, avatar_url=None)
        await self.cache_user(user)
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.repository.get_user_by_id(user_id)
        if user:
            await self.cache_user(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        user = await self.repository.get_user_by_email(email)
        if user:
            await self.cache_user(user)
        return user

    async def get_cached_user_by_email(self, email: str) -> User | None:
        redis_client = await get_redis()
        cache_key = f"user:email:{email}"
        cached_user = await redis_client.get(cache_key)
        if not cached_user:
            return None
        user_data = UserModel.model_validate_json(cached_user)
        user = User(**user_data.model_dump())
        return user

    async def confirm_user_email(self, user: User) -> User:
        user = await self._ensure_user_managed(user)
        user = await self.repository.set_email_verified(user)
        await self.cache_user(user)
        return user

    async def update_avatar(self, user: User, avatar_url: str) -> User:
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_user_avatar(user, avatar_url)
        await self.cache_user(user)
        return user

    async def _ensure_user_managed(self, user: User) -> User:
        """Ensure user is managed by session. If not, merge it."""
        state = sqlalchemy_inspect(user)
        if not state.persistent:
            user = await self.repository.db.merge(user)
            await self.repository.db.refresh(user)
        return user

    async def update_user_password(self, user: User, new_hashed_password: str) -> User:
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_user_password(user, new_hashed_password)
        await self.invalidate_user_cache(user.email)
        return user

    async def update_reset_password_token(self, user: User, token: str | None) -> User:
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_reset_password_token(user, token)
        if token is not None:
            await self.invalidate_user_cache(user.email)
        return user

    async def update_multiple_user_fields(self, user: User, **fields) -> User:
        user = await self._ensure_user_managed(user)
        user = await self.repository.update_multiple_fields(user, **fields)
        await self.cache_user(user)
        return user

    async def cache_user(self, user: User) -> None:
        redis_client = await get_redis()
        cache_key = f"user:email:{user.email}"
        user_data = UserModel.model_validate(user).model_dump_json()
        await redis_client.set(
            cache_key, user_data, ex=settings.REDIS_CACHE_EXPIRE_SECONDS
        )

    async def invalidate_user_cache(self, email: str) -> None:
        redis_client = await get_redis()
        cache_key = f"user:email:{email}"
        await redis_client.delete(cache_key)
