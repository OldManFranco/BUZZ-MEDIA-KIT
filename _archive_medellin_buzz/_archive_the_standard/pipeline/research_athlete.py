r"""
The Standard — athlete research helper (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Step 0 / Gate 0 (source of truth)
Claude Code does the web searching itself (WebSearch / WebFetch). This script
does the parts that can be checked:

  init   working\<slug>\research.md: Wikipedia summary + Wikidata facts
         (teams, years, places, awards) + the exclusion list for this video
         (do_not_cover.md section for the subject + Generic + Covered by
         The Standard + request.json "avoid").
  check  fuzzy-match every candidate angle in angles.json (title + keywords)
         against the exclusions with rapidfuzz; mark hits "excluded" with the
         matching line. Threshold --threshold (default 80).
  score  write the 5 scores per angle (surprise, arc, sources, footage,
         speech_clip; 1-5 each), drop angles with no speech-clip candidate,
         keep the top --keep (default 3), print the Gate 0 table.

angles.json entry:
  {"id": "a1", "title": "...", "logline": "...", "keywords": [...],
   "arc": {"challenge": "", "response": "", "outcome": "", "lesson": ""},
   "sources": [{"url": "", "publisher": "", "note": ""}],
   "controversy": false, "footage": "auto|manual|graphics",
   "speech_candidates": [{"url": "", "t": "12:34", "note": ""}],
   "scores": {...}, "status": "candidate|excluded|kept"}

Usage:
    python research_athlete.py init  --slug michael-jordan-02
    python research_athlete.py check --slug michael-jordan-02
    python research_athlete.py score --slug michael-jordan-02 --keep 3
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DO_NOT_COVER = ROOT / "do_not_cover.md"


def load_request(slug: str) -> dict:
    """Read working\\<slug>\\request.json."""
    raise NotImplementedError("scaffold — v3.0")


def load_exclusions(subject: str, avoid: list, path: Path = DO_NOT_COVER) -> list[str]:
    """Lines from the subject's section, Generic, Covered by The Standard, plus avoid."""
    raise NotImplementedError("scaffold — v3.0")


def fetch_wikipedia(subject: str) -> dict:
    """Wikipedia-API summary + section titles for the subject."""
    raise NotImplementedError("scaffold — v3.0")


def fetch_wikidata(subject: str) -> dict:
    """Teams, years, birthplace, awards via the Wikidata API (requests)."""
    raise NotImplementedError("scaffold — v3.0")


def cmd_init(slug: str) -> Path:
    """Write research.md. Returns its path."""
    raise NotImplementedError("scaffold — v3.0")


def match_exclusions(angle: dict, exclusions: list[str], threshold: int = 80) -> str | None:
    """Return the matching exclusion line, or None."""
    raise NotImplementedError("scaffold — v3.0")


def cmd_check(slug: str, threshold: int = 80) -> list[dict]:
    """Mark excluded angles in angles.json. Returns the angles."""
    raise NotImplementedError("scaffold — v3.0")


def cmd_score(slug: str, keep: int = 3) -> list[dict]:
    """Keep the top angles and print the Gate 0 table. Returns the kept angles."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["init", "check", "score"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--threshold", type=int, default=80)
    ap.add_argument("--keep", type=int, default=3)
    args = ap.parse_args()
    try:
        if args.cmd == "init":
            print(cmd_init(args.slug))
        elif args.cmd == "check":
            cmd_check(args.slug, args.threshold)
        else:
            cmd_score(args.slug, args.keep)
    except NotImplementedError as e:
        sys.exit(f"research_athlete.py: {e}")


if __name__ == "__main__":
    main()
