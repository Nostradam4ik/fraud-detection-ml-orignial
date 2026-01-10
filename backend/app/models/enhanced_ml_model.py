"""Enhanced ML Model with multiple algorithms and advanced features"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Available model types"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class EnhancedFraudDetectionModel:
    """
    Enhanced fraud detection model with:
    - Multiple algorithms (RF, GradientBoosting, Neural Network)
    - Ensemble voting
    - Feature engineering
    - Model retraining capabilities
    - Performance tracking
    """

    BASE_FEATURES = [
        "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
        "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
        "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28", "Amount"
    ]

    ENGINEERED_FEATURES = [
        "amount_log",  # Log of amount
        "time_of_day",  # Hour of day (0-23)
        "amount_per_second",  # Amount / Time
        "v1_v2_interaction",  # V1 * V2
        "v3_v4_interaction",  # V3 * V4
        "amount_squared",  # Amount^2
        "high_amount_flag",  # 1 if amount > threshold
    ]

    def __init__(self, model_type: ModelType = ModelType.ENSEMBLE):
        self.model_type = model_type
        self.model: Optional[Any] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_loaded: bool = False
        self.model_info: Dict = {
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "model_type": model_type.value,
            "training_history": [],
            "performance_metrics": {},
        }

    def _engineer_features(self, features: np.ndarray) -> np.ndarray:
        """
        Create additional engineered features

        Args:
            features: numpy array of shape (n_samples, 30) with base features

        Returns:
            Extended feature array with shape (n_samples, 37)
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)

        time = features[:, 0]
        amount = features[:, -1]
        v1 = features[:, 1]
        v2 = features[:, 2]
        v3 = features[:, 3]
        v4 = features[:, 4]

        # Engineer new features
        amount_log = np.log1p(amount)  # log(1 + amount) to handle zeros
        time_of_day = (time % 86400) / 3600  # Convert to hours (0-24)
        amount_per_second = amount / (time + 1)  # Avoid division by zero
        v1_v2_interaction = v1 * v2
        v3_v4_interaction = v3 * v4
        amount_squared = amount ** 2
        high_amount_flag = (amount > 500).astype(float)

        # Stack all features
        engineered = np.column_stack([
            features,
            amount_log,
            time_of_day,
            amount_per_second,
            v1_v2_interaction,
            v3_v4_interaction,
            amount_squared,
            high_amount_flag
        ])

        return engineered

    def _create_model(self) -> Any:
        """Create the appropriate model based on model_type"""
        if self.model_type == ModelType.RANDOM_FOREST:
            return RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )

        elif self.model_type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=5,
                min_samples_leaf=2,
                subsample=0.8,
                random_state=42
            )

        elif self.model_type == ModelType.NEURAL_NETWORK:
            return MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                alpha=0.001,
                batch_size=256,
                learning_rate='adaptive',
                max_iter=300,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )

        elif self.model_type == ModelType.ENSEMBLE:
            rf = RandomForestClassifier(
                n_estimators=150, max_depth=15, random_state=42, n_jobs=-1
            )
            gb = GradientBoostingClassifier(
                n_estimators=150, learning_rate=0.1, max_depth=5, random_state=42
            )
            nn = MLPClassifier(
                hidden_layer_sizes=(50, 25), max_iter=200, random_state=42
            )

            return VotingClassifier(
                estimators=[('rf', rf), ('gb', gb), ('nn', nn)],
                voting='soft',
                n_jobs=-1
            )

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Train the model with feature engineering

        Args:
            X_train: Training features (n_samples, 30)
            y_train: Training labels
            X_test: Optional test features for evaluation
            y_test: Optional test labels for evaluation

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training {self.model_type.value} model...")

        # Engineer features
        X_train_eng = self._engineer_features(X_train)

        # Initialize and fit scaler
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train_eng)

        # Create and train model
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)

        self.is_loaded = True

        # Evaluate if test data provided
        metrics = {"trained_at": datetime.now().isoformat()}

        if X_test is not None and y_test is not None:
            X_test_eng = self._engineer_features(X_test)
            X_test_scaled = self.scaler.transform(X_test_eng)

            y_pred = self.model.predict(X_test_scaled)

            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

            metrics.update({
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred)),
                "recall": float(recall_score(y_test, y_pred)),
                "f1_score": float(f1_score(y_test, y_pred)),
            })

        # Update model info
        self.model_info["training_history"].append(metrics)
        self.model_info["performance_metrics"] = metrics

        logger.info(f"Training completed. Metrics: {metrics}")
        return metrics

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
            info_path = model_file.parent / "model_info_v2.json"
            if info_path.exists():
                with open(info_path, 'r') as f:
                    self.model_info = json.load(f)

            logger.info("Enhanced model and scaler loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_loaded = False
            return False

    def save(self, model_path: str, scaler_path: str) -> bool:
        """Save the model, scaler, and metadata"""
        try:
            if not self.is_loaded:
                raise RuntimeError("No model to save")

            model_file = Path(model_path)
            scaler_file = Path(scaler_path)

            # Create directory if needed
            model_file.parent.mkdir(parents=True, exist_ok=True)

            # Save model and scaler
            joblib.dump(self.model, model_file)
            joblib.dump(self.scaler, scaler_file)

            # Save model info
            info_path = model_file.parent / "model_info_v2.json"
            with open(info_path, 'w') as f:
                json.dump(self.model_info, f, indent=2)

            logger.info("Model saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def predict(self, features: np.ndarray) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Make a prediction for a single transaction with additional metadata

        Args:
            features: numpy array of shape (30,) with transaction features

        Returns:
            Tuple of (is_fraud, fraud_probability, metadata)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() or train() first.")

        # Engineer features
        features_eng = self._engineer_features(features)

        # Scale features
        features_scaled = self.scaler.transform(features_eng)

        # Get prediction and probability
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        # Probability of fraud (class 1)
        fraud_prob = float(probabilities[1])
        is_fraud = bool(prediction == 1)

        # Additional metadata
        metadata = {
            "model_type": self.model_type.value,
            "model_version": self.model_info.get("version", "1.0"),
            "confidence_level": self.get_confidence_level(fraud_prob),
            "risk_score": self.get_risk_score(fraud_prob),
            "engineered_features_used": len(self.ENGINEERED_FEATURES)
        }

        return is_fraud, fraud_prob, metadata

    def predict_batch(
        self, features_batch: np.ndarray
    ) -> List[Tuple[bool, float, Dict[str, Any]]]:
        """
        Make predictions for multiple transactions

        Args:
            features_batch: numpy array of shape (n_samples, 30)

        Returns:
            List of (is_fraud, fraud_probability, metadata) tuples
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() or train() first.")

        # Engineer features
        features_eng = self._engineer_features(features_batch)

        # Scale features
        features_scaled = self.scaler.transform(features_eng)

        # Get predictions and probabilities
        predictions = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)

        results = []
        for pred, prob in zip(predictions, probabilities):
            is_fraud = bool(pred == 1)
            fraud_prob = float(prob[1])
            metadata = {
                "model_type": self.model_type.value,
                "model_version": self.model_info.get("version", "1.0"),
                "confidence_level": self.get_confidence_level(fraud_prob),
                "risk_score": self.get_risk_score(fraud_prob),
            }
            results.append((is_fraud, fraud_prob, metadata))

        return results

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores for all features"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() or train() first.")

        # Get importances from the underlying model
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif self.model_type == ModelType.ENSEMBLE:
            # For ensemble, average importances from RF and GB
            rf_imp = self.model.estimators_[0].feature_importances_
            gb_imp = self.model.estimators_[1].feature_importances_
            importances = (rf_imp + gb_imp) / 2
        else:
            logger.warning("Model does not support feature importance")
            return {}

        all_features = self.BASE_FEATURES + self.ENGINEERED_FEATURES
        return dict(zip(all_features, importances))

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


# Global enhanced model instance
enhanced_fraud_model = EnhancedFraudDetectionModel(model_type=ModelType.ENSEMBLE)
