"""
Buzz Media kit — benchmark scan (ANALYSIS ONLY, never writes video).

For every <name>.mp4 + <name>.info.json in a folder:
  - metadata from yt-dlp (title, duration, views, likes, upload date, description)
  - shots via PySceneDetect ContentDetector (pipeline/scene_detect.py)
  - loudness (integrated LUFS, true peak) via ffmpeg ebur128, analysis only
  - one keyframe sheet JPG per short: row 1 = the hook (0.0-3.0 s every 0.5 s),
    rows below = the rest every 3 s, each frame stamped with its time
  - if <transcripts>/<name>.words.json exists (WhisperX), first-word time, words in the
    first 3 s, speaking rate, and the last line

Writes <out>/scan.json and <out>/sheets/<name>.jpg.

Usage:
  python -I pipeline/benchmark_scan.py _benchmark/opus-clip-samples _benchmark --transcripts _benchmark/transcripts
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_detect import detect_shots  # noqa: E402

THUMB_W = 180


def probe_duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def loudness(p):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    tail = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return {"lufs": float(i.group(1)) if i else None, "true_peak_dbfs": float(tp.group(1)) if tp else None}


def frame(p, t):
    """One frame as a PIL image (rawvideo over a pipe, nothing written to disk)."""
    h = int(THUMB_W * 16 / 9)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(p), "-frames:v", "1",
                          "-vf", f"scale={THUMB_W}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    if len(raw) < THUMB_W * h * 3:
        return Image.new("RGB", (THUMB_W, h), (40, 40, 40))
    return Image.frombytes("RGB", (THUMB_W, h), raw[:THUMB_W * h * 3])


def sheet(p, dur, dst):
    hook_ts = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    rest_ts = [t for t in range(6, int(dur), 3)] + [max(dur - 0.5, 0)]
    per_row = len(hook_ts)
    rows = [hook_ts] + [rest_ts[i:i + per_row] for i in range(0, len(rest_ts), per_row)]
    h = int(THUMB_W * 16 / 9)
    img = Image.new("RGB", (per_row * THUMB_W, len(rows) * (h + 18)), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        f = ImageFont.load_default()
    for r, ts in enumerate(rows):
        for c, t in enumerate(ts):
            x, y = c * THUMB_W, r * (h + 18)
            img.paste(frame(p, min(t, max(dur - 0.05, 0))), (x, y + 18))
            d.text((x + 4, y + 2), f"{'HOOK ' if r == 0 else ''}{t:.1f}s", fill=(0, 0, 0), font=f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, quality=82)


def speech_stats(words_json, dur):
    d = json.loads(words_json.read_text(encoding="utf-8"))
    words = d.get("words", [])
    if not words:
        return {"first_word_s": None, "words_first_3s": "", "wpm": 0, "first_line": "", "last_line": "", "text": ""}
    segs = d.get("segments", [])
    spoken = sum(w["end"] - w["start"] for w in words)
    gaps = [round(b["start"] - a["end"], 2) for a, b in zip(words, words[1:]) if b["start"] - a["end"] > 0.6]
    return {
        "first_word_s": round(words[0]["start"], 2),
        "words_first_3s": " ".join(w["w"] for w in words if w["start"] < 3.0),
        "last_word_end_s": round(words[-1]["end"], 2),
        "tail_after_last_word_s": round(dur - words[-1]["end"], 2),
        "wpm": round(len(words) / (dur / 60), 1),
        "speech_ratio": round(spoken / dur, 2),
        "pauses_over_0_6s": gaps,
        "first_line": segs[0]["text"] if segs else "",
        "last_line": segs[-1]["text"] if segs else "",
        "text": " ".join(s["text"] for s in segs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--transcripts")
    ap.add_argument("--threshold", type=float, default=27.0)
    ap.add_argument("--speech-only", action="store_true", help="only (re)merge transcript stats into an existing scan.json")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    tdir = Path(a.transcripts) if a.transcripts else None

    if a.speech_only:
        rows = json.loads((out / "scan.json").read_text(encoding="utf-8"))
        for row in rows:
            wj = tdir / f"{Path(row['file']).stem}.words.json"
            if wj.exists():
                row.update(speech_stats(wj, row["duration_s"]))
        (out / "scan.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"merged speech stats into {out / 'scan.json'}")
        return

    rows = []
    for mp4 in sorted(src.glob("*.mp4")):
        info = json.loads(mp4.with_suffix(".info.json").read_text(encoding="utf-8"))
        dur = probe_duration(mp4)
        shots = detect_shots(str(mp4), threshold=a.threshold)
        lens = [s["duration_s"] for s in shots]
        row = {
            "file": mp4.name, "id": info.get("id"), "title": info.get("title"),
            "upload_date": info.get("upload_date"), "duration_s": round(dur, 2),
            "views": info.get("view_count"), "likes": info.get("like_count"), "comments": info.get("comment_count"),
            "description": info.get("description"),
            "shots": len(shots), "avg_shot_s": round(sum(lens) / len(lens), 2) if lens else None,
            "longest_shot_s": round(max(lens), 2) if lens else None,
            "cuts_first_3s": sum(1 for s in shots[1:] if s["start_s"] < 3.0),
            "cut_times": [round(s["start_s"], 2) for s in shots[1:]],
            **loudness(mp4),
        }
        if tdir and (tdir / f"{mp4.stem}.words.json").exists():
            row.update(speech_stats(tdir / f"{mp4.stem}.words.json", dur))
        sheet(mp4, dur, out / "sheets" / f"{mp4.stem}.jpg")
        rows.append(row)
        print(f"{mp4.name}: {len(shots)} shots, {row['lufs']} LUFS", flush=True)

    (out / "scan.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out / 'scan.json'}")


if __name__ == "__main__":
    main()
