r"""
Buzz Media kit — B-roll rule 4 helper: real 9:16 crops of candidate B-roll windows, one row per candidate.
Shows exactly what the short will show (the crop at that xc), not the full 16:9 frame with guide lines.

  python pipeline/broll_strips.py <project>/working/plans/s<N>_sheets/crops.jpg ^
      "A|<project>/broll/<clip>.mp4|0.22|7.0,7.6,8.2,8.8" "B|...|0.3|17.5,18.2,18.9"

Each spec: label | video | xc (crop center, 0-1 of the width) | comma-separated source times.
Built for el-hueco s3 (2026-10-27).
"""
import subprocess, sys, io
from PIL import Image, ImageDraw

out, specs = sys.argv[1], sys.argv[2:]
rows = []
for s in specs:
    label, path, xc, ts = s.split("|")
    xc = float(xc); cells = []
    for t in ts.split(","):
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", t, "-i", path, "-frames:v", "1",
                              "-vf", "scale=-2:640", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        im = Image.open(io.BytesIO(png)).convert("RGB")
        cw = int(im.height * 9 / 16)
        x0 = min(max(int(xc * im.width - cw / 2), 0), im.width - cw)
        c = im.crop((x0, 0, x0 + cw, im.height)).resize((180, 320))
        ImageDraw.Draw(c).text((4, 4), f"{label} {t}", fill="yellow")
        cells.append(c)
    rows.append(cells)
W = max(len(r) for r in rows) * 184
sheet = Image.new("RGB", (W, len(rows) * 324), "black")
for y, r in enumerate(rows):
    for x, c in enumerate(r):
        sheet.paste(c, (x * 184, y * 324))
sheet.save(out, quality=85)
