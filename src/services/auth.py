from datetime import datetime, timedelta, UTC
from typing import Literal

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.models import User
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")


def create_jwt_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
) -> str:
    to_encode = data.copy()
    now = datetime.now(tz=UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        access_token = create_jwt_token(data, expires_delta, "access")
    else:
        access_token = create_jwt_token(
            data,
            timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            "access",
        )
    return access_token


async def create_refresh_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        refresh_token = create_jwt_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_jwt_token(
            data,
            timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS),
            "refresh",
        )
    return refresh_token


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    print("get_current_user: ", id(db))
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        token_type = payload.get("token_type")
        if email is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await UserService(db).get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user


async def verify_refresh_token(token: str, db: AsyncSession) -> User | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None or payload.get("token_type") != "refresh":
            return None
        user = await UserService(db).get_user_by_email(email)
        return user
    except JWTError:
        return None


def create_eamil_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        seconds=settings.VERIFICATION_TOKEN_EXPIRE_SECONDS
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid token",
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise invalid_token_exception
        return email
    except JWTError:
        raise invalid_token_exception
