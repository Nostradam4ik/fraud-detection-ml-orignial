"""
Locust Load Testing for Fraud Detection API

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Or headless:
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class FraudDetectionUser(HttpUser):
    """Simulates a user interacting with the Fraud Detection API"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None

    def on_start(self):
        """Login on start"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "Nostradam",
                "password": "test123456"
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code}")

    @property
    def headers(self):
        """Get authorization headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(10)
    def health_check(self):
        """Check API health - most common request"""
        self.client.get("/api/v1/health")

    @task(5)
    def single_prediction(self):
        """Make a single fraud prediction"""
        transaction = self._generate_transaction()
        self.client.post(
            "/api/v1/predict",
            json=transaction,
            headers=self.headers
        )

    @task(2)
    def batch_prediction(self):
        """Make batch predictions"""
        transactions = [self._generate_transaction() for _ in range(10)]
        self.client.post(
            "/api/v1/predict/batch",
            json={"transactions": transactions},
            headers=self.headers
        )

    @task(3)
    def get_prediction_history(self):
        """Get prediction history"""
        self.client.get(
            "/api/v1/predict/history?limit=50",
            headers=self.headers
        )

    @task(3)
    def get_prediction_stats(self):
        """Get user prediction stats"""
        self.client.get(
            "/api/v1/predict/stats",
            headers=self.headers
        )

    @task(2)
    def get_analytics_stats(self):
        """Get analytics stats"""
        self.client.get(
            "/api/v1/analytics/stats",
            headers=self.headers
        )

    @task(2)
    def get_time_series(self):
        """Get time series data"""
        self.client.get(
            "/api/v1/analytics/time-series?period=day&days=30",
            headers=self.headers
        )

    @task(1)
    def get_model_info(self):
        """Get model information"""
        self.client.get(
            "/api/v1/analytics/model",
            headers=self.headers
        )

    @task(1)
    def get_feature_importance(self):
        """Get feature importance"""
        self.client.get(
            "/api/v1/analytics/features",
            headers=self.headers
        )

    @task(1)
    def get_sample_legitimate(self):
        """Get sample legitimate transaction"""
        self.client.get("/api/v1/predict/sample/legitimate")

    @task(1)
    def get_sample_fraud(self):
        """Get sample fraud transaction"""
        self.client.get("/api/v1/predict/sample/fraud")

    def _generate_transaction(self):
        """Generate a random transaction for testing"""
        # Random legitimate or fraud pattern
        is_fraud = random.random() < 0.1  # 10% fraud rate

        if is_fraud:
            return {
                "time": random.uniform(100000, 200000),
                "amount": random.uniform(500, 5000),
                **{f"v{i}": random.gauss(-2, 2) for i in range(1, 29)}
            }
        else:
            return {
                "time": random.uniform(0, 200000),
                "amount": random.uniform(1, 500),
                **{f"v{i}": random.gauss(0, 1) for i in range(1, 29)}
            }


class AdminUser(HttpUser):
    """Simulates an admin user - less frequent"""

    wait_time = between(5, 10)
    weight = 1  # Lower weight = fewer users
    token = None

    def on_start(self):
        """Login as admin"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "Nostradam",
                "password": "test123456"
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @property
    def headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(3)
    def get_system_stats(self):
        """Get system statistics (admin)"""
        self.client.get(
            "/api/v1/admin/stats",
            headers=self.headers
        )

    @task(2)
    def get_users(self):
        """Get users list (admin)"""
        self.client.get(
            "/api/v1/admin/users",
            headers=self.headers
        )

    @task(1)
    def get_audit_logs(self):
        """Get audit logs (admin)"""
        self.client.get(
            "/api/v1/admin/audit-logs",
            headers=self.headers
        )

    @task(2)
    def detailed_health(self):
        """Get detailed health status"""
        self.client.get("/api/v1/health/detailed")

    @task(1)
    def get_metrics(self):
        """Get Prometheus metrics"""
        self.client.get("/api/v1/metrics")


class APIStressTest(HttpUser):
    """High-frequency stress test user"""

    wait_time = between(0.1, 0.5)  # Very fast
    weight = 1  # Few users for stress test
    token = None

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "Nostradam", "password": "test123456"}
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @property
    def headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task
    def rapid_predictions(self):
        """Rapid fire predictions to stress test"""
        transaction = {
            "time": random.uniform(0, 200000),
            "amount": random.uniform(1, 1000),
            **{f"v{i}": random.gauss(0, 1) for i in range(1, 29)}
        }
        self.client.post(
            "/api/v1/predict",
            json=transaction,
            headers=self.headers
        )


# Event hooks for custom reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests"""
    if response_time > 1000:  # More than 1 second
        print(f"SLOW REQUEST: {request_type} {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("=" * 50)
    print("Starting Fraud Detection API Load Test")
    print("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("=" * 50)
    print("Load Test Complete!")
    print("=" * 50)
