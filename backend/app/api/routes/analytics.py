"""Analytics and statistics endpoints"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...db.database import get_db
from ...db.models import Prediction
from ...models.schemas import ModelInfo, StatsResponse, UserResponse
from ...models.ml_model import fraud_model
from ...services.fraud_detector import FraudDetectorService
from ...services.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get API usage statistics",
    description="Get statistics about API usage and predictions",
)
async def get_stats() -> StatsResponse:
    """
    Get API usage statistics including:
    - Total predictions made
    - Fraud detection count
    - Average response time
    - API uptime
    """
    return FraudDetectorService.get_stats()


@router.get(
    "/model",
    response_model=ModelInfo,
    summary="Get model information",
    description="Get details about the ML model",
)
async def get_model_info() -> ModelInfo:
    """
    Get information about the fraud detection model including:
    - Model type and version
    - Training data statistics
    - Performance metrics (accuracy, precision, recall, F1, ROC-AUC)
    """
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model files exist.",
        )

    return FraudDetectorService.get_model_info()


@router.get(
    "/features",
    response_model=Dict[str, float],
    summary="Get feature importance",
    description="Get the importance score for each feature",
)
async def get_feature_importance() -> Dict[str, float]:
    """
    Get feature importance scores from the model.
    Higher scores indicate more important features for fraud detection.
    """
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model files exist.",
        )

    try:
        return FraudDetectorService.get_feature_importance()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting feature importance: {str(e)}"
        )


@router.get(
    "/time-series",
    summary="Get time series analytics",
    description="Get prediction data aggregated by time period for charts."
)
async def get_time_series(
    period: str = Query("day", description="Aggregation period: hour, day, week, month"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get time series data for fraud predictions.

    Returns aggregated counts of fraud vs legitimate predictions over time.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query predictions in date range
    predictions = (
        db.query(Prediction)
        .filter(
            Prediction.user_id == int(current_user.id),
            Prediction.created_at >= start_date
        )
        .order_by(Prediction.created_at)
        .all()
    )

    # Aggregate by period
    data = {}
    for p in predictions:
        if period == "hour":
            key = p.created_at.strftime("%Y-%m-%d %H:00")
        elif period == "week":
            key = p.created_at.strftime("%Y-W%W")
        elif period == "month":
            key = p.created_at.strftime("%Y-%m")
        else:  # day
            key = p.created_at.strftime("%Y-%m-%d")

        if key not in data:
            data[key] = {"date": key, "fraud": 0, "legitimate": 0, "total": 0}

        data[key]["total"] += 1
        if p.is_fraud:
            data[key]["fraud"] += 1
        else:
            data[key]["legitimate"] += 1

    # Convert to list and calculate rates
    result = []
    for key in sorted(data.keys()):
        item = data[key]
        item["fraud_rate"] = item["fraud"] / item["total"] if item["total"] > 0 else 0
        result.append(item)

    return result


@router.get(
    "/predictions/filter",
    summary="Filter predictions",
    description="Get filtered prediction history with advanced filtering options."
)
async def filter_predictions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_fraud: Optional[bool] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    min_risk: Optional[int] = Query(None, ge=0, le=100),
    max_risk: Optional[int] = Query(None, ge=0, le=100),
    confidence: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get filtered predictions with advanced options.

    Supports filtering by:
    - Date range
    - Fraud status
    - Amount range
    - Risk score range
    - Confidence level
    - Batch ID
    """
    query = db.query(Prediction).filter(Prediction.user_id == int(current_user.id))

    # Apply filters
    if start_date:
        query = query.filter(Prediction.created_at >= start_date)
    if end_date:
        query = query.filter(Prediction.created_at <= end_date)
    if is_fraud is not None:
        query = query.filter(Prediction.is_fraud == is_fraud)
    if min_amount is not None:
        query = query.filter(Prediction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Prediction.amount <= max_amount)
    if min_risk is not None:
        query = query.filter(Prediction.risk_score >= min_risk)
    if max_risk is not None:
        query = query.filter(Prediction.risk_score <= max_risk)
    if confidence:
        query = query.filter(Prediction.confidence == confidence)
    if batch_id:
        query = query.filter(Prediction.batch_id == batch_id)

    # Count total before pagination
    total = query.count()

    # Sorting
    sort_column = getattr(Prediction, sort_by, Prediction.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    predictions = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "predictions": [
            {
                "id": p.id,
                "time": p.time,
                "amount": p.amount,
                "is_fraud": p.is_fraud,
                "fraud_probability": p.fraud_probability,
                "confidence": p.confidence,
                "risk_score": p.risk_score,
                "prediction_time_ms": p.prediction_time_ms,
                "batch_id": p.batch_id,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in predictions
        ]
    }


@router.get(
    "/summary",
    summary="Get analytics summary",
    description="Get a summary of prediction analytics for the current user."
)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get an analytics summary including:
    - Total predictions
    - Fraud rate
    - Average amounts
    - Risk distribution
    - Trend analysis
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get predictions in range
    predictions = (
        db.query(Prediction)
        .filter(
            Prediction.user_id == int(current_user.id),
            Prediction.created_at >= start_date
        )
        .all()
    )

    if not predictions:
        return {
            "period_days": days,
            "total_predictions": 0,
            "fraud_count": 0,
            "legitimate_count": 0,
            "fraud_rate": 0,
            "avg_amount": 0,
            "avg_fraud_amount": 0,
            "avg_legitimate_amount": 0,
            "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "trend": "stable"
        }

    total = len(predictions)
    fraud = [p for p in predictions if p.is_fraud]
    legitimate = [p for p in predictions if not p.is_fraud]

    # Calculate averages
    avg_amount = sum(p.amount for p in predictions) / total
    avg_fraud_amount = sum(p.amount for p in fraud) / len(fraud) if fraud else 0
    avg_legitimate_amount = sum(p.amount for p in legitimate) / len(legitimate) if legitimate else 0

    # Risk distribution
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for p in predictions:
        if p.risk_score < 25:
            risk_dist["low"] += 1
        elif p.risk_score < 50:
            risk_dist["medium"] += 1
        elif p.risk_score < 75:
            risk_dist["high"] += 1
        else:
            risk_dist["critical"] += 1

    # Calculate trend (compare first half vs second half)
    mid_date = start_date + timedelta(days=days // 2)
    first_half = [p for p in predictions if p.created_at < mid_date]
    second_half = [p for p in predictions if p.created_at >= mid_date]

    first_fraud_rate = len([p for p in first_half if p.is_fraud]) / len(first_half) if first_half else 0
    second_fraud_rate = len([p for p in second_half if p.is_fraud]) / len(second_half) if second_half else 0

    if second_fraud_rate > first_fraud_rate * 1.1:
        trend = "increasing"
    elif second_fraud_rate < first_fraud_rate * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "period_days": days,
        "total_predictions": total,
        "fraud_count": len(fraud),
        "legitimate_count": len(legitimate),
        "fraud_rate": len(fraud) / total,
        "avg_amount": round(avg_amount, 2),
        "avg_fraud_amount": round(avg_fraud_amount, 2),
        "avg_legitimate_amount": round(avg_legitimate_amount, 2),
        "risk_distribution": risk_dist,
        "trend": trend
    }


@router.get(
    "/shap/{prediction_id}",
    summary="Get SHAP explanations",
    description="Get SHAP values for a specific prediction to explain the model's decision."
)
async def get_shap_explanation(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get SHAP explanation for a prediction.

    Returns feature contributions showing which features most influenced
    the fraud/legitimate decision.
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == int(current_user.id)
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # If SHAP values are stored, return them
    if prediction.shap_values:
        import json
        return {
            "prediction_id": prediction_id,
            "is_fraud": prediction.is_fraud,
            "fraud_probability": prediction.fraud_probability,
            "shap_values": json.loads(prediction.shap_values)
        }

    # Otherwise, try to calculate them
    try:
        import json
        features_dict = json.loads(prediction.features_json)

        # Try to get SHAP values from the model
        shap_values = FraudDetectorService.get_shap_values_for_prediction(
            prediction.time,
            prediction.amount,
            features_dict
        )

        return {
            "prediction_id": prediction_id,
            "is_fraud": prediction.is_fraud,
            "fraud_probability": prediction.fraud_probability,
            "shap_values": shap_values
        }
    except Exception as e:
        # Return a simplified explanation if SHAP is not available
        return {
            "prediction_id": prediction_id,
            "is_fraud": prediction.is_fraud,
            "fraud_probability": prediction.fraud_probability,
            "shap_values": None,
            "message": "SHAP explanations not available for this prediction"
        }


@router.get(
    "/compare-periods",
    summary="Compare two time periods",
    description="Compare fraud statistics between two time periods for trend analysis."
)
async def compare_periods(
    period1_start: datetime = Query(..., description="Start of first period"),
    period1_end: datetime = Query(..., description="End of first period"),
    period2_start: datetime = Query(..., description="Start of second period"),
    period2_end: datetime = Query(..., description="End of second period"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Compare fraud statistics between two time periods.

    Returns metrics for both periods and percentage changes.
    """

    def get_period_stats(start: datetime, end: datetime) -> dict:
        predictions = (
            db.query(Prediction)
            .filter(
                Prediction.user_id == int(current_user.id),
                Prediction.created_at >= start,
                Prediction.created_at <= end
            )
            .all()
        )

        total = len(predictions)
        if total == 0:
            return {
                "total": 0,
                "fraud_count": 0,
                "legitimate_count": 0,
                "fraud_rate": 0,
                "avg_amount": 0,
                "total_amount": 0,
                "avg_risk_score": 0,
                "high_risk_count": 0
            }

        fraud = [p for p in predictions if p.is_fraud]
        return {
            "total": total,
            "fraud_count": len(fraud),
            "legitimate_count": total - len(fraud),
            "fraud_rate": len(fraud) / total,
            "avg_amount": sum(p.amount for p in predictions) / total,
            "total_amount": sum(p.amount for p in predictions),
            "avg_risk_score": sum(p.risk_score for p in predictions) / total,
            "high_risk_count": sum(1 for p in predictions if p.risk_score >= 70)
        }

    period1_stats = get_period_stats(period1_start, period1_end)
    period2_stats = get_period_stats(period2_start, period2_end)

    def calc_change(old_val, new_val) -> Optional[float]:
        if old_val == 0:
            return None if new_val == 0 else 100.0
        return ((new_val - old_val) / old_val) * 100

    return {
        "period1": {
            "start": period1_start.isoformat(),
            "end": period1_end.isoformat(),
            "stats": period1_stats
        },
        "period2": {
            "start": period2_start.isoformat(),
            "end": period2_end.isoformat(),
            "stats": period2_stats
        },
        "changes": {
            "total_change": calc_change(period1_stats["total"], period2_stats["total"]),
            "fraud_count_change": calc_change(period1_stats["fraud_count"], period2_stats["fraud_count"]),
            "fraud_rate_change": calc_change(period1_stats["fraud_rate"], period2_stats["fraud_rate"]),
            "avg_amount_change": calc_change(period1_stats["avg_amount"], period2_stats["avg_amount"]),
            "total_amount_change": calc_change(period1_stats["total_amount"], period2_stats["total_amount"]),
            "avg_risk_change": calc_change(period1_stats["avg_risk_score"], period2_stats["avg_risk_score"]),
            "high_risk_change": calc_change(period1_stats["high_risk_count"], period2_stats["high_risk_count"])
        }
    }


@router.get(
    "/heatmap",
    summary="Get fraud heatmap data",
    description="Get fraud distribution by hour and day of week for heatmap visualization."
)
async def get_heatmap_data(
    days: int = Query(30, ge=7, le=365),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get heatmap data showing fraud distribution by hour and day of week.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    predictions = (
        db.query(Prediction)
        .filter(
            Prediction.user_id == int(current_user.id),
            Prediction.created_at >= start_date
        )
        .all()
    )

    # Initialize heatmap data
    heatmap = {}
    for day in range(7):  # 0=Monday, 6=Sunday
        for hour in range(24):
            key = f"{day}_{hour}"
            heatmap[key] = {"total": 0, "fraud": 0}

    # Aggregate predictions
    for p in predictions:
        if p.created_at:
            day = p.created_at.weekday()
            hour = p.created_at.hour
            key = f"{day}_{hour}"
            heatmap[key]["total"] += 1
            if p.is_fraud:
                heatmap[key]["fraud"] += 1

    # Convert to list format for frontend
    result = []
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in range(7):
        for hour in range(24):
            key = f"{day}_{hour}"
            data = heatmap[key]
            fraud_rate = data["fraud"] / data["total"] if data["total"] > 0 else 0
            result.append({
                "day": day,
                "dayName": day_names[day],
                "hour": hour,
                "total": data["total"],
                "fraud": data["fraud"],
                "fraud_rate": fraud_rate
            })

    return {
        "data": result,
        "period_days": days,
        "max_fraud_rate": max(r["fraud_rate"] for r in result) if result else 0
    }
