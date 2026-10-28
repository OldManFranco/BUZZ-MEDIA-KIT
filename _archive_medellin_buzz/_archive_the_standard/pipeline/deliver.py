r"""
The Standard — Gate 2 delivery (direct local write)

CLAUDE.md v2.4 §Step 12 / Gate 2 (source of truth)
No gzip-split workaround in Claude Code: the delivery .mp4 is written straight
to outbox\. This script puts the three Gate 2 deliverables in place:
  1. outbox\<slug>_v<N>.mp4         (copied, sha256-verified)
  2. outbox\<slug>_caption.txt      (from --caption-file, if given)
  3. hook_log.md entry              "<date> | <slug> | <pattern #> | <Subject>"
                                    (if --pattern and --subject are given;
                                    file created with a header if missing;
                                    skipped if the slug is already logged)
Then surface the .mp4 to Franco in chat with SendUserFile.

Never overwrites an existing outbox version unless --force.

Usage:
    python deliver.py --delivery working/<slug>/delivery.mp4 --slug <slug> \
        --version 1 --caption-file working/<slug>/caption.txt \
        --pattern 4 --subject "Michael Jordan"
"""
import argparse
import datetime
import hashlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOK_LOG_HEADER = "# The Standard hook log (date | slug | hook pattern # | subject)"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def append_hook_log(log: Path, slug: str, pattern: int, subject: str) -> str:
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else [HOOK_LOG_HEADER]
    if any(f"| {slug} |" in ln for ln in lines):
        return f"hook_log: {slug} already logged, unchanged"
    entry = f"{datetime.date.today().isoformat()} | {slug} | {pattern} | {subject}"
    lines.append(entry)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"hook_log: added '{entry}'"


# ---------------------------------------------------------------------------
# v3.0 (CLAUDE.md v3.0 Gate 3) — opt-in with --format v3.
# Adds: _nomusic video, the "Voice: ElevenLabs" attribution line, sources.md,
# sound.txt, a v3 hook_log entry, the angle in do_not_cover.md and a metrics row.
# ---------------------------------------------------------------------------
import json  # noqa: E402

ATTRIBUTION = "Voice: ElevenLabs"


def copy_verified(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        sys.exit(f"ERROR: {dst} already exists. Use a new --version or --force.")
    shutil.copyfile(src, dst)
    if sha256_file(src) != sha256_file(dst):
        sys.exit(f"ERROR: sha256 mismatch after copying {src.name}")
    print(f"video:   {dst}  ({dst.stat().st_size / 1e6:.1f} MB, sha256 OK)")


def sources_md(slug_dir: Path, scene_dir: Path) -> str:
    claims = json.load(open(slug_dir / "claims.json", encoding="utf-8"))
    segs = json.load(open(slug_dir / "segments.json", encoding="utf-8"))["segments"]
    out = [f"# Sources — {slug_dir.name}", "", "## Claims (each verified on >=2 independent publishers)", ""]
    for c in claims["claims"]:
        out.append(f"- **{c['id']}** — {c['text']}")
        for s in c["sources"]:
            out.append(f"  - {s['publisher']}: {s['url']}")
    out += ["", "## Footage and photos (license sidecars in Scene Pack/_sourced)", ""]
    for src in sorted({s["src"] for s in segs if "src" in s}):
        side = scene_dir / (src + ".license.json")
        if side.exists():
            m = json.load(open(side, encoding="utf-8"))
            out.append(f"- `{src}` — {m.get('title', '')} · {m.get('author', '')} · {m.get('license', '')} · {m.get('page_url', '')}")
        else:
            out.append(f"- `{src}` — NO LICENSE SIDECAR")
    out += ["", "## Graphics", "", "- HyperFrames blocks (pipeline/graphics). Map: Wikimedia Commons, public domain.",
            "- Headline text is the real March 14, 1994 headline under a generic masthead (no publication logo).",
            "", "## Audio", "", "- Narration: ElevenLabs (Declan Sage), free plan — attribution in caption.",
            "- SFX: Mixkit (assets/sfx/README.md)."]
    return "\n".join(out) + "\n"


def main_v3(args) -> None:
    slug_dir = ROOT / "working" / args.slug
    req = json.load(open(slug_dir / "request.json", encoding="utf-8"))
    scene_dir = ROOT / req["subject_folder"] / "Scene Pack"
    outbox = Path(args.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    copy_verified(Path(args.delivery), outbox / f"{args.slug}_v{args.version}.mp4", args.force)
    copy_verified(Path(args.delivery_nomusic), outbox / f"{args.slug}_v{args.version}_nomusic.mp4", args.force)

    text = Path(args.caption_file).read_text(encoding="utf-8").rstrip("\n")
    low = text.lower()
    if "#thestandard" not in low:
        print("  ! caption is missing #thestandard", file=sys.stderr)
    if "#fyp" in low or "#viral" in low:
        sys.exit("ERROR: caption contains #fyp or #viral (never allowed)")
    if ATTRIBUTION not in text:
        text += "\n\n" + ATTRIBUTION
    (outbox / f"{args.slug}_caption.txt").write_text(text + "\n", encoding="utf-8")
    (outbox / f"{args.slug}_sources.md").write_text(sources_md(slug_dir, scene_dir), encoding="utf-8")
    if args.sound_file:
        shutil.copyfile(args.sound_file, outbox / f"{args.slug}_sound.txt")
    print(f"caption, sources{', sound' if args.sound_file else ''}: {outbox}")

    today = datetime.date.today().isoformat()
    log = Path(args.hook_log)
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else [HOOK_LOG_HEADER]
    if not any(f"| {args.slug} |" in ln for ln in lines):
        lines.append(f"{today} | {args.slug} | v3:{args.hook_type} | {args.subject} | {args.angle}")
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("hook_log: added")

    dnc = ROOT / "do_not_cover.md"
    t = dnc.read_text(encoding="utf-8")
    entry = f"{args.subject}: {args.angle} ({args.slug})"
    if entry not in t:
        t = t.replace("(deliver.py --format v3 appends each shipped angle here)",
                      f"(deliver.py --format v3 appends each shipped angle here)\n{entry}")
        dnc.write_text(t, encoding="utf-8")
        print("do_not_cover: angle appended")

    ml = ROOT / "metrics_log.md"
    mt = ml.read_text(encoding="utf-8")
    if f"| {args.slug} |" not in mt:
        dur = args.length_s
        ml.write_text(mt.rstrip("\n") + f"\n| {args.slug} | v3.0 | {dur} | | | | | | | | | | |\n", encoding="utf-8")
        print("metrics_log: row added (fill in at 48h / 7 days)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delivery", required=True, help="delivery .mp4 from final_render")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--caption-file", help="TikTok caption text to copy to outbox")
    ap.add_argument("--pattern", type=int, help="hook pattern # (1-5) for hook_log.md")
    ap.add_argument("--subject", help="Subject Name for hook_log.md")
    ap.add_argument("--outbox", default=str(ROOT / "outbox"))
    ap.add_argument("--hook-log", default=str(ROOT / "hook_log.md"))
    ap.add_argument("--force", action="store_true", help="overwrite an existing outbox version")
    ap.add_argument("--format", default="v2.4", choices=["v2.4", "v3"])
    ap.add_argument("--delivery-nomusic", help="v3: delivery_nomusic.mp4")
    ap.add_argument("--sound-file", help="v3: <slug>_sound.txt to copy to outbox")
    ap.add_argument("--hook-type", help="v3: number|place|date|situation")
    ap.add_argument("--angle", help="v3: one-line angle for hook_log and do_not_cover")
    ap.add_argument("--length-s", help="v3: final length for metrics_log")
    args = ap.parse_args()
    if args.format == "v3":
        if not (args.delivery_nomusic and args.caption_file and args.subject and args.hook_type and args.angle):
            ap.error("--format v3 needs --delivery-nomusic, --caption-file, --subject, --hook-type, --angle")
        main_v3(args)
        return

    src = Path(args.delivery)
    outbox = Path(args.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    dst = outbox / f"{args.slug}_v{args.version}.mp4"

    if dst.exists() and not args.force and dst.resolve() != src.resolve():
        print(f"ERROR: {dst} already exists. Use --version {args.version + 1} or --force.",
              file=sys.stderr)
        sys.exit(2)
    src_sha = sha256_file(src)
    if dst.resolve() != src.resolve():
        shutil.copyfile(src, dst)
    dst_sha = sha256_file(dst)
    if dst_sha != src_sha:
        print(f"ERROR: sha256 mismatch after copy ({src_sha} vs {dst_sha})", file=sys.stderr)
        sys.exit(2)
    print(f"video:   {dst}  ({dst.stat().st_size / 1e6:.1f} MB, sha256 OK)")

    if args.caption_file:
        cap_dst = outbox / f"{args.slug}_caption.txt"
        text = Path(args.caption_file).read_text(encoding="utf-8")
        if "#thestandard" not in text.lower():
            print("  ! caption is missing #thestandard", file=sys.stderr)
        if "#fyp" in text.lower() or "#viral" in text.lower():
            print("  ! caption contains #fyp or #viral (never allowed)", file=sys.stderr)
        cap_dst.write_text(text, encoding="utf-8")
        print(f"caption: {cap_dst}")

    if args.pattern is not None and args.subject:
        print(append_hook_log(Path(args.hook_log), args.slug, args.pattern, args.subject))

    print(f"\nNext: SendUserFile {dst}")


if __name__ == "__main__":
    main()
