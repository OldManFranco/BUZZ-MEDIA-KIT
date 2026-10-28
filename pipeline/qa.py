r"""
Buzz Media kit — step 7: automatic QA of a rendered short (CLAUDE.md §5 step 7).

  python pipeline/qa.py <project>/output/<slug>-s1_<name>.mp4 <project>/working/plans/s1_edl.json

Checks: specs (1080x1920, 30 fps, H.264 yuv420p, AAC 48 kHz stereo, the reel's min_s-max_s, default 15-60 s), loudness after AAC
(-14 +-1 LUFS, TP <= -1 dBTP), first text on screen by 1.0 s, hook words in 0-3 s vs the EDL,
re-transcription (WhisperX) vs the approved lines, the client's exclusion keywords, no word cut at a splice,
captions (safe zone y 260-1440 / x <= 940, <= 4 words, no overlap, word timing +-0.08 s),
graphics in the safe zone, black/flash frames, shots under 0.4 s, SFX spacing.
Writes <output>/<slug>-<short>_qa.md with 8 frame grabs in <output>/qa_<short>/.
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import kit  # noqa: E402

FPS = 30
SAFE = {"y0": 260, "y1": 1440, "x1": 940}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("timu", "temu").replace("u.s.", "us"))


class Report:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append((name, "PASS" if ok is True else "FAIL" if ok is False else ok, detail))
        print(f"{'PASS' if ok is True else 'FAIL' if ok is False else ok:5s} {name}: {detail}", flush=True)


def main(mp4, edl_path):
    mp4, edl = Path(mp4), json.loads(Path(edl_path).read_text(encoding="utf-8"))
    rd = kit.Project(edl).render_dir(edl["short"])
    R = Report()

    # ---- specs
    p = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)]).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    dur = float(p["format"]["duration"])
    R.add("video spec", (v["width"], v["height"], v["r_frame_rate"], v["codec_name"], v["pix_fmt"])
          == (1080, 1920, "30/1", "h264", "yuv420p"),
          f"{v['width']}x{v['height']} {v['r_frame_rate']} {v['codec_name']} {v['pix_fmt']} {v.get('profile')}")
    R.add("audio spec", bool(a) and (a["codec_name"], a["sample_rate"], a["channels"]) == ("aac", "48000", 2),
          f"{a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch" if a else "no audio")
    lo, hi = kit.length_limits(edl)
    R.add("length", lo <= dur <= hi, f"{dur:.2f} s (limits {lo:g}-{hi:g} s)")

    # ---- loudness (after AAC)
    e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    R.add("loudness", abs(I + 14) <= 1, f"{I} LUFS integrated")
    R.add("true peak", tp <= -1.0, f"{tp} dBTP")

    # ---- graphics/captions layout
    lay = json.loads((rd / "captions_layout.json").read_text(encoding="utf-8"))
    caps, ovs = lay["captions"], lay["overlays"]
    first = min([c["t0"] for c in caps] + [o["t"] for o in ovs])
    R.add("first text on screen", first <= 1.0, f"{first:.2f} s")
    bad = [c for c in caps if c["bbox"][1] < SAFE["y0"] or c["bbox"][3] > SAFE["y1"] or c["bbox"][2] > SAFE["x1"]]
    R.add("captions in safe zone", not bad, f"{len(caps)} groups, x {min(c['bbox'][0] for c in caps)}-"
          f"{max(c['bbox'][2] for c in caps)}, y {min(c['bbox'][1] for c in caps)}-{max(c['bbox'][3] for c in caps)}"
          + (f"; outside: {[c['text'] for c in bad]}" if bad else ""))
    R.add("captions <= 4 words", max(c["n_words"] for c in caps) <= 4, f"max {max(c['n_words'] for c in caps)}")
    ov = [(x["text"], y["text"]) for x, y in zip(caps, caps[1:]) if y["t0"] < x["t1"] - 1e-3]
    R.add("captions don't overlap", not ov, f"{len(ov)} overlaps")
    # full-bleed data cards cover the frame by design; their text layout is audited by `hyperframes check`
    badg = [o for o in ovs if not o.get("full_bleed") and o.get("bbox") and (
        o["bbox"][1] < SAFE["y0"] or o["bbox"][3] > SAFE["y1"] or o["bbox"][2] > SAFE["x1"])]
    R.add("graphics in safe zone", not badg, "; ".join(f"{o['kind']} '{o['text']}' {o['bbox']}" for o in ovs))

    # ---- re-transcribe the final file
    qd = rd / "qa_transcript"
    for f in qd.glob(f"{mp4.stem}.*"):
        f.unlink()
    r = sh([str(kit.WHISPERX_PY), "-I", str(kit.WHISPERX),
            str(mp4), str(qd)])
    words = json.loads((qd / f"{mp4.stem}.words.json").read_text(encoding="utf-8"))["words"]
    final_txt = " ".join(w["w"] for w in words)
    hook = " ".join(w["w"] for w in words if w["start"] < 3.0)
    ratio = difflib.SequenceMatcher(None, [norm(w) for w in hook.split()],
                                    [norm(w) for w in edl["hook_words_0_3s"].split()]).ratio()
    R.add("hook words 0-3 s match EDL", ratio >= 0.85, f"heard \"{hook}\" vs EDL \"{edl['hook_words_0_3s']}\" ({ratio:.2f})")
    A = [norm(w) for w in edl["spoken_text"].split() if norm(w)]
    B = [norm(w["w"]) for w in words if norm(w["w"])]
    sm = difflib.SequenceMatcher(None, A, B)
    diffs = [(op, " ".join(A[i1:i2]), " ".join(B[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    R.add("transcript = approved lines", sm.ratio() >= 0.97 and not any(d[0] == "insert" for d in diffs),
          f"similarity {sm.ratio():.3f}; differences: {diffs or 'none'}")
    excl = kit.exclusions(edl)
    hits = sorted({m.group(0) for pat in excl for m in re.finditer(pat, final_txt, re.I)})
    approved_hits = sorted({m.group(0) for pat in excl for m in re.finditer(pat, edl["spoken_text"], re.I)})
    new = [h for h in hits if h.lower() not in {x.lower() for x in approved_hits}]
    R.add("exclusion keywords", not new, f"hits {hits or 'none'}" +
          (f" (already reviewed at Gate 1: {approved_hits})" if approved_hits else ""))
    # splices: every A-roll piece boundary in the output timeline
    pr = json.loads((rd / "picture_runs.json").read_text(encoding="utf-8"))
    splices, t = [], 0.0
    arolls = [x for x in edl["events"] if x["kind"] == "aroll"]
    for x in arolls[:-1]:
        t += x["out"] - x["in"]
        splices.append(round(t, 3))
    cut = [(s, w["w"]) for s in splices for w in words if w["start"] + 0.04 < s < w["end"] - 0.04]
    R.add("no word cut at a splice", not cut, f"{len(splices)} splices checked" + (f"; inside a word: {cut}" if cut else ""))
    # caption timing vs the final file
    cw = [w for c in caps for w in c["words"]]
    sm2 = difflib.SequenceMatcher(None, [norm(w["w"]) for w in cw], [norm(w["w"]) for w in words])
    dts = [abs(cw[i]["s"] - words[j]["start"]) for op, i1, i2, j1, j2 in sm2.get_opcodes() if op == "equal"
           for i, j in zip(range(i1, i2), range(j1, j2))]
    late = sum(d > 0.08 for d in dts)
    med = sorted(dts)[len(dts) // 2]
    # re-transcribing the final file has its own alignment noise (s2: 5 of 218 words at 84-121 ms with a
    # 5 ms median), so a few outliers are tolerated; a real sync problem moves the median
    R.add("caption word timing +-0.08 s", med <= 0.03 and late <= max(2, int(len(dts) * 0.03)),
          f"{len(dts)} words compared, median {med * 1000:.0f} ms, {late} over 80 ms (limit 3%)")

    # ---- picture: black / flash frames, short shots
    bd = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-vf", "blackdetect=d=0.03:pix_th=0.08",
             "-an", "-f", "null", "-"]).stderr
    blacks = re.findall(r"black_start:([\d.]+)", bd)
    st = sh(["ffprobe", "-v", "error", "-f", "lavfi", "-i", f"movie={mp4.as_posix()},signalstats",
             "-show_entries", "frame_tags=lavfi.signalstats.YAVG", "-of", "csv=p=0"]).stdout.split()
    y = [float(x.strip(",")) for x in st if x.strip(",")]
    flashes = [round(i / FPS, 2) for i in range(1, len(y) - 1)
               if abs(y[i] - y[i - 1]) > 50 and abs(y[i] - y[i + 1]) > 50]
    R.add("no black frames", not blacks, f"{blacks or 'none'}")
    R.add("no single-frame flashes", not flashes, f"{flashes or 'none'} ({len(y)} frames scanned)")
    runs = pr["runs"]
    shots = []
    for k, rr in enumerate(runs):
        same_framing = k and runs[k - 1]["kind"] == rr["kind"] == "aroll" and runs[k - 1]["src"] == rr["src"] \
            and abs(runs[k - 1]["xc"] - rr["xc"]) < 1e-3 and runs[k - 1]["scale"] == rr["scale"]
        if same_framing and shots:
            shots[-1][1] += rr["n"]               # a pause cut at the same framing isn't a new shot
        else:
            shots.append([rr["f0"], rr["n"]])
    short = [(round(f0 / FPS, 2), round(n / FPS, 2)) for f0, n in shots if n < 0.4 * FPS]
    longest = max(n for _, n in shots) / FPS
    R.add("no shot under 0.4 s", not short, f"{len(shots)} shots, shortest {min(n for _, n in shots) / FPS:.2f} s"
          + (f"; short: {short}" if short else ""))
    R.add("visual change <= 5 s", edl["pacing"]["longest_hold_s"] <= 5.0,
          f"plan longest hold {edl['pacing']['longest_hold_s']} s (cuts, punch-ins, chips, B-roll); "
          f"longest single camera shot {longest:.1f} s")

    # ---- SFX
    alog = json.loads((rd / "audio_log.json").read_text(encoding="utf-8"))
    sfx = sorted(x["t"] for x in alog["sfx"])
    dense = [(a_, b_) for a_, b_ in zip(sfx, sfx[1:]) if b_ - a_ < 3.0]
    on_num = [(x["t"], w["w"]) for x in alog["sfx"] for w in words
              if re.search(r"\d", w["w"]) and w["start"] - 0.15 < x["t"] < w["end"] + 0.15]
    R.add("SFX <= 1 per 3 s", not dense, f"{len(sfx)} SFX at {sfx}" + (f"; too close: {dense}" if dense else ""))
    R.add("no SFX on a number", not on_num, f"{on_num or 'none'}")

    # ---- frame grabs
    gdir = mp4.parent / f"qa_{edl['short']}"
    gdir.mkdir(exist_ok=True)
    times = [0.0, 0.5, 1.5, 3.0] + [round(3.0 + (dur - 3.5) * k / 4, 2) for k in range(1, 5)]
    grabs = []
    for k, tt in enumerate(times):
        out = gdir / f"{k + 1:02d}_{tt:05.2f}s.jpg"
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.3f}", "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(out)])
        grabs.append(out)
    ims = [Image.open(g).resize((270, 480)) for g in grabs]
    sheet = Image.new("RGB", (270 * 8, 480))
    for i, im in enumerate(ims):
        sheet.paste(im, (270 * i, 0))
    sheet.save(gdir / "sheet.jpg", quality=85)

    # ---- report
    fails = [r_ for r_ in R.rows if r_[1] == "FAIL"]
    md = [f"# QA: {mp4.name}", "",
          f"**{len(R.rows) - len(fails)} of {len(R.rows)} checks pass.**" + (f" Failing: {', '.join(f[0] for f in fails)}." if fails else ""),
          "", "| Check | Result | Detail |", "|---|---|---|"]
    md += [f"| {n} | {s} | {d.replace('|', '/')} |" for n, s, d in R.rows]
    md += ["", "## Re-transcription of the final file (WhisperX)", "", "> " + final_txt, "",
           "## Render notes (choices that differ from the [DRAFT] spec)", ""]
    md += [f"- {n}" for n in lay.get("notes", [])]
    md += [f"- Grade: {edl.get('grade')}", f"- SFX used: " + "; ".join(
        f"{x['sfx']} at {x['t']} s ({Path(x['file']).name}, {x['db']} dB)" for x in alog["sfx"]),
        f"- Segment level matching (dB): " + ", ".join(f"seg {k}: {v:+.1f}" for k, v in alog["segment_gain_db"].items()),
        "", "## Frame grabs", "", f"![sheet](qa_{edl['short']}/sheet.jpg)", ""]
    md += [f"- {g.name}" for g in grabs]
    qa = mp4.parent / f"{edl['slug']}-{edl['short']}_qa.md"
    qa.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote", qa)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2])
