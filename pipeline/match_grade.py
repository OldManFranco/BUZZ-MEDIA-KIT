r"""
Buzz Media kit — build a .cube that makes raw footage look like the finished long-form.

Uses map.json pairs (same moment in raw and in the long-form), grabs aligned frames,
matches each RGB channel's histogram (CDF matching, top 70% of the frame so the
long-form's chips/lower thirds don't skew it), averages the curves across pairs and
writes a 33^3 .cube with those per-channel curves.

  python pipeline/match_grade.py --slug el-hueco --longform "input/el hueco/<long-form>.mp4" \
         --raw-dir "input/el hueco/raw" --pairs 12
Writes <project>\working\grade\longform_match.cube + compare.png (raw | matched | long-form).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

W, H = 640, 360


def grab(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3) if len(r.stdout) == W * H * 3 else None


def ncc(a, b):
    """Structure similarity on small grayscale versions (grade-independent: each is z-normalized)."""
    g = [np.asarray(Image.fromarray(x).convert("L").resize((64, 36)), np.float64).ravel() for x in (a, b)]
    g = [(x - x.mean()) / (x.std() + 1e-6) for x in g]
    return float((g[0] * g[1]).mean())


def cdf(x):
    h = np.bincount(x.ravel(), minlength=256).astype(np.float64)
    return np.cumsum(h) / h.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="clients/<client>/projects/<project>")
    ap.add_argument("--slug", help="archived layout only")
    ap.add_argument("--longform", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--pairs", type=int, default=12)
    a = ap.parse_args()

    wd = (kit.Project(project_dir=a.project) if a.project else kit.Project({}, slug=a.slug)).working
    runs = [r for r in json.loads((wd / "map.json").read_text(encoding="utf-8"))["runs"]
            if r["match_score"] >= 0.95 and r["longform_out"] - r["longform_in"] > 4]
    curves, pairs = [], []
    for r in runs:
        if len(curves) >= a.pairs:
            break
        for off in (1.0, 2.5, 4.0):
            raw = grab(Path(a.raw_dir) / f"{r['raw_file']}.MP4", r["raw_in"] + off)
            lf = grab(a.longform, r["longform_in"] + off)
            # keep only frames where the long-form shows this raw shot (not a card or other B-roll)
            if raw is not None and lf is not None and ncc(raw, lf) > 0.85:
                break
        else:
            continue
        top = int(H * 0.7)
        c = []
        for ch in range(3):
            cr, cl = cdf(raw[:top, :, ch]), cdf(lf[:top, :, ch])
            c.append(np.interp(cr, cl, np.arange(256)))
        curves.append(np.array(c))
        pairs.append((raw, lf))
    curve = np.median(np.array(curves), axis=0)            # 3 x 256, output 0-255 per input level
    # smooth and keep monotonic
    k = np.ones(9) / 9
    curve = np.array([np.maximum.accumulate(np.convolve(np.pad(c, 4, mode="edge"), k, "valid")) for c in curve])

    out = wd / "grade"
    out.mkdir(parents=True, exist_ok=True)
    n = 33
    lv = np.linspace(0, 255, n)
    f = [np.interp(lv, np.arange(256), curve[ch]) / 255.0 for ch in range(3)]
    lines = [f'TITLE "long-form match ({wd.parent.name if a.project else a.slug})"', f"LUT_3D_SIZE {n}"]
    for b in range(n):
        for g in range(n):
            for r_ in range(n):
                lines.append(f"{f[0][r_]:.6f} {f[1][g]:.6f} {f[2][b]:.6f}")
    (out / "longform_match.cube").write_text("\n".join(lines) + "\n", encoding="ascii")

    raw, lf = pairs[len(pairs) // 2]
    matched = np.stack([np.interp(raw[..., ch], np.arange(256), curve[ch]) for ch in range(3)], -1).astype(np.uint8)
    Image.fromarray(np.hstack([raw, matched, lf])).save(out / "compare.png")
    print(f"{len(curves)} frame pairs; wrote {out / 'longform_match.cube'} and compare.png")
    for ch, name in enumerate("RGB"):
        print(name, [int(curve[ch][i]) for i in (16, 64, 128, 192, 240)])


if __name__ == "__main__":
    main()
