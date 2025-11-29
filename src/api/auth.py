import asyncio
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request,
)
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.email import send_email
from src.schemas import (
    UserCreate,
    Token,
    UserModel,
    TokenRefreshRequest,
    EmailVerificationRequest,
)
from src.services.auth import (
    create_access_token,
    Hash,
    create_refresh_token,
    verify_refresh_token,
    get_email_from_token,
)
from src.services.users import UserService
from src.database.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)

    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.email, str(request.base_url)
    )
    return new_user


@router.post("/signin", response_model=Token)
async def signin(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await UserService(db).get_user_by_email(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.email_verified is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await asyncio.gather(
        create_access_token(data={"sub": user.email}),
        create_refresh_token(data={"sub": user.email}),
    )
    user.refresh_token = refresh_token
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def generate_access_token(
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await verify_refresh_token(body.refresh_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    new_access_token = await create_access_token(data={"sub": user.email})
    return {
        "access_token": new_access_token,
        "refresh_token": body.refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    email = get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )
    if user.email_verified:
        return {"message": "Email is already verified."}
    await user_service.confirm_user_email(user)
    return {"message": "Email verified successfully."}


@router.post("/request-confirmation-email")
async def request_confirmation_email(
    body: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).get_user_by_email(body.email)
    if user and user.email_verified:
        return {"message": "Email is already verified."}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.email, str(request.base_url)
        )
    return {"message": "Confirmation email has been sent to your email address."}
