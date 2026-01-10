"""
Authentication Routes - Register, Login, 2FA, Profile Management

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...core.config import settings
from ...db.database import get_db
from ...db.models import AuditAction
from ...models.schemas import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    PasswordResetRequest,
    PasswordReset,
    PasswordResetResponse,
    RefreshTokenRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
)
from ...services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    create_user,
    get_current_user,
    get_user_by_email,
    create_password_reset_token,
    verify_reset_token,
    invalidate_reset_token,
    reset_user_password,
    enable_2fa,
    confirm_2fa,
    disable_2fa,
    verify_totp,
    validate_password_strength,
    get_password_strength_score,
)
from ...services.audit_service import log_action
from ...services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request"""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    return client_ip, user_agent


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password."
)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters, must include uppercase, lowercase, digit, special char)
    - **full_name**: Optional full name
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {error_message}"
        )

    user = create_user(db, user_data)

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.REGISTER,
        user_id=int(user.id),
        resource_type="user",
        resource_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access token",
    description="Authenticate with username/email and password to receive JWT tokens."
)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with username or email and password.

    Returns access and refresh tokens for API authentication.
    If 2FA is enabled, you must provide the TOTP code.
    """
    user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check 2FA if enabled
    if hasattr(user, 'is_2fa_enabled') and user.is_2fa_enabled:
        if not credentials.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required",
                headers={"X-2FA-Required": "true"},
            )

        if not verify_totp(user.totp_secret, credentials.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
            )

    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    # Create refresh token
    client_ip, user_agent = get_client_info(request)
    refresh_token = create_refresh_token(
        db, user.id,
        device_info=user_agent,
        ip_address=client_ip
    )

    # Log the action
    log_action(
        db, AuditAction.LOGIN,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token_endpoint(
    token_request: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh the access token using a refresh token.

    Use this endpoint to get a new access token before/after the current one expires.
    """
    user = verify_refresh_token(db, token_request.refresh_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old refresh token
    revoke_refresh_token(db, token_request.refresh_token)

    # Create new tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    client_ip, user_agent = get_client_info(request)
    new_refresh_token = create_refresh_token(
        db, user.id,
        device_info=user_agent,
        ip_address=client_ip
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post(
    "/logout",
    summary="Logout and revoke tokens",
    description="Revoke the current refresh token."
)
async def logout(
    token_request: RefreshTokenRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout and revoke the refresh token."""
    revoke_refresh_token(db, token_request.refresh_token)

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.LOGOUT,
        user_id=int(current_user.id),
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "Logged out successfully"}


@router.post(
    "/logout-all",
    summary="Logout from all devices",
    description="Revoke all refresh tokens for the current user."
)
async def logout_all(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all devices by revoking all refresh tokens."""
    count = revoke_all_user_tokens(db, int(current_user.id))

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.LOGOUT,
        user_id=int(current_user.id),
        details={"all_devices": True, "tokens_revoked": count},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"Logged out from {count} device(s)"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user."
)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


# ============== 2FA Endpoints ==============

@router.post(
    "/2fa/setup",
    response_model=TwoFactorSetupResponse,
    summary="Setup two-factor authentication",
    description="Generate a TOTP secret and QR code for 2FA setup."
)
async def setup_2fa(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup 2FA for the current user.

    Returns a secret key and QR code. Scan the QR code with an authenticator app
    like Google Authenticator or Authy.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )

    secret, qr_code = enable_2fa(db, int(current_user.id))

    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=qr_code,
        message="Scan the QR code with your authenticator app, then verify with /2fa/verify"
    )


@router.post(
    "/2fa/verify",
    summary="Verify and enable 2FA",
    description="Verify the TOTP code to enable 2FA."
)
async def verify_2fa(
    verify_request: TwoFactorVerifyRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify TOTP code and enable 2FA.

    Enter the 6-digit code from your authenticator app to complete 2FA setup.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )

    if confirm_2fa(db, int(current_user.id), verify_request.code):
        # Log the action
        client_ip, user_agent = get_client_info(request)
        log_action(
            db, AuditAction.ENABLE_2FA,
            user_id=int(current_user.id),
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Send confirmation email
        EmailService.send_2fa_enabled_email(current_user.email, current_user.username)

        return {"message": "2FA enabled successfully"}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid verification code"
    )


@router.post(
    "/2fa/disable",
    summary="Disable 2FA",
    description="Disable two-factor authentication (requires password confirmation)."
)
async def disable_2fa_endpoint(
    disable_request: TwoFactorDisableRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA for the current user.

    Requires password confirmation for security.
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )

    if disable_2fa(db, int(current_user.id), disable_request.password):
        # Log the action
        client_ip, user_agent = get_client_info(request)
        log_action(
            db, AuditAction.DISABLE_2FA,
            user_id=int(current_user.id),
            ip_address=client_ip,
            user_agent=user_agent
        )

        return {"message": "2FA disabled successfully"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid password"
    )


# ============== Password Reset Endpoints ==============

@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
    summary="Request password reset",
    description="Request a password reset token. In production, this sends an email."
)
async def forgot_password(
    password_request: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request a password reset.

    In production, this sends an email with the reset link.
    For demo purposes, it returns the token directly.
    """
    user = get_user_by_email(db, password_request.email)

    if not user:
        # For security, don't reveal if email exists
        return PasswordResetResponse(
            message="If an account with this email exists, a reset link has been sent.",
            reset_token=None
        )

    # Generate reset token
    token = create_password_reset_token(password_request.email)

    # Try to send email
    EmailService.send_password_reset_email(user.email, token, user.username)

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.PASSWORD_RESET,
        user_id=user.id,
        details={"action": "requested"},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return PasswordResetResponse(
        message="Password reset token generated. Use it within 15 minutes.",
        reset_token=token  # Only for demo - remove in production!
    )


@router.post(
    "/reset-password",
    summary="Reset password with token",
    description="Reset password using the token from forgot-password."
)
async def reset_password(
    reset_request: PasswordReset,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid reset token.
    """
    email = verify_reset_token(reset_request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    success = reset_user_password(db, email, reset_request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )

    # Invalidate token after use
    invalidate_reset_token(reset_request.token)

    # Log the action
    user = get_user_by_email(db, email)
    if user:
        client_ip, user_agent = get_client_info(request)
        log_action(
            db, AuditAction.PASSWORD_RESET,
            user_id=user.id,
            details={"action": "completed"},
            ip_address=client_ip,
            user_agent=user_agent
        )

    return {"message": "Password reset successfully. You can now login with your new password."}


# ============== Password Change Endpoint ==============

@router.post(
    "/change-password",
    summary="Change password",
    description="Change the current user's password."
)
async def change_password(
    password_data: dict,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for the authenticated user.
    Requires current password verification.
    """
    from ...db.models import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both current and new password are required"
        )

    # Verify current password
    user = db.query(User).filter(User.id == int(current_user.id)).first()
    if not user or not pwd_context.verify(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {error_message}"
        )

    # Update password
    user.hashed_password = pwd_context.hash(new_password)
    db.commit()

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.PASSWORD_RESET,
        user_id=int(current_user.id),
        details={"action": "changed"},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "Password changed successfully"}


@router.post(
    "/password-strength",
    summary="Check password strength",
    description="Check the strength of a password without saving it."
)
async def check_password_strength(password_data: dict):
    """
    Check password strength and get feedback.
    Returns a score (0-100), level, and suggestions.
    """
    password = password_data.get("password", "")

    if not password:
        return {
            "score": 0,
            "level": "weak",
            "feedback": ["Enter a password"],
            "is_valid": False,
            "error": None
        }

    strength = get_password_strength_score(password)
    is_valid, error = validate_password_strength(password)

    return {
        **strength,
        "is_valid": is_valid,
        "error": error if not is_valid else None
    }


# ============== Sessions Endpoints ==============

@router.get(
    "/sessions",
    summary="Get active sessions",
    description="Get all active sessions for the current user."
)
async def get_sessions(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active (non-revoked) sessions for the current user."""
    from ...db.models import RefreshToken
    from datetime import datetime

    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == int(current_user.id),
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
        .order_by(RefreshToken.created_at.desc())
        .all()
    )

    # Get current token from request (would need to implement this properly)
    sessions = []
    for token in tokens:
        sessions.append({
            "id": token.id,
            "device_info": token.device_info or "Unknown Device",
            "ip_address": token.ip_address or "Unknown",
            "created_at": token.created_at.isoformat() if token.created_at else None,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "is_current": False  # Would need to compare with current token
        })

    return sessions


@router.delete(
    "/sessions/{session_id}",
    summary="Revoke a session",
    description="Revoke a specific session by its ID."
)
async def revoke_session_endpoint(
    session_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session."""
    from ...db.models import RefreshToken
    from datetime import datetime

    token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == int(current_user.id)
        )
        .first()
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    token.is_revoked = True
    token.revoked_at = datetime.utcnow()
    db.commit()

    # Log the action
    client_ip, user_agent = get_client_info(request)
    log_action(
        db, AuditAction.LOGOUT,
        user_id=int(current_user.id),
        details={"session_id": session_id, "action": "revoked"},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "Session revoked successfully"}


# ============== Data Export Endpoint (GDPR) ==============

@router.get(
    "/export-data",
    summary="Export user data",
    description="Export all user data (GDPR compliant)."
)
async def export_user_data(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all data for the current user (GDPR compliance)."""
    from ...db.models import User, Prediction, AuditLog, EmailAlert
    import json

    user_id = int(current_user.id)

    # Get user profile
    user = db.query(User).filter(User.id == user_id).first()

    # Get predictions
    predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()

    # Get audit logs
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).limit(1000).all()

    # Get alerts
    alerts = db.query(EmailAlert).filter(EmailAlert.user_id == user_id).all()

    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "profile": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": str(user.role.value) if user.role else None,
            "is_active": user.is_active,
            "is_2fa_enabled": user.is_2fa_enabled,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        },
        "predictions": [
            {
                "id": p.id,
                "amount": p.amount,
                "is_fraud": p.is_fraud,
                "fraud_probability": p.fraud_probability,
                "risk_score": p.risk_score,
                "confidence": p.confidence,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in predictions
        ],
        "activity_logs": [
            {
                "action": str(log.action.value) if log.action else None,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in audit_logs
        ],
        "alerts": [
            {
                "email": alert.email,
                "alert_type": alert.alert_type,
                "threshold": alert.threshold,
                "is_active": alert.is_active
            }
            for alert in alerts
        ]
    }

    return export_data
