r"""
Buzz Media kit — Gate 1 graphics mockup (CLAUDE.md §5 "HyperFrames graphics pass"): each HyperFrames
snapshot laid over the real 9:16 frame that will sit under it, side by side.

  python pipeline/graphics_mockup.py <project>/working/plans/s<N>_sheets/graphics_mockup.jpg ^
      "<snapshot.png>|<project>/broll/<clip>.mp4|<source t>|<xc>" ...

Snapshots come from build_graphics.py --stage snapshot (or `snapshot --at <t>` in the hf\ project).
Built for el-hueco s3 (2026-10-27).
"""
import io, subprocess, sys
from PIL import Image

cells = []
for spec in sys.argv[2:]:
    png, vid, t, xc = spec.split("|")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", t, "-i", vid, "-frames:v", "1", "-vf", "scale=-2:1920",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    bg = Image.open(io.BytesIO(raw)).convert("RGB")
    x0 = min(max(int(float(xc) * bg.width - 540), 0), bg.width - 1080)
    bg = bg.crop((x0, 0, x0 + 1080, 1920)).convert("RGBA")
    g = Image.open(png).convert("RGBA").resize((1080, 1920))
    if g.getextrema()[3][0] == 255:          # opaque snapshot: treat near-black as transparent
        px = g.load()
        for y in range(g.height):
            for x in range(g.width):
                r, gg, b, a = px[x, y]
                if r + gg + b < 12:
                    px[x, y] = (0, 0, 0, 0)
    cells.append(Image.alpha_composite(bg, g).convert("RGB").resize((540, 960)))
sheet = Image.new("RGB", (550 * len(cells), 960), "white")
for i, c in enumerate(cells):
    sheet.paste(c, (i * 550, 0))
sheet.save(sys.argv[1], quality=88)
