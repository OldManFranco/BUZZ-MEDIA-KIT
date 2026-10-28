r"""
The Standard — v3.0 audio mix

CLAUDE.md v3.0 §Step 4 (source of truth)
Narration-led timeline. v2.4's mix_audio.py stays untouched; this file reuses
its voice compression and limiter mastering so loudness is identical
(-14 LUFS, limiter 0.75, delivery ~-14.5 LUFS / ~-1.6 dBTP).

Timeline (timeline.json, "format": "v3"):
  narration      {"files": {"narr": path, "pickup": path}} + edit[] pieces
                 ({src, src_start, src_end, tl_start, beat, text})
  speech_tl[]    climax clips ({name, tl_start}) from clips/cuts.json
  drop_tl_s      video time of the first climax speech word
  music.cues[]   1-2 tracks: {"file", "track_start_s", "tl_start_s", "tl_end_s"},
                 1.5s crossfade; the drop lands on the first climax speech word
  sfx[]          {"file", "tl_s", "gain_db"}; refused when the onset lands on a
                 narrated proper noun or number (word timings from the narration islands)
  total_s        video length incl. ring-out and sign-off
Music levels: -18 dB under narration (0.5s fade-in from 0:00), -12 between beats,
ramp -18 -> 0 over the pre-climax pause, -9.5 under speech, -14 under the lesson,
-4 ring-out under "Hold the standard.", 1s fade under the sign-off.

Outputs: --out mix.wav, mix_nomusic.wav next to it (same mastering gain, music
muted), --debug-json with clip starts, beat starts, music gain at key moments.

Usage:
    python mix_audio_v3.py --timeline working/<slug>/timeline.json --out working/<slug>/mix.wav \
        --debug-json working/<slug>/mix_debug.json
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mix_audio import (SR, LIMITER_CEILING, LIMITER_TARGET_LUFS, compress_voice,  # noqa: E402
                       crest_db, db_to_amp, load_mono, measure_lufs,
                       normalize_rms, place, ramp, to_frames, voiced_rms)

ROOT = Path(__file__).resolve().parent.parent
PAD_IN, PAD_OUT = 0.03, 0.06          # breathing room around each narration island
XFADE_S = 1.5


def load_timeline(path: str) -> dict:
    """Read timeline.json; stop unless "format" == "v3"."""
    tl = json.load(open(path, encoding="utf-8"))
    if tl.get("format") != "v3":
        sys.exit("mix_audio_v3.py: timeline.json is not \"format\": \"v3\" — run mix_audio.py for v2.4")
    return tl


def resolve(p: str) -> str:
    return p if os.path.isabs(p) else str(ROOT / p)


def protected_spans(tl: dict, slug_dir: Path) -> list[tuple[float, float, str]]:
    """Video-time spans of narrated proper nouns and numbers (no SFX onset allowed)."""
    islands = {"narr": [json.loads(l) for l in open(slug_dir / "narration_islands.jsonl", encoding="utf-8")],
               "pickup": [json.loads(l) for l in open(slug_dir / "pickup_islands.jsonl", encoding="utf-8")]}
    spans = []
    for e in tl["edit"]:
        isl = islands[e["src"]][0 if e["src"] == "pickup" else e["i"]]
        toks, rel = isl["tokens"], isl["rel_timestamps"]
        words, cur = [], None
        for t, r in zip(toks, rel):
            if t.startswith(" ") or cur is None:
                cur = [t.strip(), r, r]
                words.append(cur)
            else:
                cur[0] += t
            cur[2] = r
        for k, (w, a, b) in enumerate(words):
            core = re.sub(r"[^\w']", "", w)
            nxt = words[k + 1][1] if k + 1 < len(words) else b + 0.3
            if any(ch.isdigit() for ch in core) or (core[:1].isupper() and k > 0) or core.lower() in (
                    "july", "jordan", "michael", "james", "nineteen", "thirtieth", "eighth", "ninety", "hundred"):
                off = e["tl_start"] - e["src_start"] + isl["start_s"]
                spans.append((off + a - 0.05, off + nxt, core))
    return spans


def build_voice(tl: dict, n: int, slug_dir: Path) -> tuple[np.ndarray, dict]:
    """Narration + speech clips placed on the timeline, normalized and compressed."""
    files = {k: load_mono(resolve(v)) for k, v in tl["narration"]["files"].items()}
    narr = np.zeros(n, dtype=np.float32)
    for e in tl["edit"]:
        y = files[e["src"]]
        a = max(0, to_frames(e["src_start"] - PAD_IN))
        b = min(len(y), to_frames(e["src_end"] + PAD_OUT))
        piece = y[a:b].copy()
        f = min(len(piece) // 4, to_frames(0.015))
        piece[:f] *= ramp(f, 0, 1)
        piece[-f:] *= ramp(f, 1, 0)
        at = to_frames(e["tl_start"]) - (to_frames(e["src_start"]) - a)
        if at < 0:
            piece, at = piece[-at:], 0
        place(narr, piece, at)
    narr = narr * (db_to_amp(-16.0) / voiced_rms(narr))

    cuts = json.load(open(slug_dir / "clips" / "cuts.json", encoding="utf-8"))["clips"]
    by_name = {c["name"]: c for c in cuts}
    speech = np.zeros(n, dtype=np.float32)
    for s in tl["speech_tl"]:
        y = load_mono(resolve(by_name[s["name"]]["out_path"]))
        y = y * (db_to_amp(-16.0) / voiced_rms(y))
        place(speech, y.astype(np.float32), to_frames(s["tl_start"]))

    voice = narr + speech
    stats = {"voice_crest_before_db": round(crest_db(voice), 1)}
    vc = tl.get("voice_comp", True)
    if vc is not False:
        voice = compress_voice(voice, vc if isinstance(vc, dict) else {})
        stats["voice_crest_after_db"] = round(crest_db(voice), 1)
    return voice.astype(np.float32), stats


def music_envelope(tl: dict, n: int) -> np.ndarray:
    """Per-sample music gain (linear) following the v3 level table."""
    pts = []  # (time_s, dB)
    edit = tl["edit"]
    drop = tl["drop_tl_s"]
    speech = tl["speech_tl"]
    total = tl["total_s"]
    lesson = [e for e in edit if e["beat"] == 5]
    ring_start = lesson[-1]["tl_start"]                       # "Hold the standard."
    signoff = total - 1.0
    pts += [(0.0, -60.0), (0.5, -18.0)]
    for a, b in zip(edit, edit[1:]):                          # -12 in gaps between beats (1-4)
        if a["beat"] != b["beat"] and b["beat"] <= 4:
            g0, g1 = a["tl_end"], b["tl_start"]
            pts += [(g0 + 0.05, -18.0), (g0 + 0.2, -12.0), (g1 - 0.2, -12.0), (g1 - 0.02, -18.0)]
    last4 = max(e["tl_end"] for e in edit if e["beat"] == 4)
    pts += [(last4, -18.0), (drop - 0.02, 0.0), (drop + 0.25, -9.5)]
    for a, b in zip(speech, speech[1:]):                      # thought gaps lift a little
        if b["tl_start"] - a["tl_end"] > 0.8:
            pts += [(a["tl_end"] + 0.05, -9.5), (a["tl_end"] + 0.3, -6.0), (b["tl_start"] - 0.25, -6.0), (b["tl_start"] - 0.02, -9.5)]
    sp_end = speech[-1]["tl_end"]
    pts += [(sp_end + 0.05, -9.5), (sp_end + 0.4, -12.0), (lesson[0]["tl_start"] - 0.05, -14.0),
            (ring_start - 0.3, -14.0), (ring_start, -4.0), (signoff, -4.0), (total, -60.0)]
    pts.sort()
    t = np.arange(n) / SR
    db = np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    return (10 ** (db / 20.0)).astype(np.float32), pts


def build_music(tl: dict, n: int) -> tuple[np.ndarray, list]:
    """1-2 cues with crossfade and the v3 gain envelope."""
    bed = np.zeros(n, dtype=np.float32)
    cues = tl["music"]["cues"]
    cache = {}
    for i, c in enumerate(cues):
        y = cache.setdefault(c["file"], load_mono(resolve(c["file"])))
        y = normalize_rms(y, -16.0)
        a = to_frames(c["tl_start_s"])
        b = min(n, to_frames(c["tl_end_s"]))
        s0 = to_frames(c["track_start_s"])
        piece = y[s0:s0 + (b - a)].copy()
        piece = np.pad(piece, (0, max(0, (b - a) - len(piece))))
        xf = to_frames(XFADE_S)
        if i > 0:
            piece[:xf] *= ramp(xf, 0, 1)
        if i < len(cues) - 1:
            piece[-xf:] *= ramp(xf, 1, 0)
        place(bed, piece, a)
    env, pts = music_envelope(tl, n)
    return bed * env, pts


def build_sfx(tl: dict, n: int, spans: list) -> tuple[np.ndarray, list]:
    """SFX layer, ~12 dB under the voice; stops on an onset inside a protected span."""
    out = np.zeros(n, dtype=np.float32)
    log = []
    for s in tl.get("sfx", []):
        hit = [w for a, b, w in spans if a <= s["tl_s"] < b]
        if hit:
            sys.exit(f"mix_audio_v3.py: SFX {s['file']} at {s['tl_s']}s lands on narrated '{hit[0]}' — move it")
        y = load_mono(resolve(s["file"]))
        if "max_s" in s:
            y = y[:to_frames(s["max_s"])]
            f = to_frames(0.2)
            y[-f:] *= ramp(f, 1, 0)
        y = y * (db_to_amp(-28.0 + s.get("gain_db", 0.0)) / voiced_rms(y))
        place(out, y.astype(np.float32), to_frames(s["tl_s"]))
        log.append({"file": os.path.basename(s["file"]), "tl_s": s["tl_s"]})
    return out, log


def _limit_af(gain_db: float, limit: float) -> str:
    """v2.4's normalize-then-limit chain, but the limiter runs 4x oversampled so it
    also catches inter-sample peaks (TTS consonants overshot to +2 dBTP after AAC).
    A 16 kHz low-pass first removes the near-Nyquist TTS energy that rang past the
    limiter on the way back down to 48 kHz."""
    return (f"volume={gain_db:.2f}dB,lowpass=f=16000:poles=2,aresample=192000,"
            f"alimiter=limit={limit}:attack=5:release=60:asc=1:level=disabled,"
            f"aresample=48000")


def master_limiter(mix_path: str, out_path: str, target_i: float, limit: float) -> dict:
    """Same as mix_audio.master_limiter (gain to target, limit, one correction pass), oversampled."""
    i0, _ = measure_lufs(mix_path)
    gain = target_i - i0
    for _ in range(2):
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mix_path,
                            "-af", _limit_af(gain, limit), "-ar", "48000", out_path],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"master limiter failed: {r.stderr}")
        i1, tp1 = measure_lufs(out_path)
        if abs(target_i - i1) < 0.1:
            break
        gain += target_i - i1
    return {"input_i": i0, "gain_db": round(gain, 2), "output_i": i1, "output_tp": tp1}


def write(path: str, y: np.ndarray) -> None:
    sf.write(path, np.stack([y, y], axis=1), SR, subtype="FLOAT")


def master_same_gain(src: str, out: str, gain_db: float, limit: float) -> None:
    af = _limit_af(gain_db, limit)
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
                        "-af", af, "-ar", "48000", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--debug-json", default=None)
    args = ap.parse_args()
    tl = load_timeline(args.timeline)
    slug_dir = Path(args.timeline).resolve().parent
    n = to_frames(tl["total_s"])

    voice, vstats = build_voice(tl, n, slug_dir)
    music, env_pts = build_music(tl, n)
    spans = protected_spans(tl, slug_dir)
    sfx, sfx_log = build_sfx(tl, n, spans)

    out = Path(args.out)
    raw_full = str(out.with_name(out.stem + "_raw.wav"))
    raw_nom = str(out.with_name("mix_nomusic_raw.wav"))
    write(raw_full, voice + music + sfx)
    write(raw_nom, voice + sfx)
    target = tl.get("master_target_lufs", LIMITER_TARGET_LUFS)
    limit = tl.get("master_limit", LIMITER_CEILING)
    m = master_limiter(raw_full, str(out), target, limit)
    nomusic = str(out.with_name("mix_nomusic.wav"))
    master_same_gain(raw_nom, nomusic, m["gain_db"], limit)
    i_nm, tp_nm = measure_lufs(nomusic)
    print(f"mix: {m['output_i']:.1f} LUFS / {m['output_tp']:.1f} dBTP  ({out})")
    print(f"nomusic: {i_nm:.1f} LUFS / {tp_nm:.1f} dBTP  ({nomusic}) — same gain, music muted")

    if args.debug_json:
        json.dump({"format": "v3", "total_s": tl["total_s"], "voice": vstats, "master": m,
                   "nomusic": {"lufs": i_nm, "tp": tp_nm}, "music_env_db": env_pts,
                   "sfx": sfx_log, "protected_spans": [(round(a, 2), round(b, 2), w) for a, b, w in spans],
                   "speech_tl": tl["speech_tl"], "drop_tl_s": tl["drop_tl_s"]},
                  open(args.debug_json, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
