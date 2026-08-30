from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker


DATABASE_URL = (
    "postgresql+psycopg://"
    "agent_user:agent_password@"
    "localhost:5432/"
    "enterprise_analytics"
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """
    FastAPI dependency that provides
    one database session per request.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
