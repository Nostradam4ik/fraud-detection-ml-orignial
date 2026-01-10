"""Device Fingerprint Analyzer API - Advanced device identification and fraud detection"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import random
import math
import re

router = APIRouter(prefix="/device-fingerprint", tags=["Device Fingerprint"])


# ============== Models ==============

class DeviceFingerprint(BaseModel):
    """Device fingerprint data collected from client"""
    user_agent: str
    screen_resolution: str  # "1920x1080"
    color_depth: int  # 24
    timezone_offset: int  # -60 (minutes from UTC)
    language: str  # "en-US"
    platform: str  # "Win32", "MacIntel", "Linux x86_64"
    hardware_concurrency: Optional[int] = None  # CPU cores
    device_memory: Optional[float] = None  # GB
    canvas_hash: Optional[str] = None  # Canvas fingerprint
    webgl_hash: Optional[str] = None  # WebGL fingerprint
    audio_hash: Optional[str] = None  # Audio fingerprint
    fonts_hash: Optional[str] = None  # Installed fonts hash
    plugins: Optional[List[str]] = None
    touch_support: bool = False
    do_not_track: Optional[bool] = None
    cookies_enabled: bool = True
    local_storage: bool = True
    session_storage: bool = True
    indexed_db: bool = True
    ad_blocker: bool = False
    ip_address: Optional[str] = None

class FingerprintAnalysisRequest(BaseModel):
    """Request for fingerprint analysis"""
    user_id: str
    fingerprint: DeviceFingerprint
    transaction_id: Optional[str] = None

class DeviceHistoryRequest(BaseModel):
    """Request for device history"""
    user_id: str
    days: int = 30


# ============== Risk Indicators Database ==============

# Known suspicious user agent patterns
SUSPICIOUS_UA_PATTERNS = [
    r"HeadlessChrome",
    r"PhantomJS",
    r"Selenium",
    r"WebDriver",
    r"Puppeteer",
    r"Playwright",
    r"MSIE\s[1-6]\.",  # Very old IE versions
    r"Python-urllib",
    r"curl/",
    r"wget/",
    r"scrapy",
    r"bot|crawler|spider",
]

# Known VPN/Proxy IP ranges (simplified simulation)
SUSPICIOUS_IP_PATTERNS = [
    r"^10\.",  # Private ranges often used by VPNs
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
    r"^192\.168\.",
]

# Known emulator signatures
EMULATOR_SIGNATURES = {
    "generic_emulator": {
        "screen_resolutions": ["800x600", "1024x768"],
        "hardware_concurrency": [1, 2],
        "device_memory": [1, 2],
    },
    "android_emulator": {
        "platforms": ["Linux armv7l", "Linux armv8l"],
        "suspicious_ua": ["Android SDK", "google_sdk", "Emulator"],
    },
    "ios_simulator": {
        "platforms": ["MacIntel"],  # iOS simulator runs on Mac
        "suspicious_ua": ["iPhone Simulator", "iPad Simulator"],
    }
}

# Browser consistency checks
BROWSER_PLATFORM_MAP = {
    "Chrome": ["Win32", "Win64", "MacIntel", "Linux x86_64", "Linux armv7l", "Linux armv8l"],
    "Firefox": ["Win32", "Win64", "MacIntel", "Linux x86_64"],
    "Safari": ["MacIntel", "iPhone", "iPad"],
    "Edge": ["Win32", "Win64", "MacIntel"],
}


# ============== Analysis Functions ==============

def generate_fingerprint_hash(fingerprint: DeviceFingerprint) -> str:
    """Generate a unique hash for the device fingerprint"""
    components = [
        fingerprint.user_agent,
        fingerprint.screen_resolution,
        str(fingerprint.color_depth),
        str(fingerprint.timezone_offset),
        fingerprint.language,
        fingerprint.platform,
        str(fingerprint.hardware_concurrency or ""),
        str(fingerprint.device_memory or ""),
        fingerprint.canvas_hash or "",
        fingerprint.webgl_hash or "",
        fingerprint.audio_hash or "",
        fingerprint.fonts_hash or "",
    ]
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def detect_automation(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
    """Detect automated/bot traffic"""
    indicators = []
    risk_score = 0

    # Check user agent for automation tools
    for pattern in SUSPICIOUS_UA_PATTERNS:
        if re.search(pattern, fingerprint.user_agent, re.IGNORECASE):
            indicators.append({
                "type": "automation_tool",
                "detail": f"Suspicious UA pattern: {pattern}",
                "severity": "high"
            })
            risk_score += 30

    # Check for headless browser indicators
    if fingerprint.plugins is not None and len(fingerprint.plugins) == 0:
        indicators.append({
            "type": "no_plugins",
            "detail": "No browser plugins detected (common in headless browsers)",
            "severity": "medium"
        })
        risk_score += 15

    # WebDriver detection
    if "webdriver" in fingerprint.user_agent.lower():
        indicators.append({
            "type": "webdriver",
            "detail": "WebDriver detected in user agent",
            "severity": "high"
        })
        risk_score += 40

    # Unusual screen resolution for automated tools
    if fingerprint.screen_resolution in ["800x600", "1024x768", "0x0"]:
        indicators.append({
            "type": "suspicious_resolution",
            "detail": f"Unusual resolution: {fingerprint.screen_resolution}",
            "severity": "low"
        })
        risk_score += 10

    return {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "risk_score": min(risk_score, 100)
    }


def detect_emulator(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
    """Detect emulator/simulator usage"""
    indicators = []
    risk_score = 0

    # Check for generic emulator signatures
    if fingerprint.hardware_concurrency and fingerprint.hardware_concurrency <= 2:
        if fingerprint.device_memory and fingerprint.device_memory <= 2:
            indicators.append({
                "type": "low_resources",
                "detail": f"Very low resources: {fingerprint.hardware_concurrency} cores, {fingerprint.device_memory}GB RAM",
                "severity": "medium"
            })
            risk_score += 20

    # Android emulator detection
    for sig in EMULATOR_SIGNATURES["android_emulator"]["suspicious_ua"]:
        if sig.lower() in fingerprint.user_agent.lower():
            indicators.append({
                "type": "android_emulator",
                "detail": f"Android emulator signature detected: {sig}",
                "severity": "high"
            })
            risk_score += 35

    # iOS simulator detection
    if fingerprint.platform == "MacIntel":
        for sig in EMULATOR_SIGNATURES["ios_simulator"]["suspicious_ua"]:
            if sig.lower() in fingerprint.user_agent.lower():
                indicators.append({
                    "type": "ios_simulator",
                    "detail": f"iOS simulator signature detected: {sig}",
                    "severity": "high"
                })
                risk_score += 35

    # Touch support inconsistency
    if "Mobile" in fingerprint.user_agent and not fingerprint.touch_support:
        indicators.append({
            "type": "touch_inconsistency",
            "detail": "Mobile UA but no touch support (possible emulator)",
            "severity": "medium"
        })
        risk_score += 25

    return {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "risk_score": min(risk_score, 100)
    }


def detect_vpn_proxy(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
    """Detect VPN/Proxy usage"""
    indicators = []
    risk_score = 0

    if fingerprint.ip_address:
        # Check suspicious IP patterns
        for pattern in SUSPICIOUS_IP_PATTERNS:
            if re.match(pattern, fingerprint.ip_address):
                indicators.append({
                    "type": "suspicious_ip_range",
                    "detail": f"IP in suspicious range: {fingerprint.ip_address}",
                    "severity": "low"
                })
                risk_score += 10

    # Timezone vs IP location mismatch (simulated)
    # In real implementation, would use GeoIP
    if fingerprint.timezone_offset:
        # Unusual timezone offsets
        if abs(fingerprint.timezone_offset) > 720:  # More than 12 hours
            indicators.append({
                "type": "invalid_timezone",
                "detail": f"Invalid timezone offset: {fingerprint.timezone_offset}",
                "severity": "medium"
            })
            risk_score += 20

    return {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "risk_score": min(risk_score, 100)
    }


def detect_browser_tampering(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
    """Detect modified/tampered browsers"""
    indicators = []
    risk_score = 0

    # Check browser-platform consistency
    browser = None
    if "Chrome" in fingerprint.user_agent and "Edg" not in fingerprint.user_agent:
        browser = "Chrome"
    elif "Firefox" in fingerprint.user_agent:
        browser = "Firefox"
    elif "Safari" in fingerprint.user_agent and "Chrome" not in fingerprint.user_agent:
        browser = "Safari"
    elif "Edg" in fingerprint.user_agent:
        browser = "Edge"

    if browser and browser in BROWSER_PLATFORM_MAP:
        valid_platforms = BROWSER_PLATFORM_MAP[browser]
        if fingerprint.platform not in valid_platforms:
            indicators.append({
                "type": "platform_mismatch",
                "detail": f"{browser} on unexpected platform: {fingerprint.platform}",
                "severity": "high"
            })
            risk_score += 30

    # Check for privacy browser modifications
    if fingerprint.do_not_track and fingerprint.ad_blocker:
        if not fingerprint.cookies_enabled or not fingerprint.local_storage:
            indicators.append({
                "type": "privacy_mode",
                "detail": "Enhanced privacy settings detected",
                "severity": "low"
            })
            risk_score += 5

    # Canvas fingerprint consistency
    if fingerprint.canvas_hash:
        # Spoofed canvas fingerprints are often all zeros or generic
        if fingerprint.canvas_hash in ["0" * 32, "f" * 32, "a" * 32]:
            indicators.append({
                "type": "spoofed_canvas",
                "detail": "Canvas fingerprint appears spoofed",
                "severity": "high"
            })
            risk_score += 35

    # WebGL renderer check
    if fingerprint.webgl_hash:
        if fingerprint.webgl_hash in ["0" * 32, "f" * 32]:
            indicators.append({
                "type": "spoofed_webgl",
                "detail": "WebGL fingerprint appears spoofed",
                "severity": "high"
            })
            risk_score += 35

    return {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "risk_score": min(risk_score, 100)
    }


def detect_device_cloning(fingerprint: DeviceFingerprint, user_id: str) -> Dict[str, Any]:
    """Detect if device fingerprint is used by multiple users (cloning)"""
    indicators = []
    risk_score = 0

    # Simulated check - in real implementation would check database
    # This simulates finding the same fingerprint used by different users
    fingerprint_hash = generate_fingerprint_hash(fingerprint)

    # Simulate some fingerprints being shared (for demo)
    simulated_shared = random.random() < 0.1  # 10% chance for demo

    if simulated_shared:
        other_users = random.randint(2, 5)
        indicators.append({
            "type": "shared_fingerprint",
            "detail": f"Device fingerprint seen with {other_users} other user accounts",
            "severity": "critical"
        })
        risk_score += 50

    return {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "risk_score": min(risk_score, 100)
    }


def calculate_device_trust_score(fingerprint: DeviceFingerprint) -> Dict[str, Any]:
    """Calculate overall device trust score"""
    trust_factors = []
    score = 100  # Start with full trust

    # Modern browser check
    modern_browsers = ["Chrome/1[0-9]{2}", "Firefox/1[0-9]{2}", "Safari/[0-9]{3}", "Edg/1[0-9]{2}"]
    is_modern = any(re.search(pattern, fingerprint.user_agent) for pattern in modern_browsers)
    if is_modern:
        trust_factors.append({"factor": "modern_browser", "impact": 10, "positive": True})
    else:
        trust_factors.append({"factor": "outdated_browser", "impact": -15, "positive": False})
        score -= 15

    # Standard features available
    if fingerprint.cookies_enabled and fingerprint.local_storage:
        trust_factors.append({"factor": "standard_features", "impact": 5, "positive": True})
    else:
        trust_factors.append({"factor": "limited_features", "impact": -10, "positive": False})
        score -= 10

    # Canvas/WebGL available (indicates real browser)
    if fingerprint.canvas_hash and fingerprint.webgl_hash:
        trust_factors.append({"factor": "rendering_apis", "impact": 15, "positive": True})
    else:
        trust_factors.append({"factor": "missing_apis", "impact": -20, "positive": False})
        score -= 20

    # Reasonable hardware specs
    if fingerprint.hardware_concurrency and fingerprint.hardware_concurrency >= 4:
        trust_factors.append({"factor": "adequate_hardware", "impact": 5, "positive": True})

    # Consistent platform/UA
    if fingerprint.platform in ["Win32", "Win64", "MacIntel"]:
        if "Windows" in fingerprint.user_agent or "Mac" in fingerprint.user_agent:
            trust_factors.append({"factor": "consistent_platform", "impact": 10, "positive": True})

    return {
        "score": max(0, min(100, score)),
        "factors": trust_factors,
        "level": "high" if score >= 80 else "medium" if score >= 50 else "low"
    }


# ============== API Endpoints ==============

@router.post("/analyze")
async def analyze_fingerprint(request: FingerprintAnalysisRequest):
    """
    Comprehensive device fingerprint analysis
    Returns risk assessment and detected anomalies
    """
    fingerprint = request.fingerprint

    # Run all detection algorithms
    automation = detect_automation(fingerprint)
    emulator = detect_emulator(fingerprint)
    vpn_proxy = detect_vpn_proxy(fingerprint)
    tampering = detect_browser_tampering(fingerprint)
    cloning = detect_device_cloning(fingerprint, request.user_id)
    trust = calculate_device_trust_score(fingerprint)

    # Generate fingerprint hash
    fingerprint_hash = generate_fingerprint_hash(fingerprint)

    # Calculate overall risk
    total_risk = (
        automation["risk_score"] * 0.25 +
        emulator["risk_score"] * 0.25 +
        vpn_proxy["risk_score"] * 0.15 +
        tampering["risk_score"] * 0.20 +
        cloning["risk_score"] * 0.15
    )

    # Collect all indicators
    all_indicators = (
        automation["indicators"] +
        emulator["indicators"] +
        vpn_proxy["indicators"] +
        tampering["indicators"] +
        cloning["indicators"]
    )

    # Determine risk level
    if total_risk >= 70:
        risk_level = "critical"
        recommendation = "Block transaction and require additional verification"
    elif total_risk >= 50:
        risk_level = "high"
        recommendation = "Require step-up authentication (2FA, biometrics)"
    elif total_risk >= 30:
        risk_level = "medium"
        recommendation = "Monitor transaction closely, may require verification"
    else:
        risk_level = "low"
        recommendation = "Proceed with standard security measures"

    return {
        "fingerprint_hash": fingerprint_hash,
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "user_id": request.user_id,
        "transaction_id": request.transaction_id,
        "overall_risk": {
            "score": round(total_risk, 1),
            "level": risk_level,
            "recommendation": recommendation
        },
        "trust_score": trust,
        "detections": {
            "automation": automation,
            "emulator": emulator,
            "vpn_proxy": vpn_proxy,
            "browser_tampering": tampering,
            "device_cloning": cloning
        },
        "all_indicators": all_indicators,
        "device_info": {
            "browser": extract_browser(fingerprint.user_agent),
            "os": extract_os(fingerprint.user_agent),
            "device_type": detect_device_type(fingerprint),
            "screen": fingerprint.screen_resolution,
            "language": fingerprint.language,
            "timezone": f"UTC{'+' if fingerprint.timezone_offset <= 0 else '-'}{abs(fingerprint.timezone_offset)//60}"
        }
    }


@router.get("/history/{user_id}")
async def get_device_history(user_id: str, days: int = 30):
    """
    Get device fingerprint history for a user
    Shows all devices used and any anomalies detected
    """
    # Simulated device history
    devices = []
    num_devices = random.randint(1, 4)

    for i in range(num_devices):
        device_type = random.choice(["desktop", "mobile", "tablet"])
        browser = random.choice(["Chrome", "Firefox", "Safari", "Edge"])
        os = random.choice(["Windows 11", "Windows 10", "macOS", "iOS", "Android"])

        first_seen = datetime.utcnow() - timedelta(days=random.randint(1, days))
        last_seen = datetime.utcnow() - timedelta(hours=random.randint(0, 72))

        devices.append({
            "fingerprint_hash": hashlib.sha256(f"device_{user_id}_{i}".encode()).hexdigest()[:32],
            "device_type": device_type,
            "browser": browser,
            "os": os,
            "first_seen": first_seen.isoformat(),
            "last_seen": last_seen.isoformat(),
            "total_sessions": random.randint(5, 100),
            "total_transactions": random.randint(10, 500),
            "trust_level": random.choice(["high", "high", "high", "medium", "low"]),
            "is_current": i == 0,
            "location": random.choice(["New York, US", "London, UK", "Paris, FR", "Tokyo, JP"]),
            "risk_flags": random.randint(0, 3)
        })

    # Simulated anomalies
    anomalies = []
    if random.random() < 0.3:
        anomalies.append({
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat(),
            "type": "new_device",
            "description": "New device added to account",
            "severity": "low"
        })
    if random.random() < 0.2:
        anomalies.append({
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 5))).isoformat(),
            "type": "location_change",
            "description": "Device location changed significantly",
            "severity": "medium"
        })

    return {
        "user_id": user_id,
        "period_days": days,
        "total_devices": len(devices),
        "devices": devices,
        "anomalies": anomalies,
        "summary": {
            "primary_device": devices[0]["fingerprint_hash"] if devices else None,
            "high_trust_devices": sum(1 for d in devices if d["trust_level"] == "high"),
            "flagged_devices": sum(1 for d in devices if d["risk_flags"] > 0)
        }
    }


@router.get("/known-threats")
async def get_known_threats():
    """
    Get list of known device threats and detection capabilities
    """
    return {
        "threat_categories": [
            {
                "id": "automation",
                "name": "Automation & Bots",
                "description": "Detection of automated scripts, headless browsers, and bot traffic",
                "indicators": [
                    "Selenium/WebDriver signatures",
                    "Headless Chrome detection",
                    "Missing browser plugins",
                    "Unusual user agents"
                ],
                "severity": "high"
            },
            {
                "id": "emulator",
                "name": "Emulators & Simulators",
                "description": "Detection of virtual devices and mobile emulators",
                "indicators": [
                    "Android emulator signatures",
                    "iOS simulator detection",
                    "Low hardware resources",
                    "Touch capability mismatches"
                ],
                "severity": "high"
            },
            {
                "id": "vpn_proxy",
                "name": "VPN & Proxy",
                "description": "Detection of IP masking and location spoofing",
                "indicators": [
                    "Known VPN IP ranges",
                    "Datacenter IP detection",
                    "Timezone inconsistencies",
                    "WebRTC leaks"
                ],
                "severity": "medium"
            },
            {
                "id": "tampering",
                "name": "Browser Tampering",
                "description": "Detection of modified browsers and fingerprint spoofing",
                "indicators": [
                    "Canvas fingerprint spoofing",
                    "WebGL manipulation",
                    "User agent modification",
                    "Platform inconsistencies"
                ],
                "severity": "high"
            },
            {
                "id": "cloning",
                "name": "Device Cloning",
                "description": "Detection of shared or cloned device fingerprints",
                "indicators": [
                    "Same fingerprint multiple users",
                    "Fingerprint farm detection",
                    "Cookie/session sharing"
                ],
                "severity": "critical"
            }
        ],
        "detection_capabilities": {
            "browser_types": ["Chrome", "Firefox", "Safari", "Edge", "Opera"],
            "platforms": ["Windows", "macOS", "Linux", "iOS", "Android"],
            "fingerprint_components": [
                "User Agent", "Screen Resolution", "Color Depth", "Timezone",
                "Language", "Platform", "Hardware Concurrency", "Device Memory",
                "Canvas Hash", "WebGL Hash", "Audio Hash", "Fonts Hash",
                "Plugins", "Touch Support", "DNT", "Storage APIs"
            ]
        }
    }


@router.post("/simulate-threat")
async def simulate_threat(threat_type: str = "automation"):
    """
    Simulate a specific threat for testing/demo purposes
    """
    simulated_fingerprints = {
        "automation": DeviceFingerprint(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/91.0.4472.124 Safari/537.36",
            screen_resolution="800x600",
            color_depth=24,
            timezone_offset=0,
            language="en-US",
            platform="Linux x86_64",
            hardware_concurrency=2,
            device_memory=2,
            plugins=[],
            touch_support=False,
            cookies_enabled=True
        ),
        "emulator": DeviceFingerprint(
            user_agent="Mozilla/5.0 (Linux; Android 11; Android SDK built for x86) AppleWebKit/537.36",
            screen_resolution="1080x1920",
            color_depth=24,
            timezone_offset=-300,
            language="en-US",
            platform="Linux armv7l",
            hardware_concurrency=2,
            device_memory=2,
            touch_support=False,  # Inconsistent
            cookies_enabled=True
        ),
        "tampering": DeviceFingerprint(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0",
            screen_resolution="1920x1080",
            color_depth=24,
            timezone_offset=-300,
            language="en-US",
            platform="MacIntel",  # Inconsistent with Windows UA
            hardware_concurrency=8,
            device_memory=16,
            canvas_hash="0" * 32,  # Spoofed
            webgl_hash="0" * 32,  # Spoofed
            cookies_enabled=True
        ),
        "legitimate": DeviceFingerprint(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            screen_resolution="1920x1080",
            color_depth=24,
            timezone_offset=-300,
            language="en-US",
            platform="Win32",
            hardware_concurrency=8,
            device_memory=16,
            canvas_hash="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            webgl_hash="q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6",
            plugins=["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
            touch_support=False,
            cookies_enabled=True,
            local_storage=True
        )
    }

    fingerprint = simulated_fingerprints.get(threat_type, simulated_fingerprints["legitimate"])

    request = FingerprintAnalysisRequest(
        user_id="demo_user",
        fingerprint=fingerprint,
        transaction_id=f"sim_{threat_type}_{datetime.utcnow().timestamp()}"
    )

    return await analyze_fingerprint(request)


@router.get("/stats")
async def get_fingerprint_stats():
    """
    Get overall device fingerprint statistics
    """
    return {
        "period": "last_30_days",
        "total_devices_analyzed": random.randint(10000, 50000),
        "unique_fingerprints": random.randint(5000, 20000),
        "threats_detected": {
            "automation": random.randint(50, 200),
            "emulator": random.randint(20, 100),
            "vpn_proxy": random.randint(100, 500),
            "tampering": random.randint(30, 150),
            "cloning": random.randint(5, 30)
        },
        "trust_distribution": {
            "high": random.randint(60, 80),
            "medium": random.randint(15, 30),
            "low": random.randint(5, 15)
        },
        "device_types": {
            "desktop": random.randint(40, 60),
            "mobile": random.randint(30, 45),
            "tablet": random.randint(5, 15)
        },
        "top_browsers": [
            {"name": "Chrome", "percentage": random.randint(55, 70)},
            {"name": "Safari", "percentage": random.randint(15, 25)},
            {"name": "Firefox", "percentage": random.randint(5, 15)},
            {"name": "Edge", "percentage": random.randint(3, 10)}
        ]
    }


# ============== Helper Functions ==============

def extract_browser(user_agent: str) -> str:
    """Extract browser name from user agent"""
    if "Edg/" in user_agent:
        return "Edge"
    elif "Chrome" in user_agent:
        return "Chrome"
    elif "Firefox" in user_agent:
        return "Firefox"
    elif "Safari" in user_agent:
        return "Safari"
    elif "Opera" in user_agent or "OPR" in user_agent:
        return "Opera"
    return "Unknown"


def extract_os(user_agent: str) -> str:
    """Extract OS from user agent"""
    if "Windows NT 10" in user_agent:
        return "Windows 10/11"
    elif "Windows NT" in user_agent:
        return "Windows"
    elif "Mac OS X" in user_agent:
        return "macOS"
    elif "iPhone" in user_agent:
        return "iOS"
    elif "iPad" in user_agent:
        return "iPadOS"
    elif "Android" in user_agent:
        return "Android"
    elif "Linux" in user_agent:
        return "Linux"
    return "Unknown"


def detect_device_type(fingerprint: DeviceFingerprint) -> str:
    """Detect device type from fingerprint"""
    if fingerprint.touch_support:
        if "iPad" in fingerprint.user_agent:
            return "tablet"
        elif "Mobile" in fingerprint.user_agent or "iPhone" in fingerprint.user_agent:
            return "mobile"

    # Check screen resolution for mobile/tablet
    if fingerprint.screen_resolution:
        try:
            width, height = map(int, fingerprint.screen_resolution.split("x"))
            if max(width, height) <= 1024:
                return "mobile"
            elif max(width, height) <= 1366 and fingerprint.touch_support:
                return "tablet"
        except:
            pass

    return "desktop"
