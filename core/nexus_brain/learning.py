import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DecoupledCalibrationEngine:
    """
    NEXUS Decoupled Confidence Calibration Engine.
    Implements the 4-factor formula (SuccessRate, AgentAgreement, EvidenceQuality, Uncertainty)
    to compute fully grounded, mathematically honest confidence indicators.
    """
    def __init__(
        self,
        weights: List[float] = [0.3, 0.3, 0.2, 0.2]  # Must sum to 1.0
    ):
        self.weights = weights

    def calculate_confidence(
        self,
        success_rate: float,      # Range [0.0 - 1.0]
        agent_agreement: float,   # Range [0.0 - 1.0]
        evidence_quality: float,  # Range [0.0 - 1.0]
        uncertainty: float        # Range [0.0 - 1.0]
    ) -> float:
        """
        Calculates and returns calibrated confidence score in range [0.0 - 100.0]
        Formula: (w1*Success + w2*Agreement + w3*Evidence - w4*Uncertainty)
        """
        val = (
            self.weights[0] * success_rate +
            self.weights[1] * agent_agreement +
            self.weights[2] * evidence_quality -
            self.weights[3] * uncertainty
        )
        scaled = max(0.0, min(1.0, val)) * 100.0
        logger.debug(f"Calibrated Confidence: {scaled:.2f}% (Success={success_rate:.2f}, Uncertainty={uncertainty:.2f})")
        return scaled

class AdaptiveThresholdController:
    def __init__(self, base_threshold: float = 0.85):
        self.current_threshold = base_threshold

    def adapt(self, current_win_rate: float) -> float:
        if current_win_rate > 0.65:
            self.current_threshold = max(0.70, self.current_threshold - 0.02)
        else:
            self.current_threshold = min(0.95, self.current_threshold + 0.02)
        return self.current_threshold
