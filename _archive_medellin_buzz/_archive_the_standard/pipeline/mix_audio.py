"""
The Standard — Step 5: Build the audio timeline

CLAUDE.md v2.4 §Pipeline Step 5 (source of truth)

Timeline:
  Hook narration from 0:00 over a music bed that also starts at 0:00
  (-18 dB, 0.5s fade-in).
  1.3–1.6s music-only pause on a quiet shot; music ramps bed -> 0 dB.
  Speech starts; music drop lands on the first word of the speech.
  Music ducking through speech, up to ring-out, 1s fade under sign-off.

Mix levels (CLAUDE.md):
  Under hook (bed) : -18 dB          (timeline key hook_bed_db)
  Pause (ramp-up)  : bed -> 0 dB
  Under speech     : -9.5 dB
  Short section pauses (inter-thought)  : -4 dB
  Ring-out         : -2.5 dB
  Sign-off         : fade out over 1s

Voice -> -16 dBFS RMS, then gentle voice compression (ratio 2, voice peaks
held <=14 dB over its RMS, voice level matched back so the balance is
unchanged). Master: normalize to -14 LUFS, then a lookahead limiter at 0.75
(~-2.5 dBFS). Delivery lands ~-14.5 LUFS / ~-1.6 dBTP after AAC encode.

Inputs:
  --timeline  JSON with clip order, gap/pause durations, hook & music paths,
              music_drop_s, music_end_s. Optional: hook_bed_db (-18),
              music_fade_in_s (0.5), music_enter_s (0.0). Legacy v2.3 key
              hook_enter_before_end_s still works if set explicitly.
              master_mode: "limiter" (default since 2026-10-23, see above) or
              "loudnorm" — the old v2.4 chain (two-pass loudnorm I=-13.3,
              TP=-2, 0.79 limiter, no voice compression), which lands under
              -15 LUFS on peaky live speech. Overrides: voice_comp
              (false / dict), master_target_lufs (-14), master_limit (0.75).
  --out       Output WAV path.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

try:
    import soundfile as sf
    import librosa
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr); sys.exit(2)


SR = 44100


def load_mono(path: str, sr: int = SR) -> np.ndarray:
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y.astype(np.float32)


def db_to_amp(db: float) -> float:
    return 10 ** (db / 20.0)


def ramp(n: int, start: float, end: float) -> np.ndarray:
    return np.linspace(start, end, n, dtype=np.float32)


def to_frames(seconds: float) -> int:
    return int(round(seconds * SR))


def ensure_len(y: np.ndarray, n: int) -> np.ndarray:
    if len(y) == n:
        return y
    if len(y) < n:
        return np.pad(y, (0, n - len(y)))
    return y[:n]


def place(dst: np.ndarray, src: np.ndarray, start_frame: int) -> None:
    """Add src into dst at start_frame (clipping if it extends past dst)."""
    end = min(len(dst), start_frame + len(src))
    if start_frame >= len(dst):
        return
    copy = min(len(src), end - start_frame)
    dst[start_frame:start_frame + copy] += src[:copy]


def normalize_rms(y: np.ndarray, target_dbfs: float = -16.0) -> np.ndarray:
    rms = np.sqrt(np.mean(y * y) + 1e-12)
    cur_db = 20 * np.log10(rms + 1e-12)
    gain = db_to_amp(target_dbfs - cur_db)
    return (y * gain).astype(np.float32)


VOICE_COMP_DEFAULTS = {     # "gentle" — tested best with the limiter master
    "threshold_db": -22.0,   # acompressor threshold (voice sits at -16 dBFS RMS)
    "ratio": 2.0,
    "attack_ms": 5.0,
    "release_ms": 120.0,
    "peak_crest_db": 14.0,   # then limit voice peaks to this far above its RMS
}
LIMITER_TARGET_LUFS = -14.0
LIMITER_CEILING = 0.75       # ~-2.5 dBFS; leaves room for AAC overshoot (lands ~-1.5 dBTP)


def voiced_rms(y: np.ndarray) -> float:
    v = y[np.abs(y) > 1e-4]
    return float(np.sqrt(np.mean(v * v) + 1e-12)) if len(v) else 1e-6


def crest_db(y: np.ndarray) -> float:
    return float(20 * np.log10((np.max(np.abs(y)) + 1e-12) / voiced_rms(y)))


def ff_filter(y: np.ndarray, af: str) -> np.ndarray:
    """Run a mono float32 buffer through an ffmpeg audio filter chain."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
         "-af", af, "-f", "f32le", "-"],
        input=y.astype(np.float32).tobytes(), capture_output=True)
    if r.returncode != 0:
        print(f"ffmpeg filter failed ({af}):", r.stderr.decode(errors="replace"), file=sys.stderr)
        sys.exit(2)
    return ensure_len(np.frombuffer(r.stdout, dtype=np.float32).copy(), len(y))


def compress_voice(voice: np.ndarray, cfg: dict) -> np.ndarray:
    """Tame voice peaks: compressor, match back to the original voiced RMS
    (voice/music balance unchanged), then a lookahead peak limiter at
    peak_crest_db above that RMS."""
    c = {**VOICE_COMP_DEFAULTS, **cfg}
    rms0 = voiced_rms(voice)
    out = ff_filter(voice, f"acompressor=threshold={c['threshold_db']}dB:ratio={c['ratio']}:"
                           f"attack={c['attack_ms']}:release={c['release_ms']}:knee=4")
    out = out * (rms0 / voiced_rms(out))
    peak = np.max(np.abs(out)) + 1e-12
    limit = rms0 * db_to_amp(c["peak_crest_db"])
    if limit < peak:
        # alimiter's limit must be <= 1: scale into range, limit, scale back
        k = 0.9 / peak
        out = ff_filter(out * k, f"alimiter=limit={limit * k:.5f}:attack=2:release=50:"
                                 f"level=disabled") / k
    return out.astype(np.float32)


def measure_lufs(path: str) -> tuple:
    """Integrated loudness and true peak of an audio file (ffmpeg loudnorm scan)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path,
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", r.stderr, flags=re.S)
    s = json.loads(m.group(0))
    return float(s["input_i"]), float(s["input_tp"])


def master_limiter(mix_path: str, out_path: str, target_i: float, limit: float) -> dict:
    """Normalize-then-limit mastering: gain the mix to target_i, then a
    lookahead limiter holds peaks at `limit`. One correction pass makes up
    the loudness the limiter took away."""
    i0, _ = measure_lufs(mix_path)
    gain = target_i - i0
    for _ in range(2):
        af = (f"volume={gain:.2f}dB,"
              f"alimiter=limit={limit}:attack=5:release=60:asc=1:level=disabled")
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                            "-i", mix_path, "-af", af, "-ar", "48000", out_path],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("master limiter failed:", r.stderr, file=sys.stderr)
            sys.exit(2)
        i1, tp1 = measure_lufs(out_path)
        if abs(target_i - i1) < 0.1:
            break
        gain += target_i - i1
    return {"input_i": i0, "gain_db": round(gain, 2), "output_i": i1, "output_tp": tp1}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--debug-json", default=None)
    args = ap.parse_args()

    with open(args.timeline, encoding="utf-8") as f:
        tl = json.load(f)

    hook_path = tl["hook_path"]
    music_path = tl["music_path"]
    clips_dir = Path(tl["clips_dir"])
    clip_names = tl["clip_order"]           # ordered list of clip filenames
    gaps = tl["gaps_s"]                     # len = len(clip_order) - 1
    assert len(gaps) == len(clip_names) - 1, "gaps mismatch"
    music_drop_s = tl["music_drop_s"]       # drop position in track
    music_end_s = tl["music_end_s"]         # real music end
    pause_s = tl["pause_s"]                 # pre-speech music-only pause
    ring_out_s = tl["ring_out_s"]           # after speech ends
    signoff_s = tl["signoff_s"]             # under sign-off card

    # Load pieces
    hook = normalize_rms(load_mono(hook_path), target_dbfs=-16.0)
    music = load_mono(music_path)
    speech_segments = []
    for name in clip_names:
        p = clips_dir / name
        y = load_mono(str(p))
        # Each clip already loudnormed; re-rms-normalize for consistency
        y = normalize_rms(y, target_dbfs=-16.0)
        speech_segments.append((name, y))

    # Build voice track
    hook_dur_s = len(hook) / SR
    # Hook starts at 0. Pre-speech position (video_speech_start) = hook_dur + pause
    speech_start_s = hook_dur_s + pause_s

    # Compose speech body with gaps
    voice_pieces = [hook]  # 0..hook_dur
    cur_s = hook_dur_s
    # pause fills itself as silence (we'll just skip voice during pause)
    cur_s += pause_s
    # record where each clip starts (video seconds)
    clip_starts_s = []
    for i, (name, y) in enumerate(speech_segments):
        clip_starts_s.append(cur_s)
        cur_s += len(y) / SR
        if i < len(gaps):
            cur_s += gaps[i]
    speech_end_s = cur_s
    video_total_s = speech_end_s + ring_out_s + signoff_s

    # Allocate master buffers
    total_frames = to_frames(video_total_s)
    voice = np.zeros(total_frames, dtype=np.float32)
    mus = np.zeros(total_frames, dtype=np.float32)

    # Place hook
    place(voice, hook, 0)
    # Place speech
    for (name, y), s in zip(speech_segments, clip_starts_s):
        place(voice, y, to_frames(s))

    # Optional voice compression (timeline key "voice_comp": true or a dict
    # overriding VOICE_COMP_DEFAULTS). Off when absent or false.
    voice_crest = {"before_db": round(crest_db(voice), 1)}
    master_mode = tl.get("master_mode", "limiter")
    # Limiter mastering turns gentle voice compression on unless voice_comp is false
    vc = tl.get("voice_comp", True if master_mode == "limiter" else None)
    if vc is not None and vc is not False:
        voice = compress_voice(voice, vc if isinstance(vc, dict) else {})
        voice_crest["after_db"] = round(crest_db(voice), 1)
        print(f"voice compressor: crest {voice_crest['before_db']} -> {voice_crest['after_db']} dB")

    # Compute music placement:
    # v2.4 default: music bed enters at 0:00 under the hook.
    if "hook_enter_before_end_s" in tl:  # legacy v2.3 timelines
        music_enter_video_s = hook_dur_s - tl["hook_enter_before_end_s"]
    else:
        music_enter_video_s = tl.get("music_enter_s", 0.0)
    # drop_video_s = speech_start_s (first speech word)
    drop_video_s = speech_start_s
    # Music is played continuously from enter time to end of video.
    # The track position at drop_video_s must equal music_drop_s.
    # track_pos(t_video) = track_entry + (t_video - music_enter_video_s)
    # Setting track_pos(drop_video_s) = music_drop_s =>
    track_entry_s = music_drop_s - (drop_video_s - music_enter_video_s)
    if track_entry_s < 0:
        print(f"ERROR: the music drop ({music_drop_s:.2f}s into the track) comes too "
              f"early: hook + pause need {drop_video_s - music_enter_video_s:.2f}s of "
              f"track before it. Pick a later drop or a shorter hook/pause.",
              file=sys.stderr)
        sys.exit(2)
    if music_end_s - track_entry_s < video_total_s - music_enter_video_s:
        print(f"  ! music ends {video_total_s - music_enter_video_s - (music_end_s - track_entry_s):.2f}s "
              f"before the video does (real end {music_end_s:.2f}s)", file=sys.stderr)

    # Slice music from track_entry onwards into mus from music_enter_video_s onwards
    track_start_frame = to_frames(track_entry_s)
    music_slice = music[track_start_frame:]
    # Also cap at real music end
    max_music_frames = to_frames(music_end_s - track_entry_s)
    if max_music_frames < len(music_slice):
        music_slice = music_slice[:max_music_frames]
    music_place_frame = to_frames(music_enter_video_s)
    frames_available_in_mix = total_frames - music_place_frame
    music_slice = music_slice[:frames_available_in_mix]
    place(mus, music_slice, music_place_frame)

    # Build music gain envelope (linear amp over the full timeline)
    # Default: 0 (muted)
    env = np.zeros(total_frames, dtype=np.float32)
    # Determine thought-pause spans: a "pause" (SOP's "short section pause" = -4 dB)
    # is any gap >= 1.0s between speech clips.
    thought_pause_ranges = []  # list of (start_s, end_s)
    for i, gap_s in enumerate(gaps):
        if gap_s >= 1.0:
            clip_end_s = clip_starts_s[i] + len(speech_segments[i][1]) / SR
            thought_pause_ranges.append((clip_end_s, clip_end_s + gap_s))

    # Fill envelope segment by segment:
    def fill(start_s, end_s, start_db, end_db=None):
        a = to_frames(max(0, start_s))
        b = to_frames(min(video_total_s, end_s))
        if b <= a:
            return
        n = b - a
        if end_db is None or end_db == start_db:
            env[a:b] = db_to_amp(start_db)
        else:
            env[a:b] = ramp(n, db_to_amp(start_db), db_to_amp(end_db))

    # Under hook (music_enter_video_s .. hook_dur_s): faint bed, short fade-in
    # so the music-from-0:00 bed doesn't start abruptly.
    hook_bed_db = tl.get("hook_bed_db", -18.0)
    fade_in_s = tl.get("music_fade_in_s", 0.5)
    if fade_in_s > 0:
        fill(music_enter_video_s, music_enter_video_s + fade_in_s, -60.0, hook_bed_db)
        fill(music_enter_video_s + fade_in_s, hook_dur_s, hook_bed_db)
    else:
        fill(music_enter_video_s, hook_dur_s, hook_bed_db)
    # Pre-speech pause: ramp bed -> 0 dB (0 dB = full music)
    fill(hook_dur_s, drop_video_s, hook_bed_db, 0.0)
    # Under speech body: -9.5 dB by default
    fill(drop_video_s, speech_end_s, -9.5)
    # Short section pauses override: -4 dB
    for s, e in thought_pause_ranges:
        fill(s, e, -4.0)
    # Ring-out: -2.5 dB
    fill(speech_end_s, speech_end_s + ring_out_s, -2.5)
    # Sign-off: fade from -2.5 dB to -60 dB (near-silence) over signoff_s
    fill(speech_end_s + ring_out_s, video_total_s, -2.5, -60.0)

    mus_mixed = mus * env

    # Mix: voice + music
    mix = voice + mus_mixed
    # Soft limit to prevent clipping before loudnorm
    peak = np.max(np.abs(mix)) + 1e-12
    if peak > 0.98:
        mix = mix * (0.98 / peak)

    # Write pre-loudnorm WAV
    out_wav = Path(args.out)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_wav = out_wav.with_suffix(".pre_loudnorm.wav")
    sf.write(str(tmp_wav), mix, SR, subtype="PCM_16")

    if master_mode == "limiter":
        # Normalize-then-limit (handles peaky speech that loudnorm can't lift)
        stats = master_limiter(str(tmp_wav), str(out_wav),
                               target_i=tl.get("master_target_lufs", LIMITER_TARGET_LUFS),
                               limit=tl.get("master_limit", LIMITER_CEILING))
    else:
        # Two-pass loudnorm via ffmpeg -> I=-13.3, TP=-2 (v2.4 targets)
        pass1_cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "info",
            "-i", str(tmp_wav),
            "-af", "loudnorm=I=-13.3:TP=-2:LRA=11:print_format=json",
            "-f", "null", "-",
        ]
        p1 = subprocess.run(pass1_cmd, capture_output=True, text=True)
        # Pass 1 writes JSON to stderr
        m = re.search(r"\{[^{}]*input_i[^{}]*\}", p1.stderr, flags=re.S)
        if not m:
            print("loudnorm pass 1 output:")
            print(p1.stderr)
            sys.exit(2)
        stats = json.loads(m.group(0))

        pass2_af = (
            f"loudnorm=I=-13.3:TP=-2:LRA=11:"
            f"measured_I={stats['input_i']}:"
            f"measured_LRA={stats['input_lra']}:"
            f"measured_TP={stats['input_tp']}:"
            f"measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}:"
            f"linear=true:print_format=summary,"
            # Hard safety limiter so TP never crosses -1 dBTP even if loudnorm drifts
            f"alimiter=limit=0.79:asc=1:level=disabled"
        )
        pass2_cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(tmp_wav),
            "-af", pass2_af,
            "-ar", "48000",
            str(out_wav),
        ]
        p2 = subprocess.run(pass2_cmd, capture_output=True, text=True)
        if p2.returncode != 0:
            print("loudnorm pass 2 error:", p2.stderr)
            sys.exit(2)

    # Report
    print(f"video length: {video_total_s:.3f}s")
    print(f"hook: {hook_dur_s:.3f}s  music bed {hook_bed_db} dB enters @ {music_enter_video_s:.3f}s "
          f"(fade-in {fade_in_s}s)")
    print(f"pause: {pause_s:.3f}s  ({hook_dur_s:.3f} -> {drop_video_s:.3f})")
    print(f"speech body: {speech_end_s - drop_video_s:.3f}s  ({drop_video_s:.3f} -> {speech_end_s:.3f})")
    print(f"ring-out: {ring_out_s:.3f}s  ({speech_end_s:.3f} -> {speech_end_s + ring_out_s:.3f})")
    print(f"sign-off: {signoff_s:.3f}s  ({speech_end_s + ring_out_s:.3f} -> {video_total_s:.3f})")
    print(f"music track_entry: {track_entry_s:.3f}s (track pos when music enters mix)")
    print(f"mastering ({master_mode}): {stats}")
    print(f"wrote {out_wav}")

    if args.debug_json:
        with open(args.debug_json, "w", encoding="utf-8") as f:
            json.dump({
                "music_env_db": {  # music gain at key moments, for QA
                    f"{t:.2f}": round(float(20 * np.log10(env[min(total_frames - 1, to_frames(t))] + 1e-9)), 1)
                    for t in (0.0, fade_in_s / 2, fade_in_s, hook_dur_s - 0.05,
                              (hook_dur_s + drop_video_s) / 2, drop_video_s + 0.1,
                              speech_end_s + 0.5)
                },
                "video_total_s": video_total_s,
                "hook_dur_s": hook_dur_s,
                "music_enter_video_s": music_enter_video_s,
                "drop_video_s": drop_video_s,
                "speech_end_s": speech_end_s,
                "clip_starts_s": clip_starts_s,
                "clip_durs_s": [len(y) / SR for _, y in speech_segments],
                "voice_crest": voice_crest,
                "clip_names": clip_names,
                "track_entry_s": track_entry_s,
                "thought_pause_ranges": thought_pause_ranges,
            }, f, indent=2)


if __name__ == "__main__":
    main()
