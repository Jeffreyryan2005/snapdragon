"""
SnapShield NPU: Unit Tests for Neural Audio Synthetic Detector.
"""

import unittest
import numpy as np
from snapshield.core.audio_detector import AudioSyntheticDetector
from snapshield.utils.synthetic_stream import SyntheticStreamGenerator


class TestAudioDetector(unittest.TestCase):

    def setUp(self) -> None:
        self.detector = AudioSyntheticDetector(sample_rate=16000)
        self.stream_gen = SyntheticStreamGenerator(sample_rate=16000)

    def test_authentic_voice_evaluation(self) -> None:
        """Verify that organic human speech harmonics yield high authenticity score."""
        audio = self.stream_gen.generate_synthetic_audio(is_cloned_voice=False, duration_sec=1.0)
        metrics = self.detector.analyze_audio_buffer(audio)

        self.assertTrue(metrics.is_authentic_voice)
        self.assertFalse(metrics.vocoder_artifact_detected)
        self.assertGreaterEqual(metrics.voice_authenticity_score, 0.60)

    def test_voice_clone_detection(self) -> None:
        """Verify that synthetic vocoder artifacts trigger clone detection."""
        audio = self.stream_gen.generate_synthetic_audio(is_cloned_voice=True, duration_sec=1.0)
        metrics = self.detector.analyze_audio_buffer(audio)

        self.assertFalse(metrics.is_authentic_voice)
        self.assertTrue(metrics.vocoder_artifact_detected)
        self.assertLess(metrics.voice_authenticity_score, 0.60)


if __name__ == "__main__":
    unittest.main()
