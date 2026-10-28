r"""
Buzz Media kit — step 1 inventory (CLAUDE.md §5 step 1).

ffprobes every video in a project (raw\ + broll\, plus a long-form if there is one), lists the stills in
assets\ and broll\, and writes <project>\working\inventory.json with duration, resolution, fps, orientation,
audio, plus flags: vertical, under 1080p, variable frame rate, no audio, a narrow 9:16 crop (landscape footage whose
crop is under 1080 px wide: 1080p gives 606 px, scaled up 1.78x), and a likely screen-recorder copy (written by an
ffmpeg-based recorder such as OBS: .mkv/.flv, "Lavf" encoder, "Track1" audio, no camera metadata). Each flag adds a
line to "ask_client": what to request in the first reply (the camera original, 4K, or vertical).

Usage:
  python pipeline/inventory.py --project clients/<client>/projects/<project>
  (archived layout: --input "input/el hueco" --slug el-hueco --longform "....mp4" --script "....docx")
  --out <file>: write the inventory somewhere else (default <project>\working\inventory.json)
"""
import argparse
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".m4v"}
STILL_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def probe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"file": str(path), "error": r.stderr.strip()}
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = [s for s in d["streams"] if s["codec_type"] == "audio"]
    info = {"file": path.as_posix(), "size_mb": round(int(d["format"]["size"]) / 1e6, 1),
            "duration_s": round(float(d["format"].get("duration", 0)), 3),
            "creation_time": d["format"].get("tags", {}).get("creation_time")}
    flags = []
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []):
            if "rotation" in sd:
                rot = int(sd["rotation"])
        if abs(rot) in (90, 270):
            w, h = h, w
        r_fps = float(Fraction(v.get("r_frame_rate", "0/1")))
        avg_fps = float(Fraction(v.get("avg_frame_rate", "0/1"))) if v.get("avg_frame_rate", "0/0") != "0/0" else 0
        info.update({"width": w, "height": h, "rotation": rot,
                     "orientation": "vertical" if h > w else "horizontal",
                     "fps": round(r_fps, 3), "avg_fps": round(avg_fps, 3),
                     "vcodec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
                     "bit_depth": v.get("bits_per_raw_sample"),
                     "color_transfer": v.get("color_transfer"), "color_primaries": v.get("color_primaries")})
        if h > w:
            flags.append("vertical")
        if min(w, h) < 1080:
            flags.append("under_1080p")
        if avg_fps and abs(r_fps - avg_fps) > 0.05:
            flags.append("possible_vfr")
        if v.get("color_transfer") in ("arib-std-b67", "smpte2084"):
            flags.append("hdr_or_log_transfer")
        if w > h:
            crop_w = int(h * 9 / 16) // 2 * 2
            info["crop_9x16_w"] = crop_w
            if crop_w < 1080:
                flags.append(f"narrow_9x16_crop_{crop_w}px")
        tags = {k.lower(): str(val) for k, val in d["format"].get("tags", {}).items()}
        a_titles = [str(s.get("tags", {}).get("title", "")) for s in a]
        camera = any(k in tags for k in ("com.apple.quicktime.make", "make", "model", "com.android.manufacturer")) \
            or any("handler_name" in s.get("tags", {}) and "core media" in str(s["tags"]["handler_name"]).lower()
                   for s in d["streams"])
        recorder = [why for why, hit in (
            (f"{path.suffix} container", path.suffix.lower() in (".mkv", ".flv")),
            (f"encoder {tags.get('encoder')}", any(x in tags.get("encoder", "").lower() for x in ("lavf", "obs"))),
            ("audio track 'Track1'", any(t.lower().startswith("track") for t in a_titles)),
            ("no camera metadata", not camera)) if hit]
        if len(recorder) >= 2 and not camera:
            flags.append("screen_recorder_copy?")
            info["recorder_signs"] = recorder
    else:
        flags.append("no_video")
    info["audio"] = [{"codec": s.get("codec_name"), "channels": s.get("channels"),
                      "sample_rate": s.get("sample_rate")} for s in a]
    if not a:
        flags.append("no_audio")
    info["flags"] = flags
    return info


def ask_client(i):
    """What to request in the first reply for a flagged file (CLAUDE.md §5 step 1)."""
    name, out = Path(i["file"]).name, []
    narrow = next((f for f in i.get("flags", []) if f.startswith("narrow_9x16_crop")), None)
    if "screen_recorder_copy?" in i.get("flags", []):
        out.append(f"{name}: looks like a screen-recorder copy ({', '.join(i['recorder_signs'])}). Ask for the camera's "
                   f"original file (straight off the card or phone), which is usually 4K and sharper.")
    if narrow:
        out.append(f"{name}: {i['width']}x{i['height']} landscape, so the 9:16 crop is only {i['crop_9x16_w']} px wide "
                   f"(scaled up {1080 / i['crop_9x16_w']:.2f}x, soft; punch-ins cost more). Ask for 4K or vertical "
                   f"footage; meanwhile prefer split-screen layouts and keep punch-ins <= 1.08.")
    if "under_1080p" in i.get("flags", []):
        out.append(f"{name}: under 1080p. Ask for a higher-resolution copy.")
    if "no_audio" in i.get("flags", []):
        out.append(f"{name}: no audio track. Ask whether there's a separate audio recording.")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", help="clients/<client>/projects/<project>")
    ap.add_argument("--input", help="archived layout only")
    ap.add_argument("--slug", help="archived layout only")
    ap.add_argument("--longform", default="longform.mp4")
    ap.add_argument("--script", default="script.md")
    ap.add_argument("--out", help="write the inventory here instead of <project>\\working\\inventory.json")
    a = ap.parse_args()

    proj = kit.Project(project_dir=a.project) if a.project else kit.Project({"input_dir": a.input}, slug=a.slug)
    root = proj.input
    inv = {"slug": a.slug or Path(a.project).name, "input": root.as_posix(), "missing": []}
    lf = root / a.longform
    inv["longform"] = probe(lf) if lf.exists() else None
    if not lf.exists() and not a.project:          # client projects usually have no long-form
        inv["missing"].append(a.longform)
    sc = root / a.script
    inv["script"] = sc.as_posix() if sc.exists() else None
    if not sc.exists() and not a.project:
        inv["missing"].append(a.script)
    for sub in ("raw", "broll"):
        d = root / sub
        files = sorted(p for p in d.iterdir() if p.suffix.lower() in VIDEO_EXT) if d.is_dir() else []
        inv[sub] = [probe(p) for p in files]
        if not files and not (d.is_dir() and any(p.suffix.lower() in STILL_EXT for p in d.iterdir())):
            inv["missing"].append(sub + "\\")        # a broll\ of screenshots only isn't missing
    inv["stills"] = [p.relative_to(root).as_posix() for sub in ("assets", "broll") if (root / sub).is_dir()
                     for p in sorted((root / sub).iterdir()) if p.suffix.lower() in STILL_EXT]
    for sub in ("sfx", "music"):
        inv[sub] = str(proj.library(sub)) if a.project else (root / sub).is_dir()

    inv["ask_client"] = [x for sub in ("raw", "broll") for i in inv[sub] for x in ask_client(i)]
    out = Path(a.out) if a.out else proj.working / "inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")

    def line(i):
        if "error" in i:
            return f"  {Path(i['file']).name}: ERROR {i['error']}"
        return (f"  {Path(i['file']).name:34s} {i['duration_s']:8.1f}s {i.get('width')}x{i.get('height')} "
                f"{i.get('fps')}fps {i.get('vcodec')} {i.get('pix_fmt')} {i.get('color_transfer')} "
                f"audio={[x['channels'] for x in i['audio']]} {','.join(i['flags'])}")
    print("longform:")
    if inv["longform"]:
        print(line(inv["longform"]))
    for sub in ("raw", "broll"):
        tot = sum(i.get("duration_s", 0) for i in inv[sub])
        print(f"{sub}: {len(inv[sub])} files, {tot / 60:.1f} min")
        for i in inv[sub]:
            print(line(i))
    print(f"stills: {len(inv['stills'])}", *inv["stills"], sep="\n  ")
    print("missing:", inv["missing"] or "nothing")
    print("ask the client (first reply):", *(inv["ask_client"] or ["nothing"]), sep="\n  ")
    print("wrote", out)


if __name__ == "__main__":
    main()
