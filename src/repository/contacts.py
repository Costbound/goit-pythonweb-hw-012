from typing import List
from datetime import date

from sqlalchemy import Integer, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate


class ContactRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_contacts(
        self, user: User, skip: int, limit: int, filter: dict | None = None
    ) -> List[Contact]:
        stmt = select(Contact).filter_by(user_id=user.id)

        if filter:
            conditions = []
            if filter.get("first_name"):
                conditions.append(Contact.first_name.ilike(f"%{filter['first_name']}%"))
            if filter.get("last_name"):
                conditions.append(Contact.last_name.ilike(f"%{filter['last_name']}%"))
            if filter.get("email"):
                conditions.append(Contact.email == filter["email"])

            if conditions:
                stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit)

        contacts = await self.db.execute(stmt)
        result = list(contacts.scalars().all())
        return result

    async def get_contact(self, user: User, contact_id: int) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, user: User, body: ContactModel) -> Contact:
        new_contact = Contact(**body.model_dump(exclude_unset=True), user_id=user.id)
        self.db.add(new_contact)
        await self.db.commit()
        await self.db.refresh(new_contact)
        return new_contact

    async def update_contact(
        self, user: User, contact_id: int, body: ContactUpdate
    ) -> Contact | None:
        contact = await self.get_contact(user, contact_id)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            self.db.add(contact)
            await self.db.commit()
            await self.db.refresh(contact)
            return contact
        return contact

    async def delete_contact(self, user: User, contact_id: int) -> Contact | None:
        contact = await self.get_contact(user, contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
            return contact
        return contact

    async def get_contacts_with_birthday_in_period(
        self, user: User, start_date: date, end_date: date
    ) -> List[Contact]:
        """Get contacts who will have a birthday between two dates"""

        stmt = select(Contact).where(
            Contact.user_id == user.id,
            Contact.birthday.isnot(None),
            cast(func.extract("year", func.age(start_date, Contact.birthday)), Integer)
            != cast(
                func.extract("year", func.age(end_date, Contact.birthday)), Integer
            ),
        )

        contacts = await self.db.execute(stmt)
        return list(contacts.scalars().all())
