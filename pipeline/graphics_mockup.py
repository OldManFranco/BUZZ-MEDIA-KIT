r"""
Buzz Media kit — Gate 1 mockups (CLAUDE.md §5 step 5): each graphic over the exact picture the renderer will put
under it, with the real caption layer, from one shared script (promo-02/03 each copied their own and they broke).

  - picture: the source frame at that moment, placed with the renderer's own framing (render_short.picture_plan:
    faces.json per segment, layout full/split/pip, punch with eyes at 37 %, pull-back moves); no grade
  - graphics: exact-alpha HyperFrames snapshots (build_graphics.snapshot_rgba: black and white passes)
  - captions: build_captions.Layer on the plan's own words (EDL "spoken_words"), drawn exactly as the render will

build_graphics.py --stage snapshot calls it and writes working\plans\s<N>_graphics_mockup.jpg. Standalone:
  python pipeline/graphics_mockup.py <edl> [--at 1.2,4.5,...] [--out <sheet.jpg>] [--frames <dir>]
"""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import frame_check  # noqa: E402
import kit  # noqa: E402
import render_short as rs  # noqa: E402

FPS, W, H = 30, 1080, 1920
INK = (18, 18, 18)


def source_frame(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(path), "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB") if raw else None


def picture(pic, f):
    """The renderer's picture at frame f (A-roll framing or a B-roll/still 9:16 crop), as an RGB image."""
    r = pic.run(f)
    src = pic.inp / r["src"]
    t = r["t"] + (f - r["f0"]) / FPS
    im = source_frame(src, 0 if src.suffix.lower() in rs.STILL_EXT else t)
    out = Image.new("RGB", (W, H), INK)
    if im is None:
        return out
    if r["kind"] != "aroll":
        sc = H / im.height
        x0 = min(max(r["xc"] * im.width * sc - W / 2, 0), im.width * sc - W)
        return im.transform((W, H), Image.AFFINE, (1 / sc, 0, x0 / sc, 0, 1 / sc, 0), resample=Image.BICUBIC,
                            fillcolor=INK)
    sc, ox, oy = pic.affine(r, f, im.width, im.height)
    placed = im.transform((W, H), Image.AFFINE, (1 / sc, 0, -ox / sc, 0, 1 / sc, -oy / sc), resample=Image.BICUBIC,
                          fillcolor=INK)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    if r["mode"] == "split" and not r.get("move"):
        d.rectangle((0, H // 2, W, H), fill=255)
    elif r["mode"] == "pip" and pic.edl.get("pip"):
        p = pic.edl["pip"]
        d.rounded_rectangle((p["x"], p["y"], p["x"] + p["w"] - 1, p["y"] + p["h"] - 1), p["r"], fill=255)
    else:
        d.rectangle((0, 0, W, H), fill=255)
    out.paste(placed, (0, 0), mask)
    return out


def pick(edl, times, n=15):
    """Up to n mockup moments: each graphic 0.4 s in and near its end, each layout switch 2 frames in."""
    want = []
    for o in edl["events"]:
        if o["kind"] in frame_check.OVERLAYS:
            end = o.get("t_out", o["t"] + 2.5)
            want += [o["t"] + min(0.4, (end - o["t"]) / 2), end - 0.2]
    want += [l["t"] + 2 / FPS for l in edl.get("layout", [])]
    got = []
    for w in sorted(want):
        t = min(times, key=lambda x: abs(x - w))
        if t not in got:
            got.append(t)
    step = max(1, len(got) // n + (len(got) % n > 0))
    return got[::step][:n]


def mockup(edl, frames, faces, out, n=15):
    """frames: [(t, rgba)] from build_graphics.snapshot_rgba. Writes a contact sheet of composited frames."""
    pic = frame_check.Picture(edl, faces or {})
    caps = frame_check.captions_layer(edl)
    by_t = dict(frames)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
    cells = []
    for t in pick(edl, list(by_t), n):
        f = int(round(t * FPS))
        im = picture(pic, f).convert("RGBA")
        im.alpha_composite(Image.fromarray(by_t[t], "RGBA"))
        im.alpha_composite(Image.frombytes("RGBA", (W, H), caps.frame(min(f, caps.n - 1))))
        d = ImageDraw.Draw(im)
        d.rectangle((0, H - 44, W, H), fill="#000")
        d.text((16, H - 46), f"{t:.2f}s  {pic.mode(f)}", fill="#FFC629", font=font)
        cells.append(im.convert("RGB").resize((360, 640)))
    cols = 5
    sheet = Image.new("RGB", (cols * 368 - 8, ((len(cells) + cols - 1) // cols) * 648), "#fff")
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * 368, (i // cols) * 648))
    sheet.save(out, quality=88)
    print("wrote", out, len(cells), "frames")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--at", help="comma-separated reel times (default: picked from the plan)")
    ap.add_argument("--out", help="sheet path (default: working\\plans\\<short>_graphics_mockup.jpg)")
    a = ap.parse_args()
    import build_graphics
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    proj = kit.Project(edl)
    rd = proj.render_dir(edl["short"])
    rd.mkdir(parents=True, exist_ok=True)
    n = build_graphics.n_frames(edl, rd)
    times = [float(x) for x in a.at.split(",")] if a.at else build_graphics.sample_times(edl, n)
    frames = build_graphics.snapshot_rgba(edl, rd, n, times)
    mockup(edl, frames, frame_check.load_faces(edl),
           a.out or proj.plans / f"{edl['short']}_graphics_mockup.jpg", n=len(times) if a.at else 15)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
