"""Advanced rate limiting middleware with Redis support"""

import time
import logging
from typing import Optional, Callable
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm

    Tracks requests per IP address with configurable limits
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size

        # Store request timestamps per IP
        self.minute_windows = defaultdict(lambda: deque(maxlen=requests_per_minute * 2))
        self.hour_windows = defaultdict(lambda: deque(maxlen=requests_per_hour * 2))

        # Cleanup interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leaks"""
        current_time = time.time()

        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 3600  # 1 hour ago

        # Clean up minute windows
        for ip in list(self.minute_windows.keys()):
            window = self.minute_windows[ip]
            while window and window[0] < cutoff_time:
                window.popleft()
            if not window:
                del self.minute_windows[ip]

        # Clean up hour windows
        for ip in list(self.hour_windows.keys()):
            window = self.hour_windows[ip]
            while window and window[0] < cutoff_time:
                window.popleft()
            if not window:
                del self.hour_windows[ip]

        self.last_cleanup = current_time
        logger.info(f"Rate limiter cleanup completed. Active IPs: {len(self.minute_windows)}")

    def is_allowed(self, identifier: str) -> tuple[bool, Optional[dict]]:
        """
        Check if request is allowed

        Args:
            identifier: Client identifier (usually IP address)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        self._cleanup_old_entries()

        minute_window = self.minute_windows[identifier]
        hour_window = self.hour_windows[identifier]

        # Remove requests outside the windows
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600

        while minute_window and minute_window[0] < minute_cutoff:
            minute_window.popleft()

        while hour_window and hour_window[0] < hour_cutoff:
            hour_window.popleft()

        # Check limits
        minute_count = len(minute_window)
        hour_count = len(hour_window)

        # Check for burst
        recent_requests = sum(1 for t in minute_window if current_time - t < 1)
        if recent_requests >= self.burst_size:
            return False, {
                "limit": self.burst_size,
                "remaining": 0,
                "reset": int(current_time + 1),
                "reason": "burst_limit_exceeded"
            }

        # Check minute limit
        if minute_count >= self.requests_per_minute:
            oldest = minute_window[0]
            reset_time = int(oldest + 60)
            return False, {
                "limit": self.requests_per_minute,
                "remaining": 0,
                "reset": reset_time,
                "reason": "minute_limit_exceeded"
            }

        # Check hour limit
        if hour_count >= self.requests_per_hour:
            oldest = hour_window[0]
            reset_time = int(oldest + 3600)
            return False, {
                "limit": self.requests_per_hour,
                "remaining": 0,
                "reset": reset_time,
                "reason": "hour_limit_exceeded"
            }

        # Request is allowed
        minute_window.append(current_time)
        hour_window.append(current_time)

        return True, {
            "limit_minute": self.requests_per_minute,
            "remaining_minute": self.requests_per_minute - minute_count - 1,
            "limit_hour": self.requests_per_hour,
            "remaining_hour": self.requests_per_hour - hour_count - 1,
            "reset_minute": int(current_time + 60),
            "reset_hour": int(current_time + 3600)
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Features:
    - Per-IP rate limiting
    - Different limits for authenticated vs anonymous users
    - Configurable burst protection
    - Automatic cleanup
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        authenticated_multiplier: float = 2.0,
        exempt_paths: Optional[list] = None
    ):
        super().__init__(app)

        self.anonymous_limiter = InMemoryRateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_size=burst_size
        )

        self.authenticated_limiter = InMemoryRateLimiter(
            requests_per_minute=int(requests_per_minute * authenticated_multiplier),
            requests_per_hour=int(requests_per_hour * authenticated_multiplier),
            burst_size=int(burst_size * authenticated_multiplier)
        )

        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
            "/metrics"
        ]

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated"""
        auth_header = request.headers.get("Authorization")
        return bool(auth_header and auth_header.startswith("Bearer "))

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""

        # Skip exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Get client identifier
        client_ip = self._get_client_ip(request)
        is_authenticated = self._is_authenticated(request)

        # Choose appropriate limiter
        limiter = self.authenticated_limiter if is_authenticated else self.anonymous_limiter

        # Check rate limit
        allowed, info = limiter.is_allowed(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} - "
                f"Reason: {info.get('reason')}"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "limit": info.get("limit"),
                    "remaining": info.get("remaining"),
                    "reset": info.get("reset")
                },
                headers={
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("reset", 0)),
                    "Retry-After": str(info.get("reset", int(time.time())) - int(time.time()))
                }
            )

        # Request allowed - add rate limit headers
        response = await call_next(request)

        response.headers["X-RateLimit-Limit-Minute"] = str(info.get("limit_minute", 0))
        response.headers["X-RateLimit-Remaining-Minute"] = str(info.get("remaining_minute", 0))
        response.headers["X-RateLimit-Limit-Hour"] = str(info.get("limit_hour", 0))
        response.headers["X-RateLimit-Remaining-Hour"] = str(info.get("remaining_hour", 0))

        return response


# Rate limiter with configurable tiers
class TieredRateLimiter:
    """
    Advanced rate limiter with user tiers

    Different limits for different user roles:
    - Free tier: Lower limits
    - Premium tier: Higher limits
    - Admin: Unlimited
    """

    def __init__(self):
        self.tiers = {
            "free": InMemoryRateLimiter(30, 500, 5),
            "premium": InMemoryRateLimiter(120, 5000, 20),
            "admin": InMemoryRateLimiter(1000, 100000, 100)
        }

    def is_allowed(self, identifier: str, tier: str = "free") -> tuple[bool, Optional[dict]]:
        """Check if request is allowed for the given tier"""
        limiter = self.tiers.get(tier, self.tiers["free"])
        return limiter.is_allowed(identifier)
