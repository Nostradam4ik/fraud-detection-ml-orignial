"""
ML Model Retraining Pipeline
Automated pipeline for retraining fraud detection models

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)

# Optional: XGBoost support
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# Optional: SHAP support
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelRetrainingPipeline:
    """Automated ML model retraining pipeline"""

    def __init__(
        self,
        data_path: str,
        model_output_dir: str = "models",
        model_type: str = "random_forest",
        test_size: float = 0.2,
        random_state: int = 42
    ):
        self.data_path = Path(data_path)
        self.model_output_dir = Path(model_output_dir)
        self.model_output_dir.mkdir(parents=True, exist_ok=True)
        self.model_type = model_type
        self.test_size = test_size
        self.random_state = random_state

        self.model = None
        self.scaler = None
        self.metrics = {}
        self.feature_importance = {}

    def load_data(self) -> pd.DataFrame:
        """Load training data from CSV"""
        logger.info(f"Loading data from {self.data_path}")

        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} features")

        return df

    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Preprocess data for training"""
        logger.info("Preprocessing data...")

        # Assume 'Class' is the target column (fraud/not fraud)
        if 'Class' not in df.columns:
            raise ValueError("Target column 'Class' not found in data")

        # Separate features and target
        X = df.drop('Class', axis=1)
        y = df['Class']

        # Log class distribution
        fraud_count = y.sum()
        total = len(y)
        logger.info(f"Class distribution: {fraud_count}/{total} fraud ({fraud_count/total*100:.2f}%)")

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")

        return X_train, X_test, y_train, y_test

    def train_model(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train the ML model"""
        logger.info(f"Training {self.model_type} model...")

        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            )
        elif self.model_type == "xgboost" and HAS_XGBOOST:
            # Calculate scale_pos_weight for imbalanced data
            scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='auc'
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Train
        self.model.fit(X_train, y_train)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='f1')
        logger.info(f"Cross-validation F1 scores: {cv_scores}")
        logger.info(f"Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    def evaluate_model(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate model performance"""
        logger.info("Evaluating model...")

        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]

        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_prob)
        }

        logger.info("Model Performance:")
        for metric, value in self.metrics.items():
            logger.info(f"  {metric}: {value:.4f}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")

        # Classification report
        report = classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud'])
        logger.info(f"Classification Report:\n{report}")

        return self.metrics

    def calculate_feature_importance(self, feature_names: list) -> Dict[str, float]:
        """Calculate and store feature importance"""
        logger.info("Calculating feature importance...")

        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            self.feature_importance = dict(zip(feature_names, importances))

            # Sort by importance
            sorted_features = sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )

            logger.info("Top 10 most important features:")
            for feature, importance in sorted_features[:10]:
                logger.info(f"  {feature}: {importance:.4f}")

        return self.feature_importance

    def calculate_shap_values(self, X_sample: np.ndarray, feature_names: list) -> Optional[np.ndarray]:
        """Calculate SHAP values for model explainability"""
        if not HAS_SHAP:
            logger.warning("SHAP not installed. Skipping SHAP analysis.")
            return None

        logger.info("Calculating SHAP values...")

        try:
            # Use a sample for faster computation
            sample_size = min(1000, len(X_sample))
            X_shap = X_sample[:sample_size]

            if self.model_type == "random_forest":
                explainer = shap.TreeExplainer(self.model)
            else:
                explainer = shap.Explainer(self.model, X_shap)

            shap_values = explainer.shap_values(X_shap)

            # For binary classification, get values for fraud class
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            logger.info("SHAP values calculated successfully")
            return shap_values

        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return None

    def save_model(self, version: str = None) -> Tuple[str, str]:
        """Save trained model and scaler"""
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        model_filename = f"fraud_model_{version}.joblib"
        scaler_filename = f"scaler_{version}.joblib"
        metadata_filename = f"model_metadata_{version}.json"

        model_path = self.model_output_dir / model_filename
        scaler_path = self.model_output_dir / scaler_filename
        metadata_path = self.model_output_dir / metadata_filename

        # Save model and scaler
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        # Save metadata
        metadata = {
            'version': version,
            'model_type': self.model_type,
            'trained_at': datetime.now().isoformat(),
            'metrics': self.metrics,
            'feature_importance': self.feature_importance,
            'test_size': self.test_size,
            'random_state': self.random_state
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {model_path}")
        logger.info(f"Scaler saved to {scaler_path}")
        logger.info(f"Metadata saved to {metadata_path}")

        # Also save as 'latest'
        latest_model = self.model_output_dir / "fraud_model.joblib"
        latest_scaler = self.model_output_dir / "scaler.joblib"
        joblib.dump(self.model, latest_model)
        joblib.dump(self.scaler, latest_scaler)

        return str(model_path), str(scaler_path)

    def compare_with_current(self, current_model_path: str) -> bool:
        """Compare new model with current production model"""
        if not Path(current_model_path).exists():
            logger.info("No current model found. New model will be used.")
            return True

        logger.info("Comparing with current model...")

        # Load current model metrics
        current_metadata_path = current_model_path.replace('.joblib', '_metadata.json')
        if Path(current_metadata_path).exists():
            with open(current_metadata_path, 'r') as f:
                current_metadata = json.load(f)
                current_metrics = current_metadata.get('metrics', {})

            # Compare F1 scores
            current_f1 = current_metrics.get('f1_score', 0)
            new_f1 = self.metrics.get('f1_score', 0)

            improvement = (new_f1 - current_f1) / current_f1 * 100 if current_f1 > 0 else 100

            logger.info(f"Current F1: {current_f1:.4f}, New F1: {new_f1:.4f}")
            logger.info(f"Improvement: {improvement:+.2f}%")

            # Only deploy if improvement is significant (> 1%)
            if improvement > 1:
                logger.info("New model is significantly better. Recommending deployment.")
                return True
            elif improvement > -5:
                logger.info("New model is similar to current. Consider other factors.")
                return True
            else:
                logger.warning("New model is worse than current. Not recommending deployment.")
                return False

        return True

    def run_pipeline(self, compare_current: bool = True) -> Dict[str, Any]:
        """Run the full retraining pipeline"""
        logger.info("="*50)
        logger.info("Starting Model Retraining Pipeline")
        logger.info("="*50)

        try:
            # Load data
            df = self.load_data()

            # Get feature names before preprocessing
            feature_names = [col for col in df.columns if col != 'Class']

            # Preprocess
            X_train, X_test, y_train, y_test = self.preprocess_data(df)

            # Train
            self.train_model(X_train, y_train)

            # Evaluate
            metrics = self.evaluate_model(X_test, y_test)

            # Feature importance
            self.calculate_feature_importance(feature_names)

            # SHAP values (optional)
            self.calculate_shap_values(X_test, feature_names)

            # Compare with current model
            should_deploy = True
            if compare_current:
                current_model = self.model_output_dir / "fraud_model.joblib"
                should_deploy = self.compare_with_current(str(current_model))

            # Save model
            model_path, scaler_path = self.save_model()

            result = {
                'success': True,
                'model_path': model_path,
                'scaler_path': scaler_path,
                'metrics': metrics,
                'should_deploy': should_deploy,
                'timestamp': datetime.now().isoformat()
            }

            logger.info("="*50)
            logger.info("Pipeline completed successfully!")
            logger.info("="*50)

            return result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(description='ML Model Retraining Pipeline')
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Path to training data CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='models',
        help='Output directory for models'
    )
    parser.add_argument(
        '--model-type',
        type=str,
        choices=['random_forest', 'xgboost'],
        default='random_forest',
        help='Type of model to train'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set size (0-1)'
    )
    parser.add_argument(
        '--no-compare',
        action='store_true',
        help='Skip comparison with current model'
    )

    args = parser.parse_args()

    pipeline = ModelRetrainingPipeline(
        data_path=args.data,
        model_output_dir=args.output,
        model_type=args.model_type,
        test_size=args.test_size
    )

    result = pipeline.run_pipeline(compare_current=not args.no_compare)

    if result['success']:
        print(f"\nModel trained successfully!")
        print(f"Metrics: {result['metrics']}")
        print(f"Should deploy: {result['should_deploy']}")
    else:
        print(f"\nTraining failed: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()
