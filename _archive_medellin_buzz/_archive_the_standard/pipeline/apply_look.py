r"""
The Standard — apply an era look (CLAUDE.md v3.0 Step 7) to a still or archival clip.

Looks live in pipeline\looks\looks.json as ffmpeg filter chains (era_70s, era_90s, bw_film).
b-roll / a-roll never use this; they keep standard.cube.

Usage:
    python apply_look.py --look bw_film --in <src.jpg|mp4> --out <dst.jpg|mp4>
"""
import argparse
import json
import os
import subprocess
import sys

LOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "looks", "looks.json")


def look_chain(name: str) -> str:
    looks = json.load(open(LOOKS, encoding="utf-8"))
    if name not in looks or name.startswith("_"):
        sys.exit(f"Unknown look '{name}'. Known: {[k for k in looks if not k.startswith('_')]}")
    return looks[name]


def apply(look: str, src: str, out: str) -> None:
    chain = look_chain(look)
    is_still = os.path.splitext(src)[1].lower() in (".jpg", ".jpeg", ".png", ".webp")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vf", chain]
    if is_still:
        cmd += ["-frames:v", "1", "-q:v", "2"]
    else:
        cmd += ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an"]
    cmd.append(out)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-600:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--look", required=True)
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    apply(a.look, a.src, a.out)
    print(f"{a.look}: {a.src} -> {a.out}")


if __name__ == "__main__":
    main()
