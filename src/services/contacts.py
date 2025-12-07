"""
Contact service layer.

This module provides business logic for contact management operations,
acting as an intermediary between API endpoints and the data repository layer.
"""

from typing import List
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, ContactUpdate


class ContactService:
    """
    Service class for contact management operations.

    Provides business logic for CRUD operations on contacts and handles
    birthday-related queries. Delegates data access to ContactRepository.

    :param db: Database session for repository operations.
    :type db: AsyncSession
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize contact service with database session.

        :param db: Database session for repository operations.
        :type db: AsyncSession
        """
        self.contact_repository = ContactRepository(db)

    async def get_contacts(
        self, user: User, page: int, show: int, filter: dict | None = None
    ):
        """
        Retrieve paginated list of contacts for a user.

        Supports optional filtering by first name, last name, or email.

        :param user: User whose contacts to retrieve.
        :type user: User
        :param page: Page number (1-indexed).
        :type page: int
        :param show: Number of contacts per page.
        :type show: int
        :param filter: Optional filter dictionary with first_name, last_name, or email keys.
        :type filter: dict | None
        :return: List of contacts matching criteria.
        :rtype: List[Contact]
        """
        return await self.contact_repository.get_contacts(
            user, skip=show * (page - 1), limit=show, filter=filter
        )

    async def get_contact(self, user: User, contact_id: int):
        """
        Retrieve a specific contact by ID.

        :param user: User who owns the contact.
        :type user: User
        :param contact_id: ID of the contact to retrieve.
        :type contact_id: int
        :return: Contact object if found, None otherwise.
        :rtype: Contact | None
        """
        return await self.contact_repository.get_contact(user, contact_id)

    async def create_contact(self, user: User, contact: ContactModel):
        """
        Create a new contact for a user.

        :param user: User who will own the contact.
        :type user: User
        :param contact: Contact data to create.
        :type contact: ContactModel
        :return: Newly created contact object.
        :rtype: Contact
        """
        return await self.contact_repository.create_contact(user, contact)

    async def update_contact(self, user: User, contact_id: int, contact: ContactUpdate):
        """
        Update an existing contact.

        :param user: User who owns the contact.
        :type user: User
        :param contact_id: ID of the contact to update.
        :type contact_id: int
        :param contact: Updated contact data (partial updates allowed).
        :type contact: ContactUpdate
        :return: Updated contact object if found, None otherwise.
        :rtype: Contact | None
        """
        return await self.contact_repository.update_contact(user, contact_id, contact)

    async def delete_contact(self, user: User, contact_id: int):
        """
        Delete a contact by ID.

        :param user: User who owns the contact.
        :type user: User
        :param contact_id: ID of the contact to delete.
        :type contact_id: int
        :return: Deleted contact object if found, None otherwise.
        :rtype: Contact | None
        """
        return await self.contact_repository.delete_contact(user, contact_id)

    async def get_upcoming_birthdays(
        self, user: User, days_ahead: int = 7
    ) -> List[Contact]:
        """
        Get contacts with birthdays in the specified time period.

        Returns contacts whose birthdays fall within the next N days,
        where N is specified by days_ahead parameter.

        :param user: User whose contacts to search.
        :type user: User
        :param days_ahead: Number of days ahead to search for birthdays (default: 7).
        :type days_ahead: int
        :return: List of contacts with upcoming birthdays.
        :rtype: List[Contact]
        """
        today = date.today()
        return await self.contact_repository.get_contacts_with_birthday_in_period(
            user, today, today + timedelta(days=days_ahead)
        )
