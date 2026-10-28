r"""
The Standard — hook rule validator (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Hook rule (source of truth)
Claude writes hook candidates; this script enforces the rule and keeps 3.
A hook passes only when ALL hold:
  - >=1 proper noun: an entity from research.md / Wikidata (person, team,
    place, league, event), or a capitalized non-sentence-initial word that is
    not a stopword
  - >=1 specific detail: number, $ amount, ordinal ("week 2"), year, month/date,
    known place name, or a concrete situation tagged by Claude ("situation")
  - <=14 words; the proper noun AND the detail both inside the first 5 words
    (--front-words)
  - every claim id on the hook is "verified" in claims.json
Text only — never generates audio.

Input  working\<slug>\hooks_draft.json: [{"id": "h1", "text": "...", "claims": ["c1"],
                                          "detail_type": "number|place|date|situation"}]
Output working\<slug>\hooks.json: the first 3 passing (+ every rejection with its reason).

Usage:
    python generate_hook_variants.py --slug michael-jordan-02
    python generate_hook_variants.py --test "Michael Jordan rode a bus through Birmingham for $850 a month."
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAX_WORDS = 14
FRONT_WORDS = 5


def load_entities(slug: str) -> set[str]:
    """Proper nouns known for this subject (research.md + Wikidata cache)."""
    raise NotImplementedError("scaffold — v3.0")


def find_proper_nouns(text: str, entities: set[str]) -> list[tuple[int, str]]:
    """(word index, noun) pairs found in text."""
    raise NotImplementedError("scaffold — v3.0")


def find_details(text: str, detail_type: str | None = None) -> list[tuple[int, str]]:
    """(word index, detail) pairs: numbers, money, ordinals, years, dates, places."""
    raise NotImplementedError("scaffold — v3.0")


def validate_hook(hook: dict, entities: set[str], claims: list[dict],
                  front_words: int = FRONT_WORDS) -> tuple[bool, str]:
    """(passes, reason). Reason names the first failed rule."""
    raise NotImplementedError("scaffold — v3.0")


def run(slug: str, keep: int = 3, front_words: int = FRONT_WORDS) -> list[dict]:
    """Validate hooks_draft.json, write hooks.json, print the 3 passing variants."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug")
    g.add_argument("--test", help="check one hook text without a slug (no claim check)")
    ap.add_argument("--keep", type=int, default=3)
    ap.add_argument("--front-words", type=int, default=FRONT_WORDS)
    args = ap.parse_args()
    try:
        if args.test:
            ok, reason = validate_hook({"text": args.test, "claims": []}, set(), [],
                                       args.front_words)
            print(("PASS" if ok else "REJECT") + f": {reason}")
        else:
            run(args.slug, args.keep, args.front_words)
    except NotImplementedError as e:
        sys.exit(f"generate_hook_variants.py: {e}")


if __name__ == "__main__":
    main()
