import argparse
import asyncio
from datetime import date, timedelta
from faker import Faker
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.conf.config import settings as config
from src.database.models import Contact, User

fake = Faker()


async def seed_contacts(session, user_id: int, count: int = 20):
    contacts = []
    for i in range(count):
        days_offset = fake.random_int(min=-180, max=180)
        birthday = date.today() + timedelta(days=days_offset)
        birthday = birthday.replace(year=fake.random_int(min=1950, max=2005))
        contact = Contact(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=f"+380{fake.random_number(digits=9, fix_len=True)}",
            birthday=birthday,
            additional_info=fake.text(max_nb_chars=100)
            if fake.boolean(chance_of_getting_true=30)
            else None,
            user_id=user_id,
        )
        contacts.append(contact)
    session.add_all(contacts)
    await session.commit()
    print(f"✅ Created {count} contacts")


async def seed_contacts_with_upcoming_birthdays(session, user_id: int, count: int = 5):
    contacts = []
    for i in range(count):
        days_ahead = fake.random_int(min=0, max=7)
        upcoming_date = date.today() + timedelta(days=days_ahead)
        birthday = upcoming_date.replace(year=fake.random_int(min=1960, max=2000))
        contact = Contact(
            first_name=f"Upcoming{i + 1}",
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=f"+380{fake.random_number(digits=9, fix_len=True)}",
            birthday=birthday,
            additional_info="Birthday coming soon!",
            user_id=user_id,
        )
        contacts.append(contact)
    session.add_all(contacts)
    await session.commit()
    print(f"✅ Created {count} contacts with upcoming birthdays")


async def clear_database(session):
    stmt = delete(Contact)
    result = await session.execute(stmt)
    await session.commit()
    print(f"🗑️  Cleared {result.rowcount} contacts from database")


async def get_contacts_count(session):
    stmt = select(Contact)
    result = await session.execute(stmt)
    contacts = result.scalars().all()
    return len(contacts)


async def main(user_id: int):
    engine = create_async_engine(config.DB_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(email="seeduser@example.com", hashed_password="not_a_real_hash")
            session.add(user)
            await session.commit()
            print(f"👤 Created default user with id {user.id}")
            user_id = user.id
        confirm = input("Do you want to clear existing data? (y/n): ")
        if confirm.lower() == "y":
            await clear_database(session)
        await seed_contacts(session, user_id, count=20)
        await seed_contacts_with_upcoming_birthdays(session, user_id, count=5)
        total = await get_contacts_count(session)
        print("\n✨ Database seeded successfully!")
        print(f"📊 Total contacts in database: {total}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed contacts for a user.")
    parser.add_argument("--user-id", type=int, default=1, help="User ID for contacts")
    args = parser.parse_args()
    asyncio.run(main(args.user_id))
