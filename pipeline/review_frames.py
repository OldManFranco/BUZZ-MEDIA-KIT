r"""
Buzz Media kit — self-review strips (CLAUDE.md §5 step 6): every frame from 0.3 s before to 0.3 s after each
transition, one strip per transition, plus a 1 fps overview of the whole reel. promo-03's 2-frame face overlap at
a transition was only seen because a 1 fps sheet happened to land on it; a strip shows every frame.

Transitions come from the EDL: layout switches, graphic starts and ends, A-roll cuts that change the picture,
and transition SFX (whoosh/swoosh/slide/transition files in "sfx_track").

  python pipeline/review_frames.py <reel.mp4> <edl> [--out <dir>] [--at 4.43,9.5]
    -> <dir>\t<NN>_<time>s.jpg (one strip per transition) + overview.jpg   (default <dir>: <output>\review_<short>\)

Only reads the reel and writes JPG images.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

FPS = 30
TW, TH = 216, 384          # thumbnail size
SFX_TRANSITION = re.compile(r"whoosh|woosh|swoosh|slide|transition|swipe", re.I)


def transitions(edl):
    ts = {l["t"] for l in edl.get("layout", [])}
    for o in edl["events"]:
        if o["kind"] in ("title_card", "chip", "card", "hf_scene", "broll"):
            ts.add(o["t"])
            if isinstance(o.get("t_out"), (int, float)):
                ts.add(o["t_out"])
    segs = {}
    for e in edl["events"]:
        if e["kind"] == "aroll":
            segs.setdefault(e["seg"], e["t"])
    ts.update(segs.values())
    ts.update(h["t"] for h in edl.get("sfx_track", []) if SFX_TRANSITION.search(h.get("file", "")))
    out = []
    for t in sorted(t for t in ts if 0 < t < edl["length_s"]):
        if not out or t - out[-1] > 0.3:             # transitions closer than 0.3 s share a strip
            out.append(t)
    return out


def window(mp4, t0, n, w=TW, h=TH):
    """n frames from reel time t0, as RGB arrays (w x h)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t0, 0):.4f}", "-i", str(mp4), "-frames:v", str(n),
                        "-vf", f"scale={w}:{h}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                       capture_output=True)
    k = w * h * 3
    return [np.frombuffer(r.stdout[i:i + k], np.uint8).reshape(h, w, 3) for i in range(0, len(r.stdout) - k + 1, k)]


def strip(mp4, t, font):
    f0 = max(int(round(t * FPS)) - 9, 0)
    frames = window(mp4, f0 / FPS, 19)
    im = Image.new("RGB", (len(frames) * (TW + 4), TH + 30), "#fff")
    d = ImageDraw.Draw(im)
    for i, fr in enumerate(frames):
        x = i * (TW + 4)
        im.paste(Image.fromarray(fr), (x, 30))
        f = f0 + i
        d.text((x + 4, 4), f"f{f} {f / FPS:.2f}s", fill="#d00" if f == int(round(t * FPS)) else "#000", font=font)
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mp4")
    ap.add_argument("edl")
    ap.add_argument("--out")
    ap.add_argument("--at", help="comma-separated times instead of the EDL's transitions")
    a = ap.parse_args()
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else kit.Project(edl).output / f"review_{edl['short']}"
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    ts = [float(x) for x in a.at.split(",")] if a.at else transitions(edl)
    for k, t in enumerate(ts, 1):
        strip(a.mp4, t, font).save(out / f"t{k:02d}_{t:05.2f}s.jpg", quality=85)
    secs = int(edl["length_s"]) + 1
    thumbs = [window(a.mp4, s, 1, 162, 288) for s in range(secs)]
    cols = 10
    ov = Image.new("RGB", (cols * 166, ((secs + cols - 1) // cols) * 312), "#fff")
    d = ImageDraw.Draw(ov)
    for s, th in enumerate(thumbs):
        if th:
            x, y = (s % cols) * 166, (s // cols) * 312
            ov.paste(Image.fromarray(th[0]), (x, y + 22))
            d.text((x + 4, y + 2), f"{s} s", fill="#000", font=font)
    ov.save(out / "overview.jpg", quality=85)
    print(f"wrote {len(ts)} transition strips + overview.jpg in {out}")


if __name__ == "__main__":
    main()
