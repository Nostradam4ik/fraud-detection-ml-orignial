"""
Train the fraud detection model

This script:
1. Loads the credit card fraud dataset
2. Preprocesses the data
3. Handles class imbalance with SMOTE
4. Trains a Random Forest classifier
5. Evaluates and saves the model

Usage:
    python ml/train.py

Dataset:
    Download from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
    Place creditcard.csv in the data/ folder
"""

import sys
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_data(data_path: str) -> pd.DataFrame:
    """Load the credit card fraud dataset"""
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape}")
    print(f"Fraud cases: {df['Class'].sum()} ({df['Class'].mean()*100:.2f}%)")
    return df


def preprocess_data(df: pd.DataFrame):
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

    # Handle class imbalance with SMOTE
    print("\nApplying SMOTE to handle class imbalance...")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

    print(f"After SMOTE: {X_train_resampled.shape[0]} samples")
    print(f"Fraud ratio: {y_train_resampled.mean()*100:.2f}%")

    return (
        X_train_resampled,
        X_test_scaled,
        y_train_resampled,
        y_test,
        scaler,
    )


def train_model(X_train, y_train) -> RandomForestClassifier:
    """Train the Random Forest model"""
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
    print("Model training complete!")

    return model


def evaluate_model(model, X_test, y_test) -> dict:
    """Evaluate the model and return metrics"""
    print("\nEvaluating model...")

    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }

    # Print results
    print("\n" + "=" * 50)
    print("MODEL PERFORMANCE")
    print("=" * 50)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    print("=" * 50)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"True Negatives:  {cm[0][0]}")
    print(f"False Positives: {cm[0][1]}")
    print(f"False Negatives: {cm[1][0]}")
    print(f"True Positives:  {cm[1][1]}")

    return metrics


def save_model(model, scaler, metrics: dict, models_dir: str):
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
        "version": "1.0.0",
        "training_samples": 284807,
        "fraud_samples": 492,
        "last_trained": datetime.now(),
        **metrics,
    }
    info_path = models_path / "model_info.pkl"
    joblib.dump(model_info, info_path)
    print(f"Model info saved to: {info_path}")


def print_feature_importance(model, feature_names: list):
    """Print top feature importances"""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    print("\n" + "=" * 50)
    print("TOP 10 FEATURE IMPORTANCES")
    print("=" * 50)
    for i in range(min(10, len(feature_names))):
        idx = indices[i]
        print(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("FRAUD DETECTION MODEL TRAINING")
    print("=" * 60)

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

    # Train
    model = train_model(X_train, y_train)

    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)

    # Feature importance
    print_feature_importance(model, feature_names)

    # Save
    save_model(model, scaler, metrics, str(models_dir))

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the API: cd backend && uvicorn app.main:app --reload")
    print("2. Open docs: http://localhost:8000/docs")
    print("3. Test a prediction using the /api/v1/predict endpoint")


if __name__ == "__main__":
    main()
