"""
Buzz Media kit — contact sheets for reframing 16:9 footage to 9:16 (inherited from The Standard v2.4, not yet adapted)

Source of truth: CLAUDE.md §Reframe. Crop guide still assumes 1920x1080 sources.
- No face-detection model is available. Frame by eye instead:
  1. Contact sheets: midframe of every shot with the crop guide drawn on,
     20 shots per image. Set xc per shot by looking at the sheet.
  2. Re-check with a sheet of rendered crops at 20/50/80% through each shot.
- Avoid close-ups where the face sits in the lower 35% of the frame (captions
  sit around y=1360, see _brand/brand-notes.md §4). Both sheets shade that zone red.

Mode 1 — midframe sheets (before rendering):
    python build_contact_sheet.py --video "<scene pack>" --shots shots.json \
        --out-dir working/<slug>/sheets [--xc-json xc.json]
  xc.json (optional) = {"<shot idx>": xc, ...}; default 0.5.

Mode 2 — re-check sheets (after render_shots.py):
    python build_contact_sheet.py --plan working/<slug>/shots/shot_plan.json \
        --out-dir working/<slug>/sheets
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CROP_W = 608
CAPTION_ZONE = 0.35  # lower 35% of the frame
CAPTION_Y = 1360 / 1920


def load_font(px: int):
    for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, px)
        except Exception:
            continue
    return ImageFont.load_default()


def probe_size(video: str) -> tuple:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
        capture_output=True, text=True, check=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def extract_frame(video: str, time_s: float, out_png: str, max_width: int = 480):
    """Extract one frame at `time_s`, scale to max_width."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{time_s:.3f}", "-i", video,
        "-frames:v", "1",
        "-vf", f"scale='min({max_width},iw)':-2",
        out_png,
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def draw_guide(img: Image.Image, xc: float, src_size: tuple) -> Image.Image:
    """Draw the 608x1080 crop guide (at 1080-tall source geometry) at xc.

    Inside the crop, the lower 35% (caption zone) is tinted red.
    """
    W, H = img.size
    src_w, src_h = src_size
    width = src_w * 1080 / src_h  # source width at 1080 tall
    X_src = max(0, min(width - CROP_W, xc * width - CROP_W / 2))
    x0 = int(X_src / width * W)
    x1 = int((X_src + CROP_W) / width * W)
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, 0, x0, H], fill=(0, 0, 0, 140))
    draw.rectangle([x1, 0, W, H], fill=(0, 0, 0, 140))
    draw.rectangle([x0, int(H * (1 - CAPTION_ZONE)), x1, H], fill=(255, 0, 0, 50))
    draw.rectangle([x0, 0, x1 - 1, H - 1], outline=(255, 215, 0, 255), width=2)
    return img


def midframe_sheets(args):
    with open(args.shots, encoding="utf-8") as f:
        shots = json.load(f)["shots"]
    xc_map = {}
    if args.xc_json:
        with open(args.xc_json, encoding="utf-8") as f:
            xc_map = {int(k): float(v) for k, v in json.load(f).items()}

    src_size = probe_size(args.video)
    out_dir = Path(args.out_dir)
    tmp_dir = out_dir / "_frames"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    font = load_font(16)

    per_sheet = args.cols * args.rows
    cw = args.cell_width
    ch = int(round(cw * src_size[1] / src_size[0]))

    for sheet_idx in range((len(shots) + per_sheet - 1) // per_sheet):
        sheet_shots = shots[sheet_idx * per_sheet:(sheet_idx + 1) * per_sheet]
        sheet = Image.new("RGB", (args.cols * cw, args.rows * (ch + 24)), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, shot in enumerate(sheet_shots):
            x = (i % args.cols) * cw
            y = (i // args.cols) * (ch + 24)
            xc = xc_map.get(shot["idx"], 0.5)
            mid_s = (shot["start_s_adj"] + shot["end_s"]) / 2.0
            tmp_png = tmp_dir / f"shot_{shot['idx']:04d}.png"
            try:
                extract_frame(args.video, mid_s, str(tmp_png), max_width=cw)
                thumb = Image.open(tmp_png).convert("RGB").resize((cw, ch))
                thumb = draw_guide(thumb, xc, src_size)
            except Exception as e:
                thumb = Image.new("RGB", (cw, ch), (80, 0, 0))
                ImageDraw.Draw(thumb).text((5, 5), str(e)[:60], fill="white", font=font)
            sheet.paste(thumb, (x, y))
            label = (f"#{shot['idx']}  {shot['start_s_adj']:.2f}-{shot['end_s']:.2f}  "
                     f"{shot['duration_s_adj']:.2f}s  xc={xc}")
            d.rectangle([x, y + ch, x + cw, y + ch + 24], fill=(0, 0, 0))
            d.text((x + 4, y + ch + 3), label, fill="white", font=font)
        out_path = out_dir / f"sheet_{sheet_idx:02d}.png"
        sheet.save(out_path)
        print(f"wrote {out_path}  ({len(sheet_shots)} shots)")


def recheck_sheets(args):
    """Rendered 9:16 crops at 20/50/80% through each shot, one row per shot."""
    with open(args.plan, encoding="utf-8") as f:
        rows = json.load(f)["assigned"]
    out_dir = Path(args.out_dir)
    tmp_dir = out_dir / "_frames"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    font = load_font(16)

    tw = 180
    th = 320
    label_w = 230
    per_sheet = args.recheck_rows
    for sheet_idx in range((len(rows) + per_sheet - 1) // per_sheet):
        part = rows[sheet_idx * per_sheet:(sheet_idx + 1) * per_sheet]
        sheet = Image.new("RGB", (label_w + 3 * tw, len(part) * (th + 6)), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for r, row in enumerate(part):
            y = r * (th + 6)
            src = (f"ON-CAMERA\nsrc {row['src_start_s']}s" if row.get("aroll")
                   else f"shot #{row['shot_idx']}")
            d.text((6, y + 6), f"[{r + sheet_idx * per_sheet:02d}] {row['name']}\n"
                               f"{src}\nspeed {row['speed']}\n"
                               f"xc {row['xc']}", fill="white", font=font)
            for c, frac in enumerate((0.2, 0.5, 0.8)):
                tmp_png = tmp_dir / f"recheck_{r + sheet_idx * per_sheet:02d}_{c}.png"
                try:
                    extract_frame(row["out_path"], frac * float(row["out_dur"]),
                                  str(tmp_png), max_width=tw)
                    thumb = Image.open(tmp_png).convert("RGB").resize((tw, th))
                except Exception as e:
                    thumb = Image.new("RGB", (tw, th), (80, 0, 0))
                td = ImageDraw.Draw(thumb, "RGBA")
                td.rectangle([0, int(th * (1 - CAPTION_ZONE)), tw, th], fill=(255, 0, 0, 45))
                cy = int(th * CAPTION_Y)
                td.line([0, cy, tw, cy], fill=(255, 215, 0, 255), width=1)
                sheet.paste(thumb, (label_w + c * tw, y))
                d.text((label_w + c * tw + 4, y + 4), f"{int(frac * 100)}%", fill="yellow", font=font)
        out_path = out_dir / f"recheck_{sheet_idx:02d}.png"
        sheet.save(out_path)
        print(f"wrote {out_path}  ({len(part)} shots)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", help="scene pack (mode 1)")
    ap.add_argument("--shots", help="JSON from scene_detect.py (mode 1)")
    ap.add_argument("--xc-json", help="optional {shot idx: xc} map (mode 1)")
    ap.add_argument("--plan", help="shot_plan.json from render_shots.py (mode 2)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--cell-width", type=int, default=360)
    ap.add_argument("--recheck-rows", type=int, default=6)
    args = ap.parse_args()

    if args.plan:
        recheck_sheets(args)
    elif args.video and args.shots:
        midframe_sheets(args)
    else:
        ap.error("give --video and --shots (midframe sheets) or --plan (re-check sheets)")


if __name__ == "__main__":
    main()
