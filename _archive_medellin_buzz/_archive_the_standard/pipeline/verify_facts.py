r"""
The Standard — fact verification (SCAFFOLD, not implemented yet)

CLAUDE.md v3.0 §Story rules / Claims, §Step 1 (source of truth)
Every testable claim needs >=2 INDEPENDENT sources where the claim's snippet
really appears on the page. For each claim in working\<slug>\claims.json:
  1. fetch every source URL (trafilatura; pages cached in working\<slug>\sources\)
  2. confirm each "snippet" (or its number/date) is on the fetched page
     (normalized text + rapidfuzz partial match >= --match, default 90)
  3. independence: different registered domains, not a Wikipedia mirror,
     not one source citing the other as its only basis
  4. status: "verified" (>=2 independent confirmed), "weak" (1), "failed" (0)
Writes the statuses back to claims.json and a readable working\<slug>\sources.md.

claims.json entry:
  {"id": "c1", "text": "Jordan earned $850 a month with the Barons",
   "kind": "number|date|place|quote|ranking|situation",
   "sources": [{"url": "", "snippet": "", "publisher": ""}],
   "status": "unchecked|verified|weak|failed", "notes": ""}

Usage:
    python verify_facts.py --slug michael-jordan-02 [--only c1,c4] [--refetch]
"""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def fetch_page(url: str, cache_dir: Path, refetch: bool = False) -> str:
    """Clean article text for url (cached by URL hash)."""
    raise NotImplementedError("scaffold — v3.0")


def snippet_on_page(snippet: str, page_text: str, min_score: int = 90) -> bool:
    """True when the snippet (normalized numbers/dates/quotes) is on the page."""
    raise NotImplementedError("scaffold — v3.0")


def registered_domain(url: str) -> str:
    """'https://www.al.com/sports/x' -> 'al.com'."""
    raise NotImplementedError("scaffold — v3.0")


def independent(sources: list[dict]) -> list[dict]:
    """Confirmed sources that count as independent of each other."""
    raise NotImplementedError("scaffold — v3.0")


def verify_claim(claim: dict, cache_dir: Path, min_score: int = 90,
                 refetch: bool = False) -> dict:
    """Return the claim with status + notes filled in."""
    raise NotImplementedError("scaffold — v3.0")


def write_sources_md(claims: list[dict], out: Path) -> None:
    """Claim table + every source with its confirmed/unconfirmed mark."""
    raise NotImplementedError("scaffold — v3.0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--only", default=None, help="comma-separated claim ids")
    ap.add_argument("--match", type=int, default=90, help="snippet match score 0-100")
    ap.add_argument("--refetch", action="store_true")
    args = ap.parse_args()
    try:
        raise NotImplementedError("scaffold — v3.0")
    except NotImplementedError as e:
        sys.exit(f"verify_facts.py: {e}")


if __name__ == "__main__":
    main()
