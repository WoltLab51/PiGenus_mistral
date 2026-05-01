"""
Database connection and session management for PiGenus.
"""
from sqlmodel import create_engine, Session
from core.config import settings

# Create SQLite engine
engine = create_engine(settings.database_url, echo=settings.debug)


def get_session():
    """
    Dependency function to get a database session.
    Use this in FastAPI endpoints with `Depends(get_session)`.
    """
    with Session(engine) as session:
        yield session


def init_db():
    """
    Initialize the database by creating all tables.
    """
    from db.models import SQLModel
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
