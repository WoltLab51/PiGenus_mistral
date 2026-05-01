"""
Dependencies for FastAPI endpoints in PiGenus.
"""
from fastapi import Depends
from sqlmodel import Session
from db.database import get_session
from api.auth import get_current_user, get_current_admin_user
from models.schemas import TokenData

# Database session dependency
get_db = get_session

# Authentication dependencies
get_current_user_dep = get_current_user
get_current_admin_user_dep = get_current_admin_user


async def get_db_session() -> Session:
    """
    Dependency to get a database session.
    """
    async for session in get_session():
        yield session


async def get_current_user_token(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get the current authenticated user.
    """
    return current_user


async def get_current_admin_user_token(
    current_user: TokenData = Depends(get_current_admin_user)
) -> TokenData:
    """
    Dependency to get the current authenticated admin user.
    """
    return current_user
