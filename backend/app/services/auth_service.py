"""
Authentication Service - JWT Token Management, 2FA, and User Authentication

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import secrets
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.database import get_db
from ..db.models import User, RefreshToken, UserRole
from ..models.schemas import TokenData, UserCreate, UserResponse

# HTTP Bearer token scheme
security = HTTPBearer()

# Try to import optional 2FA dependencies
try:
    import pyotp
    import qrcode
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=4)
    ).decode('utf-8')


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength against security policies.

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    errors = []

    # Minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    # Maximum length (prevent DoS)
    if len(password) > 128:
        errors.append("Password must not exceed 128 characters")

    # Must contain uppercase
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    # Must contain lowercase
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    # Must contain digit
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    # Must contain special character
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character (!@#$%^&*...)")

    # Check for common patterns
    common_passwords = [
        "password", "123456", "qwerty", "admin", "letmein",
        "welcome", "monkey", "dragon", "master", "login"
    ]
    if password.lower() in common_passwords:
        errors.append("Password is too common")

    if errors:
        return False, "; ".join(errors)

    return True, ""


def get_password_strength_score(password: str) -> Dict:
    """
    Calculate password strength score for UI display.

    Returns:
        Dict with score (0-100) and feedback
    """
    score = 0
    feedback = []

    # Length scoring
    if len(password) >= 8:
        score += 15
    if len(password) >= 12:
        score += 15
    if len(password) >= 16:
        score += 10

    # Character variety
    if any(c.isupper() for c in password):
        score += 15
    else:
        feedback.append("Add uppercase letters")

    if any(c.islower() for c in password):
        score += 10
    else:
        feedback.append("Add lowercase letters")

    if any(c.isdigit() for c in password):
        score += 15
    else:
        feedback.append("Add numbers")

    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if any(c in special_chars for c in password):
        score += 20
    else:
        feedback.append("Add special characters")

    # Bonus for variety
    unique_chars = len(set(password))
    if unique_chars >= 8:
        score += min(10, unique_chars - 7)

    # Determine strength level
    if score >= 80:
        level = "strong"
    elif score >= 60:
        level = "good"
    elif score >= 40:
        level = "fair"
    else:
        level = "weak"

    return {
        "score": min(100, score),
        "level": level,
        "feedback": feedback
    }


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def create_refresh_token(
    db: Session,
    user_id: int,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
) -> str:
    """Create a refresh token and store it in database"""
    # Generate unique token
    token = secrets.token_urlsafe(64)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    # Create token record
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address
    )

    db.add(refresh_token)
    db.commit()

    return token


def verify_refresh_token(db: Session, token: str) -> Optional[User]:
    """Verify a refresh token and return the associated user"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.is_revoked == False
    ).first()

    if not refresh_token:
        return None

    # Check expiration
    if datetime.utcnow() > refresh_token.expires_at:
        # Mark as revoked
        refresh_token.is_revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        db.commit()
        return None

    return refresh_token.user


def revoke_refresh_token(db: Session, token: str) -> bool:
    """Revoke a refresh token"""
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()

    if not refresh_token:
        return False

    refresh_token.is_revoked = True
    refresh_token.revoked_at = datetime.utcnow()
    db.commit()

    return True


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user"""
    result = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.utcnow()
    })

    db.commit()
    return result


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("type", "access")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing username",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(username=username, user_id=user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username from database"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email from database"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID from database"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate, role: UserRole = UserRole.VIEWER) -> UserResponse:
    """Create a new user in database"""
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        role=role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse(
        id=str(db_user.id),
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        role=db_user.role.value if db_user.role else "viewer",
        is_2fa_enabled=db_user.is_2fa_enabled if hasattr(db_user, 'is_2fa_enabled') else False,
        created_at=db_user.created_at
    )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username/email and password"""
    # Try to find by username
    user = get_user_by_username(db, username)

    # If not found, try by email
    if not user:
        user = get_user_by_email(db, username)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    token_data = decode_token(token)

    user = get_user_by_username(db, token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role.value if user.role else "viewer",
        is_2fa_enabled=user.is_2fa_enabled if hasattr(user, 'is_2fa_enabled') else False,
        created_at=user.created_at
    )


# Role-based access control
async def get_current_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_analyst(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require analyst or admin role"""
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required"
        )
    return current_user


# Optional: Get current user (returns None if not authenticated)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise return None"""
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        token_data = decode_token(token)
        user = get_user_by_username(db, token_data.username)

        if user and user.is_active:
            return UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                role=user.role.value if user.role else "viewer",
                is_2fa_enabled=user.is_2fa_enabled if hasattr(user, 'is_2fa_enabled') else False,
                created_at=user.created_at
            )
    except HTTPException:
        pass

    return None


# ============== 2FA (TOTP) ==============

def generate_totp_secret() -> str:
    """Generate a new TOTP secret"""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA not available. Install pyotp and qrcode.")
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    """Generate TOTP URI for QR code"""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA not available")
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=settings.totp_issuer)


def generate_qr_code(uri: str) -> str:
    """Generate QR code as base64 string"""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA not available")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code"""
    if not TOTP_AVAILABLE:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 1 step window for clock drift


def enable_2fa(db: Session, user_id: int) -> Tuple[str, str]:
    """Enable 2FA for a user, returns (secret, qr_code_base64)"""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA not available. Install pyotp and qrcode.")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate new secret
    secret = generate_totp_secret()

    # Store secret (but don't enable yet - need verification first)
    user.totp_secret = secret
    db.commit()

    # Generate QR code
    uri = get_totp_uri(secret, user.username)
    qr_code = generate_qr_code(uri)

    return secret, qr_code


def confirm_2fa(db: Session, user_id: int, code: str) -> bool:
    """Confirm 2FA setup by verifying the first code"""
    user = get_user_by_id(db, user_id)
    if not user or not user.totp_secret:
        return False

    if verify_totp(user.totp_secret, code):
        user.is_2fa_enabled = True
        db.commit()
        return True

    return False


def disable_2fa(db: Session, user_id: int, password: str) -> bool:
    """Disable 2FA for a user (requires password confirmation)"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    user.is_2fa_enabled = False
    user.totp_secret = None
    db.commit()

    return True


# ============== Password Reset ==============

# In-memory storage for reset tokens (in production, use Redis or database)
_reset_tokens: Dict[str, dict] = {}


def create_password_reset_token(email: str) -> Optional[str]:
    """Create a password reset token for an email"""
    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Store token with expiration (15 minutes)
    _reset_tokens[token] = {
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(minutes=15)
    }

    return token


def verify_reset_token(token: str) -> Optional[str]:
    """Verify a reset token and return the associated email"""
    if token not in _reset_tokens:
        return None

    token_data = _reset_tokens[token]

    # Check expiration
    if datetime.utcnow() > token_data["expires_at"]:
        # Token expired, remove it
        del _reset_tokens[token]
        return None

    return token_data["email"]


def invalidate_reset_token(token: str) -> None:
    """Invalidate a reset token after use"""
    if token in _reset_tokens:
        del _reset_tokens[token]


def reset_user_password(db: Session, email: str, new_password: str) -> bool:
    """Reset user password by email"""
    user = get_user_by_email(db, email)

    if not user:
        return False

    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()

    # Revoke all refresh tokens for security
    revoke_all_user_tokens(db, user.id)

    db.commit()
    return True
