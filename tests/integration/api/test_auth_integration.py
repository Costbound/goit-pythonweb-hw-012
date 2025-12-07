from unittest.mock import Mock

import pytest
from sqlalchemy import select

from src.database.models import User
from src.database.models import UserRole

user_data = {
    "email": "test@mail.com",
    "password": "password",
    "role": UserRole.USER,
}


@pytest.mark.asyncio
async def test_signup(client, monkeypatch):
    """Test successful user registration"""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    response = await client.post("/api/auth/signup", json=user_data)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_signup_duplicate_email(client, monkeypatch):
    """Signup should fail with 409 if email already exists"""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    # first signup
    resp1 = await client.post("/api/auth/signup", json=user_data)
    assert resp1.status_code == 201

    # second signup with same email
    resp2 = await client.post("/api/auth/signup", json=user_data)
    assert resp2.status_code == 409
    data = resp2.json()
    assert "already exists" in data["message"]


@pytest.mark.asyncio
async def test_signin_unverified_email(client, monkeypatch):
    """
    Signin should fail with 401 if user is not email_verified.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    # create user via signup (email_verified = False by default)
    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    # try to login
    login_resp = await client.post(
        "/api/auth/signin",
        data={"username": user_data["email"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 401
    data = login_resp.json()
    assert "not verified" in data["message"]


@pytest.mark.asyncio
async def test_signin_success_after_verification(client, db_session, monkeypatch):
    """Successful signin after setting email_verified=True in DB."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    # signup
    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    # manually mark user as verified in DB
    result = await db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user: User = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    # signin
    login_resp = await client.post(
        "/api/auth/signin",
        data={"username": user_data["email"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signin_wrong_password(client, db_session, monkeypatch):
    """Signin should fail with 401 for wrong password."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    # create verified user
    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user: User = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    # wrong password
    login_resp = await client.post(
        "/api/auth/signin",
        data={"username": user_data["email"], "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 401
    data = login_resp.json()
    assert "Incorrect email or password" in data["message"]


@pytest.mark.asyncio
async def test_refresh_token_success(client, db_session, monkeypatch):
    """Generate new access token from valid refresh token."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    # signup + verify + signin to get refresh_token
    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user: User = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    signin_resp = await client.post(
        "/api/auth/signin",
        data={"username": user_data["email"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert signin_resp.status_code == 200
    tokens = signin_resp.json()
    refresh_token = tokens["refresh_token"]

    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Refresh with invalid token returns 401."""
    resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert "Unauthorized" in data["message"]


@pytest.mark.asyncio
async def test_request_confirmation_email_for_unverified_user(client, monkeypatch):
    """Request confirmation email sends email task for unverified user."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    resp2 = await client.post(
        "/api/auth/request-confirmation-email",
        json={"email": user_data["email"]},
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert "Confirmation email has been sent" in data["message"]
