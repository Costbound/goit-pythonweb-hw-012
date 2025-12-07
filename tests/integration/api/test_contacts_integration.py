import pytest
from datetime import date, timedelta

# Sample contact data
contact_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+380501234567",
    "birthday": "1990-05-15",
    "additional_info": "Test contact",
}


@pytest.mark.asyncio
async def test_create_contact_success(authorized_client):
    """Test creating a new contact."""
    response = await authorized_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["last_name"] == contact_data["last_name"]
    assert data["email"] == contact_data["email"]
    assert data["phone"] == contact_data["phone"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_contact_unauthorized(client):
    """Test creating contact without authentication."""
    response = await client.post("/api/contacts", json=contact_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_contact_duplicate_email(authorized_client):
    """Test creating contact with duplicate email for same user."""
    # Create first contact
    resp1 = await authorized_client.post("/api/contacts", json=contact_data)
    assert resp1.status_code == 201

    # Try to create second contact with same email
    resp2 = await authorized_client.post("/api/contacts", json=contact_data)
    assert resp2.status_code == 409
    data = resp2.json()
    assert "already exists" in data["message"]


@pytest.mark.asyncio
async def test_create_contact_duplicate_phone(authorized_client):
    """Test creating contact with duplicate phone for same user."""
    # Create first contact
    resp1 = await authorized_client.post("/api/contacts", json=contact_data)
    assert resp1.status_code == 201

    # Try to create second contact with same phone but different email
    duplicate_phone_data = contact_data.copy()
    duplicate_phone_data["email"] = "different@example.com"

    resp2 = await authorized_client.post("/api/contacts", json=duplicate_phone_data)
    assert resp2.status_code == 409
    data = resp2.json()
    assert "phone number already exists" in data["message"]


@pytest.mark.asyncio
async def test_create_contact_invalid_phone(authorized_client):
    """Test creating contact with invalid phone number."""
    invalid_contact = contact_data.copy()
    invalid_contact["phone"] = "invalid-phone"
    invalid_contact["email"] = "unique@example.com"

    response = await authorized_client.post("/api/contacts", json=invalid_contact)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_contacts_empty(authorized_client):
    """Test getting contacts when none exist."""
    response = await authorized_client.get("/api/contacts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_contacts_list(authorized_client):
    """Test getting list of contacts."""
    # Create multiple contacts
    for i in range(3):
        contact = contact_data.copy()
        contact["email"] = f"contact{i}@example.com"
        contact["phone"] = f"+38050123456{i}"
        await authorized_client.post("/api/contacts", json=contact)

    # Get contacts
    response = await authorized_client.get("/api/contacts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_contacts_pagination(authorized_client):
    """Test pagination in get contacts."""
    # Create 15 contacts
    for i in range(15):
        contact = contact_data.copy()
        contact["email"] = f"contact{i}@example.com"
        contact["phone"] = f"+38050123{i:04d}"
        await authorized_client.post("/api/contacts", json=contact)

    # Get first page (default show=10)
    resp1 = await authorized_client.get("/api/contacts?page=1&show=10")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1) == 10

    # Get second page
    resp2 = await authorized_client.get("/api/contacts?page=2&show=10")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 5


@pytest.mark.asyncio
async def test_get_contacts_filter_by_first_name(authorized_client):
    """Test filtering contacts by first name."""
    # Create contacts with different names
    contact1 = contact_data.copy()
    contact1["first_name"] = "Alice"
    contact1["email"] = "alice@example.com"
    contact1["phone"] = "+380501111111"

    contact2 = contact_data.copy()
    contact2["first_name"] = "Bob"
    contact2["email"] = "bob@example.com"
    contact2["phone"] = "+380502222222"

    await authorized_client.post("/api/contacts", json=contact1)
    await authorized_client.post("/api/contacts", json=contact2)

    # Filter by first name
    response = await authorized_client.get("/api/contacts?first_name=Alice")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_contacts_filter_by_email(authorized_client):
    """Test filtering contacts by email."""
    # Create contacts
    contact1 = contact_data.copy()
    contact1["email"] = "findme@example.com"
    contact1["phone"] = "+380501111111"

    await authorized_client.post("/api/contacts", json=contact1)

    # Filter by email
    response = await authorized_client.get("/api/contacts?email=findme@example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "findme@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_id_success(authorized_client):
    """Test getting a specific contact by ID."""
    # Create contact
    create_resp = await authorized_client.post("/api/contacts", json=contact_data)
    contact_id = create_resp.json()["id"]

    # Get contact by ID
    response = await authorized_client.get(f"/api/contacts/{contact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["first_name"] == contact_data["first_name"]


@pytest.mark.asyncio
async def test_get_contact_by_id_not_found(authorized_client):
    """Test getting non-existent contact."""
    response = await authorized_client.get("/api/contacts/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contact_success(authorized_client):
    """Test updating a contact."""
    # Create contact
    create_resp = await authorized_client.post("/api/contacts", json=contact_data)
    contact_id = create_resp.json()["id"]

    # Update contact
    update_data = {"first_name": "Jane", "phone": "+380509999999"}
    response = await authorized_client.patch(
        f"/api/contacts/{contact_id}", json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["phone"] == "+380509999999"
    assert data["last_name"] == contact_data["last_name"]  # Unchanged


@pytest.mark.asyncio
async def test_update_contact_not_found(authorized_client):
    """Test updating non-existent contact."""
    update_data = {"first_name": "Jane"}
    response = await authorized_client.patch("/api/contacts/99999", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_contact_success(authorized_client):
    """Test deleting a contact."""
    # Create contact
    create_resp = await authorized_client.post("/api/contacts", json=contact_data)
    contact_id = create_resp.json()["id"]

    # Delete contact
    response = await authorized_client.delete(f"/api/contacts/{contact_id}")
    assert response.status_code == 204

    # Verify deletion
    get_resp = await authorized_client.get(f"/api/contacts/{contact_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_contact_not_found(authorized_client):
    """Test deleting non-existent contact."""
    response = await authorized_client.delete("/api/contacts/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(authorized_client):
    """Test getting contacts with upcoming birthdays."""
    today = date.today()

    # Create contact with birthday in 3 days
    upcoming_contact = contact_data.copy()
    upcoming_birthday = today + timedelta(days=3)
    upcoming_contact["birthday"] = upcoming_birthday.replace(year=1990).isoformat()
    upcoming_contact["email"] = "upcoming@example.com"
    upcoming_contact["phone"] = "+380501111111"

    # Create contact with past birthday
    past_contact = contact_data.copy()
    past_birthday = today - timedelta(days=30)
    past_contact["birthday"] = past_birthday.replace(year=1990).isoformat()
    past_contact["email"] = "past@example.com"
    past_contact["phone"] = "+380502222222"

    await authorized_client.post("/api/contacts", json=upcoming_contact)
    await authorized_client.post("/api/contacts", json=past_contact)

    # Get upcoming birthdays
    response = await authorized_client.get(
        "/api/contacts/birthdays/upcoming?days_ahead=7"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verify upcoming contact is in results
    emails = [contact["email"] for contact in data]
    assert "upcoming@example.com" in emails


@pytest.mark.asyncio
async def test_contacts_isolation_between_users(client, create_authenticated_user):
    """Test that users can only access their own contacts."""
    # Create first user
    user1_token, user1 = await create_authenticated_user(
        "user1@example.com", "password123"
    )

    # Create contact for first user
    contact1 = contact_data.copy()
    contact1["email"] = "user1contact@example.com"
    await client.post(
        "/api/contacts",
        json=contact1,
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    # Create second user
    user2_token, user2 = await create_authenticated_user(
        "user2@example.com", "password456"
    )

    # Second user should not see first user's contacts
    response = await client.get(
        "/api/contacts",
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_create_contact_missing_required_fields(authorized_client):
    """Test creating contact with missing required fields."""
    incomplete_data = {"first_name": "John"}

    response = await authorized_client.post("/api/contacts", json=incomplete_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_contact_invalid_email(authorized_client):
    """Test creating contact with invalid email format."""
    invalid_contact = contact_data.copy()
    invalid_contact["email"] = "not-an-email"
    invalid_contact["phone"] = "+380509999999"

    response = await authorized_client.post("/api/contacts", json=invalid_contact)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_contact_partial_update(authorized_client):
    """Test partial update of contact (only some fields)."""
    # Create contact
    create_resp = await authorized_client.post("/api/contacts", json=contact_data)
    contact_id = create_resp.json()["id"]

    # Update only additional_info
    update_data = {"additional_info": "Updated info"}
    response = await authorized_client.patch(
        f"/api/contacts/{contact_id}", json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["additional_info"] == "Updated info"
    assert data["first_name"] == contact_data["first_name"]  # Unchanged
    assert data["email"] == contact_data["email"]  # Unchanged
