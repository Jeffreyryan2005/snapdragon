"""
SnapShield NPU: Real-Time Edge Deepfake & Biometric Synthetic Attack Interceptor.
Core package.
"""

from snapshield.core.rppg_engine import RPPGEngine, RPPGMetrics
from snapshield.core.audio_detector import AudioSyntheticDetector, AudioAuthenticityMetrics
from snapshield.core.face_mesh_tracker import FaceMeshTracker, FaceTrackingResult
from snapshield.core.qnn_provider import QNNInferenceManager, HardwareTelemetry
from snapshield.core.fusion_sentinel import FusionSentinel, SentinelEvaluation, ThreatLevel

__all__ = [
    "RPPGEngine",
    "RPPGMetrics",
    "AudioSyntheticDetector",
    "AudioAuthenticityMetrics",
    "FaceMeshTracker",
    "FaceTrackingResult",
    "QNNInferenceManager",
    "HardwareTelemetry",
    "FusionSentinel",
    "SentinelEvaluation",
    "ThreatLevel",
]
