"""AI Fraud Explainer API - Generates natural language explanations for fraud predictions"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import json

from ...db.database import get_db
from ...db.models import Prediction, User
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/explain", tags=["AI Explainer"])


class ExplanationRequest(BaseModel):
    prediction_id: Optional[int] = None
    # Or provide transaction data directly
    amount: Optional[float] = None
    risk_score: Optional[int] = None
    fraud_probability: Optional[float] = None
    is_fraud: Optional[bool] = None
    shap_values: Optional[dict] = None
    time: Optional[float] = None


class FeatureContribution(BaseModel):
    feature: str
    contribution: str  # "increases" or "decreases"
    impact: str  # "high", "medium", "low"
    human_readable: str
    icon: str


class RiskFactor(BaseModel):
    category: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    technical_detail: str
    icon: str


class ActionRecommendation(BaseModel):
    priority: int
    action: str
    reason: str
    icon: str
    action_type: str  # "block", "review", "monitor", "allow"


class ExplanationResponse(BaseModel):
    summary: str
    verdict: str  # "FRAUD", "SUSPICIOUS", "LEGITIMATE"
    confidence_level: str
    confidence_percentage: float

    # Natural language explanation
    main_explanation: str
    detailed_explanation: str

    # Risk breakdown
    risk_factors: list[RiskFactor]
    feature_contributions: list[FeatureContribution]

    # Recommendations
    recommended_actions: list[ActionRecommendation]

    # Comparative context
    comparison: dict

    # Metadata
    explanation_generated_at: str
    model_version: str


# Feature name mappings for human-readable explanations
FEATURE_NAMES = {
    "V1": "Transaction Velocity Pattern",
    "V2": "Geographic Dispersion",
    "V3": "Time-based Anomaly Score",
    "V4": "Card Usage Pattern",
    "V5": "Merchant Category Risk",
    "V6": "Transaction Frequency",
    "V7": "Amount Deviation Score",
    "V8": "Historical Behavior Match",
    "V9": "Device Fingerprint Score",
    "V10": "Network Risk Indicator",
    "V11": "Cross-border Activity",
    "V12": "Velocity Acceleration",
    "V13": "Time Gap Analysis",
    "V14": "High-risk Merchant Flag",
    "V15": "Unusual Hour Indicator",
    "V16": "Sequential Pattern Break",
    "V17": "Amount Clustering Score",
    "V18": "Geo-velocity Mismatch",
    "V19": "Card Not Present Risk",
    "V20": "Recurring Pattern Score",
    "V21": "New Merchant Flag",
    "V22": "Rapid Succession Flag",
    "V23": "Round Amount Indicator",
    "V24": "Weekend/Holiday Flag",
    "V25": "Peak Hour Indicator",
    "V26": "Low Balance Alert",
    "V27": "Cross-channel Activity",
    "V28": "Behavioral Anomaly Score",
    "Amount": "Transaction Amount",
    "Time": "Transaction Timing"
}

# Icons for different categories
CATEGORY_ICONS = {
    "amount": "💰",
    "timing": "⏰",
    "pattern": "📊",
    "location": "📍",
    "velocity": "⚡",
    "merchant": "🏪",
    "device": "📱",
    "behavior": "🔍",
    "network": "🌐"
}

ACTION_ICONS = {
    "block": "🚫",
    "review": "👁️",
    "monitor": "📡",
    "allow": "✅",
    "alert": "🚨",
    "verify": "🔐"
}


def get_feature_category(feature: str) -> str:
    """Determine the category of a feature for better explanations"""
    feature_upper = feature.upper()

    if feature_upper in ["V7", "V17", "V23", "AMOUNT"]:
        return "amount"
    elif feature_upper in ["V3", "V13", "V15", "V24", "V25", "TIME"]:
        return "timing"
    elif feature_upper in ["V1", "V6", "V12", "V22"]:
        return "velocity"
    elif feature_upper in ["V2", "V11", "V18"]:
        return "location"
    elif feature_upper in ["V5", "V14", "V21"]:
        return "merchant"
    elif feature_upper in ["V9", "V19"]:
        return "device"
    elif feature_upper in ["V4", "V8", "V16", "V20", "V28"]:
        return "behavior"
    else:
        return "pattern"


def generate_feature_explanation(feature: str, value: float, contribution: float) -> FeatureContribution:
    """Generate human-readable explanation for a feature's contribution"""

    feature_name = FEATURE_NAMES.get(feature, feature)
    category = get_feature_category(feature)
    icon = CATEGORY_ICONS.get(category, "📊")

    # Determine impact level
    abs_contribution = abs(contribution)
    if abs_contribution > 0.15:
        impact = "high"
    elif abs_contribution > 0.08:
        impact = "medium"
    else:
        impact = "low"

    # Determine direction
    contributes_to_fraud = contribution > 0
    direction = "increases" if contributes_to_fraud else "decreases"

    # Generate human-readable explanation based on feature category
    explanations = {
        "amount": {
            True: f"The transaction amount shows unusual patterns that are commonly associated with fraudulent activity.",
            False: f"The transaction amount falls within normal spending patterns for this profile."
        },
        "timing": {
            True: f"The transaction timing raises concerns - it occurred at an unusual time or with suspicious timing patterns.",
            False: f"The transaction timing is consistent with typical behavior patterns."
        },
        "velocity": {
            True: f"There's an unusual spike in transaction velocity that could indicate automated or rapid fraud attempts.",
            False: f"Transaction frequency is within normal limits."
        },
        "location": {
            True: f"Geographic patterns suggest potential location-based fraud indicators.",
            False: f"Location patterns are consistent with expected behavior."
        },
        "merchant": {
            True: f"The merchant category or profile presents elevated risk characteristics.",
            False: f"The merchant has a low-risk profile."
        },
        "device": {
            True: f"Device-related signals indicate potential fraud risk.",
            False: f"Device patterns are consistent with legitimate use."
        },
        "behavior": {
            True: f"Behavioral patterns deviate significantly from established norms.",
            False: f"Behavioral patterns match expected profile."
        },
        "pattern": {
            True: f"Statistical patterns in the data suggest elevated fraud risk.",
            False: f"Data patterns are consistent with legitimate transactions."
        }
    }

    human_readable = explanations.get(category, explanations["pattern"])[contributes_to_fraud]

    return FeatureContribution(
        feature=feature_name,
        contribution=direction,
        impact=impact,
        human_readable=human_readable,
        icon=icon
    )


def generate_risk_factors(
    amount: float,
    risk_score: int,
    fraud_probability: float,
    shap_values: dict,
    time: float
) -> list[RiskFactor]:
    """Generate list of risk factors with explanations"""

    risk_factors = []

    # Amount-based risk
    if amount > 1000:
        severity = "critical" if amount > 5000 else "high" if amount > 2000 else "medium"
        risk_factors.append(RiskFactor(
            category="Transaction Amount",
            severity=severity,
            description=f"High-value transaction of ${amount:.2f} detected",
            technical_detail=f"Amount is {amount/200:.1f}x the average transaction value",
            icon="💰"
        ))

    # Probability-based risk
    if fraud_probability > 0.7:
        risk_factors.append(RiskFactor(
            category="Model Confidence",
            severity="critical",
            description="Very high fraud probability detected by ML model",
            technical_detail=f"Probability score: {fraud_probability:.1%}",
            icon="🎯"
        ))
    elif fraud_probability > 0.5:
        risk_factors.append(RiskFactor(
            category="Model Confidence",
            severity="high",
            description="Elevated fraud probability detected",
            technical_detail=f"Probability score: {fraud_probability:.1%}",
            icon="🎯"
        ))

    # Time-based risk (late night transactions)
    hour = (time / 3600) % 24
    if hour >= 0 and hour <= 5:
        risk_factors.append(RiskFactor(
            category="Transaction Timing",
            severity="medium",
            description="Transaction occurred during high-risk hours (midnight to 5 AM)",
            technical_detail=f"Transaction hour: {int(hour):02d}:00",
            icon="⏰"
        ))

    # Analyze SHAP values for additional risks
    if shap_values:
        high_impact_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )[:5]

        for feature, value in high_impact_features:
            if isinstance(value, (int, float)) and value > 0.1:
                category = get_feature_category(feature)
                risk_factors.append(RiskFactor(
                    category=FEATURE_NAMES.get(feature, feature),
                    severity="high" if value > 0.15 else "medium",
                    description=f"Significant anomaly detected in {FEATURE_NAMES.get(feature, feature).lower()}",
                    technical_detail=f"SHAP contribution: +{value:.3f}",
                    icon=CATEGORY_ICONS.get(category, "📊")
                ))

    # Overall risk score
    if risk_score >= 75:
        risk_factors.insert(0, RiskFactor(
            category="Overall Risk Assessment",
            severity="critical",
            description="Transaction flagged as critical risk",
            technical_detail=f"Risk score: {risk_score}/100",
            icon="🚨"
        ))
    elif risk_score >= 50:
        risk_factors.insert(0, RiskFactor(
            category="Overall Risk Assessment",
            severity="high",
            description="Transaction flagged as high risk",
            technical_detail=f"Risk score: {risk_score}/100",
            icon="⚠️"
        ))

    return risk_factors[:8]  # Limit to 8 risk factors


def generate_recommendations(
    is_fraud: bool,
    risk_score: int,
    fraud_probability: float,
    amount: float
) -> list[ActionRecommendation]:
    """Generate actionable recommendations based on the analysis"""

    recommendations = []

    if is_fraud or risk_score >= 75:
        # Critical - Block immediately
        recommendations.append(ActionRecommendation(
            priority=1,
            action="Block this transaction immediately",
            reason="High confidence fraud detection requires immediate action to prevent financial loss",
            icon=ACTION_ICONS["block"],
            action_type="block"
        ))
        recommendations.append(ActionRecommendation(
            priority=2,
            action="Alert the fraud investigation team",
            reason="Manual review by specialists can uncover additional fraud patterns",
            icon=ACTION_ICONS["alert"],
            action_type="review"
        ))
        recommendations.append(ActionRecommendation(
            priority=3,
            action="Temporarily freeze the associated account",
            reason="Prevent potential follow-up fraudulent transactions",
            icon=ACTION_ICONS["block"],
            action_type="block"
        ))
        if amount > 1000:
            recommendations.append(ActionRecommendation(
                priority=4,
                action="Initiate customer verification callback",
                reason="High-value transactions require additional identity confirmation",
                icon=ACTION_ICONS["verify"],
                action_type="verify"
            ))

    elif risk_score >= 50:
        # High risk - Review
        recommendations.append(ActionRecommendation(
            priority=1,
            action="Flag for manual review within 1 hour",
            reason="Elevated risk level requires human verification before processing",
            icon=ACTION_ICONS["review"],
            action_type="review"
        ))
        recommendations.append(ActionRecommendation(
            priority=2,
            action="Request additional authentication (2FA/OTP)",
            reason="Step-up authentication can prevent unauthorized transactions",
            icon=ACTION_ICONS["verify"],
            action_type="verify"
        ))
        recommendations.append(ActionRecommendation(
            priority=3,
            action="Monitor account for 24 hours",
            reason="Watch for additional suspicious activity patterns",
            icon=ACTION_ICONS["monitor"],
            action_type="monitor"
        ))

    elif risk_score >= 25:
        # Medium risk - Monitor
        recommendations.append(ActionRecommendation(
            priority=1,
            action="Process with enhanced monitoring",
            reason="Allow transaction but track for pattern development",
            icon=ACTION_ICONS["monitor"],
            action_type="monitor"
        ))
        recommendations.append(ActionRecommendation(
            priority=2,
            action="Add to watchlist for 7 days",
            reason="Temporary elevated scrutiny can catch developing fraud patterns",
            icon=ACTION_ICONS["review"],
            action_type="review"
        ))

    else:
        # Low risk - Allow
        recommendations.append(ActionRecommendation(
            priority=1,
            action="Approve transaction",
            reason="Risk assessment indicates legitimate transaction",
            icon=ACTION_ICONS["allow"],
            action_type="allow"
        ))
        recommendations.append(ActionRecommendation(
            priority=2,
            action="Log for routine audit",
            reason="Maintain transaction records for compliance",
            icon=ACTION_ICONS["monitor"],
            action_type="monitor"
        ))

    return recommendations


def generate_comparison(risk_score: int, fraud_probability: float, amount: float) -> dict:
    """Generate comparative context for the transaction"""

    # These would ideally come from actual statistics
    avg_amount = 150.0
    avg_risk = 15
    fraud_rate = 0.0017  # 0.17% typical fraud rate

    return {
        "amount_comparison": {
            "percentile": min(99, int((amount / 500) * 50)),
            "vs_average": f"{amount / avg_amount:.1f}x average",
            "category": "high" if amount > 500 else "medium" if amount > 100 else "low"
        },
        "risk_comparison": {
            "percentile": min(99, risk_score),
            "vs_average": f"{risk_score / max(avg_risk, 1):.1f}x average risk",
            "category": "critical" if risk_score >= 75 else "high" if risk_score >= 50 else "medium" if risk_score >= 25 else "low"
        },
        "probability_context": {
            "relative_to_baseline": f"{fraud_probability / fraud_rate:.0f}x baseline fraud rate",
            "confidence_band": "high" if fraud_probability > 0.8 or fraud_probability < 0.2 else "medium"
        }
    }


def generate_main_explanation(
    is_fraud: bool,
    risk_score: int,
    fraud_probability: float,
    amount: float,
    top_features: list
) -> tuple[str, str]:
    """Generate the main natural language explanation"""

    # Determine verdict
    if is_fraud or risk_score >= 75:
        verdict_text = "FRAUDULENT"
        confidence = "high confidence"
    elif risk_score >= 50:
        verdict_text = "HIGHLY SUSPICIOUS"
        confidence = "moderate confidence"
    elif risk_score >= 25:
        verdict_text = "POTENTIALLY SUSPICIOUS"
        confidence = "low confidence"
    else:
        verdict_text = "LEGITIMATE"
        confidence = "high confidence"

    # Build main explanation
    if is_fraud or risk_score >= 50:
        main_parts = [
            f"This ${amount:.2f} transaction has been classified as **{verdict_text}** with {confidence}.",
            f"The fraud probability is {fraud_probability:.1%}, with an overall risk score of {risk_score}/100."
        ]

        if top_features:
            feature_names = [FEATURE_NAMES.get(f, f) for f, _ in top_features[:3]]
            main_parts.append(
                f"Key contributing factors include: {', '.join(feature_names)}."
            )
    else:
        main_parts = [
            f"This ${amount:.2f} transaction appears to be **{verdict_text}** with {confidence}.",
            f"The risk score of {risk_score}/100 falls within acceptable limits."
        ]

    main_explanation = " ".join(main_parts)

    # Build detailed explanation
    detailed_parts = []

    if is_fraud or risk_score >= 50:
        detailed_parts.append(
            "**Why this was flagged:** Our machine learning model analyzed 30 different transaction "
            "characteristics and detected patterns consistent with known fraud signatures."
        )

        if amount > 500:
            detailed_parts.append(
                f"**Amount Analysis:** The transaction amount of ${amount:.2f} is significantly "
                "higher than typical transactions, which increases fraud risk."
            )

        detailed_parts.append(
            "**Model Confidence:** The neural network's fraud probability output indicates "
            f"a {fraud_probability:.1%} likelihood of fraud based on the aggregate feature analysis."
        )

        detailed_parts.append(
            "**Recommended Response:** Based on the risk level, immediate action is recommended "
            "to prevent potential financial loss. See the action recommendations below."
        )
    else:
        detailed_parts.append(
            "**Analysis Summary:** This transaction's characteristics fall within normal parameters "
            "when compared against our fraud detection model's training data."
        )
        detailed_parts.append(
            f"**Risk Assessment:** With a risk score of {risk_score}/100, this transaction "
            "does not exhibit the patterns typically associated with fraudulent activity."
        )

    detailed_explanation = "\n\n".join(detailed_parts)

    return main_explanation, detailed_explanation


@router.post("", response_model=ExplanationResponse)
@router.post("/", response_model=ExplanationResponse)
async def explain_prediction(
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered natural language explanation for a fraud prediction.

    Provides:
    - Human-readable summary of why a transaction was flagged
    - Detailed risk factor breakdown
    - Feature contribution analysis
    - Actionable recommendations
    - Comparative context
    """

    # Get prediction data
    if request.prediction_id:
        prediction = db.query(Prediction).filter(
            Prediction.id == request.prediction_id,
            Prediction.user_id == current_user.id
        ).first()

        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")

        amount = prediction.amount
        risk_score = prediction.risk_score or 0
        fraud_probability = prediction.fraud_probability or 0.0
        is_fraud = prediction.is_fraud
        shap_values = json.loads(prediction.shap_values) if prediction.shap_values else {}
        time_value = prediction.time_feature or 0
    else:
        # Use provided data
        amount = request.amount or 0.0
        risk_score = request.risk_score or 0
        fraud_probability = request.fraud_probability or 0.0
        is_fraud = request.is_fraud or False
        shap_values = request.shap_values or {}
        time_value = request.time or 0

    # Determine verdict
    if is_fraud or risk_score >= 75:
        verdict = "FRAUD"
    elif risk_score >= 50:
        verdict = "SUSPICIOUS"
    else:
        verdict = "LEGITIMATE"

    # Calculate confidence
    if fraud_probability > 0.8 or fraud_probability < 0.2:
        confidence_level = "High"
        confidence_percentage = max(fraud_probability, 1 - fraud_probability) * 100
    elif fraud_probability > 0.6 or fraud_probability < 0.4:
        confidence_level = "Medium"
        confidence_percentage = 70.0
    else:
        confidence_level = "Low"
        confidence_percentage = 55.0

    # Get top contributing features
    top_features = []
    if shap_values:
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )
        top_features = sorted_features[:10]

    # Generate feature contributions
    feature_contributions = []
    for feature, value in top_features:
        if isinstance(value, (int, float)):
            contribution = generate_feature_explanation(feature, 0, value)
            feature_contributions.append(contribution)

    # Generate explanations
    main_explanation, detailed_explanation = generate_main_explanation(
        is_fraud, risk_score, fraud_probability, amount, top_features
    )

    # Generate risk factors
    risk_factors = generate_risk_factors(
        amount, risk_score, fraud_probability, shap_values, time_value
    )

    # Generate recommendations
    recommendations = generate_recommendations(
        is_fraud, risk_score, fraud_probability, amount
    )

    # Generate comparison
    comparison = generate_comparison(risk_score, fraud_probability, amount)

    # Build summary
    if is_fraud or risk_score >= 75:
        summary = f"🚨 HIGH ALERT: Fraudulent transaction detected (${amount:.2f}, Risk: {risk_score}%)"
    elif risk_score >= 50:
        summary = f"⚠️ WARNING: Suspicious transaction requires review (${amount:.2f}, Risk: {risk_score}%)"
    elif risk_score >= 25:
        summary = f"📋 NOTICE: Transaction flagged for monitoring (${amount:.2f}, Risk: {risk_score}%)"
    else:
        summary = f"✅ CLEAR: Transaction appears legitimate (${amount:.2f}, Risk: {risk_score}%)"

    return ExplanationResponse(
        summary=summary,
        verdict=verdict,
        confidence_level=confidence_level,
        confidence_percentage=confidence_percentage,
        main_explanation=main_explanation,
        detailed_explanation=detailed_explanation,
        risk_factors=risk_factors,
        feature_contributions=feature_contributions,
        recommended_actions=recommendations,
        comparison=comparison,
        explanation_generated_at=datetime.utcnow().isoformat(),
        model_version="1.0.0"
    )


@router.get("/quick/{prediction_id}")
async def get_quick_explanation(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a quick one-liner explanation for a prediction"""

    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    risk_score = prediction.risk_score or 0
    amount = prediction.amount

    if prediction.is_fraud or risk_score >= 75:
        explanation = f"Transaction blocked: Multiple fraud indicators detected including unusual amount pattern (${amount:.2f}) and behavioral anomalies."
    elif risk_score >= 50:
        explanation = f"Transaction flagged: Elevated risk due to amount (${amount:.2f}) deviating from typical patterns. Manual review recommended."
    elif risk_score >= 25:
        explanation = f"Transaction monitored: Minor anomalies detected in ${amount:.2f} transaction. Continuing surveillance."
    else:
        explanation = f"Transaction approved: ${amount:.2f} transaction matches expected behavior patterns."

    return {
        "prediction_id": prediction_id,
        "quick_explanation": explanation,
        "risk_level": "critical" if risk_score >= 75 else "high" if risk_score >= 50 else "medium" if risk_score >= 25 else "low",
        "action": "block" if risk_score >= 75 else "review" if risk_score >= 50 else "monitor" if risk_score >= 25 else "allow"
    }


@router.get("/features")
async def get_feature_descriptions(
    current_user: User = Depends(get_current_user)
):
    """Get human-readable descriptions for all features"""

    descriptions = []
    for feature, name in FEATURE_NAMES.items():
        category = get_feature_category(feature)
        descriptions.append({
            "feature": feature,
            "name": name,
            "category": category,
            "icon": CATEGORY_ICONS.get(category, "📊")
        })

    return {
        "features": descriptions,
        "categories": [
            {"key": "amount", "name": "Amount Analysis", "icon": "💰"},
            {"key": "timing", "name": "Timing Patterns", "icon": "⏰"},
            {"key": "velocity", "name": "Transaction Velocity", "icon": "⚡"},
            {"key": "location", "name": "Geographic Signals", "icon": "📍"},
            {"key": "merchant", "name": "Merchant Risk", "icon": "🏪"},
            {"key": "device", "name": "Device Fingerprint", "icon": "📱"},
            {"key": "behavior", "name": "Behavioral Analysis", "icon": "🔍"},
            {"key": "pattern", "name": "Statistical Patterns", "icon": "📊"}
        ]
    }
