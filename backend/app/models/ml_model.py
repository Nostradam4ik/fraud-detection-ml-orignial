"""ML Model wrapper for fraud detection"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class FraudDetectionModel:
    """Wrapper class for the fraud detection ML model"""

    FEATURE_NAMES = [
        "Time",
        "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
        "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
        "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
        "Amount",
    ]

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_loaded: bool = False
        self.model_info: Dict = {}

    def load(self, model_path: str, scaler_path: str) -> bool:
        """Load the trained model and scaler from disk"""
        try:
            model_file = Path(model_path)
            scaler_file = Path(scaler_path)

            if not model_file.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False

            if not scaler_file.exists():
                logger.warning(f"Scaler file not found: {scaler_path}")
                return False

            self.model = joblib.load(model_file)
            self.scaler = joblib.load(scaler_file)
            self.is_loaded = True

            # Load model info if available
            info_path = model_file.parent / "model_info.pkl"
            if info_path.exists():
                self.model_info = joblib.load(info_path)

            logger.info("Model and scaler loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_loaded = False
            return False

    def predict(self, features: np.ndarray) -> Tuple[bool, float]:
        """
        Make a prediction for a single transaction

        Args:
            features: numpy array of shape (30,) with transaction features

        Returns:
            Tuple of (is_fraud, fraud_probability)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Reshape for single prediction
        features = features.reshape(1, -1)

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Get prediction and probability
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        # Probability of fraud (class 1)
        fraud_prob = float(probabilities[1])
        is_fraud = bool(prediction == 1)

        return is_fraud, fraud_prob

    def predict_batch(
        self, features_batch: np.ndarray
    ) -> List[Tuple[bool, float]]:
        """
        Make predictions for multiple transactions

        Args:
            features_batch: numpy array of shape (n_samples, 30)

        Returns:
            List of (is_fraud, fraud_probability) tuples
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Scale features
        features_scaled = self.scaler.transform(features_batch)

        # Get predictions and probabilities
        predictions = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)

        results = []
        for pred, prob in zip(predictions, probabilities):
            is_fraud = bool(pred == 1)
            fraud_prob = float(prob[1])
            results.append((is_fraud, fraud_prob))

        return results

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        importances = self.model.feature_importances_
        return dict(zip(self.FEATURE_NAMES, importances))

    @staticmethod
    def get_confidence_level(probability: float) -> str:
        """Convert probability to confidence level"""
        if probability < 0.3:
            return "low"
        elif probability < 0.7:
            return "medium"
        else:
            return "high"

    @staticmethod
    def get_risk_score(probability: float) -> int:
        """Convert probability to risk score (0-100)"""
        return int(probability * 100)


# Global model instance
fraud_model = FraudDetectionModel()
