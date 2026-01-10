"""Data preprocessing utilities"""

from typing import List

import numpy as np

from ..models.schemas import TransactionInput


class DataProcessor:
    """Process and transform transaction data for ML model"""

    @staticmethod
    def transaction_to_array(transaction: TransactionInput) -> np.ndarray:
        """Convert a TransactionInput to numpy array for model prediction"""
        return np.array([
            transaction.time,
            transaction.v1,
            transaction.v2,
            transaction.v3,
            transaction.v4,
            transaction.v5,
            transaction.v6,
            transaction.v7,
            transaction.v8,
            transaction.v9,
            transaction.v10,
            transaction.v11,
            transaction.v12,
            transaction.v13,
            transaction.v14,
            transaction.v15,
            transaction.v16,
            transaction.v17,
            transaction.v18,
            transaction.v19,
            transaction.v20,
            transaction.v21,
            transaction.v22,
            transaction.v23,
            transaction.v24,
            transaction.v25,
            transaction.v26,
            transaction.v27,
            transaction.v28,
            transaction.amount,
        ])

    @staticmethod
    def transactions_to_batch(transactions: List[TransactionInput]) -> np.ndarray:
        """Convert list of transactions to numpy array for batch prediction"""
        return np.array([
            DataProcessor.transaction_to_array(t) for t in transactions
        ])

    @staticmethod
    def generate_sample_transaction(is_fraud: bool = False) -> dict:
        """Generate a sample transaction for testing"""
        # Don't use fixed seed - generate random each time

        if is_fraud:
            # Fraud transactions: match the pattern from training data
            # Base features: normal distribution with higher variance
            base_features = np.random.randn(28) * 2.5

            # Add positive shift to specific features (V1, V3, V4, V11, V12, V13, V15, V17, V18)
            # These are indices 0, 2, 3, 10, 11, 12, 14, 16, 17 in the features array
            fraud_indices = [0, 2, 3, 10, 11, 12, 14, 16, 17]
            for idx in fraud_indices:
                base_features[idx] += np.random.uniform(2, 5)

            return {
                "time": float(np.random.uniform(0, 172792)),
                "v1": float(base_features[0]),
                "v2": float(base_features[1]),
                "v3": float(base_features[2]),
                "v4": float(base_features[3]),
                "v5": float(base_features[4]),
                "v6": float(base_features[5]),
                "v7": float(base_features[6]),
                "v8": float(base_features[7]),
                "v9": float(base_features[8]),
                "v10": float(base_features[9]),
                "v11": float(base_features[10]),
                "v12": float(base_features[11]),
                "v13": float(base_features[12]),
                "v14": float(base_features[13]),
                "v15": float(base_features[14]),
                "v16": float(base_features[15]),
                "v17": float(base_features[16]),
                "v18": float(base_features[17]),
                "v19": float(base_features[18]),
                "v20": float(base_features[19]),
                "v21": float(base_features[20]),
                "v22": float(base_features[21]),
                "v23": float(base_features[22]),
                "v24": float(base_features[23]),
                "v25": float(base_features[24]),
                "v26": float(base_features[25]),
                "v27": float(base_features[26]),
                "v28": float(base_features[27]),
                "amount": float(np.random.uniform(500, 2000)),  # Large amount for fraud
            }
        else:
            # Normal transaction patterns
            return {
                "time": float(np.random.uniform(0, 172792)),
                "v1": float(np.random.normal(0, 1)),
                "v2": float(np.random.normal(0, 1)),
                "v3": float(np.random.normal(0, 1)),
                "v4": float(np.random.normal(0, 1)),
                "v5": float(np.random.normal(0, 1)),
                "v6": float(np.random.normal(0, 1)),
                "v7": float(np.random.normal(0, 1)),
                "v8": float(np.random.normal(0, 1)),
                "v9": float(np.random.normal(0, 1)),
                "v10": float(np.random.normal(0, 1)),
                "v11": float(np.random.normal(0, 1)),
                "v12": float(np.random.normal(0, 1)),
                "v13": float(np.random.normal(0, 1)),
                "v14": float(np.random.normal(0, 1)),
                "v15": float(np.random.normal(0, 1)),
                "v16": float(np.random.normal(0, 1)),
                "v17": float(np.random.normal(0, 1)),
                "v18": float(np.random.normal(0, 1)),
                "v19": float(np.random.normal(0, 1)),
                "v20": float(np.random.normal(0, 1)),
                "v21": float(np.random.normal(0, 1)),
                "v22": float(np.random.normal(0, 1)),
                "v23": float(np.random.normal(0, 1)),
                "v24": float(np.random.normal(0, 1)),
                "v25": float(np.random.normal(0, 1)),
                "v26": float(np.random.normal(0, 1)),
                "v27": float(np.random.normal(0, 1)),
                "v28": float(np.random.normal(0, 1)),
                "amount": float(np.random.uniform(10, 200)),
            }
