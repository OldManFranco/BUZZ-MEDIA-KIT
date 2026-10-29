"""
Buzz Media kit — scene detection (inherited from The Standard v2.4)

Source of truth: CLAUDE.md §Pipeline step 2.
- PySceneDetect ContentDetector threshold 27.
- Some shots open with a dissolve from the previous shot — offset start by
  ~0.25s when the first frame still shows the old scene.

Writes shots.json with (idx, start_s, end_s, duration_s) per shot.
"""
import argparse
import json
from pathlib import Path


def detect_shots(video_path: str, threshold: float = 27.0,
                 min_scene_len_frames: int = 15):
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except ImportError:
        # Never auto-install (the kit user approves every install).
        import sys
        print('Missing: PySceneDetect. Ask the kit user, then: pip install "scenedetect[opencv]"',
              file=sys.stderr)
        sys.exit(2)

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames)
    )
    scene_manager.detect_scenes(video, show_progress=False)
    scenes = scene_manager.get_scene_list()
    out = []
    for i, (start, end) in enumerate(scenes):
        # PySceneDetect 0.7 has a .seconds property; older versions only get_seconds()
        s = start.seconds if hasattr(start, "seconds") else start.get_seconds()
        e = end.seconds if hasattr(end, "seconds") else end.get_seconds()
        out.append({
            "idx": i,
            "start_s": round(s, 3),
            "end_s": round(e, 3),
            "duration_s": round(e - s, 3),
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threshold", type=float, default=27.0)
    ap.add_argument("--dissolve-offset-s", type=float, default=0.25,
                    help="Shift each shot's start forward by this to skip a dissolve first frame")
    args = ap.parse_args()

    shots = detect_shots(args.video, threshold=args.threshold)
    # Apply dissolve offset to EVERY non-first shot (SOP: 'Some shots open with a dissolve')
    # Keep original fields; add adjusted ones.
    for i, s in enumerate(shots):
        if i > 0:
            s["start_s_adj"] = round(s["start_s"] + args.dissolve_offset_s, 3)
        else:
            s["start_s_adj"] = s["start_s"]
        s["duration_s_adj"] = round(s["end_s"] - s["start_s_adj"], 3)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"video": args.video, "shots": shots}, f, indent=2)
    print(f"detected {len(shots)} shots")
    for s in shots[:5]:
        print(f"  shot {s['idx']}: {s['start_s']:7.3f}-{s['end_s']:7.3f}  dur {s['duration_s']:.3f}s")
    if len(shots) > 5:
        print("  ...")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
