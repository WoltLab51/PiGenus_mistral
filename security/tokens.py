"""
Token management utilities for PiGenus.
"""
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenManager:
    """Service for managing JWT tokens."""

    @staticmethod
    def create_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT token with the given data.
        
        Args:
            data: Dictionary of claims to include in the token
            expires_delta: Optional timedelta for expiration
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and verify a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data, or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except Exception as e:
            logger.warning(f"Failed to decode token: {e}")
            return None

    @staticmethod
    def verify_token(token: str) -> bool:
        """
        Verify if a token is valid.
        
        Args:
            token: JWT token string
            
        Returns:
            True if valid, False otherwise
        """
        return TokenManager.decode_token(token) is not None

    @staticmethod
    def get_token_expiration(token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime, or None if invalid
        """
        payload = TokenManager.decode_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Check if a token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if expired, False otherwise
        """
        expiration = TokenManager.get_token_expiration(token)
        if expiration is None:
            return True
        return datetime.utcnow() > expiration


# Singleton instance
token_manager = TokenManager()
