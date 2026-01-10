"""
Security Headers Middleware

Implements security headers including CSP, HSTS, X-Frame-Options, etc.

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers implemented:
    - Content-Security-Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    - Strict-Transport-Security (HSTS) - only in production
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Content-Security-Policy with Swagger CDN support
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",  # Added CDN for Swagger
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # Added CDN for Swagger
            "img-src 'self' data: https:",
            "font-src 'self' data: https://cdn.jsdelivr.net",  # Added CDN for Swagger fonts
            "connect-src 'self' ws: wss: http://localhost:* https://api.anthropic.com",
            "frame-ancestors 'self'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        permissions = [
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "battery=()",
            "camera=()",
            "display-capture=()",
            "document-domain=()",
            "encrypted-media=()",
            "fullscreen=(self)",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "midi=()",
            "payment=()",
            "picture-in-picture=()",
            "publickey-credentials-get=()",
            "screen-wake-lock=()",
            "sync-xhr=(self)",
            "usb=()",
            "web-share=()",
            "xr-spatial-tracking=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # HSTS - only enable in production with HTTPS
        if not settings.debug:
            # max-age=31536000 (1 year), includeSubDomains, preload
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            # Don't cache API responses by default
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for basic input sanitization.

    Note: This is a basic layer. Always validate inputs at the endpoint level too.
    """

    # Patterns that might indicate malicious input
    SUSPICIOUS_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
        "eval(",
        "document.cookie",
        "document.write",
        ".innerHTML",
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check query parameters
        for key, value in request.query_params.items():
            if self._contains_suspicious(value):
                return Response(
                    content='{"detail": "Potentially malicious input detected"}',
                    status_code=400,
                    media_type="application/json"
                )

        # For POST/PUT/PATCH, we could check body but that requires reading it
        # which can cause issues. Better to validate at endpoint level.

        return await call_next(request)

    def _contains_suspicious(self, value: str) -> bool:
        """Check if value contains suspicious patterns"""
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in self.SUSPICIOUS_PATTERNS)
