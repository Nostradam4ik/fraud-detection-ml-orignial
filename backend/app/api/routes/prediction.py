"""Prediction endpoints"""

import uuid
import io
from typing import Dict, List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...models.schemas import (
    TransactionInput,
    PredictionResponse,
    BatchPredictionInput,
    BatchPredictionResponse,
    UserResponse,
)
from ...models.ml_model import fraud_model
from ...services.fraud_detector import FraudDetectorService
from ...services.data_processor import DataProcessor
from ...services.auth_service import get_current_user
from ...services.prediction_service import save_prediction, get_user_predictions, get_user_prediction_stats, save_batch_predictions
from ...db.database import get_db
from ...db.models import AuditAction
from ...services.audit_service import log_action
from ...core.rate_limit import limiter
from ...core.config import settings

router = APIRouter()


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Predict fraud for a single transaction",
    description="Analyze a transaction and predict if it's fraudulent. Requires authentication.",
)
async def predict_fraud(
    request: Request,
    transaction: TransactionInput,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionResponse:
    """
    Predict if a single transaction is fraudulent.

    - **time**: Seconds elapsed since first transaction in dataset
    - **v1-v28**: PCA transformed features (anonymized)
    - **amount**: Transaction amount

    Returns prediction with probability, confidence level, and risk score.
    """
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model files exist.",
        )

    try:
        result = FraudDetectorService.predict_single(transaction)

        # Save prediction to database
        save_prediction(db, int(current_user.id), transaction, result)

        return result
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Prediction error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Predict fraud for multiple transactions",
    description="Analyze multiple transactions in a single request. Requires authentication.",
)
async def predict_fraud_batch(
    request: Request,
    batch: BatchPredictionInput,
    current_user: UserResponse = Depends(get_current_user)
) -> BatchPredictionResponse:
    """
    Predict fraud for multiple transactions at once.

    Maximum 1000 transactions per batch.
    Returns summary statistics and individual predictions.
    """
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model files exist.",
        )

    try:
        return FraudDetectorService.predict_batch(batch.transactions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


@router.get(
    "/history",
    summary="Get prediction history",
    description="Get the authenticated user's prediction history.",
)
async def get_history(
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get the user's prediction history from database."""
    predictions = get_user_predictions(db, int(current_user.id), limit=limit)

    return [
        {
            "id": p.id,
            "time": p.time,
            "amount": p.amount,
            "is_fraud": p.is_fraud,
            "fraud_probability": p.fraud_probability,
            "confidence": p.confidence,
            "risk_score": p.risk_score,
            "prediction_time_ms": p.prediction_time_ms,
            "created_at": p.created_at.isoformat()
        }
        for p in predictions
    ]


@router.get(
    "/stats",
    summary="Get user prediction stats",
    description="Get prediction statistics for the authenticated user.",
)
async def get_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get the user's prediction statistics."""
    return get_user_prediction_stats(db, int(current_user.id))


@router.get(
    "/sample/legitimate",
    response_model=Dict,
    summary="Get sample legitimate transaction",
    description="Generate a sample transaction that is likely legitimate",
)
async def get_sample_legitimate() -> Dict:
    """Get a sample transaction with typical legitimate patterns for testing."""
    return DataProcessor.generate_sample_transaction(is_fraud=False)


@router.get(
    "/sample/fraud",
    response_model=Dict,
    summary="Get sample fraudulent transaction",
    description="Generate a sample transaction that is likely fraudulent",
)
async def get_sample_fraud() -> Dict:
    """Get a sample transaction with typical fraud patterns for testing."""
    return DataProcessor.generate_sample_transaction(is_fraud=True)


@router.post(
    "/upload-csv",
    summary="Upload CSV for batch prediction",
    description="Upload a CSV file with transactions for batch fraud prediction.",
)
async def upload_csv_predictions(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file with transactions for batch prediction.

    CSV format should have columns: time, amount, v1, v2, ... v28
    Maximum file size: 10MB
    Maximum rows: 10000

    Returns a CSV file with predictions added.
    """
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model files exist.",
        )

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Read file content
    content = await file.read()

    # Check file size (10MB limit)
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_upload_size // (1024*1024)}MB"
        )

    try:
        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))

        # Check row limit
        if len(df) > 10000:
            raise HTTPException(status_code=400, detail="Maximum 10000 rows allowed")

        # Validate columns
        required_cols = ['time', 'amount'] + [f'v{i}' for i in range(1, 29)]
        missing_cols = [col for col in required_cols if col.lower() not in [c.lower() for c in df.columns]]

        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(missing_cols)}"
            )

        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()

        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Process each row
        predictions = []
        for _, row in df.iterrows():
            transaction = TransactionInput(
                time=float(row['time']),
                amount=float(row['amount']),
                **{f'v{i}': float(row[f'v{i}']) for i in range(1, 29)}
            )

            result = FraudDetectorService.predict_single(transaction)
            predictions.append({
                'is_fraud': result.is_fraud,
                'fraud_probability': result.fraud_probability,
                'confidence': result.confidence,
                'risk_score': result.risk_score
            })

        # Add predictions to dataframe
        df['is_fraud'] = [p['is_fraud'] for p in predictions]
        df['fraud_probability'] = [p['fraud_probability'] for p in predictions]
        df['confidence'] = [p['confidence'] for p in predictions]
        df['risk_score'] = [p['risk_score'] for p in predictions]

        # Save batch predictions to database
        save_batch_predictions(db, int(current_user.id), df, batch_id)

        # Log the action
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:255]
        log_action(
            db, AuditAction.BATCH_PREDICTION,
            user_id=int(current_user.id),
            resource_type="batch",
            resource_id=batch_id,
            details={
                "rows": len(df),
                "fraud_count": sum(1 for p in predictions if p['is_fraud']),
                "filename": file.filename
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Generate result CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        # Count fraud
        fraud_count = sum(1 for p in predictions if p['is_fraud'])

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=predictions_{batch_id[:8]}.csv",
                "X-Batch-ID": batch_id,
                "X-Total-Rows": str(len(df)),
                "X-Fraud-Count": str(fraud_count),
                "X-Legitimate-Count": str(len(df) - fraud_count)
            }
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logging.error(f"CSV upload error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
