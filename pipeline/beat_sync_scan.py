"""
Buzz Media kit — benchmark helper: do cuts land on the music? (ANALYSIS ONLY, never writes video.)

For every short in <scan.json> (a list with file, cut_times, duration_s) (from benchmark_scan.py):
  - beat grid: librosa beat_track on the percussive part of the mix (HPSS), so speech doesn't drive it
  - hits: the strongest percussive onsets (top 10 % of onset strength), candidates for SFX hits and drum hits
  - for every cut: distance to the nearest beat and to the nearest hit
  - a chance baseline: the same measure for random times, so "62 % of cuts within 2 frames of a beat"
    can be read against what random cutting would score on that beat grid
  - hits that sit on a cut (within 2 frames) vs. hits away from cuts (likely SFX accents or music)

The mix has voice, music and SFX together; this measures alignment, it can't separate the stems.
Treat it as evidence to check by ear, not ground truth.

Usage:
  python -I pipeline/beat_sync_scan.py _benchmark/kallaway-reels _benchmark/kallaway/scan.json
"""
import json
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np

SR = 22050
TOL = 2 / 30  # 2 frames at 30 fps


def load_audio(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def nearest(ts, grid):
    if len(grid) == 0:
        return np.full(len(ts), np.inf)
    grid = np.asarray(grid)
    return np.array([np.min(np.abs(grid - t)) for t in ts])


def analyse(p, cuts, dur):
    y = load_audio(p)
    _, perc = librosa.effects.hpss(y)
    env = librosa.onset.onset_strength(y=perc, sr=SR)
    tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=SR)
    beat_t = librosa.frames_to_time(beats, sr=SR)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, units="frames")
    strength = env[on]
    keep = on[strength >= np.quantile(strength, 0.9)] if len(on) else on
    hit_t = librosa.frames_to_time(keep, sr=SR)

    rng = np.random.default_rng(0)
    rand = rng.uniform(0.5, max(dur - 0.5, 1.0), 2000)
    cuts = np.asarray(cuts)
    d_beat, d_hit = nearest(cuts, beat_t), nearest(cuts, hit_t)
    hits_on_cut = int(np.sum(nearest(hit_t, cuts) <= TOL)) if len(cuts) else 0
    return {
        "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 1),
        "beats": len(beat_t),
        "cuts": len(cuts),
        "cuts_on_beat_pct": round(100 * float(np.mean(d_beat <= TOL)), 1) if len(cuts) else None,
        "chance_on_beat_pct": round(100 * float(np.mean(nearest(rand, beat_t) <= TOL)), 1),
        "cuts_on_hit_pct": round(100 * float(np.mean(d_hit <= TOL)), 1) if len(cuts) else None,
        "chance_on_hit_pct": round(100 * float(np.mean(nearest(rand, hit_t) <= TOL)), 1),
        "hits": len(hit_t),
        "hits_on_cut": hits_on_cut,
        "hit_times": [round(float(t), 2) for t in hit_t],
        "cut_to_beat_ms": [round(1000 * float(d)) for d in d_beat],
    }


def main():
    src, scan_path = Path(sys.argv[1]), Path(sys.argv[2])
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    for item in scan:
        p = src / item["file"]
        item["beat_sync"] = analyse(p, item["cut_times"], item["duration_s"])
        b = item["beat_sync"]
        print(f"{item['file']}: {b['tempo_bpm']} bpm, cuts on beat {b['cuts_on_beat_pct']}% "
              f"(chance {b['chance_on_beat_pct']}%), on hit {b['cuts_on_hit_pct']}% (chance {b['chance_on_hit_pct']}%)")
    scan_path.write_text(json.dumps(scan, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
