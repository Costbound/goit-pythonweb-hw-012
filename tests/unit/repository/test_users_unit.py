import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.users import UserRepository
from src.database.models import User, UserRole
from src.schemas import UserCreate


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def user_repository(mock_session):
    """Create UserRepository instance with mock session"""
    return UserRepository(mock_session)


@pytest.fixture
def mock_user():
    """Create a mock user"""
    user = User(
        id=1,
        email="test@example.com",
        password_hash="hashed_password",
        email_verified=False,
        avatar_url=None,
        reset_password_token=None,
    )
    return user


@pytest.fixture
def user_create_data():
    """Sample user creation data"""
    return UserCreate(
        email="newuser@example.com",
        password="SecurePassword123!",
        role=UserRole.USER,
    )


class TestGetUserById:
    """Tests for get_user_by_id method"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, user_repository, mock_session, mock_user):
        """Test getting an existing user by ID"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_repository.get_user_by_id(user_id=1)

        # Assert
        assert user is not None
        assert user.id == 1
        assert user.email == "test@example.com"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_repository, mock_session):
        """Test getting a non-existing user by ID"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_repository.get_user_by_id(user_id=999)

        # Assert
        assert user is None
        mock_session.execute.assert_called_once()


class TestGetUserByEmail:
    """Tests for get_user_by_email method"""

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(
        self, user_repository, mock_session, mock_user
    ):
        """Test getting an existing user by email"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_repository.get_user_by_email(email="test@example.com")

        # Assert
        assert user is not None
        assert user.email == "test@example.com"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repository, mock_session):
        """Test getting a non-existing user by email"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_repository.get_user_by_email(email="nonexistent@example.com")

        # Assert
        assert user is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_case_sensitive(
        self, user_repository, mock_session
    ):
        """Test that email lookup is case-sensitive"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_repository.get_user_by_email(email="TEST@EXAMPLE.COM")

        # Assert
        assert user is None
        mock_session.execute.assert_called_once()


class TestCreateUser:
    """Tests for create_user method"""

    @pytest.mark.asyncio
    async def test_create_user_without_avatar(
        self, user_repository, mock_session, user_create_data
    ):
        """Test creating a user without avatar"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        user = await user_repository.create_user(user_create_data)

        # Assert
        assert user.email == "newuser@example.com"
        assert user.password_hash == "SecurePassword123!"
        assert user.avatar_url is None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_with_avatar(
        self, user_repository, mock_session, user_create_data
    ):
        """Test creating a user with avatar URL"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        avatar_url = "https://example.com/avatar.jpg"

        # Act
        user = await user_repository.create_user(
            user_create_data, avatar_url=avatar_url
        )

        # Assert
        assert user.email == "newuser@example.com"
        assert user.password_hash == "SecurePassword123!"
        assert user.avatar_url == avatar_url
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestSetEmailVerified:
    """Tests for set_email_verified method"""

    @pytest.mark.asyncio
    async def test_set_email_verified(self, user_repository, mock_session, mock_user):
        """Test marking user email as verified"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        assert mock_user.email_verified is False

        # Act
        updated_user = await user_repository.set_email_verified(mock_user)

        # Assert
        assert updated_user.email_verified is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)


class TestUpdateUserAvatar:
    """Tests for update_user_avatar method"""

    @pytest.mark.asyncio
    async def test_update_user_avatar(self, user_repository, mock_session, mock_user):
        """Test updating user avatar URL"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        new_avatar_url = "https://example.com/new-avatar.jpg"
        assert mock_user.avatar_url is None

        # Act
        updated_user = await user_repository.update_user_avatar(
            mock_user, new_avatar_url
        )

        # Assert
        assert updated_user.avatar_url == new_avatar_url
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_user_avatar_replace_existing(
        self, user_repository, mock_session, mock_user
    ):
        """Test replacing existing avatar URL"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_user.avatar_url = "https://example.com/old-avatar.jpg"
        new_avatar_url = "https://example.com/new-avatar.jpg"

        # Act
        updated_user = await user_repository.update_user_avatar(
            mock_user, new_avatar_url
        )

        # Assert
        assert updated_user.avatar_url == new_avatar_url
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)


class TestUpdateUserPassword:
    """Tests for update_user_password method"""

    @pytest.mark.asyncio
    async def test_update_user_password(self, user_repository, mock_session, mock_user):
        """Test updating user password"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        old_hash = mock_user.password_hash
        new_hash = "new_hashed_password_123"

        # Act
        updated_user = await user_repository.update_user_password(mock_user, new_hash)

        # Assert
        assert updated_user.password_hash == new_hash
        assert updated_user.password_hash != old_hash
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)


class TestUpdateResetPasswordToken:
    """Tests for update_reset_password_token method"""

    @pytest.mark.asyncio
    async def test_set_reset_password_token(
        self, user_repository, mock_session, mock_user
    ):
        """Test setting reset password token"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        token = "reset_token_123abc"
        assert mock_user.reset_password_token is None

        # Act
        updated_user = await user_repository.update_reset_password_token(
            mock_user, token
        )

        # Assert
        assert updated_user.reset_password_token == token
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_clear_reset_password_token(
        self, user_repository, mock_session, mock_user
    ):
        """Test clearing reset password token"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_user.reset_password_token = "existing_token"

        # Act
        updated_user = await user_repository.update_reset_password_token(
            mock_user, None
        )

        # Assert
        assert updated_user.reset_password_token is None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)


class TestUpdateMultipleFields:
    """Tests for update_multiple_fields method"""

    @pytest.mark.asyncio
    async def test_update_single_allowed_field(
        self, user_repository, mock_session, mock_user
    ):
        """Test updating a single allowed field"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        updated_user = await user_repository.update_multiple_fields(
            mock_user, avatar_url="https://example.com/avatar.jpg"
        )

        # Assert
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_multiple_allowed_fields(
        self, user_repository, mock_session, mock_user
    ):
        """Test updating multiple allowed fields atomically"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        updated_user = await user_repository.update_multiple_fields(
            mock_user,
            avatar_url="https://example.com/avatar.jpg",
            email_verified=True,
            reset_password_token="token123",
        )

        # Assert
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
        assert updated_user.email_verified is True
        assert updated_user.reset_password_token == "token123"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_protected_field_raises_error(
        self, user_repository, mock_session, mock_user
    ):
        """Test that updating protected fields raises ValueError"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot update protected fields: email"):
            await user_repository.update_multiple_fields(
                mock_user, email="newemail@example.com"
            )

        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_invalid_field_raises_error(
        self, user_repository, mock_session, mock_user
    ):
        """Test that updating non-existent fields raises ValueError"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="Fields do not exist in User model"):
            await user_repository.update_multiple_fields(
                mock_user, invalid_field="value"
            )

        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_multiple_fields_one_protected(
        self, user_repository, mock_session, mock_user
    ):
        """Test that mixing allowed and protected fields raises error"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot update protected fields: id"):
            await user_repository.update_multiple_fields(
                mock_user,
                avatar_url="https://example.com/avatar.jpg",
                id=999,  # Protected field
            )

        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_all_allowed_fields(
        self, user_repository, mock_session, mock_user
    ):
        """Test updating all allowed fields at once"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        updated_user = await user_repository.update_multiple_fields(
            mock_user,
            password_hash="new_hash",
            avatar_url="https://example.com/avatar.jpg",
            email_verified=True,
            reset_password_token="token123",
        )

        # Assert
        assert updated_user.password_hash == "new_hash"
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
        assert updated_user.email_verified is True
        assert updated_user.reset_password_token == "token123"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_no_fields(self, user_repository, mock_session, mock_user):
        """Test calling update with no fields - should not commit"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = AsyncMock()

        # Act
        updated_user = await user_repository.update_multiple_fields(mock_user)

        # Assert
        assert updated_user == mock_user
        mock_session.add.assert_not_called()  # Should NOT add
        mock_session.commit.assert_not_called()  # Should NOT commit
        mock_session.refresh.assert_not_called()  # Should NOT refresh

    @pytest.mark.asyncio
    async def test_update_with_none_values(
        self, user_repository, mock_session, mock_user
    ):
        """Test updating fields with None values (clearing fields)"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_user.avatar_url = "https://example.com/old.jpg"
        mock_user.reset_password_token = "old_token"

        # Act
        updated_user = await user_repository.update_multiple_fields(
            mock_user, avatar_url=None, reset_password_token=None
        )

        # Assert
        assert updated_user.avatar_url is None
        assert updated_user.reset_password_token is None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)
