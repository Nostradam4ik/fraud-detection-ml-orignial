"""
Fraud Detection API - Main Application

A machine learning-powered API for detecting fraudulent credit card transactions.
Built with FastAPI, scikit-learn, and modern Python best practices.

Author: Zhmuryk Andrii
LinkedIn: https://www.linkedin.com/in/andrii-zhmuryk-5a3a972b4/
Copyright (c) 2024 - All Rights Reserved
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .api import router
from .core.config import settings
from .core.rate_limit import limiter, RateLimitHeaderMiddleware, rate_limit_exceeded_handler, get_rate_limit_status
from .core.logging_config import setup_logging, RequestLogger
from .core.security_headers import SecurityHeadersMiddleware
from .models.ml_model import fraud_model
from .db.database import init_db

# Configure structured logging
setup_logging(
    log_level=settings.log_level,
    log_dir="logs",
    json_logs=not settings.debug  # JSON in production, colored in dev
)
logger = logging.getLogger(__name__)
request_logger = RequestLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logger.info("Starting Fraud Detection API...")

    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    # Get the backend directory path
    backend_dir = Path(__file__).parent.parent

    # Load ML model
    model_path = backend_dir / settings.model_path
    scaler_path = backend_dir / settings.scaler_path

    if model_path.exists() and scaler_path.exists():
        success = fraud_model.load(str(model_path), str(scaler_path))
        if success:
            logger.info("ML model loaded successfully")
        else:
            logger.warning("Failed to load ML model")
    else:
        logger.warning(
            f"Model files not found. Expected:\n"
            f"  - {model_path}\n"
            f"  - {scaler_path}\n"
            "Run 'python ml/train.py' to train the model."
        )

    yield

    # Shutdown
    logger.info("Shutting down Fraud Detection API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## Fraud Detection API

A machine learning-powered API for detecting fraudulent credit card transactions.

### Features
- **Real-time fraud detection** - Predict fraud probability in milliseconds
- **Batch processing** - Analyze multiple transactions at once
- **Model insights** - View feature importance and model performance
- **Statistics** - Track API usage and fraud rates

### Dataset
Trained on the [Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
dataset from Kaggle with 284,807 transactions.

### Tech Stack
- FastAPI + Python 3.11
- scikit-learn (Random Forest)
- Docker ready

### Author
**Zhmuryk Andrii** - [LinkedIn](https://www.linkedin.com/in/andrii-zhmuryk-5a3a972b4/)

Copyright (c) 2024 - All Rights Reserved
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add GZip compression middleware (compress responses > 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limit header middleware
app.add_middleware(RateLimitHeaderMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Batch-ID", "X-Total-Rows", "X-Fraud-Count", "X-Legitimate-Count", "Content-Disposition",
        "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"
    ],
)

# Include API routes
app.include_router(router, prefix=settings.api_v1_prefix)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000

    # Log the request
    request_logger.log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_ip=request.client.host if request.client else None
    )

    return response


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "author": "Zhmuryk Andrii",
        "linkedin": "https://www.linkedin.com/in/andrii-zhmuryk-5a3a972b4/",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
