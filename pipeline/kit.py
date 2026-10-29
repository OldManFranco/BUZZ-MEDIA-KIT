r"""
Buzz Media kit — where things live (CLAUDE.md §2). Every pipeline script asks this module for paths
instead of hard-coding them, so the same scripts serve every client.

A project EDL carries
  "client": "buzz-media", "project": "promo-01", "slug": "buzz-media-promo-01", "short": "s1",
  "project_dir": "clients/buzz-media/projects/promo-01"
and the project folder holds raw\ broll\ assets\ working\ output\. EDLs without "project_dir" (the archived
Medellin Buzz ones) resolve to the old input\<slug>\ working\<slug>\ output\<slug>\ layout.

Fallbacks: client sfx\ / music\ when non-empty, else the kit's; client _brand\brand.json, else the kit's neutral
default (_setup\default_brand\brand.json; Buzz Media's own brand lives in clients\buzz-media\_brand\).

The kit's user (who approves plans and cuts) is "user" in kit.local.json at the kit root, one per computer, not in git.

Scripts run from the kit root (relative paths in EDLs are relative to it).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
WHISPERX_PY = TOOLS / "venv_whisperx" / "Scripts" / "python.exe"
WHISPERX = TOOLS / "transcribir_whisperx.py"
RENDER_PY = TOOLS / "venv_render" / "Scripts" / "python.exe"
FACE_DIR = TOOLS / "render"                       # cara.py (MediaPipe face landmarker, models in tools\models\)
DEFAULT_BRAND = ROOT / "_setup" / "default_brand"


def user():
    """The kit user's name from kit.local.json ({"user": "Franco"}), or None before setup."""
    f = ROOT / "kit.local.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("user") if f.exists() else None
    except ValueError:
        return None


class Project:
    """Paths for one project, from its EDL (or from a project folder given on the command line)."""

    def __init__(self, edl=None, project_dir=None, slug=None):
        edl = edl or {}
        pd = project_dir or edl.get("project_dir")
        if pd:
            self.dir = (ROOT / pd).resolve() if not Path(pd).is_absolute() else Path(pd)
            self.client_dir = self.dir.parent.parent
            self.input = self.dir                 # raw\ broll\ assets\ live in the project folder
            self.working = self.dir / "working"
            self.output = self.dir / "output"
        else:                                     # archived Medellin Buzz layout
            slug = slug or edl["slug"]
            self.dir = self.client_dir = None
            self.input = ROOT / (edl.get("input_dir") or f"input/{slug}")
            self.working = ROOT / "working" / slug
            self.output = ROOT / "output" / slug
        self.plans = self.working / "plans"
        self.transcripts = self.working / "transcripts"

    def render_dir(self, short):
        return self.working / "render" / short

    def library(self, kind):
        """'sfx' or 'music': the client's folder when it holds any file, else the kit's shared one."""
        if self.client_dir is not None:
            own = self.client_dir / kind
            if own.is_dir() and any(p.is_file() and p.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac")
                                    for p in own.rglob("*")):
                return own
        return ROOT / kind

    def brand_dir(self):
        if self.client_dir is not None and (self.client_dir / "_brand" / "brand.json").exists():
            return self.client_dir / "_brand"
        return DEFAULT_BRAND


def brand(edl):
    """The brand tokens for an EDL: colors as hex, fonts as absolute paths (+ variable-font weight)."""
    bd = Project(edl).brand_dir() if edl.get("project_dir") else DEFAULT_BRAND
    b = json.loads((bd / "brand.json").read_text(encoding="utf-8"))
    for role, f in b["fonts"].items():
        f["path"] = str((bd / f["file"]).resolve())
    b["dir"] = str(bd)
    return b


def exclusions(edl):
    """Regexes for words a client never wants heard (clients\\<c>\\_instructions\\exclusions.json, "patterns"),
    plus any the EDL adds under "exclude_patterns". The archived Medellin Buzz list lives in
    _archive_medellin_buzz\\exclusions.json."""
    pats = list(edl.get("exclude_patterns", []))
    cd = Project(edl).client_dir if edl.get("project_dir") else None
    f = cd / "_instructions" / "exclusions.json" if cd else None
    if f and f.exists():
        pats += json.loads(f.read_text(encoding="utf-8")).get("patterns", [])
    return pats


def length_limits(edl):
    """(min_s, max_s) for a reel: the EDL's "min_s"/"max_s" (from the client's brief), else 15-60 s."""
    return float(edl.get("min_s", 15)), float(edl.get("max_s", 60))


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
