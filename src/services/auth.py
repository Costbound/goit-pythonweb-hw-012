"""
Authentication and authorization services.

This module provides authentication services including password hashing,
JWT token creation and validation, user authentication, and role-based
access control using OAuth2 bearer tokens.
"""

from datetime import datetime, timedelta, UTC
from typing import Literal

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from redis.asyncio import Redis

from src.database.models import User, UserRole
from src.database.db import get_db
from src.database.redis import get_redis
from src.conf.config import settings
from src.services.users import UserService


import logging

logger = logging.getLogger(__name__)


class Hash:
    """
    Password hashing utility class.

    Provides methods for hashing passwords and verifying password hashes
    using bcrypt algorithm through passlib.

    :cvar pwd_context: Password context for bcrypt hashing.
    :type pwd_context: CryptContext
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        :param plain_password: Plain text password to verify.
        :type plain_password: str
        :param hashed_password: Hashed password to compare against.
        :type hashed_password: str
        :return: True if password matches, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain text password.

        :param password: Plain text password to hash.
        :type password: str
        :return: Hashed password string.
        :rtype: str
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")
"""OAuth2 password bearer scheme for token authentication."""


def create_jwt_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
) -> str:
    """
    Create a JWT token with expiration and type.

    :param data: Payload data to encode in the token.
    :type data: dict
    :param expires_delta: Time until token expiration.
    :type expires_delta: timedelta
    :param token_type: Type of token ('access' or 'refresh').
    :type token_type: Literal["access", "refresh"]
    :return: Encoded JWT token string.
    :rtype: str
    """
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
    """
    Create an access token for authentication.

    :param data: Payload data to encode in the token (typically contains user email).
    :type data: dict
    :param expires_delta: Custom expiration time (optional).
    :type expires_delta: timedelta | None
    :return: Encoded access token.
    :rtype: str
    """
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
    """
    Create a refresh token for obtaining new access tokens.

    :param data: Payload data to encode in the token (typically contains user email).
    :type data: dict
    :param expires_delta: Custom expiration time (optional).
    :type expires_delta: timedelta | None
    :return: Encoded refresh token.
    :rtype: str
    """
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
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    """
    Get the current authenticated user from JWT token.

    Validates the access token and retrieves the user from cache or database.
    Used as a dependency in protected routes.

    :param token: JWT access token from Authorization header.
    :type token: str
    :param db: Database session dependency.
    :type db: AsyncSession
    :param redis_client: Redis client for caching.
    :type redis_client: Redis
    :raises HTTPException: 401 if token is invalid or user not found.
    :return: Authenticated user object.
    :rtype: User
    """
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

    user_service = UserService(db, redis_client)
    user = await user_service.get_cached_user_by_email(email)
    if user is None:
        user = await user_service.get_user_by_email(email)

    if user is None:
        raise credentials_exception
    return user


async def verify_refresh_token(
    token: str, db: AsyncSession, redis_client: Redis
) -> User | None:
    """
    Verify a refresh token and return the associated user.

    :param token: JWT refresh token to verify.
    :type token: str
    :param db: Database session.
    :type db: AsyncSession
    :param redis_client: Redis client for caching.
    :type redis_client: Redis
    :return: User object if token is valid, None otherwise.
    :rtype: User | None
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None or payload.get("token_type") != "refresh":
            return None
        user = await UserService(db, redis_client).get_user_by_email(email)
        return user
    except JWTError:
        return None


def create_email_token(data: dict) -> str:
    """
    Create a JWT token for email verification or password reset.

    :param data: Payload data (typically contains user email).
    :type data: dict
    :return: Encoded email verification token.
    :rtype: str
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        seconds=settings.VERIFICATION_TOKEN_EXPIRE_SECONDS
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Extract email address from a JWT token.

    Used for email verification and password reset tokens.

    :param token: JWT token containing email in the 'sub' claim.
    :type token: str
    :raises HTTPException: 422 if token is invalid or email not found.
    :return: Email address from token.
    :rtype: str
    """
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


def get_current_admin_user(user: User = Depends(get_current_user)):
    """
    Verify that the current user has admin role.

    Dependency function for protecting admin-only routes.

    :param user: Current authenticated user.
    :type user: User
    :raises HTTPException: 403 if user is not an admin.
    :return: Admin user object.
    :rtype: User
    """
    print(f"user.role: {user.role!r} (type: {type(user.role)})")
    print(f"UserRole.ADMIN: {UserRole.ADMIN!r} (type: {type(UserRole.ADMIN)})")
    print(f"Are they equal? {user.role == UserRole.ADMIN}")
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user
