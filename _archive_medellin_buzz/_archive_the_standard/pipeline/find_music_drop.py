"""
The Standard — Step 6: Find the music drop

CLAUDE.md v2.4 §Pipeline Step 6 (source of truth)
- Scan with ffprobe-sized RMS envelope at 100ms resolution.
- First-rise bias: 0.3s smoothing, pick the FIRST rise within 3 dB of the max.
- Snap the detected drop to the nearest onset (librosa onset_detect).
- Report real music length (an audio file's duration can include trailing
  silence — NEFFEX "Free Me" is 137s on disk, music ends at 87s).

Writes a known-drops entry for the SOP once Franco approves.

Usage:
    python find_music_drop.py "<path-to-mp3>"
"""
import argparse
import json
import sys

import numpy as np

try:
    import librosa
except ImportError:
    print("Missing: librosa. pip install librosa", file=sys.stderr)
    sys.exit(2)


def rms_envelope(y: np.ndarray, sr: int, hop_ms: int = 100) -> tuple[np.ndarray, int]:
    hop = int(sr * hop_ms / 1000)
    frames = len(y) // hop
    y2 = y[: frames * hop].reshape(frames, hop)
    rms = np.sqrt(np.mean(y2 * y2, axis=1) + 1e-12)
    return rms, hop


def db(x: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(x + 1e-12)


def find_music_end(dbs: np.ndarray, hop_s: float, silence_db: float = -55.0,
                   min_tail_s: float = 2.0) -> float:
    """Where does audible music stop? Last frame above `silence_db`."""
    above = np.where(dbs > silence_db)[0]
    if len(above) == 0:
        return 0.0
    end_frame = above[-1]
    return (end_frame + 1) * hop_s


def find_drop(y: np.ndarray, sr: int, dbs: np.ndarray, hop_s: float,
              search_s: tuple[float, float] = (3.0, 60.0),
              snap_window_s: float = 0.6,
              smooth_window_s: float = 0.3,
              lookback_s: float = 0.5) -> dict:
    """Pick the frame with the largest short-window RMS jump, then snap to onset.

    `smooth_window_s` is kept small (0.3s) so a sharp drop isn't averaged out.
    The score at frame i is (mean of next 1s) − (mean of previous `lookback_s`),
    which captures a one-shot step rather than a trend.
    """
    s_lo = max(int(lookback_s / hop_s), int(search_s[0] / hop_s))
    s_hi = min(len(dbs) - 10, int(search_s[1] / hop_s))

    k_smooth = max(1, int(smooth_window_s / hop_s))
    smooth = np.convolve(dbs, np.ones(k_smooth) / k_smooth, mode="same")

    lb = max(1, int(lookback_s / hop_s))
    fwd = max(1, int(1.0 / hop_s))  # 1s forward window for the "after" level
    score = np.full_like(smooth, -1e9)
    for i in range(s_lo, s_hi):
        before = smooth[i - lb : i].mean()
        after = smooth[i : i + fwd].mean()
        score[i] = after - before

    # Pick the FIRST rise strong enough to count (within 3 dB of the max rise),
    # not the strongest overall. Earlier drops give more usable track length.
    sl = score[s_lo:s_hi]
    peak_val = sl.max()
    threshold = peak_val - 3.0
    first_idx = int(np.argmax(sl > threshold))
    peak_frame = first_idx + s_lo
    rough_t = peak_frame * hop_s

    # Snap to nearest onset within +/- snap_window_s
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, units="frames", backtrack=False, hop_length=512
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    if len(onset_times) == 0:
        return {
            "rough_s": round(float(rough_t), 3),
            "snapped_s": round(float(rough_t), 3),
            "rise_db": round(float(score[peak_frame]), 2),
        }

    within = np.abs(onset_times - rough_t) <= snap_window_s
    if within.any():
        snapped = float(onset_times[within][np.argmin(np.abs(onset_times[within] - rough_t))])
    else:
        snapped = float(onset_times[int(np.argmin(np.abs(onset_times - rough_t)))])

    return {
        "rough_s": round(float(rough_t), 3),
        "snapped_s": round(snapped, 3),
        "rise_db": round(float(score[peak_frame]), 2),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("music", help="Path to music mp3/wav")
    ap.add_argument("--search-start", type=float, default=3.0)
    ap.add_argument("--search-end", type=float, default=90.0)
    args = ap.parse_args()

    print(f"Analyzing: {args.music}")
    y, sr = librosa.load(args.music, sr=None, mono=True)
    duration = len(y) / sr
    print(f"  on-disk duration: {duration:.3f}s")

    rms, hop = rms_envelope(y, sr, hop_ms=100)
    hop_s = hop / sr
    dbs = db(rms)

    music_end = find_music_end(dbs, hop_s)
    print(f"  real music ends at: {music_end:.3f}s")
    if duration - music_end > 2.0:
        print(f"  ! trailing silence: {duration - music_end:.2f}s (SOP: compute against real end)")

    drop = find_drop(
        y, sr, dbs, hop_s,
        search_s=(args.search_start, min(args.search_end, music_end - 2.0)),
    )
    print(f"  rough drop at: {drop['rough_s']}s  (rise {drop['rise_db']} dB)")
    print(f"  snapped drop:  {drop['snapped_s']}s  (nearest onset)")

    print("\nAdd this to SOP §Pipeline Step 6 known-drops once confirmed in-mix:")
    import os
    print(f"  - `{os.path.basename(args.music)}`: drop at **{drop['snapped_s']}s**. "
          f"Music ends at {music_end:.1f}s.")

    print("\n--- JSON ---")
    print(json.dumps({
        "file": args.music,
        "duration_s": round(duration, 3),
        "music_end_s": round(music_end, 3),
        "trailing_silence_s": round(max(0, duration - music_end), 3),
        "drop": drop,
    }, indent=2))


if __name__ == "__main__":
    main()
