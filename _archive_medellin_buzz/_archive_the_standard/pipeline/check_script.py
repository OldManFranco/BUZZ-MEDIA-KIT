r"""
The Standard — script check (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §The format / §Script craft / §Step 1 (source of truth)
Validates working\<slug>\script.json before Gate 1:
  - 150-175 narration words (spoken form)
  - per-beat time estimate at --wpm (default 150) against the beat windows
    (hook 0-3s, scene 3-15s, story 15-50s, result 50-75s incl. speech, lesson 75-89s)
  - total estimate (narration + speech clip --speech-s + pauses + 1s sign-off) in 60-95s
  - every claim id used is "verified" in claims.json
  - hook passes the hook rule (calls generate_hook_variants.validate_hook)
  - last narrated line is "Hold the standard."
  - no sentence matches an exclusion (research_athlete.match_exclusions)
Exit 1 on any failure; prints a pass/fail table.

script.json:
  {"format": "v3", "hook_id": "h2",
   "beats": [{"beat": 1, "name": "hook", "sentences": [
       {"spoken": "...", "display": "...", "claims": ["c1"], "visual": "stat_callout"}]}],
   "speech_clips": ["climax1"]}

Usage:
    python check_script.py --slug michael-jordan-02 [--wpm 150] [--speech-s 16]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORDS_MIN, WORDS_MAX = 150, 175
BEAT_WINDOWS_S = {1: (0, 3), 2: (3, 15), 3: (15, 50), 4: (50, 75), 5: (75, 89)}
BRAND_LINE = "Hold the standard."


def narration_words(script: dict) -> int:
    """Word count of all spoken sentences."""
    raise NotImplementedError("scaffold — v3.0")


def beat_estimates(script: dict, wpm: float = 150.0) -> dict:
    """{beat: estimated seconds} from spoken word counts."""
    raise NotImplementedError("scaffold — v3.0")


def check_claims(script: dict, claims: list[dict]) -> list[str]:
    """Claim ids that are missing or not 'verified'."""
    raise NotImplementedError("scaffold — v3.0")


def check(slug: str, wpm: float = 150.0, speech_s: float = 16.0) -> list[str]:
    """All failures as readable lines (empty list = pass)."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--wpm", type=float, default=150.0)
    ap.add_argument("--speech-s", type=float, default=16.0)
    args = ap.parse_args()
    try:
        fails = check(args.slug, args.wpm, args.speech_s)
    except NotImplementedError as e:
        sys.exit(f"check_script.py: {e}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
