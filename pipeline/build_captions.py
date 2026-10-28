r"""
Buzz Media kit — the graphics layer for a short: karaoke captions, title card, chips.

Used by render_short.py (stage "final"): Layer(edl, words, n_frames).frame(f) returns one
1080x1920 RGBA frame (bytes) that ffmpeg overlays on picture.mp4. layout_log records every
element's box and times for qa.py.

Spec: CLAUDE.md §7 (captions, title card) + the client's _brand\brand.json (colors, fonts, caption case),
read through kit.brand(). "orange" in EDLs and in this file's names means the brand's accent color.
Render-time choices that differ from the [DRAFT] spec are listed in RENDER_NOTES and copied to the QA report.
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

FPS, W, H = 30, 1080, 1920
# set from the client's brand.json by apply_brand(); fonts are (path, weight) so variable fonts work
INK = CREAM = ORANGE = ORANGE_TEXT = GRAY = WHITE = None
FONT_XB = FONT_MD = None
CASE = "upper"

CAP_SIZE, CAP_MAXW, CAP_BASE_Y = 86, 760, 1360  # base y: EDL "caption_base_y" overrides (split screen: ~990)      # 760 + plate padding, centered at 540, stays left of x=940
CAP_MIN = 72                                         # a group may shrink to this before it splits
WORD_GAP = 26                                        # on top of the font space: the 6 px outline and plate eat it
CARD_TOP, CHIP_CY = 300, 380
RENDER_NOTES = [
    "Title card at y 300-~600 and chips centered at y 380 (spec said y 420-760 / 500-900): in these selfie "
    "framings the speaker's face fills y ~300-1180, so the spec band would cover his eyes. The top band only overlaps hair/sky.",
    "Caption max width 760 px (spec ~900) so a centered group, plate included, never crosses x = 940. A group that doesn't fit at 86 px shrinks (to 72 px min) instead of splitting into one-word groups.",
    "While an orange graphic is on screen (title card, orange chip), the caption's active-word plate turns ink "
    "with white text: one orange element at a time (a cream plate vanished over the cream shirt in s1).",
    "Captions mute under a chip that shows the same words (mute_captions).",
]
FIXES = {"u.s": "US"}   # kit-wide spellings only; per-reel fixes go in the EDL's "caption_fixes"
UNITS = {"pesos", "us", "dollars", "minutes", "years", "times"}
CARRY = {"THE", "A", "AN", "TO", "OF", "AT", "ON", "IN", "FOR", "AND", "EL", "LA", "LOS", "LAS", "DE", "DEL"}


def apply_brand(edl):
    """Colors, fonts, caption case and caption height for this EDL's client (kit.brand)."""
    global INK, CREAM, ORANGE, ORANGE_TEXT, GRAY, WHITE, FONT_XB, FONT_MD, CASE, CAP_BASE_Y
    b = kit.brand(edl)
    c = {k: kit.rgb(v) for k, v in b["colors"].items()}
    INK, CREAM, ORANGE, GRAY, WHITE = c["ink"], c["cream"], c["accent"], c["gray"], c["white"]
    ORANGE_TEXT = c.get("accent_text", c["white"])
    FONT_XB = (b["fonts"]["heavy"]["path"], b["fonts"]["heavy"].get("weight"))
    lab = b["fonts"].get("label", b["fonts"]["heavy"])
    FONT_MD = (lab["path"], lab.get("weight"))
    CASE = b.get("caption_case", "upper")
    CAP_BASE_Y = int(edl.get("caption_base_y", 1360))


@lru_cache(None)
def font(spec, size):
    path, weight = spec
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([weight])      # variable font (Schibsted Grotesk[wght])
        except OSError:
            pass                                   # static font: the file is the weight
    return f


def ease_out(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def clean(w):
    k = w.strip().lower()
    if k.strip(".,?!") in FIXES:
        w = FIXES[k.strip(".,?!")] + ("?" if k.endswith("?") else "")
    w = re.sub(r"[.,!]+$", "", w)                      # keep '?' and inner commas (70,000)
    return w.upper() if CASE == "upper" else w


class Layer:
    def __init__(self, edl, words, n_frames):
        apply_brand(edl)
        self.n = n_frames
        # "graphics_engine": "hyperframes" -> title cards/chips/cards come from build_graphics.py (graphics.mov);
        # this layer keeps their timing for the one-orange rule and caption muting but doesn't draw them
        self.draw_overlays = edl.get("graphics_engine", "pillow") != "hyperframes"
        self.layout_log = {"notes": RENDER_NOTES, "captions": [], "overlays": []}
        self.overlays = [e for e in edl["events"] if e["kind"] in ("title_card", "chip", "card", "hf_scene")]
        for o in self.overlays:
            o.setdefault("t_out", o["t"] + 2.5)
        # pictures that are themselves orange (e.g. the Temu logo card) count as the one orange element
        self.orange_spans = [(e["t"], e["t_out"]) for e in edl["events"] if e["kind"] == "broll" and e.get("orange")]
        # EDL "caption_fixes": {"$180,": "180,"} per-short spelling fixes on the final-audio transcript
        # (s2: WhisperX wrote peso amounts as dollars and dropped the Spanish ¿?), applied before clean()
        # a key "of@51.48" fixes only the word starting within 0.15 s of that time ("of" -> "of the")
        fixes = edl.get("caption_fixes", {})
        timed = [(k.rsplit("@", 1)[0], float(k.rsplit("@", 1)[1]), v) for k, v in fixes.items() if "@" in k[1:]]

        def fix(w):
            for k, at, v in timed:
                if w["w"] == k and abs(w["start"] - at) <= 0.15:
                    return v
            return fixes.get(w["w"], w["w"])
        self.words = [{"w": clean(fix(w)), "raw": fix(w), "s": w["start"], "e": w["end"]} for w in words]
        self.break_before = edl.get("caption_break_before", [])
        self.join = edl.get("caption_join", [])
        self.groups = self._group()
        self._layout()

    # ------------------------------------------------------------ captions
    def _group(self):
        emph = lambda w: bool(re.search(r"\d", w["w"]))
        unit = lambda w: w["w"].lower() in UNITS
        groups, cur = [], []
        # EDL "caption_break_before": ["ONE HANDSHAKE"] starts a new group at that phrase (payoff lines)
        forced = set()
        for ph in self.break_before:
            ph = ph.upper().split()
            for i in range(len(self.words) - len(ph) + 1):
                if [x["w"].upper() for x in self.words[i:i + len(ph)]] == ph:
                    forced.add(i)
        # EDL "caption_join": ["¿Y SI LE COMPRO DOS?"] keeps a phrase in one group across pauses
        joined = set()
        for ph in self.join:
            ph = ph.upper().split()
            for i in range(len(self.words) - len(ph) + 1):
                if [x["w"].upper() for x in self.words[i:i + len(ph)]] == ph:
                    joined.update(range(i + 1, i + len(ph)))
        for i, w in enumerate(self.words):
            if cur and i in joined:
                pass
            elif cur and i in forced:
                groups.append(cur)
                cur = []
            elif cur:
                prev = cur[-1]
                in_emph = emph(cur[0]) and all(emph(x) or unit(x) for x in cur)
                ends_thought = (re.search(r"[.,?!]$", prev["raw"])
                                and not re.fullmatch(r"(?:[A-Za-z]\.){2,}", prev["raw"]))   # "U.S." isn't an ending
                # a number keeps its unit across a pause, even if that needs two lines ("22 US / DOLLARS")
                keeps_unit = in_emph and unit(w)
                brk = (len(cur) >= 4
                       or (not keeps_unit and (w["s"] - prev["e"] > 0.3 or ends_thought
                                               or self._width([x["w"] for x in cur + [w]], CAP_MIN) > CAP_MAXW))
                       or (emph(w) and not in_emph)
                       or (in_emph and not unit(w)))
                if brk:
                    # never leave "THE", "EL", "TO"... dangling at the end of a group: carry it forward
                    if (len(cur) > 1 and cur[-1]["w"].upper() in CARRY and not ends_thought
                            and w["s"] - prev["e"] <= 0.3):
                        groups.append(cur[:-1])
                        cur = [cur[-1]]
                    else:
                        groups.append(cur)
                        cur = []
            cur.append(w)
        if cur:
            groups.append(cur)
        out = []
        for k, g in enumerate(groups):
            nxt = groups[k + 1][0]["s"] if k + 1 < len(groups) else g[-1]["e"] + 0.6
            out.append({"words": g, "t0": g[0]["s"] - 0.05, "t1": min(nxt - 0.05, g[-1]["e"] + 0.4),
                        "emph": any(emph(w) for w in g)})
        return out

    @staticmethod
    def _width(ws, size):
        f = font(FONT_XB, size)
        return sum(f.getlength(w) for w in ws) + (f.getlength(" ") + WORD_GAP) * (len(ws) - 1)

    def _layout(self):
        for g in self.groups:
            size = int(CAP_SIZE * 1.1) if g["emph"] else CAP_SIZE
            ws = [w["w"] for w in g["words"]]
            floor = 50 if len(ws) == 1 else CAP_MIN
            while self._width(ws, size) > CAP_MAXW and size > floor:
                size -= 2
            lines = [ws]
            if self._width(ws, size) > CAP_MAXW and len(ws) > 1:      # two balanced lines
                best = min(range(1, len(ws)), key=lambda k: abs(self._width(ws[:k], size) - self._width(ws[k:], size)))
                lines = [ws[:best], ws[best:]]
            f = font(FONT_XB, size)
            sp = f.getlength(" ") + WORD_GAP
            lh = int(size * 1.15)
            base0 = CAP_BASE_Y - (len(lines) - 1) * lh
            boxes, k = [], 0
            for li, line in enumerate(lines):
                x = W / 2 - self._width(line, size) / 2
                y = base0 + li * lh
                for w in line:
                    l, t, r, b = f.getbbox(w, anchor="ls")
                    boxes.append({"w": w, "x": x, "y": y, "box": (x + l, y + t, x + r, y + b), "word": g["words"][k]})
                    x += f.getlength(w) + sp
                    k += 1
            g.update(size=size, boxes=boxes)
            x0 = min(b["box"][0] for b in boxes) - 14      # = plate padding
            x1 = max(b["box"][2] for b in boxes) + 14
            y0 = min(b["box"][1] for b in boxes) - 16
            y1 = max(b["box"][3] for b in boxes) + 16
            g["bbox"] = (int(x0), int(y0), int(x1), int(y1))
            self.layout_log["captions"].append({"t0": round(g["t0"], 3), "t1": round(g["t1"], 3),
                                                "text": " ".join(ws), "n_words": len(ws), "bbox": g["bbox"],
                                                "words": [{"w": b["w"], "s": b["word"]["s"], "e": b["word"]["e"]}
                                                          for b in boxes]})

    @lru_cache(None)
    def _shadow(self, gi):
        g = self.groups[gi]
        f = font(FONT_XB, g["size"])
        im = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(im)
        for b in g["boxes"]:
            d.text((b["x"], b["y"] + 4), b["w"], font=f, fill=INK + (255,), anchor="ls", stroke_width=6,
                   stroke_fill=INK + (255,))
        x0, y0, x1, y1 = g["bbox"]
        crop = im.crop((x0 - 30, y0 - 30, x1 + 30, y1 + 30)).filter(ImageFilter.GaussianBlur(8))
        a = crop.getchannel("A").point(lambda v: int(v * 0.4))
        crop.putalpha(a)
        return crop, (x0 - 30, y0 - 30)

    @lru_cache(None)
    def _text(self, gi, active, plate_style):
        g = self.groups[gi]
        f = font(FONT_XB, g["size"])
        fa = font(FONT_XB, int(round(g["size"] * 1.08)))
        im = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(im)
        for k, b in enumerate(g["boxes"]):
            if k == active:
                continue
            d.text((b["x"], b["y"]), b["w"], font=f, fill=WHITE + (255,), anchor="ls", stroke_width=6,
                   stroke_fill=INK + (255,))
        if active is not None:
            b = g["boxes"][active]
            cx = (b["box"][0] + b["box"][2]) / 2
            cy = (b["box"][1] + b["box"][3]) / 2
            col = ORANGE_TEXT if plate_style == "orange" else WHITE
            d.text((cx, cy), b["w"], font=fa, fill=col + (255,), anchor="mm")
        x0, y0, x1, y1 = g["bbox"]
        return im.crop((x0 - 30, y0 - 40, x1 + 30, y1 + 40)), (x0 - 30, y0 - 40)

    def _plate_rect(self, g, k):
        x0, y0, x1, y1 = g["boxes"][k]["box"]
        return (x0 - 14, y0 - 10, x1 + 14, y1 + 10)

    def _captions(self, canvas, t, orange_busy, muted):
        gi = next((i for i, g in enumerate(self.groups) if g["t0"] <= t < g["t1"]), None)
        if gi is None or muted:
            return
        g = self.groups[gi]
        ws = [b["word"] for b in g["boxes"]]
        k = max([i for i, w in enumerate(ws) if w["s"] <= t] or [0])
        style = "ink" if orange_busy else "orange"
        oy = CAP_BASE_Y - 360                                    # local band: 360 above the baseline, 160 below
        layer = Image.new("RGBA", (W, 520))
        sh, (sx, sy) = self._shadow(gi)
        layer.alpha_composite(sh, (sx, sy - oy))
        # plate slides from the previous word over 80 ms
        r1 = self._plate_rect(g, k)
        if k > 0:
            p = ease_out((t - ws[k]["s"]) / 0.08)
            r0 = self._plate_rect(g, k - 1)
            r1 = tuple(a + (b - a) * p for a, b in zip(r0, r1))
        ImageDraw.Draw(layer).rounded_rectangle((r1[0], r1[1] - oy, r1[2], r1[3] - oy), radius=10,
                                                fill=(ORANGE if style == "orange" else INK) + (255,))
        tx, (px, py) = self._text(gi, k, style)
        layer.alpha_composite(tx, (int(px), int(py - oy)))
        # group in: 80 -> 100% over 4 frames
        age = (t - g["t0"]) * FPS
        if age < 4:
            s = 0.8 + 0.2 * ease_out(age / 4)
            cy = (g["bbox"][1] + g["bbox"][3]) / 2 - oy
            scaled = layer.resize((int(W * s), int(520 * s)), Image.LANCZOS)
            nx, ny = int(W / 2 - W * s / 2), int(cy - cy * s)
            layer = Image.new("RGBA", (W, 520))
            layer.alpha_composite(scaled, (max(nx, 0), max(ny, 0)))
        canvas.alpha_composite(layer, (0, oy))

    # ------------------------------------------------------------ title card + chips
    @staticmethod
    def _spaced(d, xy, text, f, fill, spacing):
        x, y = xy
        for ch in text:
            d.text((x, y), ch, font=f, fill=fill, anchor="ls")
            x += f.getlength(ch) + spacing

    @lru_cache(None)
    def _card_image(self, oi):
        o = self.overlays[oi]
        fe, ft = font(FONT_MD, 34), font(FONT_XB, 88)
        words = o["text"].split()
        lines, cur = [], []
        for w in words:
            if w == "|":                                # explicit line break: "SAY THIS. | PAY LESS."
                lines.append(cur)
                cur = []
                continue
            if cur and self._width(cur + [w], 88) > 820:
                lines.append(cur)
                cur = []
            cur.append(w)
        lines.append(cur)
        pad_x, pad_y, lh = 44, 38, 100
        eb_w = sum(fe.getlength(c) + 4 for c in o.get("eyebrow", ""))
        tw = max(max(self._width(l, 88) for l in lines), eb_w)
        w = int(tw + 2 * pad_x)
        h = int(pad_y + 34 + 26 + lh * len(lines) - 22 + pad_y)
        bg = CREAM if o.get("plate") == "cream" else INK
        fg = INK if bg == CREAM else WHITE
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=12, fill=bg + (255,))
        self._spaced(d, (pad_x, pad_y + 26), o.get("eyebrow", ""), fe, GRAY + (255,), 4)
        y = pad_y + 34 + 26 + 66
        sp = ft.getlength(" ")
        for line in lines:
            x = pad_x
            for wd in line:
                col = ORANGE if wd == o.get("orange") or (o.get("orange") and o["orange"] in wd) else fg
                d.text((x, y), wd, font=ft, fill=col + (255,), anchor="ls")
                x += ft.getlength(wd) + sp
            y += lh
        return im

    def _title_card(self, canvas, oi, t):
        o = self.overlays[oi]
        im = self._card_image(oi)
        w, h = im.size
        x, y = (W - w) // 2, CARD_TOP
        p_in = ease_out((t - o["t"]) / 0.3)
        p_out = ease_out((o["t_out"] - t) / 0.2)
        p = min(p_in, p_out)
        if p <= 0:
            return
        # masked reveal: a left-to-right wipe, content rising 16 px into place
        lift = int(16 * (1 - p_in))
        show = im.crop((0, 0, max(1, int(w * p)), h))
        canvas.alpha_composite(show, (x, y + lift))
        self._log(oi, (x, y, x + w, y + h))

    @lru_cache(None)
    def _chip_image(self, oi):
        o = self.overlays[oi]
        st = o.get("style", "")
        f = font(FONT_XB, 72)
        bg = CREAM if "cream plate" in st else ORANGE if "orange plate" in st else INK
        fg = CREAM if "cream text" in st else INK if "ink text" in st else WHITE
        m = re.search(r",\s*(\S+) orange", st)
        tok = m.group(1) if m else None
        words = o["text"].split()
        tw = sum(f.getlength(w) for w in words) + f.getlength(" ") * (len(words) - 1)
        l, t, r, b = f.getbbox("ÁG", anchor="ls")
        w, h = int(tw + 52), int(b - t + 28)
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=8, fill=bg + (255,))
        x, y = 26, 14 - t
        for wd in words:
            d.text((x, y), wd, font=f, fill=(ORANGE if tok and wd == tok else fg) + (255,), anchor="ls")
            x += f.getlength(wd) + f.getlength(" ")
        return im

    def _chip(self, canvas, oi, t):
        o = self.overlays[oi]
        im = self._chip_image(oi)
        a_in, a_out = (t - o["t"]) * FPS, (o["t_out"] - t) * FPS
        if a_in < 4:                                   # in: 80 -> 100% while rising, 4 frames
            s, dy = 0.8 + 0.2 * ease_out(a_in / 4), int(12 * (1 - ease_out(a_in / 4)))
        elif a_out < 5:                                # out: to 64% while dropping, 5 frames
            q = 1 - a_out / 5
            s, dy = 1 - 0.36 * q, int(12 * q)
        else:
            s, dy = 1.0, 0
        w, h = im.size
        if s != 1.0:
            im = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
        x, y = int(W / 2 - im.size[0] / 2), int(CHIP_CY - im.size[1] / 2 + dy)
        canvas.alpha_composite(im, (x, y))
        self._log(oi, (int(W / 2 - w / 2), int(CHIP_CY - h / 2), int(W / 2 + w / 2), int(CHIP_CY + h / 2)))

    def _log(self, oi, box):
        o = self.overlays[oi]
        if not any(e["i"] == oi for e in self.layout_log["overlays"]):
            self.layout_log["overlays"].append({"i": oi, "kind": o["kind"], "text": o.get("text"),
                                                "t": o["t"], "t_out": o["t_out"], "bbox": box})

    # ------------------------------------------------------------ frame
    def frame(self, f):
        t = f / FPS
        canvas = Image.new("RGBA", (W, H))
        live = [i for i, o in enumerate(self.overlays) if o["t"] <= t < o["t_out"]]
        orange = any(self.overlays[i]["kind"] == "title_card" or "orange" in self.overlays[i].get("style", "")
                     or self.overlays[i].get("has_orange")
                     for i in live) or any(a <= t < b for a, b in self.orange_spans)
        muted = any(self.overlays[i].get("mute_captions") or self.overlays[i]["kind"] == "card"
                    or self.overlays[i].get("full_bleed") for i in live)
        self._captions(canvas, t, orange, muted)
        for i in (live if self.draw_overlays else []):
            if self.overlays[i]["kind"] == "title_card":
                self._title_card(canvas, i, t)
            elif self.overlays[i]["kind"] == "chip":
                self._chip(canvas, i, t)
        return canvas.tobytes()
