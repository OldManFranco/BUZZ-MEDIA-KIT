r"""
Buzz Media kit — step 6: render an approved EDL (CLAUDE.md §5 step 6). Paths come from kit.Project(edl).

  python pipeline/render_short.py clients/<client>/projects/<project>/working/plans/s1_edl.json --name <title-slug>
         [--stage picture|audio|captions|graphics|final|all]

Stages (each reuses the previous stage's files in <project>\working\render\<short>\):
  picture   frame-exact 30 fps timeline: A-roll cropped 9:16 around the speaker's eyes (faces.json from
            face_track.py; any source size), punch-ins, B-roll cut-ins; graded with the EDL's "grade" .cube
            (or <project>\working\grade\longform_match.cube if present; no grade otherwise) -> picture.mp4
  audio     voice spliced sample-exact from the raw clips (5 ms fades at splices, segment levels matched),
            cleaned (HPF 80 Hz, light de-noise, 2:1 comp) -> voice.wav; + B-roll natural sound + SFX,
            two-pass loudnorm to -14 LUFS / -1.5 dBTP -> mix.wav
  captions  WhisperX on voice.wav (the kit's tools\venv_whisperx) -> voice.words.json for the karaoke captions
  graphics  "graphics_engine": "hyperframes" EDLs only: title cards, chips and data cards as a HyperFrames
            project, checked and rendered transparent -> graphics.mov (build_graphics.py)
  final     picture.mp4 + graphics.mov (if any) + the Pillow layer (build_captions.py: karaoke captions, and
            the title card/chips for older "pillow" EDLs) + mix.wav
            -> <project>\output\<slug>-<short>_<name>.mp4 (1080x1920, 30 fps, H.264 yuv420p, AAC 48 kHz)
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

FPS, SR = 30, 48000
OUT_W, OUT_H = 1080, 1920
EYES_TARGET = 0.37            # eyes at 37% from the top on punch-ins (CLAUDE.md §6: 35-40%)
SFX = {  # short names -> files inside the SFX library (catalogo_sfx.json entries, plus the synthesized _synth\)
    "ui_pop": "ui_pop/px_s_348820_pop_sfx_soft_subtle_ui.mp3",
    "whoosh": "whoosh/mk_s_166_fast_small_sweep_transition.wav",
    "impacto": "_synth/soft_hit.wav",
}


def sfx_file(edl, name):
    r"""An EDL "sfx" is a short name (SFX) or a path inside the library; the client's sfx\ wins when non-empty."""
    rel = SFX.get(name, name)
    for lib in (kit.Project(edl).library("sfx"), kit.ROOT / "sfx"):
        if (lib / rel).is_file():
            return lib / rel
    return None


def grade_file(edl):
    g = edl.get("grade")
    if g:
        return Path(g)
    auto = kit.Project(edl).working / "grade" / "longform_match.cube"
    return auto if auto.exists() else None


_sizes = {}


def src_size(src):
    if str(src) not in _sizes:
        out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                   "-of", "csv=p=0", str(src)]).stdout.strip().split(",")
        _sizes[str(src)] = (int(out[0]), int(out[1]))
    return _sizes[str(src)]
STILL_EXT = {".png", ".jpg", ".jpeg"}


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(map(str, cmd))[:400]}\n{r.stderr[-2000:]}")
    return r


def fr(t):
    return int(round(t * FPS))


# ---------------------------------------------------------------- picture

def picture_plan(edl, faces):
    """One entry per output frame range: what to show and how to crop it."""
    arolls = [e for e in edl["events"] if e["kind"] == "aroll"]
    ov = [e for e in edl["events"] if e["kind"] not in ("aroll", "ending")]
    hold = next((e["hold_s"] for e in edl["events"] if e["kind"] == "ending"), 0.0)
    # frame-exact A-roll pieces (cumulative, so rounding never drifts)
    pieces, t = [], 0.0
    for i, e in enumerate(arolls):
        dur = e["out"] - e["in"] + (hold if i == len(arolls) - 1 else 0.0)
        pieces.append({"i": i, "seg": e["seg"], "src": e["src"], "in": e["in"], "f0": fr(t), "f1": fr(t + dur),
                       "key": f"{e['src']}|{e['in']}|{e['out']}", "reframe": e.get("reframe") or {}})
        t += dur
    n = pieces[-1]["f1"]
    seg_end = {}
    for p in pieces:
        seg_end[p["seg"]] = max(seg_end.get(p["seg"], 0), p["f1"])

    # one crop per segment (median of its pieces): per-piece centers would jitter at every pause cut
    seg_face = {}
    for s in {p["seg"] for p in pieces}:
        fs = [faces[p["key"]] for p in pieces if p["seg"] == s and faces.get(p["key"], {}).get("n")]
        if fs:
            seg_face[s] = {k: float(np.median([f[k] for f in fs])) for k in ("eyes_x", "eyes_y")}
    frames = []
    for p in pieces:
        face = seg_face.get(p["seg"], {})
        for f in range(p["f0"], p["f1"]):
            lock = p["reframe"].get("lock")
            xc = p["reframe"]["xc"] if lock else face.get("eyes_x", p["reframe"].get("xc", 0.5))
            scale = p["reframe"].get("punch", 1.0)
            frames.append({"kind": "aroll", "piece": p["i"], "src": p["src"], "t": p["in"] + (f - p["f0"]) / FPS,
                           "xc": xc, "scale": scale, "eyes_y": face.get("eyes_y", 0.36), "seg": p["seg"],
                           "lock": bool(lock)})
    for o in sorted(ov, key=lambda o: o["t"]):
        f0 = fr(o["t"])
        if o["kind"] == "reframe":            # a locked framing (e.g. the shirt) hands over to the face
            seg = frames[f0]["seg"]
            for f in range(f0, seg_end[seg]):
                if frames[f]["kind"] == "aroll" and frames[f]["seg"] == seg:
                    # the locked segment's own median includes the shirt-framed piece; use the face pieces only
                    face = faces.get(next(p["key"] for p in pieces if p["i"] == frames[f]["piece"]), {})
                    fx = [faces[p["key"]]["eyes_x"] for p in pieces if p["seg"] == seg and p["f1"] > f0
                          and faces.get(p["key"], {}).get("n")]
                    frames[f]["xc"] = (float(np.median(fx)) if fx else face.get("eyes_x", 0.5)) \
                        if o.get("to") == "face" else o["xc"]
                    frames[f]["lock"] = False
        elif o["kind"] == "punch_in":          # holds to the end of that segment
            seg = frames[f0]["seg"]
            for f in range(f0, seg_end[seg]):
                if frames[f]["kind"] == "aroll":
                    frames[f]["scale"] = max(frames[f]["scale"], o["scale"])
    for o in ov:
        if o["kind"] != "broll":
            continue
        f0, f1 = fr(o["t"]), min(fr(o["t_out"]), n)
        for f in range(f0, f1):
            frames[f] = {"kind": "broll", "piece": f"b{f0}", "src": o["src"], "t": o.get("in", 0.0) + (f - f0) / FPS,
                         "xc": o.get("xc", 0.5), "scale": 1.0, "eyes_y": 0.5, "seg": None, "lock": True}
    # no visible shot shorter than 0.4 s: a sliver left by a punch-in or a B-roll edge takes its neighbor's look
    MIN = int(0.4 * FPS)
    for _ in range(3):
        runs = group(frames)
        for k, r in enumerate(runs):
            if r["n"] >= MIN or len(runs) == 1:
                continue
            prev = runs[k - 1] if k else None
            nxt = runs[k + 1] if k + 1 < len(runs) else None
            same = lambda o: o and (o["kind"] == "broll" or (o["kind"] == "aroll" and o["k"][0] == r["k"][0]))
            nb = prev if same(prev) else nxt if same(nxt) else None
            if nb is None:
                continue                      # a real jump cut between pieces at the same framing: fine
            for f in range(r["f0"], r["f0"] + r["n"]):
                if nb["kind"] == "broll":     # extend the B-roll shot, continuing its source time
                    base = frames[nb["f0"]]
                    frames[f] = dict(base, t=base["t"] + (f - nb["f0"]) / FPS)
                else:
                    frames[f] = dict(frames[f], xc=nb["xc"], scale=nb["scale"])
    return group(frames), n


def group(frames):
    """Consecutive frames with the same source piece and crop become one renderable run."""
    runs = []
    for f, x in enumerate(frames):
        k = (x["piece"], round(x["xc"], 4), x["scale"])
        if runs and runs[-1]["k"] == k:
            runs[-1]["n"] += 1
        else:
            runs.append({"k": k, "f0": f, "n": 1, **{a: x[a] for a in ("kind", "src", "t", "xc", "scale", "eyes_y")}})
    return runs


def crop_for(r, src_w, src_h):
    h = src_h / r["scale"]
    w = h * OUT_W / OUT_H
    x = min(max(r["xc"] * src_w - w / 2, 0), src_w - w)
    y = 0 if r["scale"] == 1.0 else min(max(r["eyes_y"] * src_h - EYES_TARGET * h, 0), src_h - h)
    ev = lambda v: int(v) // 2 * 2
    return ev(w), ev(h), ev(x), ev(y)


def stage_picture(edl, rd, inp):
    faces = json.loads((rd / "faces.json").read_text(encoding="utf-8"))
    runs, n = picture_plan(edl, faces)
    parts = rd / "parts"
    shutil.rmtree(parts, ignore_errors=True)
    parts.mkdir(parents=True)
    grade = grade_file(edl)
    lst = []
    for k, r in enumerate(runs):
        out = parts / f"p{k:03d}.mp4"
        src = Path(r["src"]) if Path(r["src"]).is_absolute() or Path(r["src"]).exists() else inp / r["src"]
        if src.suffix.lower() in STILL_EXT:
            # still image: 9:16 crop around xc, slow 4% push-in (EDL "push": -0.04 pulls out instead),
            # no grade (it isn't our camera)
            push = next((o.get("push", 0.04) for o in edl["events"] if o.get("src") == r["src"]), 0.04)
            z0 = 1.0 if push >= 0 else 1.0 - push
            vf = (f"scale=-2:{OUT_H + 80}:flags=lanczos,"
                  f"crop={(OUT_H + 80) * 9 // 16 // 2 * 2}:{OUT_H + 80}:"
                  f"'max(0,min(iw-ow,iw*{r['xc']}-ow/2))':0,"
                  f"zoompan=z='{z0}+({push})*on/{max(r['n'] - 1, 1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
                  f"d={r['n']}:s={OUT_W}x{OUT_H}:fps={FPS},format=yuv420p")
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf]
        else:
            w, h, x, y = crop_for(r, *src_size(src))
            lut = f"lut3d={grade.as_posix()}," if grade else ""
            vf = (f"crop={w}:{h}:{x}:{y},scale={OUT_W}:{OUT_H}:flags=lanczos,fps={FPS},"
                  f"{lut}format=yuv420p")
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{r['t']:.4f}", "-i", str(src), "-an", "-vf", vf]
        run(cmd + ["-frames:v", str(r["n"]), "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                   "-r", str(FPS), "-video_track_timescale", "15360", str(out)])
        lst.append(f"file '{out.name}'")
        print(f"  part {k:03d} f{r['f0']:5d}+{r['n']:3d} {r['kind']:5s} {Path(r['src']).name} @{r['t']:.2f} "
              f"xc={r['xc']:.2f} x{r['scale']}", flush=True)
    (parts / "list.txt").write_text("\n".join(lst) + "\n", encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(parts / "list.txt"),
         "-c", "copy", str(rd / "picture.mp4")])
    (rd / "picture_runs.json").write_text(json.dumps({"frames": n, "runs": runs}, indent=1), encoding="utf-8")
    print(f"picture.mp4: {n} frames ({n / FPS:.2f} s), {len(runs)} parts")


# ---------------------------------------------------------------- audio

_cache = {}


def load_audio(path):
    path = str(path)
    if path not in _cache:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True)
        _cache[path] = np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
    return _cache[path]


def fade(x, n_in, n_out):
    x = x.copy()
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
    return x


def place(bus, x, at):
    a = max(at, 0)
    x = x[a - at:]
    b = min(a + len(x), len(bus))
    bus[a:b] += x[: b - a]


def db(v):
    return 10 ** (v / 20)


def stage_audio(edl, rd, inp):
    pr = json.loads((rd / "picture_runs.json").read_text(encoding="utf-8"))
    n = pr["frames"]
    total = n * SR // FPS
    arolls = [e for e in edl["events"] if e["kind"] == "aroll"]
    hold = next((e["hold_s"] for e in edl["events"] if e["kind"] == "ending"), 0.0)
    # voice: same cumulative frame grid as the picture
    voice = np.zeros((total, 2), np.float32)
    slices, t = [], 0.0
    for i, e in enumerate(arolls):
        last = i == len(arolls) - 1
        dur = e["out"] - e["in"] + (hold if last else 0.0)
        f0, f1 = fr(t), fr(t + dur)
        src = load_audio(inp / e["src"])
        s0 = int(round(e["in"] * SR))
        x = src[s0: s0 + (f1 - f0) * SR // FPS]
        if last and hold:
            # the ending hold is picture only: Andrew's next word can start inside it (s2: "Sometimes"
            # 0.26 s after "works."), so the voice ends at the segment's out with a 60 ms fade
            k = int(round((e["out"] - e["in"]) * SR))
            x = np.concatenate([fade(x[:k], 0, int(0.06 * SR)), np.zeros_like(x[k:])])
        slices.append((e["seg"], f0 * SR // FPS, fade(x, 240, int(0.25 * SR) if last and not hold else 240)))
        t += dur
    # match levels between segments (speech RMS, ignoring quiet frames), max +-3 dB
    def speech_rms(x):
        fr_ = x[: len(x) // 960 * 960].reshape(-1, 960, 2)
        r = np.sqrt((fr_ ** 2).mean(axis=(1, 2)))
        r = r[r > 10 ** (-40 / 20)]
        return float(np.sqrt((r ** 2).mean())) if len(r) else None
    segs = {}
    for seg, _, x in slices:
        segs.setdefault(seg, []).append(x)
    lv = {s: speech_rms(np.concatenate(xs)) for s, xs in segs.items()}
    ref = float(np.median([v for v in lv.values() if v]))
    gains = {s: float(np.clip(20 * np.log10(ref / v), -3, 3)) if v else 0.0 for s, v in lv.items()}
    for seg, at, x in slices:
        place(voice, x * db(gains[seg]), at)
    raw_voice = rd / "voice_raw.f32"
    voice.tofile(raw_voice)
    run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw_voice),
         "-af", "highpass=f=80,afftdn=nr=6:nf=-40,acompressor=threshold=-20dB:ratio=2:attack=10:release=150",
         "-c:a", "pcm_f32le", str(rd / "voice.wav")])
    voice = load_audio(rd / "voice.wav")[:total]

    bus = np.zeros((total, 2), np.float32)
    place(bus, voice, 0)
    sfx_log = []
    for o in edl["events"]:
        if o["kind"] == "broll" and Path(o["src"]).suffix.lower() not in STILL_EXT:
            g = -24.0 if "-24" in o.get("audio", "") else -20.0
            src = load_audio(inp / o["src"])
            s0 = int(round(o["in"] * SR))
            L = int(round((o["t_out"] - o["t"]) * SR))
            place(bus, fade(src[s0: s0 + L], int(0.03 * SR), int(0.03 * SR)) * db(g), int(round(o["t"] * SR)))
        sfx = o.get("sfx")
        if o["kind"] in ("title_card", "chip", "broll") and sfx:
            name, level = sfx.split(" (")[0].split()[0], float(sfx.split()[-2])
            f = sfx_file(edl, name)
            if not f:
                print(f"  SFX '{name}' not found in the library, skipped")
                continue
            lead = 0.12 if o["kind"] == "broll" else 0.0
            place(bus, load_audio(f) * db(level), int(round((o["t"] - lead) * SR)))
            sfx_log.append({"t": round(o["t"] - lead, 2), "sfx": name, "file": str(f), "db": level})
    mixf = rd / "mix_pre.f32"
    bus.tofile(mixf)
    inp_args = ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(mixf)]
    r = run(["ffmpeg", "-hide_banner", "-nostats", *inp_args, "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", *inp_args, "-af", ln + f",aresample={SR}", "-c:a", "pcm_s24le",
         str(rd / "mix.wav")])
    (rd / "audio_log.json").write_text(json.dumps({"segment_gain_db": gains, "sfx": sfx_log,
                                                    "loudnorm_first_pass": m}, indent=1), encoding="utf-8")
    raw_voice.unlink()
    mixf.unlink()
    print(f"voice.wav + mix.wav ({total / SR:.2f} s); segment gains {gains}; {len(sfx_log)} SFX")


# ---------------------------------------------------------------- captions + final

def stage_captions(edl, rd):
    tdir = rd / "transcript"
    for f in tdir.glob("voice.*"):
        f.unlink()
    run([str(kit.WHISPERX_PY), "-I", str(kit.WHISPERX), str(rd / "voice.wav"), str(tdir)])
    print("wrote", tdir / "voice.words.json")


def stage_final(edl, rd, name):
    sys.path.insert(0, str(Path(__file__).parent))
    import build_captions
    pr = json.loads((rd / "picture_runs.json").read_text(encoding="utf-8"))
    n = pr["frames"]
    words = json.loads((rd / "transcript" / "voice.words.json").read_text(encoding="utf-8"))["words"]
    layer = build_captions.Layer(edl, words, n)
    out_dir = kit.Project(edl).output
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{edl['slug']}-{edl['short']}_{name}.mp4"
    hf = edl.get("graphics_engine") == "hyperframes" and layer.overlays
    if hf and not (rd / "graphics.mov").exists():
        sys.exit("graphics.mov missing: run --stage graphics first")
    # picture -> HyperFrames graphics -> Pillow captions on top
    inputs = ["-i", str(rd / "picture.mp4"),
              "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-"]
    if hf:
        inputs += ["-i", str(rd / "graphics.mov")]
        fc = ("[0:v][2:v]overlay=0:0:format=auto:eof_action=pass[g];"
              "[g][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    else:
        fc = "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    audio_idx = 3 if hf else 2
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-i", str(rd / "mix.wav"),
           "-filter_complex", fc,
           "-map", "[v]", "-map", f"{audio_idx}:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-movflags", "+faststart",
           "-frames:v", str(n), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(layer.frame(f))
        if f % 150 == 0:
            print(f"  graphics frame {f}/{n}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("final encode failed")
    if hf:   # QA reads graphic boxes from here: measured from the rendered HyperFrames layer
        layer.layout_log["overlays"] = json.loads((rd / "graphics_layout.json").read_text(encoding="utf-8"))
        layer.layout_log["notes"].append("Title cards, chips and data cards rendered with HyperFrames "
                                         "(build_graphics.py); boxes measured from graphics.mov.")
    (rd / "captions_layout.json").write_text(json.dumps(layer.layout_log, indent=1, ensure_ascii=False),
                                             encoding="utf-8")
    shutil.copy(rd.parent.parent / "plans" / f"{edl['short']}_edl.json", out_dir / f"{edl['slug']}-{edl['short']}_edl.json")
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edl")
    ap.add_argument("--name", required=True, help="short-title slug for the output file name")
    ap.add_argument("--stage", default="all", choices=["picture", "audio", "captions", "graphics", "final", "all"])
    ap.add_argument("--input", default=None, help="input folder (default: the EDL's project folder)")
    a = ap.parse_args()
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    proj = kit.Project(edl)
    inp = Path(a.input) if a.input else proj.input
    rd = proj.render_dir(edl["short"])
    rd.mkdir(parents=True, exist_ok=True)
    stages = ["picture", "audio", "captions", "graphics", "final"] if a.stage == "all" else [a.stage]
    for s in stages:
        print(f"== {s}", flush=True)
        if s == "picture":
            stage_picture(edl, rd, inp)
        elif s == "audio":
            stage_audio(edl, rd, inp)
        elif s == "captions":
            stage_captions(edl, rd)
        elif s == "graphics":
            if edl.get("graphics_engine") == "hyperframes":
                sys.path.insert(0, str(Path(__file__).parent))
                import build_graphics
                n = json.loads((rd / "picture_runs.json").read_text(encoding="utf-8"))["frames"]
                build_graphics.run(edl, rd, n)
            else:
                print("  pillow graphics (drawn in the final stage)")
        else:
            stage_final(edl, rd, a.name)


if __name__ == "__main__":
    main()
