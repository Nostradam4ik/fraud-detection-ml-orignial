"""API Routes"""

from fastapi import APIRouter

from .prediction import router as prediction_router
from .analytics import router as analytics_router
from .health import router as health_router
from .auth import router as auth_router
from .admin import router as admin_router
from .teams import router as teams_router
from .alerts import router as alerts_router
from .reports import router as reports_router
from .websocket import router as websocket_router
from .webhooks import router as webhooks_router
from .api_keys import router as api_keys_router
from .fraud_network import router as fraud_network_router
from .explainer import router as explainer_router
from .forecast import router as forecast_router
from .simulation import router as simulation_router
from .geo_velocity import router as geo_velocity_router
from .device_fingerprint import router as device_fingerprint_router
from .feedback import router as feedback_router

router = APIRouter()

# Include all route modules
router.include_router(auth_router)  # Authentication routes
router.include_router(prediction_router, prefix="/predict", tags=["Predictions"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
router.include_router(health_router, tags=["Health"])
router.include_router(admin_router)  # Admin routes (has own prefix)
router.include_router(teams_router)  # Team management routes (has own prefix)
router.include_router(alerts_router)  # Email alerts routes (has own prefix)
router.include_router(reports_router)  # PDF reports routes (has own prefix)
router.include_router(websocket_router)  # WebSocket routes
router.include_router(webhooks_router)  # Webhook routes (has own prefix)
router.include_router(api_keys_router)  # API keys routes (has own prefix)
router.include_router(fraud_network_router)  # Fraud network graph (has own prefix)
router.include_router(explainer_router)  # AI Fraud Explainer (has own prefix)
router.include_router(forecast_router)  # Risk Forecast (has own prefix)
router.include_router(simulation_router)  # Fraud Simulation Lab (has own prefix)
router.include_router(geo_velocity_router)  # Geo-Velocity Tracker (has own prefix)
router.include_router(device_fingerprint_router)  # Device Fingerprint Analyzer (has own prefix)
router.include_router(feedback_router)  # ML Feedback & Retraining (has own prefix)
