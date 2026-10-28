r"""
Buzz Media kit — steps 4-5 helper: turn a draft EDL into a timed plan and check it before Gate 1.

A draft lists A-roll segments in order (raw clip + word-snapped in/out) and overlays anchored to a source moment.
This script:
  - tightens every pause > 0.30 s inside a segment to 0.15 s (CLAUDE.md §5/§9; draft "gap_max"/"gap_new" override),
    except gaps listed in "keep_gaps" (breaths before a payoff) and the gap right after a number (WhisperX often
    times "200" as "two" only, with "hundred" in what looks like a pause: promo-01), and drops "drop" ranges
    (their edges are hard cut limits)
  - pads each splice with room tone (0.06 s before the first word, 0.08 s after the last), then snaps every cut
    point to the quietest 10 ms of the source audio within +-60 ms (draft "snap_cuts": false turns it off) and
    warns on a cut louder than -35 dBFS (the first sound of a dropped word leaking through)
  - assigns output time t to every segment, overlay, "layout" range, "sfx_track" hit and "caption_layout.mute"
    range; layout and overlay times sit on frame boundaries, and an overlay edge within 3 frames of a picture
    switch moves onto that switch's frame (promo-02/03: a panel 2 frames late showed bare ink)
  - ends the reel ~0.1 s after the last word ("ending_tail_s"; promo-02/03: the old 0.6 s hold showed the speaker
    looking away and was trimmed by hand every time). "ending_hold_s" still sets the hold explicitly
  - prints the words heard in 0-3 s, total length, visual changes (cuts, overlays, layout switches, hf_scene
    "beats"), longest hold
  - scans the spoken text for the client's exclusion keywords (kit.exclusions)
  - Gate 1 checks (also in the EDL's "checks"): every number token and the gap after it; clauses dropped from
    inside a sentence (with the length if they're restored); an ending that isn't a sentence end or that the
    speaker talks on after; SFX closer than 3 s or on a number or name being said; on-screen text held too short
    to read (0.5 s + 0.3 s per word); interpolated words at a cut edge; length outside min_s-max_s
    (default 15-60 s); a hold over 4 s without a visual change; a bare anchor word that occurs more than once; a
    "flash_in" scene that isn't covering the frame before the cut it hides; a punch-in under a graphic; a "matte"
    that outlasts its A-roll segment
Writes the timed EDL next to the draft (s<N>_edl.json).
Draft needs "project_dir" (kit.Project); each segment's "clip" is a transcript stem in <project>\working\transcripts\
(e.g. "promo-01" for raw\promo-01.mkv).

Times: anything that has to follow the A-roll is written as an anchor, never as a reel time, so it survives
every audio fix. "anchor" (start) and "until" (end) take:
  [seg, src_t]                       a source moment in that A-roll segment
  "upload" / "ready to post#2"       a spoken word or phrase (#n = its n-th occurrence, default the first)
  {"word": "upload", "n": 1, "offset": -0.1}
  "end" (until only)                 through the ending hold
They work on overlays, "layout" items (a layout item without an end runs to the next one), "sfx_track" hits and
the two ends of each "caption_layout" "mute" range. An hf_scene can name word "cues" ({"upload": "upload"}: filled
into the scene as {{cue_upload}}, seconds from the scene's start) and list its "beats" (seconds from its start,
cue names or anchors: when its picture changes; they count as visual changes). A scene with a subject cutout
("matte": true) can end the cutout early with "matte_until" (an anchor): the face checks skip the cutout's span only.

Usage:
  python pipeline/plan_shorts.py clients/<client>/projects/<project>/working/plans/s1_draft.json [...]
"""
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

MAX_GAP, NEW_GAP = 0.30, 0.15
PAD_IN, PAD_OUT = 0.06, 0.08
SR = 48000
SNAP_WIN, SNAP_FRAME, LOUD_CUT_DB = 0.06, 0.010, -35.0
SFX_MIN_GAP = 3.0
FPS = 30
TAIL = 0.1             # seconds of picture after the last word's end (its natural decay)
SNAP_FRAMES = 3        # an overlay edge this close to a picture switch moves onto it


def q(t):
    """A time on a frame boundary, rounded down at 4 decimals so the renderer (round(t*30)) and HyperFrames (a
    layer shows from its data-start) agree on the frame."""
    return int(round(t * FPS) / FPS * 1e4) / 1e4
FILLERS = {"uh", "um", "uhm", "ah", "er", "erm", "hmm", "like"}
PICTURE = {"broll", "punch_in", "chip", "card", "title_card", "reframe", "hf_scene"}
# exclusion keywords are per client now: kit.exclusions(edl)


def transcript_for(d, clip):
    """The words.json for a clip id: an exact stem first, then any stem containing it (old DJI names)."""
    tdir = kit.Project(d).transcripts
    exact = tdir / f"{clip}.words.json"
    return exact if exact.exists() else Path(sorted(glob.glob(str(tdir / f"*{clip}*.words.json")))[0])


def words_for(d, clip):
    return json.loads(transcript_for(d, clip).read_text(encoding="utf-8"))["words"]


def source_for(d, clip):
    r"""raw\<stem>.<ext> for the clip's transcript (whatever the container: .mp4, .MP4, .mkv, .mov)."""
    stem = transcript_for(d, clip).name.replace(".words.json", "")
    hits = sorted(kit.Project(d).input.glob(f"raw/{stem}.*"))
    return f"raw/{hits[0].name}" if hits else f"raw/{stem}.MP4"


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def is_number(w):
    return bool(re.search(r"\d", w))


def ends_sentence(w):
    return bool(re.search(r"[.?!][\"')\]]*$", w))


# ---------------------------------------------------------------- numbers

ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + say(n % 100))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div:
            return say(n // div) + " " + name + ("" if n % div == 0 else " " + say(n % div))


def syllables(text):
    n = 0
    for w in text.split():
        k = len(re.findall(r"[aeiouy]+", w))
        n += max(1, k - (1 if w.endswith("e") and not w.endswith("le") and k > 1 else 0))
    return n


def spoken_estimate(tok):
    """Rough seconds a number token takes to say (0.12 s per syllable), or None if it can't be read."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", tok)
    if not m:
        return None
    s = m.group().replace(",", "")
    a, _, b = s.partition(".")
    if len(a) > 12:
        return None
    text = say(int(a))
    if b:   # "$1.99" is said "one ninety-nine"; "2.5" is "two point five"
        text += " " + (say(int(b)) if tok.startswith("$") and len(b) == 2 else "point " + " ".join(ONES[int(c)] for c in b))
    return round(0.12 * syllables(text), 2)


# ---------------------------------------------------------------- cut points

_audio = {}


def source_audio(d, src):
    """The raw clip's audio, mono float32 at 48 kHz (read only)."""
    if src not in _audio:
        path = kit.Project(d).input / src
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True)
        _audio[src] = np.frombuffer(r.stdout, np.float32) if r.returncode == 0 and r.stdout else None
    return _audio[src]


def level_db(x, t, width=SNAP_FRAME):
    i0 = max(int((t - width / 2) * SR), 0)
    a = x[i0: i0 + int(width * SR)]
    return round(float(10 * np.log10((a.astype(np.float64) ** 2).mean() + 1e-12)), 1) if len(a) else -120.0


def snap(x, t, lo, hi):
    """The center of the quietest 10 ms frame within +-60 ms of t, kept inside [lo, hi]."""
    lo, hi = max(lo, t - SNAP_WIN), min(hi, t + SNAP_WIN)
    win = int(SNAP_FRAME * SR)
    i0, i1 = int(lo * SR), int(hi * SR)
    if i1 - i0 < win or i1 > len(x):
        return t
    e = (x[i0:i1].astype(np.float64)) ** 2
    c = np.concatenate([[0.0], np.cumsum(e)])
    m = (c[win:] - c[:-win])[:: SR // 1000]                    # 10 ms windows on a 1 ms hop
    return round((i0 + int(np.argmin(m)) * (SR // 1000) + win / 2) / SR, 4)


def build_segment(ws, seg):
    """Pieces [(src_in, src_out)] after dropping ranges and tightening gaps, the words kept, the numbers seen and
    the snapping limits of every cut: a list of (lo, hi) per piece edge."""
    drops = seg.get("drop", [])
    keep = [w for w in ws if w["start"] >= seg["in"] - 0.01 and w["end"] <= seg["out"] + 0.01
            and not any(a - 0.01 <= w["start"] and w["end"] <= b + 0.01 for a, b in drops)]
    if not keep:
        raise ValueError(f"no words in segment {seg}")
    i_first = next(i for i, w in enumerate(ws) if w is keep[0])
    i_last = next(i for i, w in enumerate(ws) if w is keep[-1])
    prev_src = ws[i_first - 1] if i_first else None
    next_src = ws[i_last + 1] if i_last + 1 < len(ws) else None
    pieces = []
    cur = [keep[0]["start"] - PAD_IN, None, (prev_src["end"] if prev_src else 0.0, keep[0]["start"])]
    numbers = []
    for prev, w in zip(keep, keep[1:]):
        gap = w["start"] - prev["end"]
        drop = next(((a, b) for a, b in drops if prev["end"] - 0.06 <= a and b <= w["start"] + 0.06), None)
        kept_gap = any(abs(prev["end"] - g) < 0.05 for g in seg.get("keep_gaps", []))
        if is_number(prev["w"]):
            numbers.append({"w": prev["w"], "src_t": prev["start"], "dur": round(prev["end"] - prev["start"], 2),
                            "gap_after": round(gap, 2), "est_s": spoken_estimate(prev["w"])})
        if (gap > MAX_GAP and not kept_gap and not is_number(prev["w"])) or drop:
            half = min(gap, NEW_GAP) / 2
            # a drop range's edges are hard limits: WhisperX word edges run ~50 ms late, so a cut half a gap
            # after the last kept word can let the first sound of the dropped word through (promo-01: "th-at")
            cur[1] = min(prev["end"] + half, drop[0]) if drop else prev["end"] + half
            cur.append((prev["start"] + 0.05, drop[0] if drop else w["start"]))
            pieces.append(cur)
            cur = [max(w["start"] - half, drop[1]) if drop else w["start"] - half, None,
                   (drop[1] if drop else prev["end"], w["start"])]
    if is_number(keep[-1]["w"]):
        numbers.append({"w": keep[-1]["w"], "src_t": keep[-1]["start"],
                        "dur": round(keep[-1]["end"] - keep[-1]["start"], 2), "gap_after": None,
                        "est_s": spoken_estimate(keep[-1]["w"])})
    cur[1] = keep[-1]["end"] + PAD_OUT
    cur.append((keep[-1]["start"] + 0.05, next_src["start"] if next_src else keep[-1]["end"] + 1.0))
    pieces.append(cur)
    return pieces, keep, numbers, prev_src, next_src


def sentence_checks(ws, seg, keep, prev_src, k):
    """Mid-sentence edges and clauses dropped from inside a sentence (CLAUDE.md §5: cut whole sentences)."""
    out = []
    if prev_src and not ends_sentence(prev_src["w"]) and keep[0]["start"] - prev_src["end"] < 1.0:
        out.append(f"seg {k}: starts mid-sentence (after '{prev_src['w']}')")
    mid_drops = []
    for a, b in seg.get("drop", []):
        before = [w for w in keep if w["end"] <= a + 0.06]
        dropped = [w["w"] for w in ws if a - 0.01 <= w["start"] and w["end"] <= b + 0.01]
        if before and not ends_sentence(before[-1]["w"]) and not all(norm(x) in FILLERS for x in dropped):
            mid_drops.append([a, b])
            out.append(f"seg {k}: drops a clause from inside a sentence: \"{' '.join(dropped)}\" (a filler or "
                       f"false start is fine; a clause costs context: show the full-line option at Gate 1)")
    return out, mid_drops


# ---------------------------------------------------------------- anchors

def make_resolver(seg_maps, spoken, total, notes=None):
    def src_to_out(seg, src_t):
        for a, b, tt in seg_maps[seg]:
            if a - 0.3 <= src_t <= b + 0.3:
                return round(tt + max(0.0, src_t - a), 2)
        raise ValueError(f"anchor {seg}@{src_t} falls in a removed gap")

    def word_at(phrase, n=1):
        ph = [norm(x) for x in phrase.split()]
        hits = [i for i in range(len(spoken) - len(ph) + 1)
                if [norm(s["w"]) for s in spoken[i:i + len(ph)]] == ph]
        if len(hits) < n:
            raise ValueError(f"anchor word '{phrase}'#{n} isn't in the spoken words")
        return spoken[hits[n - 1]]["t"], len(hits)

    def at(a):
        if isinstance(a, (int, float)):
            return float(a)
        if a == "end":
            return round(total, 2)
        if isinstance(a, list):
            return src_to_out(*a)
        if isinstance(a, dict):
            t, k = word_at(a["word"], a.get("n", 1))
            if k > 1 and "n" not in a and notes is not None:
                notes.append(f"anchor '{a['word']}' occurs {k} times: it took the first ({t} s); add \"n\" or use "
                             f"[seg, src_t]")
            return round(t + a.get("offset", 0.0), 2)
        phrase, _, n = a.partition("#")
        t, k = word_at(phrase, int(n or 1))
        if k > 1 and not n and notes is not None:
            notes.append(f"anchor '{phrase}' occurs {k} times: it took the first ({t} s); write '{phrase}#2'... or "
                         f"[seg, src_t]")
        return t
    return at


def place(item, at, end_value):
    o = dict(item)
    if "anchor" in o:
        o["t"] = at(o.pop("anchor"))
    if "until" in o:
        u = o.pop("until")
        o["t_out"] = end_value if u == "end" else at(u)
    return o


def visual_changes(edl, total):
    """Reel times where the picture changes: a new A-roll segment, an overlay with picture in or out, a layout
    switch (mode or punch), an hf_scene beat. Shared with qa.py."""
    ev = edl["events"]
    ts = {next(e["t"] for e in ev if e["kind"] == "aroll" and e["seg"] == s)
          for s in {e["seg"] for e in ev if e["kind"] == "aroll"}}
    for o in ev:
        if o["kind"] in PICTURE:
            ts.add(o["t"])
            if isinstance(o.get("t_out"), (int, float)):
                ts.add(o["t_out"])
            ts.update(o.get("beat_times", []))
    last = None
    for l in sorted(edl.get("layout", []), key=lambda l: l["t"]):
        look = (l["mode"], l.get("punch"))
        if look != last:
            ts.add(l["t"])
        last = look
    ts = sorted({round(t, 2) for t in ts if 0 <= t <= total} | {round(total, 2)})
    longest = max(b - a for a, b in zip(ts, ts[1:])) if len(ts) > 1 else total
    return ts, longest


def sfx_hits(edl):
    hits = [{"t": h["t"], "what": h["file"]} for h in edl.get("sfx_track", [])]
    for o in edl["events"]:
        if o.get("sfx") and o["kind"] in ("title_card", "chip", "broll"):
            hits.append({"t": round(o["t"] - (0.12 if o["kind"] == "broll" else 0.0), 2), "what": o["sfx"]})
    return sorted(hits, key=lambda h: h["t"])


def is_name(spoken, i):
    w = spoken[i]["w"]
    first = i == 0 or ends_sentence(spoken[i - 1]["w"])
    return w[:1].isupper() and not first and not re.match(r"^I('|$)", w)


# ---------------------------------------------------------------- main

def main(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    global MAX_GAP, NEW_GAP
    MAX_GAP, NEW_GAP = d.get("gap_max", MAX_GAP), d.get("gap_new", NEW_GAP)
    t, timeline, spoken, warnings = 0.0, [], [], []
    seg_maps, numbers, cuts, mid_sentence, restore_s = [], [], [], [], 0.0
    ending = {}
    for k, seg in enumerate(d["aroll"]):
        ws = words_for(d, seg["clip"])
        src = source_for(d, seg["clip"])
        pieces, keep, nums, prev_src, next_src = build_segment(ws, seg)
        for edge in (keep[0], keep[-1]):
            if edge.get("interpolada"):
                warnings.append(f"seg {k}: cut edge on interpolated word '{edge['w']}'")
        msgs, mid_drops = sentence_checks(ws, seg, keep, prev_src, k)
        mid_sentence += msgs
        if mid_drops:   # how long the reel gets with those clauses back (unsnapped piece lengths)
            full = build_segment(ws, {**seg, "drop": [x for x in seg["drop"] if x not in mid_drops]})[0]
            restore_s += sum(p[1] - p[0] for p in full) - sum(p[1] - p[0] for p in pieces)
        if k + 1 < len(d["aroll"]) and not ends_sentence(keep[-1]["w"]):
            mid_sentence.append(f"seg {k}: ends mid-sentence on '{keep[-1]['w']}'")
        for n in nums:
            n["seg"] = k
            if n["est_s"] and n["dur"] < n["est_s"]:
                n["suspect"] = (f"timed {n['dur']} s, saying it takes ~{n['est_s']} s: the rest of the number may "
                                f"sit in the gap after it (kept untightened)")
        numbers += nums
        x = source_audio(d, src) if d.get("snap_cuts", True) else None
        if d.get("snap_cuts", True) and x is None:
            warnings.append(f"seg {k}: no audio read from {src}, cut points not snapped")
        m = []
        for a, b, lim_a, lim_b in pieces:
            if x is not None:
                a, b = snap(x, a, *lim_a), snap(x, b, *lim_b)
                for edge, side in ((a, "in"), (b, "out")):
                    lv = level_db(x, edge)
                    cuts.append({"seg": k, "side": side, "src_t": edge, "db": lv})
                    if lv > LOUD_CUT_DB:
                        warnings.append(f"seg {k}: {side}-point at {edge:.3f} s lands on sound ({lv} dBFS > "
                                        f"{LOUD_CUT_DB:g}): listen for a leaked syllable")
            m.append((a, b, t))
            timeline.append({"t": round(t, 2), "kind": "aroll", "seg": k, "src": src,
                             "in": round(a, 3), "out": round(b, 3), "dur": round(b - a, 2),
                             "reframe": seg.get("reframe"), "note": seg.get("note")})
            t += b - a
        seg_maps.append(m)
        for w in keep:
            out_t = next((tt + (w["start"] - a) for a, b, tt in m if a <= w["start"] <= b), None)
            spoken.append({"w": w["w"], "t": round(out_t, 2), "e": round(out_t + w["end"] - w["start"], 2),
                           "seg": k, "src_t": w["start"]})
        if k == len(d["aroll"]) - 1:
            after = [w["w"] for w in ws[ws.index(keep[-1]) + 1:] if w["start"] < keep[-1]["end"] + 30][:15]
            ending = {"last_word": keep[-1]["w"], "next_words": " ".join(after),
                      "next_word_after_s": round(next_src["start"] - keep[-1]["end"], 2) if next_src else None}
            if not ends_sentence(keep[-1]["w"]):
                warnings.append(f"ending: last word '{keep[-1]['w']}' doesn't end a sentence")
            if next_src and next_src["start"] - keep[-1]["end"] < 0.6:
                warnings.append(f"ending: the speaker goes on {next_src['start'] - keep[-1]['end']:.2f} s after the "
                                f"out-point (\"{' '.join(after[:8])}...\"): does the thought close here?")
    last_end = spoken[-1]["e"]
    tail = d.get("ending_tail_s", TAIL)
    if "ending_hold_s" not in d and t - last_end > tail:     # the room-tone pad ran past the tail: trim the last piece
        cut = t - last_end - tail
        e = timeline[-1]
        e["out"], e["dur"] = round(e["out"] - cut, 3), round(e["dur"] - cut, 2)
        a, b, tt = seg_maps[-1][-1]
        seg_maps[-1][-1] = (a, b - cut, tt)
        t -= cut
    hold = d["ending_hold_s"] if "ending_hold_s" in d else round(max(0.0, tail - (t - last_end)), 3)
    total = t + hold
    ending["tail_s"] = round(total - last_end, 3)
    anchor_notes = []
    at = make_resolver(seg_maps, spoken, total, anchor_notes)

    overlays = []
    for o in d.get("overlays", []):
        o = place(o, at, round(total, 2))
        if o["kind"] == "hf_scene":
            if "cues" in o:
                o["cue_times"] = {n: round(at(a) - o["t"], 3) for n, a in o["cues"].items()}
            if "beats" in o:
                cues = o.get("cue_times", {})
                o["beat_times"] = [round(o["t"] + (b if isinstance(b, (int, float)) else
                                                   cues[b] if isinstance(b, str) and b in cues else at(b) - o["t"]), 2)
                                   for b in o["beats"]]
            if "matte_until" in o:
                mu = o["matte_until"]
                o["matte_until"] = (o.get("cue_times", {})[mu] if isinstance(mu, str) and mu in o.get("cue_times", {})
                                    else mu if isinstance(mu, (int, float)) else round(at(mu) - o["t"], 3))
            # "orange_from" may be a cue name or an anchor too (promo-02); build_captions needs seconds from the start
            of = o.get("orange_from")
            if of is not None and not isinstance(of, (int, float)):
                cue = o.get("cue_times", {}).get(of) if isinstance(of, str) else None
                o["orange_from"] = cue if cue is not None else round(at(of) - o["t"], 3)
        overlays.append(o)
    overlays.sort(key=lambda o: o["t"])
    layout = sorted((place(l, at, "end") for l in d.get("layout", [])), key=lambda l: l["t"])
    for l, nxt in zip(layout, layout[1:] + [None]):
        l.setdefault("t_out", nxt["t"] if nxt else "end")
    seg_cuts = sorted({q(next(e["t"] for e in timeline if e["seg"] == k)) for k in {e["seg"] for e in timeline}})
    synced = []

    def on_cut(v, what):
        """A layout edge within 3 frames of an A-roll cut moves onto the cut (promo-02: a switch 2 frames after
        the cut gave those 2 frames the next layout's look)."""
        v = q(v)
        near = min(seg_cuts, key=lambda c: abs(c - v))
        if 0 < abs(near - v) <= SNAP_FRAMES / FPS + 1e-6:
            synced.append(f"layout {what} {v} -> {near} (A-roll cut)")
            return near
        return v
    for l in layout:
        l["t"] = on_cut(l["t"], f"{l['mode']} t")
        if l["t_out"] != "end":
            l["t_out"] = on_cut(l["t_out"], f"{l['mode']} t_out")
    # picture switches: a new A-roll segment or a layout change (mode or punch); a graphic that dresses a switch
    # starts and ends on the switch's frame, not on the word (promo-02: bare ink for 2 frames)
    switches = sorted({q(e["t"]) for e in timeline if e is next(x for x in timeline if x["seg"] == e["seg"])}
                      | {l["t"] for i, l in enumerate(layout)
                         if i and (l["mode"], l.get("punch")) != (layout[i - 1]["mode"], layout[i - 1].get("punch"))})
    for o in overlays:
        for key in ("t", "t_out"):
            v = o.get(key)
            if not isinstance(v, (int, float)):
                continue
            v = q(v)
            near = min(switches, key=lambda s_: abs(s_ - v), default=None)
            if near is not None and key == "t" and o.get("flash_in"):
                near = q(near - 1 / FPS)     # a covering flash is at full cover on the cut frame: start 1 frame early
            if near is not None and 0 < abs(near - v) <= SNAP_FRAMES / FPS + 1e-6:
                synced.append(f"{Path(o.get('src', o['kind'])).stem} {key} {v} -> {near} (picture switch)")
                v = near
            o[key] = v
    sfx_track = sorted((place(h, at, round(total, 2)) for h in d.get("sfx_track", [])), key=lambda h: h["t"])
    cap_layout = dict(d.get("caption_layout") or {})
    if "mute" in cap_layout:
        cap_layout["mute"] = [[x if x == "end" else at(x) for x in r] for r in cap_layout["mute"]]

    text = " ".join(w["w"] for w in spoken)
    hits = sorted({m.group(0) for pat in kit.exclusions(d) for m in re.finditer(pat, text, re.I)})
    hook_words = " ".join(w["w"] for w in spoken if w["t"] < 3.0)
    out = {k: v for k, v in d.items() if k not in ("aroll", "overlays")}
    for key, val in (("layout", layout), ("sfx_track", sfx_track)):
        if val:
            out[key] = val
    if cap_layout:
        out["caption_layout"] = cap_layout
    out["events"] = timeline + overlays + [{"t": round(t, 2), "kind": "ending", "hold_s": hold,
                                             "type": d.get("ending_type", "payoff")}]
    changes, longest = visual_changes(out, total)
    lo, hi = kit.length_limits(d)
    if not lo <= total <= hi:
        warnings.append(f"length {total:.1f}s outside {lo:g}-{hi:g} s")
    if longest > 4.0:
        warnings.append(f"longest hold without a visual change {longest:.1f}s (> 4 s)")

    warnings += list(dict.fromkeys(anchor_notes))     # once each
    seg_span = {k: (min(e["t"] for e in timeline if e["seg"] == k),
                    max(e["t"] + e["dur"] for e in timeline if e["seg"] == k)) for k in {e["seg"] for e in timeline}}
    cuts_out = sorted({q(a) for a, _ in seg_span.values()} - {0.0})
    for o in overlays:
        name = Path(o.get("src", o["kind"])).stem
        # a covering transition is at full cover on the cut frame, so it starts at least 1 frame before it
        if o.get("flash_in"):
            cut = min(cuts_out + [l["t"] for l in layout], key=lambda c: abs(c - o["t"]), default=None)
            if cut is not None and abs(cut - o["t"]) < 0.3 and o["t"] > cut - 1 / FPS + 1e-6:
                warnings.append(f"{name}: flash_in starts at {o['t']} s but the cut it hides is at {cut} s: start it "
                                f"at {q(cut - 1 / FPS)} s or earlier, at full cover on the cut frame")
        # a cutout of the subject never runs past its A-roll segment (it would paint the old shot over the new one)
        if o.get("matte"):
            m_end = o["t"] + o["matte_until"] if "matte_until" in o else o.get("t_out", total)
            seg = next((k for k, (a, b) in seg_span.items() if a <= o["t"] < b), None)
            if seg is not None and q(m_end) > q(seg_span[seg][1]) + 1e-3:
                warnings.append(f"{name}: the matte runs to {m_end:.2f} s, past its A-roll segment's end "
                                f"({seg_span[seg][1]:.2f} s): end it (\"matte_until\") before the cut")
        # a punch-in moves the face (eyes to 37 %): a graphic placed against the 1.0 framing ends up on the chin
        if o["kind"] in ("hf_scene", "chip", "card") and not (o.get("background") or o.get("full_bleed")
                                                             or o.get("matte") or o.get("placed_for_punch")):
            o_end = o.get("t_out", total)
            for l in layout:
                l_end = total if l["t_out"] == "end" else l["t_out"]
                if l["mode"] == "full" and l.get("punch", 1.0) > 1.0 and l["t"] < o_end and o["t"] < l_end:
                    warnings.append(f"{name}: punch {l['punch']} at {l['t']}-{l_end} s under this graphic moves the "
                                    f"face; drop the punch, or place the graphic for the punched frame "
                                    f"(\"placed_for_punch\": true)")
                    break

    # SFX against the same rules qa.py applies after the render
    sfx = sfx_hits(out)
    sfx_problems = [f"SFX {a['t']} s and {b['t']} s are {b['t'] - a['t']:.1f} s apart (min {SFX_MIN_GAP:g} s)"
                    for a, b in zip(sfx, sfx[1:]) if b["t"] - a["t"] < SFX_MIN_GAP]
    for h in sfx:
        for i, w in enumerate(spoken):
            if (is_number(w["w"]) or is_name(spoken, i)) and w["t"] - 0.15 < h["t"] < w["e"] + 0.15:
                sfx_problems.append(f"SFX at {h['t']} s ({h['what']}) lands on '{w['w']}' being said")
    warnings += sfx_problems
    # on-screen text long enough to read
    for o in overlays:
        txt = (o.get("text") or "").replace("|", " ").split()
        if txt and isinstance(o.get("t_out"), (int, float)):
            need = 0.5 + 0.3 * len(txt)
            if o["t_out"] - o["t"] < need:
                warnings.append(f"{o['kind']} '{o['text']}' on screen {o['t_out'] - o['t']:.2f} s, needs {need:.1f} s "
                                f"to be read")
    for n in numbers:
        if n.get("suspect"):
            warnings.append(f"number '{n['w']}' (seg {n['seg']}): {n['suspect']}")
    if restore_s:
        mid_sentence.append(f"length with every dropped clause restored: {total + restore_s:.1f} s "
                            f"(this plan: {total:.1f} s)")

    out.setdefault("graphics_engine", "hyperframes")      # title cards, chips, data cards (build_graphics.py)
    out.update({"status": "draft", "length_s": round(total, 1), "hook_words_0_3s": hook_words,
                "spoken_text": text, "spoken_words": spoken, "exclusion_scan": hits or "clean",
                "pacing": {"visual_changes": len(changes) - 1, "longest_hold_s": round(longest, 1)},
                "checks": {"numbers": numbers, "mid_sentence": mid_sentence, "ending": ending, "synced": synced,
                           "sfx": sfx, "loudest_cuts": sorted(cuts, key=lambda c: -c["db"])[:5]},
                "warnings": warnings})
    dst = Path(path).with_name(Path(path).name.replace("_draft", "_edl"))
    dst.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{d['short']}: {total:.1f}s | hook 0-3s: \"{hook_words}\" | changes {len(changes) - 1}, "
          f"longest hold {longest:.1f}s | exclusion hits: {hits or 'none'}")
    print("  numbers (gap after each is never tightened):")
    for n in numbers:
        print(f"    '{n['w']}' seg {n['seg']} @{n['src_t']:.2f}: {n['dur']} s, gap after {n['gap_after']} s"
              + (f"  << {n['suspect']}" if n.get("suspect") else ""))
    print(f"  ending: '{ending.get('last_word')}' + {ending.get('tail_s')} s, then the speaker says: "
          f"\"{ending.get('next_words')}\"")
    for x in synced:
        print(f"  synced: {x}")
    print(f"  SFX: {[(h['t'], Path(h['what']).stem) for h in sfx] or 'none'}")
    if cuts:
        c = max(cuts, key=lambda c: c["db"])
        print(f"  cut points: {len(cuts)} snapped to the quietest 10 ms; loudest {c['db']} dBFS (seg {c['seg']} "
              f"{c['side']} @{c['src_t']:.3f})")
    for s in mid_sentence:
        print(f"  sentence: {s}")
    print(f"  warnings: {len(warnings)}")
    for w in warnings:
        print(f"    - {w}")
    print(f"  wrote {dst}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for p in sys.argv[1:]:
        main(p)
