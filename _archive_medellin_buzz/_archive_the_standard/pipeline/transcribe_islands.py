r"""
The Standard — Step 2: Transcribe via Parakeet + Island method

CLAUDE.md v2.4 §Pipeline Step 2 (source of truth)
Parakeet word timestamps drift 0.1–0.4s, so we don't cut on them directly.
Instead:
  1. Split the audio into "islands" of speech using an energy threshold
     (-55 dB, 10ms frames, merge gaps <0.12s). Clean sources show digital
     silence (~-83 dB) between phrases, so island edges are frame-accurate.
  2. Re-run recognition on each island to get exact text per island.
     This also reveals fillers the full-file pass hides.
  3. Cut at island edges where possible. For cuts inside an island, test
     each candidate cut by recognizing the piece alone and nudging start/end
     by 0.05s until the text is clean.

This module exposes:
  - find_islands(audio_path, dbfs=-55, frame_ms=10, merge_gap_ms=120, min_len_ms=250)
  - transcribe_islands(audio_path, recognizer, limit=None)
  - transcribe_file_fast(audio_path, recognizer) — full-file pass, for scanning
  - cli: emits JSON lines, one per island.

--model-dir defaults to pipeline\models\sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.

Usage:
    python transcribe_islands.py \
        --audio "E:\\FRANCO\\The Standard\\Michael Jordan\\Speech\\MJ Hall of fame speech.mp3" \
        --out   "working/michael-jordan-01/islands.jsonl"
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

try:
    import librosa  # resampling, mp3 decode fallback
    import soundfile as sf
except ImportError as e:
    print(f"Missing dependency: {e}. pip install sherpa-onnx soundfile librosa",
          file=sys.stderr)
    sys.exit(2)


SAMPLE_RATE = 16000  # Parakeet expects 16kHz mono
DEFAULT_MODEL_DIR = str(Path(__file__).resolve().parent / "models"
                        / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")


def load_audio_mono_16k(path: str) -> np.ndarray:
    """Return mono float32 PCM at 16kHz."""
    y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return y.astype(np.float32)


def db_envelope(y: np.ndarray, frame_samples: int) -> np.ndarray:
    """RMS envelope in dBFS, one value per frame of `frame_samples` length."""
    n = len(y) // frame_samples
    y = y[: n * frame_samples].reshape(n, frame_samples)
    rms = np.sqrt(np.mean(y * y, axis=1) + 1e-12)
    return 20.0 * np.log10(rms + 1e-12)


def find_islands(
    audio_path: str,
    dbfs: float = -55.0,
    frame_ms: int = 10,
    merge_gap_ms: int = 120,
    min_len_ms: int = 250,
):
    """Return list of (start_s, end_s) spans of voiced audio."""
    y = load_audio_mono_16k(audio_path)
    frame_samples = int(SAMPLE_RATE * frame_ms / 1000)
    env = db_envelope(y, frame_samples)
    voiced = env > dbfs  # bool per frame

    # Build raw runs
    spans = []
    i = 0
    while i < len(voiced):
        if voiced[i]:
            j = i
            while j < len(voiced) and voiced[j]:
                j += 1
            spans.append([i, j])
            i = j
        else:
            i += 1

    # Merge spans separated by <= merge_gap_ms of silence
    merge_gap_frames = merge_gap_ms // frame_ms
    merged = []
    for s, e in spans:
        if merged and s - merged[-1][1] <= merge_gap_frames:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    # Drop spans shorter than min_len_ms
    min_len_frames = min_len_ms // frame_ms
    kept = [(s, e) for s, e in merged if (e - s) >= min_len_frames]

    # Convert frames -> seconds
    return [
        (s * frame_ms / 1000.0, e * frame_ms / 1000.0)
        for s, e in kept
    ]


def build_recognizer(model_dir: str, num_threads: int = 2):
    """Build sherpa-onnx offline Parakeet transducer recognizer."""
    import sherpa_onnx
    md = Path(model_dir)
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(md / "encoder.int8.onnx"),
        decoder=str(md / "decoder.int8.onnx"),
        joiner=str(md / "joiner.int8.onnx"),
        tokens=str(md / "tokens.txt"),
        num_threads=num_threads,
        sample_rate=SAMPLE_RATE,
        feature_dim=80,
        decoding_method="greedy_search",
        model_type="nemo_transducer",
    )


def recognize(recognizer, pcm: np.ndarray) -> dict:
    """Run recognition on a mono 16k float32 slice; return {text, tokens, timestamps}."""
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, pcm)
    recognizer.decode_stream(stream)
    r = stream.result
    return {
        "text": r.text,
        "tokens": list(r.tokens),
        "timestamps": list(r.timestamps),
    }


def transcribe_file_fast(audio_path: str, recognizer) -> dict:
    """One-shot recognition on the whole file. Use for scanning, not cutting."""
    y = load_audio_mono_16k(audio_path)
    return recognize(recognizer, y)


def transcribe_islands(
    audio_path: str,
    recognizer,
    dbfs: float = -55.0,
    frame_ms: int = 10,
    merge_gap_ms: int = 120,
    min_len_ms: int = 250,
    limit: int | None = None,
    start_s: float = 0.0,
    end_s: float | None = None,
):
    """Yield one dict per island: {idx, start_s, end_s, text, tokens, rel_timestamps}."""
    y = load_audio_mono_16k(audio_path)
    duration = len(y) / SAMPLE_RATE
    if end_s is None:
        end_s = duration

    islands = find_islands(audio_path, dbfs, frame_ms, merge_gap_ms, min_len_ms)
    islands = [(s, e) for s, e in islands if e > start_s and s < end_s]
    if limit:
        islands = islands[:limit]

    for idx, (s, e) in enumerate(islands):
        a = max(0, int(s * SAMPLE_RATE))
        b = min(len(y), int(e * SAMPLE_RATE))
        if b - a < int(0.08 * SAMPLE_RATE):
            continue
        clip = y[a:b]
        rec = recognize(recognizer, clip)
        yield {
            "idx": idx,
            "start_s": round(s, 3),
            "end_s": round(e, 3),
            "dur_s": round(e - s, 3),
            "text": rec["text"],
            "tokens": rec["tokens"],
            "rel_timestamps": rec["timestamps"],
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    ap.add_argument("--out", default=None, help="Write JSONL of islands here")
    ap.add_argument("--mode", choices=("islands", "fast"), default="islands")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start-s", type=float, default=0.0)
    ap.add_argument("--end-s", type=float, default=None)
    ap.add_argument("--dbfs", type=float, default=-55.0)
    args = ap.parse_args()

    rec = build_recognizer(args.model_dir)

    if args.mode == "fast":
        r = transcribe_file_fast(args.audio, rec)
        print(r["text"])
        return

    out_fh = open(args.out, "w", encoding="utf-8") if args.out else None
    try:
        for island in transcribe_islands(
            args.audio, rec,
            dbfs=args.dbfs,
            limit=args.limit,
            start_s=args.start_s,
            end_s=args.end_s,
        ):
            line = json.dumps(island, ensure_ascii=False)
            print(line)
            if out_fh:
                out_fh.write(line + "\n")
    finally:
        if out_fh:
            out_fh.close()


if __name__ == "__main__":
    main()
