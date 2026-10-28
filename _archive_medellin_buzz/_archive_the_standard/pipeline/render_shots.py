"""
The Standard — Steps 7+8: Shot assignment, reframe, speed-ramp, grade

CLAUDE.md v2.4 §Pipeline Steps 7 & 8 (source of truth)

- Output: 1080x1920, 30fps, H.264 yuv420p. No blurred background, no letterbox.
- Per-shot ffmpeg filter chain (sources not exactly 1080 tall are first
  scaled to 1080 tall so the 608x1080 crop frames the same way):
    [hqdn3d,]                    (low-res sources only, see "enhance")
    [scale=-2:1080,]
    setpts=(PTS-STARTPTS)/SPEED,
    minterpolate=mi_mode=blend, fps=30,      (b-roll only)
    crop=608:1080:X:0,
    scale=1080:1920:flags=lanczos,
    [unsharp,]                   (low-res sources only)
    lut3d=file=<standard.cube>,
    setsar=1,
    format=yuv420p,
    tpad=stop_mode=clone
- Crop math: X = xc * W - 304, clamped 0..W-608 (W = source width at 1080
  tall; 1920 -> 0..1312).
- B-roll speed: fixed per shot. Default 0.5x; hook 0.64x; fast action
  0.6-0.7x via the segment's "speed". The source is trimmed to out_dur * speed.
- On-camera (a-roll) segments show the subject giving the speech, in sync
  with the speech audio: always 1.0x, no minterpolate. Their source time is
  computed from cuts.json + the mix timeline, so lips match the words.
  An on-camera segment must sit inside ONE speech clip (it can't span a cut
  or the gap between clips).
- Enhance: sources under 1080 tall get a light denoise before upscaling and
  a light sharpen after (e.g. 480p speech footage). Override per segment
  with "enhance": true/false.
- ffmpeg gotchas:
    * `-t` must come BEFORE `-i` for slow-mo
    * minterpolate=mi_mode=blend + tpad=stop_mode=clone so slow-mo reaches
      the full frame count
    * --target-dur-s tpads the LAST frame of the concat so the b-roll
      length equals the audio length (minus the sign-off) exactly

Segments JSON: {"segments": [{
    "name": "hook",
    "out_dur_s": 2.9,
    "shot_idx": 12,            # b-roll: hand-picked shot from shots.json (optional;
                               #   without it, the next unused shot long enough)
    "src_offset_s": 0.4,       # b-roll: start this far into the shot (optional)
    "speed": 0.64,             # b-roll: optional (hook default 0.64, else 0.5)
    "hook": true,              # optional
    "aroll": true,             # on-camera speech shot (needs --cuts + --mix-stats)
    "video": "<path>",         # a-roll: optional, defaults to the clip's speech file
    "enhance": true,           # optional, default: source under 1080 tall
    "xc": 0.5                  # crop centre, OR keyframes [[t_out_s, xc], ...]
}]}
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


OUT_W, OUT_H = 1080, 1920
CROP_W = 608
FPS = 30
DEFAULT_SPEED = 0.5
HOOK_SPEED = 0.64
AROLL_EPS_S = 0.02     # timeline slack when fitting an a-roll segment in a clip
DENOISE = "hqdn3d=2:1.5:4:3"
SHARPEN = "unsharp=5:5:0.7:5:5:0.0"


def ff_path(p: str) -> str:
    """Path for use inside an ffmpeg filter option: forward slashes, colon escaped."""
    return str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:")


_sizes = {}


def probe_size(video: str) -> tuple:
    if video not in _sizes:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
            capture_output=True, text=True, check=True)
        w, h = r.stdout.strip().split(",")[:2]
        _sizes[video] = (int(w), int(h))
    return _sizes[video]


def scaled_width(src_w: int, src_h: int) -> int:
    """Source width after scaling to 1080 tall (even, as scale=-2 does)."""
    w = int(round(src_w * 1080 / src_h))
    return w - (w % 2)


def xc_to_X(xc: float, width: int) -> int:
    X = int(round(xc * width - CROP_W / 2))
    return max(0, min(width - CROP_W, X))


def crop_x_expr(xc, width: int) -> str:
    """Crop x: a number, or a per-frame piecewise-linear expression of t."""
    if not isinstance(xc, list):
        return str(xc_to_X(float(xc), width))
    pts = sorted((float(t), float(x)) for t, x in xc)
    if len(pts) == 1:
        return str(xc_to_X(pts[0][1], width))
    px = [(t, x * width - CROP_W / 2) for t, x in pts]
    expr = f"{px[-1][1]:.2f}"
    for (t0, x0), (t1, x1) in reversed(list(zip(px, px[1:]))):
        lerp = f"{x0:.2f}+({x1 - x0:.2f})*(t-{t0:.3f})/{max(1e-3, t1 - t0):.3f}"
        expr = f"if(lt(t\\,{t1:.3f})\\,{lerp}\\,{expr})"
    expr = f"if(lt(t\\,{px[0][0]:.3f})\\,{px[0][1]:.2f}\\,{expr})"
    return f"'clip({expr}\\,0\\,{width - CROP_W})'"


def render_shot(src_video: str, lut_path: str,
                src_start_s: float, src_avail_s: float,
                out_dur_s: float, speed: float, xc,
                out_path: str, aroll: bool = False, enhance=None) -> dict:
    """Render ONE shot: (scale) + speed + crop + scale + LUT, exactly out_dur_s."""
    src_w, src_h = probe_size(src_video)
    width = scaled_width(src_w, src_h) if src_h != 1080 else src_w
    if enhance is None:
        enhance = src_h < 1080
    need_src = out_dur_s * speed
    src_dur = min(need_src, src_avail_s)

    pre = DENOISE + "," if enhance else ""
    pre += "scale=-2:1080:flags=lanczos," if src_h != 1080 else ""
    if aroll:
        timing = f"setpts=PTS-STARTPTS,fps={FPS},"
    else:
        timing = (f"setpts=(PTS-STARTPTS)/{speed},"
                  f"minterpolate=mi_mode=blend:fps={FPS},"
                  f"fps={FPS},")
    vf = (
        f"{pre}{timing}"
        f"crop={CROP_W}:1080:{crop_x_expr(xc, width)}:0,"
        f"scale={OUT_W}:{OUT_H}:flags=lanczos,"
        f"{SHARPEN + ',' if enhance else ''}"
        f"lut3d=file='{ff_path(lut_path)}',"
        f"setsar=1,"
        f"format=yuv420p,"
        f"tpad=stop_mode=clone:stop_duration={out_dur_s + 0.5}"
    )

    # Pre -i: -ss and -t (-t must be BEFORE -i for slow-mo)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{src_start_s:.3f}", "-t", f"{src_dur:.3f}",
        "-i", src_video,
        "-vf", vf,
        "-t", f"{out_dur_s:.3f}",     # Post-i -t clamps the OUTPUT to exact length
        "-r", str(FPS),
        "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-pix_fmt", "yuv420p",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "ok": r.returncode == 0,
        "stderr": r.stderr[-500:],
        "src_dur": round(src_dur, 3),
        "frozen_s": round(max(0.0, (need_src - src_avail_s) / speed), 3),
        "out_dur": round(out_dur_s, 3),
        "speed": speed,
        "enhance": enhance,
        "xc": xc,
    }


def assign_shots(shots: list, segments: list) -> list:
    """B-roll: hand-picked shot_idx wins; otherwise the next unused shot long enough."""
    by_idx = {s["idx"]: s for s in shots}
    used = {seg["shot_idx"] for seg in segments if "shot_idx" in seg}
    cursor = 0
    assigned = []
    for seg in segments:
        speed = seg.get("speed", HOOK_SPEED if seg.get("hook") else DEFAULT_SPEED)
        need = seg["out_dur_s"] * speed
        if "shot_idx" in seg:
            s = by_idx[seg["shot_idx"]]
        else:
            s = None
            while cursor < len(shots):
                cand = shots[cursor]
                cursor += 1
                if cand["idx"] not in used and cand["duration_s_adj"] >= need:
                    s = cand
                    break
            if s is None:
                raise RuntimeError(f"ran out of shots at segment {seg['name']}")
        used.add(s["idx"])
        offset = seg.get("src_offset_s", 0.0)
        assigned.append({
            **seg,
            "speed": speed,
            "shot_idx": s["idx"],
            "src_start_s": round(s["start_s_adj"] + offset, 3),
            "src_avail_s": round(s["end_s"] - s["start_s_adj"] - offset, 3),
        })
    return assigned


def assign_aroll(seg: dict, t0: float, clips: list, clip_starts: list,
                 clip_durs: list = None) -> dict:
    """Map an on-camera segment at timeline t0 to the speech source, in sync.

    The segment must sit inside one speech clip: its source time is that
    clip's source start plus how far into the clip the segment begins.
    Clip lengths come from the mix (clip_durs_s) when available.
    """
    t1 = t0 + seg["out_dur_s"]
    if not clip_durs:
        clip_durs = [c["end_s"] - c["start_s"] for c in clips]
    for i, (c, cs, cd) in enumerate(zip(clips, clip_starts, clip_durs)):
        ce = cs + cd
        if cs - AROLL_EPS_S <= t0 and t1 <= ce + AROLL_EPS_S:
            into = max(0.0, t0 - cs)
            video = seg.get("video") or c.get("src_path")
            if not video:
                raise RuntimeError(f"a-roll {seg['name']}: no video path (re-run cut_speech.py "
                                   f"so cuts.json has src_path, or set \"video\")")
            return {**seg, "speed": 1.0, "shot_idx": None, "video": video, "clip_idx": i,
                    "src_start_s": round(c["start_s"] + into, 3),
                    "src_avail_s": round(c["end_s"] - c["start_s"] - into + 0.5, 3)}
    spans = ", ".join(f"clip {i}: {cs:.2f}-{cs + cd:.2f}s"
                      for i, (cs, cd) in enumerate(zip(clip_starts, clip_durs)))
    raise RuntimeError(f"a-roll {seg['name']} ({t0:.2f}-{t1:.2f}s on the timeline) is not inside "
                       f"one speech clip. Move or split it at a clip edge. Clips: {spans}")


# ---------------------------------------------------------------------------
# v3.0 (CLAUDE.md v3.0 Step 6/7) — opt-in with --format v3.
# Segment types: broll (src file in Scene Pack, standard.cube), still (photo,
# slow push-in 1.0 -> 1.08 toward "focus", era look from looks.json), graphic
# (cut from the HyperFrames reel by graphics_plan.json, not graded).
# ---------------------------------------------------------------------------
PUSH_TO = 1.08


def render_still_v3(src: str, look_chain: str, out_dur_s: float, focus, out_path: str) -> dict:
    fx, fy = focus
    n = max(1, int(round(out_dur_s * FPS)))
    vf = (f"scale={OUT_W * 2}:{OUT_H * 2}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={OUT_W * 2}:{OUT_H * 2}:(iw-ow)*{fx}:(ih-oh)*{fy},"
          f"zoompan=z='1+{PUSH_TO - 1}*on/{n}':x='(iw-iw/zoom)*{fx}':y='(ih-ih/zoom)*{fy}':"
          f"d={n}:s={OUT_W}x{OUT_H}:fps={FPS},"
          f"{look_chain},setsar=1,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", src,
           "-vf", vf, "-frames:v", str(n), "-r", str(FPS), "-an",
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": r.returncode == 0, "stderr": r.stderr[-500:], "out_dur": round(n / FPS, 3)}


def cut_graphic_v3(reel: str, start_s: float, out_dur_s: float, out_path: str) -> dict:
    n = max(1, int(round(out_dur_s * FPS)))
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start_s:.3f}", "-i", reel,
           "-vf", f"fps={FPS},setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=1",
           "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "16",
           "-pix_fmt", "yuv420p", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": r.returncode == 0, "stderr": r.stderr[-500:], "out_dur": round(n / FPS, 3)}


def media_duration(p: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", p], capture_output=True, text=True)
    return float(r.stdout.strip())


def main_v3(args) -> None:
    segs_doc = json.load(open(args.segments, encoding="utf-8"))
    if segs_doc.get("format") != "v3":
        print("ERROR: --format v3 but segments.json has no \"format\": \"v3\"", file=sys.stderr)
        sys.exit(2)
    looks = json.load(open(Path(__file__).resolve().parent / "looks" / "looks.json", encoding="utf-8"))
    plan = json.load(open(args.graphics_plan, encoding="utf-8"))
    reel_at = {b["name"]: b["reel_start_s"] for b in plan["beats"]}
    scene = Path(args.scene_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    concat_list = out_dir / "_concat.txt"
    rows, t0 = [], 0.0
    # Frame-exact cuts: each segment ends on the frame nearest its timeline end
    with open(concat_list, "w", encoding="utf-8") as cf:
        for i, seg in enumerate(segs_doc["segments"]):
            start_f = int(round(seg["tl_start_s"] * FPS))
            end_f = int(round((seg["tl_start_s"] + seg["out_dur_s"]) * FPS))
            dur = (end_f - start_f) / FPS
            out_path = out_dir / f"{i:02d}_{seg['name']}.mp4"
            kind = seg["type"]
            if kind == "broll":
                src = str(scene / seg["src"])
                off = seg.get("src_offset_s", 0.0)
                res = render_shot(src, args.lut, off, media_duration(src) - off, dur,
                                  seg.get("speed", DEFAULT_SPEED), seg.get("xc", 0.5), str(out_path),
                                  enhance=seg.get("enhance"))
            elif kind == "still":
                res = render_still_v3(str(scene / seg["src"]), looks[seg.get("grade", "bw_film")],
                                      dur, seg.get("focus", [0.5, 0.5]), str(out_path))
            elif kind == "graphic":
                res = cut_graphic_v3(args.graphics_reel, reel_at[seg["reel"]], dur, str(out_path))
            else:
                print(f"ERROR: segment type '{kind}' not supported", file=sys.stderr)
                sys.exit(2)
            if not res["ok"]:
                print(f"  [{i:02d}] {seg['name']} FAILED: {res['stderr']}")
                sys.exit(2)
            warn = f"  ! frozen {res['frozen_s']}s" if res.get("frozen_s", 0) > 0.1 else ""
            print(f"  [{i:02d}] {seg['name']:<12s} @{seg['tl_start_s']:6.2f}s {kind:<8s} {dur:5.2f}s{warn}")
            cf.write(f"file '{out_path.name}'\n")
            rows.append({**seg, **res, "out_path": str(out_path)})
    concat_cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                  "-i", str(concat_list)]
    if args.target_dur_s:
        concat_cmd += ["-vf", "tpad=stop_mode=clone:stop_duration=2", "-t", f"{args.target_dur_s:.3f}"]
    concat_cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
                   "-r", str(FPS), "-an", args.concat_out]
    r = subprocess.run(concat_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("concat failed:", r.stderr)
        sys.exit(2)
    json.dump({"format": "v3", "assigned": rows}, open(out_dir / "shot_plan.json", "w", encoding="utf-8"),
              indent=2, default=str)
    print(f"wrote {args.concat_out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", help="scene pack video (b-roll; v2.4)")
    ap.add_argument("--shots", help="shots.json from scene_detect (v2.4)")
    ap.add_argument("--format", default="v2.4", choices=["v2.4", "v3"])
    ap.add_argument("--scene-dir", help="v3: <Subject>/Scene Pack (segment src paths are relative to it)")
    ap.add_argument("--graphics-reel", help="v3: rendered HyperFrames reel mp4")
    ap.add_argument("--graphics-plan", help="v3: graphics_plan.json (reel start of each graphic beat)")
    ap.add_argument("--segments", required=True, help="JSON list of output segments")
    ap.add_argument("--lut", required=True, help="standard.cube path")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--concat-out", required=True, help="Final concat mp4")
    ap.add_argument("--default-xc", type=float, default=0.5)
    ap.add_argument("--target-dur-s", type=float, default=None,
                    help="pad/trim the concat to exactly this length (audio length minus sign-off)")
    ap.add_argument("--cuts", help="cuts.json from cut_speech (needed for a-roll)")
    ap.add_argument("--mix-stats", help="mix_audio --debug-json output (needed for a-roll)")
    args = ap.parse_args()
    if args.format == "v3":
        main_v3(args)
        return
    if not (args.video and args.shots):
        ap.error("--video and --shots are required for v2.4")

    with open(args.shots, encoding="utf-8") as f:
        shots = json.load(f)["shots"]
    with open(args.segments, encoding="utf-8") as f:
        segments = json.load(f)["segments"]
    for seg in segments:
        seg.setdefault("xc", args.default_xc)

    clips = clip_starts = clip_durs = None
    if any(s.get("aroll") for s in segments):
        if not (args.cuts and args.mix_stats):
            print("ERROR: a-roll segments need --cuts and --mix-stats", file=sys.stderr)
            sys.exit(2)
        with open(args.cuts, encoding="utf-8") as f:
            clips = json.load(f)["clips"]
        with open(args.mix_stats, encoding="utf-8") as f:
            mix_stats = json.load(f)
        clip_starts = mix_stats["clip_starts_s"]
        clip_durs = mix_stats.get("clip_durs_s")

    # Timeline start of each segment = sum of the previous out_dur_s
    starts = []
    t = 0.0
    for seg in segments:
        starts.append(t)
        t += seg["out_dur_s"]

    broll = [s for s in segments if not s.get("aroll")]
    broll_assigned = iter(assign_shots(shots, broll))
    try:
        assigned = [assign_aroll(s, t0, clips, clip_starts, clip_durs) if s.get("aroll")
                    else next(broll_assigned)
                    for s, t0 in zip(segments, starts)]
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    for v in {args.video, *(a["video"] for a in assigned if a.get("aroll"))}:
        w, h = probe_size(v)
        if h != 1080:
            print(f"{Path(v).name}: {w}x{h} -> scaled to 1080 tall before the crop"
                  + (" (+ denoise/sharpen)" if h < 1080 else ""))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    concat_list = out_dir / "_concat.txt"
    rows = []

    with open(concat_list, "w", encoding="utf-8") as cf:
        for i, (seg, t0) in enumerate(zip(assigned, starts)):
            name = seg["name"]
            out_path = out_dir / f"{i:02d}_{name}.mp4"
            res = render_shot(
                src_video=seg.get("video") if seg.get("aroll") else args.video,
                lut_path=args.lut,
                src_start_s=seg["src_start_s"], src_avail_s=seg["src_avail_s"],
                out_dur_s=seg["out_dur_s"], speed=seg["speed"], xc=seg["xc"],
                out_path=str(out_path), aroll=bool(seg.get("aroll")),
                enhance=seg.get("enhance"),
            )
            rows.append({**seg, **res, "timeline_start_s": round(t0, 3), "out_path": str(out_path)})
            if res["ok"]:
                cf.write(f"file '{out_path.name}'\n")
                warn = f"  ! shot too short, last {res['frozen_s']}s frozen" if res["frozen_s"] > 0.1 else ""
                what = (f"ON-CAMERA clip {seg['clip_idx']} src {seg['src_start_s']:.2f}s"
                        if seg.get("aroll") else f"shot#{seg['shot_idx']}")
                print(f"  [{i:02d}] {name:<14s} @{t0:6.2f}s  {what:<34s} "
                      f"out={res['out_dur']:.2f}s speed={res['speed']} xc={res['xc']}{warn}")
            else:
                print(f"  [{i:02d}] {name} FAILED: {res['stderr']}")
                sys.exit(2)

    # Concat (+ pad the last frame so b-roll length == audio length)
    print("\nConcatenating ...")
    concat_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
    ]
    if args.target_dur_s:
        concat_cmd += ["-vf", "tpad=stop_mode=clone:stop_duration=2",
                       "-t", f"{args.target_dur_s:.3f}"]
    concat_cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-an",
        args.concat_out,
    ]
    r = subprocess.run(concat_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("concat failed:", r.stderr)
        sys.exit(2)
    print(f"wrote {args.concat_out}")

    plan_json = out_dir / "shot_plan.json"
    with open(plan_json, "w", encoding="utf-8") as f:
        json.dump({"video": args.video, "assigned": rows}, f, indent=2, default=str)
    print(f"wrote {plan_json}")


if __name__ == "__main__":
    main()
