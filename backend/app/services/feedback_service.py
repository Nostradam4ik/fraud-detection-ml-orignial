"""Service for collecting feedback and retraining ML models"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

from app.db.database import Base
from app.models.enhanced_ml_model import EnhancedFraudDetectionModel, ModelType

logger = logging.getLogger(__name__)


class PredictionFeedback(Base):
    """Store feedback on predictions for model retraining"""
    __tablename__ = "prediction_feedback"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)

    # Original prediction
    predicted_fraud = Column(Boolean, nullable=False)
    predicted_probability = Column(Float, nullable=False)

    # User feedback
    actual_fraud = Column(Boolean, nullable=True)  # True label from user
    feedback_type = Column(String(50))  # "correct", "false_positive", "false_negative"
    feedback_confidence = Column(String(20))  # "low", "medium", "high"

    # Features (stored as JSON string)
    features_json = Column(Text, nullable=False)

    # Metadata
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Training status
    used_in_training = Column(Boolean, default=False)
    training_batch_id = Column(String(50), nullable=True)


class ModelTrainingJob(Base):
    """Track model retraining jobs"""
    __tablename__ = "model_training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), unique=True, index=True)

    model_type = Column(String(50), nullable=False)

    # Training data stats
    total_samples = Column(Integer, nullable=False)
    fraud_samples = Column(Integer, nullable=False)
    legitimate_samples = Column(Integer, nullable=False)

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackService:
    """Service for managing prediction feedback and model retraining"""

    def __init__(self):
        self.model = EnhancedFraudDetectionModel()

    def add_feedback(
        self,
        db: Session,
        prediction_id: int,
        user_id: int,
        predicted_fraud: bool,
        predicted_probability: float,
        actual_fraud: bool,
        features: List[float],
        feedback_notes: Optional[str] = None,
        feedback_confidence: str = "high"
    ) -> PredictionFeedback:
        """
        Add user feedback for a prediction

        Args:
            db: Database session
            prediction_id: ID of the original prediction
            user_id: ID of the user providing feedback
            predicted_fraud: What the model predicted
            predicted_probability: Prediction probability
            actual_fraud: True label from user
            features: Original features (30 values)
            feedback_notes: Optional notes from user
            feedback_confidence: User's confidence in their feedback

        Returns:
            Created PredictionFeedback object
        """
        import json

        # Determine feedback type
        if predicted_fraud == actual_fraud:
            feedback_type = "correct"
        elif predicted_fraud and not actual_fraud:
            feedback_type = "false_positive"
        else:
            feedback_type = "false_negative"

        feedback = PredictionFeedback(
            prediction_id=prediction_id,
            user_id=user_id,
            predicted_fraud=predicted_fraud,
            predicted_probability=predicted_probability,
            actual_fraud=actual_fraud,
            feedback_type=feedback_type,
            feedback_confidence=feedback_confidence,
            features_json=json.dumps(features),
            feedback_notes=feedback_notes
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"Feedback added: {feedback_type} for prediction {prediction_id}")
        return feedback

    def get_feedback_stats(self, db: Session) -> Dict[str, Any]:
        """Get statistics about collected feedback"""
        total = db.query(PredictionFeedback).count()
        correct = db.query(PredictionFeedback).filter(
            PredictionFeedback.feedback_type == "correct"
        ).count()
        false_positives = db.query(PredictionFeedback).filter(
            PredictionFeedback.feedback_type == "false_positive"
        ).count()
        false_negatives = db.query(PredictionFeedback).filter(
            PredictionFeedback.feedback_type == "false_negative"
        ).count()
        unused = db.query(PredictionFeedback).filter(
            PredictionFeedback.used_in_training == False
        ).count()

        return {
            "total_feedback": total,
            "correct_predictions": correct,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "unused_for_training": unused,
            "accuracy_from_feedback": correct / total if total > 0 else 0.0
        }

    def get_training_data(
        self,
        db: Session,
        min_samples: int = 100,
        include_used: bool = False
    ) -> Optional[tuple]:
        """
        Get training data from feedback

        Args:
            db: Database session
            min_samples: Minimum samples required
            include_used: Whether to include previously used samples

        Returns:
            Tuple of (X, y) or None if insufficient data
        """
        import json

        query = db.query(PredictionFeedback)
        if not include_used:
            query = query.filter(PredictionFeedback.used_in_training == False)

        feedbacks = query.all()

        if len(feedbacks) < min_samples:
            logger.warning(
                f"Insufficient feedback samples: {len(feedbacks)} < {min_samples}"
            )
            return None

        # Extract features and labels
        X = []
        y = []

        for feedback in feedbacks:
            try:
                features = json.loads(feedback.features_json)
                X.append(features)
                y.append(int(feedback.actual_fraud))
            except Exception as e:
                logger.error(f"Error parsing feedback {feedback.id}: {e}")
                continue

        return np.array(X), np.array(y)

    def retrain_model(
        self,
        db: Session,
        model_type: ModelType = ModelType.ENSEMBLE,
        min_samples: int = 100,
        test_split: float = 0.2
    ) -> Optional[ModelTrainingJob]:
        """
        Retrain the model using collected feedback

        Args:
            db: Database session
            model_type: Type of model to train
            min_samples: Minimum samples required
            test_split: Fraction of data for testing

        Returns:
            ModelTrainingJob object or None if failed
        """
        import uuid
        from sklearn.model_selection import train_test_split

        batch_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        # Create training job
        job = ModelTrainingJob(
            batch_id=batch_id,
            model_type=model_type.value,
            total_samples=0,
            fraud_samples=0,
            legitimate_samples=0,
            status="pending",
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        try:
            job.status = "running"
            db.commit()

            # Get training data
            data = self.get_training_data(db, min_samples=min_samples)
            if data is None:
                raise ValueError(f"Insufficient training samples (need {min_samples})")

            X, y = data

            # Update job stats
            job.total_samples = len(y)
            job.fraud_samples = int(np.sum(y))
            job.legitimate_samples = int(len(y) - np.sum(y))
            db.commit()

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_split, stratify=y, random_state=42
            )

            # Train model
            model = EnhancedFraudDetectionModel(model_type=model_type)
            metrics = model.train(X_train, y_train, X_test, y_test)

            # Save model
            model_path = f"models/enhanced_model_{batch_id}.pkl"
            scaler_path = f"models/enhanced_scaler_{batch_id}.pkl"
            model.save(model_path, scaler_path)

            # Update job with metrics
            job.accuracy = metrics.get("accuracy")
            job.precision = metrics.get("precision")
            job.recall = metrics.get("recall")
            job.f1_score = metrics.get("f1_score")
            job.status = "completed"
            job.completed_at = datetime.utcnow()

            # Mark feedback as used
            db.query(PredictionFeedback).filter(
                PredictionFeedback.used_in_training == False
            ).update({
                "used_in_training": True,
                "training_batch_id": batch_id
            })

            db.commit()
            db.refresh(job)

            logger.info(f"Model retraining completed: {batch_id}")
            logger.info(f"Metrics: {metrics}")

            return job

        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            return job

    def get_training_history(
        self,
        db: Session,
        limit: int = 10
    ) -> List[ModelTrainingJob]:
        """Get recent training jobs"""
        return db.query(ModelTrainingJob).order_by(
            ModelTrainingJob.created_at.desc()
        ).limit(limit).all()


# Global service instance
feedback_service = FeedbackService()
