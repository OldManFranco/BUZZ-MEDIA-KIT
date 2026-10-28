"""
The Standard — Step 1: Inventory and classify

CLAUDE.md v2.4 §Pipeline Step 1 (source of truth)
Walks the subject folder recursively, classifies files, ffprobes real media info,
hash-dedupes audio, and prints a report before Step 2 (transcribe).

Usage:
    python inventory.py "<path-to-subject-folder>"
    e.g. python inventory.py "E:\\FRANCO\\The Standard\\Michael Jordan"
"""
import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path


HOOK_MARKERS = ("eleven", "hook", "narration")


def ffprobe(path: str) -> dict:
    """Return parsed ffprobe JSON for a media file."""
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return {"error": out.stderr.strip()}
    return json.loads(out.stdout)


def classify(path: Path, subject_root: Path) -> str:
    """Return one of: hook, subject_audio, music, broll, other.

    New per-subject folder convention (post-michael-jordan-01):
      - Narration/*   -> hook (ElevenLabs AI narration lives here)
      - Speech/*      -> subject_audio (keyword fallback still recognizes
                        hook files dropped there by old habit)
      - Scene Pack/*  -> broll
      - Music/*       -> music
    """
    rel = path.relative_to(subject_root)
    parts = {p.lower() for p in rel.parts}
    name = path.name.lower()
    if "narration" in parts:
        return "hook"
    if "speech" in parts:
        if any(m in name for m in HOOK_MARKERS):
            return "hook"
        return "subject_audio"
    if "music" in parts:
        return "music"
    if "scene pack" in parts:
        return "broll"
    return "other"


def md5_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def media_summary(info: dict) -> dict:
    """Pull the fields we actually care about out of ffprobe JSON."""
    if "error" in info:
        return {"error": info["error"]}
    fmt = info.get("format", {})
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    out = {
        "duration_s": round(float(fmt.get("duration", 0.0)), 3),
        "size_bytes": int(fmt.get("size", 0)),
        "format": fmt.get("format_name", ""),
    }
    if video:
        out["video"] = {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": video.get("avg_frame_rate"),
        }
    if audio:
        out["audio"] = {
            "codec": audio.get("codec_name"),
            "sample_rate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
        }
    return out


def main(subject_root: str):
    root = Path(subject_root).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    print(f"\n=== Inventory for: {root.name} ===")
    print(f"root: {root}\n")

    buckets = {"hook": [], "subject_audio": [], "music": [], "broll": [], "other": []}
    hashes = {}  # md5 -> first path

    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name == ".inventory.json":
            continue
        cls = classify(p, root)
        rel = p.relative_to(root)
        info = ffprobe(str(p))
        summary = media_summary(info)
        entry = {"path": str(rel), "class": cls, "media": summary}

        # Hash-dedupe audio only
        if cls in ("hook", "subject_audio", "music"):
            try:
                digest = md5_file(p)
                if digest in hashes:
                    entry["duplicate_of"] = hashes[digest]
                else:
                    hashes[digest] = str(rel)
                entry["md5"] = digest
            except Exception as e:
                entry["hash_error"] = str(e)

        buckets.setdefault(cls, []).append(entry)

    # Print report
    for cls in ("subject_audio", "hook", "music", "broll", "other"):
        items = buckets[cls]
        print(f"--- {cls} ({len(items)}) ---")
        for e in items:
            m = e["media"]
            dup = f"  [DUP of {e['duplicate_of']}]" if e.get("duplicate_of") else ""
            if "error" in m:
                print(f"  {e['path']}  [ffprobe error: {m['error']}]{dup}")
                continue
            if "video" in m:
                v = m["video"]
                print(f"  {e['path']}  {v['width']}x{v['height']} @ {v['fps']}  "
                      f"{m['duration_s']}s  {m['size_bytes']/1e6:.1f} MB{dup}")
            else:
                a = m.get("audio", {})
                print(f"  {e['path']}  {a.get('codec','?')}/{a.get('sample_rate','?')}Hz/"
                      f"{a.get('channels','?')}ch  {m['duration_s']}s  "
                      f"{m['size_bytes']/1e6:.1f} MB{dup}")
        print()

    # Checks per SOP §Preflight + Step 1
    print("--- Checks ---")
    n_subject = len(buckets["subject_audio"])
    n_music = len(buckets["music"])
    n_broll = len(buckets["broll"])
    print(f"  subject_audio count: {n_subject}  (need >=1)  {'OK' if n_subject>=1 else 'MISSING'}")
    print(f"  music count:         {n_music}  (need ==1)   {'OK' if n_music==1 else 'CHECK'}")
    print(f"  broll count:         {n_broll}  (need >=1)  {'OK' if n_broll>=1 else 'MISSING'}")
    print(f"  hook present yet:    {len(buckets['hook'])}  (expected 0 at pre-Gate 1)")

    # Speech files with a video stream can supply on-camera (a-roll) shots.
    # Low-res is allowed (old footage often only exists at 480p);
    # render_shots.py denoises/sharpens it.
    for e in buckets["subject_audio"]:
        v = e["media"].get("video", {})
        if v and v.get("width"):
            w, h = v["width"], v["height"]
            note = "" if min(w, h) >= 1080 else " (low-res: usable, gets denoise/sharpen; tell Franco)"
            print(f"  On-camera clips available from {e['path']}: {w}x{h}{note}")

    # Scene pack real-resolution check — the SOP mandates ffprobe over filenames
    for e in buckets["broll"]:
        v = e["media"].get("video", {})
        if v:
            h = v.get("height") or 0
            w = v.get("width") or 0
            # The short side must reach 1080: a 1920x800 pack is NOT 1080p.
            if min(w, h) < 1080:
                print(f"  !! Scene pack {e['path']} is {w}x{h} — below 1080p. "
                      "SOP requires real 1080p+ pack. Flag to Franco.")
            else:
                print(f"  Scene pack {e['path']} is {w}x{h} — OK (>=1080p).")

    # Return machine-readable too
    out_path = root / ".inventory.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(buckets, f, indent=2, default=str)
        print(f"\n  Wrote {out_path}")
    except Exception as e:
        print(f"\n  (could not write inventory json: {e})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
