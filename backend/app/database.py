"""Database connection and session management."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=20,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables.

    Strategy:
    1. Use a PostgreSQL advisory lock to ensure only ONE worker process
       performs DB initialization, even when uvicorn runs multiple workers.
    2. Use drop_all + create_all within a single transaction so that
       composite types are properly cleaned up before recreation.

    The advisory lock key 42 is arbitrary but fixed; pg_try_advisory_lock
    returns true if the lock was acquired, false if another session holds it.
    The lock is automatically released when the connection/transaction ends.
    """
    # Import all models so Base.metadata knows about them
    import app.models.agent  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.memory  # noqa: F401
    import app.models.tenant  # noqa: F401
    import app.models.tool  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.workflow  # noqa: F401

    async with engine.begin() as conn:
        # Try to acquire advisory lock (non-blocking)
        result = await conn.execute(
            text("SELECT pg_try_advisory_xact_lock(42)")
        )
        acquired = result.scalar()

        if not acquired:
            logger.info(
                "Another worker is initializing the database, skipping."
            )
            return

        logger.info("Advisory lock acquired, initializing database...")

        # drop_all respects FK dependency order and removes composite types
        logger.info("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)

        logger.info("Creating all tables from models...")
        await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialization complete.")
