import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactRepository
from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def contact_repository(mock_session):
    """Create ContactRepository instance with mock session"""
    return ContactRepository(mock_session)


@pytest.fixture
def mock_user():
    """Create a mock user"""
    user = User(
        id=1,
        email="test@example.com",
        password_hash="hashed_password",
        email_verified=True,
    )
    return user


@pytest.fixture
def mock_contact():
    """Create a mock contact"""
    contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+380509876543",
        birthday=date(1990, 5, 15),
        user_id=1,
    )
    return contact


@pytest.fixture
def contact_data():
    """Sample contact data for creation"""
    return ContactModel(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone="+380509876543",
        birthday=date(1995, 8, 20),
        additional_info="Test data",
    )


class TestGetContacts:
    """Tests for get_contacts method"""

    @pytest.mark.asyncio
    async def test_get_contacts_no_filter(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test getting contacts without filters"""
        # Arrange
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_contact]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        contacts = await contact_repository.get_contacts(
            user=mock_user, skip=0, limit=10, filter=None
        )

        # Assert
        assert len(contacts) == 1
        assert contacts[0].id == 1
        assert contacts[0].first_name == "John"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts_with_first_name_filter(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test getting contacts filtered by first name"""
        # Arrange
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_contact]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        contacts = await contact_repository.get_contacts(
            user=mock_user, skip=0, limit=10, filter={"first_name": "John"}
        )

        # Assert
        assert len(contacts) == 1
        assert contacts[0].first_name == "John"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts_with_email_filter(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test getting contacts filtered by email"""
        # Arrange
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_contact]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        contacts = await contact_repository.get_contacts(
            user=mock_user, skip=0, limit=10, filter={"email": "john.doe@example.com"}
        )

        # Assert
        assert len(contacts) == 1
        assert contacts[0].email == "john.doe@example.com"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts_with_pagination(
        self, contact_repository, mock_session, mock_user
    ):
        """Test getting contacts with pagination"""
        # Arrange
        contacts = [
            Contact(id=i, first_name=f"User{i}", user_id=1) for i in range(1, 6)
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = contacts[2:4]  # Skip 2, limit 2
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        result = await contact_repository.get_contacts(
            user=mock_user, skip=2, limit=2, filter=None
        )

        # Assert
        assert len(result) == 2
        assert result[0].id == 3
        assert result[1].id == 4
        mock_session.execute.assert_called_once()


class TestGetContact:
    """Tests for get_contact method"""

    @pytest.mark.asyncio
    async def test_get_contact_found(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test getting an existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_session.execute.return_value = mock_result

        # Act
        contact = await contact_repository.get_contact(mock_user, contact_id=1)

        # Assert
        assert contact is not None
        assert contact.id == 1
        assert contact.first_name == "John"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact_not_found(
        self, contact_repository, mock_session, mock_user
    ):
        """Test getting a non-existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        contact = await contact_repository.get_contact(mock_user, contact_id=999)

        # Assert
        assert contact is None
        mock_session.execute.assert_called_once()


class TestCreateContact:
    """Tests for create_contact method"""

    @pytest.mark.asyncio
    async def test_create_contact(
        self, contact_repository, mock_session, mock_user, contact_data
    ):
        """Test creating a new contact"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        contact = await contact_repository.create_contact(mock_user, contact_data)

        # Assert
        assert contact.first_name == "Jane"
        assert contact.last_name == "Smith"
        assert contact.email == "jane.smith@example.com"
        assert contact.user_id == mock_user.id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestUpdateContact:
    """Tests for update_contact method"""

    @pytest.mark.asyncio
    async def test_update_contact_success(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test updating an existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        update_data = ContactUpdate(first_name="Johnny", phone="+380509999999")  # type: ignore

        # Act
        updated_contact = await contact_repository.update_contact(
            mock_user, contact_id=1, body=update_data
        )

        # Assert
        assert updated_contact is not None
        assert updated_contact.first_name == "Johnny"
        assert updated_contact.phone == "+380509999999"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_contact_not_found(
        self, contact_repository, mock_session, mock_user
    ):
        """Test updating a non-existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = ContactUpdate(first_name="Johnny")  # type: ignore

        # Act
        updated_contact = await contact_repository.update_contact(
            mock_user, contact_id=999, body=update_data
        )

        # Assert
        assert updated_contact is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestDeleteContact:
    """Tests for delete_contact method"""

    @pytest.mark.asyncio
    async def test_delete_contact_success(
        self, contact_repository, mock_session, mock_user, mock_contact
    ):
        """Test deleting an existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act
        deleted_contact = await contact_repository.delete_contact(
            mock_user, contact_id=1
        )

        # Assert
        assert deleted_contact is not None
        assert deleted_contact.id == 1
        mock_session.delete.assert_called_once_with(mock_contact)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(
        self, contact_repository, mock_session, mock_user
    ):
        """Test deleting a non-existing contact"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        deleted_contact = await contact_repository.delete_contact(
            mock_user, contact_id=999
        )

        # Assert
        assert deleted_contact is None
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


class TestGetContactsWithBirthdayInPeriod:
    """Tests for get_contacts_with_birthday_in_period method"""

    @pytest.mark.asyncio
    async def test_get_contacts_with_upcoming_birthdays(
        self, contact_repository, mock_session, mock_user
    ):
        """Test getting contacts with birthdays in a date range"""
        # Arrange
        today = date.today()
        next_week = today + timedelta(days=7)

        contacts_with_birthdays = [
            Contact(
                id=1, first_name="John", birthday=today + timedelta(days=3), user_id=1
            ),
            Contact(
                id=2, first_name="Jane", birthday=today + timedelta(days=5), user_id=1
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = contacts_with_birthdays
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        contacts = await contact_repository.get_contacts_with_birthday_in_period(
            mock_user, start_date=today, end_date=next_week
        )

        # Assert
        assert len(contacts) == 2
        assert contacts[0].first_name == "John"
        assert contacts[1].first_name == "Jane"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts_no_birthdays_in_period(
        self, contact_repository, mock_session, mock_user
    ):
        """Test when no contacts have birthdays in the period"""
        # Arrange
        today = date.today()
        next_week = today + timedelta(days=7)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        contacts = await contact_repository.get_contacts_with_birthday_in_period(
            mock_user, start_date=today, end_date=next_week
        )

        # Assert
        assert len(contacts) == 0
        mock_session.execute.assert_called_once()
