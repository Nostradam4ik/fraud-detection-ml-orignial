"""
Advanced Model Training with XGBoost and SHAP

This script:
1. Loads the credit card fraud dataset
2. Preprocesses the data with SMOTE
3. Trains both Random Forest and XGBoost models
4. Compares model performance
5. Generates SHAP explanations
6. Saves the best model

Usage:
    python ml/train_advanced.py

Dataset:
    Download from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
    Place creditcard.csv in the data/ folder

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import sys
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Try to import XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not installed. Run: pip install xgboost")

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not installed. Run: pip install shap")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_data(data_path: str) -> pd.DataFrame:
    """Load the credit card fraud dataset"""
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape}")
    print(f"Fraud cases: {df['Class'].sum()} ({df['Class'].mean()*100:.3f}%)")
    return df


def preprocess_data(df: pd.DataFrame, use_smote: bool = True):
    """Preprocess the dataset"""
    print("\nPreprocessing data...")

    # Features and target
    X = df.drop("Class", axis=1)
    y = df["Class"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    if use_smote:
        # Handle class imbalance with SMOTE
        print("\nApplying SMOTE to handle class imbalance...")
        smote = SMOTE(random_state=42)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
        print(f"After SMOTE: {X_train_resampled.shape[0]} samples")
        print(f"Fraud ratio: {y_train_resampled.mean()*100:.2f}%")
        return X_train_resampled, X_test_scaled, y_train_resampled, y_test, scaler

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler


def train_random_forest(X_train, y_train):
    """Train Random Forest model"""
    print("\nTraining Random Forest model...")

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)
    return model


def train_xgboost(X_train, y_train):
    """Train XGBoost model"""
    if not XGBOOST_AVAILABLE:
        return None

    print("\nTraining XGBoost model...")

    # Calculate scale_pos_weight for imbalanced data
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=10,
        learning_rate=0.1,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        use_label_encoder=False,
        eval_metric='logloss'
    )

    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    """Evaluate the model and return metrics"""
    print(f"\nEvaluating {model_name}...")

    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    metrics = {
        "model_name": model_name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
    }

    # Print results
    print(f"\n{'=' * 50}")
    print(f"{model_name.upper()} PERFORMANCE")
    print("=" * 50)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")

    return metrics


def generate_shap_explanations(model, X_train, X_test, feature_names, models_dir):
    """Generate SHAP explanations for model predictions"""
    if not SHAP_AVAILABLE:
        print("\nSHAP not available. Skipping explanations.")
        return None

    print("\nGenerating SHAP explanations...")

    # Create SHAP explainer
    # Use TreeExplainer for tree-based models (RF, XGBoost)
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test[:1000])  # Use subset for speed

        # For binary classification, use values for positive class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        # Calculate mean absolute SHAP values for feature importance
        shap_importance = np.abs(shap_values).mean(axis=0)
        feature_importance = dict(zip(feature_names, shap_importance.tolist()))

        # Sort by importance
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        print("\nTop 10 Features by SHAP Importance:")
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:10]):
            print(f"{i+1}. {feature}: {importance:.4f}")

        # Save SHAP values
        shap_data = {
            "feature_importance": feature_importance,
            "expected_value": float(explainer.expected_value) if isinstance(explainer.expected_value, (int, float)) else float(explainer.expected_value[1]),
        }

        shap_path = Path(models_dir) / "shap_values.json"
        with open(shap_path, 'w') as f:
            json.dump(shap_data, f, indent=2)
        print(f"\nSHAP values saved to: {shap_path}")

        return feature_importance

    except Exception as e:
        print(f"Error generating SHAP explanations: {e}")
        return None


def compare_models(metrics_list: list) -> dict:
    """Compare model performance and return the best one"""
    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)

    # Create comparison table
    print(f"{'Model':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AUC':>10}")
    print("-" * 70)

    for m in metrics_list:
        print(f"{m['model_name']:<20} {m['accuracy']:>10.4f} {m['precision']:>10.4f} "
              f"{m['recall']:>10.4f} {m['f1_score']:>10.4f} {m['roc_auc']:>10.4f}")

    # Find best model by F1 score (good balance for imbalanced data)
    best = max(metrics_list, key=lambda x: x['f1_score'])
    print(f"\nBest Model: {best['model_name']} (F1: {best['f1_score']:.4f})")

    return best


def save_model(model, scaler, metrics: dict, shap_importance: dict, models_dir: str, model_type: str):
    """Save the trained model, scaler, and model info"""
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = models_path / "fraud_detector.pkl"
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")

    # Save scaler
    scaler_path = models_path / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to: {scaler_path}")

    # Save model info
    model_info = {
        "version": "2.0.0",
        "model_type": model_type,
        "training_date": datetime.now().isoformat(),
        "training_samples": 284807,
        "fraud_samples": 492,
        "metrics": metrics,
        "shap_feature_importance": shap_importance,
    }
    info_path = models_path / "model_info.json"
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    print(f"Model info saved to: {info_path}")

    # Also save as pkl for backward compatibility
    joblib.dump({**model_info, "last_trained": datetime.now()}, models_path / "model_info.pkl")


def main():
    """Main training pipeline"""
    print("=" * 70)
    print("ADVANCED FRAUD DETECTION MODEL TRAINING")
    print("=" * 70)

    # Paths
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "creditcard.csv"
    models_dir = base_dir / "models"

    # Check if data exists
    if not data_path.exists():
        print(f"\nERROR: Dataset not found at {data_path}")
        print("\nPlease download the dataset from:")
        print("https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
        print(f"\nAnd place 'creditcard.csv' in: {base_dir / 'data'}")
        sys.exit(1)

    # Load data
    df = load_data(str(data_path))

    # Get feature names before preprocessing
    feature_names = df.drop("Class", axis=1).columns.tolist()

    # Preprocess
    X_train, X_test, y_train, y_test, scaler = preprocess_data(df)

    # Train models
    models = {}
    metrics_list = []

    # Random Forest
    rf_model = train_random_forest(X_train, y_train)
    models["Random Forest"] = rf_model
    rf_metrics = evaluate_model(rf_model, X_test, y_test, "Random Forest")
    metrics_list.append(rf_metrics)

    # XGBoost
    if XGBOOST_AVAILABLE:
        xgb_model = train_xgboost(X_train, y_train)
        if xgb_model:
            models["XGBoost"] = xgb_model
            xgb_metrics = evaluate_model(xgb_model, X_test, y_test, "XGBoost")
            metrics_list.append(xgb_metrics)

    # Compare and select best model
    best_metrics = compare_models(metrics_list)
    best_model = models[best_metrics["model_name"]]
    model_type = best_metrics["model_name"]

    # Generate SHAP explanations for best model
    shap_importance = generate_shap_explanations(
        best_model, X_train, X_test, feature_names, str(models_dir)
    )

    # Save best model
    save_model(best_model, scaler, best_metrics, shap_importance, str(models_dir), model_type)

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nBest Model: {model_type}")
    print(f"F1 Score: {best_metrics['f1_score']:.4f}")
    print(f"ROC-AUC: {best_metrics['roc_auc']:.4f}")
    print("\nNext steps:")
    print("1. Start the API: cd backend && uvicorn app.main:app --reload")
    print("2. Open docs: http://localhost:8000/docs")
    print("3. Test predictions with SHAP explanations")


if __name__ == "__main__":
    main()
