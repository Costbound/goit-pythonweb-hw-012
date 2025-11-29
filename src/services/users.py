from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.users import UserRepository
from src.schemas import UserCreate
from src.database.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate) -> User:
        return await self.repository.create_user(body, avatar_url=None)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repository.get_user_by_email(email)

    async def confirm_user_email(self, user: User) -> User:
        return await self.repository.set_email_verified(user)

    async def update_avatar(self, user: User, avatar_url: str) -> User:
        return await self.repository.update_user_avatar(user, avatar_url)
