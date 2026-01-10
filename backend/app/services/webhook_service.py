"""
Webhook Service - Send notifications to external URLs

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
import hmac
import hashlib
import logging
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.models import Webhook

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing and triggering webhooks"""

    VALID_EVENTS = [
        "fraud_detected",
        "high_risk",
        "batch_complete",
        "prediction_made",
        "threshold_exceeded"
    ]

    @staticmethod
    def create_webhook(
        db: Session,
        user_id: int,
        name: str,
        url: str,
        event_types: List[str],
        secret: Optional[str] = None
    ) -> Webhook:
        """Create a new webhook configuration"""
        # Validate event types
        invalid_events = [e for e in event_types if e not in WebhookService.VALID_EVENTS]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")

        webhook = Webhook(
            user_id=user_id,
            name=name,
            url=url,
            secret=secret,
            event_types=json.dumps(event_types),
            is_active=True
        )

        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        return webhook

    @staticmethod
    def get_user_webhooks(db: Session, user_id: int) -> List[Webhook]:
        """Get all webhooks for a user"""
        return db.query(Webhook).filter(
            Webhook.user_id == user_id
        ).order_by(desc(Webhook.created_at)).all()

    @staticmethod
    def get_webhook(db: Session, webhook_id: int, user_id: int) -> Optional[Webhook]:
        """Get a specific webhook"""
        return db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.user_id == user_id
        ).first()

    @staticmethod
    def update_webhook(
        db: Session,
        webhook: Webhook,
        name: Optional[str] = None,
        url: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        secret: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Webhook:
        """Update a webhook"""
        if name is not None:
            webhook.name = name
        if url is not None:
            webhook.url = url
        if event_types is not None:
            invalid_events = [e for e in event_types if e not in WebhookService.VALID_EVENTS]
            if invalid_events:
                raise ValueError(f"Invalid event types: {invalid_events}")
            webhook.event_types = json.dumps(event_types)
        if secret is not None:
            webhook.secret = secret
        if is_active is not None:
            webhook.is_active = is_active

        db.commit()
        db.refresh(webhook)

        return webhook

    @staticmethod
    def delete_webhook(db: Session, webhook: Webhook) -> None:
        """Delete a webhook"""
        db.delete(webhook)
        db.commit()

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def trigger_webhook(
        db: Session,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Trigger a webhook with the given payload"""
        if not webhook.is_active:
            return False

        # Check if webhook subscribes to this event
        subscribed_events = json.loads(webhook.event_types)
        if event_type not in subscribed_events:
            return False

        # Prepare payload
        full_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }
        payload_str = json.dumps(full_payload)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat()
        }

        # Add signature if secret is configured
        if webhook.secret:
            signature = WebhookService.generate_signature(payload_str, webhook.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_str,
                    headers=headers
                )

            # Update webhook status
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_status_code = response.status_code

            if response.is_success:
                webhook.failure_count = 0
                db.commit()
                logger.info(f"Webhook {webhook.id} triggered successfully: {response.status_code}")
                return True
            else:
                webhook.failure_count += 1
                db.commit()
                logger.warning(f"Webhook {webhook.id} failed: {response.status_code}")
                return False

        except Exception as e:
            webhook.last_triggered_at = datetime.utcnow()
            webhook.failure_count += 1
            db.commit()
            logger.error(f"Webhook {webhook.id} error: {str(e)}")
            return False

    @staticmethod
    async def trigger_webhooks_for_event(
        db: Session,
        user_id: int,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, int]:
        """Trigger all user webhooks for a specific event"""
        webhooks = db.query(Webhook).filter(
            Webhook.user_id == user_id,
            Webhook.is_active == True
        ).all()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for webhook in webhooks:
            subscribed_events = json.loads(webhook.event_types)
            if event_type not in subscribed_events:
                results["skipped"] += 1
                continue

            success = await WebhookService.trigger_webhook(db, webhook, event_type, payload)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        return results

    @staticmethod
    async def test_webhook(db: Session, webhook: Webhook) -> Dict[str, Any]:
        """Send a test payload to webhook"""
        test_payload = {
            "test": True,
            "message": "This is a test webhook from Fraud Detection System",
            "webhook_id": webhook.id,
            "webhook_name": webhook.name
        }

        success = await WebhookService.trigger_webhook(
            db, webhook, "test", test_payload
        )

        return {
            "success": success,
            "status_code": webhook.last_status_code,
            "message": "Test webhook sent successfully" if success else "Test webhook failed"
        }
