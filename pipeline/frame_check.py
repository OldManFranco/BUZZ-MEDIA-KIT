r"""
Buzz Media kit — frame checks on the graphics layer (CLAUDE.md §5 step 5-6, §7): the subject's face, the phone safe
zone, the space above the captions, and blank space, measured on real frames instead of one mockup.

Called by build_graphics.py (--stage snapshot: on exact-alpha snapshots, before anything renders) and by
render_short.py (graphics stage: on every frame of graphics.mov). Standalone:
  python pipeline/frame_check.py <edl> [--mov <graphics.mov>] [--faces <faces.json>]

Checks (each frame, with the overlays live at that time and the picture the renderer puts under it, from
render_short.picture_plan + faces.json):
  face       no graphic over the subject's face, forehead to chin, from the face_track samples nearest that frame
             (punch-ins, split screen, pip and pull-back moves included). A moving element may pass the LOWER face
             for up to 0.5 s (Franco, 2026-10-28); anything on the eyes/forehead, or longer, fails. Skipped while a
             full-frame graphic hides the picture, and inside a "matte" scene's cutout span (its "matte_until"):
             after the cutout ends, anything left behind the subject shows on the face and fails here (promo-03).
  safe zone  drawn pixels (shadows and pop-up scale included, since they're measured on the frame) inside y 260-1440,
             x 140-940. Full-frame artwork ("background", "full_bleed", "matte") and the top panel of a split are
             exempt by design.
  captions   >= 20 px of empty space between a graphic and the caption group live at that time, and no caption
             drawn over a graphic (promo-03: a source line under a chest card sat in the caption band).
  blank      a split's top half and everything outside a pip are covered by graphics; a "background" scene covers
             the whole frame, with no plain band along an edge (promo-03: a zoom-out showed its artwork's edge).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402
import render_short as rs  # noqa: E402

FPS, W, H = 30, 1080, 1920
SAFE = {"x0": 140, "x1": 940, "y0": 260, "y1": 1440}
CAPTION_GAP = 20
BRIEF_PASS_S = 0.5
OVERLAYS = ("title_card", "chip", "card", "hf_scene")
EXEMPT = ("background", "full_bleed", "matte")


class Picture:
    """Where the renderer puts the subject's face, frame by frame (output pixels)."""

    def __init__(self, edl, faces):
        self.edl, self.faces = edl, faces
        self.runs, self.n = rs.picture_plan(edl, faces)
        self.arolls = [e for e in edl["events"] if e["kind"] == "aroll"]
        self.at = np.zeros(self.n, int)
        for i, r in enumerate(self.runs):
            self.at[r["f0"]: r["f0"] + r["n"]] = i
        self.inp = kit.Project(edl).input

    def run(self, f):
        return self.runs[self.at[min(max(f, 0), self.n - 1)]]

    def affine(self, r, f, sw, sh):
        """(s, ox, oy): output = s * source + o for the run's framing at frame f."""
        if r.get("move"):
            a = rs.move_affine(r, f - r["f0"], sw, sh)
            return 1 / a[0], -a[2] / a[0], -a[5] / a[0]
        if r["mode"] == "pip":
            p = self.edl["pip"]
            h = min(p["crop_h_src"], sh)
            w = h * p["w"] / p["h"]
            x = min(max(r["xc"] * sw - w / 2, 0), sw - w)
            y = min(max(r["eyes_y"] * sh - 0.30 * h, 0), sh - h)
            sc = p["w"] / w
            return sc, p["x"] - sc * x, p["y"] - sc * y
        return rs.frame_map(r["mode"], r["scale"], r, sw, sh)

    def face(self, f):
        """{"x0", "x1", "top", "nose", "chin"} of the face in output pixels at frame f, or None."""
        r = self.run(f)
        if r["kind"] != "aroll" or Path(r["src"]).suffix.lower() in rs.STILL_EXT:
            return None
        a = self.arolls[r["k"][0]] if isinstance(r["k"][0], int) else None
        fc = self.faces.get(f"{a['src']}|{a['in']}|{a['out']}", {}) if a else {}
        if not fc.get("n"):
            return None
        t_src = r["t"] + (f - r["f0"]) / FPS
        if fc.get("samples"):
            s = min(fc["samples"], key=lambda x: abs(x[0] - t_src))
            ex, ey, fh, top, chin = s[1], s[2], s[3], s[4], s[5]
        else:   # older faces.json: medians only
            ex, ey, fh = fc["eyes_x"], fc["eyes_y"], fc["face_h"]
            top, chin = ey - 0.40 * fh, ey + 0.60 * fh
        sw, sh = rs.src_size(self.inp / r["src"])
        sc, ox, oy = self.affine(r, f, sw, sh)
        half = 0.42 * fh * sh
        box = {"x0": sc * (ex * sw - half) + ox, "x1": sc * (ex * sw + half) + ox, "top": sc * top * sh + oy,
               "nose": sc * (ey + 0.25 * fh) * sh + oy, "chin": sc * chin * sh + oy}
        if r["mode"] == "split" and not r.get("move"):
            box["top"] = max(box["top"], H / 2)
        return box

    def mode(self, f):
        r = self.run(f)
        return "move" if r.get("move") else r["mode"]


def captions_layer(edl):
    """The real caption layer (build_captions.Layer) on the plan's own words."""
    import build_captions
    sw = edl["spoken_words"]      # plans before v0.3 have no word ends: use the next word's start
    words = [{"w": w["w"], "start": w["t"],
              "end": w.get("e", min(sw[i + 1]["t"] if i + 1 < len(sw) else w["t"] + 0.4, w["t"] + 0.6))}
             for i, w in enumerate(sw)]
    n = int(round(edl["length_s"] * FPS)) + 1
    return build_captions.Layer(json.loads(json.dumps(edl)), words, n)


def live(edl, t):
    return [o for o in edl["events"] if o["kind"] in OVERLAYS and o["t"] <= t < o.get("t_out", o["t"] + 2.5)]


def in_matte(o, t):
    return o.get("matte") and t < o["t"] + o.get("matte_until", 1e9)


def check(edl, frames, faces=None, scale=1.0, gap=0.2):
    """frames: iterable of (t, rgba uint8 array H*scale x W*scale x 4). Returns (findings, frames checked)."""
    pic = Picture(edl, faces) if faces else None
    caps = captions_layer(edl)
    k = scale
    hits = {"face": [], "safe": [], "captions": [], "blank": []}
    count = 0
    for t, im in frames:
        count += 1
        f = int(round(t * FPS))
        a = im[..., 3]
        ov = live(edl, t)
        # a cutaway by design: full-frame artwork, a cutout, a frame the graphics fill (older plans without the
        # flags), or the first 0.3 s of a planned flash wipe ("flash_in")
        exempt = (any(o.get(x) for o in ov for x in EXEMPT) or float((a > 128).mean()) > 0.9
                  or any(o.get("flash_in") and t < o["t"] + 0.3 for o in ov))
        mode = pic.mode(f) if pic else "full"
        drawn = a > 16
        # ---- face
        if pic and not any(in_matte(o, t) for o in ov):
            b = pic.face(f)
            if b:
                x0, x1 = int(max(b["x0"], 0) * k), int(min(b["x1"], W) * k)
                top, nose, chin = (int(min(max(v, 0), H) * k) for v in (b["top"], b["nose"], b["chin"]))
                upper, lower = a[top:nose, x0:x1], a[nose:chin, x0:x1]
                cover = lambda z: float((z > 128).mean()) if z.size else 0.0
                # a cutaway: full-frame artwork (also while it slides in over the picture) or a frame-filling flash
                if not (exempt and not any(o.get("matte") for o in ov)) and (cover(upper) > 0.03 or cover(lower) > 0.03):
                    rows = np.nonzero((a[top:chin, x0:x1] > 128).mean(axis=1) > 0.03)[0]
                    hits["face"].append((t, "upper" if cover(upper) > 0.03 else "lower", round(b["top"]),
                                         round(b["chin"]), round(rows.min() / k + top / k), round(rows.max() / k + top / k)))
        # ---- safe zone
        if not exempt:
            m = drawn.copy()
            if mode in ("split", "move"):
                m[: int(H / 2 * k)] = False                              # the top panel is full-width by design
            out = m.copy()
            out[int(SAFE["y0"] * k): int(SAFE["y1"] * k) + 1, int(SAFE["x0"] * k): int(SAFE["x1"] * k) + 1] = False
            if out.any():
                ys, xs = np.nonzero(out)
                hits["safe"].append((t, [int(xs.min() / k), int(ys.min() / k), int(xs.max() / k) + 1,
                                         int(ys.max() / k) + 1]))
        # ---- captions
        g = next((g for g in caps.layout_log["captions"] if g["t0"] <= t < g["t1"]), None)
        muted = any(o.get("mute_captions") or o["kind"] == "card" or o.get("full_bleed") for o in ov) or \
            any(lo <= t < hi for lo, hi in caps.mutes)
        if g and not muted and not exempt and mode == "full":
            cx0, cy0, cx1, cy1 = g["bbox"]
            cy0 += 6                               # the bbox carries 16 px of padding; the word plate starts 6 px in
            y_from = max(int((cy0 - 400) * k), 0)
            region = a[y_from: int(cy1 * k), int(cx0 * k): int(cx1 * k)]

            def bottom(th):
                rows = np.nonzero((region > th).any(axis=1))[0]
                return y_from / k + rows.max() / k if len(rows) else None
            solid_b, soft_b = bottom(200), bottom(40)          # the graphic itself / with its shadow
            if solid_b is not None and solid_b > cy0:
                hits["captions"].append((t, f"caption '{g['text']}' drawn over a graphic (graphic to y "
                                            f"{int(solid_b)}, caption plate from y {cy0})"))
            elif soft_b is not None and cy0 - soft_b < CAPTION_GAP:
                hits["captions"].append((t, f"graphic (shadow included) ends {int(cy0 - soft_b)} px from caption "
                                            f"'{g['text']}' (min {CAPTION_GAP})"))
        # ---- blank space
        solid = a >= 250
        if mode == "split":
            top = solid[: int(H / 2 * k)]
            if top.mean() < 0.99:
                hits["blank"].append((t, f"split top half {100 * (1 - top.mean()):.0f}% uncovered (bare ink)"))
        elif mode == "pip" and edl.get("pip"):
            p = edl["pip"]
            m = np.ones_like(solid)
            m[int(p["y"] * k): int((p["y"] + p["h"]) * k), int(p["x"] * k): int((p["x"] + p["w"]) * k)] = False
            if solid[m].mean() < 0.99:
                hits["blank"].append((t, f"pip frame {100 * (1 - solid[m].mean()):.0f}% uncovered around the pip"))
        # a full-frame scene may slide or wipe in and out over the live picture (its first and last 0.3 s); in
        # between, its artwork covers the frame at every scale it reaches
        bg = [o for o in ov if o.get("background")]
        if bg and all(o["t"] + 0.3 <= t < o.get("t_out", o["t"] + 2.5) - 0.3 for o in bg):
            if solid.mean() < 0.995:
                hits["blank"].append((t, f"background scene leaves {100 * (1 - solid.mean()):.1f}% of the frame "
                                         f"uncovered"))
            else:
                rgb = im[..., :3].astype(np.float32)
                e = max(int(12 * k), 2)
                for side, strip, inner in (("top", rgb[:e], rgb[e:e * 5]), ("bottom", rgb[-e:], rgb[-e * 5:-e]),
                                           ("left", rgb[:, :e], rgb[:, e:e * 5]),
                                           ("right", rgb[:, -e:], rgb[:, -e * 5:-e])):
                    if strip.std() < 1.5 and inner.std() > 6:
                        hits["blank"].append((t, f"plain band along the {side} edge (the artwork's edge shows)"))
    return summarize(hits, gap), count


def spans(items, key, gap=0.2):
    """Group (t, ...) hits into [t0, t1, first item, all items] spans: consecutive times with the same key."""
    out = []
    for h in sorted(items, key=lambda x: x[0]):
        if out and h[0] - out[-1][1] <= gap and key(h) == key(out[-1][2]):
            out[-1][1] = h[0]
            out[-1][3].append(h)
        else:
            out.append([h[0], h[0], h, [h]])
    return out


def summarize(hits, gap=0.2):
    found = []
    for t0, t1, h, _ in spans(hits["face"], key=lambda h: h[1], gap=gap):
        dur = t1 - t0 + 1 / FPS
        if h[1] == "lower" and dur <= BRIEF_PASS_S:
            found.append(("NOTE", "face", t0, t1, f"a graphic passes the lower face for {dur:.2f} s (brief pass, "
                                                  f"allowed)"))
        else:
            found.append(("FAIL", "face", t0, t1, f"a graphic covers the {h[1]} face for {dur:.2f} s (face y "
                                                  f"{h[2]}-{h[3]}, covered y {h[4]}-{h[5]} at {t0:.2f} s)"))
    for t0, t1, h, _ in spans(hits["safe"], key=lambda h: 0, gap=gap):
        found.append(("FAIL", "safe zone", t0, t1, f"graphics drawn at {h[1]} (safe x {SAFE['x0']}-{SAFE['x1']}, "
                                                   f"y {SAFE['y0']}-{SAFE['y1']})"))
    over = lambda h: "over a graphic" in h[1]
    for t0, t1, h, all_ in spans(hits["captions"], key=over, gap=gap):
        n = len(all_)
        found.append(("FAIL" if over(h) else "WARN", "captions", t0, t1,
                      h[1] + (f" (+{n - 1} more frames)" if n > 1 else "")))
    for t0, t1, h, all_ in spans(hits["blank"], key=lambda h: h[1].split(" ")[0], gap=gap):
        found.append(("FAIL", "blank", t0, t1, h[1] + (f" (over {len(all_)} frames)" if len(all_) > 1 else "")))
    return found


def report(found, count, dst=None):
    for lvl, what, t0, t1, msg in found:
        print(f"  {lvl:4s} {what:9s} {t0:6.2f}-{t1:6.2f} s  {msg}")
    fails = [x for x in found if x[0] == "FAIL"]
    print(f"frame check: {count} frames, {len(fails)} failures, "
          f"{sum(x[0] == 'WARN' for x in found)} warnings, {sum(x[0] == 'NOTE' for x in found)} notes")
    if dst:
        Path(dst).write_text(json.dumps([dict(zip(("level", "check", "t0", "t1", "detail"), x)) for x in found],
                                        indent=1, ensure_ascii=False), encoding="utf-8")
    return not fails


def load_faces(edl, path=None):
    p = Path(path) if path else kit.Project(edl).render_dir(edl["short"]) / "faces.json"
    if not p.exists():
        print(f"  no {p.name}: face checks skipped (run face_track.py first)")
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def mov_frames(mov, scale=0.5, step=1):
    """Every step-th frame of a transparent graphics.mov, as RGBA at the given scale."""
    w, h = int(W * scale), int(H * scale)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(mov), "-vf", f"scale={w}:{h}:flags=area",
                          "-pix_fmt", "rgba", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    f = 0
    while True:
        buf = p.stdout.read(w * h * 4)
        if len(buf) < w * h * 4:
            break
        if f % step == 0:
            yield f / FPS, np.frombuffer(buf, np.uint8).reshape(h, w, 4)
        f += 1
    p.wait()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--mov", help="graphics.mov to check (default: render\\<short>\\graphics.mov)")
    ap.add_argument("--faces", help="faces.json (default: render\\<short>\\faces.json)")
    ap.add_argument("--out", help="write the findings here as JSON")
    a = ap.parse_args()
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    rd = kit.Project(edl).render_dir(edl["short"])
    mov = Path(a.mov) if a.mov else rd / "graphics.mov"
    found, n = check(edl, mov_frames(mov), load_faces(edl, a.faces), scale=0.5)
    sys.exit(0 if report(found, n, a.out) else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
