"""
ML Model Drift Detection
Monitors model performance and data distribution for drift

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriftSeverity(Enum):
    """Severity levels for drift detection"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftResult:
    """Result of drift detection"""
    drift_detected: bool
    severity: DriftSeverity
    drift_score: float
    details: Dict
    timestamp: str
    recommendations: List[str]


class DataDriftDetector:
    """Detect data distribution drift"""

    def __init__(
        self,
        reference_data: np.ndarray,
        threshold_ks: float = 0.1,
        threshold_psi: float = 0.2
    ):
        """
        Initialize with reference (training) data distribution

        Args:
            reference_data: Reference data to compare against
            threshold_ks: KS test threshold for drift detection
            threshold_psi: PSI threshold for drift detection
        """
        self.reference_data = reference_data
        self.threshold_ks = threshold_ks
        self.threshold_psi = threshold_psi

        # Calculate reference statistics
        self.reference_stats = self._calculate_statistics(reference_data)

    def _calculate_statistics(self, data: np.ndarray) -> Dict:
        """Calculate distribution statistics"""
        return {
            'mean': np.mean(data, axis=0),
            'std': np.std(data, axis=0),
            'median': np.median(data, axis=0),
            'min': np.min(data, axis=0),
            'max': np.max(data, axis=0),
            'percentiles': {
                '25': np.percentile(data, 25, axis=0),
                '75': np.percentile(data, 75, axis=0)
            }
        }

    def kolmogorov_smirnov_test(
        self,
        current_data: np.ndarray,
        feature_idx: int = None
    ) -> Tuple[float, float]:
        """
        Perform KS test to detect distribution drift

        Returns:
            (statistic, p_value)
        """
        if feature_idx is not None:
            ref = self.reference_data[:, feature_idx]
            curr = current_data[:, feature_idx]
        else:
            ref = self.reference_data.flatten()
            curr = current_data.flatten()

        statistic, p_value = stats.ks_2samp(ref, curr)
        return statistic, p_value

    def population_stability_index(
        self,
        current_data: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI)

        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Slight change
        PSI >= 0.2: Significant change
        """
        psi_values = []

        for feature_idx in range(self.reference_data.shape[1]):
            ref_feature = self.reference_data[:, feature_idx]
            curr_feature = current_data[:, feature_idx]

            # Create bins based on reference data
            bins = np.linspace(
                min(ref_feature.min(), curr_feature.min()),
                max(ref_feature.max(), curr_feature.max()),
                n_bins + 1
            )

            # Calculate bin frequencies
            ref_counts, _ = np.histogram(ref_feature, bins=bins)
            curr_counts, _ = np.histogram(curr_feature, bins=bins)

            # Convert to percentages (add small epsilon to avoid division by zero)
            epsilon = 1e-10
            ref_pct = (ref_counts + epsilon) / (len(ref_feature) + epsilon * n_bins)
            curr_pct = (curr_counts + epsilon) / (len(curr_feature) + epsilon * n_bins)

            # Calculate PSI for this feature
            psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
            psi_values.append(psi)

        return np.mean(psi_values)

    def detect_drift(self, current_data: np.ndarray) -> DriftResult:
        """
        Detect data drift using multiple methods

        Args:
            current_data: Current production data

        Returns:
            DriftResult with detection details
        """
        logger.info("Running data drift detection...")

        # PSI calculation
        psi = self.population_stability_index(current_data)
        logger.info(f"PSI: {psi:.4f}")

        # KS test for each feature
        ks_results = []
        for i in range(self.reference_data.shape[1]):
            stat, p_value = self.kolmogorov_smirnov_test(current_data, i)
            ks_results.append({
                'feature': i,
                'statistic': stat,
                'p_value': p_value,
                'drift': stat > self.threshold_ks or p_value < 0.05
            })

        # Count drifted features
        drifted_features = sum(1 for r in ks_results if r['drift'])
        drift_ratio = drifted_features / len(ks_results)

        # Determine severity
        if psi < 0.1 and drift_ratio < 0.1:
            severity = DriftSeverity.NONE
        elif psi < 0.15 and drift_ratio < 0.2:
            severity = DriftSeverity.LOW
        elif psi < 0.2 and drift_ratio < 0.3:
            severity = DriftSeverity.MEDIUM
        elif psi < 0.3 and drift_ratio < 0.5:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        # Calculate overall drift score (0-1)
        drift_score = min(1.0, (psi / 0.3 + drift_ratio) / 2)

        # Generate recommendations
        recommendations = []
        if severity in [DriftSeverity.MEDIUM, DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
            recommendations.append("Consider retraining the model with recent data")
        if drift_ratio > 0.3:
            recommendations.append("Investigate features with significant drift")
        if psi > 0.25:
            recommendations.append("Data distribution has changed significantly")
        if severity == DriftSeverity.CRITICAL:
            recommendations.append("URGENT: Model may be unreliable, immediate attention required")

        result = DriftResult(
            drift_detected=severity != DriftSeverity.NONE,
            severity=severity,
            drift_score=drift_score,
            details={
                'psi': psi,
                'drift_ratio': drift_ratio,
                'drifted_features': drifted_features,
                'total_features': len(ks_results),
                'ks_results': ks_results[:10]  # Top 10 features
            },
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )

        logger.info(f"Drift Detection Result: {severity.value} (score: {drift_score:.4f})")
        return result


class ModelPerformanceDriftDetector:
    """Detect model performance drift over time"""

    def __init__(
        self,
        baseline_metrics: Dict[str, float],
        threshold_accuracy: float = 0.05,
        threshold_f1: float = 0.1
    ):
        """
        Initialize with baseline performance metrics

        Args:
            baseline_metrics: Baseline model metrics from training
            threshold_accuracy: Acceptable accuracy drop threshold
            threshold_f1: Acceptable F1 score drop threshold
        """
        self.baseline_metrics = baseline_metrics
        self.threshold_accuracy = threshold_accuracy
        self.threshold_f1 = threshold_f1
        self.performance_history: List[Dict] = []

    def add_performance_sample(
        self,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None
    ):
        """Add a performance measurement to history"""
        self.performance_history.append({
            'metrics': metrics,
            'timestamp': timestamp or datetime.now()
        })

    def detect_performance_drift(
        self,
        current_metrics: Dict[str, float]
    ) -> DriftResult:
        """
        Detect performance drift compared to baseline

        Args:
            current_metrics: Current model performance metrics

        Returns:
            DriftResult with detection details
        """
        logger.info("Running performance drift detection...")

        # Calculate degradation
        degradation = {}
        for metric, baseline_value in self.baseline_metrics.items():
            if metric in current_metrics:
                current_value = current_metrics[metric]
                drop = baseline_value - current_value
                drop_pct = (drop / baseline_value) * 100 if baseline_value > 0 else 0
                degradation[metric] = {
                    'baseline': baseline_value,
                    'current': current_value,
                    'drop': drop,
                    'drop_pct': drop_pct
                }

        # Check critical metrics
        accuracy_drop = degradation.get('accuracy', {}).get('drop', 0)
        f1_drop = degradation.get('f1_score', {}).get('drop', 0)

        # Determine severity
        if accuracy_drop <= 0 and f1_drop <= 0:
            severity = DriftSeverity.NONE
        elif accuracy_drop < self.threshold_accuracy and f1_drop < self.threshold_f1:
            severity = DriftSeverity.LOW
        elif accuracy_drop < self.threshold_accuracy * 2 and f1_drop < self.threshold_f1 * 2:
            severity = DriftSeverity.MEDIUM
        elif accuracy_drop < self.threshold_accuracy * 3:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        # Calculate drift score
        drift_score = min(1.0, max(
            accuracy_drop / (self.threshold_accuracy * 3),
            f1_drop / (self.threshold_f1 * 3)
        ))

        # Recommendations
        recommendations = []
        if severity in [DriftSeverity.MEDIUM, DriftSeverity.HIGH]:
            recommendations.append("Model performance is degrading, consider retraining")
        if severity == DriftSeverity.CRITICAL:
            recommendations.append("CRITICAL: Model performance severely degraded")
            recommendations.append("Immediate retraining recommended")
        if f1_drop > accuracy_drop * 2:
            recommendations.append("Class imbalance may have changed in production data")

        result = DriftResult(
            drift_detected=severity != DriftSeverity.NONE,
            severity=severity,
            drift_score=drift_score,
            details={
                'degradation': degradation,
                'baseline_metrics': self.baseline_metrics,
                'current_metrics': current_metrics
            },
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )

        logger.info(f"Performance Drift Result: {severity.value}")
        return result


class ConceptDriftDetector:
    """Detect concept drift (changes in the relationship between features and target)"""

    def __init__(self, window_size: int = 1000, threshold: float = 0.1):
        """
        Initialize concept drift detector

        Args:
            window_size: Size of sliding window for comparison
            threshold: Threshold for drift detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.prediction_history: List[Dict] = []

    def add_prediction(
        self,
        features: np.ndarray,
        prediction: int,
        probability: float,
        actual: Optional[int] = None
    ):
        """Add a prediction to history"""
        self.prediction_history.append({
            'features': features,
            'prediction': prediction,
            'probability': probability,
            'actual': actual,
            'timestamp': datetime.now()
        })

        # Keep only recent history
        if len(self.prediction_history) > self.window_size * 2:
            self.prediction_history = self.prediction_history[-self.window_size * 2:]

    def detect_concept_drift(self) -> DriftResult:
        """
        Detect concept drift using prediction confidence and error rates

        Returns:
            DriftResult with detection details
        """
        if len(self.prediction_history) < self.window_size * 2:
            return DriftResult(
                drift_detected=False,
                severity=DriftSeverity.NONE,
                drift_score=0.0,
                details={'message': 'Not enough data for concept drift detection'},
                timestamp=datetime.now().isoformat(),
                recommendations=[]
            )

        # Split into old and new windows
        old_window = self.prediction_history[:self.window_size]
        new_window = self.prediction_history[-self.window_size:]

        # Compare prediction confidence distributions
        old_probs = [p['probability'] for p in old_window]
        new_probs = [p['probability'] for p in new_window]

        ks_stat, p_value = stats.ks_2samp(old_probs, new_probs)

        # Compare error rates if actual labels available
        old_errors = [1 for p in old_window if p['actual'] is not None and p['prediction'] != p['actual']]
        new_errors = [1 for p in new_window if p['actual'] is not None and p['prediction'] != p['actual']]

        old_error_rate = len(old_errors) / len([p for p in old_window if p['actual'] is not None]) if any(p['actual'] is not None for p in old_window) else 0
        new_error_rate = len(new_errors) / len([p for p in new_window if p['actual'] is not None]) if any(p['actual'] is not None for p in new_window) else 0

        error_rate_change = new_error_rate - old_error_rate

        # Determine severity
        if ks_stat < 0.1 and error_rate_change < 0.05:
            severity = DriftSeverity.NONE
        elif ks_stat < 0.15 and error_rate_change < 0.1:
            severity = DriftSeverity.LOW
        elif ks_stat < 0.2 and error_rate_change < 0.15:
            severity = DriftSeverity.MEDIUM
        elif ks_stat < 0.3:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        drift_score = min(1.0, (ks_stat + abs(error_rate_change)) / 0.5)

        recommendations = []
        if severity in [DriftSeverity.MEDIUM, DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
            recommendations.append("Concept drift detected - model predictions are changing")
            recommendations.append("Consider retraining with recent labeled data")

        return DriftResult(
            drift_detected=severity != DriftSeverity.NONE,
            severity=severity,
            drift_score=drift_score,
            details={
                'ks_statistic': ks_stat,
                'p_value': p_value,
                'old_error_rate': old_error_rate,
                'new_error_rate': new_error_rate,
                'error_rate_change': error_rate_change,
                'window_size': self.window_size
            },
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )


class DriftMonitor:
    """Unified drift monitoring combining all drift detection methods"""

    def __init__(
        self,
        reference_data: np.ndarray,
        baseline_metrics: Dict[str, float],
        alert_callback=None
    ):
        """
        Initialize unified drift monitor

        Args:
            reference_data: Reference data for data drift detection
            baseline_metrics: Baseline model metrics
            alert_callback: Function to call when drift is detected
        """
        self.data_drift_detector = DataDriftDetector(reference_data)
        self.performance_drift_detector = ModelPerformanceDriftDetector(baseline_metrics)
        self.concept_drift_detector = ConceptDriftDetector()
        self.alert_callback = alert_callback

    def check_all_drift(
        self,
        current_data: Optional[np.ndarray] = None,
        current_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, DriftResult]:
        """
        Run all drift detection methods

        Returns:
            Dictionary with results from each drift detector
        """
        results = {}

        if current_data is not None:
            results['data_drift'] = self.data_drift_detector.detect_drift(current_data)

        if current_metrics is not None:
            results['performance_drift'] = self.performance_drift_detector.detect_performance_drift(current_metrics)

        results['concept_drift'] = self.concept_drift_detector.detect_concept_drift()

        # Alert if any critical drift detected
        for drift_type, result in results.items():
            if result.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
                if self.alert_callback:
                    self.alert_callback(drift_type, result)
                logger.warning(f"{drift_type.upper()}: {result.severity.value} drift detected!")

        return results
