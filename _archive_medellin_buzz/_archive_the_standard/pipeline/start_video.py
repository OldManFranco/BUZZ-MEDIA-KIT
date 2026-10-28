r"""
The Standard — start a v3.0 video (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Input / §Step 0 (source of truth)
Creates the subject folder tree and working\<slug>\request.json:
  <Subject Name>\Speech\  Narration\  Scene Pack\_sourced\  Music\
  working\<slug>\request.json   {"subject", "slug", "avoid", "angle_hint",
                                 "allow_controversy", "format": "v3", "created"}
The slug is the next free "<subject-slug>-NN" (checks working\ and hook_log.md).
Never overwrites an existing request.json unless --force.

Usage:
    python start_video.py "Michael Jordan" --avoid "Bulls Finals runs" [--angle-hint "..."]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUBJECT_DIRS = ["Speech", "Narration", "Scene Pack", "Scene Pack/_sourced", "Music"]


def slugify(subject: str) -> str:
    """'J J Watt' -> 'jj-watt' (matches existing slugs: jon-jones, michael-jordan)."""
    raise NotImplementedError("scaffold — v3.0")


def next_slug(subject: str, working: Path, hook_log: Path) -> str:
    """Next free '<slug>-NN' not used in working\\ or hook_log.md."""
    raise NotImplementedError("scaffold — v3.0")


def make_subject_tree(subject: str, root: Path = ROOT) -> Path:
    """Create <Subject Name>\\ and SUBJECT_DIRS if missing. Returns the subject folder."""
    raise NotImplementedError("scaffold — v3.0")


def write_request(slug: str, subject: str, avoid: list, angle_hint: str | None,
                  working: Path, force: bool = False) -> Path:
    """Write working\\<slug>\\request.json. Returns its path."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subject", help="athlete's full name, e.g. \"Michael Jordan\"")
    ap.add_argument("--avoid", action="append", default=[], help="topic to stay away from (repeatable)")
    ap.add_argument("--angle-hint", default=None)
    ap.add_argument("--slug", default=None, help="override the auto slug")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    try:
        make_subject_tree(args.subject)
        slug = args.slug or next_slug(args.subject, ROOT / "working", ROOT / "hook_log.md")
        print(write_request(slug, args.subject, args.avoid, args.angle_hint,
                            ROOT / "working", args.force))
    except NotImplementedError as e:
        sys.exit(f"start_video.py: {e}")


if __name__ == "__main__":
    main()
