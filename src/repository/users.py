from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    UPDATABLE_FIELDS = {
        "password_hash",
        "avatar_url",
        "email_verified",
        "reset_password_token",
    }

    def __init__(self, session: AsyncSession):
        self.db = session
        self._valid_fields = {col.key for col in inspect(User).mapper.column_attrs}

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

    async def update_user_password(self, user: User, new_hashed_password: str) -> User:
        user.password_hash = new_hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_reset_password_token(self, user: User, token: str | None) -> User:
        user.reset_password_token = token
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # Use this method to update multiple fields atomically and with one commit
    async def update_multiple_fields(self, user: User, **fields) -> User:
        """
        Update multiple user fields atomically.
        Uses whitelist of allowed fields for security.

        Args:
            user: User object to update
            **fields: Field names and values to update

        Returns:
            Updated user object

        Raises:
            ValueError: If invalid or protected field is provided
        """
        invalid_fields = set(fields.keys()) - self._valid_fields
        if invalid_fields:
            raise ValueError(
                f"Fields do not exist in User model: {', '.join(invalid_fields)}"
            )

        protected_fields = set(fields.keys()) - self.UPDATABLE_FIELDS
        if protected_fields:
            raise ValueError(
                f"Cannot update protected fields: {', '.join(protected_fields)}. "
                f"Allowed fields: {', '.join(self.UPDATABLE_FIELDS)}"
            )

        for key, value in fields.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user
