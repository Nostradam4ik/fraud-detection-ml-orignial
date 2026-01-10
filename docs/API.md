# Fraud Detection API Documentation

## Overview

The Fraud Detection API provides machine learning-powered endpoints for detecting fraudulent credit card transactions. Built with FastAPI and scikit-learn.

**Base URL:** `http://localhost:8000/api/v1`

## Authentication

All endpoints (except `/health` and `/auth/login`) require a JWT bearer token.

```bash
# Login to get token
curl -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" /api/v1/predict
```

---

## Endpoints

### Health Check

#### `GET /health`

Check API status and model health.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

### Authentication

#### `POST /auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com",
  "role": "VIEWER"
}
```

#### `POST /auth/login`

Authenticate and receive JWT token.

**Request Body:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1440
}
```

#### `GET /auth/me`

Get current user profile.

**Headers:** `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "role": "ADMIN",
  "is_2fa_enabled": false
}
```

#### `POST /auth/change-password`

Change user password.

**Request Body:**
```json
{
  "current_password": "oldpass",
  "new_password": "newpass"
}
```

---

### Predictions

#### `POST /predict`

Analyze a single transaction for fraud.

**Request Body:**
```json
{
  "time": 0,
  "amount": 149.62,
  "v1": -1.359807,
  "v2": -0.072781,
  ...
  "v28": -0.021053
}
```

**Response:**
```json
{
  "is_fraud": false,
  "fraud_probability": 0.05,
  "confidence": "high",
  "risk_score": 15,
  "prediction_time_ms": 42.5,
  "features_analyzed": 30,
  "recommendation": "Transaction appears legitimate"
}
```

#### `POST /predict/batch`

Analyze multiple transactions at once.

**Request Body:**
```json
{
  "transactions": [
    {"time": 0, "amount": 149.62, "v1": -1.359, ...},
    {"time": 100, "amount": 250.00, "v1": 1.234, ...}
  ]
}
```

**Response:**
```json
{
  "batch_id": "abc123",
  "total": 2,
  "fraud_count": 0,
  "legitimate_count": 2,
  "results": [...]
}
```

#### `POST /predict/upload-csv`

Upload a CSV file for batch predictions.

**Form Data:** `file` (multipart/form-data)

**Response:** CSV file with predictions

#### `GET /predict/sample/legitimate`

Get a sample legitimate transaction.

#### `GET /predict/sample/fraud`

Get a sample fraudulent transaction.

#### `GET /predict/history`

Get prediction history for current user.

**Query Parameters:**
- `limit` (int, default=50): Max results

**Response:**
```json
[
  {
    "id": 1,
    "amount": 149.62,
    "is_fraud": false,
    "fraud_probability": 0.05,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### `GET /predict/stats`

Get user's prediction statistics.

**Response:**
```json
{
  "total_predictions": 150,
  "fraud_detected": 12,
  "legitimate_detected": 138,
  "fraud_rate": 0.08,
  "average_response_time_ms": 45.2
}
```

---

### Analytics

#### `GET /analytics/stats`

Get global API statistics.

#### `GET /analytics/model`

Get model information and metrics.

**Response:**
```json
{
  "model_type": "RandomForestClassifier",
  "version": "1.0.0",
  "accuracy": 0.9985,
  "precision": 0.9456,
  "recall": 0.7891,
  "f1_score": 0.8605,
  "roc_auc": 0.9821
}
```

#### `GET /analytics/features`

Get feature importance scores.

**Response:**
```json
{
  "V14": 0.152,
  "V17": 0.128,
  "V12": 0.098,
  ...
}
```

#### `GET /analytics/time-series`

Get time series data for charts.

**Query Parameters:**
- `period` (string): `hour`, `day`, `week`, `month`
- `days` (int): Look-back period

**Response:**
```json
[
  {"date": "2024-01-15", "fraud": 2, "legitimate": 48, "total": 50, "fraud_rate": 0.04}
]
```

#### `GET /analytics/predictions/filter`

Advanced prediction filtering with pagination.

**Query Parameters:**
- `start_date`, `end_date`: Date range
- `is_fraud`: Filter by fraud status
- `min_amount`, `max_amount`: Amount range
- `min_risk`, `max_risk`: Risk score range
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "predictions": [...]
}
```

#### `GET /analytics/heatmap`

Get fraud heatmap data by hour and day of week.

---

### Reports

#### `GET /reports/fraud-summary`

Generate PDF fraud summary report.

**Query Parameters:**
- `days` (int, default=30): Period

**Response:** PDF file

#### `GET /reports/export/excel`

Export predictions to Excel.

**Query Parameters:**
- `days` (int, default=30): Period

**Response:** XLSX file

#### `GET /reports/export/excel/fraud-only`

Export only fraud predictions to Excel.

#### `GET /reports/export/excel/high-risk`

Export high-risk predictions to Excel.

**Query Parameters:**
- `days` (int)
- `threshold` (int, default=50): Minimum risk score

#### `GET /reports/export/csv`

Export predictions to CSV.

---

### Admin (Admin role required)

#### `GET /admin/users`

Get all users list.

**Query Parameters:**
- `skip`, `limit`: Pagination

#### `PATCH /admin/users/{user_id}/role`

Change user role.

**Query Parameters:**
- `role`: `VIEWER`, `ANALYST`, `ADMIN`

#### `DELETE /admin/users/{user_id}`

Delete a user.

#### `GET /admin/audit-logs`

Get audit logs.

---

## Rate Limiting

- Default: 100 requests per minute
- Batch endpoints: 10 requests per minute

**Headers returned:**
- `X-RateLimit-Limit`: Max requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## Error Responses

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limited
- `500`: Server Error

---

## Interactive Documentation

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

---

## Example: Full Flow

```python
import requests

BASE = "http://localhost:8000/api/v1"

# 1. Login
resp = requests.post(f"{BASE}/auth/login", json={
    "username": "demo",
    "password": "demo123"
})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Make prediction
transaction = {
    "time": 0,
    "amount": 149.62,
    "v1": -1.359807,
    "v2": -0.072781,
    # ... v3-v28
}
result = requests.post(f"{BASE}/predict", json=transaction, headers=headers)
print(result.json())

# 3. Get statistics
stats = requests.get(f"{BASE}/predict/stats", headers=headers)
print(stats.json())

# 4. Export to Excel
excel = requests.get(f"{BASE}/reports/export/excel?days=30", headers=headers)
with open("export.xlsx", "wb") as f:
    f.write(excel.content)
```
