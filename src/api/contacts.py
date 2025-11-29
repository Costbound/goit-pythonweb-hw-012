from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from src.database.db import get_db
from src.database.models import User
from src.schemas import (
    ContactResponse,
    ContactModel,
    ContactShortResponse,
    ContactUpdate,
)
from src.services.contacts import ContactService
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=List[ContactShortResponse])
async def get_contacts(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    show: int = Query(10, ge=1),
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts(
        user,
        page,
        show,
        filter={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        },
    )
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    contact = await contact_service.get_contact(user, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactModel,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    try:
        return await contact_service.create_contact(user, contact)
    except IntegrityError as e:
        if "uq_contact_email_user" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with this email already exists",
            )
        elif "uq_contact_phone_user" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with this phone number already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create contact"
        )


@router.patch("{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    updated_contact = await contact_service.update_contact(user, contact_id, contact)
    if not updated_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return updated_contact


@router.delete("{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    deleted_contact = await contact_service.delete_contact(user, contact_id)
    if deleted_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return deleted_contact


@router.get("/birthdays/upcoming", response_model=List[ContactShortResponse])
async def get_upcoming_birthdays(
    days_ahead: int = 7,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    contacts = await contact_service.get_upcoming_birthdays(user, days_ahead)
    return contacts
