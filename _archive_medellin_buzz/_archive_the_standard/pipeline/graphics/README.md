# Graphics block library (HyperFrames)

CLAUDE.md v3.0 §16b is the source of truth. Each block is one HyperFrames
sub-composition in `compositions/` (HTML + GSAP timeline), 1080×1920 @ 30fps,
copy and media as variables. `build_graphics.py` copies blocks into
`working\<slug>\graphics\`, fills the variables, runs `npx hyperframes check --json`,
and renders.

Rules for every block:
- Monochrome: `tokens.css`, accent white. Emphasis = size / weight / underline.
- Fonts via `@font-face` from `assets/fonts/` (Anton, Playfair Display, IBM Plex Mono — OFL).
- All key text inside y=380–1180 (`--safe-top` / `--safe-bottom`).
- Never a real publication's masthead, an invented headline or quote, or a league/team logo.
- Before hand-building a block, check the HyperFrames registry for a starting point.

Status (2026-10-24): 7 blocks built and used in michael-jordan-02. Blocks are **full-frame** (photo inside the
block, pre-graded with `apply_look.py`); no alpha needed. Anton comes from `assets/fonts/` in the project;
Playfair Display and IBM Plex Mono are bundled with HyperFrames.

| Block | Variables | Default duration | SFX cue | Status |
|---|---|---|---|---|
| `hook_title` | line, highlight | 2.6s | impact | to build |
| `era_banner` | year, place, subtitle | 2.4s | whoosh | built (vars: photo, year, line) |
| `stat_callout` | number, prefix, suffix, label | 2.6s | text_pop + impact | built (vars: a_value, a_label, b_text, b_label, switch_s) |
| `quote_card` | quote, who, source, year | 3.5s | typewriter | to build |
| `newspaper_clipping` | headline, dateline, deck, highlight | 3.0s | film click | built (vars: masthead, dateline, headline, deck) |
| `location_map` | state, city, pin_x, pin_y | 2.8s | tick | built for NC (inline Commons PD map) |
| `timeline_strip` | items[2–5]: date, label | 3.5s | tick per dot | to build |
| `name_card` | name, role | 2.2s | pop | to build |
| `versus_card` | left_label, left_value, right_label, right_value | 3.0s | impact | to build |
| `archival_frame` | src, date_stamp, look | per segment | projector loop | built (vars: photo, stamp, title) — also used as hook_title |
| `photo_push` | src, focus_x, focus_y | 3.0s | — | to build |
| `beat_transition` | style (leak/whip) | 0.4s | whoosh | to build |
| `lesson_card` | line | 3.0s | swell | built (vars: kicker, line) |
| `brand_lockup` | — ("HOLD THE STANDARD.") | 2.0s | impact | built |
