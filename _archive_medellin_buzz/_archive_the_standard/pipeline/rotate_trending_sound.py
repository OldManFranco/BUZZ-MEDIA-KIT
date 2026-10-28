r"""
The Standard — trending sound pick for in-app use (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Step 10 (source of truth)
Trending sounds are NEVER mixed into a delivery file. Franco adds the chosen
sound in the TikTok app over outbox\<slug>_v<N>_nomusic.mp4.

  1. read assets\trending_sounds\sounds.txt   ("<date> | <url> | <note>" per line)
  2. yt-dlp each URL into assets\trending_sounds\downloads\ (gitignored) —
     analysis only, skip ones already downloaded
  3. per sound: length, BPM (librosa), RMS envelope, drop position
     (find_music_drop.find_drop)
  4. score fit for the 90s format: drop can line up with the climax word
     (--climax-s, default from timeline.json), steady stretch for under
     narration, energy, freshness (days since bookmarked), not used in the
     last 3 videos (hook_log.md / previous *_sound.txt)
  5. write outbox\<slug>_sound.txt: sound to pick, start offset in the app,
     suggested volume (~15%), runner-up

Usage:
    python rotate_trending_sound.py --slug michael-jordan-02 [--climax-s 52.3]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOUNDS_DIR = ROOT / "assets" / "trending_sounds"


def read_bookmarks(path: Path = SOUNDS_DIR / "sounds.txt") -> list[dict]:
    """[{"date", "url", "note"}], skipping comments and blank lines."""
    raise NotImplementedError("scaffold — v3.0")


def download(url: str, dest: Path = SOUNDS_DIR / "downloads") -> Path:
    """yt-dlp audio-only download. Returns the file path."""
    raise NotImplementedError("scaffold — v3.0")


def analyze(path: Path) -> dict:
    """{"length_s", "bpm", "drop_s", "steady_s", "energy"}."""
    raise NotImplementedError("scaffold — v3.0")


def score(sound: dict, climax_s: float, recent_urls: set[str]) -> float:
    """Higher = better fit."""
    raise NotImplementedError("scaffold — v3.0")


def write_pick(slug: str, ranked: list[dict], out_dir: Path = ROOT / "outbox") -> Path:
    """outbox\\<slug>_sound.txt. Returns its path."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--climax-s", type=float, default=None,
                    help="video time of the climax word (default: from timeline.json)")
    args = ap.parse_args()
    try:
        raise NotImplementedError("scaffold — v3.0")
    except NotImplementedError as e:
        sys.exit(f"rotate_trending_sound.py: {e}")


if __name__ == "__main__":
    main()
