"""
Admin Routes - Model Management, User Management, System Settings

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.config import settings
from ...db.database import get_db
from ...db.models import User, Prediction, AuditLog, ModelVersion, UserRole, AuditAction
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_admin, get_current_analyst
from ...services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== Model Management ==============

@router.get(
    "/models",
    summary="List all model versions",
    description="Get a list of all trained model versions. Requires admin access."
)
async def list_models(
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all model versions with their metrics"""
    models = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()

    return [
        {
            "id": m.id,
            "version": m.version,
            "model_type": m.model_type,
            "accuracy": m.accuracy,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "roc_auc": m.roc_auc,
            "training_samples": m.training_samples,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "notes": m.notes
        }
        for m in models
    ]


@router.get(
    "/models/active",
    summary="Get active model",
    description="Get the currently active model version."
)
async def get_active_model(
    current_user: UserResponse = Depends(get_current_analyst),
    db: Session = Depends(get_db)
) -> dict:
    """Get the currently active model"""
    model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()

    if not model:
        return {"message": "No active model found", "model": None}

    return {
        "id": model.id,
        "version": model.version,
        "model_type": model.model_type,
        "accuracy": model.accuracy,
        "precision": model.precision,
        "recall": model.recall,
        "f1_score": model.f1_score,
        "roc_auc": model.roc_auc,
        "training_samples": model.training_samples,
        "is_active": model.is_active,
        "model_path": model.model_path,
        "scaler_path": model.scaler_path,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "notes": model.notes
    }


@router.post(
    "/models/{model_id}/activate",
    summary="Activate a model version",
    description="Set a specific model version as the active model. Requires admin access."
)
async def activate_model(
    model_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Activate a specific model version"""
    # Find the model
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")

    # Deactivate all other models
    db.query(ModelVersion).update({"is_active": False})

    # Activate this model
    model.is_active = True
    db.commit()

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.SETTINGS_CHANGE,
        user_id=int(current_user.id),
        resource_type="model",
        resource_id=str(model_id),
        details={"action": "activate_model", "version": model.version},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"Model {model.version} activated successfully"}


# ============== User Management ==============

@router.get(
    "/users",
    summary="List all users",
    description="Get a list of all users. Requires admin access."
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all users with their details"""
    users = db.query(User).offset(skip).limit(limit).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value if u.role else "viewer",
            "is_active": u.is_active,
            "is_2fa_enabled": u.is_2fa_enabled,
            "is_email_verified": u.is_email_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        }
        for u in users
    ]


@router.patch(
    "/users/{user_id}/role",
    summary="Change user role",
    description="Change a user's role. Requires admin access."
)
async def change_user_role(
    user_id: int,
    role: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Change a user's role"""
    # Validate role
    valid_roles = ["admin", "analyst", "viewer"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-demotion
    if user.id == int(current_user.id) and role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

    old_role = user.role.value if user.role else "viewer"
    user.role = UserRole(role)
    db.commit()

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_UPDATE,
        user_id=int(current_user.id),
        resource_type="user",
        resource_id=str(user_id),
        details={"old_role": old_role, "new_role": role},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"User role changed to {role}"}


@router.patch(
    "/users/{user_id}/status",
    summary="Enable/disable user",
    description="Enable or disable a user account. Requires admin access."
)
async def change_user_status(
    user_id: int,
    is_active: bool,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Enable or disable a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deactivation
    if user.id == int(current_user.id) and not is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = is_active
    db.commit()

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_UPDATE,
        user_id=int(current_user.id),
        resource_type="user",
        resource_id=str(user_id),
        details={"action": "activate" if is_active else "deactivate"},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"User {'activated' if is_active else 'deactivated'}"}


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    description="Delete a user account. Requires admin access."
)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Delete a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion
    if user.id == int(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    username = user.username
    db.delete(user)
    db.commit()

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_DELETE,
        user_id=int(current_user.id),
        resource_type="user",
        resource_id=str(user_id),
        details={"deleted_username": username},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "User deleted successfully"}


# ============== Audit Logs ==============

@router.get(
    "/audit-logs",
    summary="Get audit logs",
    description="Get system audit logs. Requires admin access."
)
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get audit logs with optional filtering"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action.value if log.action else None,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


# ============== System Stats ==============

@router.get(
    "/stats",
    summary="Get system statistics",
    description="Get overall system statistics. Requires admin access."
)
async def get_system_stats(
    current_user: UserResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Get overall system statistics"""
    # User stats
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    admin_count = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar()

    # Prediction stats
    total_predictions = db.query(func.count(Prediction.id)).scalar()
    fraud_predictions = db.query(func.count(Prediction.id)).filter(Prediction.is_fraud == True).scalar()

    # Today's stats
    today = datetime.utcnow().date()
    today_predictions = db.query(func.count(Prediction.id)).filter(
        func.date(Prediction.created_at) == today
    ).scalar()

    # Model stats
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    total_models = db.query(func.count(ModelVersion.id)).scalar()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_count
        },
        "predictions": {
            "total": total_predictions,
            "fraud": fraud_predictions,
            "legitimate": total_predictions - fraud_predictions,
            "fraud_rate": fraud_predictions / total_predictions if total_predictions > 0 else 0,
            "today": today_predictions
        },
        "models": {
            "total": total_models,
            "active_version": active_model.version if active_model else None
        }
    }
