"""
Middleware for PiGenus API.
Includes rate limiting, request logging, and error handling.
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Callable, Awaitable
import logging
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory, for development)
# In production, use Redis or database
rate_limit_store: dict = defaultdict(dict)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def is_rate_limited(self, identifier: str) -> bool:
        """
        Check if the identifier has exceeded the rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Get or create request times for this identifier
        request_times = rate_limit_store.get(identifier, [])

        # Remove old requests outside the window
        request_times = [t for t in request_times if t > window_start]
        rate_limit_store[identifier] = request_times

        # Check if limit exceeded
        if len(request_times) >= self.max_requests:
            return True

        # Add current request
        request_times.append(now)
        return False

    def reset(self, identifier: str):
        """Reset rate limit for an identifier."""
        if identifier in rate_limit_store:
            del rate_limit_store[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable]
) -> JSONResponse:
    """
    Middleware to enforce rate limiting.
    Currently disabled by default (return await call_next(request)).
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Skip rate limiting for health endpoint
    if request.url.path == "/health":
        return await call_next(request)

    # Check rate limit
    if rate_limiter.is_rate_limited(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests",
                "retry_after": 60
            }
        )

    # Process request
    response = await call_next(request)
    return response


async def logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable]
) -> JSONResponse:
    """
    Middleware to log all requests.
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - "
        f"{duration:.4f}s - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    return response


async def error_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable]
) -> JSONResponse:
    """
    Middleware to handle errors consistently.
    """
    try:
        return await call_next(request)
    except HTTPException as e:
        logger.error(f"HTTP Error: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def setup_middleware(app: FastAPI):
    """
    Setup all middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add middleware in order
    # Order matters: error handling should be last
    app.middleware("http")(logging_middleware)
    # app.middleware("http")(rate_limit_middleware)  # Disabled by default
    app.middleware("http")(error_middleware)

    logger.info("Middleware setup complete")
