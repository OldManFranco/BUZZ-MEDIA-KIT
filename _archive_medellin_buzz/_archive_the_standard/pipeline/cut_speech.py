"""
The Standard — Step 4: Cut the speech

CLAUDE.md v2.4 §Pipeline Step 4 (source of truth)
- Find each selected thought's words IN THE ACTUAL FILE (island method),
  never raw Parakeet timestamps on the full-file pass.
- Cut only at sentence boundaries (island edges) at the quietest point.
- Gaps inside a thought: 0.3-0.6s. Longer music-only pauses (1.3-1.6s) only
  between complete thoughts (handled in Step 5 mix, not here).
- Run recognition on every cut segment and confirm against the brief before
  continuing.

This script:
  1. Takes a cut map (JSON: {src_map, clips:[{name, src, start_s, end_s, expected}]}).
  2. Extracts each clip with ffmpeg (re-encodes to mono 44.1k mp3; applies a
     small sub-30ms fade-in/out so cuts don't click on a crowd-noise floor).
  3. Transcribes each clip via Parakeet to confirm the text, printing it next
     to the expected text (on by default; --no-verify to skip).
  4. Writes <out-dir>/cuts.json — each clip's "expected" text is the caption
     source of truth for Step 9. Mark caption emphasis words (P style) with
     asterisks in "expected", e.g. "you made a *mistake*".

Usage:
    python cut_speech.py --cut-map working/<slug>/cut_map.json \
        --out-dir working/<slug>/clips
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe_islands import DEFAULT_MODEL_DIR


def ffmpeg_cut(src: str, out: str, start_s: float, end_s: float,
               fade_ms: int = 15) -> dict:
    """Cut [start, end] from `src` to `out` as mono 44.1k mp3. Short fades."""
    dur = max(0.05, end_s - start_s)
    fade_s = fade_ms / 1000.0
    af = (
        f"afade=t=in:st=0:d={fade_s:.3f},"
        f"afade=t=out:st={dur - fade_s:.3f}:d={fade_s:.3f},"
        f"loudnorm=I=-18:TP=-2:LRA=11"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start_s:.3f}", "-t", f"{dur:.3f}", "-i", src,
        "-ac", "1", "-ar", "44100",
        "-af", af,
        "-codec:a", "libmp3lame", "-b:a", "192k",
        out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "ok": r.returncode == 0,
        "stderr": r.stderr[-400:] if r.returncode != 0 else "",
        "duration_s": round(dur, 3),
    }


def transcribe_clip(path: str, model_dir: str) -> str:
    """Fast Parakeet transcription of a short clip."""
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from transcribe_islands import build_recognizer, load_audio_mono_16k, recognize
    rec = build_recognizer(model_dir)
    pcm = load_audio_mono_16k(path)
    return recognize(rec, pcm)["text"]


def normalize_text(t: str) -> str:
    import re
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def text_diff_ratio(expected: str, got: str) -> float:
    """Jaccard similarity on word sets as a cheap sanity check."""
    e = set(normalize_text(expected).split())
    g = set(normalize_text(got).split())
    if not e and not g:
        return 1.0
    return len(e & g) / max(1, len(e | g))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cut-map", required=True,
                    help="JSON file: {src_map:{name:path}, clips:[{name,src,start_s,end_s,expected,group}]}")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL_DIR,
                    help="Parakeet model used to verify each clip against expected text")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    with open(args.cut_map, encoding="utf-8") as f:
        cmap = json.load(f)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    src_map = cmap["src_map"]

    report = []
    rec = None  # built lazily so one import failure doesn't block the whole run
    for i, clip in enumerate(cmap["clips"]):
        src = src_map[clip["src"]]
        name = clip["name"]
        out = out_dir / f"{i:02d}_{name}.mp3"
        cut = ffmpeg_cut(src, str(out), clip["start_s"], clip["end_s"])
        entry = {
            "idx": i,
            "name": name,
            "group": clip.get("group"),
            "src": clip["src"],
            "src_path": src,  # render_shots.py uses this for on-camera (a-roll) shots
            "start_s": clip["start_s"],
            "end_s": clip["end_s"],
            "duration_s": cut["duration_s"],
            "out_path": str(out),
            "expected": clip.get("expected", ""),
            "ok": cut["ok"],
        }

        if cut["ok"] and args.model_dir and not args.no_verify:
            if rec is None:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from transcribe_islands import build_recognizer, load_audio_mono_16k, recognize
                rec = build_recognizer(args.model_dir)
            # recognize this clip
            from transcribe_islands import load_audio_mono_16k, recognize
            pcm = load_audio_mono_16k(str(out))
            text = recognize(rec, pcm)["text"].strip()
            entry["recognized"] = text
            entry["match_ratio"] = round(text_diff_ratio(entry["expected"], text), 3)
        else:
            entry["recognized"] = None
            entry["match_ratio"] = None
            if not cut["ok"]:
                entry["ffmpeg_error"] = cut["stderr"]

        report.append(entry)
        # Live print
        if entry["ok"]:
            vr = entry["match_ratio"]
            vr_str = f" verify={vr}" if vr is not None else ""
            print(f"  [{i:02d}] {name:<30s}  {entry['duration_s']:5.2f}s{vr_str}")
            if entry["recognized"]:
                print(f"       expected: {entry['expected']}")
                print(f"       got     : {entry['recognized']}")
        else:
            print(f"  [{i:02d}] {name:<30s}  FAILED: {entry.get('ffmpeg_error','')}")

    out_json = out_dir / "cuts.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"clips": report}, f, indent=2)
    print(f"\n  Wrote {out_json}")


if __name__ == "__main__":
    main()
