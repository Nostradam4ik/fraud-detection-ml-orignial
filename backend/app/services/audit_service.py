"""
Audit Service - Logging and tracking user actions

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.models import AuditLog, AuditAction, User


def log_action(
    db: Session,
    action: AuditAction,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """Log an action to the audit log"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """Get audit logs with optional filters"""
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if action is not None:
        try:
            action_enum = AuditAction(action)
            query = query.filter(AuditLog.action == action_enum)
        except ValueError:
            pass

    if start_date is not None:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date is not None:
        query = query.filter(AuditLog.created_at <= end_date)

    return query.order_by(desc(AuditLog.created_at)).limit(limit).all()


def get_user_activity(db: Session, user_id: int, limit: int = 50) -> List[AuditLog]:
    """Get recent activity for a specific user"""
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(desc(AuditLog.created_at)).limit(limit).all()


def get_action_count(
    db: Session,
    action: AuditAction,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None
) -> int:
    """Count occurrences of a specific action"""
    query = db.query(AuditLog).filter(AuditLog.action == action)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if start_date is not None:
        query = query.filter(AuditLog.created_at >= start_date)

    return query.count()
