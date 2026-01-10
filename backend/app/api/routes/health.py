"""Health check endpoints with advanced monitoring"""

import os
import sys
import time
import platform
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request
from sqlalchemy import text

from ...models.schemas import HealthResponse
from ...models.ml_model import fraud_model
from ...core.config import settings
from ...core.rate_limit import get_rate_limit_status
from ...db.database import engine

router = APIRouter()

# Track startup time
STARTUP_TIME = time.time()


def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "type": "sqlite" if "sqlite" in str(engine.url) else "postgresql"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity (if configured)"""
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)
        start = time.time()
        client.ping()
        latency = (time.time() - start) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "message": "Redis not configured or unreachable"
        }


def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    try:
        process = psutil.Process()
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "disk_percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent,
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else None,
            "threads": process.num_threads()
        }
    except Exception as e:
        return {"error": str(e)}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and model is loaded",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.
    Returns the API status and whether the ML model is loaded.
    """
    return HealthResponse(
        status="healthy",
        model_loaded=fraud_model.is_loaded,
        version=settings.app_version,
        timestamp=datetime.now(),
    )


@router.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Get detailed health status including all dependencies."
)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with dependency status.

    Checks:
    - API status
    - ML model status
    - Database connectivity
    - Redis connectivity (if configured)
    - System resources
    """
    db_status = check_database()
    redis_status = check_redis()
    system_metrics = get_system_metrics()

    # Determine overall status
    is_healthy = (
        fraud_model.is_loaded and
        db_status.get("status") == "healthy"
    )

    uptime_seconds = time.time() - STARTUP_TIME

    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": format_uptime(uptime_seconds),
        "components": {
            "api": {
                "status": "healthy",
                "version": settings.app_version
            },
            "ml_model": {
                "status": "healthy" if fraud_model.is_loaded else "unhealthy",
                "loaded": fraud_model.is_loaded,
                "type": fraud_model.model_info.get("model_type", "unknown") if fraud_model.is_loaded else None
            },
            "database": db_status,
            "redis": redis_status
        },
        "system": system_metrics,
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "debug_mode": settings.debug
        }
    }


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes."
)
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Returns 200 if the API is running.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Readiness check for Kubernetes - verifies all dependencies."
)
async def readiness_probe():
    """
    Kubernetes readiness probe.
    Returns 200 only if all critical dependencies are ready.
    """
    db_status = check_database()

    if db_status.get("status") != "healthy":
        return {"status": "not_ready", "reason": "database_unavailable"}

    if not fraud_model.is_loaded:
        return {"status": "not_ready", "reason": "model_not_loaded"}

    return {"status": "ready"}


@router.get(
    "/rate-limit",
    summary="Rate limit status",
    description="Get current rate limit status for your requests."
)
async def get_rate_limit_info(request: Request):
    """
    Get rate limit information for the current user/IP.

    Returns:
    - limit: Maximum requests allowed per minute
    - remaining: Requests remaining in current window
    - reset: Unix timestamp when the limit resets
    - reset_in_seconds: Seconds until limit reset
    """
    status = get_rate_limit_status(request)

    return {
        "rate_limit": status,
        "headers_info": {
            "X-RateLimit-Limit": "Maximum requests per window",
            "X-RateLimit-Remaining": "Requests remaining",
            "X-RateLimit-Reset": "Unix timestamp when limit resets",
            "Retry-After": "Seconds to wait (only on 429)"
        }
    }


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Get metrics in Prometheus format for monitoring."
)
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus exposition format.

    Includes:
    - API request counts
    - Response times
    - System resources
    - Model performance
    """
    system = get_system_metrics()
    uptime = time.time() - STARTUP_TIME

    # Basic Prometheus format metrics
    metrics = []

    # System metrics
    metrics.append(f"# HELP fraud_detection_uptime_seconds API uptime in seconds")
    metrics.append(f"# TYPE fraud_detection_uptime_seconds gauge")
    metrics.append(f'fraud_detection_uptime_seconds {uptime:.2f}')

    if "cpu_percent" in system:
        metrics.append(f"# HELP fraud_detection_cpu_percent CPU usage percentage")
        metrics.append(f"# TYPE fraud_detection_cpu_percent gauge")
        metrics.append(f'fraud_detection_cpu_percent {system["cpu_percent"]}')

    if "memory_percent" in system:
        metrics.append(f"# HELP fraud_detection_memory_percent Memory usage percentage")
        metrics.append(f"# TYPE fraud_detection_memory_percent gauge")
        metrics.append(f'fraud_detection_memory_percent {system["memory_percent"]}')

    if "memory_used_mb" in system:
        metrics.append(f"# HELP fraud_detection_memory_used_mb Memory used in MB")
        metrics.append(f"# TYPE fraud_detection_memory_used_mb gauge")
        metrics.append(f'fraud_detection_memory_used_mb {system["memory_used_mb"]}')

    # Model status
    metrics.append(f"# HELP fraud_detection_model_loaded Model loaded status (1=loaded, 0=not loaded)")
    metrics.append(f"# TYPE fraud_detection_model_loaded gauge")
    metrics.append(f'fraud_detection_model_loaded {1 if fraud_model.is_loaded else 0}')

    # Join with newlines
    return "\n".join(metrics) + "\n"


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
