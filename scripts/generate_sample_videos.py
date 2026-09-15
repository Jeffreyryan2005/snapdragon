"""
SnapShield NPU: Sample Video Clip Generator for Evaluation.

Generates pre-recorded test video clips in data/samples/:
1. authentic_call_sample.mp4 (Authentic living human face with biological capillary perfusion at 72 BPM)
2. deepfake_attack_sample.mp4 (Synthetic deepfake attack feed with absent hemodynamics)
"""

import os
import sys
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from snapshield.utils.synthetic_stream import SyntheticStreamGenerator


def generate_sample_videos(output_dir: str = "data/samples") -> None:
    os.makedirs(output_dir, exist_ok=True)
    fps = 30.0
    duration_sec = 4.0
    total_frames = int(fps * duration_sec)
    width, height = 640, 480

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    # 1. Generate Authentic Video Clip
    auth_path = os.path.join(output_dir, "authentic_call_sample.mp4")
    out_auth = cv2.VideoWriter(auth_path, fourcc, fps, (width, height))
    stream_auth = SyntheticStreamGenerator(fps=fps)
    stream_auth.target_heart_rate_bpm = 72.0

    print(f"[+] Rendering authentic sample video ({total_frames} frames)...")
    for _ in range(total_frames):
        frame = stream_auth.generate_synthetic_frame(is_deepfake=False, width=width, height=height)
        out_auth.write(frame)
    out_auth.release()
    print(f"[OK] Generated: {auth_path}")

    # 2. Generate Deepfake Attack Video Clip
    fake_path = os.path.join(output_dir, "deepfake_attack_sample.mp4")
    out_fake = cv2.VideoWriter(fake_path, fourcc, fps, (width, height))
    stream_fake = SyntheticStreamGenerator(fps=fps)

    print(f"[+] Rendering deepfake attack sample video ({total_frames} frames)...")
    for _ in range(total_frames):
        frame = stream_fake.generate_synthetic_frame(is_deepfake=True, width=width, height=height)
        out_fake.write(frame)
    out_fake.release()
    print(f"[OK] Generated: {fake_path}")


if __name__ == "__main__":
    generate_sample_videos("data/samples")
