# HyperFrames graphics library (Medellin Buzz Shorts)

The motion-graphics layer of every short since kit v0.4: title cards, chips and data cards, written as HyperFrames
compositions (HTML + GSAP), rendered transparent and laid over the picture by `render_short.py`.
Karaoke captions stay in Pillow (`build_captions.py`): their word timing and QA were tuned on s1/s2.

| File | What |
|---|---|
| `brand.css` | Brand tokens (ink `#1D1D1D`, cream `#F4EFE2`, orange `#D95633`, warm gray `#8C857A`) and `@font-face` for Poppins from `brand\fonts\` |
| `templates/title_card.html` | CLAUDE.md §7. Top y 300, Poppins ExtraBold 88/100, ink or cream plate, one orange word, masked reveal 0.3 s `expo.out` |
| `templates/chip.html` | Alejo's chip look. Centered y 380, ExtraBold 72, ink/cream/orange plate, 80→100 % in 4 frames, out to 64 % in 5 |
| `templates/data_card.html` | Alejo's card system re-laid for 9:16: full-bleed cream or ink, eyebrow, hero number rolling in, label, rule drawing on, source line. Text inside y 168–1330, x ≤ 940 |
| `compositions/components/number-wheel.html` | Registry component (`hyperframes add number-wheel`): the rolling-digit counter |
| `vendor/gsap.min.js` | GSAP 3.14.2, copied into each project so renders never fetch from the network |

## EDL events it draws

```json
{"kind": "title_card", "eyebrow": "EL HUECO · MEDELLÍN", "text": "SAY THIS. | PAY LESS.", "orange": "LESS", "plate": "ink", "t": 0.06, "t_out": 1.7}
{"kind": "chip", "text": "TIP 2 OF 4", "style": "ink plate, 2 orange", "t": 20.41, "t_out": 21.91}
{"kind": "card", "text": "17,000 BUSINESSES", "orange": "17,000", "counter": "rolls 0 -> 17,000",
 "eyebrow": "EL HUECO", "source_line": "Source: La República", "bg": "cream", "t": 3.01, "t_out": 5.73}
```

- `|` forces a title-card line break; otherwise it wraps at 820 px.
- Chip `style`: `ink|cream|orange plate`, optional `cream text|ink text`, and `<token> orange` for the one orange word.
- Card: the first word with a digit is the hero number (rolls if `counter` is set); the rest is the label. A card with no number shows its text as a smaller hero. Captions mute under cards.
- The EDL needs `"graphics_engine": "hyperframes"` (`plan_shorts.py` writes it on new plans). EDLs without it use the old Pillow title card and chips.

## Running it

`render_short.py` runs it as the `graphics` stage. On its own:

```
python pipeline/build_graphics.py working/<slug>/plans/s<N>_edl.json --stage snapshot   # build + check + PNG frames, no video
python pipeline/build_graphics.py working/<slug>/plans/s<N>_edl.json --stage render     # + transparent graphics.mov
```

The project lands in `working\<slug>\render\s<N>\hf\`. Open it in the HyperFrames desktop app to tweak a card by hand; re-running `build` rewrites only the `g<NN>-*.html` scenes, `index.html`, fonts and GSAP, never `.hyperframes\` (history).

`hyperframes check` warnings that are expected for an overlay layer (blank between graphics, no audio, the counter's in-between digits) are filtered out; anything else is printed.

## Adding a block

1. Look in the registry first: `catalog --query "<what it should do>" --json` through the plugin launcher (see `build_graphics.hf_cli()`).
2. Add a template under `templates/` with `{{id}}`, `{{brand_css}}`, `{{dur}}` slots; one orange element; ease-out arrivals 0.3–0.5 s, no bounce/elastic/glitch.
3. Map an EDL `kind` to it in `build_graphics.py` and run `--stage snapshot` on a real plan before any render.

## Custom scenes (`hf_scene`)

Any one-off animation made for a short: a map of the route, a chart, kinetic type, a registry block restyled to the brand.

```json
{"kind": "hf_scene", "src": "working/el-hueco/graphics/route_map.html", "note": "Poblado -> El Hueco route",
 "t": 12.4, "t_out": 15.0, "full_bleed": false, "has_orange": true, "assets": ["working/el-hueco/stills/map.png"]}
```

The file is a normal HyperFrames scene (`<template>`, scene root styled as `#root`-equivalent, one paused timeline registered under the scene id) with `{{id}}` wherever the id goes; it may also use `{{brand_css}}` and `{{dur}}`. Assets are copied into the project's `assets/` (reference them as `assets/<file>`). `full_bleed` mutes captions and skips the QA safe-zone box; `has_orange` tells the captions to keep their plate ink. More flags (kit v0.2, from promo-01): `background: true` marks full-frame artwork (QA skips its box; captions keep the accent plate over a dark band); `orange_from` (seconds) says when its accent element appears; `cues` maps names to spoken words in the draft (`{"upload": "upload"}`) and the scene reads `{{cue_upload}}` (seconds from its start), so its beats follow the A-roll; `beats` lists when its picture changes (seconds, cue names or anchors) so the pacing checks see them. Text in a scene stays on screen 0.5 s + 0.3 s per word: `hyperframes check`'s `line_unread` stops the graphics stage. If it works well, turn it into a template here, or keep its generator in `scenes/`.

| Scene generator | First used | What |
|---|---|---|
| `scenes/towns_map.py` | el-hueco s3 | Cream panel (x 160–920, y 300–1200), "ANTIOQUIA · COLOMBIA" eyebrow, 24 unlabeled dots at town-seat positions around Medellín, gray lines drawing in to one orange EL HUECO dot. `python pipeline/graphics/scenes/towns_map.py working/<slug>/graphics/towns_map.html` |

## Trap: GSAP start values come back when the renderer seeks backwards

HyperFrames renders frames out of order across workers, so a timeline gets seeked backwards. A `fromTo` (or `immediateRender: false`) that starts *visible* later in the scene renders its start state before its start time once it has initialized. In s3, the hub ring meant to pulse at 1.9 s showed as an outline from the first frame. Fix: give a hidden element its hidden state in CSS (`opacity: 0`) and bring it in with `to` tweens, never a `fromTo` whose start value is visible. Check the first frames of every scene in the render, not only the midpoint snapshot.
