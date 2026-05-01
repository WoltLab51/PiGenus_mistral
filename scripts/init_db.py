#!/usr/bin/env python3
"""
Initialize the PiGenus database.
Creates all tables and optionally adds a test admin user.
"""
from db.database import engine, init_db
from db.models import SQLModel, User
from sqlmodel import Session, select
from security.tokens import get_password_hash
import os
from core.config import settings


def create_test_admin():
    """Create a test admin user if none exists."""
    with Session(engine) as session:
        # Check if any admin user exists
        admin_exists = session.exec(
            select(User).where(User.is_admin == True)
        ).first()

        if not admin_exists:
            hashed_password = get_password_hash("admin123")
            admin = User(
                username="admin",
                hashed_password=hashed_password,
                is_admin=True
            )
            session.add(admin)
            session.commit()
            print("Created test admin user: username='admin', password='admin123'")
        else:
            print("Admin user already exists")


def main():
    print("Initializing PiGenus database...")
    
    # Create all tables
    init_db()
    
    # Create test admin if in debug mode or if requested
    if settings.debug or os.getenv("CREATE_TEST_ADMIN", "").lower() == "true":
        create_test_admin()
    
    print("Database initialization complete!")


if __name__ == "__main__":
    main()
