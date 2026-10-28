r"""
Buzz Media kit — a cutout (matte) of the subject, for graphics that pass behind them (CLAUDE.md §7). Generalised
from promo-03's orbit opener (working/graphics/make_assets.py there).

The cutout is the renderer's own picture of the subject (graphics_mockup.picture: the same framing, frame for frame,
from render_short.picture_plan), with the subject's alpha from MediaPipe's selfie segmenter, a guided-filter edge
(hair, shirt, mic) and light temporal smoothing, encoded VP9 with alpha. HyperFrames plays it in the scene above the
"back" elements, so they pass behind the subject.

Rules it keeps: the cutout never runs past its A-roll segment (it would paint the old shot over the new one), and it
ends at the scene's "matte_until" when there is one. Everything behind it must be gone before then (frame_check.py
fails on anything left over the face after the cutout ends).

  tools\venv_render\Scripts\python.exe -I pipeline/matte.py <edl> --scene <scene file stem, e.g. orbit>
      [--out <file.webm>]      default: <project>\working\graphics\assets\<stem>_matte.webm
      [--preview <reel t>]     write one PNG (the cutout over a checkerboard) instead of the video

Writes a new video file: run it only after Franco approves the scene at Gate 1 (CLAUDE.md §1.8). The grade isn't
applied: with an EDL "grade", the cutout's colour would differ from the graded picture under it.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import frame_check  # noqa: E402
import graphics_mockup  # noqa: E402
import kit  # noqa: E402

FPS, W, H = 30, 1080, 1920


def span(edl, scene):
    """(first frame, end frame) of the cutout: the scene's start to its matte_until / end, cut at the segment end."""
    seg_end = max(e["t"] + e["dur"] for e in edl["events"] if e["kind"] == "aroll"
                  and e["seg"] == next(x["seg"] for x in edl["events"] if x["kind"] == "aroll"
                                       and x["t"] <= scene["t"] < x["t"] + x["dur"]))
    end = min(scene["t"] + scene.get("matte_until", 1e9), scene.get("t_out", 1e9), seg_end)
    return int(round(scene["t"] * FPS)), int(round(end * FPS))


def segmenter():
    return vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(kit.TOOLS / "models/selfie_segmenter.tflite")),
        running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))


def alpha(seg, rgb, i, prev):
    small = cv2.resize(rgb, (540, 960), interpolation=cv2.INTER_AREA)
    m = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(small)),
                              int(i * 1000 / FPS)).confidence_masks[0].numpy_view().astype(np.float32)
    m = m[..., 0] if m.ndim == 3 else m
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    m = cv2.ximgproc.guidedFilter(rgb, m, 8, 1e-3)          # the edge follows hair and shirt
    m = m if prev is None else 0.6 * m + 0.4 * prev          # calm frame-to-frame flicker
    a = np.clip((m - 0.35) / 0.3, 0, 1)
    return m, (cv2.GaussianBlur(a, (0, 0), 1.2) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--scene", required=True, help="the hf_scene's file stem (orbit for .../orbit.html)")
    ap.add_argument("--out")
    ap.add_argument("--preview", type=float, help="reel time: write one PNG instead of the video")
    a = ap.parse_args()
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    scene = next(o for o in edl["events"] if o["kind"] == "hf_scene" and Path(o["src"]).stem == a.scene)
    if edl.get("grade"):
        print("  note: the EDL has a grade; the cutout is ungraded and may not match the picture under it")
    pic = frame_check.Picture(edl, frame_check.load_faces(edl) or {})
    f0, f1 = span(edl, scene)
    seg = segmenter()
    proj = kit.Project(edl)
    if a.preview is not None:
        f = int(round(a.preview * FPS))
        if not f0 <= f < f1:
            sys.exit(f"{a.preview} s is outside the cutout ({f0 / FPS:.2f}-{f1 / FPS:.2f} s)")
        rgb = np.asarray(graphics_mockup.picture(pic, f))
        _, al = alpha(seg, rgb, 0, None)
        board = ((np.indices((H, W)).sum(axis=0) // 40) % 2 * 80 + 90).astype(np.uint8)
        comp = (rgb * (al[..., None] / 255) + board[..., None] * (1 - al[..., None] / 255)).astype(np.uint8)
        dst = Path(a.out or proj.working / "graphics" / f"{a.scene}_matte_preview.png")
        Image.fromarray(comp).save(dst)
        print("wrote", dst)
        return
    dst = Path(a.out or proj.working / "graphics" / "assets" / f"{a.scene}_matte.webm")
    dst.parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                            "-crf", "28", "-row-mt", "1", "-auto-alt-ref", "0", str(dst)], stdin=subprocess.PIPE)
    prev = None
    for i, f in enumerate(range(f0, f1)):
        rgb = np.asarray(graphics_mockup.picture(pic, f))
        prev, al = alpha(seg, rgb, i, prev)
        enc.stdin.write(np.dstack([rgb, al]).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("matte encode failed")
    print(f"wrote {dst}: {f1 - f0} frames ({f0 / FPS:.2f}-{f1 / FPS:.2f} s). In the scene: data-start=\"0\", "
          f"duration {(f1 - f0) / FPS:.3f} s; set \"matte_until\" to {(f1 - f0) / FPS:.3f} if it ends before the scene")


if __name__ == "__main__":
    main()
