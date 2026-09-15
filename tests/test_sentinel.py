"""
SnapShield NPU: Unit Tests for Multi-Modal Fusion Sentinel.
"""

import unittest
from snapshield.core.audio_detector import AudioAuthenticityMetrics
from snapshield.core.fusion_sentinel import FusionSentinel, ThreatLevel
from snapshield.core.rppg_engine import RPPGMetrics
import numpy as np


class TestFusionSentinel(unittest.TestCase):

    def setUp(self) -> None:
        self.sentinel = FusionSentinel()

    def test_verdict_when_authentic(self) -> None:
        rppg = RPPGMetrics(
            heart_rate_bpm=72.0,
            snr_db=4.5,
            pulse_confidence=0.92,
            is_biologically_authentic=True,
            bvp_signal=np.zeros(10),
            psd_frequencies=np.zeros(10),
            psd_power=np.zeros(10),
            inter_beat_intervals_ms=[830.0, 835.0, 828.0],
        )
        audio = AudioAuthenticityMetrics(
            is_authentic_voice=True,
            voice_authenticity_score=0.95,
            spectral_flatness=0.08,
            high_freq_ratio=0.12,
            pitch_jitter_score=0.15,
            vocoder_artifact_detected=False,
            snr_db=18.0,
        )
        evaluation = self.sentinel.evaluate(rppg, audio, face_detected=True)
        self.assertEqual(evaluation.threat_level, ThreatLevel.VERIFIED_AUTHENTIC)
        self.assertFalse(evaluation.is_attack_active)
        self.assertLess(evaluation.threat_probability, 0.3)

    def test_verdict_when_attack(self) -> None:
        rppg = RPPGMetrics(
            heart_rate_bpm=0.0,
            snr_db=-3.2,
            pulse_confidence=0.08,
            is_biologically_authentic=False,
            bvp_signal=np.zeros(10),
            psd_frequencies=np.zeros(10),
            psd_power=np.zeros(10),
            inter_beat_intervals_ms=[],
        )
        audio = AudioAuthenticityMetrics(
            is_authentic_voice=False,
            voice_authenticity_score=0.20,
            spectral_flatness=0.48,
            high_freq_ratio=0.001,
            pitch_jitter_score=0.02,
            vocoder_artifact_detected=True,
            snr_db=12.0,
        )
        evaluation = self.sentinel.evaluate(rppg, audio, face_detected=True)
        self.assertEqual(evaluation.threat_level, ThreatLevel.CRITICAL_SYNTHETIC_ATTACK)
        self.assertTrue(evaluation.is_attack_active)
        self.assertGreaterEqual(evaluation.threat_probability, 0.65)


if __name__ == "__main__":
    unittest.main()
