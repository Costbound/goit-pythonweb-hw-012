from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, body: UserCreate, avatar_url: str | None = None
    ) -> User:
        new_user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            password_hash=body.password,
            avatar_url=avatar_url,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def set_email_verified(self, user: User) -> User:
        user.email_verified = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_avatar(self, user: User, avatar_url: str) -> User:
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user
