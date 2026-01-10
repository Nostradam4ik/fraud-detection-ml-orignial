"""
Rate Limiting Configuration using SlowAPI

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


def get_identifier(request: Request) -> str:
    """Get identifier for rate limiting - use user ID if authenticated, else IP"""
    # Try to get user from token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Use a hash of the token as identifier for authenticated users
        return f"user:{hash(auth_header)}"
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance with headers enabled
# Disable in testing environment
import os
_testing = os.environ.get("TESTING", "").lower() == "true"

limiter = Limiter(
    key_func=get_identifier,
    headers_enabled=True,  # Enable rate limit headers
    enabled=not _testing  # Disable in testing
)


# In-memory rate limit tracking for headers
class RateLimitTracker:
    """Track rate limits for displaying in headers"""

    def __init__(self):
        self._limits: Dict[str, Dict[str, Tuple[int, int, float]]] = defaultdict(dict)
        # {identifier: {endpoint: (remaining, limit, reset_time)}}

    def update(self, identifier: str, endpoint: str, limit: int, remaining: int, reset_time: float):
        self._limits[identifier][endpoint] = (remaining, limit, reset_time)

    def get(self, identifier: str, endpoint: str = None) -> Tuple[int, int, float]:
        if endpoint and endpoint in self._limits[identifier]:
            return self._limits[identifier][endpoint]
        # Return default if not tracked
        return (settings.rate_limit_per_minute, settings.rate_limit_per_minute, time.time() + 60)

    def cleanup_old(self):
        """Remove expired entries"""
        current_time = time.time()
        for identifier in list(self._limits.keys()):
            for endpoint in list(self._limits[identifier].keys()):
                _, _, reset_time = self._limits[identifier][endpoint]
                if reset_time < current_time:
                    del self._limits[identifier][endpoint]
            if not self._limits[identifier]:
                del self._limits[identifier]


rate_limit_tracker = RateLimitTracker()


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded with proper headers"""
    # Parse retry-after from exception
    retry_after = 60  # Default
    try:
        if hasattr(exc, 'detail') and exc.detail:
            # Try to extract time from message
            detail_str = str(exc.detail)
            if 'per' in detail_str:
                retry_after = 60
    except Exception:
        pass

    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": retry_after
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time() + retry_after))
        }
    )
    return response


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Get identifier
        identifier = get_identifier(request)

        # Get current limits
        remaining, limit, reset_time = rate_limit_tracker.get(identifier, request.url.path)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response


# Rate limit decorators
def rate_limit(limit: str = None):
    """Get rate limit string"""
    if limit:
        return limit
    return f"{settings.rate_limit_per_minute}/minute"


def get_rate_limit_status(request: Request) -> Dict:
    """Get current rate limit status for the request"""
    identifier = get_identifier(request)
    remaining, limit, reset_time = rate_limit_tracker.get(identifier)

    return {
        "limit": limit,
        "remaining": remaining,
        "reset": int(reset_time),
        "reset_in_seconds": max(0, int(reset_time - time.time()))
    }
