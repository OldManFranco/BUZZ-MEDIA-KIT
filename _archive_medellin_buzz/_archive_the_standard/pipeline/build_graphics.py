r"""
The Standard — HyperFrames graphic beats (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §16b (source of truth)
Reads working\<slug>\graphics_plan.json, copies the needed blocks from
pipeline\graphics\compositions\ into a per-video HyperFrames project at
working\<slug>\graphics\, fills in each block's variables, runs
`npx hyperframes check --json` (stops on errors), then renders each beat to
working\<slug>\graphics\out\<name>.mp4 (1080x1920, 30fps).
--stills renders one still per beat (for the Gate 2 storyboard) instead.

graphics_plan.json:
  {"format": "v3", "beats": [
     {"name": "b1_hook", "block": "stat_callout", "duration_s": 2.6,
      "vars": {"number": "850", "prefix": "$", "label": "A MONTH"},
      "claims": ["c1"]}]}

Every block's text must sit inside y=380-1180; monochrome, accent #FFFFFF.

Usage:
    python build_graphics.py --slug michael-jordan-02 [--stills] [--only b1_hook]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LIBRARY = Path(__file__).resolve().parent / "graphics"


def load_plan(slug: str) -> dict:
    """Read and sanity-check graphics_plan.json (known blocks, claims verified)."""
    raise NotImplementedError("scaffold — v3.0")


def make_project(slug: str, plan: dict) -> Path:
    """Create working\\<slug>\\graphics\\ with the needed blocks + tokens + fonts."""
    raise NotImplementedError("scaffold — v3.0")


def fill_vars(project: Path, beat: dict) -> None:
    """Write the beat's variables into its composition copy."""
    raise NotImplementedError("scaffold — v3.0")


def hf_check(project: Path) -> list[dict]:
    """`npx hyperframes check --json`; returns the errors."""
    raise NotImplementedError("scaffold — v3.0")


def hf_render(project: Path, beat: dict, still: bool = False) -> Path:
    """Render one beat (mp4, or png when still). Returns the output path."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--only", default=None, help="comma-separated beat names")
    args = ap.parse_args()
    try:
        raise NotImplementedError("scaffold — v3.0")
    except NotImplementedError as e:
        sys.exit(f"build_graphics.py: {e}")


if __name__ == "__main__":
    main()
