r"""
Buzz Media kit — motion graphics with HyperFrames (CLAUDE.md §7). Colors and fonts come from the client's
_brand\brand.json (kit.brand), filled into graphics\brand.css.

Turns an EDL's graphic events (title_card, chip, card) into a HyperFrames project, checks it, and renders one
transparent 1080x1920 layer (graphics.mov) that render_short.py lays over the picture, under nothing but the
karaoke captions' timing logic (captions themselves stay in Pillow: build_captions.py).

Library: pipeline\graphics\ (brand.css tokens, templates\*.html, the registry component number-wheel).
Project:  <project>\working\render\<short>\hf\  (index.html + compositions\g<NN>_<kind>.html + assets\fonts\)

  python pipeline/build_graphics.py clients/<client>/projects/<project>/working/plans/s1_edl.json [--frames 1650]
         [--stage build|check|snapshot|render|all]

  build     write the project (no browser)
  check     npx hyperframes check --json; stops on errors
  snapshot  PNG frames at each graphic's midpoint -> hf\.hyperframes\artifacts\snapshots\ (look before rendering)
  render    transparent MOV -> render\<short>\graphics.mov, then graphics_layout.json (measured boxes, for qa.py)

Only EDLs with "graphics_engine": "hyperframes" use this; older EDLs keep the Pillow title card and chips.
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

FPS, W, H = 30, 1080, 1920
LIB = Path(__file__).resolve().parent / "graphics"
KINDS = ("title_card", "chip", "card", "hf_scene")


def hf_cli():
    """The HyperFrames CLI through the Claude plugin launcher (pins the plugin's CLI version)."""
    if os.environ.get("HF_CLI"):
        return ["node", os.environ["HF_CLI"]]
    found = sorted(glob.glob(os.path.expanduser(
        "~/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs")))
    if not found:
        sys.exit("HyperFrames plugin not found; set HF_CLI to plugin-cli.mjs")
    return ["node", found[-1]]


def overlays(edl):
    return [e for e in edl["events"] if e["kind"] in KINDS]


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{\w+\}\}", tpl)
    if left:
        raise ValueError(f"unfilled template slots: {left}")
    return tpl


def esc(s):
    return html.escape(s or "", quote=False)


def number_wheel():
    src = (LIB / "compositions/components/number-wheel.html").read_text(encoding="utf-8")
    css = re.search(r"<style[^>]*>(.*?)</style>", src, re.S).group(1)
    js = re.search(r"<script>(.*?)</script>", src, re.S).group(1)
    # GSAP owns the strip's transform (the data card tweens it with fromTo); a CSS transform would conflict
    css = re.sub(r"\n\s*transform:\s*translateY\(0em\);", "", css)
    return css, js


def is_orange(word, orange):
    return bool(orange) and (word == orange or orange in word)


def title_card(o, cid, dur, brand):
    text = o["text"]
    forced = "|" in text
    lines = [l.strip() for l in text.split("|")] if forced else [text]
    out = []
    for line in lines:
        words = " ".join(f'<span class="mb-orange">{esc(w)}</span>' if is_orange(w, o.get("orange")) else esc(w)
                         for w in line.split())
        out.append(f'<div class="tc-line{" forced" if forced else ""}">{words}</div>')
    return fill((LIB / "templates/title_card.html").read_text(encoding="utf-8"),
                id=cid, brand_css=brand, plate="cream" if o.get("plate") == "cream" else "ink",
                eyebrow=esc(o.get("eyebrow", "")), lines="".join(out), dur=f"{dur:.3f}")


def chip(o, cid, dur, brand):
    st = o.get("style", "")
    plate = "cream" if "cream plate" in st else "orange" if "orange plate" in st else "ink"
    text_class = ("t-cream" if "cream text" in st else "t-ink" if "ink text" in st
                  else "t-accent" if plate == "orange" else "t-white")
    m = re.search(r",\s*(\S+) orange", st)
    tok = m.group(1) if m else None
    words = " ".join(f'<span class="mb-orange">{esc(w)}</span>' if tok and w == tok else esc(w)
                     for w in o["text"].split())
    return fill((LIB / "templates/chip.html").read_text(encoding="utf-8"),
                id=cid, brand_css=brand, plate=plate, text_class=text_class, words=words, dur=f"{dur:.3f}")


def data_card(o, cid, dur, brand):
    words = o["text"].split()
    i = next((k for k, w in enumerate(words) if re.search(r"\d", w)), None)
    orange = o.get("orange")
    if i is not None:
        hero_txt, label_words = words[i], words[:i] + words[i + 1:]
        hero_class = "mb-orange" if is_orange(hero_txt, orange) else ""
        hero = (f'<span class="hf-number-wheel" data-value="{esc(hero_txt)}">{esc(hero_txt)}</span>'
                if o.get("counter") else esc(hero_txt))
    else:                                   # no number: the line itself is the hero, smaller
        hero, hero_class, label_words = esc(o["text"]), "small", []
    label = " ".join(f'<span class="mb-orange">{esc(w)}</span>'
                     if is_orange(w, orange) and "mb-orange" not in hero_class else esc(w) for w in label_words)
    css, js = number_wheel()
    return fill((LIB / "templates/data_card.html").read_text(encoding="utf-8"),
                id=cid, brand_css=brand, number_wheel_css=css, number_wheel_js=js,
                bg="ink" if o.get("bg") == "ink" else "cream", eyebrow=esc(o.get("eyebrow", "")),
                hero=hero, hero_class=hero_class, label=label, source=esc(o.get("source_line", "")),
                dur=f"{dur:.3f}")


def custom_scene(o, cid, dur, brand, proj):
    """A one-off HyperFrames scene made for this short (any animation, map, chart, kinetic type, registry block).
    The EDL event names its source file; this copies it in under the mount id and inlines the brand tokens.
    The file follows the HyperFrames scene contract with "{{id}}" wherever the scene id goes, and may use
    {{brand_css}} and {{dur}}, and {{cue_<name>}} for each of the EDL event's "cue_times" (seconds from the scene's
    start to a spoken word, from plan_shorts.py "cues"), so beats inside the scene follow the A-roll instead of
    being typed as numbers. Assets it needs go in its "assets" list (copied to the project's assets/)."""
    src = Path(o["src"])
    for a in o.get("assets", []):
        dst = proj / "assets" / Path(a).name
        shutil.copy(a, dst)
    tpl = src.read_text(encoding="utf-8")
    slots = {"id": cid, "brand_css": brand, "dur": f"{dur:.3f}",
             **{f"cue_{n}": f"{v:.3f}" for n, v in o.get("cue_times", {}).items()}}
    missing = sorted(set(re.findall(r"\{\{(cue_\w+)\}\}", tpl)) - set(slots))
    if missing:
        sys.exit(f"{src.name} uses {missing} but the EDL event has no such cue (plan_shorts.py \"cues\")")
    return fill(tpl, **{k: v for k, v in slots.items() if "{{" + k + "}}" in tpl})


def brand_css(edl, proj):
    """graphics\brand.css filled with the client's brand; copies its font files into the project."""
    b = kit.brand(edl)
    faces, seen = [], set()
    for role in ("heavy", "bold", "label"):
        f = b["fonts"].get(role)
        if not f:
            continue
        name = Path(f["path"]).name
        if name not in seen:
            shutil.copy(f["path"], proj / "assets/fonts" / name)
            seen.add(name)
        w = f.get("weight", 400)
        faces.append(f'@font-face {{ font-family: "{f["family"]}"; font-weight: {w}; '
                     f'src: url("assets/fonts/{name}"); }}')
    heavy, label = b["fonts"]["heavy"], b["fonts"].get("label", b["fonts"]["heavy"])
    c = b["colors"]
    return fill((LIB / "brand.css").read_text(encoding="utf-8"), font_faces="\n".join(faces),
                ink=c["ink"], cream=c["cream"], accent=c["accent"], accent_text=c.get("accent_text", c["white"]),
                gray=c["gray"], white=c["white"], heavy_family=heavy["family"], heavy_weight=heavy.get("weight", 800),
                label_family=label["family"], label_weight=label.get("weight", 500))


def build(edl, rd, n_frames):
    proj = rd / "hf"
    # rewrite only what this script generates; .hyperframes\ (project history, snapshots) is never deleted
    (proj / "compositions").mkdir(parents=True, exist_ok=True)
    (proj / "assets/fonts").mkdir(parents=True, exist_ok=True)
    for old in (proj / "compositions").glob("g[0-9][0-9]-*.html"):
        old.unlink()
    shutil.copy(LIB / "vendor/gsap.min.js", proj / "assets/gsap.min.js")   # GSAP 3.14.2, local: no network at render
    brand = brand_css(edl, proj)
    total = n_frames / FPS
    hosts, plan = [], []
    for k, o in enumerate(overlays(edl), 1):
        start = round(o["t"], 3)
        end = min(o.get("t_out", o["t"] + 2.5), total)
        dur = round(end - start, 3)
        cid = f"g{k:02d}-{o['kind'].replace('_', '-')}"
        if o["kind"] == "hf_scene":
            html_ = custom_scene(o, cid, dur, brand, proj)
        else:
            html_ = {"title_card": title_card, "chip": chip, "card": data_card}[o["kind"]](o, cid, dur, brand)
        (proj / "compositions" / f"{cid}.html").write_text(html_, encoding="utf-8")
        hosts.append(
            f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html"\n'
            f'           data-start="{start}" data-duration="{dur}" data-track-index="{k}" data-track-kind="graphics"\n'
            f'           data-width="{W}" data-height="{H}" style="z-index: {k}"></div>')
        plan.append({"id": cid, "kind": o["kind"], "text": o.get("text") or o.get("note"), "t": start,
                     "t_out": round(end, 3), "full_bleed": o["kind"] == "card" or bool(o.get("full_bleed")),
                     "background": bool(o.get("background"))})
    index = (
        "<!doctype html>\n<html>\n  <head>\n    <meta charset=\"utf-8\" />\n"
        '    <script src="assets/gsap.min.js"></script>\n  </head>\n  <body>\n'
        f'    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}"\n'
        f'         data-width="{W}" data-height="{H}">\n' + "\n".join(hosts) + "\n    </div>\n"
        '    <script>\n      window.__timelines["main"] = gsap.timeline({ paused: true });\n    </script>\n'
        "  </body>\n</html>\n")
    (proj / "index.html").write_text(index, encoding="utf-8")
    (proj / "graphics_plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"built {proj} ({len(plan)} graphics, {total:.2f} s)")
    return proj, plan


def check(proj, edl=None):
    r = subprocess.run(hf_cli() + ["check", "--json"], cwd=proj, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    (proj / "check.json").write_text(r.stdout, encoding="utf-8")
    try:
        rep = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        sys.exit(f"hyperframes check produced no JSON:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    found = [f for sec in rep.values() if isinstance(sec, dict) for f in sec.get("findings", [])]
    # Expected for a transparent overlay layer, not a standalone film: blank between graphics (the footage plays
    # there), no audio (mixed by render_short.py), and the counter's in-between digits rolling past unread.
    expected = {"subcomposition_blanks_before_host", "first_frame_empty", "film_silent", "dead_stretch"}

    def is_expected(f):
        return f.get("code") in expected or (
            f.get("code") == "line_unread" and re.match(r'^"\d" \(1 word\)', f.get("message", "")))
    errors = [f for f in found if f.get("severity") == "error"]
    warns = [f for f in found if f.get("severity") == "warning" and not is_expected(f)]
    # text on screen too short to read is a fix, not noise (promo-01: "BACK IN 48 H" held 0.76 s): hold it
    # 0.5 s + 0.3 s per word, or list the exact message text in the EDL's "unread_ok" after Franco agrees
    ok = set(edl.get("unread_ok", [])) if edl else set()
    unread = [f for f in warns if f.get("code") == "line_unread" and not any(x in f.get("message", "") for x in ok)]
    for f in errors + warns:
        print(f"  {'FIX' if f in unread else f.get('severity')}: {f.get('code')}: {f.get('message', '')[:200]}")
    if rep.get("browserSkipped"):
        print("  note: check skipped its browser audits (runtime/layout/contrast)")
    print(f"check: {len(errors)} errors, {len(warns)} warnings (full report: {proj / 'check.json'})")
    if errors or rep.get("ok") is False:
        sys.exit("hyperframes check failed")
    if unread:
        sys.exit(f"{len(unread)} on-screen text(s) too short to read: hold them longer (0.5 s + 0.3 s per word)")
    return rep


def snapshot(proj, plan):
    ats = ",".join(f"{(p['t'] + min(p['t_out'], p['t'] + 1.6)) / 2:.2f}" for p in plan)
    subprocess.run(hf_cli() + ["snapshot", "--at", ats], cwd=proj, check=True)


def measure(mov, plan):
    """Bounding box of the visible pixels of each graphic at its midpoint, from the rendered layer."""
    out = []
    for p in plan:
        t = (p["t"] + p["t_out"]) / 2
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mov), "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
        a = np.frombuffer(raw[:W * H * 4], np.uint8).reshape(H, W, 4)[:, :, 3]
        ys, xs = np.nonzero(a > 16)
        box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None
        out.append({**p, "bbox": box})
    return out


def render(proj, plan, rd):
    mov = rd / "graphics.mov"
    subprocess.run(hf_cli() + ["render", "--format", "mov", "--fps", str(FPS), "--quality", "delivery",
                               "--output", str(mov.resolve())], cwd=proj, check=True)
    layout = measure(mov, plan)
    (rd / "graphics_layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", mov)
    return mov


def run(edl, rd, n_frames, stages=("build", "check", "render")):
    proj, plan = build(edl, rd, n_frames)
    if "check" in stages:
        check(proj, edl)
    if "snapshot" in stages:
        snapshot(proj, plan)
    if "render" in stages:
        return render(proj, plan, rd)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--frames", type=int, help="length in frames (default: render\\<short>\\picture_runs.json)")
    ap.add_argument("--stage", default="all", choices=["build", "check", "snapshot", "render", "all"])
    a = ap.parse_args()
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    rd = kit.Project(edl).render_dir(edl["short"])
    rd.mkdir(parents=True, exist_ok=True)
    n = a.frames or json.loads((rd / "picture_runs.json").read_text(encoding="utf-8"))["frames"]
    stages = {"build": ("build",), "check": ("build", "check"), "snapshot": ("build", "check", "snapshot"),
              "render": ("build", "check", "render"), "all": ("build", "check", "render")}[a.stage]
    run(edl, rd, n, stages)


if __name__ == "__main__":
    main()
