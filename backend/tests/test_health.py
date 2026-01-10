"""
Health Check Tests

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import pytest


class TestHealth:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "author" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data
        assert "timestamp" in data


class TestAnalytics:
    """Test analytics endpoints"""

    def test_get_stats(self, client):
        """Test getting API stats"""
        response = client.get("/api/v1/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "fraud_detected" in data
        assert "legitimate_detected" in data

    def test_get_model_info(self, client):
        """Test getting model info"""
        response = client.get("/api/v1/analytics/model")
        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert "model_version" in data
        assert "features_count" in data

    def test_get_feature_importance(self, client):
        """Test getting feature importance"""
        response = client.get("/api/v1/analytics/features")
        assert response.status_code == 200
        data = response.json()
        # API returns dict with feature names as keys
        assert isinstance(data, dict)
        assert len(data) > 0
