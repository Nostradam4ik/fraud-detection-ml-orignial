"""
A/B Testing Framework for ML Models
Compare model performance in production with controlled traffic splitting

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import hashlib
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an A/B experiment"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ModelVariant:
    """A model variant in an A/B test"""
    name: str
    model_path: str
    traffic_percentage: float
    is_control: bool = False
    predictions: int = 0
    correct_predictions: int = 0
    fraud_detected: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_response_time_ms: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExperimentResult:
    """Result of an A/B experiment"""
    winner: Optional[str]
    confidence: float
    metrics_comparison: Dict[str, Dict]
    statistical_significance: bool
    recommendation: str


class ABTestExperiment:
    """Represents an A/B test experiment for ML models"""

    def __init__(
        self,
        experiment_id: str,
        name: str,
        description: str = "",
        variants: List[ModelVariant] = None,
        min_samples: int = 1000,
        confidence_level: float = 0.95
    ):
        """
        Initialize an A/B test experiment

        Args:
            experiment_id: Unique identifier for the experiment
            name: Human-readable experiment name
            description: Experiment description
            variants: List of model variants to test
            min_samples: Minimum samples per variant before analysis
            confidence_level: Required confidence level for statistical significance
        """
        self.experiment_id = experiment_id
        self.name = name
        self.description = description
        self.variants = variants or []
        self.min_samples = min_samples
        self.confidence_level = confidence_level

        self.status = ExperimentStatus.DRAFT
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        self._validate_traffic_split()

    def _validate_traffic_split(self):
        """Validate that traffic percentages sum to 100%"""
        if self.variants:
            total = sum(v.traffic_percentage for v in self.variants)
            if abs(total - 100.0) > 0.01:
                raise ValueError(f"Traffic percentages must sum to 100%, got {total}")

    def add_variant(self, variant: ModelVariant):
        """Add a variant to the experiment"""
        self.variants.append(variant)
        self._validate_traffic_split()

    def start(self):
        """Start the experiment"""
        if not self.variants:
            raise ValueError("Cannot start experiment without variants")
        if not any(v.is_control for v in self.variants):
            logger.warning("No control variant specified")

        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now()
        logger.info(f"Experiment '{self.name}' started")

    def pause(self):
        """Pause the experiment"""
        self.status = ExperimentStatus.PAUSED
        logger.info(f"Experiment '{self.name}' paused")

    def resume(self):
        """Resume a paused experiment"""
        if self.status != ExperimentStatus.PAUSED:
            raise ValueError("Can only resume paused experiments")
        self.status = ExperimentStatus.RUNNING
        logger.info(f"Experiment '{self.name}' resumed")

    def complete(self, result: ExperimentResult):
        """Complete the experiment"""
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        logger.info(f"Experiment '{self.name}' completed. Winner: {result.winner}")

    def get_variant_for_user(self, user_id: str) -> ModelVariant:
        """
        Get the assigned variant for a user (deterministic)

        Uses consistent hashing to ensure users always get the same variant
        """
        if self.status != ExperimentStatus.RUNNING:
            # Return control variant if experiment not running
            control = next((v for v in self.variants if v.is_control), self.variants[0])
            return control

        # Consistent hashing based on user_id and experiment_id
        hash_input = f"{user_id}:{self.experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        # Assign variant based on traffic percentages
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                return variant

        return self.variants[-1]

    def record_prediction(
        self,
        variant_name: str,
        is_fraud_predicted: bool,
        is_fraud_actual: Optional[bool] = None,
        response_time_ms: float = 0.0
    ):
        """Record a prediction result for a variant"""
        variant = next((v for v in self.variants if v.name == variant_name), None)
        if not variant:
            logger.warning(f"Unknown variant: {variant_name}")
            return

        variant.predictions += 1
        variant.total_response_time_ms += response_time_ms

        if is_fraud_predicted:
            variant.fraud_detected += 1

        if is_fraud_actual is not None:
            if is_fraud_predicted == is_fraud_actual:
                variant.correct_predictions += 1
            elif is_fraud_predicted and not is_fraud_actual:
                variant.false_positives += 1
            elif not is_fraud_predicted and is_fraud_actual:
                variant.false_negatives += 1

    def get_variant_metrics(self, variant: ModelVariant) -> Dict[str, float]:
        """Calculate metrics for a variant"""
        if variant.predictions == 0:
            return {}

        metrics = {
            'predictions': variant.predictions,
            'fraud_detected': variant.fraud_detected,
            'fraud_rate': variant.fraud_detected / variant.predictions,
            'avg_response_time_ms': variant.total_response_time_ms / variant.predictions
        }

        # Add accuracy metrics if we have ground truth
        total_labeled = variant.correct_predictions + variant.false_positives + variant.false_negatives
        if total_labeled > 0:
            metrics['accuracy'] = variant.correct_predictions / total_labeled

            # Precision and recall
            if variant.fraud_detected > 0:
                metrics['precision'] = (variant.fraud_detected - variant.false_positives) / variant.fraud_detected
            if (variant.fraud_detected - variant.false_positives + variant.false_negatives) > 0:
                tp = variant.fraud_detected - variant.false_positives
                metrics['recall'] = tp / (tp + variant.false_negatives)

            if metrics.get('precision') and metrics.get('recall'):
                p, r = metrics['precision'], metrics['recall']
                metrics['f1_score'] = 2 * (p * r) / (p + r) if (p + r) > 0 else 0

        return metrics

    def analyze_results(self) -> ExperimentResult:
        """Analyze experiment results and determine winner"""
        logger.info(f"Analyzing results for experiment '{self.name}'")

        # Check minimum samples
        for variant in self.variants:
            if variant.predictions < self.min_samples:
                logger.warning(f"Variant {variant.name} has only {variant.predictions} samples")

        # Get metrics for all variants
        metrics_by_variant = {}
        for variant in self.variants:
            metrics_by_variant[variant.name] = self.get_variant_metrics(variant)

        # Find control variant
        control = next((v for v in self.variants if v.is_control), self.variants[0])
        control_metrics = metrics_by_variant[control.name]

        # Compare each treatment to control
        comparisons = {}
        best_variant = control
        best_improvement = 0

        for variant in self.variants:
            if variant.name == control.name:
                continue

            variant_metrics = metrics_by_variant[variant.name]

            # Statistical test on fraud detection rates
            control_fraud_rate = control_metrics.get('fraud_rate', 0)
            variant_fraud_rate = variant_metrics.get('fraud_rate', 0)

            # Two-proportion z-test
            n1, n2 = control.predictions, variant.predictions
            p1, p2 = control_fraud_rate, variant_fraud_rate

            if n1 > 0 and n2 > 0:
                pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)
                se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
                z_stat = (p2 - p1) / se if se > 0 else 0
                p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

                is_significant = p_value < (1 - self.confidence_level)
            else:
                z_stat = 0
                p_value = 1.0
                is_significant = False

            comparisons[variant.name] = {
                'control_metrics': control_metrics,
                'variant_metrics': variant_metrics,
                'z_statistic': z_stat,
                'p_value': p_value,
                'is_significant': is_significant,
                'improvement': {
                    'fraud_rate': variant_fraud_rate - control_fraud_rate,
                    'response_time': (
                        variant_metrics.get('avg_response_time_ms', 0) -
                        control_metrics.get('avg_response_time_ms', 0)
                    )
                }
            }

            # Determine if this variant is better
            # Prioritize: accuracy > response time
            if variant_metrics.get('accuracy', 0) > control_metrics.get('accuracy', 0):
                improvement = variant_metrics.get('accuracy', 0) - control_metrics.get('accuracy', 0)
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_variant = variant

        # Generate recommendation
        if best_variant.name != control.name and best_improvement > 0.01:
            recommendation = f"Deploy variant '{best_variant.name}' as the new model"
            winner = best_variant.name
        else:
            recommendation = f"Keep current model '{control.name}'"
            winner = control.name

        # Calculate overall confidence
        max_confidence = max(
            (1 - comp['p_value']) for comp in comparisons.values()
        ) if comparisons else 0

        result = ExperimentResult(
            winner=winner,
            confidence=max_confidence,
            metrics_comparison=comparisons,
            statistical_significance=any(c['is_significant'] for c in comparisons.values()),
            recommendation=recommendation
        )

        return result

    def to_dict(self) -> Dict:
        """Convert experiment to dictionary"""
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'variants': [asdict(v) for v in self.variants],
            'min_samples': self.min_samples,
            'confidence_level': self.confidence_level,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class ABTestingService:
    """Service for managing A/B testing experiments"""

    def __init__(self):
        self.experiments: Dict[str, ABTestExperiment] = {}
        self._model_loaders: Dict[str, callable] = {}

    def register_model_loader(self, variant_name: str, loader: callable):
        """Register a model loader function for a variant"""
        self._model_loaders[variant_name] = loader

    def create_experiment(
        self,
        name: str,
        description: str = "",
        control_model_path: str = "",
        treatment_model_paths: List[str] = None,
        traffic_split: Optional[List[float]] = None,
        min_samples: int = 1000
    ) -> ABTestExperiment:
        """Create a new A/B testing experiment"""
        import uuid
        experiment_id = str(uuid.uuid4())[:8]

        # Create variants
        variants = []
        treatment_model_paths = treatment_model_paths or []
        all_models = [control_model_path] + treatment_model_paths

        if traffic_split is None:
            # Equal split
            traffic_per_variant = 100 / len(all_models)
            traffic_split = [traffic_per_variant] * len(all_models)

        for i, model_path in enumerate(all_models):
            variant = ModelVariant(
                name=f"variant_{chr(65 + i)}",  # A, B, C, ...
                model_path=model_path,
                traffic_percentage=traffic_split[i],
                is_control=(i == 0)
            )
            variants.append(variant)

        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            min_samples=min_samples
        )

        self.experiments[experiment_id] = experiment
        logger.info(f"Created experiment '{name}' with ID {experiment_id}")

        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[ABTestExperiment]:
        """Get an experiment by ID"""
        return self.experiments.get(experiment_id)

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None
    ) -> List[ABTestExperiment]:
        """List all experiments, optionally filtered by status"""
        if status:
            return [e for e in self.experiments.values() if e.status == status]
        return list(self.experiments.values())

    def get_active_experiments(self) -> List[ABTestExperiment]:
        """Get all running experiments"""
        return self.list_experiments(ExperimentStatus.RUNNING)

    def predict_with_ab_test(
        self,
        experiment_id: str,
        user_id: str,
        features: np.ndarray
    ) -> Tuple[str, Any]:
        """
        Make a prediction using A/B test assignment

        Returns:
            Tuple of (variant_name, prediction_result)
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Experiment {experiment_id} not found or not running")

        # Get assigned variant for user
        variant = experiment.get_variant_for_user(user_id)

        # Load and use the model for this variant
        if variant.name in self._model_loaders:
            model = self._model_loaders[variant.name]()
            prediction = model.predict(features)
        else:
            # Fallback - return variant info
            prediction = {'variant': variant.name, 'model_path': variant.model_path}

        return variant.name, prediction

    def complete_experiment(self, experiment_id: str) -> ExperimentResult:
        """Analyze and complete an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        result = experiment.analyze_results()
        experiment.complete(result)

        return result

    def export_experiment_report(self, experiment_id: str) -> Dict:
        """Export detailed experiment report"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        report = experiment.to_dict()

        # Add metrics for each variant
        report['variant_metrics'] = {}
        for variant in experiment.variants:
            report['variant_metrics'][variant.name] = experiment.get_variant_metrics(variant)

        # Add analysis if completed
        if experiment.status == ExperimentStatus.COMPLETED:
            result = experiment.analyze_results()
            report['analysis'] = {
                'winner': result.winner,
                'confidence': result.confidence,
                'statistical_significance': result.statistical_significance,
                'recommendation': result.recommendation,
                'metrics_comparison': result.metrics_comparison
            }

        return report


# Global A/B testing service instance
ab_testing_service = ABTestingService()
