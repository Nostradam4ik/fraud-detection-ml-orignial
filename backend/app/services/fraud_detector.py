"""Fraud detection service - Main business logic"""

import time
from datetime import datetime
from typing import Dict, List

import numpy as np

from ..models.ml_model import fraud_model, FraudDetectionModel
from ..models.schemas import (
    TransactionInput,
    PredictionResponse,
    BatchPredictionResponse,
    SingleBatchResult,
    ModelInfo,
    StatsResponse,
)
from .data_processor import DataProcessor


class FraudDetectorService:
    """Service for fraud detection operations"""

    # Track statistics
    _stats = {
        "total_predictions": 0,
        "fraud_detected": 0,
        "legitimate_detected": 0,
        "total_response_time_ms": 0.0,
        "start_time": datetime.now(),
    }

    @classmethod
    def predict_single(cls, transaction: TransactionInput) -> PredictionResponse:
        """Make a fraud prediction for a single transaction"""
        start_time = time.perf_counter()

        # Convert transaction to numpy array
        features = DataProcessor.transaction_to_array(transaction)

        # Make prediction
        is_fraud, fraud_prob = fraud_model.predict(features)

        # Calculate metrics
        prediction_time_ms = (time.perf_counter() - start_time) * 1000
        confidence = FraudDetectionModel.get_confidence_level(
            fraud_prob if is_fraud else (1 - fraud_prob)
        )
        risk_score = FraudDetectionModel.get_risk_score(fraud_prob)

        # Update stats
        cls._update_stats(is_fraud, prediction_time_ms)

        return PredictionResponse(
            is_fraud=is_fraud,
            fraud_probability=round(fraud_prob, 4),
            confidence=confidence,
            risk_score=risk_score,
            prediction_time_ms=round(prediction_time_ms, 2),
        )

    @classmethod
    def predict_batch(
        cls, transactions: List[TransactionInput]
    ) -> BatchPredictionResponse:
        """Make fraud predictions for multiple transactions"""
        start_time = time.perf_counter()

        # Convert to batch array
        features_batch = DataProcessor.transactions_to_batch(transactions)

        # Make predictions
        predictions = fraud_model.predict_batch(features_batch)

        # Process results
        results = []
        fraud_count = 0

        for idx, (is_fraud, fraud_prob) in enumerate(predictions):
            if is_fraud:
                fraud_count += 1

            results.append(
                SingleBatchResult(
                    index=idx,
                    is_fraud=is_fraud,
                    fraud_probability=round(fraud_prob, 4),
                    risk_score=FraudDetectionModel.get_risk_score(fraud_prob),
                )
            )

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        # Update stats
        for is_fraud, _ in predictions:
            cls._update_stats(is_fraud, processing_time_ms / len(predictions))

        legitimate_count = len(transactions) - fraud_count
        fraud_rate = fraud_count / len(transactions) if transactions else 0

        return BatchPredictionResponse(
            total_transactions=len(transactions),
            fraud_count=fraud_count,
            legitimate_count=legitimate_count,
            fraud_rate=round(fraud_rate, 4),
            results=results,
            processing_time_ms=round(processing_time_ms, 2),
        )

    @classmethod
    def get_model_info(cls) -> ModelInfo:
        """Get information about the loaded model"""
        info = fraud_model.model_info

        return ModelInfo(
            model_name="Random Forest Classifier",
            model_version=info.get("version", "1.0.0"),
            features_count=30,
            training_samples=info.get("training_samples", 284807),
            fraud_samples=info.get("fraud_samples", 492),
            accuracy=info.get("accuracy", 0.9995),
            precision=info.get("precision", 0.95),
            recall=info.get("recall", 0.80),
            f1_score=info.get("f1_score", 0.87),
            roc_auc=info.get("roc_auc", 0.98),
            last_trained=info.get("last_trained"),
        )

    @classmethod
    def get_stats(cls) -> StatsResponse:
        """Get API usage statistics"""
        total = cls._stats["total_predictions"]
        avg_time = (
            cls._stats["total_response_time_ms"] / total if total > 0 else 0
        )
        uptime = (datetime.now() - cls._stats["start_time"]).total_seconds()

        fraud_rate = (
            cls._stats["fraud_detected"] / total if total > 0 else 0
        )

        return StatsResponse(
            total_predictions=total,
            fraud_detected=cls._stats["fraud_detected"],
            legitimate_detected=cls._stats["legitimate_detected"],
            fraud_rate=round(fraud_rate, 4),
            average_response_time_ms=round(avg_time, 2),
            uptime_seconds=round(uptime, 2),
        )

    @classmethod
    def get_feature_importance(cls) -> Dict[str, float]:
        """Get feature importance from the model"""
        return fraud_model.get_feature_importance()

    @classmethod
    def _update_stats(cls, is_fraud: bool, response_time_ms: float) -> None:
        """Update internal statistics"""
        cls._stats["total_predictions"] += 1
        cls._stats["total_response_time_ms"] += response_time_ms

        if is_fraud:
            cls._stats["fraud_detected"] += 1
        else:
            cls._stats["legitimate_detected"] += 1

    @classmethod
    def reset_stats(cls) -> None:
        """Reset statistics (for testing)"""
        cls._stats = {
            "total_predictions": 0,
            "fraud_detected": 0,
            "legitimate_detected": 0,
            "total_response_time_ms": 0.0,
            "start_time": datetime.now(),
        }
