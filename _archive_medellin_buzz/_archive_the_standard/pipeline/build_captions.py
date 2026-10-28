"""
The Standard — Step 9: Captions (LOCKED one-caption-at-a-time)

CLAUDE.md v2.4 §Pipeline Step 9 (source of truth)

Caption source of truth (v2.4):
  Each clip's "expected" text from cuts.json is distributed over Parakeet
  word timings within that clip, matched by TEXT via difflib (not by
  proportional index). No per-video fix-up map.

Timing:
  Forced-align on the FINAL cut clips, never the raw transcript.
  Rebuild after any audio change.

Snap after silence:
  Any word following >=120ms silence snaps to the first voiced sample
  (-55 dB voiced detector, --snap-dbfs to change). Tolerance +-0.25s.

One-caption-at-a-time:
  Each chunk ends at least 1 frame (33ms) before the next starts.
  Never extend past the next chunk's start.
  If a chunk would be shorter than ~0.2s, merge with its neighbor — only
  when the merged chunk still fits (<=3 words AND <=900px).
  Rebalance pass lengthens short captions (toward >=0.2s) without moving
  any start more than 0.14s from its word.
  QA assertion: no two Main-layer events overlap in time.

Chunking:
  At most 3 words per chunk. At most ~900px wide at 200px Anton
  (measured with PIL at the real font). Break on punctuation and on
  gaps >0.35s. Long single words scale down to fit 960px.

Style (LOCKED):
  ALL CAPS. Font Anton. Styles W (200px) and P (225px, emphasis).
  Emphasis words are marked with asterisks in cuts.json "expected"
  (e.g. "you made a *mistake*"); each is its own caption in style P.
  Small words (THE/A/I/WERE/...) never get P.
  Every word is TWO Dialogue lines (halo + text).
  Position x=540, y=1380, fixed every word, every video.

Outputs:
  --out-ass          the .ass file for ffmpeg's subtitles filter
  --out-chunks-json  chunks with start/end/text/style and the measured time
                     of each chunk's first word (qa.py checks +-0.15s)
"""
import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

try:
    from PIL import ImageFont
    import soundfile as sf
    import librosa
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr); sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe_islands import (DEFAULT_MODEL_DIR, SAMPLE_RATE, build_recognizer,
                                db_envelope, load_audio_mono_16k, recognize)


ROOT = Path(__file__).resolve().parent.parent
Y_POS = 1380
X_POS = 540
MAIN_LAYER = 0  # halo
TEXT_LAYER = 1
STYLE_W = "W"   # Anton 200
STYLE_P = "P"   # Anton 225 (emphasis)
FONT_PX = {STYLE_W: 200, STYLE_P: 225}
MAX_WIDTH_PX = 900
MAX_SINGLE_WORD_PX = 960
MAX_WORDS_PER_CHUNK = 3
MIN_CHUNK_DUR_S = 0.20
BACK_TO_BACK_GAP_S = 0.15
FRAME_MS = 33          # one-caption-at-a-time pre-end gap
SNAP_AFTER_SILENCE_MS = 120
SNAP_TOLERANCE_S = 0.25
WORD_TOL_S = 0.14      # a caption may start at most this far from its word (QA: 0.15)
SMALL_WORDS = {"THE", "A", "AN", "I", "WERE", "WAS", "IS", "ARE", "TO", "OF",
               "AND", "OR", "IN", "ON", "AT", "IT", "BE", "ME", "MY", "YOU",
               "HE", "SHE", "WE", "SO", "BUT", "FOR", "AS", "THAT", "THIS"}

_recognizer = None


def get_recognizer(model_dir: str):
    """Build the Parakeet recognizer once and reuse it for every clip."""
    global _recognizer
    if _recognizer is None:
        _recognizer = build_recognizer(model_dir)
    return _recognizer


def transcribe_clip_words(pcm: np.ndarray, model_dir: str) -> list:
    """Return [(word, start_s_in_clip, is_terminal_punct), ...] for a clip."""
    r = recognize(get_recognizer(model_dir), pcm)
    toks = r["tokens"]
    ts = r["timestamps"]
    # Join subword tokens into words. A new word starts when token begins with
    # a space.
    words = []
    cur = ""
    cur_t = None
    for t, s in zip(toks, ts):
        if t.startswith(" ") and cur:
            words.append((cur, cur_t, cur.rstrip()[-1] in ".!?,;"))
            cur = ""
            cur_t = None
        if cur_t is None:
            cur_t = s
        cur += t
    if cur.strip():
        words.append((cur, cur_t, cur.rstrip()[-1] in ".!?,;"))
    return [(w.strip(), t, p) for w, t, p in words if w.strip()]


def voiced_onsets(pcm: np.ndarray, dbfs: float = -55.0, frame_ms: int = 10,
                  min_silence_ms: int = SNAP_AFTER_SILENCE_MS) -> list:
    """Times (s) where voice starts after >= min_silence_ms of silence.

    The clip start counts as preceded by silence (clips are cut at island edges).
    """
    frame = int(SAMPLE_RATE * frame_ms / 1000)
    voiced = db_envelope(pcm, frame) > dbfs
    need = min_silence_ms // frame_ms
    onsets = []
    silent_run = need  # treat clip start as after silence
    for i, v in enumerate(voiced):
        if v:
            if silent_run >= need:
                onsets.append(i * frame_ms / 1000.0)
            silent_run = 0
        else:
            silent_run += 1
    return onsets


def snap_after_silence(times: list, onsets: list,
                       tol_s: float = SNAP_TOLERANCE_S) -> list:
    """Snap each word that follows a silence to that silence's voiced onset.

    Each onset goes to its nearest word within +-tol_s; a word keeps its
    order between its neighbours (never moves past them).
    """
    out = list(times)
    claimed = {}
    for o in onsets:
        j = int(np.argmin([abs(t - o) for t in times])) if times else -1
        if j < 0 or abs(times[j] - o) > tol_s:
            continue
        if j not in claimed or abs(o - times[j]) < abs(claimed[j] - times[j]):
            claimed[j] = o
    for j in sorted(claimed):
        o = claimed[j]
        lo = out[j - 1] + 0.05 if j > 0 else -1e9
        hi = times[j + 1] - 0.05 if j + 1 < len(times) else 1e9
        if lo < o < hi:
            out[j] = o
    return out


def parse_expected(text: str) -> list:
    """'you made a *mistake*.' -> [('YOU', False), ..., ('MISTAKE.', True)]"""
    out = []
    for raw in text.split():
        emph = "*" in raw
        w = raw.replace("*", "").upper()
        if w:
            core = re.sub(r"[^A-Z0-9']", "", w)
            out.append((w, emph and core not in SMALL_WORDS))
    return out


def chunk_words(words: list, font_path: str = None) -> list:
    """Group (word, t_video, is_punct, is_emph) tuples into caption chunks."""
    fonts = {}
    for style, px in FONT_PX.items():
        try:
            fonts[style] = ImageFont.truetype(font_path, px) if font_path else None
        except Exception:
            fonts[style] = None

    def measure(text, style=STYLE_W):
        font = fonts[style]
        if font is None:
            return len(text) * FONT_PX[style] * 0.55
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    # An emphasis word is always its own chunk, so P (225px) never lands on
    # the small words around it.
    chunks = []  # (start, text, emph, first_word_t)
    cur_words = []
    cur_start = None
    for i, (w, t_video, is_punct, is_emph) in enumerate(words):
        if is_emph:
            if cur_words:
                chunks.append((cur_start, " ".join(cur_words), False, cur_start))
                cur_words = []
            chunks.append((t_video, w, True, t_video))
            continue
        if not cur_words:
            cur_start = t_video
        candidate = cur_words + [w]
        text = " ".join(candidate)
        over_width = measure(text) > MAX_WIDTH_PX
        over_count = len(candidate) > MAX_WORDS_PER_CHUNK
        gap_next = (words[i + 1][1] - t_video) if i + 1 < len(words) else 1e9
        if over_width or over_count:
            if cur_words:
                chunks.append((cur_start, " ".join(cur_words), False, cur_start))
            cur_words = [w]
            cur_start = t_video
            if is_punct or gap_next > 0.35:
                chunks.append((cur_start, w, False, cur_start))
                cur_words = []
        else:
            cur_words.append(w)
            if is_punct or gap_next > 0.35:
                chunks.append((cur_start, " ".join(cur_words), False, cur_start))
                cur_words = []
    if cur_words:
        chunks.append((cur_start, " ".join(cur_words), False, cur_start))

    # Compute end times (one-caption-at-a-time)
    out = []
    for i, (start, text, emph, word_t) in enumerate(chunks):
        if i + 1 < len(chunks):
            end = chunks[i + 1][0] - FRAME_MS / 1000.0
        else:
            end = start + max(0.4, 0.12 * len(text.split()))
        out.append({"start": round(start, 3), "end": round(end, 3), "text": text,
                    "emph": emph, "word_t": round(word_t, 3)})

    # Merge too-short chunks into a neighbor — but ONLY if the merged chunk
    # still respects the word-count and width limits. (v1 bug: merging
    # without re-checking produced "GOOD AS MAGIC JOHNSON" at 1883px.)
    def fits(text):
        return (len(text.split()) <= MAX_WORDS_PER_CHUNK
                and measure(text) <= MAX_WIDTH_PX)

    # Emphasis chunks never merge (the rebalance pass below lengthens them).
    merged = []
    i = 0
    while i < len(out):
        c = out[i]
        short = c["end"] - c["start"] < MIN_CHUNK_DUR_S and not c["emph"]
        if (short and merged and not merged[-1]["emph"]
                and fits(merged[-1]["text"] + " " + c["text"])):
            merged[-1]["text"] = merged[-1]["text"] + " " + c["text"]
            merged[-1]["end"] = c["end"]
        elif (short and i + 1 < len(out) and not out[i + 1]["emph"]
                and fits(c["text"] + " " + out[i + 1]["text"])):
            out[i + 1]["text"] = c["text"] + " " + out[i + 1]["text"]
            out[i + 1]["start"] = c["start"]
            out[i + 1]["word_t"] = c["word_t"]
        else:
            merged.append(c)  # keep as-is rather than break the width rule
        i += 1

    # Rebalance any chunk still shorter than MIN_CHUNK_DUR_S (it couldn't merge).
    # Borrow time from its neighbours, but never move any caption's start more
    # than WORD_TOL_S from its word (the QA timing rule wins over the 0.2s
    # floor): first push the next caption's start later, then pull this
    # caption's start earlier. Neighbours keep at least MIN_CHUNK_DUR_S.
    gap = FRAME_MS / 1000.0
    for _ in range(3):
        changed = False
        for i, c in enumerate(merged):
            need = MIN_CHUNK_DUR_S - (c["end"] - c["start"])
            if need <= 1e-6:
                continue
            if i + 1 < len(merged):
                n = merged[i + 1]
                room = min(n["word_t"] + WORD_TOL_S - n["start"],
                           (n["end"] - n["start"]) - MIN_CHUNK_DUR_S)
                d = max(0.0, min(need, room))
                if d > 0:
                    n["start"] = round(n["start"] + d, 3)
                    c["end"] = round(n["start"] - gap, 3)
                    need -= d
                    changed = True
            if need > 1e-6:
                lo = c["word_t"] - WORD_TOL_S
                lo = max(lo, merged[i - 1]["start"] + MIN_CHUNK_DUR_S + gap) if i > 0 else max(lo, 0.0)
                d = max(0.0, min(need, c["start"] - lo))
                if d > 0:
                    c["start"] = round(c["start"] - d, 3)
                    if i > 0:
                        merged[i - 1]["end"] = round(c["start"] - gap, 3)
                    changed = True
        if not changed:
            break

    # Style + scale. Chunks over the single-word limit (long single words, or
    # an emphasis chunk at 225px) are scaled down to fit.
    for c in merged:
        c["style"] = STYLE_P if c.pop("emph") else STYLE_W
        w = measure(c["text"], c["style"])
        c["scale"] = round(min(1.0, MAX_SINGLE_WORD_PX / w), 3) if w > 0 else 1.0

    # Final assertion: no two chunks overlap
    for i in range(len(merged) - 1):
        assert merged[i]["end"] <= merged[i + 1]["start"], \
            f"Overlap at chunks {i}/{i+1}: {merged[i]} vs {merged[i+1]}"

    return merged


def s_to_ass(t: float) -> str:
    cs = int(round(t * 100))
    h = cs // 360000
    cs -= h * 360000
    m = cs // 6000
    cs -= m * 6000
    s = cs // 100
    cs -= s * 100
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(chunks: list, out_path: str, video_w=1080, video_h=1920):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {STYLE_W},Anton,200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0,0
Style: {STYLE_P},Anton,225,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    halo_tpl = ("{{\\pos({x},{y})\\fad(60,{fo})\\fscx{s0}\\fscy{s0}"
                "\\t(0,100,\\fscx{s1}\\fscy{s1})\\bord18\\shad0\\blur22"
                "\\3c&H000000&\\3a&H28&\\1a&HFF&}}{text}")
    text_tpl = ("{{\\pos({x},{y})\\fad(60,{fo})\\fscx{s0}\\fscy{s0}"
                "\\t(0,100,\\fscx{s1}\\fscy{s1})\\bord5\\shad0\\blur0.6}}{text}")

    events = []
    for i, c in enumerate(chunks):
        text_up = c["text"].upper()
        start = s_to_ass(c["start"])
        end = s_to_ass(c["end"])
        k = c.get("scale", 1.0)
        s0, s1 = round(78 * k), round(100 * k)
        # Back-to-back with the next chunk (gap <0.15s): no fade-out, hard cut.
        back_to_back = (i + 1 < len(chunks)
                        and chunks[i + 1]["start"] - c["end"] < BACK_TO_BACK_GAP_S)
        fo = 0 if back_to_back else 80
        style = c.get("style", STYLE_W)
        halo = halo_tpl.format(x=X_POS, y=Y_POS, text=text_up, s0=s0, s1=s1, fo=fo)
        text = text_tpl.format(x=X_POS, y=Y_POS, text=text_up, s0=s0, s1=s1, fo=fo)
        events.append(f"Dialogue: {MAIN_LAYER},{start},{end},{style},,0,0,0,,{halo}")
        events.append(f"Dialogue: {TEXT_LAYER},{start},{end},{style},,0,0,0,,{text}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")


# ---------------------------------------------------------------------------
# v3.0 (CLAUDE.md v3.0 Step 8) — opt-in with --format v3.
# Narration text = script.json "display"; speech text = cuts.json "expected".
# Both are aligned (difflib, by text) to Parakeet words recognized on the FINAL
# voice mix (mix_nomusic.wav) inside each narration piece / speech clip window.
# Captions are muted inside segments marked "mute_captions" (brand_lockup etc.).
# ---------------------------------------------------------------------------
def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def _align(desired, rec):
    """desired: [(word, emph)], rec: [(word, t_abs)] -> list of times (interpolated)."""
    d_norm = [_norm(w) for w, _ in desired]
    r_norm = [_norm(w) for w, _ in rec]
    times = [None] * len(desired)
    sm = difflib.SequenceMatcher(a=d_norm, b=r_norm, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = rec[blk.b + k][1]
    if times[0] is None:
        times[0] = rec[0][1]
    if times[-1] is None:
        times[-1] = max(rec[-1][1], times[0])
    j = 0
    while j < len(times):
        if times[j] is None:
            k = j
            while times[k] is None:
                k += 1
            t0, t1 = times[j - 1], times[k]
            for q in range(j, k):
                times[q] = t0 + (t1 - t0) * (q - j + 1) / (k - j + 1)
            j = k
        j += 1
    return times


def _window_words(pcm, t0, t1, model_dir, snap_dbfs):
    a, b = max(0, int(t0 * SAMPLE_RATE)), int(t1 * SAMPLE_RATE)
    seg = pcm[a:b]
    words = transcribe_clip_words(seg, model_dir)
    onsets = [t0 + o for o in voiced_onsets(seg, dbfs=snap_dbfs)]
    return [(w, t0 + t) for w, t, _ in words], onsets


def main_v3(args):
    slug_dir = Path(args.timeline).resolve().parent
    tl = json.load(open(args.timeline, encoding="utf-8"))
    segs = json.load(open(slug_dir / "segments.json", encoding="utf-8"))
    script = json.load(open(slug_dir / "script.json", encoding="utf-8"))
    cuts = json.load(open(args.cuts_json or slug_dir / "clips" / "cuts.json", encoding="utf-8"))["clips"]
    for doc, name in ((tl, "timeline.json"), (segs, "segments.json"), (script, "script.json")):
        if doc.get("format") != "v3":
            sys.exit(f"build_captions.py --format v3: {name} is not format v3")
    pcm = load_audio_mono_16k(str(slug_dir / "mix_nomusic.wav"))

    # Narration: all display words vs all recognized words across the edit pieces
    desired = []
    for b in script["beats"]:
        for snt in b["sentences"]:
            desired += parse_expected(snt["display"])
    rec, onsets = [], []
    for e in tl["edit"]:
        w, o = _window_words(pcm, e["tl_start"] - 0.05, e["tl_end"] + 0.12, args.model_dir, args.snap_dbfs)
        rec += w
        onsets += o
    n_times = _align(desired, rec)
    n_times = snap_after_silence(n_times, onsets)
    words = list(zip(desired, n_times))

    # Speech clips
    by_name = {c["name"]: c for c in cuts}
    for s in tl["speech_tl"]:
        d = parse_expected(by_name[s["name"]]["expected"])
        w, o = _window_words(pcm, s["tl_start"] - 0.03, s["tl_end"] + 0.08, args.model_dir, args.snap_dbfs)
        if not w:
            w = [("", s["tl_start"])]
        t = snap_after_silence(_align(d, w), o)
        words += list(zip(d, t))

    mutes = [(g["tl_start_s"], g["tl_start_s"] + g["out_dur_s"]) for g in segs["segments"] if g.get("mute_captions")]
    all_words = []
    for (w, emph), t in sorted(words, key=lambda x: x[1]):
        if any(a - 0.05 <= t < b for a, b in mutes):
            continue
        is_punct = w.rstrip().endswith((".", "!", "?", ",", ";"))
        shown = w.rstrip(",!?;:")
        # Strip the sentence period, but keep abbreviations whole (P.M.); a decimal like .202 is not one
        if "." not in shown.rstrip(".") or re.fullmatch(r"\$?\.?\d[\d.,]*\.", shown):
            shown = shown.rstrip(".")
        all_words.append((shown, round(t, 3), is_punct, emph))

    chunks = chunk_words(all_words, font_path=args.font_path)
    write_ass(chunks, args.out_ass)
    json.dump({"format": "v3", "chunks": chunks}, open(args.out_chunks_json, "w", encoding="utf-8"), indent=2)
    n_p = sum(1 for c in chunks if c["style"] == STYLE_P)
    print(f"wrote {args.out_ass} with {len(chunks)} caption chunks ({n_p} emphasis, {len(mutes)} muted spans)")
    for i in range(len(chunks) - 1):
        if chunks[i]["end"] > chunks[i + 1]["start"]:
            print(f"  OVERLAP {i}/{i+1}: {chunks[i]} vs {chunks[i+1]}")
            sys.exit(2)
    print("  overlap check: no overlapping captions OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeline", required=True,
                    help="timeline.json (clips_dir, clip_order)")
    ap.add_argument("--format", default="v2.4", choices=["v2.4", "v3"])
    ap.add_argument("--mix-stats", required=False,
                    help="mix_audio --debug-json output (clip_starts_s)")
    ap.add_argument("--cuts-json", required=False,
                    help="cuts.json from cut_speech (expected text per clip)")
    ap.add_argument("--out-ass", required=True)
    ap.add_argument("--out-chunks-json", required=True)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    ap.add_argument("--font-path", default=str(ROOT / "Anton-Regular.ttf"))
    ap.add_argument("--snap-dbfs", type=float, default=-55.0,
                    help="voiced detector for snap-after-silence (-40 for noisy sources)")
    args = ap.parse_args()
    if args.format == "v3":
        main_v3(args)
        return
    if not args.mix_stats:
        ap.error("--mix-stats is required for v2.4")

    with open(args.timeline, encoding="utf-8") as f:
        tl = json.load(f)
    with open(args.mix_stats, encoding="utf-8") as f:
        mix_stats = json.load(f)

    clips_dir = Path(tl["clips_dir"])
    clip_names = tl["clip_order"]
    clip_starts_s = mix_stats["clip_starts_s"]

    # For each clip we have the DESIRED caption text (what the audio actually
    # says, from cuts.json "expected"). We align desired words to Parakeet's
    # words by text and take Parakeet's measured times; unmatched words are
    # interpolated between matched neighbours.
    cuts_path = tl.get("cuts_json") or args.cuts_json
    with open(cuts_path, encoding="utf-8") as f:
        cuts = json.load(f)["clips"]
    expected_by_order = [c["expected"] for c in cuts]

    def norm(w):
        return re.sub(r"[^a-z0-9']", "", w.lower())

    all_words = []
    n_snapped = 0
    for i, (name, start_s) in enumerate(zip(clip_names, clip_starts_s)):
        clip_path = clips_dir / name
        desired = parse_expected(expected_by_order[i])
        if not desired:
            continue
        pcm = load_audio_mono_16k(str(clip_path))
        parakeet_words = transcribe_clip_words(pcm, args.model_dir)
        p_times = [t for (_, t, _) in parakeet_words]
        if not p_times:
            dur = len(pcm) / SAMPLE_RATE
            p_times = [j * (dur / max(1, len(desired) - 1)) for j in range(len(desired))]
            parakeet_words = [("", t, False) for t in p_times]
        p_norm = [norm(w) for (w, _, _) in parakeet_words]
        d_norm = [norm(w) for w, _ in desired]
        times = [None] * len(desired)
        sm = difflib.SequenceMatcher(a=d_norm, b=p_norm, autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = p_times[blk.b + k]
        if times[0] is None:
            times[0] = p_times[0]
        if times[-1] is None:
            times[-1] = max(p_times[-1], times[0])
        j = 0
        while j < len(times):
            if times[j] is None:
                k = j
                while times[k] is None:
                    k += 1
                t0, t1 = times[j - 1], times[k]
                for q in range(j, k):
                    times[q] = t0 + (t1 - t0) * (q - j + 1) / (k - j + 1)
                j = k
            j += 1

        snapped = snap_after_silence(times, voiced_onsets(pcm, dbfs=args.snap_dbfs))
        n_snapped += sum(1 for a, b in zip(times, snapped) if abs(a - b) > 1e-6)

        for (w, emph), t_clip in zip(desired, snapped):
            is_punct = w.rstrip().endswith((".", "!", "?", ",", ";"))
            # Strip sentence punctuation, but keep abbreviations whole (P.M., U.S.)
            shown = w.rstrip(",!?;:")
            if "." not in shown.rstrip("."):
                shown = shown.rstrip(".")
            all_words.append((shown, round(start_s + t_clip, 3), is_punct, emph))

    chunks = chunk_words(all_words, font_path=args.font_path)
    write_ass(chunks, args.out_ass)
    with open(args.out_chunks_json, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, indent=2)

    n_p = sum(1 for c in chunks if c["style"] == STYLE_P)
    print(f"wrote {args.out_ass} with {len(chunks)} caption chunks "
          f"({n_p} emphasis, {n_snapped} words snapped after silence)")

    # Overlap QA
    for i in range(len(chunks) - 1):
        if chunks[i]["end"] > chunks[i + 1]["start"]:
            print(f"  OVERLAP {i}/{i+1}: {chunks[i]} vs {chunks[i+1]}")
            sys.exit(2)
    print("  overlap check: no overlapping captions OK")


if __name__ == "__main__":
    main()
