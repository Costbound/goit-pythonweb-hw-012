from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

import phonenumbers
from phonenumbers import NumberParseException


def validate_phone_number(phone: str) -> str:
    try:
        parsed = phonenumbers.parse(phone, None)

        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        raise ValueError("Invalid phone number format")


def validate_birthday(birthday: Optional[date]) -> Optional[date]:
    if birthday and birthday > date.today():
        raise ValueError("Birthday cannot be in the future")
    return birthday


class ContactModel(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: Optional[date]) -> Optional[date]:
        return validate_birthday(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone_number(v)


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: Optional[date]) -> Optional[date]:
        return validate_birthday(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone_number(v) if v is not None else v


class ContactResponse(ContactModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ContactShortResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    id: int
    email: EmailStr
    avatar_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
