"""API routes for prediction feedback and model retraining"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.services.feedback_service import feedback_service, ModelTrainingJob
from app.models.enhanced_ml_model import ModelType
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """Request to submit prediction feedback"""
    prediction_id: int
    predicted_fraud: bool
    predicted_probability: float
    actual_fraud: bool
    features: List[float] = Field(..., min_items=30, max_items=30)
    feedback_notes: Optional[str] = None
    feedback_confidence: str = Field(default="high", pattern="^(low|medium|high)$")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    id: int
    prediction_id: int
    feedback_type: str
    created_at: datetime
    message: str


class FeedbackStatsResponse(BaseModel):
    """Statistics about collected feedback"""
    total_feedback: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    unused_for_training: int
    accuracy_from_feedback: float


class RetrainRequest(BaseModel):
    """Request to retrain the model"""
    model_type: str = Field(default="ensemble", pattern="^(random_forest|gradient_boosting|neural_network|ensemble)$")
    min_samples: int = Field(default=100, ge=50, le=10000)
    test_split: float = Field(default=0.2, ge=0.1, le=0.5)


class TrainingJobResponse(BaseModel):
    """Response with training job details"""
    id: int
    batch_id: str
    model_type: str
    total_samples: int
    fraud_samples: int
    legitimate_samples: int
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    status: str
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


@router.post("/submit", response_model=FeedbackResponse)
def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback on a prediction

    This feedback will be used to retrain and improve the model.
    """
    try:
        result = feedback_service.add_feedback(
            db=db,
            prediction_id=feedback.prediction_id,
            user_id=current_user["id"],
            predicted_fraud=feedback.predicted_fraud,
            predicted_probability=feedback.predicted_probability,
            actual_fraud=feedback.actual_fraud,
            features=feedback.features,
            feedback_notes=feedback.feedback_notes,
            feedback_confidence=feedback.feedback_confidence
        )

        return FeedbackResponse(
            id=result.id,
            prediction_id=result.prediction_id,
            feedback_type=result.feedback_type,
            created_at=result.created_at,
            message=f"Feedback recorded: {result.feedback_type}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStatsResponse)
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics about collected feedback"""
    stats = feedback_service.get_feedback_stats(db)
    return stats


@router.post("/retrain", response_model=TrainingJobResponse)
def retrain_model(
    request: RetrainRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger model retraining with collected feedback

    Requires sufficient feedback samples (min_samples).
    Only available to admin users.
    """
    # Check if user is admin
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can retrain models"
        )

    try:
        model_type = ModelType(request.model_type)

        job = feedback_service.retrain_model(
            db=db,
            model_type=model_type,
            min_samples=request.min_samples,
            test_split=request.test_split
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start retraining job"
            )

        return TrainingJobResponse(
            id=job.id,
            batch_id=job.batch_id,
            model_type=job.model_type,
            total_samples=job.total_samples,
            fraud_samples=job.fraud_samples,
            legitimate_samples=job.legitimate_samples,
            accuracy=job.accuracy,
            precision=job.precision,
            recall=job.recall,
            f1_score=job.f1_score,
            status=job.status,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retraining failed: {str(e)}"
        )


@router.get("/training-history", response_model=List[TrainingJobResponse])
def get_training_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get history of model training jobs"""
    jobs = feedback_service.get_training_history(db, limit=limit)

    return [
        TrainingJobResponse(
            id=job.id,
            batch_id=job.batch_id,
            model_type=job.model_type,
            total_samples=job.total_samples,
            fraud_samples=job.fraud_samples,
            legitimate_samples=job.legitimate_samples,
            accuracy=job.accuracy,
            precision=job.precision,
            recall=job.recall,
            f1_score=job.f1_score,
            status=job.status,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at
        )
        for job in jobs
    ]
