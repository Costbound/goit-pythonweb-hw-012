"""
Database models and ORM definitions.

This module defines the SQLAlchemy ORM models for the application, including
User and Contact entities with their relationships and constraints.
"""

from enum import Enum
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, String, Date, Text, DateTime, Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Provides the declarative base for SQLAlchemy model definitions.
    All models should inherit from this class.
    """

    pass


class UserRole(str, Enum):
    """
    User role enumeration.

    Defines the available roles for users in the system.

    :cvar ADMIN: Administrator role with elevated privileges.
    :cvar USER: Regular user role with standard access.
    """

    ADMIN = "ADMIN"
    USER = "USER"


class Contact(Base):
    """
    Contact model representing a user's contact entry.

    Each contact belongs to a user and contains personal information
    including name, email, phone, birthday, and additional notes.

    :param id: Primary key identifier.
    :type id: int
    :param first_name: Contact's first name.
    :type first_name: str
    :param last_name: Contact's last name.
    :type last_name: str
    :param email: Contact's email address (unique per user).
    :type email: str
    :param phone: Contact's phone number (unique per user).
    :type phone: str
    :param birthday: Contact's date of birth (optional).
    :type birthday: date | None
    :param additional_info: Additional notes about the contact (optional).
    :type additional_info: str | None
    :param created_at: Timestamp when the contact was created.
    :type created_at: datetime
    :param updated_at: Timestamp when the contact was last updated.
    :type updated_at: datetime
    :param user_id: Foreign key referencing the owner user.
    :type user_id: int
    :param user: Relationship to the User model.
    :type user: User
    """

    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("email", "user_id", name="uq_contact_email_user"),
        UniqueConstraint("phone", "user_id", name="uq_contact_phone_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    additional_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_contacts_user_id_users"),
        nullable=False,
    )

    user = relationship("User", backref="contacts")


class User(Base):
    """
    User model representing an authenticated user.

    Contains user authentication information, profile data, and
    relationships to their contacts. Supports role-based access control.

    :param id: Primary key identifier.
    :type id: int
    :param email: User's email address (unique).
    :type email: str
    :param password_hash: Hashed password for authentication.
    :type password_hash: str
    :param created_at: Timestamp when the user account was created.
    :type created_at: datetime
    :param avatar_url: URL to user's avatar image (optional).
    :type avatar_url: str | None
    :param refresh_token: JWT refresh token for session management (optional).
    :type refresh_token: str | None
    :param email_verified: Flag indicating if email is verified.
    :type email_verified: bool
    :param reset_password_token: Token for password reset functionality (optional).
    :type reset_password_token: str | None
    :param role: User's role (ADMIN or USER).
    :type role: UserRole
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    reset_password_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
