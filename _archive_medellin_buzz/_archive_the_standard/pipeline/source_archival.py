r"""
The Standard — legal archival sourcing + manual shot list (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Step 2 (source of truth)
For every visual need in working\<slug>\script.json (sentence "visual" + beat):
  1. search the allow-listed sources in pipeline\archival_sources.json:
       archive.org      internetarchive search, ONLY items whose licenseurl is
                        publicdomain / CC0 / CC-BY (uploader "public domain"
                        text alone is not enough)
       commons          Wikimedia Commons API, free licenses only (mostly stills)
       usgov            public-domain federal works (e.g. White House ceremonies)
       youtube_channels Franco-approved channels only, via yt-dlp
  2. download into <Subject>\Scene Pack\_sourced\ with a .license.json sidecar:
       {"source", "url", "title", "author", "license", "license_url",
        "retrieved", "notes"}
     and ffprobe each file (resolution, fps, duration).
  3. flag anything that looks like league broadcast footage (logos, scorebugs
     in the title/description) as "rights unclear" — never auto-use it.
  4. write working\<slug>\shot_list.md for everything not sourced:
       P1 essential / P2 strong / P3 nice — what to find, search hints,
       suggested timestamps if known, and the HyperFrames fallback block.
Paid sources (Getty, Pond5) are never used without Franco's OK.

Usage:
    python source_archival.py --slug michael-jordan-02 [--only archive,commons] [--dry-run]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCES_JSON = Path(__file__).resolve().parent / "archival_sources.json"
FREE_LICENSE_MARKERS = ("publicdomain", "/zero/", "/by/")


def visual_needs(script: dict) -> list[dict]:
    """[{"beat", "sentence", "need", "priority"}] from script.json."""
    raise NotImplementedError("scaffold — v3.0")


def search_archive_org(query: str, limit: int = 20) -> list[dict]:
    """archive.org movies/image items with a free licenseurl."""
    raise NotImplementedError("scaffold — v3.0")


def search_commons(query: str, limit: int = 20) -> list[dict]:
    """Wikimedia Commons files with free licenses."""
    raise NotImplementedError("scaffold — v3.0")


def search_allowed_channels(query: str, channels: list[dict]) -> list[dict]:
    """yt-dlp search restricted to the allow-listed channels."""
    raise NotImplementedError("scaffold — v3.0")


def looks_like_broadcast(item: dict) -> bool:
    """Heuristic rights flag (league names, network names, 'highlights')."""
    raise NotImplementedError("scaffold — v3.0")


def download_with_sidecar(item: dict, dest_dir: Path) -> Path:
    """Download the file and write <file>.license.json. Returns the file path."""
    raise NotImplementedError("scaffold — v3.0")


def write_shot_list(needs: list[dict], sourced: list[dict], out: Path) -> None:
    """shot_list.md grouped P1/P2/P3 with fallback blocks."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--only", default=None, help="comma list: archive,commons,usgov,youtube")
    ap.add_argument("--dry-run", action="store_true", help="search and list, download nothing")
    args = ap.parse_args()
    try:
        raise NotImplementedError("scaffold — v3.0")
    except NotImplementedError as e:
        sys.exit(f"source_archival.py: {e}")


if __name__ == "__main__":
    main()
