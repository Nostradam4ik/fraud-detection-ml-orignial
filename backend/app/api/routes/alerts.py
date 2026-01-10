"""
Email Alerts Routes - Manage email notification preferences

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import EmailAlert
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/alerts", tags=["Email Alerts"])


@router.get(
    "",
    summary="Get user's email alerts",
    description="Get all email alert configurations for the current user."
)
async def list_alerts(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all email alerts for the current user"""
    alerts = db.query(EmailAlert).filter(
        EmailAlert.user_id == int(current_user.id)
    ).all()

    return [
        {
            "id": a.id,
            "email": a.email,
            "alert_type": a.alert_type,
            "threshold": a.threshold,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in alerts
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create email alert",
    description="Create a new email alert configuration."
)
async def create_alert(
    email: str,
    alert_type: str,
    threshold: float = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Create a new email alert.

    Alert types:
    - fraud_detected: Alert when fraud is detected (threshold = minimum probability)
    - high_risk: Alert for high-risk transactions (threshold = minimum risk score)
    - daily_report: Daily summary report
    - weekly_report: Weekly summary report
    """
    valid_types = ["fraud_detected", "high_risk", "daily_report", "weekly_report"]
    if alert_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid alert type. Must be one of: {', '.join(valid_types)}"
        )

    # Check for duplicate
    existing = db.query(EmailAlert).filter(
        EmailAlert.user_id == int(current_user.id),
        EmailAlert.email == email,
        EmailAlert.alert_type == alert_type
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Alert already exists")

    alert = EmailAlert(
        user_id=int(current_user.id),
        email=email,
        alert_type=alert_type,
        threshold=threshold,
        is_active=True
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "email": alert.email,
        "alert_type": alert.alert_type,
        "threshold": alert.threshold,
        "is_active": alert.is_active,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }


@router.patch(
    "/{alert_id}",
    summary="Update email alert",
    description="Update an email alert configuration."
)
async def update_alert(
    alert_id: int,
    email: str = None,
    threshold: float = None,
    is_active: bool = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update an email alert"""
    alert = db.query(EmailAlert).filter(
        EmailAlert.id == alert_id,
        EmailAlert.user_id == int(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if email is not None:
        alert.email = email
    if threshold is not None:
        alert.threshold = threshold
    if is_active is not None:
        alert.is_active = is_active

    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "email": alert.email,
        "alert_type": alert.alert_type,
        "threshold": alert.threshold,
        "is_active": alert.is_active,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
    }


@router.delete(
    "/{alert_id}",
    summary="Delete email alert",
    description="Delete an email alert configuration."
)
async def delete_alert(
    alert_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete an email alert"""
    alert = db.query(EmailAlert).filter(
        EmailAlert.id == alert_id,
        EmailAlert.user_id == int(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()

    return {"message": "Alert deleted successfully"}


@router.post(
    "/test/{alert_id}",
    summary="Test email alert",
    description="Send a test email for an alert configuration."
)
async def test_alert(
    alert_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Send a test email for an alert"""
    from ...services.email_service import EmailService

    alert = db.query(EmailAlert).filter(
        EmailAlert.id == alert_id,
        EmailAlert.user_id == int(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Send test email based on alert type
    success = EmailService.send_test_alert_email(
        alert.email,
        alert.alert_type,
        current_user.username
    )

    if success:
        return {"message": "Test email sent successfully"}
    else:
        return {"message": "Test email queued (SMTP not configured)"}
