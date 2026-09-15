"""
SnapShield NPU: Enterprise Cyber-Sentinel Heads-Up Display (HUD).

Renders a high-frame-rate, broadcast-grade security HUD over the camera feed:
- Face bounding brackets with sub-dermal perfusion ROI targeting.
- Real-time rolling cardiac blood-volume pulse (BVP) waveform.
- Biometric liveness gauge and threat probability status.
- Qualcomm Hexagon NPU hardware telemetry (TOPS, latency, power).
"""

from typing import List, Optional, Tuple
import cv2
import numpy as np

from snapshield.core.fusion_sentinel import SentinelEvaluation, ThreatLevel
from snapshield.core.qnn_provider import HardwareTelemetry
from snapshield.core.rppg_engine import RPPGMetrics


class SentinelHUD:
    """
    High-Performance HUD Renderer for Qualcomm Snapdragon & HP OmniBook PCs.
    Renders telemetry directly onto the frame buffer with minimal CPU overhead.
    """

    # Color definitions (BGR)
    COLOR_BG_DARK = (18, 20, 24)
    COLOR_CYAN_ACCENT = (235, 185, 30)       # Qualcomm Teal/Cyan
    COLOR_GREEN_SAFE = (80, 220, 100)       # Verified Authentic
    COLOR_AMBER_WARN = (40, 180, 255)       # Warning / Suspicious
    COLOR_RED_ALERT = (50, 50, 240)         # Deepfake Attack
    COLOR_TEXT_WHITE = (245, 245, 250)
    COLOR_TEXT_DIM = (140, 145, 155)

    def __init__(self, width: int = 1280, height: int = 720) -> None:
        self.canvas_w = width
        self.canvas_h = height
        self.pulse_history: List[float] = [0.0] * 120

    def render_hud(
        self,
        raw_frame: np.ndarray,
        face_box: Optional[Tuple[int, int, int, int]],
        rppg_metrics: Optional[RPPGMetrics],
        evaluation: SentinelEvaluation,
        telemetry: HardwareTelemetry,
        is_attack_injected: bool = False,
        source_mode: str = "Live Camera",
    ) -> np.ndarray:
        """
        Compose full security dashboard canvas with video feed,
        biometric graphs, and hardware telemetry sidebar.
        """
        # Create full 1280x720 canvas
        canvas = np.full((self.canvas_h, self.canvas_w, 3), self.COLOR_BG_DARK, dtype=np.uint8)

        # Scale and insert video feed into primary viewport (900x675)
        vw, vh = 900, 675
        feed_resized = cv2.resize(raw_frame, (vw, vh))

        # Determine theme color based on threat level
        if evaluation.threat_level == ThreatLevel.CRITICAL_SYNTHETIC_ATTACK:
            theme_color = self.COLOR_RED_ALERT
            status_text = "CRITICAL: SYNTHETIC DEEPFAKE ATTACK DETECTED"
        elif evaluation.threat_level == ThreatLevel.SUSPICIOUS_ANOMALY:
            theme_color = self.COLOR_AMBER_WARN
            status_text = "WARNING: PHYSIOLOGICAL COHERENCE DEGRADED"
        elif evaluation.threat_level == ThreatLevel.VERIFIED_AUTHENTIC:
            theme_color = self.COLOR_GREEN_SAFE
            status_text = "SECURED: LIVING BIOMETRIC LIVENESS VERIFIED"
        else:
            theme_color = self.COLOR_CYAN_ACCENT
            status_text = "INITIALIZING BIOMETRIC SENSOR BUFFER..."

        # Draw Face Tracking Reticle on the video feed
        if face_box is not None:
            # Map face_box coordinates from raw frame to viewport dimensions
            scale_x = vw / raw_frame.shape[1]
            scale_y = vh / raw_frame.shape[0]
            fx, fy, fw, fh = (
                int(face_box[0] * scale_x),
                int(face_box[1] * scale_y),
                int(face_box[2] * scale_x),
                int(face_box[3] * scale_y),
            )
            self._draw_reticle(feed_resized, fx, fy, fw, fh, theme_color)

        # Place video feed onto canvas (with 20px padding)
        canvas[25 : 25 + vh, 25 : 25 + vw] = feed_resized
        # Outer viewport border
        cv2.rectangle(canvas, (24, 24), (25 + vw, 25 + vh), theme_color, 2)

        # Top Header Bar across Canvas
        self._render_header(canvas, status_text, theme_color, source_mode, is_attack_injected)

        # Right Telemetry Sidebar
        self._render_sidebar(canvas, 945, 25, 310, vh, rppg_metrics, evaluation, telemetry)

        return canvas

    def _draw_reticle(
        self,
        img: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Draw high-tech corner brackets and ROI labels."""
        line_len = min(24, w // 4)
        thickness = 2

        # Top-Left
        cv2.line(img, (x, y), (x + line_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + line_len), color, thickness)
        # Top-Right
        cv2.line(img, (x + w, y), (x + w - line_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + line_len), color, thickness)
        # Bottom-Left
        cv2.line(img, (x, y + h), (x + line_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - line_len), color, thickness)
        # Bottom-Right
        cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, thickness)

        # Sub-dermal arteriole scan box (forehead)
        fh_y = y + int(0.12 * h)
        fh_h = int(0.20 * h)
        fh_x = x + int(0.25 * w)
        fh_w = int(0.50 * w)
        cv2.rectangle(img, (fh_x, fh_y), (fh_x + fh_w, fh_y + fh_h), (color[0], color[1], color[2]), 1)
        cv2.putText(
            img,
            "HEMODYNAMIC ROI",
            (fh_x, fh_y - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            color,
            1,
            cv2.LINE_AA,
        )

    def _render_header(
        self,
        canvas: np.ndarray,
        status_text: str,
        status_color: Tuple[int, int, int],
        source_mode: str,
        is_attack_injected: bool,
    ) -> None:
        """Render top banner with system title and security status."""
        cv2.putText(
            canvas,
            "SNAPSHIELD NPU",
            (25, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            self.COLOR_CYAN_ACCENT,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            "|  Air-Gapped Real-Time Deepfake & Voice Clone Interceptor",
            (180, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            self.COLOR_TEXT_DIM,
            1,
            cv2.LINE_AA,
        )

        # Status badge
        cv2.putText(
            canvas,
            status_text,
            (450, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            status_color,
            2,
            cv2.LINE_AA,
        )

        # Attack simulation indicator
        if is_attack_injected:
            cv2.putText(
                canvas,
                "[ ATTACK INJECTION ACTIVE ]",
                (1010, 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                self.COLOR_RED_ALERT,
                2,
                cv2.LINE_AA,
            )
        else:
            cv2.putText(
                canvas,
                f"Source: {source_mode}",
                (1080, 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                self.COLOR_TEXT_DIM,
                1,
                cv2.LINE_AA,
            )

    def _render_sidebar(
        self,
        canvas: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        rppg_metrics: Optional[RPPGMetrics],
        evaluation: SentinelEvaluation,
        telemetry: HardwareTelemetry,
    ) -> None:
        """Render metrics, real-time waveform graph, and hardware stats."""
        # Panel background
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (26, 30, 36), -1)
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (45, 52, 64), 1)

        cur_y = y + 25

        # Section 1: Biometric Liveness Verification
        cv2.putText(canvas, "BIOMETRIC LIVENESS", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, self.COLOR_CYAN_ACCENT, 2, cv2.LINE_AA)
        cur_y += 28

        # Pulse Waveform Visualization
        if rppg_metrics and len(rppg_metrics.bvp_signal) > 0:
            latest_val = float(rppg_metrics.bvp_signal[-1])
        else:
            latest_val = 0.0

        self.pulse_history.append(latest_val)
        if len(self.pulse_history) > 100:
            self.pulse_history.pop(0)

        # Draw waveform box
        gw, gh = w - 30, 55
        gx, gy = x + 15, cur_y
        cv2.rectangle(canvas, (gx, gy), (gx + gw, gy + gh), (15, 18, 22), -1)
        cv2.rectangle(canvas, (gx, gy), (gx + gw, gy + gh), (50, 60, 75), 1)

        # Plot waveform points
        pts = []
        for i, val in enumerate(self.pulse_history):
            px = int(gx + (i / max(len(self.pulse_history) - 1, 1)) * gw)
            # val is [-1.0, 1.0]
            py = int(gy + (gh // 2) - (val * (gh // 2 - 4)))
            pts.append((px, py))

        if len(pts) > 1:
            wave_color = self.COLOR_GREEN_SAFE if evaluation.biological_liveness_score > 0.6 else self.COLOR_RED_ALERT
            for i in range(1, len(pts)):
                cv2.line(canvas, pts[i - 1], pts[i], wave_color, 2)

        cv2.putText(canvas, "Capillary Pulse Waveform (POS/CHROM)", (gx + 6, gy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.32, self.COLOR_TEXT_DIM, 1, cv2.LINE_AA)
        cur_y += gh + 22

        # Telemetry stats
        bpm_str = f"{evaluation.heart_rate_bpm:.0f} BPM" if evaluation.heart_rate_bpm > 0 else "-- BPM"
        snr_val = rppg_metrics.snr_db if rppg_metrics else 0.0
        snr_str = f"{snr_val:+.1f} dB"

        self._draw_key_value(canvas, x + 15, cur_y, "Cardiac Pulse:", bpm_str, self.COLOR_TEXT_WHITE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Hemodynamic SNR:", snr_str, self.COLOR_GREEN_SAFE if snr_val > 2.0 else self.COLOR_AMBER_WARN)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Liveness Index:", f"{evaluation.biological_liveness_score * 100:.1f}%", self.COLOR_TEXT_WHITE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Voice Authenticity:", f"{evaluation.voice_authenticity_score * 100:.1f}%", self.COLOR_TEXT_WHITE)
        cur_y += 35

        # Section 2: Executive Wellness & Fatigue Sentinel
        cv2.line(canvas, (x + 15, cur_y), (x + w - 15, cur_y), (45, 52, 64), 1)
        cur_y += 20
        cv2.putText(canvas, "COGNITIVE SENTINEL", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, self.COLOR_CYAN_ACCENT, 2, cv2.LINE_AA)
        cur_y += 28

        self._draw_key_value(canvas, x + 15, cur_y, "Heart Rate Variability:", f"{evaluation.hrv_sdnn_ms:.1f} ms", self.COLOR_TEXT_WHITE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Mental State:", evaluation.cognitive_fatigue_level, self.COLOR_TEXT_WHITE)
        cur_y += 35

        # Section 3: Qualcomm Snapdragon NPU Telemetry
        cv2.line(canvas, (x + 15, cur_y), (x + w - 15, cur_y), (45, 52, 64), 1)
        cur_y += 20
        cv2.putText(canvas, "QUALCOMM HEXAGON NPU", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, self.COLOR_CYAN_ACCENT, 2, cv2.LINE_AA)
        cur_y += 28

        self._draw_key_value(canvas, x + 15, cur_y, "Compute Engine:", "Hexagon HTP / NPU", self.COLOR_TEXT_WHITE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "AI Acceleration:", f"{telemetry.rated_tops:.1f} TOPS", self.COLOR_GREEN_SAFE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Inference Latency:", f"{telemetry.average_latency_ms:.1f} ms", self.COLOR_GREEN_SAFE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Power Budget:", f"{telemetry.power_budget_watts:.1f} W (Silent)", self.COLOR_TEXT_WHITE)
        cur_y += 24
        self._draw_key_value(canvas, x + 15, cur_y, "Air-Gapped Privacy:", "100% On-Device", self.COLOR_GREEN_SAFE)
        cur_y += 38

        # Bottom Instructions
        cv2.line(canvas, (x + 15, cur_y), (x + w - 15, cur_y), (45, 52, 64), 1)
        cur_y += 24
        cv2.putText(canvas, "CONTROLS:", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, self.COLOR_CYAN_ACCENT, 1, cv2.LINE_AA)
        cur_y += 20
        cv2.putText(canvas, "[T] Toggle Deepfake Attack Injection", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.34, self.COLOR_TEXT_DIM, 1, cv2.LINE_AA)
        cur_y += 18
        cv2.putText(canvas, "[M] Toggle Camera / Synthetic Feed", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.34, self.COLOR_TEXT_DIM, 1, cv2.LINE_AA)
        cur_y += 18
        cv2.putText(canvas, "[Q] Quit Sentinel Application", (x + 15, cur_y), cv2.FONT_HERSHEY_SIMPLEX, 0.34, self.COLOR_TEXT_DIM, 1, cv2.LINE_AA)

    def _draw_key_value(
        self,
        canvas: np.ndarray,
        x: int,
        y: int,
        key: str,
        value: str,
        val_color: Tuple[int, int, int],
    ) -> None:
        """Helper to draw clean aligned key-value telemetry pairs."""
        cv2.putText(canvas, key, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, self.COLOR_TEXT_DIM, 1, cv2.LINE_AA)
        cv2.putText(canvas, value, (x + 165, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, val_color, 1, cv2.LINE_AA)
