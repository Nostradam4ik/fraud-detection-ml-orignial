"""
Database Models - SQLAlchemy ORM Models

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Enum, Table
from sqlalchemy.orm import relationship

from .database import Base


# ============== Enums ==============

class UserRole(str, PyEnum):
    """User roles for access control"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AuditAction(str, PyEnum):
    """Audit log action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    PREDICTION = "prediction"
    BATCH_PREDICTION = "batch_prediction"
    MODEL_RETRAIN = "model_retrain"
    SETTINGS_CHANGE = "settings_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    EXPORT_DATA = "export_data"
    ENABLE_2FA = "enable_2fa"
    DISABLE_2FA = "disable_2fa"


# ============== Association Tables ==============

team_members = Table(
    'team_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow)
)


# ============== Models ==============

class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)

    # 2FA fields
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)

    # Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    teams = relationship("Team", secondary=team_members, back_populates="members")
    owned_teams = relationship("Team", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class RefreshToken(Base):
    """Refresh token model for JWT refresh"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    # Device info for security
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class Prediction(Base):
    """Prediction history model"""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction data
    time = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

    # PCA features stored as JSON string
    features_json = Column(Text, nullable=False)

    # Prediction results
    is_fraud = Column(Boolean, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    confidence = Column(String(20), nullable=False)
    risk_score = Column(Integer, nullable=False)
    prediction_time_ms = Column(Float, nullable=False)

    # SHAP explanations (JSON)
    shap_values = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String(36), nullable=True, index=True)  # UUID for batch predictions

    # Relationship to user
    user = relationship("User", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(id={self.id}, is_fraud={self.is_fraud}, probability={self.fraud_probability})>"


class AuditLog(Base):
    """Audit log for tracking user actions"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous actions
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=True)  # e.g., "prediction", "user", "model"
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)  # JSON string with additional details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"


class Team(Base):
    """Team model for collaborative work"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=team_members, back_populates="teams")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"


class EmailAlert(Base):
    """Email alert configuration"""

    __tablename__ = "email_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)  # "fraud_detected", "daily_report", "weekly_report"
    threshold = Column(Float, nullable=True)  # For fraud alerts: minimum probability
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EmailAlert(id={self.id}, user_id={self.user_id}, type='{self.alert_type}')>"


class Webhook(Base):
    """Webhook configuration for external notifications"""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=True)  # For signature verification
    event_types = Column(Text, nullable=False)  # JSON array: ["fraud_detected", "high_risk", "batch_complete"]
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    last_status_code = Column(Integer, nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url[:30]}...')>"


class ModelVersion(Base):
    """Model version tracking"""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)  # "random_forest", "xgboost", "neural_network"
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    training_samples = Column(Integer, nullable=False)
    model_path = Column(String(255), nullable=False)
    scaler_path = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)
    trained_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ModelVersion(version='{self.version}', type='{self.model_type}', active={self.is_active})>"
