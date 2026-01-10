"""Geo-Velocity Tracker API

Detects physically impossible travel patterns by analyzing
the geographic distance and time between transactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum
import math
import random

def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC)"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

router = APIRouter(prefix="/geo-velocity", tags=["Geo-Velocity Tracker"])


# ============== Constants ==============

# Maximum realistic travel speeds (km/h)
MAX_SPEEDS = {
    "walking": 6,
    "car": 150,
    "train": 350,
    "commercial_flight": 900,
    "supersonic": 2200,  # Concorde-level (not commercially available)
}

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371


# ============== City Coordinates Database ==============

CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    # North America
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Philadelphia, PA": (39.9526, -75.1652),
    "San Antonio, TX": (29.4241, -98.4936),
    "San Diego, CA": (32.7157, -117.1611),
    "Dallas, TX": (32.7767, -96.7970),
    "San Jose, CA": (37.3382, -121.8863),
    "Austin, TX": (30.2672, -97.7431),
    "Jacksonville, FL": (30.3322, -81.6557),
    "San Francisco, CA": (37.7749, -122.4194),
    "Seattle, WA": (47.6062, -122.3321),
    "Denver, CO": (39.7392, -104.9903),
    "Boston, MA": (42.3601, -71.0589),
    "Miami, FL": (25.7617, -80.1918),
    "Atlanta, GA": (33.7490, -84.3880),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Portland, OR": (45.5155, -122.6789),
    "Toronto, Canada": (43.6532, -79.3832),
    "Vancouver, Canada": (49.2827, -123.1207),
    "Montreal, Canada": (45.5017, -73.5673),
    "Mexico City, Mexico": (19.4326, -99.1332),

    # Europe
    "London, UK": (51.5074, -0.1278),
    "Paris, France": (48.8566, 2.3522),
    "Berlin, Germany": (52.5200, 13.4050),
    "Madrid, Spain": (40.4168, -3.7038),
    "Rome, Italy": (41.9028, 12.4964),
    "Amsterdam, Netherlands": (52.3676, 4.9041),
    "Vienna, Austria": (48.2082, 16.3738),
    "Prague, Czech Republic": (50.0755, 14.4378),
    "Barcelona, Spain": (41.3851, 2.1734),
    "Munich, Germany": (48.1351, 11.5820),
    "Milan, Italy": (45.4642, 9.1900),
    "Dublin, Ireland": (53.3498, -6.2603),
    "Brussels, Belgium": (50.8503, 4.3517),
    "Zurich, Switzerland": (47.3769, 8.5417),
    "Stockholm, Sweden": (59.3293, 18.0686),
    "Oslo, Norway": (59.9139, 10.7522),
    "Copenhagen, Denmark": (55.6761, 12.5683),
    "Helsinki, Finland": (60.1699, 24.9384),
    "Warsaw, Poland": (52.2297, 21.0122),
    "Moscow, Russia": (55.7558, 37.6173),
    "Kyiv, Ukraine": (50.4501, 30.5234),

    # Asia
    "Tokyo, Japan": (35.6762, 139.6503),
    "Beijing, China": (39.9042, 116.4074),
    "Shanghai, China": (31.2304, 121.4737),
    "Hong Kong": (22.3193, 114.1694),
    "Singapore": (1.3521, 103.8198),
    "Seoul, South Korea": (37.5665, 126.9780),
    "Mumbai, India": (19.0760, 72.8777),
    "Delhi, India": (28.7041, 77.1025),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Dubai, UAE": (25.2048, 55.2708),
    "Tel Aviv, Israel": (32.0853, 34.7818),
    "Istanbul, Turkey": (41.0082, 28.9784),

    # Oceania
    "Sydney, Australia": (-33.8688, 151.2093),
    "Melbourne, Australia": (-37.8136, 144.9631),
    "Auckland, New Zealand": (-36.8509, 174.7645),

    # South America
    "São Paulo, Brazil": (-23.5505, -46.6333),
    "Rio de Janeiro, Brazil": (-22.9068, -43.1729),
    "Buenos Aires, Argentina": (-34.6037, -58.3816),
    "Lima, Peru": (-12.0464, -77.0428),
    "Bogotá, Colombia": (4.7110, -74.0721),
    "Santiago, Chile": (-33.4489, -70.6693),

    # Africa
    "Cairo, Egypt": (30.0444, 31.2357),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Johannesburg, South Africa": (-26.2041, 28.0473),
    "Cape Town, South Africa": (-33.9249, 18.4241),
    "Nairobi, Kenya": (-1.2921, 36.8219),
    "Casablanca, Morocco": (33.5731, -7.5898),
}


# ============== Enums ==============

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TravelType(str, Enum):
    WALKING = "walking"
    CAR = "car"
    TRAIN = "train"
    FLIGHT = "flight"
    IMPOSSIBLE = "impossible"


# ============== Pydantic Models ==============

class GeoTransaction(BaseModel):
    id: str
    timestamp: datetime
    location: str
    latitude: float
    longitude: float
    amount: float
    merchant: str
    user_id: str


class VelocityAlert(BaseModel):
    alert_id: str
    user_id: str
    severity: AlertSeverity
    from_transaction: GeoTransaction
    to_transaction: GeoTransaction
    distance_km: float
    time_diff_hours: float
    required_speed_kmh: float
    max_possible_speed_kmh: float
    travel_type_required: TravelType
    is_impossible: bool
    probability_fraud: float
    explanation: str
    recommendation: str


class GeoVelocityAnalysis(BaseModel):
    user_id: str
    analysis_period_days: int
    total_transactions: int
    unique_locations: int
    alerts: List[VelocityAlert]
    risk_score: float
    travel_pattern: str
    most_frequent_locations: List[Dict]
    suspicious_patterns: List[str]


class TransactionInput(BaseModel):
    location: str
    timestamp: datetime
    amount: float = 100.0
    merchant: str = "Generic Merchant"


class CheckVelocityRequest(BaseModel):
    user_id: str
    new_transaction: TransactionInput
    previous_transactions: Optional[List[TransactionInput]] = None


class VelocityCheckResult(BaseModel):
    is_suspicious: bool
    alert: Optional[VelocityAlert]
    risk_level: AlertSeverity
    can_proceed: bool
    requires_verification: bool
    message: str


# ============== Helper Functions ==============

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth using Haversine formula"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_KM * c


def get_coordinates(location: str) -> Tuple[float, float]:
    """Get coordinates for a location, with fuzzy matching"""
    # Exact match
    if location in CITY_COORDINATES:
        return CITY_COORDINATES[location]

    # Partial match
    location_lower = location.lower()
    for city, coords in CITY_COORDINATES.items():
        if location_lower in city.lower() or city.lower() in location_lower:
            return coords

    # Default to random location if not found (for demo purposes)
    return (random.uniform(-60, 60), random.uniform(-150, 150))


def determine_travel_type(speed_kmh: float) -> TravelType:
    """Determine what type of travel would be required for a given speed"""
    if speed_kmh <= MAX_SPEEDS["walking"]:
        return TravelType.WALKING
    elif speed_kmh <= MAX_SPEEDS["car"]:
        return TravelType.CAR
    elif speed_kmh <= MAX_SPEEDS["train"]:
        return TravelType.TRAIN
    elif speed_kmh <= MAX_SPEEDS["commercial_flight"]:
        return TravelType.FLIGHT
    else:
        return TravelType.IMPOSSIBLE


def calculate_fraud_probability(speed_kmh: float, distance_km: float) -> float:
    """Calculate probability that this velocity pattern indicates fraud"""
    # Base probability based on required speed
    if speed_kmh <= MAX_SPEEDS["commercial_flight"]:
        base_prob = min(speed_kmh / MAX_SPEEDS["commercial_flight"] * 0.5, 0.5)
    else:
        # Impossible speed - very high probability
        excess_speed = speed_kmh - MAX_SPEEDS["commercial_flight"]
        base_prob = min(0.7 + (excess_speed / 1000) * 0.3, 0.99)

    # Adjust for distance (longer distances with high speed are more suspicious)
    distance_factor = min(distance_km / 10000, 1.0) * 0.2

    return min(base_prob + distance_factor, 0.99)


def get_severity(speed_kmh: float, is_impossible: bool) -> AlertSeverity:
    """Determine alert severity based on speed"""
    if is_impossible:
        return AlertSeverity.CRITICAL
    elif speed_kmh > MAX_SPEEDS["train"]:
        return AlertSeverity.HIGH
    elif speed_kmh > MAX_SPEEDS["car"]:
        return AlertSeverity.MEDIUM
    else:
        return AlertSeverity.LOW


def generate_explanation(from_loc: str, to_loc: str, distance_km: float,
                         time_hours: float, speed_kmh: float, travel_type: TravelType) -> str:
    """Generate human-readable explanation of the velocity alert"""
    if travel_type == TravelType.IMPOSSIBLE:
        return (
            f"Transaction detected in {to_loc} only {time_hours:.1f} hours after "
            f"a transaction in {from_loc}. The distance of {distance_km:.0f} km would require "
            f"traveling at {speed_kmh:.0f} km/h, which exceeds the speed of commercial aircraft. "
            f"This is physically impossible and strongly suggests fraudulent activity."
        )
    elif travel_type == TravelType.FLIGHT:
        return (
            f"Transaction in {to_loc} occurred {time_hours:.1f} hours after {from_loc}. "
            f"Distance: {distance_km:.0f} km. This would require air travel at {speed_kmh:.0f} km/h. "
            f"While possible, this rapid international movement warrants verification."
        )
    elif travel_type == TravelType.TRAIN:
        return (
            f"Transaction in {to_loc} after {from_loc} ({distance_km:.0f} km in {time_hours:.1f} hours). "
            f"Required speed: {speed_kmh:.0f} km/h. High-speed train could be possible."
        )
    else:
        return (
            f"Transaction locations {from_loc} and {to_loc} are {distance_km:.0f} km apart, "
            f"with {time_hours:.1f} hours between them. Movement appears normal."
        )


def generate_recommendation(severity: AlertSeverity, travel_type: TravelType) -> str:
    """Generate recommendation based on alert severity"""
    if severity == AlertSeverity.CRITICAL:
        return "BLOCK transaction immediately. Contact customer for verification. High likelihood of stolen credentials."
    elif severity == AlertSeverity.HIGH:
        return "Request step-up authentication (2FA, biometric). Review recent account activity."
    elif severity == AlertSeverity.MEDIUM:
        return "Send notification to customer. Monitor subsequent transactions closely."
    else:
        return "Log for pattern analysis. No immediate action required."


# ============== In-Memory Storage (Demo) ==============

user_transaction_history: Dict[str, List[GeoTransaction]] = {}


# ============== API Endpoints ==============

@router.post("/check", response_model=VelocityCheckResult)
async def check_velocity(request: CheckVelocityRequest):
    """Check if a new transaction has suspicious geo-velocity patterns"""
    user_id = request.user_id
    new_tx = request.new_transaction

    # Get coordinates for new transaction
    new_coords = get_coordinates(new_tx.location)

    # Create GeoTransaction object
    new_geo_tx = GeoTransaction(
        id=f"tx_{random.randint(100000, 999999)}",
        timestamp=new_tx.timestamp,
        location=new_tx.location,
        latitude=new_coords[0],
        longitude=new_coords[1],
        amount=new_tx.amount,
        merchant=new_tx.merchant,
        user_id=user_id
    )

    # Get previous transactions
    previous = user_transaction_history.get(user_id, [])

    # Also include any provided previous transactions
    if request.previous_transactions:
        for pt in request.previous_transactions:
            coords = get_coordinates(pt.location)
            previous.append(GeoTransaction(
                id=f"tx_{random.randint(100000, 999999)}",
                timestamp=pt.timestamp,
                location=pt.location,
                latitude=coords[0],
                longitude=coords[1],
                amount=pt.amount,
                merchant=pt.merchant,
                user_id=user_id
            ))

    # Sort by timestamp
    previous.sort(key=lambda x: x.timestamp, reverse=True)

    # Check against most recent transaction
    if not previous:
        # First transaction - store and allow
        user_transaction_history.setdefault(user_id, []).append(new_geo_tx)
        return VelocityCheckResult(
            is_suspicious=False,
            alert=None,
            risk_level=AlertSeverity.LOW,
            can_proceed=True,
            requires_verification=False,
            message="First transaction for this user. No velocity check possible."
        )

    last_tx = previous[0]

    # Calculate distance and time
    distance_km = haversine_distance(
        last_tx.latitude, last_tx.longitude,
        new_geo_tx.latitude, new_geo_tx.longitude
    )

    time_diff = ensure_utc(new_geo_tx.timestamp) - ensure_utc(last_tx.timestamp)
    time_hours = time_diff.total_seconds() / 3600

    if time_hours <= 0:
        time_hours = 0.001  # Avoid division by zero

    # Calculate required speed
    required_speed = distance_km / time_hours

    # Determine travel type and if impossible
    travel_type = determine_travel_type(required_speed)
    is_impossible = travel_type == TravelType.IMPOSSIBLE

    # Calculate fraud probability
    fraud_prob = calculate_fraud_probability(required_speed, distance_km)

    # Get severity
    severity = get_severity(required_speed, is_impossible)

    # Store new transaction
    user_transaction_history.setdefault(user_id, []).append(new_geo_tx)

    # Determine if suspicious (speed > car speed or impossible)
    is_suspicious = required_speed > MAX_SPEEDS["car"] or is_impossible

    if is_suspicious:
        alert = VelocityAlert(
            alert_id=f"alert_{random.randint(100000, 999999)}",
            user_id=user_id,
            severity=severity,
            from_transaction=last_tx,
            to_transaction=new_geo_tx,
            distance_km=round(distance_km, 2),
            time_diff_hours=round(time_hours, 2),
            required_speed_kmh=round(required_speed, 2),
            max_possible_speed_kmh=MAX_SPEEDS["commercial_flight"],
            travel_type_required=travel_type,
            is_impossible=is_impossible,
            probability_fraud=round(fraud_prob, 2),
            explanation=generate_explanation(
                last_tx.location, new_geo_tx.location,
                distance_km, time_hours, required_speed, travel_type
            ),
            recommendation=generate_recommendation(severity, travel_type)
        )

        return VelocityCheckResult(
            is_suspicious=True,
            alert=alert,
            risk_level=severity,
            can_proceed=severity not in [AlertSeverity.CRITICAL],
            requires_verification=severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
            message=f"Suspicious velocity detected: {distance_km:.0f} km in {time_hours:.1f} hours ({required_speed:.0f} km/h)"
        )

    return VelocityCheckResult(
        is_suspicious=False,
        alert=None,
        risk_level=AlertSeverity.LOW,
        can_proceed=True,
        requires_verification=False,
        message=f"Velocity check passed: {distance_km:.0f} km in {time_hours:.1f} hours is within normal range"
    )


@router.get("/analyze/{user_id}", response_model=GeoVelocityAnalysis)
async def analyze_user_velocity(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """Analyze a user's geo-velocity patterns over time"""
    # Generate demo data if user doesn't exist
    if user_id not in user_transaction_history or len(user_transaction_history[user_id]) < 5:
        # Generate sample transactions
        cities = list(CITY_COORDINATES.keys())
        base_time = datetime.now() - timedelta(days=days)

        transactions = []
        for i in range(random.randint(10, 30)):
            city = random.choice(cities)
            coords = CITY_COORDINATES[city]
            transactions.append(GeoTransaction(
                id=f"tx_{random.randint(100000, 999999)}",
                timestamp=base_time + timedelta(days=random.uniform(0, days)),
                location=city,
                latitude=coords[0],
                longitude=coords[1],
                amount=random.uniform(10, 500),
                merchant=random.choice(["Amazon", "Walmart", "Target", "Starbucks", "Local Shop"]),
                user_id=user_id
            ))

        user_transaction_history[user_id] = transactions

    transactions = user_transaction_history.get(user_id, [])
    transactions.sort(key=lambda x: x.timestamp)

    # Filter by date range
    cutoff = datetime.now() - timedelta(days=days)
    filtered_tx = [tx for tx in transactions if tx.timestamp >= cutoff]

    if not filtered_tx:
        raise HTTPException(status_code=404, detail="No transactions found for analysis")

    # Analyze velocity between consecutive transactions
    alerts = []
    suspicious_patterns = []

    for i in range(1, len(filtered_tx)):
        prev_tx = filtered_tx[i - 1]
        curr_tx = filtered_tx[i]

        distance_km = haversine_distance(
            prev_tx.latitude, prev_tx.longitude,
            curr_tx.latitude, curr_tx.longitude
        )

        time_diff = curr_tx.timestamp - prev_tx.timestamp
        time_hours = max(time_diff.total_seconds() / 3600, 0.001)

        required_speed = distance_km / time_hours
        travel_type = determine_travel_type(required_speed)

        if required_speed > MAX_SPEEDS["car"]:
            is_impossible = travel_type == TravelType.IMPOSSIBLE
            severity = get_severity(required_speed, is_impossible)
            fraud_prob = calculate_fraud_probability(required_speed, distance_km)

            alert = VelocityAlert(
                alert_id=f"alert_{random.randint(100000, 999999)}",
                user_id=user_id,
                severity=severity,
                from_transaction=prev_tx,
                to_transaction=curr_tx,
                distance_km=round(distance_km, 2),
                time_diff_hours=round(time_hours, 2),
                required_speed_kmh=round(required_speed, 2),
                max_possible_speed_kmh=MAX_SPEEDS["commercial_flight"],
                travel_type_required=travel_type,
                is_impossible=is_impossible,
                probability_fraud=round(fraud_prob, 2),
                explanation=generate_explanation(
                    prev_tx.location, curr_tx.location,
                    distance_km, time_hours, required_speed, travel_type
                ),
                recommendation=generate_recommendation(severity, travel_type)
            )
            alerts.append(alert)

            if is_impossible:
                suspicious_patterns.append(
                    f"Impossible travel: {prev_tx.location} → {curr_tx.location} in {time_hours:.1f}h"
                )

    # Calculate statistics
    unique_locations = len(set(tx.location for tx in filtered_tx))

    # Location frequency
    location_counts = {}
    for tx in filtered_tx:
        location_counts[tx.location] = location_counts.get(tx.location, 0) + 1

    most_frequent = sorted(
        [{"location": loc, "count": count} for loc, count in location_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]

    # Calculate risk score
    if not alerts:
        risk_score = 0
    else:
        critical_count = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
        high_count = sum(1 for a in alerts if a.severity == AlertSeverity.HIGH)
        medium_count = sum(1 for a in alerts if a.severity == AlertSeverity.MEDIUM)

        risk_score = min(
            (critical_count * 40 + high_count * 20 + medium_count * 10) / len(filtered_tx) * 100,
            100
        )

    # Determine travel pattern
    if unique_locations <= 2:
        travel_pattern = "Local - transactions in 1-2 locations"
    elif unique_locations <= 5:
        travel_pattern = "Regional - transactions across several locations"
    elif alerts and any(a.is_impossible for a in alerts):
        travel_pattern = "SUSPICIOUS - Impossible travel patterns detected"
    else:
        travel_pattern = "International - transactions across many locations"

    return GeoVelocityAnalysis(
        user_id=user_id,
        analysis_period_days=days,
        total_transactions=len(filtered_tx),
        unique_locations=unique_locations,
        alerts=alerts,
        risk_score=round(risk_score, 1),
        travel_pattern=travel_pattern,
        most_frequent_locations=most_frequent,
        suspicious_patterns=suspicious_patterns
    )


@router.get("/map-data/{user_id}")
async def get_map_data(user_id: str, days: int = Query(default=30, ge=1, le=365)):
    """Get transaction data formatted for map visualization"""
    # Generate demo data if needed
    if user_id not in user_transaction_history:
        await analyze_user_velocity(user_id, days)

    transactions = user_transaction_history.get(user_id, [])
    cutoff = datetime.now() - timedelta(days=days)
    filtered_tx = [tx for tx in transactions if tx.timestamp >= cutoff]
    filtered_tx.sort(key=lambda x: x.timestamp)

    # Create markers
    markers = [
        {
            "id": tx.id,
            "position": [tx.latitude, tx.longitude],
            "location": tx.location,
            "timestamp": tx.timestamp.isoformat(),
            "amount": tx.amount,
            "merchant": tx.merchant
        }
        for tx in filtered_tx
    ]

    # Create path lines
    paths = []
    for i in range(1, len(filtered_tx)):
        prev_tx = filtered_tx[i - 1]
        curr_tx = filtered_tx[i]

        distance_km = haversine_distance(
            prev_tx.latitude, prev_tx.longitude,
            curr_tx.latitude, curr_tx.longitude
        )

        time_diff = curr_tx.timestamp - prev_tx.timestamp
        time_hours = max(time_diff.total_seconds() / 3600, 0.001)
        speed = distance_km / time_hours

        is_suspicious = speed > MAX_SPEEDS["commercial_flight"]

        paths.append({
            "from": [prev_tx.latitude, prev_tx.longitude],
            "to": [curr_tx.latitude, curr_tx.longitude],
            "distance_km": round(distance_km, 2),
            "time_hours": round(time_hours, 2),
            "speed_kmh": round(speed, 2),
            "is_suspicious": is_suspicious,
            "color": "#ef4444" if is_suspicious else "#22c55e"
        })

    return {
        "user_id": user_id,
        "markers": markers,
        "paths": paths,
        "center": markers[0]["position"] if markers else [0, 0],
        "total_distance_km": round(sum(p["distance_km"] for p in paths), 2)
    }


@router.get("/cities")
async def get_available_cities():
    """Get list of cities with coordinates for the demo"""
    return {
        "cities": [
            {"name": city, "latitude": coords[0], "longitude": coords[1]}
            for city, coords in sorted(CITY_COORDINATES.items())
        ],
        "total": len(CITY_COORDINATES)
    }


@router.get("/speed-limits")
async def get_speed_limits():
    """Get the maximum speed limits used for travel type determination"""
    return {
        "limits": MAX_SPEEDS,
        "description": {
            "walking": "Normal walking speed",
            "car": "Highway driving speed",
            "train": "High-speed rail (TGV, Shinkansen)",
            "commercial_flight": "Commercial jet aircraft",
            "supersonic": "Reference only - not commercially available"
        }
    }


@router.delete("/history/{user_id}")
async def clear_user_history(user_id: str):
    """Clear transaction history for a user (for testing)"""
    if user_id in user_transaction_history:
        del user_transaction_history[user_id]
        return {"message": f"History cleared for user {user_id}"}
    return {"message": f"No history found for user {user_id}"}


@router.post("/simulate-fraud")
async def simulate_fraud_scenario(user_id: str = "demo_user"):
    """Generate a demo fraud scenario with impossible travel"""
    # Clear existing history
    user_transaction_history[user_id] = []

    # Create a realistic sequence followed by impossible travel
    scenarios = [
        {
            "location": "New York, NY",
            "time_offset_hours": -24,
            "amount": 45.50,
            "merchant": "Starbucks"
        },
        {
            "location": "New York, NY",
            "time_offset_hours": -20,
            "amount": 125.00,
            "merchant": "Amazon"
        },
        {
            "location": "New York, NY",
            "time_offset_hours": -12,
            "amount": 32.00,
            "merchant": "Uber"
        },
        # Suspicious - flight would be tight
        {
            "location": "Los Angeles, CA",
            "time_offset_hours": -6,
            "amount": 89.00,
            "merchant": "Best Buy"
        },
        # IMPOSSIBLE - can't be in Tokyo 2 hours after LA
        {
            "location": "Tokyo, Japan",
            "time_offset_hours": -4,
            "amount": 350.00,
            "merchant": "Electronics Store"
        },
        # Even more impossible
        {
            "location": "London, UK",
            "time_offset_hours": -2,
            "amount": 200.00,
            "merchant": "Harrods"
        }
    ]

    now = datetime.now()
    transactions = []

    for scenario in scenarios:
        coords = get_coordinates(scenario["location"])
        tx = GeoTransaction(
            id=f"tx_{random.randint(100000, 999999)}",
            timestamp=now + timedelta(hours=scenario["time_offset_hours"]),
            location=scenario["location"],
            latitude=coords[0],
            longitude=coords[1],
            amount=scenario["amount"],
            merchant=scenario["merchant"],
            user_id=user_id
        )
        transactions.append(tx)

    user_transaction_history[user_id] = transactions

    return {
        "message": "Fraud scenario created",
        "user_id": user_id,
        "transactions_created": len(transactions),
        "note": "Use /analyze/{user_id} to see the velocity analysis"
    }
