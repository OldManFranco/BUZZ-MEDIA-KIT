r"""
Buzz Media kit — download the shared SFX and music library on a new computer (_setup\SETUP.md step 7).

The audio files never go on GitHub: Mixkit, Pixabay and YouTube Audio Library let you use their files in your
videos, not pass the files on. So each person downloads them from the source, under that source's license,
into the paths the catalogs list (sfx\catalogo_sfx.json, music\catalogo_musica.json):

  - Mixkit (49 SFX, 56 tracks): downloaded here from Mixkit's own file links.
  - Pixabay (14 SFX, 7 tracks) and YouTube Audio Library (27 tracks): no direct links (Pixabay's site blocks
    scripts; the YouTube library needs a YouTube login), so they're listed with their pages for a manual
    download. The kit works without them.
  - sfx\_synth\: made for the kit, no license; it's in the repo already.

  python _setup\fetch_library.py            download what's missing
  python _setup\fetch_library.py --check    list what's missing, download nothing
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (buzz-media-kit fetch_library)"}


def mixkit_id(entry):
    m = re.match(r"mk_[sm]_(\d+)$", entry.get("id_lista") or "")
    return m.group(1) if m else None


def wanted():
    """[(local path, source url or None, entry)] for every catalogued file."""
    out = []
    sfx = json.loads((ROOT / "sfx" / "catalogo_sfx.json").read_text(encoding="utf-8"))["sfx"]
    for v in sfx.values():
        dst = ROOT / "sfx" / v["archivo"].replace("\\", "/")
        i = mixkit_id(v)
        url = f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}{Path(v['archivo_original']).suffix}" if i else None
        out.append((dst, url, v))
    music = json.loads((ROOT / "music" / "catalogo_musica.json").read_text(encoding="utf-8"))["pistas"]
    for name, v in music.items():
        i = mixkit_id(v)
        out.append((ROOT / "music" / name, f"https://assets.mixkit.co/music/{i}/{i}.mp3" if i else None, v))
    return out


def fetch(url, dst):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(dst)
    return len(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="list what's missing, download nothing")
    a = ap.parse_args()
    items = wanted()
    missing = [(d, u, v) for d, u, v in items if not d.exists()]
    auto = [m for m in missing if m[1]]
    manual = [m for m in missing if not m[1]]
    print(f"{len(items)} catalogued files, {len(items) - len(missing)} here, {len(auto)} to download from Mixkit, "
          f"{len(manual)} manual (Pixabay / YouTube Audio Library)")
    failed = []
    if not a.check:
        for k, (dst, url, _) in enumerate(auto, 1):
            try:
                n = fetch(url, dst)
                print(f"  [{k}/{len(auto)}] {dst.relative_to(ROOT)}  {n / 1e6:.1f} MB")
            except Exception as e:
                failed.append((dst, url, str(e)))
                print(f"  [{k}/{len(auto)}] FAILED {dst.relative_to(ROOT)}: {e}")
    if manual:
        print("\nManual downloads (optional; save each file under the name shown):")
        for dst, _, v in manual:
            page = v.get("url_pagina") or v.get("url") or "YouTube Studio > Audio Library: search the title"
            print(f"  {dst.relative_to(ROOT)}\n      {v.get('fuente', '?')}: {page}")
    if failed:
        print(f"\n{len(failed)} downloads failed; run again later.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
