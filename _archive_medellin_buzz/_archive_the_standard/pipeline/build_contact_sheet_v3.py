r"""
The Standard — v3.0 storyboard sheet (CLAUDE.md v3.0 Step 3.5, GATE 2).

One 9:16 frame per segment in segments.json, rendered the way the edit will treat it:
  broll  -> frame at the segment middle, 9:16 crop at xc, standard.cube
  still  -> era look (looks.json), cover-crop toward focus
  graphic-> HyperFrames snapshot of that beat (qa/gfx_stills, from graphics_plan.json reel times)
Each frame gets the watermark (y=300) and the caption chunk at y=1380, plus a beat label.

Usage:
    python build_contact_sheet_v3.py --slug michael-jordan-02 [--cols 8]
"""
import argparse
import glob
import json
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTON = os.path.join(ROOT, "Anton-Regular.ttf")
CUBE = os.path.join(ROOT, "standard.cube").replace("\\", "/").replace(":", "\\:")
LOOKS = json.load(open(os.path.join(ROOT, "pipeline", "looks", "looks.json"), encoding="utf-8"))
W, H = 1080, 1920


def ff_frame(src, t, vf, out):
    seek = ["-ss", f"{t:.3f}"] if t > 0 else []  # -ss on a still image yields no frame
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *seek, "-i", src,
           "-frames:v", "1", "-vf", vf, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])


def broll_frame(seg, scene_dir, tmp):
    src = os.path.join(scene_dir, seg["src"])
    t = seg.get("src_offset_s", 0) + seg["out_dur_s"] * seg.get("speed", 0.5) / 2
    xc = seg.get("xc", 0.5)
    vf = (f"scale=-2:1080,crop=608:1080:'max(0,min(iw-608,{xc}*iw-304))':0,"
          f"scale={W}:{H}:flags=lanczos,lut3d=file='{CUBE}'")
    out = os.path.join(tmp, seg["name"] + ".png")
    ff_frame(src, t, vf, out)
    return Image.open(out).convert("RGB")


def still_frame(seg, scene_dir, tmp):
    src = os.path.join(scene_dir, seg["src"])
    fx, fy = seg.get("focus", [0.5, 0.5])
    look = LOOKS[seg.get("grade", "bw_film")]
    sw, sh = Image.open(src).size
    k = max(W / sw, H / sh)
    nw, nh = int(round(sw * k / 2) * 2), int(round(sh * k / 2) * 2)
    cx = int(max(0, min(nw - W, fx * nw - W / 2)))
    cy = int(max(0, min(nh - H, fy * nh - H / 2)))
    vf = f"scale={nw}:{nh}:flags=lanczos,crop={W}:{H}:{cx}:{cy},{look}"
    out = os.path.join(tmp, seg["name"] + ".png")
    ff_frame(src, 0, vf, out)
    return Image.open(out).convert("RGB")


def graphic_frame(seg, plan, stills_dir):
    beat = next(b for b in plan["beats"] if b["name"] == seg["reel"])
    best, best_d = None, 1e9
    for p in glob.glob(os.path.join(stills_dir, "at-*.png")):
        t = float(os.path.basename(p)[3:-5])
        if beat["reel_start_s"] <= t < beat["reel_start_s"] + beat["dur_s"]:
            d = abs(t - (beat["reel_start_s"] + beat["dur_s"] * 0.6))
            if d < best_d:
                best, best_d = p, d
    if not best:
        return Image.new("RGB", (W, H), (40, 0, 0))
    return Image.open(best).convert("RGB").resize((W, H))


def caption_at(t, timeline, cuts_expected):
    for e in timeline["edit"]:
        if e["tl_start"] <= t < e["tl_end"] + 0.4:
            words = e["text"].split()
            frac = (t - e["tl_start"]) / max(0.01, e["tl_end"] - e["tl_start"])
            i = min(len(words) - 1, max(0, int(frac * len(words))))
            return " ".join(words[i:i + 3])
    for c in timeline.get("speech_tl", []):
        if c["tl_start"] <= t < c["tl_end"]:
            words = cuts_expected.get(c["name"], "").replace("*", "").split()
            frac = (t - c["tl_start"]) / max(0.01, c["tl_end"] - c["tl_start"])
            i = min(len(words) - 1, max(0, int(frac * len(words))))
            return " ".join(words[i:i + 3])
    return ""


def overlay(img, caption, label):
    d = ImageDraw.Draw(img)
    wm = ImageFont.truetype(ANTON, 44)
    tw = d.textlength("@thestandard.daily", font=wm)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(((W - tw) / 2, 300 - 26), "@thestandard.daily", font=wm, fill=(255, 255, 255, 64))
    if caption:
        cap = caption.upper()
        size = 200
        f = ImageFont.truetype(ANTON, size)
        while d.textlength(cap, font=f) > 960 and size > 80:
            size -= 10
            f = ImageFont.truetype(ANTON, size)
        cw = d.textlength(cap, font=f)
        x, y = (W - cw) / 2, 1380 - size * 0.62
        halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(halo).text((x, y), cap, font=f, fill=(0, 0, 0, 215), stroke_width=18, stroke_fill=(0, 0, 0, 215))
        layer = Image.alpha_composite(layer, halo.filter(ImageFilter.GaussianBlur(22)))
        ImageDraw.Draw(layer).text((x, y), cap, font=f, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0, 255))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(ANTON, 64)
    d.rectangle([0, 0, W, 110], fill=(0, 0, 0))
    d.text((24, 18), label, font=lf, fill=(255, 220, 90))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--cols", type=int, default=8)
    a = ap.parse_args()
    wd = os.path.join(ROOT, "working", a.slug)
    req = json.load(open(os.path.join(wd, "request.json"), encoding="utf-8"))
    scene_dir = os.path.join(ROOT, req["subject_folder"], "Scene Pack")
    segs = json.load(open(os.path.join(wd, "segments.json"), encoding="utf-8"))
    tl = json.load(open(os.path.join(wd, "timeline.json"), encoding="utf-8"))
    if segs.get("format") != "v3" or tl.get("format") != "v3":
        raise SystemExit("segments.json / timeline.json are not format v3")
    plan = json.load(open(os.path.join(wd, "graphics_plan.json"), encoding="utf-8"))
    cuts = json.load(open(os.path.join(wd, "clips", "cuts.json"), encoding="utf-8"))
    cuts_expected = {c["name"]: c["expected"] for c in cuts.get("clips", cuts if isinstance(cuts, list) else [])}
    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in segs["segments"]:
            if s["type"] == "broll":
                img = broll_frame(s, scene_dir, tmp)
            elif s["type"] == "still":
                img = still_frame(s, scene_dir, tmp)
            else:
                img = graphic_frame(s, plan, os.path.join(wd, "qa", "gfx_stills"))
            mid = s["tl_start_s"] + s["out_dur_s"] / 2
            cap = "" if s.get("mute_captions") else caption_at(mid, tl, cuts_expected)
            label = f"{s['name']}  {s['tl_start_s']:.1f}s  {s['out_dur_s']:.1f}s"
            tiles.append(overlay(img, cap, label).resize((270, 480)))
    cols = a.cols
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270 + (cols + 1) * 8, rows * 480 + (rows + 1) * 8), (25, 25, 25))
    for i, t in enumerate(tiles):
        sheet.paste(t, (8 + (i % cols) * 278, 8 + (i // cols) * 488))
    out = os.path.join(wd, "qa", "storyboard_v3.jpg")
    sheet.save(out, quality=88)
    print(out, f"{len(tiles)} frames")


if __name__ == "__main__":
    main()
