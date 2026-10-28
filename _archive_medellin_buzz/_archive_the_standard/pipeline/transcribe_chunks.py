r"""
The Standard — Transcription fallback: fixed-length chunks for noisy sources

CLAUDE.md v2.4 §Pipeline Step 2 (live-recording fallback).
The islands method assumes clean audio with digital
silence between phrases. For live recordings (HOF speeches, applause-heavy
sources) where the noise floor stays above -55 dBFS, islands collapse into
one huge span and Parakeet OOMs on the whole file.

Fallback: window the file into fixed chunks (default 60s with 2s overlap)
and recognize each chunk independently. Timestamps are chunk-relative +
chunk_start, so an estimate exists even if word timings drift.

For final cutting of chosen thoughts, re-run islands on a narrow window
(--start-s / --end-s on transcribe_islands.py) with a tighter --dbfs.

--model-dir defaults to pipeline\models\sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.

Usage:
    python transcribe_chunks.py --audio "<path>" \
        --out working/<slug>/<basename>_chunks.jsonl
"""
import argparse
import json
import os
import sys

import numpy as np

try:
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe_islands import DEFAULT_MODEL_DIR


SAMPLE_RATE = 16000


def load_audio(path: str) -> np.ndarray:
    y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return y.astype(np.float32)


def build_recognizer(model_dir: str, num_threads: int = 2):
    import sherpa_onnx
    from pathlib import Path
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
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, pcm)
    recognizer.decode_stream(stream)
    r = stream.result
    return {"text": r.text, "tokens": list(r.tokens), "timestamps": list(r.timestamps)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    ap.add_argument("--out", default=None)
    ap.add_argument("--chunk-s", type=float, default=60.0)
    ap.add_argument("--overlap-s", type=float, default=2.0)
    ap.add_argument("--start-s", type=float, default=0.0)
    ap.add_argument("--end-s", type=float, default=None)
    args = ap.parse_args()

    print(f"Loading audio: {args.audio}", file=sys.stderr)
    y = load_audio(args.audio)
    total_s = len(y) / SAMPLE_RATE
    end_s = args.end_s if args.end_s is not None else total_s
    print(f"  duration: {total_s:.1f}s  processing {args.start_s:.1f}-{end_s:.1f}s "
          f"in {args.chunk_s}s chunks (overlap {args.overlap_s}s)", file=sys.stderr)

    print(f"Building recognizer...", file=sys.stderr)
    rec = build_recognizer(args.model_dir)
    print(f"  ready", file=sys.stderr)

    out_fh = open(args.out, "w", encoding="utf-8") if args.out else None
    step = args.chunk_s - args.overlap_s

    try:
        t = args.start_s
        idx = 0
        while t < end_s:
            cs = t
            ce = min(end_s, t + args.chunk_s)
            a = int(cs * SAMPLE_RATE)
            b = int(ce * SAMPLE_RATE)
            clip = y[a:b]
            if len(clip) < int(0.2 * SAMPLE_RATE):
                break
            r = recognize(rec, clip)
            record = {
                "idx": idx,
                "chunk_start_s": round(cs, 3),
                "chunk_end_s": round(ce, 3),
                "text": r["text"],
                "word_times_abs": [round(cs + t, 3) for t in r["timestamps"]],
                "tokens": r["tokens"],
            }
            line = json.dumps(record, ensure_ascii=False)
            print(line)
            if out_fh:
                out_fh.write(line + "\n")
                out_fh.flush()
            print(f"  [{idx:3d}] {cs:7.1f}-{ce:7.1f}  {len(r['text'])} chars", file=sys.stderr)
            idx += 1
            t += step
    finally:
        if out_fh:
            out_fh.close()


if __name__ == "__main__":
    main()
