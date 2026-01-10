"""Tests for ML model and services"""

import numpy as np
import pytest

from app.models.ml_model import FraudDetectionModel
from app.services.data_processor import DataProcessor


class TestFraudDetectionModel:
    """Tests for FraudDetectionModel class"""

    def test_confidence_level_low(self):
        """Test low confidence classification"""
        assert FraudDetectionModel.get_confidence_level(0.1) == "low"
        assert FraudDetectionModel.get_confidence_level(0.29) == "low"

    def test_confidence_level_medium(self):
        """Test medium confidence classification"""
        assert FraudDetectionModel.get_confidence_level(0.3) == "medium"
        assert FraudDetectionModel.get_confidence_level(0.5) == "medium"
        assert FraudDetectionModel.get_confidence_level(0.69) == "medium"

    def test_confidence_level_high(self):
        """Test high confidence classification"""
        assert FraudDetectionModel.get_confidence_level(0.7) == "high"
        assert FraudDetectionModel.get_confidence_level(0.9) == "high"
        assert FraudDetectionModel.get_confidence_level(1.0) == "high"

    def test_risk_score_range(self):
        """Test risk score is in valid range"""
        assert FraudDetectionModel.get_risk_score(0.0) == 0
        assert FraudDetectionModel.get_risk_score(0.5) == 50
        assert FraudDetectionModel.get_risk_score(1.0) == 100

    def test_feature_names(self):
        """Test feature names are correctly defined"""
        model = FraudDetectionModel()
        assert len(model.FEATURE_NAMES) == 30
        assert "Time" in model.FEATURE_NAMES
        assert "Amount" in model.FEATURE_NAMES
        assert "V1" in model.FEATURE_NAMES
        assert "V28" in model.FEATURE_NAMES


class TestDataProcessor:
    """Tests for DataProcessor class"""

    def test_transaction_to_array_shape(self):
        """Test that transaction converts to correct array shape"""
        from app.models.schemas import TransactionInput

        sample = DataProcessor.generate_sample_transaction()
        transaction = TransactionInput(**sample)
        array = DataProcessor.transaction_to_array(transaction)

        assert isinstance(array, np.ndarray)
        assert array.shape == (30,)

    def test_transactions_to_batch_shape(self):
        """Test that batch conversion has correct shape"""
        from app.models.schemas import TransactionInput

        samples = [
            DataProcessor.generate_sample_transaction() for _ in range(5)
        ]
        transactions = [TransactionInput(**s) for s in samples]
        batch = DataProcessor.transactions_to_batch(transactions)

        assert isinstance(batch, np.ndarray)
        assert batch.shape == (5, 30)

    def test_sample_transactions_different(self):
        """Test that fraud and legitimate samples have different patterns"""
        legitimate = DataProcessor.generate_sample_transaction(is_fraud=False)
        fraud = DataProcessor.generate_sample_transaction(is_fraud=True)

        # Fraud transactions typically have higher amounts in our generator
        assert fraud["amount"] != legitimate["amount"]

    def test_sample_transaction_valid_values(self):
        """Test that generated samples have valid values"""
        sample = DataProcessor.generate_sample_transaction()

        assert sample["time"] >= 0
        assert sample["amount"] >= 0
        assert all(f"v{i}" in sample for i in range(1, 29))
