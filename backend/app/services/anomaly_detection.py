"""Real-time anomaly detection and alerting service"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import deque
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text

from app.db.database import Base

logger = logging.getLogger(__name__)


class AnomalyAlert(Base):
    """Store detected anomalies and alerts"""
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    anomaly_type = Column(String(50), nullable=False)  # "velocity", "amount_spike", "pattern_change"
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"

    description = Column(Text, nullable=False)
    anomaly_score = Column(Float, nullable=False)

    # Related data
    related_transaction_ids = Column(Text, nullable=True)  # JSON array of IDs
    affected_features = Column(Text, nullable=True)  # JSON array of feature names

    # Alert status
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnomalyDetector:
    """
    Real-time anomaly detection system

    Monitors transactions for:
    - Transaction velocity anomalies
    - Amount spikes
    - Pattern changes
    - Geographic anomalies
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size

        # Store recent transactions per user (in-memory cache)
        self.user_transactions: Dict[int, deque] = {}

        # Global statistics
        self.global_amount_mean = 0.0
        self.global_amount_std = 1.0

    def update_global_stats(self, db: Session):
        """Update global transaction statistics"""
        try:
            from app.db.models import Prediction

            # Get recent predictions
            recent = db.query(Prediction).order_by(
                Prediction.created_at.desc()
            ).limit(1000).all()

            if not recent:
                return

            amounts = [p.amount for p in recent if p.amount is not None]
            if amounts:
                self.global_amount_mean = np.mean(amounts)
                self.global_amount_std = np.std(amounts)

            logger.info(f"Updated global stats: mean={self.global_amount_mean:.2f}, std={self.global_amount_std:.2f}")

        except Exception as e:
            logger.error(f"Failed to update global stats: {e}")

    def add_transaction(self, user_id: int, transaction: Dict[str, Any]):
        """Add a transaction to user's history"""
        if user_id not in self.user_transactions:
            self.user_transactions[user_id] = deque(maxlen=self.window_size)

        self.user_transactions[user_id].append({
            "timestamp": datetime.utcnow(),
            "amount": transaction.get("amount", 0),
            "fraud_probability": transaction.get("fraud_probability", 0),
            "is_fraud": transaction.get("is_fraud", False)
        })

    def detect_velocity_anomaly(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Detect unusual transaction velocity

        Returns anomaly details if detected, None otherwise
        """
        if user_id not in self.user_transactions:
            return None

        transactions = list(self.user_transactions[user_id])
        if len(transactions) < 5:
            return None

        # Check transactions in last 10 minutes
        now = datetime.utcnow()
        recent = [
            t for t in transactions
            if (now - t["timestamp"]).total_seconds() < 600
        ]

        if len(recent) >= 5:
            # High velocity detected
            return {
                "anomaly_type": "velocity",
                "severity": "high" if len(recent) >= 10 else "medium",
                "description": f"{len(recent)} transactions in 10 minutes",
                "anomaly_score": min(len(recent) / 20.0, 1.0),
                "transaction_count": len(recent)
            }

        return None

    def detect_amount_spike(self, user_id: int, current_amount: float) -> Optional[Dict[str, Any]]:
        """
        Detect unusual transaction amount

        Returns anomaly details if detected, None otherwise
        """
        if user_id not in self.user_transactions:
            # Compare against global stats
            z_score = abs((current_amount - self.global_amount_mean) / self.global_amount_std)

            if z_score > 3.0:  # More than 3 standard deviations
                return {
                    "anomaly_type": "amount_spike",
                    "severity": "high" if z_score > 5.0 else "medium",
                    "description": f"Amount ${current_amount:.2f} is {z_score:.1f}σ above normal",
                    "anomaly_score": min(z_score / 5.0, 1.0),
                    "z_score": z_score
                }
            return None

        transactions = list(self.user_transactions[user_id])
        if len(transactions) < 3:
            return None

        # Calculate user's average
        amounts = [t["amount"] for t in transactions]
        user_mean = np.mean(amounts)
        user_std = np.std(amounts) if len(amounts) > 1 else 1.0

        z_score = abs((current_amount - user_mean) / user_std) if user_std > 0 else 0

        if z_score > 3.0:
            return {
                "anomaly_type": "amount_spike",
                "severity": "critical" if z_score > 5.0 else "high",
                "description": f"Amount ${current_amount:.2f} is {z_score:.1f}σ above user average ${user_mean:.2f}",
                "anomaly_score": min(z_score / 5.0, 1.0),
                "z_score": z_score,
                "user_mean": user_mean
            }

        return None

    def detect_pattern_change(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Detect sudden change in transaction patterns

        Returns anomaly details if detected, None otherwise
        """
        if user_id not in self.user_transactions:
            return None

        transactions = list(self.user_transactions[user_id])
        if len(transactions) < 20:
            return None

        # Split into recent and historical
        recent = transactions[-5:]
        historical = transactions[-20:-5]

        recent_fraud_rate = sum(1 for t in recent if t["is_fraud"]) / len(recent)
        historical_fraud_rate = sum(1 for t in historical if t["is_fraud"]) / len(historical)

        # Check for significant increase in fraud rate
        if recent_fraud_rate > 0.6 and recent_fraud_rate > historical_fraud_rate * 2:
            return {
                "anomaly_type": "pattern_change",
                "severity": "critical" if recent_fraud_rate > 0.8 else "high",
                "description": f"Fraud rate jumped from {historical_fraud_rate:.1%} to {recent_fraud_rate:.1%}",
                "anomaly_score": recent_fraud_rate,
                "recent_fraud_rate": recent_fraud_rate,
                "historical_fraud_rate": historical_fraud_rate
            }

        return None

    def analyze_transaction(
        self,
        db: Session,
        user_id: int,
        transaction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze a transaction for anomalies

        Args:
            db: Database session
            user_id: User ID
            transaction: Transaction data

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check velocity
        velocity_anomaly = self.detect_velocity_anomaly(user_id)
        if velocity_anomaly:
            anomalies.append(velocity_anomaly)

        # Check amount spike
        amount = transaction.get("amount", 0)
        amount_anomaly = self.detect_amount_spike(user_id, amount)
        if amount_anomaly:
            anomalies.append(amount_anomaly)

        # Check pattern change
        pattern_anomaly = self.detect_pattern_change(user_id)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)

        # Store anomalies in database
        for anomaly in anomalies:
            self._create_alert(db, user_id, anomaly)

        # Add transaction to history
        self.add_transaction(user_id, transaction)

        return anomalies

    def _create_alert(self, db: Session, user_id: int, anomaly: Dict[str, Any]):
        """Create an alert in the database"""
        try:
            import json

            alert = AnomalyAlert(
                user_id=user_id,
                anomaly_type=anomaly["anomaly_type"],
                severity=anomaly["severity"],
                description=anomaly["description"],
                anomaly_score=anomaly["anomaly_score"],
                affected_features=json.dumps(list(anomaly.keys()))
            )

            db.add(alert)
            db.commit()

            logger.warning(f"Anomaly alert created: {anomaly['anomaly_type']} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            db.rollback()

    def get_user_alerts(
        self,
        db: Session,
        user_id: int,
        unresolved_only: bool = True,
        limit: int = 50
    ) -> List[AnomalyAlert]:
        """Get alerts for a user"""
        query = db.query(AnomalyAlert).filter(AnomalyAlert.user_id == user_id)

        if unresolved_only:
            query = query.filter(AnomalyAlert.resolved == False)

        return query.order_by(AnomalyAlert.created_at.desc()).limit(limit).all()

    def acknowledge_alert(self, db: Session, alert_id: int, user_id: int) -> bool:
        """Mark an alert as acknowledged"""
        try:
            alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
            if not alert:
                return False

            alert.acknowledged = True
            alert.updated_at = datetime.utcnow()
            db.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            db.rollback()
            return False

    def resolve_alert(self, db: Session, alert_id: int, resolved_by: int) -> bool:
        """Mark an alert as resolved"""
        try:
            alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
            if not alert:
                return False

            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            alert.updated_at = datetime.utcnow()
            db.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            db.rollback()
            return False


# Global anomaly detector instance
anomaly_detector = AnomalyDetector()
