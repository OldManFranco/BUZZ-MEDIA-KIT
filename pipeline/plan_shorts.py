r"""
Buzz Media kit — steps 4-5 helper: turn a draft EDL into a timed plan and check it.

A draft lists A-roll segments in order (raw clip + word-snapped in/out) and
overlays anchored to a source moment. This script:
  - tightens every pause > 0.30 s inside a segment to 0.15 s (CLAUDE.md §5/§9; draft "gap_max"/"gap_new" override),
    except gaps listed in "keep_gaps" (breaths before a payoff), and drops "drop" ranges
  - pads each splice with room tone (0.06 s before the first word, 0.08 s after the last)
  - assigns output time t to every segment and overlay, adds the ending hold
  - prints the words heard in 0-3 s, total length, cut count, longest hold
  - scans the spoken text for the client's exclusion keywords (kit.exclusions)
  - warns on interpolated words at a cut edge, length outside the reel's min_s-max_s (default 15-60 s),
    a hold over 4 s without a visual change
Writes the timed EDL next to the draft (s<N>_edl.json) and a text summary.
Draft needs "project_dir" (kit.Project); each segment's "clip" is a transcript stem in <project>\working\transcripts\
(e.g. "promo-01" for raw\promo-01.mkv).

Usage:
  python pipeline/plan_shorts.py clients/<client>/projects/<project>/working/plans/s1_draft.json [...]
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

MAX_GAP, NEW_GAP = 0.30, 0.15
PAD_IN, PAD_OUT = 0.06, 0.08
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


def build_segment(ws, seg):
    """Return pieces [(src_in, src_out)] after dropping ranges and tightening gaps, plus the words kept."""
    drops = seg.get("drop", [])
    keep = [w for w in ws if w["start"] >= seg["in"] - 0.01 and w["end"] <= seg["out"] + 0.01
            and not any(a - 0.01 <= w["start"] and w["end"] <= b + 0.01 for a, b in drops)]
    if not keep:
        raise ValueError(f"no words in segment {seg}")
    pieces, cur = [], [keep[0]["start"] - PAD_IN, None]
    for prev, w in zip(keep, keep[1:]):
        gap = w["start"] - prev["end"]
        dropped_between = any(prev["end"] - 0.01 <= a and b <= w["start"] + 0.01 for a, b in drops)
        kept_gap = any(abs(prev["end"] - g) < 0.05 for g in seg.get("keep_gaps", []))
        if (gap > MAX_GAP and not kept_gap) or dropped_between:
            half = min(gap, NEW_GAP) / 2
            cur[1] = prev["end"] + half
            pieces.append(tuple(cur))
            cur = [w["start"] - half, None]
    cur[1] = keep[-1]["end"] + PAD_OUT
    pieces.append(tuple(cur))
    return pieces, keep


def main(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    global MAX_GAP, NEW_GAP
    MAX_GAP, NEW_GAP = d.get("gap_max", MAX_GAP), d.get("gap_new", NEW_GAP)
    t, timeline, spoken, warnings = 0.0, [], [], []
    seg_maps = []
    for k, seg in enumerate(d["aroll"]):
        ws = words_for(d, seg["clip"])
        pieces, keep = build_segment(ws, seg)
        for edge in (keep[0], keep[-1]):
            if edge.get("interpolada"):
                warnings.append(f"seg {k}: cut edge on interpolated word '{edge['w']}'")
        m = []
        for a, b in pieces:
            m.append((a, b, t))
            timeline.append({"t": round(t, 2), "kind": "aroll", "seg": k,
                             "src": source_for(d, seg["clip"]),
                             "in": round(a, 3), "out": round(b, 3), "dur": round(b - a, 2),
                             "reframe": seg.get("reframe"), "note": seg.get("note")})
            t += b - a
        seg_maps.append(m)
        for w in keep:
            src_t = w["start"]
            out_t = next((tt + (src_t - a) for a, b, tt in m if a <= src_t <= b), None)
            spoken.append({"w": w["w"], "t": round(out_t, 2), "seg": k, "src_t": src_t})
    hold = d.get("ending_hold_s", 0.6)
    total = t + hold

    def src_to_out(seg, src_t):
        for a, b, tt in seg_maps[seg]:
            if a - 0.3 <= src_t <= b + 0.3:
                return round(tt + max(0.0, src_t - a), 2)
        raise ValueError(f"anchor {seg}@{src_t} falls in a removed gap")

    overlays = []
    for o in d.get("overlays", []):
        o = dict(o)
        if "anchor" in o:
            o["t"] = src_to_out(*o.pop("anchor"))
        if o.get("until") == "end":                     # runs through the ending hold
            o.pop("until")
            o["t_out"] = round(total, 2)
        elif "until" in o:
            o["t_out"] = src_to_out(*o.pop("until"))
        overlays.append(o)
    overlays.sort(key=lambda o: o["t"])

    text = " ".join(w["w"] for w in spoken)
    hits = sorted({m.group(0) for pat in kit.exclusions(d) for m in re.finditer(pat, text, re.I)})
    hook_words = " ".join(w["w"] for w in spoken if w["t"] < 3.0)
    # visual changes: every aroll piece from a new segment or reframe change, plus overlays with picture
    seg_starts = {next(e["t"] for e in timeline if e["seg"] == k) for k in range(len(d["aroll"]))}
    picture = {"broll", "punch_in", "chip", "card", "title_card", "reframe"}
    changes = sorted(seg_starts | {o["t"] for o in overlays if o["kind"] in picture}
                     | {o["t_out"] for o in overlays if o["kind"] in picture and "t_out" in o}
                     | {round(total, 2)})
    longest = max(b - a for a, b in zip(changes, changes[1:])) if len(changes) > 1 else total
    lo, hi = kit.length_limits(d)
    if not lo <= total <= hi:
        warnings.append(f"length {total:.1f}s outside {lo:g}-{hi:g} s")
    if longest > 4.0:
        warnings.append(f"longest hold without a visual change {longest:.1f}s (> 4 s)")

    out = {k: v for k, v in d.items() if k not in ("aroll", "overlays")}
    out.setdefault("graphics_engine", "hyperframes")      # title cards, chips, data cards (build_graphics.py)
    out.update({"status": "draft", "length_s": round(total, 1), "hook_words_0_3s": hook_words,
                "events": timeline + overlays + [{"t": round(t, 2), "kind": "ending", "hold_s": hold,
                                                  "type": d.get("ending_type", "payoff")}],
                "spoken_text": text, "spoken_words": spoken, "exclusion_scan": hits or "clean",
                "pacing": {"visual_changes": len(changes) - 1, "longest_hold_s": round(longest, 1)},
                "warnings": warnings})
    dst = Path(path).with_name(Path(path).name.replace("_draft", "_edl"))
    dst.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{d['short']}: {total:.1f}s | hook 0-3s: \"{hook_words}\" | changes {len(changes) - 1}, "
          f"longest hold {longest:.1f}s | exclusion hits: {hits or 'none'} | warnings: {warnings or 'none'}")
    print(f"  wrote {dst}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for p in sys.argv[1:]:
        main(p)
