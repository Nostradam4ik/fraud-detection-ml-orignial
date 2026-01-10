"""
Evaluate the trained fraud detection model

This script loads a trained model and evaluates it on test data,
generating detailed reports and visualizations.

Usage:
    python ml/evaluate.py
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_model_and_scaler(models_dir: str):
    """Load the trained model and scaler"""
    models_path = Path(models_dir)

    model = joblib.load(models_path / "fraud_detector.pkl")
    scaler = joblib.load(models_path / "scaler.pkl")
    model_info = joblib.load(models_path / "model_info.pkl")

    return model, scaler, model_info


def evaluate_at_thresholds(y_true, y_prob):
    """Evaluate model at different probability thresholds"""
    print("\n" + "=" * 60)
    print("EVALUATION AT DIFFERENT THRESHOLDS")
    print("=" * 60)

    thresholds = [0.3, 0.5, 0.7, 0.9]

    print(f"{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print("-" * 48)

    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        print(f"{thresh:<12.1f} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f}")


def analyze_predictions(y_true, y_pred, y_prob):
    """Detailed analysis of predictions"""
    print("\n" + "=" * 60)
    print("PREDICTION ANALYSIS")
    print("=" * 60)

    # Confusion matrix breakdown
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    print(f"\nTrue Negatives (Correct legitimate):  {tn:,}")
    print(f"False Positives (False alarms):       {fp:,}")
    print(f"False Negatives (Missed fraud):       {fn:,}")
    print(f"True Positives (Caught fraud):        {tp:,}")

    # Business metrics
    total_fraud = tp + fn
    caught_rate = tp / total_fraud if total_fraud > 0 else 0
    false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0

    print(f"\nFraud Detection Rate: {caught_rate:.2%}")
    print(f"False Alarm Rate: {false_alarm_rate:.4%}")

    # Confidence analysis
    print("\n" + "-" * 40)
    print("CONFIDENCE DISTRIBUTION")
    print("-" * 40)

    high_conf_fraud = np.sum((y_prob >= 0.9) & (y_true == 1))
    med_conf_fraud = np.sum((y_prob >= 0.5) & (y_prob < 0.9) & (y_true == 1))
    low_conf_fraud = np.sum((y_prob < 0.5) & (y_true == 1))

    print(f"High confidence fraud (>=90%): {high_conf_fraud}")
    print(f"Medium confidence fraud (50-90%): {med_conf_fraud}")
    print(f"Low confidence fraud (<50%): {low_conf_fraud}")


def main():
    """Main evaluation pipeline"""
    print("=" * 60)
    print("FRAUD DETECTION MODEL EVALUATION")
    print("=" * 60)

    # Paths
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "creditcard.csv"
    models_dir = base_dir / "models"

    # Check files exist
    if not data_path.exists():
        print(f"\nERROR: Dataset not found at {data_path}")
        sys.exit(1)

    if not (models_dir / "fraud_detector.pkl").exists():
        print(f"\nERROR: Model not found. Run train.py first.")
        sys.exit(1)

    # Load model
    print("\nLoading model...")
    model, scaler, model_info = load_model_and_scaler(str(models_dir))

    print(f"Model version: {model_info.get('version', 'unknown')}")
    print(f"Last trained: {model_info.get('last_trained', 'unknown')}")

    # Load and prepare data
    print("\nLoading test data...")
    df = pd.read_csv(data_path)
    X = df.drop("Class", axis=1)
    y = df["Class"]

    # Use same split as training
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_test_scaled = scaler.transform(X_test)

    # Make predictions
    print("Making predictions...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    # Standard metrics
    print("\n" + "=" * 60)
    print("STANDARD METRICS")
    print("=" * 60)

    print(f"\nAccuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))

    # Threshold analysis
    evaluate_at_thresholds(y_test, y_prob)

    # Detailed analysis
    analyze_predictions(y_test, y_pred, y_prob)

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
