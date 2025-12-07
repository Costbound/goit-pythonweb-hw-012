"""
Database connection and session management.

This module provides database session management using SQLAlchemy async engine
and session makers with proper context management and error handling.
"""

import contextlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.conf.config import settings


class DatabaseSessionManager:
    """
    Database session manager for handling async SQLAlchemy sessions.

    Manages the creation and lifecycle of database sessions using
    SQLAlchemy's async engine and session maker pattern.

    :param url: Database connection URL.
    :type url: str
    """

    def __init__(self, url: str):
        """
        Initialize the database session manager.

        Creates an async engine and session maker for the database connection.

        :param url: Database connection URL.
        :type url: str
        """
        self._engine: AsyncEngine = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Create and manage a database session context.

        Provides an async context manager for database sessions with
        automatic rollback on errors and proper cleanup.

        :raises Exception: If session maker is not initialized.
        :yields: AsyncSession: Database session.
        """
        if self._session_maker is None:
            raise Exception("Database session maker is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)
"""Global database session manager instance."""


async def get_db():
    """
    Dependency function to get database session.

    Provides a database session for FastAPI dependency injection.
    Automatically handles session lifecycle and cleanup.

    :yields: AsyncSession: Database session for use in route handlers.
    """
    async with sessionmanager.session() as session:
        yield session
