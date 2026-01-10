"""
Prediction Service - Save and retrieve predictions from database

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db.models import Prediction
from ..models.schemas import TransactionInput, PredictionResponse


def save_prediction(
    db: Session,
    user_id: int,
    transaction: TransactionInput,
    result: PredictionResponse
) -> Prediction:
    """Save a prediction to the database"""

    # Convert PCA features to JSON
    features = {
        f"v{i}": getattr(transaction, f"v{i}")
        for i in range(1, 29)
    }

    db_prediction = Prediction(
        user_id=user_id,
        time=transaction.time,
        amount=transaction.amount,
        features_json=json.dumps(features),
        is_fraud=result.is_fraud,
        fraud_probability=result.fraud_probability,
        confidence=result.confidence,
        risk_score=result.risk_score,
        prediction_time_ms=result.prediction_time_ms
    )

    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)

    return db_prediction


def get_user_predictions(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Prediction]:
    """Get predictions for a specific user"""
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_user_prediction_stats(db: Session, user_id: int) -> dict:
    """Get prediction statistics for a user"""
    predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()

    if not predictions:
        return {
            "total_predictions": 0,
            "fraud_detected": 0,
            "legitimate_detected": 0,
            "fraud_rate": 0.0,
            "average_response_time_ms": 0.0
        }

    total = len(predictions)
    fraud_count = sum(1 for p in predictions if p.is_fraud)
    legitimate_count = total - fraud_count
    avg_time = sum(p.prediction_time_ms for p in predictions) / total

    return {
        "total_predictions": total,
        "fraud_detected": fraud_count,
        "legitimate_detected": legitimate_count,
        "fraud_rate": fraud_count / total if total > 0 else 0.0,
        "average_response_time_ms": avg_time
    }


def get_prediction_by_id(db: Session, prediction_id: int) -> Optional[Prediction]:
    """Get a specific prediction by ID"""
    return db.query(Prediction).filter(Prediction.id == prediction_id).first()


def save_batch_predictions(
    db: Session,
    user_id: int,
    df,
    batch_id: str
) -> int:
    """Save batch predictions from a DataFrame to database"""
    import pandas as pd

    count = 0
    for _, row in df.iterrows():
        # Convert PCA features to JSON
        features = {
            f"v{i}": float(row[f'v{i}'])
            for i in range(1, 29)
        }

        db_prediction = Prediction(
            user_id=user_id,
            time=float(row['time']),
            amount=float(row['amount']),
            features_json=json.dumps(features),
            is_fraud=bool(row['is_fraud']),
            fraud_probability=float(row['fraud_probability']),
            confidence=str(row['confidence']),
            risk_score=int(row['risk_score']),
            prediction_time_ms=0.0,  # Batch doesn't track individual timing
            batch_id=batch_id
        )

        db.add(db_prediction)
        count += 1

    db.commit()
    return count


def get_batch_predictions(
    db: Session,
    user_id: int,
    batch_id: str
) -> List[Prediction]:
    """Get all predictions for a specific batch"""
    return (
        db.query(Prediction)
        .filter(
            Prediction.user_id == user_id,
            Prediction.batch_id == batch_id
        )
        .order_by(Prediction.id)
        .all()
    )


def get_user_batches(
    db: Session,
    user_id: int,
    limit: int = 20
) -> List[dict]:
    """Get list of batch predictions for a user"""
    from sqlalchemy import func

    results = (
        db.query(
            Prediction.batch_id,
            func.count(Prediction.id).label('count'),
            func.sum(func.cast(Prediction.is_fraud, db.bind.dialect.name == 'sqlite' and 'INTEGER' or 'INT')).label('fraud_count'),
            func.min(Prediction.created_at).label('created_at')
        )
        .filter(
            Prediction.user_id == user_id,
            Prediction.batch_id.isnot(None)
        )
        .group_by(Prediction.batch_id)
        .order_by(func.min(Prediction.created_at).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "batch_id": r.batch_id,
            "total_count": r.count,
            "fraud_count": r.fraud_count or 0,
            "legitimate_count": r.count - (r.fraud_count or 0),
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]
