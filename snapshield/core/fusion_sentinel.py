"""
SnapShield NPU: Multi-Modal Fusion Sentinel.

Combines physiological rPPG pulse verification and neural acoustic analysis
into a unified zero-trust threat score, while computing executive cognitive
health telemetry (BPM, HRV, fatigue index).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import numpy as np

from snapshield.core.audio_detector import AudioAuthenticityMetrics
from snapshield.core.rppg_engine import RPPGMetrics


class ThreatLevel(Enum):
    VERIFIED_AUTHENTIC = "AUTHENTIC_BIOMETRIC"
    EVALUATING = "EVALUATING_BUFFER"
    SUSPICIOUS_ANOMALY = "SUSPICIOUS_ANOMALY"
    CRITICAL_SYNTHETIC_ATTACK = "CRITICAL_SYNTHETIC_ATTACK"


@dataclass
class SentinelEvaluation:
    """Comprehensive verdict and telemetry for the active session."""
    threat_level: ThreatLevel
    threat_probability: float  # [0.0, 1.0] (0.0 = completely safe, 1.0 = deepfake attack)
    biological_liveness_score: float  # [0.0, 1.0]
    voice_authenticity_score: float  # [0.0, 1.0]
    heart_rate_bpm: float
    hrv_sdnn_ms: float
    cognitive_fatigue_level: str  # "Optimal", "Moderate Focus", "Elevated Strain"
    incident_alert_message: str
    is_attack_active: bool


class FusionSentinel:
    """
    Zero-Trust Multi-Modal Decision Engine.
    Fuses vision rPPG hemodynamics with acoustic spectral features.
    """

    def __init__(
        self,
        attack_threshold: float = 0.65,
        suspicious_threshold: float = 0.40,
    ) -> None:
        self.attack_threshold = attack_threshold
        self.suspicious_threshold = suspicious_threshold
        self.ibi_history: List[float] = []

    def evaluate(
        self,
        rppg_metrics: Optional[RPPGMetrics],
        audio_metrics: Optional[AudioAuthenticityMetrics],
        face_detected: bool,
    ) -> SentinelEvaluation:
        """Compute composite threat score and cognitive metrics."""
        if not face_detected:
            return SentinelEvaluation(
                threat_level=ThreatLevel.EVALUATING,
                threat_probability=0.0,
                biological_liveness_score=0.0,
                voice_authenticity_score=audio_metrics.voice_authenticity_score if audio_metrics else 1.0,
                heart_rate_bpm=0.0,
                hrv_sdnn_ms=0.0,
                cognitive_fatigue_level="Standby (No Face)",
                incident_alert_message="Awaiting Participant Video Feed",
                is_attack_active=False,
            )

        if rppg_metrics is None:
            return SentinelEvaluation(
                threat_level=ThreatLevel.EVALUATING,
                threat_probability=0.15,
                biological_liveness_score=0.5,
                voice_authenticity_score=audio_metrics.voice_authenticity_score if audio_metrics else 1.0,
                heart_rate_bpm=0.0,
                hrv_sdnn_ms=0.0,
                cognitive_fatigue_level="Calibrating Sensor Buffer...",
                incident_alert_message="Acquiring Sub-Dermal Hemodynamic Signal",
                is_attack_active=False,
            )

        # 1. Biological Liveness Scoring
        liveness_score = rppg_metrics.pulse_confidence
        voice_score = audio_metrics.voice_authenticity_score if audio_metrics else 1.0

        # Synthetic Video Probability: Deepfakes fail to maintain biological pulse SNR
        p_video_fake = 1.0 - liveness_score

        # Synthetic Audio Probability
        p_audio_fake = 1.0 - voice_score

        # Multi-modal fusion probability
        # Video rPPG has primary weight for visual meetings; audio adds corroboration
        threat_prob = (0.70 * p_video_fake) + (0.30 * p_audio_fake)

        # If audio vocoder is explicitly confirmed, elevate threat
        if audio_metrics and audio_metrics.vocoder_artifact_detected:
            threat_prob = max(threat_prob, 0.85)

        # If video rPPG has zero pulse and negative SNR, elevate threat
        if not rppg_metrics.is_biologically_authentic and rppg_metrics.snr_db < 0.0:
            threat_prob = max(threat_prob, 0.90)

        # 2. Cognitive Health & HRV Metrics
        bpm = rppg_metrics.heart_rate_bpm
        if rppg_metrics.inter_beat_intervals_ms:
            self.ibi_history.extend(rppg_metrics.inter_beat_intervals_ms)
            if len(self.ibi_history) > 60:
                self.ibi_history = self.ibi_history[-60:]

        hrv_sdnn = float(np.std(self.ibi_history)) if len(self.ibi_history) >= 5 else 42.0

        # Fatigue / Stress classification based on resting BPM and HRV
        if hrv_sdnn > 45.0 and bpm <= 85.0:
            fatigue = "Optimal Resilience"
        elif 30.0 <= hrv_sdnn <= 45.0:
            fatigue = "Normal Cognitive Focus"
        else:
            fatigue = "Elevated Fatigue / High Stress"

        # 3. Verdict Assignment
        if threat_prob >= self.attack_threshold:
            level = ThreatLevel.CRITICAL_SYNTHETIC_ATTACK
            is_attack = True
            msg = "SYNTHETIC DEEPFAKE ATTACK DETECTED: Capillary Hemodynamics Absent"
            if audio_metrics and audio_metrics.vocoder_artifact_detected:
                msg += " + Neural Voice Clone Active"
        elif threat_prob >= self.suspicious_threshold:
            level = ThreatLevel.SUSPICIOUS_ANOMALY
            is_attack = False
            msg = "PHYSIOLOGICAL ANOMALY: Degraded Signal Coherence / Motion Artifact"
        else:
            level = ThreatLevel.VERIFIED_AUTHENTIC
            is_attack = False
            msg = f"VERIFIED LIVING HUMAN: Cardiac Pulse {bpm:.0f} BPM (SNR {rppg_metrics.snr_db:+.1f} dB)"

        return SentinelEvaluation(
            threat_level=level,
            threat_probability=round(float(threat_prob), 3),
            biological_liveness_score=round(float(liveness_score), 3),
            voice_authenticity_score=round(float(voice_score), 3),
            heart_rate_bpm=bpm,
            hrv_sdnn_ms=round(hrv_sdnn, 1),
            cognitive_fatigue_level=fatigue,
            incident_alert_message=msg,
            is_attack_active=is_attack,
        )
