"""
Users API endpoints.

This module provides endpoints for user profile management, including
retrieving current user information and updating user avatars.
"""

from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis.asyncio import Redis

from src.database.db import get_db
from src.database.models import User
from src.database.redis import get_redis
from src.schemas import UserModel
from src.services.auth import get_current_user, get_current_admin_user
from src.services.users import UserService
from src.services.cloudinary import CloudinaryService
from src.conf.config import settings

router = APIRouter(prefix="/users", tags=["contacts"])

limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserModel)
@limiter.limit("2/minute")
async def get_current_user_info(
    request: Request,
    user: User = Depends(get_current_user),
):
    """
    Retrieve current authenticated user information.

    Rate limited to 2 requests per minute per IP address.

    :param request: The HTTP request object (used for rate limiting).
    :type request: Request
    :param user: The authenticated user.
    :type user: User
    :return: Current user details.
    :rtype: UserModel
    """
    return user


@router.patch("/avatar", response_model=UserModel)
async def update_user_avatar(
    file: UploadFile = File(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_admin_user),
):
    """
    Update user avatar image.

    Uploads the avatar to Cloudinary and updates the user's profile.
    Requires admin role.

    :param file: The avatar image file to upload.
    :type file: UploadFile
    :param db: Database session dependency.
    :type db: AsyncSession
    :param redis: Redis client dependency.
    :type redis: Redis
    :param user: The authenticated admin user.
    :type user: User
    :raises HTTPException: 500 if avatar upload fails.
    :return: Updated user with new avatar URL.
    :rtype: UserModel
    """
    try:
        avatar_url = CloudinaryService(
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        ).upload_file(file, user.id)
        user = await UserService(db, redis).update_avatar(user, avatar_url)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload avatar: {str(e)}"
        )
