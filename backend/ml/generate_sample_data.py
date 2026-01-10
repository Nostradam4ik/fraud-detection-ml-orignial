"""
Generate synthetic credit card transaction data for testing

This creates a dataset similar to the Kaggle Credit Card Fraud dataset
with 30 features (Time, V1-V28, Amount, Class)
"""

import numpy as np
import pandas as pd
from pathlib import Path

def generate_synthetic_data(n_samples=10000, fraud_ratio=0.002):
    """
    Generate synthetic credit card transaction data

    Args:
        n_samples: Number of samples to generate
        fraud_ratio: Ratio of fraudulent transactions (default: 0.2%)
    """
    print(f"Generating {n_samples} synthetic transactions...")

    np.random.seed(42)

    # Calculate number of fraud cases
    n_fraud = int(n_samples * fraud_ratio)
    n_normal = n_samples - n_fraud

    # Generate Time feature (seconds elapsed)
    time = np.random.uniform(0, 172800, n_samples)  # 48 hours

    # Generate V1-V28 features (PCA components)
    # Normal transactions: centered around 0
    normal_features = np.random.randn(n_normal, 28) * 1.5

    # Fraudulent transactions: shifted distribution
    fraud_features = np.random.randn(n_fraud, 28) * 2.5
    fraud_features[:, [0, 2, 3, 10, 11, 12, 14, 16, 17]] += np.random.uniform(2, 5, (n_fraud, 9))

    # Combine features
    V_features = np.vstack([normal_features, fraud_features])

    # Generate Amount feature
    # Normal: mostly small amounts
    normal_amounts = np.random.gamma(2, 30, n_normal)
    # Fraud: mixture of small and large amounts
    fraud_amounts = np.concatenate([
        np.random.gamma(2, 30, n_fraud // 2),  # Small amounts
        np.random.uniform(200, 2000, n_fraud - n_fraud // 2)  # Large amounts
    ])
    amounts = np.concatenate([normal_amounts, fraud_amounts])

    # Create labels
    labels = np.concatenate([np.zeros(n_normal), np.ones(n_fraud)])

    # Shuffle data
    indices = np.random.permutation(n_samples)

    # Create DataFrame
    data = {
        'Time': time[indices],
        **{f'V{i}': V_features[indices, i-1] for i in range(1, 29)},
        'Amount': amounts[indices],
        'Class': labels[indices].astype(int)
    }

    df = pd.DataFrame(data)

    print(f"Dataset shape: {df.shape}")
    print(f"Fraud cases: {df['Class'].sum()} ({df['Class'].mean()*100:.2f}%)")

    return df


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate data with 2% fraud rate (200 fraud cases)
    df = generate_synthetic_data(n_samples=10000, fraud_ratio=0.02)

    # Save to CSV
    output_path = data_dir / "creditcard.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSynthetic data saved to: {output_path}")
    print("\nNote: This is synthetic data for testing purposes only.")
    print("For production, use the real Kaggle dataset:")
    print("https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
