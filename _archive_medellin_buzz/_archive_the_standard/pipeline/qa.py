r"""
The Standard — Step 13: Automatic QA

CLAUDE.md v2.4 §Pipeline Step 13 (source of truth) checks:
  - Length 61-70s
  - Loudness -14 +-1 LUFS, true peak below -1 dBTP (warns near the edge)
  - >=6 frame grabs; every one is 9:16 (1080x1920)
  - No two Main-layer caption events overlap (parse .ass)
  - Every caption all-caps
  - Every caption starts within +-0.15s of its word   (needs --chunks)
  - Captions match the cuts.json expected text        (needs --chunks, --cuts)
  - Watermark present on frames before the sign-off   (needs --broll)
  - Sign-off card is the last 1s                      (needs --signoff)
  - Delivery file <=30 MB

Optional checks print SKIP when their input isn't given.
Frame grabs go to --grab-dir (default: next to the report), never outbox\.
Prints PASS/FAIL per check and exits non-zero on any FAIL.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image


WM_BAND = (300, 270, 780, 345)       # x0, y0, x1, y1 around the watermark (y=300)
CONTROL_BAND = (300, 600, 780, 675)  # same size, no overlays there


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def check(cond: bool, label: str, detail: str = ""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {label}" + (f"  — {detail}" if detail else ""))
    return cond


def skip(label: str, why: str):
    print(f"  [SKIP] {label}  — {why}")


def parse_ass(ass_path: str):
    events = []
    with open(ass_path, encoding="utf-8") as f:
        in_events = False
        for line in f:
            line = line.rstrip("\r\n")
            if line.strip() == "[Events]":
                in_events = True; continue
            if not in_events or not line.startswith("Dialogue:"):
                continue
            parts = line.split(",", 9)
            layer = int(parts[0].split(":")[1].strip())
            events.append((layer, parts[1].strip(), parts[2].strip(), parts[9]))
    return events


def ass_time_to_s(t: str) -> float:
    h, m, rest = t.split(":")
    s, cs = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0


def grab(video: str, t: float, out_png: Path) -> np.ndarray:
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", str(out_png)])
    return np.asarray(Image.open(out_png).convert("L"), dtype=np.float32)


def band(img: np.ndarray, box) -> np.ndarray:
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1]


def norm_words(text: str) -> list:
    return re.sub(r"[^a-z0-9' ]", " ", text.replace("*", "").lower()).split()


def checks_v3(args, dur, chunks_path, grab_dir, report) -> bool:
    """CLAUDE.md v3.0 Step 12 additions."""
    import difflib
    sd = Path(args.slug_dir)
    ok = True

    def ld(n):
        return json.load(open(sd / n, encoding="utf-8"))

    tl, segs, script, claims = ld("timeline.json"), ld("segments.json"), ld("script.json"), ld("claims.json")
    cuts = ld("clips/cuts.json")["clips"]
    mixdbg = ld("mix_debug.json")
    ok &= check(tl.get("format") == "v3" and segs.get("format") == "v3", "timeline.json / segments.json are format v3")
    if not 88.0 <= dur <= 92.0:
        print(f"  [WARN] Length outside the 88-92s target  — {dur:.2f}s")

    # Hook rule on the first 2.0s of the final narration
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from transcribe_islands import build_recognizer, recognize, load_audio_mono_16k, DEFAULT_MODEL_DIR
    rec = build_recognizer(DEFAULT_MODEL_DIR)
    pcm = load_audio_mono_16k(str(sd / "mix_nomusic.wav"))
    head = recognize(rec, pcm[:int(2.0 * 16000)])["text"]
    hw = norm_words(head)
    hooks = ld("hooks.json")
    picked = next(h for h in hooks["variants"] if h["id"] == script.get("hook_id", "H1"))
    proper = any(w in hw for w in ("michael", "jordan", "jordan's"))
    detail_words = norm_words(picked["detail"].split("(")[0])
    detail = any(ch.isdigit() for ch in head) or sum(w in hw for w in detail_words) >= 2
    report["hook_first_2s"] = head
    ok &= check(proper and detail, "Hook rule in the first 2.0s (proper noun + specific detail)", f"'{head}'")

    # Narration transcript vs script.json
    want = norm_words(" ".join(snt["spoken"] for b in script["beats"] for snt in b["sentences"]))
    got = []
    for e in tl["edit"]:
        a, b = max(0, int((e["tl_start"] - 0.05) * 16000)), int((e["tl_end"] + 0.1) * 16000)
        got += norm_words(recognize(rec, pcm[a:b])["text"])
    ratio = difflib.SequenceMatcher(a=want, b=got, autojunk=False).ratio()
    report["narration_match"] = round(ratio, 3)
    ok &= check(ratio >= 0.85, "Narration transcript matches script.json", f"word match {ratio:.2f}")

    # Claims
    status = {c["id"]: c["status"] for c in claims["claims"]}
    used = {cid for b in script["beats"] for snt in b["sentences"] for cid in snt["claims"]}
    bad = sorted(c for c in used if status.get(c) != "verified")
    ok &= check(not bad, "Every claim used is verified", f"{len(used)} claims" if not bad else f"unverified: {bad}")

    # Real speech: 12-20s, only in beat 4, matches cuts.json
    sp = tl["speech_tl"]
    total = sum(c["tl_end"] - c["tl_start"] for c in sp)
    b4 = min(e["tl_start"] for e in tl["edit"] if e["beat"] == 4)
    b5 = min(e["tl_start"] for e in tl["edit"] if e["beat"] == 5)
    inside = all(b4 <= c["tl_start"] and c["tl_end"] <= b5 for c in sp)
    ok &= check(12.0 <= total <= 20.0 and inside, "Real speech 12-20s, only in beat 4", f"{total:.1f}s")
    exp = norm_words(" ".join(c["expected"] for c in cuts))
    sgot = []
    for c in sp:
        a, b = int((c["tl_start"] - 0.03) * 16000), int((c["tl_end"] + 0.08) * 16000)
        sgot += norm_words(recognize(rec, pcm[a:b])["text"])
    sr = difflib.SequenceMatcher(a=exp, b=sgot, autojunk=False).ratio()
    ok &= check(sr >= 0.85, "Speech matches cuts.json", f"word match {sr:.2f}")

    # License sidecars
    req = ld("request.json")
    src_dir = Path(__file__).resolve().parent.parent / req["subject_folder"] / "Scene Pack" / "_sourced"
    media = [p for p in src_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm")]
    missing = [p.name for p in media if not Path(str(p) + ".license.json").exists()]
    ok &= check(not missing, "Every _sourced file has a .license.json",
                f"{len(media)} files" if not missing else str(missing))

    # Graphic text inside y=380-1180 (blocks without a photo background, on the clean reel)
    plan = ld("graphics_plan.json")
    reel = str(sd / plan["reel"])
    outside = []
    for b in plan["beats"]:
        if b["block"] in ("era_banner", "archival_frame"):
            continue
        img = grab(reel, b["reel_start_s"] + b["dur_s"] * 0.7, grab_dir / f"safe_{b['name']}.png")
        rows = np.where((img > 200).sum(axis=1) > 6)[0]
        if len(rows) and (rows.min() < 380 or rows.max() > 1180):
            outside.append(f"{b['name']} rows {rows.min()}-{rows.max()}")
    ok &= check(not outside, "Graphic text inside the safe zone (y=380-1180)", "; ".join(outside) or "ok")

    # SFX onsets vs narrated proper nouns / numbers
    hits = [(x["tl_s"], w) for x in mixdbg["sfx"] for a, b, w in mixdbg["protected_spans"] if a <= x["tl_s"] < b]
    ok &= check(not hits, "No SFX onset on a narrated proper noun or number",
                f"{len(mixdbg['sfx'])} SFX" if not hits else str(hits))

    # _nomusic delivery
    if args.delivery_nomusic and os.path.exists(args.delivery_nomusic):
        d2 = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", args.delivery_nomusic]).stdout.strip())
        ok &= check(abs(d2 - dur) < 0.05, "_nomusic file present, same length", f"{d2:.3f}s vs {dur:.3f}s")
    else:
        ok &= check(False, "_nomusic file present", "missing")

    # Captions vs script display + cuts expected (the muted brand line is the only allowed gap)
    if chunks_path:
        chunks = json.load(open(chunks_path, encoding="utf-8"))["chunks"]
        # Video order: narration beats 1-4, the real speech, then beat 5
        disp = lambda beats: norm_words(" ".join(snt["display"] for b in beats for snt in b["sentences"]))
        want = (disp([b for b in script["beats"] if b["beat"] <= 4]) + exp
                + disp([b for b in script["beats"] if b["beat"] >= 5]))
        got = norm_words(" ".join(c["text"] for c in chunks))
        sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
        ops = sm.get_opcodes()
        dropped = [w for op, a1, a2, b1, b2 in ops if op in ("delete", "replace") for w in want[a1:a2]]
        added = [w for op, a1, a2, b1, b2 in ops if op in ("insert", "replace") for w in got[b1:b2]]
        muted_ok = dropped == ["hold", "the", "standard"] and not added
        ok &= check(muted_ok or (not dropped and not added), "Captions match script.json + cuts.json",
                    "only the muted brand line differs" if muted_ok else f"dropped {dropped[:8]} added {added[:8]}")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delivery", required=True)
    ap.add_argument("--ass", required=True)
    ap.add_argument("--chunks", help="build_captions --out-chunks-json")
    ap.add_argument("--cuts", help="cuts.json from cut_speech")
    ap.add_argument("--broll", help="b-roll concat (no overlays) for the watermark check")
    ap.add_argument("--signoff", help="signoff_card.mp4 for the last-1s check")
    ap.add_argument("--signoff-dur-s", type=float, default=1.0)
    ap.add_argument("--out-report", required=True)
    ap.add_argument("--grab-dir", default=None)
    ap.add_argument("--min-len-s", type=float, default=61.0)
    ap.add_argument("--format", default="v2.4", choices=["v2.4", "v3"])
    ap.add_argument("--slug-dir", help="v3: working/<slug>")
    ap.add_argument("--delivery-nomusic", help="v3: delivery_nomusic.mp4")
    args = ap.parse_args()
    v3 = args.format == "v3"
    if v3 and not args.slug_dir:
        ap.error("--format v3 needs --slug-dir")

    grab_dir = Path(args.grab_dir or Path(args.out_report).parent / "qa_grabs")
    grab_dir.mkdir(parents=True, exist_ok=True)
    report = {"delivery": args.delivery}
    ok_all = True

    # Length
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", args.delivery]).stdout.strip())
    report["duration_s"] = round(dur, 3)
    lo, hi = (60.0, 95.0) if v3 else (args.min_len_s, 70.0)
    ok_all &= check(lo <= dur <= hi, f"Length {lo:g}-{hi:g}s", f"{dur:.3f}s")

    # Resolution / fps
    probe = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height,r_frame_rate",
                 "-of", "default=noprint_wrappers=1", args.delivery]).stdout
    w = int(re.search(r"width=(\d+)", probe).group(1))
    h = int(re.search(r"height=(\d+)", probe).group(1))
    fps = float(Fraction(re.search(r"r_frame_rate=(\S+)", probe).group(1)))
    report.update(width=w, height=h, fps=fps)
    ok_all &= check(w == 1080 and h == 1920, "Resolution 1080x1920", f"{w}x{h}")
    ok_all &= check(abs(fps - 30) < 0.5, "Frame rate 30fps", f"{fps:g}fps")

    # Loudness
    ln = run(["ffmpeg", "-i", args.delivery,
              "-af", "loudnorm=print_format=json:I=-14:TP=-1:LRA=11", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", ln.stderr, flags=re.S)
    if m:
        stats = json.loads(m.group(0))
        lufs, tp = float(stats["input_i"]), float(stats["input_tp"])
        report.update(lufs=lufs, tp=tp)
        near = "  (within 0.2 of the limit)" if 0 <= min(lufs + 15, -13 - lufs) < 0.2 else ""
        ok_all &= check(-15.0 <= lufs <= -13.0, "Loudness -14 ±1 LUFS", f"{lufs} LUFS{near}")
        ok_all &= check(tp < -0.99, "True peak < -1 dBTP", f"{tp} dBTP")
    else:
        ok_all &= check(False, "Loudness measured", "loudnorm gave no stats")

    # File size
    sz = os.path.getsize(args.delivery) / 1e6
    report["size_mb"] = round(sz, 2)
    ok_all &= check(sz <= 30.0, "Delivery <= 30 MB", f"{sz:.1f} MB")

    # ASS parse: overlap + all caps
    events = parse_ass(args.ass)
    main_events = [e for e in events if e[0] == 0]
    overlap_bad = any(ass_time_to_s(main_events[i][2]) > ass_time_to_s(main_events[i + 1][1])
                      for i in range(len(main_events) - 1))
    ok_all &= check(not overlap_bad, "No overlapping Main-layer captions",
                    f"{len(main_events)} captions")
    all_caps_ok = True
    for _, _, _, text in events:
        letters = re.sub(r"[^A-Za-z]", "", re.sub(r"\{[^}]*\}", "", text))
        if letters and letters != letters.upper():
            all_caps_ok = False; break
    ok_all &= check(all_caps_ok, "Captions all uppercase")

    # Caption timing + text vs cuts.json
    if args.chunks:
        with open(args.chunks, encoding="utf-8") as f:
            chunks = json.load(f)["chunks"]
        offs = [abs(c["start"] - c["word_t"]) for c in chunks if "word_t" in c]
        worst = max(offs) if offs else 0.0
        report["caption_max_offset_s"] = round(worst, 3)
        ok_all &= check(bool(offs) and worst <= 0.15, "Captions start within ±0.15s of their word",
                        f"worst {worst:.3f}s")
        if v3:
            skip("Captions match cuts.json expected text (v2.4)", "v3 checks script.json + cuts.json below")
        elif args.cuts:
            with open(args.cuts, encoding="utf-8") as f:
                expected = " ".join(c["expected"] for c in json.load(f)["clips"])
            got = norm_words(" ".join(c["text"] for c in chunks))
            want = norm_words(expected)
            ok_all &= check(got == want, "Captions match cuts.json expected text",
                            f"{len(got)} words" if got == want else
                            f"got {len(got)} words, expected {len(want)}")
        else:
            skip("Captions match cuts.json expected text", "no --cuts")
    else:
        skip("Caption timing / text checks", "no --chunks")

    # Frame grabs: 6 across the video, check resolution per grab
    grabs = []
    for i in range(6):
        t = (i + 0.5) * dur / 6
        img = grab(args.delivery, t, grab_dir / f"grab{i:02d}.png")
        grabs.append({"t": round(t, 3), "w": img.shape[1], "h": img.shape[0]})
    report["frame_grabs"] = grabs
    ok_all &= check(all(g["w"] == 1080 and g["h"] == 1920 for g in grabs),
                    "All 6 frame grabs are 1080x1920", str(grab_dir))

    # Watermark: delivery vs b-roll differ in the watermark band, not elsewhere
    broll_end = dur - args.signoff_dur_s
    if args.broll:
        hits = 0
        n = 6
        for i in range(n):
            t = (i + 0.5) * broll_end / n
            a = grab(args.delivery, t, grab_dir / f"wm_d{i:02d}.png")
            b = grab(args.broll, t, grab_dir / f"wm_b{i:02d}.png")
            wm_diff = float(np.abs(band(a, WM_BAND) - band(b, WM_BAND)).mean())
            ctl_diff = float(np.abs(band(a, CONTROL_BAND) - band(b, CONTROL_BAND)).mean())
            hits += wm_diff > ctl_diff + 1.0
        ok_all &= check(hits == n, "Watermark present before the sign-off", f"{hits}/{n} frames")
    else:
        skip("Watermark present before the sign-off", "no --broll")

    # Sign-off: last 1s of the delivery matches the sign-off card (and has no watermark)
    if args.signoff:
        a = grab(args.delivery, broll_end + args.signoff_dur_s / 2, grab_dir / "signoff_d.png")
        b_png = grab_dir / "signoff_ref.png"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-ss", f"{args.signoff_dur_s / 2:.3f}", "-i", args.signoff,
             "-vf", "scale=1080:1920:flags=lanczos", "-frames:v", "1", str(b_png)])
        b = np.asarray(Image.open(b_png).convert("L"), dtype=np.float32)
        diff = float(np.abs(a - b).mean())
        wm_diff = float(np.abs(band(a, WM_BAND) - band(b, WM_BAND)).mean())
        report["signoff_diff"] = round(diff, 2)
        ok_all &= check(diff < 6.0 and wm_diff < 6.0, "Sign-off card is the last 1s (no watermark)",
                        f"mean diff {diff:.1f}, watermark band {wm_diff:.1f}")
    else:
        skip("Sign-off card is the last 1s", "no --signoff")

    if v3:
        print("  -- v3.0 checks --")
        ok_all &= checks_v3(args, dur, args.chunks, grab_dir, report)

    with open(args.out_report, "w", encoding="utf-8") as f:
        json.dump({"ok": bool(ok_all), **report}, f, indent=2)
    print(f"\nwrote {args.out_report}")
    print(f"OVERALL: {'PASS' if ok_all else 'FAIL'}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
