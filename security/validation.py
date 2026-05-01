"""
Input validation utilities for PiGenus.
"""
from pydantic import BaseModel, validator, Field
from typing import Any, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error."""
    pass


class InputValidator:
    """Service for validating input data."""

    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate a username.
        
        Rules:
        - 1-50 characters
        - Alphanumeric + underscore, hyphen, dot
        - Cannot start or end with special character
        """
        if not 1 <= len(username) <= 50:
            raise ValidationError("Username must be 1-50 characters")
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9]$', username):
            raise ValidationError(
                "Username can only contain alphanumeric characters, "
                "underscores, hyphens, and dots, and cannot start/end with special characters"
            )
        
        return username

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate a password.
        
        Rules:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character")
        
        return password

    @staticmethod
    def validate_worker_name(name: str) -> str:
        """
        Validate a worker name.
        
        Rules:
        - 1-100 characters
        - Alphanumeric + hyphen, underscore, dot
        """
        if not 1 <= len(name) <= 100:
            raise ValidationError("Worker name must be 1-100 characters")
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            raise ValidationError(
                "Worker name can only contain alphanumeric characters, "
                "hyphens, underscores, and dots"
            )
        
        return name

    @staticmethod
    def validate_job_priority(priority: int) -> int:
        """
        Validate job priority.
        
        Rules:
        - Non-negative integer
        - Reasonable upper limit (e.g., 1000)
        """
        if not isinstance(priority, int):
            raise ValidationError("Priority must be an integer")
        
        if priority < 0:
            raise ValidationError("Priority cannot be negative")
        
        if priority > 1000:
            raise ValidationError("Priority cannot exceed 1000")
        
        return priority

    @staticmethod
    def validate_json_data(data: Any) -> Dict[str, Any]:
        """
        Validate that data is JSON-serializable.
        """
        try:
            import json
            json.dumps(data)
            return data
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Data must be JSON-serializable: {e}")

    @staticmethod
    def validate_memory_key(key: str) -> str:
        """
        Validate a memory key.
        
        Rules:
        - 1-255 characters
        - No spaces
        - Alphanumeric + common special characters
        """
        if not 1 <= len(key) <= 255:
            raise ValidationError("Memory key must be 1-255 characters")
        
        if ' ' in key:
            raise ValidationError("Memory key cannot contain spaces")
        
        if not re.match(r'^[a-zA-Z0-9_./-]+$', key):
            raise ValidationError(
                "Memory key can only contain alphanumeric characters, "
                "underscores, dots, hyphens, and forward slashes"
            )
        
        return key


# Pydantic models for common validations
class ValidatedWorkerName(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('name')
    def validate_name(cls, v):
        return InputValidator.validate_worker_name(v)


class ValidatedUsername(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    
    @validator('username')
    def validate_username(cls, v):
        return InputValidator.validate_username(v)


class ValidatedPassword(BaseModel):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        return InputValidator.validate_password(v)


# Singleton instance
validator = InputValidator()
