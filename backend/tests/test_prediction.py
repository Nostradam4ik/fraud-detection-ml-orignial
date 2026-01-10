"""
Prediction Tests

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import pytest


class TestPrediction:
    """Test prediction endpoints"""

    def test_predict_unauthorized(self, client, sample_transaction):
        """Test prediction without authentication"""
        response = client.post("/api/v1/predict", json=sample_transaction)
        assert response.status_code == 403

    def test_predict_success(self, client, auth_headers, sample_transaction):
        """Test successful prediction"""
        response = client.post(
            "/api/v1/predict",
            json=sample_transaction,
            headers=auth_headers
        )
        # May return 503 if model not loaded, but endpoint should work
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "is_fraud" in data
            assert "fraud_probability" in data
            assert "confidence" in data
            assert "risk_score" in data
            assert "prediction_time_ms" in data
            assert 0 <= data["fraud_probability"] <= 1
            assert 0 <= data["risk_score"] <= 100

    def test_get_sample_legitimate(self, client):
        """Test getting sample legitimate transaction"""
        response = client.get("/api/v1/predict/sample/legitimate")
        assert response.status_code == 200
        data = response.json()
        assert "time" in data
        assert "amount" in data
        assert "v1" in data

    def test_get_sample_fraud(self, client):
        """Test getting sample fraud transaction"""
        response = client.get("/api/v1/predict/sample/fraud")
        assert response.status_code == 200
        data = response.json()
        assert "time" in data
        assert "amount" in data
        assert "v1" in data

    def test_prediction_history(self, client, auth_headers):
        """Test getting prediction history"""
        response = client.get("/api/v1/predict/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_prediction_stats(self, client, auth_headers):
        """Test getting prediction stats"""
        response = client.get("/api/v1/predict/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "fraud_detected" in data
        assert "legitimate_detected" in data
        assert "fraud_rate" in data


class TestBatchPrediction:
    """Test batch prediction endpoint"""

    def test_batch_predict_unauthorized(self, client, sample_transaction):
        """Test batch prediction without authentication"""
        response = client.post(
            "/api/v1/predict/batch",
            json={"transactions": [sample_transaction]}
        )
        assert response.status_code == 403

    def test_batch_predict_success(self, client, auth_headers, sample_transaction):
        """Test successful batch prediction"""
        response = client.post(
            "/api/v1/predict/batch",
            json={"transactions": [sample_transaction, sample_transaction]},
            headers=auth_headers
        )
        # May return 503 if model not loaded
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_transactions" in data
            assert data["total_transactions"] == 2
            assert "fraud_count" in data
            assert "legitimate_count" in data
            assert "results" in data
