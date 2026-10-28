r"""
The Standard — learning-batch metrics (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Measuring the learning batch (source of truth)
  --add <slug>      add an empty row to metrics_log.md at delivery (deliver.py calls this)
  --update <slug>   fill in numbers Franco reads from TikTok analytics:
                    --at 48h|7d --views --likes --shares --avg-watch-s
                    --r2 --r5 --r10 --r30 (retention %, read off the curve)
                    --full-pct (% watched in full)
  --compare         print v3.0 videos vs the v2.4 baseline (jon-jones-01, michael-jordan-01),
                    comparing retention points, not average watch time

Usage:
    python log_metrics.py --add michael-jordan-02
    python log_metrics.py --update michael-jordan-02 --at 48h --views 900 --r2 61 --r5 44
    python log_metrics.py --compare
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
METRICS = ROOT / "metrics_log.md"


def add_row(slug: str, path: Path = METRICS) -> str:
    """Append an empty row for slug (skip if present)."""
    raise NotImplementedError("scaffold — v3.0")


def update_row(slug: str, at: str, values: dict, path: Path = METRICS) -> str:
    """Fill the slug's 48h or 7d cells."""
    raise NotImplementedError("scaffold — v3.0")


def compare(path: Path = METRICS) -> None:
    """Print v3.0 vs v2.4 baseline table."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--add", metavar="SLUG")
    g.add_argument("--update", metavar="SLUG")
    g.add_argument("--compare", action="store_true")
    ap.add_argument("--at", choices=["48h", "7d"])
    for k in ("views", "likes", "shares"):
        ap.add_argument(f"--{k}", type=int)
    for k in ("avg-watch-s", "r2", "r5", "r10", "r30", "full-pct"):
        ap.add_argument(f"--{k}", type=float)
    args = ap.parse_args()
    try:
        raise NotImplementedError("scaffold — v3.0")
    except NotImplementedError as e:
        sys.exit(f"log_metrics.py: {e}")


if __name__ == "__main__":
    main()
