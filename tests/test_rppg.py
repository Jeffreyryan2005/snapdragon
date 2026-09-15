"""
SnapShield NPU: Unit Tests for rPPG Biometric Pulse Extraction Engine.
"""

import unittest
import numpy as np
from snapshield.core.rppg_engine import RPPGEngine
from snapshield.utils.synthetic_stream import SyntheticStreamGenerator


class TestRPPGEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.rppg = RPPGEngine(sampling_rate_fps=30.0, buffer_window_seconds=5.0)
        self.stream_gen = SyntheticStreamGenerator(fps=30.0)

    def test_authentic_pulse_detection(self) -> None:
        """Verify that genuine periodic capillary oscillations yield a valid heart rate and high SNR."""
        self.stream_gen.target_heart_rate_bpm = 72.0
        metrics = None

        # Feed 120 frames (4 seconds) of authentic physiological frames
        for _ in range(120):
            frame = self.stream_gen.generate_synthetic_frame(is_deepfake=False)
            # Forehead/cheek skin crop inside facial oval
            roi = frame[150:190, 290:350]
            metrics = self.rppg.update_frame_roi(roi)

        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.snr_db, 1.5)
        self.assertTrue(metrics.is_biologically_authentic)
        # Heart rate should be approximately 72 BPM (+- 8 BPM)
        self.assertAlmostEqual(metrics.heart_rate_bpm, 72.0, delta=8.0)

    def test_deepfake_attack_rejection(self) -> None:
        """Verify that synthetic skin noise or flat color fails liveness verification."""
        self.rppg.reset()
        metrics = None

        # Feed 120 frames of deepfake frames (chaotic noise / absent hemodynamics)
        for _ in range(120):
            frame = self.stream_gen.generate_synthetic_frame(is_deepfake=True)
            roi = frame[150:190, 290:350]
            metrics = self.rppg.update_frame_roi(roi)

        self.assertIsNotNone(metrics)
        # Deepfake should fail biological authenticity
        self.assertFalse(metrics.is_biologically_authentic)
        self.assertLess(metrics.pulse_confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
