# Medellin Buzz — Brand Notes for Shorts (v0.1)

Sources read on 2026-10-27:
- `_brand/Medellin_Buzz_Brand_Kit.pdf` (Brand Kit 2026, 9 pages; it was sitting in this folder's root)
- Alejo's editing bible: `E:\FRANCO\MEDELLIN_BUZZ CLAUDE KIT\CLAUDE\MEDELLIN_BUZZ_EDITORIAL_AND_EDITING_BIBLE.md` §10 (text/graphics), §12.2 (SFX), §14 (branding), §16 (thumbnails), §18 (Shorts)
- Alejo's renderers: `CLAUDE\tools\render\placas.py` (chips + lower thirds), `cards.py` / `graficos.py` (data cards)
- The approved data-card reference: `CLAUDE\activos\referencias\Medellin Buzz Data Cards.mp4` (142.8 s, 1920×1080, sampled every 8 s)
- The official end banner: `CLAUDE\activos\marca\Medellin Buzz Official Banner.png` + `banner_oficial.json`

---

## 0. Two palettes exist. Read this first.

The 2026 Brand Kit PDF and the long-form videos do **not** use the same hex values.

| Role | Brand Kit PDF (print, decks, social) | Long-form video system (Alejo's bible §14.3, `[ABSOLUTE]`) |
|---|---|---|
| Dark | Ink `#111111` | Near-black `#1D1D1D` |
| Light | Sand `#FBF8F4` · Paper `#FFFFFF` | Cream `#F4EFE2` |
| Accent | Terracotta `#C1502E` | Burnt orange `#D95633` |
| Accent, dark | Terracotta Dark `#8F3A1F` | n/a |
| Quiet accent | Antique Brass `#9C7A46` | n/a |
| Secondary text | Warm Gray `#6B6660` | Warm gray `#8C857A` |

They are visibly the same family (warm neutrals + one clay-orange accent). The brand kit itself says on-screen video text is a *separate convention* from the print system.

**Decision for shorts: use the video-system values** (`#1D1D1D`, `#F4EFE2`, `#D95633`, `#8C857A`). The goal is "looks like the long-form", and the long-form ships with these. `#D95633` is also a touch brighter than `#C1502E`, which helps on phone screens over footage.
**Approved by Franco, 2026-10-27.** If Andrew/Alejo ever move everything to the Brand Kit hexes, it's a 4-value swap in `brand.json` (to be written next session), not a redesign.

Another contradiction to flag: page 8 of the Brand Kit says on-screen video text (lower thirds, title cards) "stays Impact per the editing brief". Alejo's bible, which is what the videos actually use, says Poppins ExtraBold `[ABSOLUTE]`, and no Impact font exists in his kit. **Shorts follow the bible (Poppins).** Impact would read as generic meme-text, which is the opposite of the brand's "premium, editorial" positioning.

---

## 1. Fonts in use

All live in `brand\fonts\` (symlink to `CLAUDE\tools\fonts\`, see `_setup\create_brand_symlink.ps1`).

| File | Used for in long-form | Shorts use |
|---|---|---|
| `Poppins-ExtraBold.ttf` | Chips/texts (54 px @1080p), card titles, numbers, labels, lower-third name line, thumbnail text | **Captions**, title card hook text, chips, numbers |
| `Poppins-SemiBold.ttf` | Lower-third secondary line (30 px), "CONCEPT RENDER" label | Lower-third secondary line, small labels |
| `Poppins-Medium.ttf` | Small text on cards, source footers | Eyebrows on title cards (tracked +2), source lines |
| `Lora-Italic.ttf` | Editorial interpretation, quotes only ("italic = interpretation, upright bold = fact") | Pull-quote card only, rare |
| `PlayfairDisplay-VF.ttf` | Present in the folder, not referenced in the bible | Not used |

Licenses: `OFL-Poppins.txt`, `OFL-PlayfairDisplay.txt` sit next to the fonts. All OFL, fine to embed in renders.

**Missing from Alejo's folder** (needed only for the logo wordmark, never for in-video text): Lora SemiBold (upright, the "medellin" wordmark) and Lato (Brand Kit body copy). We don't rebuild the wordmark anyway; we use the approved banner PNG as-is.

---

## 2. Colors (shorts, hex)

| Token | Hex | Where |
|---|---|---|
| `ink` | `#1D1D1D` | Title-card backgrounds, plate backgrounds, caption outline |
| `cream` | `#F4EFE2` | Light card backgrounds, text on ink |
| `orange` | `#D95633` | **The one accent.** Caption active-word plate, the key number, BUZZ. Max one orange element on screen at a time |
| `warm_gray` | `#8C857A` | Eyebrows, source lines |
| `white` | `#FFFFFF` | Caption text, plate text |

Proportion rule from the Brand Kit: ~60% neutral, ~30% ink, ~10% accent, never more. In video that means orange marks exactly one thing at a time (bible §10.4).

Never: green (Opus Clip's default and Medellín Living's reel price color `#39E650`), yellow, navy-and-gold, gradients, neon.

---

## 3. How Alejo uses the brand in long-form

**Text chips (zone A)** — `placas.py`
- 1–3 words, English, UPPERCASE, Poppins ExtraBold 54 px @1080p.
- Rounded plate (radius ~6 px @1080p, padding ~18×6 px). Three styles: ink plate + white text, orange plate + white text, cream plate + ink text.
- Enumerations as chips "#1 NO TITLE INSURANCE" with the `#1` in orange on an ink plate.
- Enters on the exact word it echoes, holds 3–5 s. Rapid sequences replace each other by hard cut.
- Animation (Video 1 final): in = scale 80→100% while rising, 4 frames; out = scale to 64% while dropping, 5 frames. Every text carries an SFX on the same playhead.

**Lower thirds (zone B)**
- Orange bar on top (secondary line, Poppins SemiBold 30 px, uppercase, white) stacked on an ink bar (name, Poppins ExtraBold 38 px, uppercase, white).
- Only for people and services. Names only when the spelling is confirmed.

**Data cards** (`cards.py`, reference MP4)
- Full-bleed, no frame. Alternates ink `#1D1D1D` and cream `#F4EFE2` backgrounds.
- Tiny tracked eyebrow in warm gray ("REAL ESTATE COMMISSION · COLOMBIA"), big Poppins ExtraBold title or hero number, thin rules, check-list rows, timelines with dots.
- Exactly one orange element per card (the argument: the number, the last checklist row, the conclusion).
- Motion: masked reveals, rolling counters, lines that draw on, clean wipes. Expo/quint ease-out, 0.3–0.5 s per move; entrance 0.4–0.6 s, exit 0.3–0.4 s. **No bounce, elastic, spin, glitch, confetti, 3D.**
- Every fact verified, source line at the bottom.

**Intro/outro**
- No branded intro card in long-form (cold open on Andrew).
- Outro: the approved Official Banner (ink background, white serif "medellin" + orange tracked "BUZZ", tagline "Helping foreigners relocate & buy property in Medellin.") for 20 s. Never redrawn, cropped or recolored (§14.1). It's 1672×940 (16:9), so in a 9:16 short it would be a small band. For shorts we don't use the 20 s banner (see §5).

**SFX map** (bible §12.2): chips → whoosh −9 dB, plain texts → pop −10 dB, big reveals → cinematic hit −7 dB, lower thirds → swoosh −10 dB, counters → tick, risers ending on the hit (≤6 per long video).

**Look:** warm grade (LUT candidate `CLAUDE\tools\luts\mb_look_video1_candidato.cube`), vignette on Andrew only, never on graphics.

---

## 4. Caption spec for shorts (deliberately NOT Opus Clip)

Font decision: **Poppins ExtraBold**. It *is* the brand's video font, it's a geometric sans that stays legible at small sizes, and it matches every chip and card in the long-form. No separate display font needed. **Approved by Franco, 2026-10-27**, together with the orange active-word plate below.

| Property | Value @1080×1920 |
|---|---|
| Font | Poppins ExtraBold, UPPERCASE |
| Size | 86 px base (≈ 54 px chips × 1.6 for a phone-first frame). Long single words scale down to fit 900 px |
| Words on screen | 2–4 per group, max ~900 px wide, break on punctuation and on gaps > 0.3 s |
| Base text | White `#FFFFFF`, 6 px ink `#1D1D1D` outline + soft shadow (blur ~8, 40% ink, offset 0/4) |
| Karaoke highlight | **Active word sits on an orange `#D95633` rounded plate** (radius 10, padding 14×4) with white text. This is the long-form chip style applied word-by-word, so it reads as Medellin Buzz, not as a caption template. Opus Clip's default is a green *text color* change; ours is a brand plate |
| Highlight motion | Plate slides from word to word (80 ms ease-out), active word scales 100→108%. No bounce |
| Group in/out | In: 80→100% scale over 4 frames (same as Alejo's chips). Out: hard cut to the next group |
| Position | Centered x = 540, baseline y ≈ 1360 (top of the lower third; moved down from 1250 by Franco, 2026-10-27, after el-hueco s1: at 1250 the captions sat on Andrew's chin on punch-ins. Not lower: below 1440 the apps' username/description layer covers them). Safe zone: nothing below y = 1440 (Shorts/Reels/TikTok caption + buttons) or right of x = 940 (IG/TikTok icon column); nothing above y = 260 |
| Over Andrew's face | Captions never cover the mouth. If a reframe puts the chin below y = 1150, move the group up to y ≈ 1000 for that shot only (logged in the EDL) |
| Emphasis | Numbers, money and place names get their own group and +10% size. They do not get a second orange plate: one orange element at a time |
| Mutes | Captions mute while a title card or data card shows the same words |

Alternative if the plate looks too heavy in testing: active word turns `#D95633` text with a thicker ink outline. Decide after the first render.

---

## 5. Brand elements in a short

- **Second 0–1 title card (optional, per short):** ink `#1D1D1D` plate band or full frame, the hook claim in Poppins ExtraBold, one word/number in orange, warm-gray tracked eyebrow ("MEDELLÍN · 2026"). Only when the spoken hook needs help (see `_benchmark/beat-opus-clip.md`).
- **Chips:** same as long-form (1–3 words, uppercase, plate, SFX on the playhead), positioned y ≈ 500–900 so they never fight the captions.
- **Data cards:** 9:16 re-layout of the long-form card system. Same palette, same motion rules, one orange element.
- **End:** no banner and no branded end card (Franco, 2026-10-27). Shorts end on the payoff line plus a short hold, or loop back to the first frame. Revisit only if Andrew asks for a branded ending.
- **Logo/icon:** don't overlay the terracotta-tiles icon or the wordmark on footage. The Brand Kit only allows them on Ink, Paper or Sand fields.
- **Watermark:** none. The platform shows the channel handle. (The Standard's watermark rule was archived.)
