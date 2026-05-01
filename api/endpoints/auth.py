"""
Authentication endpoints for PiGenus API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlmodel import Session
from db.database import get_session
from db.models import User
from api.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    Token,
    UserInDB
)
from models.schemas import LoginRequest, Token as TokenSchema
from core.config import settings

router = APIRouter()


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    Generate a JWT access token for authentication.
    Use username and password to get a token.
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={
            "sub": user.username,
            "is_admin": user.is_admin
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# For development: Create a test user if none exists
@router.post("/create-test-user", response_model=TokenSchema)
async def create_test_user(
    login: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    **Development only**: Create a test user and return a token.
    This endpoint should be disabled in production!
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in debug mode"
        )

    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.username == login.username)
    ).first()

    if existing_user:
        # User exists, just authenticate
        user = authenticate_user(session, login.username, login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
    else:
        # Create new user
        hashed_password = get_password_hash(login.password)
        user = User(
            username=login.username,
            hashed_password=hashed_password,
            is_admin=True  # Test user is admin
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    # Generate token
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={
            "sub": user.username,
            "is_admin": user.is_admin
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
