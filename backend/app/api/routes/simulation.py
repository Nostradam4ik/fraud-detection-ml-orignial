"""Fraud Simulation Lab API

An innovative sandbox environment for testing fraud scenarios,
training analysts, and validating detection rules without real risk.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import random
import uuid
import math
import numpy as np

router = APIRouter(prefix="/simulation", tags=["Simulation Lab"])


# ============== Enums ==============

class ScenarioCategory(str, Enum):
    CARD_NOT_PRESENT = "card_not_present"
    ACCOUNT_TAKEOVER = "account_takeover"
    IDENTITY_THEFT = "identity_theft"
    MONEY_LAUNDERING = "money_laundering"
    VELOCITY_ATTACK = "velocity_attack"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    FRIENDLY_FRAUD = "friendly_fraud"
    BUST_OUT = "bust_out"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== Pydantic Models ==============

class FraudScenario(BaseModel):
    id: str
    name: str
    category: ScenarioCategory
    difficulty: DifficultyLevel
    description: str
    learning_objectives: List[str]
    typical_indicators: List[str]
    real_world_examples: List[str]
    detection_tips: List[str]
    estimated_time_minutes: int


class SimulatedTransaction(BaseModel):
    id: str
    timestamp: datetime
    amount: float
    merchant: str
    merchant_category: str
    location: str
    card_present: bool
    is_fraud: bool
    fraud_indicators: List[str]
    risk_score: float
    velocity_flags: List[str]
    user_id: str
    device_fingerprint: str
    ip_address: str


class SimulationConfig(BaseModel):
    scenario_id: str
    num_transactions: int = Field(default=50, ge=10, le=500)
    fraud_rate: float = Field(default=0.15, ge=0.05, le=0.50)
    time_span_hours: int = Field(default=24, ge=1, le=168)
    include_edge_cases: bool = True
    randomize_patterns: bool = True


class SimulationResult(BaseModel):
    simulation_id: str
    scenario: FraudScenario
    status: SimulationStatus
    transactions: List[SimulatedTransaction]
    start_time: datetime
    end_time: Optional[datetime]
    stats: Dict[str, Any]
    analyst_score: Optional[float]
    feedback: Optional[str]


class AnalystDecision(BaseModel):
    transaction_id: str
    decision: str  # "fraud" or "legitimate"
    confidence: float = Field(ge=0, le=100)
    reasoning: Optional[str]


class AnalystSubmission(BaseModel):
    simulation_id: str
    decisions: List[AnalystDecision]
    time_taken_seconds: int


class AnalystEvaluation(BaseModel):
    simulation_id: str
    total_transactions: int
    correct_decisions: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positives: int
    false_negatives: int
    missed_fraud_amount: float
    blocked_legitimate_amount: float
    time_taken_seconds: int
    performance_grade: str
    detailed_feedback: List[str]
    areas_to_improve: List[str]
    badges_earned: List[str]


class CustomScenarioRequest(BaseModel):
    name: str
    description: str
    category: ScenarioCategory
    fraud_patterns: List[str]
    num_transactions: int = 50
    fraud_rate: float = 0.15


# ============== Predefined Scenarios ==============

FRAUD_SCENARIOS: Dict[str, FraudScenario] = {
    "cnp_basic": FraudScenario(
        id="cnp_basic",
        name="Card-Not-Present Attack",
        category=ScenarioCategory.CARD_NOT_PRESENT,
        difficulty=DifficultyLevel.BEGINNER,
        description="Simulates online fraud where stolen card details are used for unauthorized purchases. Common in e-commerce fraud.",
        learning_objectives=[
            "Identify unusual purchase patterns",
            "Recognize geographic anomalies",
            "Detect velocity indicators",
            "Understand device fingerprinting"
        ],
        typical_indicators=[
            "Multiple failed attempts before success",
            "Unusual purchase time",
            "High-value items",
            "New device/IP address",
            "Shipping differs from billing"
        ],
        real_world_examples=[
            "Stolen credit card used for electronics purchase",
            "Gift card fraud from data breach",
            "Carding attacks on e-commerce sites"
        ],
        detection_tips=[
            "Check for velocity of transactions",
            "Compare device fingerprint history",
            "Verify shipping address matches billing",
            "Look for unusual merchant categories"
        ],
        estimated_time_minutes=15
    ),
    "ato_intermediate": FraudScenario(
        id="ato_intermediate",
        name="Account Takeover Attack",
        category=ScenarioCategory.ACCOUNT_TAKEOVER,
        difficulty=DifficultyLevel.INTERMEDIATE,
        description="Simulates scenarios where fraudsters gain unauthorized access to legitimate user accounts through phishing, credential stuffing, or social engineering.",
        learning_objectives=[
            "Detect suspicious login patterns",
            "Identify password reset abuse",
            "Recognize behavior changes post-login",
            "Understand session hijacking indicators"
        ],
        typical_indicators=[
            "Login from new device/location",
            "Password change followed by transactions",
            "Unusual account settings changes",
            "Multiple failed login attempts",
            "Session from different IP mid-transaction"
        ],
        real_world_examples=[
            "Phishing attack leading to account compromise",
            "Credential stuffing from dark web data",
            "SIM swap to bypass 2FA"
        ],
        detection_tips=[
            "Monitor for device/location changes",
            "Track account settings modifications",
            "Implement step-up authentication",
            "Analyze login time patterns"
        ],
        estimated_time_minutes=25
    ),
    "velocity_attack": FraudScenario(
        id="velocity_attack",
        name="Rapid-Fire Velocity Attack",
        category=ScenarioCategory.VELOCITY_ATTACK,
        difficulty=DifficultyLevel.INTERMEDIATE,
        description="Simulates high-frequency transaction attacks where fraudsters attempt many small transactions quickly to test cards or drain accounts before detection.",
        learning_objectives=[
            "Recognize abnormal transaction frequency",
            "Identify testing patterns (small amounts)",
            "Understand time-window analysis",
            "Learn burst detection techniques"
        ],
        typical_indicators=[
            "Multiple transactions within minutes",
            "Small test amounts followed by large ones",
            "Same merchant hit multiple times",
            "Sequential card numbers tested",
            "Transactions just under velocity limits"
        ],
        real_world_examples=[
            "Card testing on donation sites",
            "BIN attacks on e-commerce",
            "Automated carding bots"
        ],
        detection_tips=[
            "Set velocity rules (X transactions in Y minutes)",
            "Monitor for small 'test' transactions",
            "Track merchant-specific patterns",
            "Implement progressive delays"
        ],
        estimated_time_minutes=20
    ),
    "money_laundering": FraudScenario(
        id="money_laundering",
        name="Layering & Structuring",
        category=ScenarioCategory.MONEY_LAUNDERING,
        difficulty=DifficultyLevel.ADVANCED,
        description="Simulates money laundering patterns including structuring (smurfing), layering through multiple accounts, and integration attempts.",
        learning_objectives=[
            "Identify structuring patterns",
            "Recognize round-number transactions",
            "Detect circular money flows",
            "Understand shell company indicators"
        ],
        typical_indicators=[
            "Transactions just under reporting thresholds",
            "Round amounts (e.g., $9,900)",
            "Rapid movement between accounts",
            "Unusual business transaction patterns",
            "Geographic dispersion of funds"
        ],
        real_world_examples=[
            "Cash deposits split to avoid $10K reporting",
            "Shell company invoice fraud",
            "Crypto-to-fiat laundering"
        ],
        detection_tips=[
            "Look for structuring patterns",
            "Analyze network of related accounts",
            "Monitor for unusual cash patterns",
            "Check business transaction ratios"
        ],
        estimated_time_minutes=35
    ),
    "synthetic_identity": FraudScenario(
        id="synthetic_identity",
        name="Synthetic Identity Fraud",
        category=ScenarioCategory.SYNTHETIC_IDENTITY,
        difficulty=DifficultyLevel.EXPERT,
        description="Simulates fraud using fabricated identities created by combining real and fake information. These 'Frankenstein IDs' are built over time to appear legitimate.",
        learning_objectives=[
            "Identify inconsistent identity elements",
            "Recognize credit building patterns",
            "Detect authorized user abuse",
            "Understand bust-out timing"
        ],
        typical_indicators=[
            "Thin credit file with sudden activity",
            "SSN/DOB/Name mismatches in databases",
            "Multiple identities with shared elements",
            "Authorized user on multiple accounts",
            "Address associated with fraud rings"
        ],
        real_world_examples=[
            "Child SSN used with adult identity",
            "Deceased person's information reused",
            "Credit piggybacking schemes"
        ],
        detection_tips=[
            "Cross-reference identity elements",
            "Analyze credit history depth",
            "Check for shared addresses/phones",
            "Monitor authorized user patterns"
        ],
        estimated_time_minutes=45
    ),
    "friendly_fraud": FraudScenario(
        id="friendly_fraud",
        name="Friendly Fraud / Chargeback Abuse",
        category=ScenarioCategory.FRIENDLY_FRAUD,
        difficulty=DifficultyLevel.INTERMEDIATE,
        description="Simulates scenarios where legitimate customers make purchases and then falsely claim fraud to get refunds while keeping the goods.",
        learning_objectives=[
            "Identify chargeback patterns",
            "Recognize serial abusers",
            "Understand dispute timing",
            "Learn evidence collection"
        ],
        typical_indicators=[
            "Previous chargebacks on account",
            "Digital goods with quick chargebacks",
            "Disputes after delivery confirmation",
            "Repeat purchases after refunds",
            "Claims don't match delivery data"
        ],
        real_world_examples=[
            "Digital download refund abuse",
            "Delivery confirmation ignored",
            "Family member unauthorized use claims"
        ],
        detection_tips=[
            "Track customer chargeback history",
            "Collect delivery proof",
            "Analyze dispute claim patterns",
            "Monitor repeat refund requests"
        ],
        estimated_time_minutes=25
    ),
    "bust_out": FraudScenario(
        id="bust_out",
        name="Bust-Out Fraud",
        category=ScenarioCategory.BUST_OUT,
        difficulty=DifficultyLevel.EXPERT,
        description="Simulates sophisticated fraud where accounts are built up with good payment history before 'busting out' with maximum credit utilization and disappearing.",
        learning_objectives=[
            "Identify account maturation patterns",
            "Recognize pre-bust-out signals",
            "Detect sudden behavior changes",
            "Understand credit utilization spikes"
        ],
        typical_indicators=[
            "Sudden max credit utilization",
            "Cash advance activity increase",
            "Balance transfer patterns",
            "Address/phone changes before spike",
            "Payment pattern changes"
        ],
        real_world_examples=[
            "Credit card bust-out rings",
            "Business credit fraud",
            "Authorized user manipulation"
        ],
        detection_tips=[
            "Monitor utilization velocity",
            "Track contact info changes",
            "Analyze payment behavior shifts",
            "Watch for cash-equivalent purchases"
        ],
        estimated_time_minutes=40
    )
}


# ============== Simulation Engine ==============

class SimulationEngine:
    """Engine for generating realistic fraud simulation data"""

    MERCHANTS = [
        ("Amazon", "E-commerce", False),
        ("Walmart Online", "E-commerce", False),
        ("Best Buy", "Electronics", True),
        ("Target", "Retail", True),
        ("Apple Store", "Electronics", True),
        ("Steam", "Digital Goods", False),
        ("Netflix", "Subscription", False),
        ("Uber", "Transportation", False),
        ("DoorDash", "Food Delivery", False),
        ("GameStop", "Gaming", True),
        ("Nike", "Apparel", True),
        ("Sephora", "Beauty", True),
        ("Home Depot", "Home Improvement", True),
        ("Costco", "Wholesale", True),
        ("Starbucks", "Food & Beverage", True),
        ("Shell Gas", "Fuel", True),
        ("CVS Pharmacy", "Pharmacy", True),
        ("Expedia", "Travel", False),
        ("Delta Airlines", "Travel", False),
        ("Hilton Hotels", "Lodging", True),
    ]

    LOCATIONS = [
        "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
        "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
        "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
        "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "Seattle, WA",
        "Denver, CO", "Boston, MA", "Detroit, MI", "Miami, FL"
    ]

    FOREIGN_LOCATIONS = [
        "London, UK", "Paris, France", "Tokyo, Japan", "Moscow, Russia",
        "Lagos, Nigeria", "Mumbai, India", "São Paulo, Brazil", "Bangkok, Thailand"
    ]

    def __init__(self, scenario: FraudScenario, config: SimulationConfig):
        self.scenario = scenario
        self.config = config
        self.base_time = datetime.now() - timedelta(hours=config.time_span_hours)

    def generate_transactions(self) -> List[SimulatedTransaction]:
        """Generate a mix of legitimate and fraudulent transactions"""
        transactions = []
        num_fraud = int(self.config.num_transactions * self.config.fraud_rate)
        num_legit = self.config.num_transactions - num_fraud

        # Generate legitimate transactions
        for _ in range(num_legit):
            transactions.append(self._generate_legitimate_transaction())

        # Generate fraudulent transactions based on scenario
        fraud_generator = self._get_fraud_generator()
        for _ in range(num_fraud):
            transactions.append(fraud_generator())

        # Shuffle and sort by timestamp
        random.shuffle(transactions)
        transactions.sort(key=lambda t: t.timestamp)

        return transactions

    def _get_fraud_generator(self):
        """Return appropriate fraud generator based on scenario"""
        generators = {
            ScenarioCategory.CARD_NOT_PRESENT: self._generate_cnp_fraud,
            ScenarioCategory.ACCOUNT_TAKEOVER: self._generate_ato_fraud,
            ScenarioCategory.VELOCITY_ATTACK: self._generate_velocity_fraud,
            ScenarioCategory.MONEY_LAUNDERING: self._generate_ml_fraud,
            ScenarioCategory.SYNTHETIC_IDENTITY: self._generate_synthetic_fraud,
            ScenarioCategory.FRIENDLY_FRAUD: self._generate_friendly_fraud,
            ScenarioCategory.BUST_OUT: self._generate_bustout_fraud,
            ScenarioCategory.IDENTITY_THEFT: self._generate_cnp_fraud,  # Similar patterns
        }
        return generators.get(self.scenario.category, self._generate_cnp_fraud)

    def _random_timestamp(self) -> datetime:
        """Generate random timestamp within simulation timespan"""
        offset = random.randint(0, self.config.time_span_hours * 3600)
        return self.base_time + timedelta(seconds=offset)

    def _generate_legitimate_transaction(self) -> SimulatedTransaction:
        """Generate a legitimate transaction"""
        merchant, category, card_present = random.choice(self.MERCHANTS)

        # Normal amount distribution
        amount = abs(np.random.lognormal(mean=3.5, sigma=1.0))
        amount = min(amount, 500)  # Cap at reasonable amount

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category=category,
            location=random.choice(self.LOCATIONS),
            card_present=card_present,
            is_fraud=False,
            fraud_indicators=[],
            risk_score=random.uniform(5, 25),
            velocity_flags=[],
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_{random.randint(100000, 999999)}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )

    def _generate_cnp_fraud(self) -> SimulatedTransaction:
        """Generate Card-Not-Present fraud transaction"""
        indicators = []
        velocity_flags = []

        # High-value electronics are common targets
        if random.random() > 0.5:
            merchant = "Best Buy"
            category = "Electronics"
            amount = random.uniform(300, 2000)
            indicators.append("High-value electronics purchase")
        else:
            merchant = random.choice(["Amazon", "Walmart Online", "Steam"])
            category = "E-commerce" if merchant != "Steam" else "Digital Goods"
            amount = random.uniform(50, 800)

        # Unusual timing
        hour = random.choice([2, 3, 4, 5, 23, 0, 1])  # Late night
        timestamp = self.base_time + timedelta(
            hours=random.randint(0, self.config.time_span_hours - 1),
            minutes=random.randint(0, 59)
        )
        timestamp = timestamp.replace(hour=hour)
        indicators.append("Unusual transaction hour")

        # Foreign IP
        if random.random() > 0.6:
            ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            indicators.append("Foreign IP address")
            velocity_flags.append("New IP address")
        else:
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

        # New device
        indicators.append("New device fingerprint")
        velocity_flags.append("First transaction from device")

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=timestamp,
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category=category,
            location=random.choice(self.FOREIGN_LOCATIONS if random.random() > 0.7 else self.LOCATIONS),
            card_present=False,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(65, 95),
            velocity_flags=velocity_flags,
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_NEW_{random.randint(100000, 999999)}",
            ip_address=ip
        )

    def _generate_ato_fraud(self) -> SimulatedTransaction:
        """Generate Account Takeover fraud transaction"""
        indicators = [
            "Login from new location",
            "Device not recognized",
            "Recent password change"
        ]

        if random.random() > 0.5:
            indicators.append("Account settings modified")
        if random.random() > 0.6:
            indicators.append("Multiple failed login attempts before success")

        merchant, category, _ = random.choice(self.MERCHANTS)
        amount = random.uniform(100, 1500)

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category=category,
            location=random.choice(self.FOREIGN_LOCATIONS),
            card_present=False,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(70, 95),
            velocity_flags=["New location", "New device", "Behavior change"],
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_HIJACK_{random.randint(100000, 999999)}",
            ip_address=f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )

    def _generate_velocity_fraud(self) -> SimulatedTransaction:
        """Generate Velocity Attack fraud transaction"""
        indicators = ["Part of rapid transaction sequence"]
        velocity_flags = ["Exceeds velocity threshold", "Multiple transactions in short window"]

        # Small test amounts or escalating amounts
        if random.random() > 0.7:
            amount = random.uniform(0.50, 5.00)  # Test amount
            indicators.append("Small test amount")
        else:
            amount = random.uniform(50, 300)
            indicators.append("Follows test transaction pattern")

        merchant, category, card_present = random.choice(self.MERCHANTS)

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category=category,
            location=random.choice(self.LOCATIONS),
            card_present=False,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(60, 90),
            velocity_flags=velocity_flags,
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_BOT_{random.randint(100000, 999999)}",
            ip_address=f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
        )

    def _generate_ml_fraud(self) -> SimulatedTransaction:
        """Generate Money Laundering fraud transaction"""
        indicators = []

        # Structuring - amounts just under reporting threshold
        if random.random() > 0.5:
            amount = random.uniform(9000, 9900)
            indicators.append("Amount just under $10K reporting threshold")
        else:
            # Round amounts
            amount = random.choice([5000, 7500, 8000, 9000, 9500]) + random.uniform(-50, 50)
            indicators.append("Suspicious round amount")

        indicators.append("Unusual transaction pattern for account")
        if random.random() > 0.6:
            indicators.append("Part of rapid fund movement sequence")

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant="Wire Transfer" if random.random() > 0.5 else "ACH Transfer",
            merchant_category="Financial Services",
            location=random.choice(self.LOCATIONS + self.FOREIGN_LOCATIONS),
            card_present=False,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(55, 85),
            velocity_flags=["Multiple transfers today", "Unusual transfer pattern"],
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_{random.randint(100000, 999999)}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )

    def _generate_synthetic_fraud(self) -> SimulatedTransaction:
        """Generate Synthetic Identity fraud transaction"""
        indicators = [
            "Thin credit file",
            "SSN issued recently",
            "Address linked to other synthetic identities"
        ]

        if random.random() > 0.5:
            indicators.append("Authorized user on multiple accounts")
        if random.random() > 0.6:
            indicators.append("Inconsistent identity elements")

        amount = random.uniform(200, 3000)
        merchant, category, card_present = random.choice(self.MERCHANTS)

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category=category,
            location=random.choice(self.LOCATIONS),
            card_present=card_present,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(50, 80),
            velocity_flags=["New account", "Rapid credit building"],
            user_id=f"synthetic_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_{random.randint(100000, 999999)}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )

    def _generate_friendly_fraud(self) -> SimulatedTransaction:
        """Generate Friendly Fraud transaction"""
        indicators = [
            "Previous chargeback on account",
            "Digital goods purchase"
        ]

        if random.random() > 0.5:
            indicators.append("Dispute filed after confirmed delivery")
        if random.random() > 0.6:
            indicators.append("Pattern of refund requests")

        # Digital goods are common targets
        merchant = random.choice(["Steam", "PlayStation Store", "Xbox Store", "iTunes", "Google Play"])
        amount = random.uniform(20, 200)

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category="Digital Goods",
            location=random.choice(self.LOCATIONS),
            card_present=False,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(45, 75),
            velocity_flags=["Multiple refund requests"],
            user_id=f"user_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_{random.randint(100000, 999999)}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )

    def _generate_bustout_fraud(self) -> SimulatedTransaction:
        """Generate Bust-Out fraud transaction"""
        indicators = [
            "Sudden credit utilization spike",
            "Recent address change",
            "Payment pattern deviation"
        ]

        if random.random() > 0.5:
            indicators.append("Cash advance activity")
        if random.random() > 0.4:
            indicators.append("Balance transfer before spike")

        # High-value, easy to resell items
        merchant = random.choice(["Best Buy", "Apple Store", "Jewelry Store", "Electronics Outlet"])
        amount = random.uniform(500, 5000)

        return SimulatedTransaction(
            id=str(uuid.uuid4())[:8],
            timestamp=self._random_timestamp(),
            amount=round(amount, 2),
            merchant=merchant,
            merchant_category="Electronics" if "Electronics" in merchant or "Apple" in merchant or "Best" in merchant else "Luxury",
            location=random.choice(self.LOCATIONS),
            card_present=random.random() > 0.5,
            is_fraud=True,
            fraud_indicators=indicators,
            risk_score=random.uniform(60, 90),
            velocity_flags=["Utilization spike", "Behavior change"],
            user_id=f"bustout_{random.randint(1000, 9999)}",
            device_fingerprint=f"fp_{random.randint(100000, 999999)}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        )


# ============== In-Memory Storage ==============

active_simulations: Dict[str, SimulationResult] = {}


# ============== API Endpoints ==============

@router.get("/scenarios", response_model=List[FraudScenario])
async def get_scenarios(
    category: Optional[ScenarioCategory] = None,
    difficulty: Optional[DifficultyLevel] = None
):
    """Get all available fraud simulation scenarios"""
    scenarios = list(FRAUD_SCENARIOS.values())

    if category:
        scenarios = [s for s in scenarios if s.category == category]
    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty]

    return scenarios


@router.get("/scenarios/{scenario_id}", response_model=FraudScenario)
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario"""
    if scenario_id not in FRAUD_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return FRAUD_SCENARIOS[scenario_id]


@router.post("/start", response_model=SimulationResult)
async def start_simulation(config: SimulationConfig):
    """Start a new fraud simulation"""
    if config.scenario_id not in FRAUD_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = FRAUD_SCENARIOS[config.scenario_id]
    simulation_id = str(uuid.uuid4())[:12]

    # Generate transactions
    engine = SimulationEngine(scenario, config)
    transactions = engine.generate_transactions()

    # Calculate stats
    fraud_count = sum(1 for t in transactions if t.is_fraud)
    total_amount = sum(t.amount for t in transactions)
    fraud_amount = sum(t.amount for t in transactions if t.is_fraud)

    result = SimulationResult(
        simulation_id=simulation_id,
        scenario=scenario,
        status=SimulationStatus.RUNNING,
        transactions=transactions,
        start_time=datetime.now(),
        end_time=None,
        stats={
            "total_transactions": len(transactions),
            "fraud_count": fraud_count,
            "legitimate_count": len(transactions) - fraud_count,
            "fraud_rate": fraud_count / len(transactions),
            "total_amount": round(total_amount, 2),
            "fraud_amount": round(fraud_amount, 2),
            "avg_risk_score": round(sum(t.risk_score for t in transactions) / len(transactions), 2)
        },
        analyst_score=None,
        feedback=None
    )

    active_simulations[simulation_id] = result
    return result


@router.get("/active/{simulation_id}", response_model=SimulationResult)
async def get_simulation(simulation_id: str):
    """Get an active simulation by ID"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return active_simulations[simulation_id]


@router.post("/submit", response_model=AnalystEvaluation)
async def submit_decisions(submission: AnalystSubmission):
    """Submit analyst decisions and get evaluation"""
    if submission.simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    simulation = active_simulations[submission.simulation_id]
    transactions = {t.id: t for t in simulation.transactions}

    # Evaluate decisions
    correct = 0
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    missed_fraud_amount = 0
    blocked_legitimate_amount = 0

    for decision in submission.decisions:
        if decision.transaction_id not in transactions:
            continue

        tx = transactions[decision.transaction_id]
        predicted_fraud = decision.decision.lower() == "fraud"
        actual_fraud = tx.is_fraud

        if predicted_fraud and actual_fraud:
            true_positives += 1
            correct += 1
        elif not predicted_fraud and not actual_fraud:
            true_negatives += 1
            correct += 1
        elif predicted_fraud and not actual_fraud:
            false_positives += 1
            blocked_legitimate_amount += tx.amount
        else:  # not predicted_fraud and actual_fraud
            false_negatives += 1
            missed_fraud_amount += tx.amount

    total = len(submission.decisions)
    accuracy = correct / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Determine grade
    if f1 >= 0.9:
        grade = "A+"
    elif f1 >= 0.85:
        grade = "A"
    elif f1 >= 0.8:
        grade = "B+"
    elif f1 >= 0.75:
        grade = "B"
    elif f1 >= 0.7:
        grade = "C+"
    elif f1 >= 0.65:
        grade = "C"
    elif f1 >= 0.6:
        grade = "D"
    else:
        grade = "F"

    # Generate feedback
    feedback = []
    areas_to_improve = []
    badges = []

    if accuracy >= 0.9:
        feedback.append("Excellent accuracy! You correctly identified most transactions.")
        badges.append("Sharp Eye")
    elif accuracy >= 0.75:
        feedback.append("Good accuracy. Keep practicing to improve further.")
    else:
        feedback.append("Accuracy needs improvement. Review the training materials.")
        areas_to_improve.append("Overall pattern recognition")

    if recall >= 0.9:
        feedback.append("Outstanding fraud detection rate!")
        badges.append("Fraud Hunter")
    elif recall < 0.7:
        areas_to_improve.append("Fraud detection sensitivity - you missed some fraudulent transactions")

    if precision >= 0.9:
        feedback.append("Excellent precision - minimal false alarms!")
        badges.append("Precision Master")
    elif precision < 0.7:
        areas_to_improve.append("False positive rate - some legitimate transactions were flagged")

    if false_negatives > 0:
        feedback.append(f"You missed {false_negatives} fraudulent transaction(s) totaling ${missed_fraud_amount:.2f}")

    if false_positives > 0:
        feedback.append(f"You blocked {false_positives} legitimate transaction(s) totaling ${blocked_legitimate_amount:.2f}")

    if submission.time_taken_seconds < simulation.scenario.estimated_time_minutes * 60 * 0.7:
        badges.append("Speed Demon")
        feedback.append("Impressive speed! But make sure you're not sacrificing accuracy.")

    if f1 >= 0.85 and submission.time_taken_seconds < simulation.scenario.estimated_time_minutes * 60:
        badges.append("Elite Analyst")

    # Update simulation
    simulation.status = SimulationStatus.COMPLETED
    simulation.end_time = datetime.now()
    simulation.analyst_score = f1 * 100

    return AnalystEvaluation(
        simulation_id=submission.simulation_id,
        total_transactions=total,
        correct_decisions=correct,
        accuracy=round(accuracy * 100, 2),
        precision=round(precision * 100, 2),
        recall=round(recall * 100, 2),
        f1_score=round(f1 * 100, 2),
        false_positives=false_positives,
        false_negatives=false_negatives,
        missed_fraud_amount=round(missed_fraud_amount, 2),
        blocked_legitimate_amount=round(blocked_legitimate_amount, 2),
        time_taken_seconds=submission.time_taken_seconds,
        performance_grade=grade,
        detailed_feedback=feedback,
        areas_to_improve=areas_to_improve,
        badges_earned=badges
    )


@router.get("/leaderboard")
async def get_leaderboard(scenario_id: Optional[str] = None, limit: int = 10):
    """Get top performers for simulations"""
    # Filter completed simulations with scores
    completed = [
        s for s in active_simulations.values()
        if s.status == SimulationStatus.COMPLETED and s.analyst_score is not None
    ]

    if scenario_id:
        completed = [s for s in completed if s.scenario.id == scenario_id]

    # Sort by score
    completed.sort(key=lambda s: s.analyst_score or 0, reverse=True)

    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "simulation_id": s.simulation_id,
                "scenario": s.scenario.name,
                "score": s.analyst_score,
                "completed_at": s.end_time
            }
            for i, s in enumerate(completed[:limit])
        ]
    }


@router.post("/custom-scenario", response_model=SimulationResult)
async def create_custom_simulation(request: CustomScenarioRequest):
    """Create a simulation with custom fraud patterns"""
    # Create custom scenario
    custom_scenario = FraudScenario(
        id=f"custom_{uuid.uuid4().hex[:8]}",
        name=request.name,
        category=request.category,
        difficulty=DifficultyLevel.INTERMEDIATE,
        description=request.description,
        learning_objectives=["Custom scenario training"],
        typical_indicators=request.fraud_patterns,
        real_world_examples=["Custom scenario"],
        detection_tips=["Apply general fraud detection principles"],
        estimated_time_minutes=20
    )

    config = SimulationConfig(
        scenario_id=custom_scenario.id,
        num_transactions=request.num_transactions,
        fraud_rate=request.fraud_rate
    )

    # Temporarily add to scenarios
    FRAUD_SCENARIOS[custom_scenario.id] = custom_scenario

    # Generate simulation
    engine = SimulationEngine(custom_scenario, config)
    transactions = engine.generate_transactions()

    simulation_id = str(uuid.uuid4())[:12]
    fraud_count = sum(1 for t in transactions if t.is_fraud)
    total_amount = sum(t.amount for t in transactions)
    fraud_amount = sum(t.amount for t in transactions if t.is_fraud)

    result = SimulationResult(
        simulation_id=simulation_id,
        scenario=custom_scenario,
        status=SimulationStatus.RUNNING,
        transactions=transactions,
        start_time=datetime.now(),
        end_time=None,
        stats={
            "total_transactions": len(transactions),
            "fraud_count": fraud_count,
            "legitimate_count": len(transactions) - fraud_count,
            "fraud_rate": fraud_count / len(transactions),
            "total_amount": round(total_amount, 2),
            "fraud_amount": round(fraud_amount, 2),
            "avg_risk_score": round(sum(t.risk_score for t in transactions) / len(transactions), 2)
        },
        analyst_score=None,
        feedback=None
    )

    active_simulations[simulation_id] = result
    return result


@router.get("/hints/{simulation_id}/{transaction_id}")
async def get_hint(simulation_id: str, transaction_id: str):
    """Get a hint for a specific transaction (costs points)"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    simulation = active_simulations[simulation_id]
    transaction = next((t for t in simulation.transactions if t.id == transaction_id), None)

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Provide hints without revealing the answer
    hints = []

    if transaction.risk_score > 70:
        hints.append("This transaction has a high risk score")
    elif transaction.risk_score > 40:
        hints.append("This transaction has a moderate risk score")
    else:
        hints.append("This transaction has a low risk score")

    if not transaction.card_present:
        hints.append("This is a card-not-present transaction")

    if transaction.velocity_flags:
        hints.append(f"Velocity flags detected: {len(transaction.velocity_flags)}")

    if transaction.location in SimulationEngine.FOREIGN_LOCATIONS:
        hints.append("Transaction originated from an unusual location")

    return {
        "transaction_id": transaction_id,
        "hints": hints,
        "hint_penalty": 5  # Points deducted for using hint
    }


@router.delete("/cancel/{simulation_id}")
async def cancel_simulation(simulation_id: str):
    """Cancel an active simulation"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    simulation = active_simulations[simulation_id]
    simulation.status = SimulationStatus.FAILED
    simulation.end_time = datetime.now()

    return {"message": "Simulation cancelled", "simulation_id": simulation_id}
