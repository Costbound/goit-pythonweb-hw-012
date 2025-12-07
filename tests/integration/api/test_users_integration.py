import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from src.database.models import UserRole


@pytest.mark.asyncio
async def test_get_current_user_info_success(authorized_client, test_user_in_db):
    """Test getting current user information."""
    response = await authorized_client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_in_db.email
    assert "id" in data


@pytest.mark.asyncio
async def test_get_current_user_info_unauthorized(client):
    """Test getting user info without authentication."""
    response = await client.get("/api/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_info_rate_limit(authorized_client, test_user_in_db):
    """Test rate limiting on get current user endpoint (1 request per minute)."""
    # Make first request (should succeed)
    resp1 = await authorized_client.get("/api/users/me")
    assert resp1.status_code == 200

    # Second request should be rate limited
    resp2 = await authorized_client.get("/api/users/me")
    assert resp2.status_code == 429  # Too Many Requests


@pytest.mark.asyncio
async def test_update_user_avatar_success(
    client, db_session, create_authenticated_user
):
    """Test updating user avatar."""
    # Create admin user
    admin_token, admin_user = await create_authenticated_user(
        "admin@example.com", "adminpass123"
    )

    # Make user admin (use role enum)
    admin_user.role = UserRole.ADMIN
    await db_session.commit()

    # Mock Cloudinary upload
    mock_avatar_url = "https://res.cloudinary.com/test/image/upload/avatar.jpg"

    with patch("src.api.users.CloudinaryService") as mock_cloudinary_class:
        mock_instance = MagicMock()
        mock_instance.upload_file.return_value = mock_avatar_url
        mock_cloudinary_class.return_value = mock_instance

        # Create fake image file
        file_content = b"fake image content"
        files = {"file": ("avatar.jpg", BytesIO(file_content), "image/jpeg")}

        response = await client.patch(
            "/api/users/avatar",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == mock_avatar_url
        assert data["email"] == admin_user.email

        # Verify Cloudinary was called
        mock_instance.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_avatar_unauthorized(client):
    """Test updating avatar without authentication."""
    file_content = b"fake image content"
    files = {"file": ("avatar.jpg", BytesIO(file_content), "image/jpeg")}

    response = await client.patch("/api/users/avatar", files=files)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_avatar_non_admin(authorized_client):
    """Test updating avatar as non-admin user (should fail)."""
    file_content = b"fake image content"
    files = {"file": ("avatar.jpg", BytesIO(file_content), "image/jpeg")}

    response = await authorized_client.patch("/api/users/avatar", files=files)
    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_update_user_avatar_invalid_file_type(
    client, db_session, create_authenticated_user
):
    """Test updating avatar with invalid file type."""
    # Create admin user
    admin_token, admin_user = await create_authenticated_user(
        "admin2@example.com", "adminpass123"
    )

    # Make user admin (use role enum)
    admin_user.role = UserRole.ADMIN
    await db_session.commit()

    # Mock Cloudinary to raise exception
    with patch("src.api.users.CloudinaryService") as mock_cloudinary_class:
        mock_instance = MagicMock()
        mock_instance.upload_file.side_effect = Exception("Invalid file type")
        mock_cloudinary_class.return_value = mock_instance

        # Try to upload a text file instead of image
        file_content = b"not an image"
        files = {"file": ("document.txt", BytesIO(file_content), "text/plain")}

        response = await client.patch(
            "/api/users/avatar",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should fail with 500 (caught by global exception handler)
        assert response.status_code == 500
        assert "internal server error" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_update_user_avatar_cloudinary_error(
    client, db_session, create_authenticated_user
):
    """Test avatar update when Cloudinary service fails."""
    # Create admin user
    admin_token, admin_user = await create_authenticated_user(
        "admin3@example.com", "adminpass123"
    )

    # Make user admin (use role enum)
    admin_user.role = UserRole.ADMIN
    await db_session.commit()

    # Mock Cloudinary failure
    with patch("src.api.users.CloudinaryService") as mock_cloudinary_class:
        mock_instance = MagicMock()
        mock_instance.upload_file.side_effect = Exception("Cloudinary upload failed")
        mock_cloudinary_class.return_value = mock_instance

        file_content = b"fake image content"
        files = {"file": ("avatar.jpg", BytesIO(file_content), "image/jpeg")}

        response = await client.patch(
            "/api/users/avatar",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should return 500 error (caught by global exception handler)
        assert response.status_code == 500
        assert "internal server error" in response.json()["message"].lower()
