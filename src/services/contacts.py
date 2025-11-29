from typing import List
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, ContactUpdate


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repository = ContactRepository(db)

    async def get_contacts(
        self, user: User, page: int, show: int, filter: dict | None = None
    ):
        return await self.contact_repository.get_contacts(
            user, skip=show * (page - 1), limit=show, filter=filter
        )

    async def get_contact(self, user: User, contact_id: int):
        return await self.contact_repository.get_contact(user, contact_id)

    async def create_contact(self, user: User, contact: ContactModel):
        return await self.contact_repository.create_contact(user, contact)

    async def update_contact(self, user: User, contact_id: int, contact: ContactUpdate):
        return await self.contact_repository.update_contact(user, contact_id, contact)

    async def delete_contact(self, user: User, contact_id: int):
        return await self.contact_repository.delete_contact(user, contact_id)

    async def get_upcoming_birthdays(
        self, user: User, days_ahead: int = 7
    ) -> List[Contact]:
        today = date.today()
        return await self.contact_repository.get_contacts_with_birthday_in_period(
            user, today, today + timedelta(days=days_ahead)
        )
