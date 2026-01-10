"""
Webhook Routes - Manage webhook configurations

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Webhook
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user
from ...services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookCreate(BaseModel):
    name: str
    url: str
    event_types: List[str]
    secret: Optional[str] = None


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    event_types: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    event_types: List[str]
    is_active: bool
    last_triggered_at: Optional[str]
    last_status_code: Optional[int]
    failure_count: int
    created_at: str

    class Config:
        from_attributes = True


def webhook_to_response(webhook: Webhook) -> dict:
    """Convert Webhook model to response dict"""
    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "event_types": json.loads(webhook.event_types),
        "is_active": webhook.is_active,
        "last_triggered_at": webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
        "last_status_code": webhook.last_status_code,
        "failure_count": webhook.failure_count,
        "created_at": webhook.created_at.isoformat() if webhook.created_at else None
    }


@router.get(
    "",
    summary="List webhooks",
    description="Get all webhook configurations for the current user."
)
async def list_webhooks(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all webhooks for the current user"""
    webhooks = WebhookService.get_user_webhooks(db, int(current_user.id))
    return [webhook_to_response(w) for w in webhooks]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook",
    description="Create a new webhook configuration."
)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Create a new webhook.

    Event types:
    - fraud_detected: Triggered when fraud is detected
    - high_risk: Triggered for high-risk transactions (risk_score > 70)
    - batch_complete: Triggered when batch processing completes
    - prediction_made: Triggered for every prediction
    - threshold_exceeded: Triggered when custom threshold is exceeded
    """
    try:
        webhook = WebhookService.create_webhook(
            db=db,
            user_id=int(current_user.id),
            name=webhook_data.name,
            url=webhook_data.url,
            event_types=webhook_data.event_types,
            secret=webhook_data.secret
        )
        return webhook_to_response(webhook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/events",
    summary="List available events",
    description="Get list of available webhook event types."
)
async def list_events() -> dict:
    """Get available webhook events"""
    return {
        "events": [
            {
                "type": "fraud_detected",
                "description": "Triggered when a transaction is classified as fraud"
            },
            {
                "type": "high_risk",
                "description": "Triggered for transactions with risk score > 70%"
            },
            {
                "type": "batch_complete",
                "description": "Triggered when batch prediction processing completes"
            },
            {
                "type": "prediction_made",
                "description": "Triggered for every prediction made"
            },
            {
                "type": "threshold_exceeded",
                "description": "Triggered when a custom threshold is exceeded"
            }
        ]
    }


@router.get(
    "/{webhook_id}",
    summary="Get webhook",
    description="Get a specific webhook configuration."
)
async def get_webhook(
    webhook_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get a specific webhook"""
    webhook = WebhookService.get_webhook(db, webhook_id, int(current_user.id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook_to_response(webhook)


@router.patch(
    "/{webhook_id}",
    summary="Update webhook",
    description="Update a webhook configuration."
)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update a webhook"""
    webhook = WebhookService.get_webhook(db, webhook_id, int(current_user.id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    try:
        updated = WebhookService.update_webhook(
            db=db,
            webhook=webhook,
            name=webhook_data.name,
            url=webhook_data.url,
            event_types=webhook_data.event_types,
            secret=webhook_data.secret,
            is_active=webhook_data.is_active
        )
        return webhook_to_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{webhook_id}",
    summary="Delete webhook",
    description="Delete a webhook configuration."
)
async def delete_webhook(
    webhook_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete a webhook"""
    webhook = WebhookService.get_webhook(db, webhook_id, int(current_user.id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    WebhookService.delete_webhook(db, webhook)
    return {"message": "Webhook deleted successfully"}


@router.post(
    "/{webhook_id}/test",
    summary="Test webhook",
    description="Send a test payload to the webhook URL."
)
async def test_webhook(
    webhook_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Test a webhook by sending a test payload"""
    webhook = WebhookService.get_webhook(db, webhook_id, int(current_user.id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await WebhookService.test_webhook(db, webhook)
    return result


@router.post(
    "/{webhook_id}/toggle",
    summary="Toggle webhook",
    description="Enable or disable a webhook."
)
async def toggle_webhook(
    webhook_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Toggle webhook active state"""
    webhook = WebhookService.get_webhook(db, webhook_id, int(current_user.id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook.is_active = not webhook.is_active
    db.commit()
    db.refresh(webhook)

    return {
        "id": webhook.id,
        "is_active": webhook.is_active,
        "message": f"Webhook {'enabled' if webhook.is_active else 'disabled'}"
    }
