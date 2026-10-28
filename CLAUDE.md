# Buzz Media Kit — Editing Engine (v0.2)

**What this is:** the procedure Claude follows to turn a client's phone footage into finished vertical reels (Instagram Reels, YouTube Shorts, TikTok, Facebook) for **Buzz Media**. When Franco asks for a reel for any client, follow this doc.

**Status:** v0.2 (2026-10-27). Forked from the Medellin Buzz Shorts Kit v0.5 (3 approved shorts; everything channel-specific is in `_archive_medellin_buzz\`, see `ARCHIVED.md` there). First Buzz Media reel: **promo-01 "Who edits my videos", approved at v2 (35.9 s)**. Its two render rounds were almost all about audio, flow, pacing and context, not design; v0.2 turns each of those fixes into a check that runs before Franco sees a render (§13). Rules marked `[DRAFT]` haven't been tested on a Buzz Media render.

**Language:** Franco works in English. Chat, reports and generated files in English. On-screen text in the client's language (English unless `_instructions\` says otherwise).

---

## 0. Buzz Media, the agency

- **Buzz Media** (Franco and his brother Andrew) is a video **strategy, production and editing** agency. Tagline: **Strategy. Film. Edit.**
- **Core offer:** "You film on your phone and upload to a shared folder. We write the hooks, edit, caption and send back finished reels within **48 hours**."
- **Clients:** brands, restaurants and companies that need short-form content but don't have time to edit. Plans start at 10 reels/month (see `clients\buzz-media\_instructions\`).
- **This kit serves every current and future client.** Buzz Media is its own first client (`clients\buzz-media\`): the structure is dogfooded from day 1.
- Every reel gets a **human finish**: Franco approves the plan (Gate 1) and the cut (Gate 2). That's the promise behind "10 spots".

---

## 1. Hard rules

1. **Real voices only.** Every word heard is the client (or the person they filmed), from their own footage. No TTS, no AI narration, no voice cloning, no generated "pickup" lines. If a reel needs a line nobody said, it becomes on-screen text or a different clip. Never invent words.
2. **No synthetic people.** No lip-sync fixes, face edits or AI-generated shots of a real person.
3. **Default output** (overridable per client in `_instructions\`, or per project): 1080×1920, 9:16, 30 fps, H.264 yuv420p, AAC 48 kHz stereo, MP4 ready to upload. Target **30–60 s**, floor 15 s. −14 LUFS integrated, true peak ≤ −1 dBTP. A client or project limit (e.g. "30 s max") overrides the default; say which applies in the plan.
4. **Hook rule (hard):** the first 3 seconds must capture attention. One of:
   - a **punchy line** that states the payoff, a number, money, a result or a conflict, and makes sense with zero context;
   - a **loud visual** (strong motion, a reveal, a before/after, a screen of proof) with the hook line landing by 1.5 s;
   - a **title card hook** (§7) over the first shot, on screen from frame 0 while the line starts.
   **Never:** "hey guys", "so", "today I want to talk about", a mid-story opener, a question with no stakes, a logo intro, a slow walk-in.
   If a candidate clip has no 3-second hook, **propose how to construct one from available footage, screenshots or B-roll before cutting**: pull a stronger later line forward, open on the proof visual, or add a title card (§6).
5. **The client's `_instructions\` are law.** Their exclusions, claims they can't make, words they don't use, and anything legal (regulated claims, prices, offers) override this doc. If something in the footage conflicts with them, cut around it or skip it, and flag it in the plan.
6. **No made-up facts on screen.** Numbers, prices, names and dates in cards or chips come from what's said in the clip, the client's `_instructions\`, or an asset they provided (a stats screenshot). Otherwise verify on the web (2 sources, noted in the plan) or leave it off.
7. **Brand:** the client's `_brand\` sets fonts and colors. **Never green highlights** (Opus Clip's look), never Impact, no watermark unless the client's brand asks for one.
8. **Approval gates:** nothing renders before Franco approves the EDL plan (Gate 1, §5). **Ask before running ffmpeg to write any new video file** outside an approved render.

---

## 2. Multi-client architecture

```
E:\FRANCO\BUZZ MEDIA KIT\
  CLAUDE.md                 ← this file (kit-wide)
  .claude\settings.json     ← pins the HyperFrames plugin for this folder
  pipeline\                 ← shared scripts (§12); pipeline\kit.py resolves every path below
  tools\                    ← the kit's own WhisperX + face-tracking venvs and scripts (tools\README.md)
  sfx\                      ← shared SFX library (catalogo_sfx.json + folders, _synth\, _uncatalogued\)
  music\                    ← shared music library (catalogo_musica.json)
  _brand_assets\            ← Buzz Media's OWN brand kit: PDF, brand-notes.md, brand.json (pipeline tokens), fonts\
  _benchmark\               ← studied references: kallaway-analysis.md, kallaway-inspired-rules.md, kallaway\ (scan, sheets), kallaway-reels\ (mp4 gitignored)
  _archive_medellin_buzz\   ← the forked kit's specific pieces, kept for diffing
  _setup\                   ← install notes and setup scripts
  _to_delete\               ← files Franco should delete by hand (gitignored)
  clients\
    <client>\
      _brand\               ← client brand kit + brand-notes.md + brand.json + fonts\ (copies, not symlinks)
      _instructions\        ← client's Word docs, WhatsApp notes, filming notes, voice notes, brief-summary.md, exclusions.json
      sfx\                  ← client SFX (empty → shared)
      music\                ← client music (empty → shared)
      projects\
        <project-slug>\
          raw\              ← the client's footage (gitignored)
          broll\            ← extra footage (gitignored)
          assets\           ← screenshots, profile pictures, logos we're given (gitignored)
          working\          ← transcripts, shots, render parts (gitignored) · working\plans\ is tracked
          output\           ← finished reels + package (gitignored)
```

### Fallback rules (always)

- Client-specific `clients\<client>\sfx\` and `music\` folders take priority when non-empty; otherwise fall back to the shared library at the kit root (`sfx\`, `music\`).
- Client-specific `_brand\` overrides any default styling.
- Every client's `_instructions\` folder is read FIRST before any editing decision for that client — it holds the client's Word doc, WhatsApp notes, filming instructions, voice notes.
- Every project goes under `clients\<client>\projects\<project-slug>\` — never at the kit root.
- Buzz Media itself is treated as a client (`clients\buzz-media\`) — dogfood the structure from day 1.

### New client checklist
1. `clients\<client-slug>\` with `_brand\`, `_instructions\`, `sfx\`, `music\`, `projects\`.
2. Drop their brand kit into `_brand\` and write `_brand\brand-notes.md` (palette, fonts, caption colors, logo rules) in the shape of `_brand_assets\brand-notes.md`. Then `_brand\brand.json` (the values the pipeline reads: `ink`, `cream`, `accent`, `accent_text`, `gray`, `white`; fonts `heavy`/`bold`/`label` with file + weight + family; `caption_case` `upper` or `sentence`) and the font files in `_brand\fonts\` (free fonts only, license file alongside; ask Franco before downloading). No brand kit → ask Franco; meanwhile Buzz Media's `_brand_assets\brand.json` applies.
3. Read everything in `_instructions\`. Write `_instructions\brief-summary.md`: offer, audience, CTA, exclusions, per-reel asks, length limit, open questions. Settle the open questions with Franco one at a time before planning (promo-01: that's how every number on screen got a real source). Always on the list: **length cap vs. full sentences** (if the lines don't fit the cap without cutting inside sentences, which wins? promo-01: full lines at 35.9 s beat a harsh 30 s), and **footage quality** (camera original, 4K or vertical?). Put words the client must never say on air in `_instructions\exclusions.json` (`"patterns"`: regexes; plan and QA scan for them).
4. Each delivery batch is a project: `projects\<slug>\` with `raw\ broll\ assets\ working\ output\`.

---

## 3. 48-hour turnaround

The offer promises finished reels within 48 h of upload. Plan around it:

| From upload | Step |
|---|---|
| 0–2 h | Read `_instructions\`, inventory, transcribe, scene-detect. Report what's missing (footage, assets, unclear asks) **in the first reply**, so the client can fix it the same day. |
| 2–6 h | Hook candidates + EDL plans + graphics mockups → **Gate 1** (Franco). |
| 6–24 h | Render, self-review, QA → **Gate 2** (Franco, phone copy). |
| 24–36 h | One round of notes, re-render only the stages a fix touches. |
| 36–48 h | Package (titles, captions, cover frame) and deliver. Buffer. |

- A single reel from a ready pipeline took ~1–1.5 h of session time on Medellin Buzz (timing logs in `_archive_medellin_buzz\CLAUDE.md` §11). The 48 h is for the human gates and the client's own delays, not for Claude.
- **Goal per reel: v1 approved, or one round of notes.** Plan every rule in before the render (that's what got Medellin Buzz s3 approved with no notes).
- Batch work: plan all reels of a project at one Gate 1; render in priority order; deliver as each passes Gate 2.

---

## 4. Output per reel (`projects\<slug>\output\`)

```
<client>-<project>_<short-title>.mp4   ← final master
<client>-<project>_package.md          ← 3 title options, caption/description per platform, hashtags, cover frame, posting note, licenses
<client>-<project>_edl.json            ← the approved plan, as rendered
<client>-<project>_qa.md               ← QA report + frame grabs
```

---

## 5. Pipeline

Order: **read client `_instructions\` → inventory → transcribe (WhisperX) → scene-detect → identify hook candidates → write EDL plans (hook + body + optional CTA) → GATE 1 (Franco approves) → render with captions + motion graphics (HyperFrames) + SFX + music → self-review → QA → GATE 2 → package.**

### Step 0: Read the client
- Read every file in `clients\<client>\_instructions\` and `_brand\brand-notes.md`. If there's no `brief-summary.md`, write it first.
- Extract per reel: the angle, the exact lines the client wants said, the on-screen text they asked for, the B-roll they asked for, length limit, CTA.

### Step 1: Inventory
- `pipeline\inventory.py --project <p>`: `ffprobe` every file (duration, resolution, fps, orientation, audio). Flags horizontal footage with a narrow 9:16 crop (`narrow_9x16_crop_606px` on 1080p), under 1080p, variable frame rate (phones), missing audio, and `screen_recorder_copy?` (an ffmpeg-based recorder like OBS wrote it: `.mkv`, "Lavf" encoder, a "Track1" audio track, no camera metadata; promo-01's raw was this).
- Writes `working\inventory.json` with an `ask_client` list. **The first reply asks the client for what it lists:** the camera original, 4K or vertical footage, a separate audio file. Plus what's missing.

### Step 2: Transcribe + scene-detect
- **WhisperX** (large-v3 + wav2vec2 alignment, RTX 3060), from the kit's own `tools\` (`tools\README.md`):
  ```
  tools\venv_whisperx\Scripts\python.exe -I tools\transcribir_whisperx.py <project>\raw <project>\working\transcripts
  ```
  Outputs `<clip>.words.json` (word-level `w/s/e/p`) and `<clip>.txt`. Numbers like "$199" are interpolated (`"interpolada": true`): never cut on an interpolated word edge.
- **Scene detection:** `pipeline\scene_detect.py` (threshold 27) on edited sources and B-roll.
- **Takes:** phone footage usually has several takes of each line. Mark the best take of each line (clean delivery, energy, eyes on lens) before planning; the script is the order, the take is the choice.

### Step 3 (when there's a long-form): map long-form → raw
Only when the client gives a finished long video plus its raw: `pipeline\map_longform_raw.py` finds every long-form moment in the raw takes (better takes, what was said around it).

### Step 4: Hook candidates
- Talking-head scripts (most clients): one reel per script; the "candidates" are 2–3 ways to open it. Long or unscripted footage: 3–5 candidate reels.
- Each must be **self-contained**, **one idea**, inside the client's exclusions, and have a **strong first line** (a number, a result, money, a comparison, a conflict).
- Write the hook explicitly: `hook_type` (`line` · `pulled_forward` · `title_card` · `visual`), the exact words in 0–3 s, what's on screen, and how it's constructed if the natural start fails.

### Step 5: EDL plans → GATE 1
Write `working\plans\s<N>_draft.json`, run `pipeline\plan_shorts.py` on it (→ timed `s<N>_edl.json`), and a readable summary. Structure: **hook (0–3 s) → body (proof before the ask) → CTA / ending.** Same schema as Medellin Buzz (example in `_archive_medellin_buzz\CLAUDE.md` §5), plus these fields every Buzz Media EDL carries:

```json
"client": "buzz-media", "project": "promo-01", "slug": "buzz-media-promo-01", "short": "s1",
"project_dir": "clients/buzz-media/projects/promo-01",
"min_s": 15, "max_s": 30,
"caption_base_y": 1360,
"grade": null,
"exclude_patterns": []
```
- `project_dir` is what makes every script find `raw\`, `broll\`, `assets\`, `working\`, `output\`, the client's brand, SFX and music (`pipeline\kit.py`). Each A-roll segment's `"clip"` is a transcript stem (`"promo-01"` for `raw\promo-01.mkv`).
- `min_s`/`max_s`: the reel's length limits from the brief (default 15–60). `caption_base_y`: 1360 full-frame, ~990 on a split-screen seam. `grade`: a `.cube` path, or null for none. `exclude_patterns`: extra regexes on top of the client's `exclusions.json`.
- Optional renderer fields (promo-01): `"layout"` (`full` / `split` / `pip` per time range, with `"punch"`), `"pip"` (the rounded rectangle), `"sfx_track"` (`[{"anchor", "file", "db"}]`), `"music"` (`file`, `in`, `bed_db`, `gap_db`, `fade_out`, `license`), `"caption_layout"` (`split_y`, `full_y`, `mute` ranges), `"caption_emphasis"` (words allowed to stand alone as a caption).
- **Write every time as a word anchor, never as a reel time.** Overlays, layout ranges, SFX hits and caption mutes take `"anchor"` / `"until"`: a spoken word (`"upload"`, `"ready to post"`, `"edit#2"` for the second one), `{"word": "upload", "offset": -0.1}`, `[seg, src_t]`, or `"end"`. A layout item with no end runs to the next one. Inside an `hf_scene`, beats come from `"cues"` (`{"upload": "upload"}` → `{{cue_upload}}` in the scene file, seconds from its start), never typed numbers. promo-01 used reel times: every audio fix meant re-mapping ~30 times by hand.
- **Read `plan_shorts.py`'s Gate 1 checks** (printed, and in the EDL's `"checks"` / `"warnings"`) and fix or explain each one before Gate 1:
  - **numbers:** every number token and the gap after it. That gap is never tightened (WhisperX timed "200" as "two" only; "hundred" sat in the "pause" and got cut). A `suspect` number is timed shorter than it takes to say: listen to it.
  - **cut points:** every cut is snapped to the quietest 10 ms of the source within ±60 ms; a cut still louder than −35 dBFS is a warning (a leaked syllable: "th-" of a dropped "that").
  - **sentences:** a segment starting or ending mid-sentence, a clause dropped from inside a sentence, and the length with those clauses restored.
  - **ending:** the last word and what the speaker says next. A warning if it doesn't end a sentence or the speaker goes on within 0.6 s.
  - **SFX:** ≥ 3 s apart, never on a number or a name being said (the same rules `qa.py` applies after the render).
  - **text on screen:** at least 0.5 s + 0.3 s per word.
  - **pacing:** visual changes count cuts, overlays, layout switches and `hf_scene` `"beats"` (list them: when the scene's picture changes).

**Body rules:**
- **Cut on ideas, not words.** Never mid-sentence. Remove "uh/um", false starts, repeats. Gaps inside a thought 0.10–0.30 s, never right after a number.
- **Cut whole sentences, or pick a tighter take. Don't remove clauses from inside a sentence to save time.** promo-01 v1 cut "or on your camera" and "it to our shared drive" to hit 30 s; Franco: too harsh, context missing. v2 restored the full lines (35.9 s) and was approved. When a length cap would force mid-sentence trims, Gate 1 shows **both options with their exact lengths** (full lines vs. trimmed) and recommends full lines. Context beats the cap unless Franco says otherwise.
- **Pacing:** see the craft rules (§9): a visual change every 1.5–3 s, never more than 4 s of the same framing.
- **B-roll rules** (Franco's notes on Medellin Buzz, now kit-wide):
  1. **They name it → show it.** A place, a product, a channel, a number on a screen: cut to it on the sentence.
  2. **No footage → quick stills or a card.** Wikimedia Commons (CC0, public domain or CC BY only, logged in `working\stills\sources.json`), the client's own screenshots, or a HyperFrames card. Never show a stand-in as the real thing.
  3. **B-roll starts on the first word of its sentence**, not halfway in on the matching word.
  4. **The picture matches the words literally.** Pick from 9:16 contact sheets (`build_contact_sheet.py`, `broll_strips.py`), never from one frame.
  5. **The closing stretch can stay on B-roll**; pick the last in-point so the final frame is strong.
  6. **No chip that repeats a spoken word.** A graphic adds what the caption doesn't (a counter, a source, a before/after).
  7. **No still that's only roughly right.** Stay on the speaker with a punch-in instead.
  8. **Reusing a clip across reels of the same client is OK;** flag it so they post on different days.
- **Creative-license clause (B-roll substitution).** When the instructions call for footage the client didn't provide (e.g. "shot of me and Alejo working at a computer"), **substitute creatively instead of refusing to proceed**: profile pictures, channel screenshots, screen recordings, animated text cards, HyperFrames motion graphics (a name card, a counter over a screenshot, a scrolling wall of thumbnails). **Propose every substitution in the EDL plan for Franco's approval before rendering**, saying what was asked, what we use instead and why. A substitution never pretends to be the real thing (a profile picture is shown as a profile picture, not as a "working" shot).
- **Endings close the thought.** Read 20–30 s of transcript past the planned out-point (`plan_shorts.py` prints the next words). A line with a "but…" coming isn't an ending, and neither is a comma: promo-01 v1 ended on "comment EDIT below," and Andrew went on "…and I'll send you all the information in a DM." **The CTA line keeps its tail.** Default end hold 0.6 s, music fade-out 1.0 s. Personal last line → end on the face; place/product → end on B-roll.
- **CTA:** only the client's own CTA (from their line or `_instructions\`), **one per reel**, said and shown. On-screen CTA text matches the brief exactly ("Comment EDIT"). No invented "link in bio".
- **HyperFrames graphics pass (every reel).** Go through the script line by line and decide where a card, counter, chart, map, kinetic phrase or transition makes it clearer. Simplest first: library (title card, chip, data card with rolling counter) → HyperFrames registry block (search before hand-building) → a one-off `hf_scene`. Restraint: a graphic never covers the speaker's face or repeats the caption; one accent-color element at a time; "no graphic here" is a valid decision. Gate 1 shows each graphic (time, what, engine piece) and a still mockup for anything new (`build_graphics.py --stage snapshot`, `graphics_mockup.py`).

**→ GATE 1: Franco sees** a table per reel (hook words, hook type, length, why it works, risks, exclusion notes, **substitutions**, **planned graphics**, **music + SFX plan** with the SFX check result, **the number tokens and the ending** as `plan_shorts.py` printed them, and **both length options** when the cap forces trims) + one EDL each. Nothing renders before his OK.

### Step 6: Render (after Gate 1)
- **Reframe 16:9 → 9:16** around the face (`face_track.py`, run with `tools\venv_render\Scripts\python.exe -I`), eyes at ~35–40 % from the top. Any source size works. Vertical footage as-is. No blurred-background letterboxing.
- **1080p landscape sources** (Buzz Media's desk footage): a full-height 9:16 crop is 606×1080 scaled up 1.78×, so keep punch-ins ≤ 1.08 and prefer the split-screen layout for the speaker (it needs a wider, sharper crop). Ask clients for 4K or vertical footage.
- **Grade:** consistent across takes. Phone footage: a gentle correction only (exposure, white balance, mild contrast). `match_grade.py` when there's a finished reference to match.
- **Captions** (§7). **Motion graphics** = HyperFrames (§7, `pipeline\graphics\README.md`). **Sound** (§8).
- **Render order: words before graphics.** `render_short.py --stage all` runs picture → audio → captions (WhisperX on the final voice) → **words**: it diffs that transcript against the approved lines and repeats the plan's number/ending warnings, and **stops** unless they match exactly. The graphics render is the slow part (~3 min, ~1 GB), and the re-transcription is what caught promo-01's cut number, leaked syllable and open ending. Fix the plan, or listen, decide it's transcription noise and continue with `--stage rest` (graphics + final).
- **Long stages run in the background** (`run_in_background`), never in a blocking shell: the graphics stage, `--stage all`, and `qa.py` (WhisperX again). A ten-minute render was cut short by a blocking shell on promo-01. Run `qa.py` once per render.
- **HyperFrames check:** a `line_unread` warning (text on screen too short to read) now stops the graphics stage. Hold the text 0.5 s + 0.3 s per word; only if Franco accepts a fast flash, list its text in the EDL's `"unread_ok"`.
- **Self-review before sending v1** (frame at every picture change, look at all of them; on promo-01 this caught a one-word caption and a too-short tag): everything named has its picture; B-roll on sentence starts and literal; no chip repeats a word; captions in the safe zone and off the mouth; stills not badly cropped; the hook works with sound off; the last frame is strong; the ending closes; caption text matches the speech (caption traps below); every substitution is the approved one; SFX land on the planned frames.
- **Caption text traps** (fix in the EDL with `caption_fixes`, `caption_join`, `caption_break_before`, never by hand): currency symbols on non-dollar amounts; dropped words (`"of@51.48": "of the"`); spoken numbers shown as digits ("a hundred" → `100`: show the words; digits are for prices and figures); foreign phrases split or missing ¿?; payoff phrases split across groups; a single word left alone (`build_captions.py` now joins a lone number to the next word and a lone word to its neighbour when it fits; what's left is listed in the QA notes; `"caption_emphasis"` keeps a planned single word).
- The ending hold is picture only (voice stops at the last word, 60 ms fade).

### Step 7: QA (`pipeline\qa.py`)
Spec (size, fps, length vs. the reel's limit, −14 ±1 LUFS, TP ≤ −1 dBTP) · first word or title card by 1.0 s · hook words match the EDL · WhisperX re-transcription contains only approved lines and no client-excluded words · no mid-word cuts · **every splice in a dip** of the source audio (≤ −35 dBFS) · captions in the safe zone, ≤ 4 words, timing median ≤ 30 ms · graphics in the safe zone (full-bleed cards and `"background": true` scenes skipped) · visual change ≤ 5 s (counting layout switches and scene `"beats"`) · SFX spacing and not on a number · no black/flash at splices · no shot under 0.4 s unless intended · 8 frame grabs in `_qa.md`. `--out <dir>` writes the report somewhere else (re-checking an approved reel without overwriting its report). **A false failure is a bug in the kit:** fix the check or the EDL flag, don't train everyone to ignore QA.

### Step 8: GATE 2 + package
Send the master **and** a phone copy (`working\review\<…>_v<k>_phone.mp4`, H.264 4 Mb/s, AAC 160k, `+faststart`; Remote Control can't send files over 30 MB). After approval write `_package.md`: 3 titles (≤50 chars, client's voice), caption per platform (Reels / Shorts / TikTok / Facebook) with 3–5 hashtags (never #fyp, #viral), cover frame time + why, posting note (spread out; 3+ the same day costs reach), music/SFX license lines, CC BY credits.

---

## 6. Hook construction toolbox

In order of preference:
1. **The natural first line**, if it passes §1.4.
2. **Pull forward:** the strongest line (the number, the result, the comparison) plays first as a 1–3 s cold open; not repeated later in full.
3. **Better take:** the same line said punchier in another take.
4. **Proof first:** open on the most striking visual of the proof (a stats screen, a before/after, a fast scroll of work) with the line already under it.
5. **Title card** over the first shot (§7) when the line needs a frame to land in silent autoplay.

**Triple alignment:** the spoken hook, the on-screen text and the picture point at the same single idea, without the text repeating the same words. **Silent-autoplay check:** sound off, do the first 2 seconds still stop a thumb?

---

## 7. Captions, title cards, graphics

**Caption spec (deliberately not Opus Clip):**
- **Colors from the client's brand palette** (`_brand\brand-notes.md`). Highlight color is the client's accent, **never green**.
- **Karaoke, word by word**, timed from WhisperX words of the **final** audio.
- **3–4 words on screen max**, one line preferred, two at most.
- **Bold** (the brand's heavy weight) **with a text shadow** (soft drop shadow, plus a thin dark outline on busy footage) so it reads on any picture.
- **Phone-safe zone:** inside y 260–1440 and x 140–940. Default baseline **y 1360** (top of the lower third, below the chin in a talking-head crop); in a split-screen layout, on the seam (y ≈ 960, §9). Never lower than y 1440: the apps' username/caption layer covers it (where Opus puts its captions).
- Active word: accent-colored text, or an accent plate with dark text. While another accent graphic is on screen, the active word drops to white/plate so only one accent element shows (an `hf_scene`'s `"orange_from"` says when its accent appears). **Readability beats that rule over busy artwork:** while an `hf_scene` with `"background": true` (full-frame artwork) is up, the captions keep the accent plate and a dark band sits behind them (Franco's note on promo-01 0–4 s).
- **Where the look comes from:** `build_captions.py` and `build_graphics.py` read the client's `_brand\brand.json` (falling back to `_brand_assets\brand.json`). In EDLs and in the code, `"orange"` means **the brand's accent color** (a leftover name from Medellin Buzz): `"orange": "200+"` paints that word in Buzz Yellow, `"style": "orange plate"` is an accent plate with `accent_text` lettering.
- **Buzz Media's own reels:** Schibsted Grotesk ExtraBold, white, sentence case, Buzz Yellow `#FFC629` active-word plate with ink text (see `_brand_assets\brand-notes.md` §4). Fonts in `_brand_assets\fonts\` (OFL). Title cards and chips print the EDL's text as written: write them in sentence case for Buzz Media (brand rule), uppercase only for brands that use it.

**Title card** `[DRAFT]`: a text layer over the first shot from frame 0 (not a separate intro), 2–6 words, the key word in the accent color, y ≈ 300–600 (clear of the face and the captions). In: masked reveal 0.2–0.3 s ease-out with a hit SFX. Out: hard cut on the next shot, or 0.2 s. Says something the spoken line doesn't.

**Motion graphics = HyperFrames.** Library in `pipeline\graphics\` (title card, chip, data card + rolling counter, `hf_scene` for one-offs), rendered transparent and stacked picture → graphics → captions. Motion: ease-out 0.2–0.5 s; no bounce/elastic/glitch unless the client's brand calls for it. Install and gotchas: `_setup\hyperframes-install-notes.md`. Use the `/hyperframes:hyperframes` skill before writing any new scene.

---

## 8. Audio

- **Voice first.** High-pass 80 Hz, gentle de-noise (phone/room audio), light compression 2:1, consistent level across takes.
- **Music bed:** usually yes for promo/business reels, low (−22 to −26 dB under voice, can rise in gaps), ducked under speech. Pick tempo and mood to the script; cuts can land on its beats (§9). **License note required, and it must cover every platform the reel goes to.** Most tracks in `music\catalogo_musica.json` are YouTube Audio Library: cleared for YouTube, **not guaranteed for Instagram/TikTok/Facebook**; check the license field or add music in-app.
- **SFX library:** client `sfx\` if non-empty, else shared `sfx\`: catalogued folders (`catalogo_sfx.json`: Mixkit / Pixabay licenses), `_synth\` (synthesized, no license issue). `_uncatalogued\` holds 16 Pixabay-style files with no license logged yet: **don't use until they're added to the catalog** (2 of them duplicate catalog entries). New outside sources need Franco's OK.
- **SFX use:** see the craft rules (§9) for placement. Never on top of a number or name being said.
- **Master:** −14 LUFS integrated, true peak ≤ −1 dBTP after AAC.

---

## 9. Kallaway-inspired craft rules

Andrew set Kallaway as the quality bar for cuts, beat-syncing and SFX. The study is in `_benchmark\kallaway-analysis.md`; the rules we adopt (inspired, never copied) are in `_benchmark\kallaway-inspired-rules.md`. **Re-read that file before writing any EDL.** Summary:

- **Hook:** first word by 0.15 s, ~8–10 words in 3 s, claim then twist within 5 s; a 2-line hook headline from frame 0 (white + accent line, ink plate) that labels the stake without repeating the words; proof on screen inside 2 s; first picture change by 1.2 s.
- **Cadence:** a picture change every 1.5–2 s (1.2–1.5 s in the first 10 s); no shot over 4 s (screen demos 6 s, with motion inside); changes go on sentence/clause starts and emphasis words; voice cut tight (40–120 ms inside a sentence, breaths out), jump cuts hidden by layout switches or 5–8 % punch-ins. Never speed up a voice.
- **Layouts:** split screen (proof top, speaker bottom) is the default for talking heads; rotate at least 3 layouts (split · full-frame face · full-frame B-roll · card on ink with a circle picture-in-picture · stacked comparison cards); full-frame face on the line that carries the point; credit third-party footage on screen.
- **Captions:** on the seam in split screen, at y 1360 full-frame; 1–3 words usually, 4 max; quiet in split screen; one big accent-colored emphasis word on the face shots, max one per ~8 s; data reveals sit on the picture.
- **Structure:** hook + twist → proof → (re-hook if the client says one) → offer/takeaway → CTA. One analogy gets its own picture. Lists build item by item.
- **Endings:** no outro or logo sting; keyword CTA said and shown on the brand end card; no CTA → end on the takeaway, last word large.
- **Sound** `[EAR]`: SFX as accents (headline hit, whoosh into full-frame/cards, counter ticks, pop on the big word), ~1 per 3–4 s, never every cut; music bed −24 to −28 dB, 100–130 bpm, from frame 0; big moments (headline, layout switches, emphasis words) nudged ≤ 2 frames onto downbeats, routine swaps follow speech.
- **Not copied:** his fonts, red/yellow plate, set, catchphrases, 85 s length, script formula.

---

## 10. Working with Franco

- English, plain words, checklists for steps. Franco is new to Claude Code.
- Ask before installing anything, creating accounts, using a new music/SFX source, any paid source, or downloading files.
- Accounts: Franco's only.
- **The kit is self-contained.** Its tools live in `tools\` (copied from Alejo's kit 2026-10-27, Franco: "no borrowing"). Never point a script at Alejo's kit (`E:\FRANCO\MEDELLIN_BUZZ CLAUDE KIT\`), and never write into it.
- **This kit is the engine, not a project.** A session that builds or changes the kit doesn't edit, cut or render client footage. Reels are made in their own sessions, one project at a time.
- **Never delete files.** Move what should go into `_to_delete\` with a line in its README; Franco deletes by hand.
- Git: `origin` = `https://github.com/OldManFranco/BUZZ-MEDIA-KIT` (private). The repo is **the kit only**: `clients\` is never committed (gitignored; Franco, 2026-10-27), and neither are footage, renders, audio or venvs. Commit only when Franco asks; work on a branch, merge into `main`, push. Never create a new remote without asking. The pre-GitHub local history (it had client files) is kept on the local-only branch `local-history-with-clients`: never push it.
- Don't get stuck: if a path blocks, find another legitimate route. Never bypass CAPTCHAs or log into anything for downloads.

---

## 11. Benchmark

- `_benchmark\kallaway-analysis.md`: 15 most recent Kallaway YouTube Shorts (Sep 11 – Oct 19, 2026): hooks, cut cadence, beat sync, SFX, captions, cards, pacing, endings. Raw numbers in `_benchmark\kallaway\scan.json`, keyframe sheets in `_benchmark\kallaway\sheets\`, transcripts in `_benchmark\kallaway-transcripts\`.
- `_benchmark\kallaway-inspired-rules.md`: what we adopt.
- Instagram reels: yt-dlp's Instagram extractor is broken without a login (2026-10-27). Franco downloads by hand into `_benchmark\kallaway-reels\` if needed.
- The Medellin Buzz Opus Clip study is in `_archive_medellin_buzz\_benchmark\` (what the "Opus look" is, and why we avoid it).

---

## 12. `pipeline\` status

✅ tested on a Buzz Media render · 🟢 adapted and checked without rendering video · ⚪ benchmark/helper

Every script now gets its paths from `pipeline\kit.py` (project folder from the EDL's `project_dir` or a `--project` argument; client brand, SFX/music fallbacks, exclusions, length limits; the kit's own `tools\`). Archived Medellin Buzz EDLs (no `project_dir`) still resolve to the old `input\ working\ output\` layout. **No script has rendered a Buzz Media video yet:** the first reel session is the first real run, so check each stage's output as it lands.

What was checked 2026-10-27 without writing any video: both venvs run from `tools\` (CUDA on; a 66 s clip transcribed in 7 s; `cara.Medidor` loads), caption frames render in the Buzz Media brand at y 1360 and y 990, a HyperFrames snapshot of a title card, an accent chip and a data card with counter in the Buzz Media brand (`check`: 0 errors), crop math for 1080p and 4K sources, SFX and brand fallbacks, inventory on a test project, every script compiles.

| Script | Status | Does |
|---|---|---|
| `kit.py` | 🟢 new | Paths, brand, SFX/music fallback, exclusions, length limits, tool locations |
| `inventory.py --project <p>` | 🟢 | Step 1 → `<p>\working\inventory.json` (videos + stills); narrow-crop and screen-recorder flags, `ask_client` list for the first reply |
| `tools\transcribir_whisperx.py` | 🟢 | Step 2, WhisperX (`tools\README.md`) |
| `scene_detect.py` | ✅ (Medellin Buzz) | Shots → `shots.json` |
| `map_longform_raw.py --project <p>` | 🟢 | Step 3, only when there's a long-form |
| `plan_shorts.py <draft>` | ✅ (promo-01) | Steps 4–5: draft → timed EDL; gaps > 0.30 s tightened to 0.15 s (draft `gap_max`/`gap_new`) except after numbers; cuts snapped to the quietest 10 ms; word anchors for overlays, layout, SFX, caption mutes, scene cues and beats; Gate 1 checks (numbers, cut levels, mid-sentence trims + full-line length, ending, SFX rules, text read time, pacing, exclusions, length) |
| `face_track.py <edl>` | 🟢 | Eye position per A-roll piece (run with `tools\venv_render`) |
| `match_grade.py --project <p>` | 🟢 | Long-form-matched `.cube` (only with a long-form) |
| `render_short.py <edl>` | ✅ (promo-01) | Picture (any source size; `layout` full/split/pip, `pip`; optional grade) → audio (SFX by short name or library path, client `sfx\` first; `sfx_track`; `music` bed ducked under speech, 1.0 s fade) → captions (kit WhisperX) → **words** (stops on a diff) → graphics → final MP4 in `<p>\output\` |
| `build_captions.py` | ✅ (promo-01) | Karaoke layer in the client's brand; `caption_layout` (baseline per layout, mutes), `orange_from`; no lone numbers or words; accent plate + dark band over `background` scenes |
| `build_graphics.py` + `graphics\` | ✅ (promo-01) | HyperFrames layer from `brand.json`; scene `{{cue_<name>}}` from `cue_times`; `line_unread` stops the stage (`unread_ok` to accept) |
| `qa.py` | ✅ (promo-01) | Step 7: + splice-in-a-dip check, `background` scenes skipped in the safe zone, beats and layout switches in the pacing check, `--out` |
| `broll_strips.py`, `graphics_mockup.py`, `build_contact_sheet.py` | 🟢 | Take explicit paths; unchanged apart from docs |
| `benchmark_scan.py`, `beat_sync_scan.py` | ⚪ | Benchmark analysis (used on Kallaway) |
| `graphics\scenes\towns_map.py` | ⚪ | El Hueco map; kept as an `hf_scene` generator example |

promo-01 s1 (2026-10-27) was the first Buzz Media render; the scripts marked ✅ ran on it, and the v0.2 checks were tested on its EDL and its approved v2 file without writing any video (§13). Still known gaps: stacked cards and a big emphasis word aren't renderer features yet (promo-01 drew them as `hf_scene`s). Build them as `hf_scene`s or renderer options when the first reel needs them, and add them to `pipeline\graphics\`. The data-card counter spaces the comma wide on 6-character numbers (`20,000`): check the snapshot. HyperFrames needs short paths (Windows 260-character limit): keep projects under `clients\`.

Python 3.12 (system) has PySceneDetect, OpenCV, Pillow, librosa 1.0. ffmpeg 9.0.2 on PATH. HyperFrames 0.8.186 plugin (`_setup\hyperframes-install-notes.md`). yt-dlp: `pipeline\bin\yt-dlp.exe` (gitignored). Buzz Media fonts: `_brand_assets\fonts\` (Schibsted Grotesk variable 400–900, IBM Plex Mono 400/500/600/700, OFL licenses alongside).

---

## 13. Version history

- **v0.2 (2026-10-27):** lessons from promo-01 (approved at v2, 35.9 s), so the next reel needs fewer rounds. Fixed in the process, not the design:
  - `plan_shorts.py`: never tightens the gap after a number (the cut "200"), snaps every cut to the quietest 10 ms and warns on loud cuts (leaked syllables), flags mid-sentence trims with the full-line length, ending checks, SFX rules at plan time, text read time, word anchors for everything timed (`anchor`/`until` on layout, `sfx_track`, caption mutes; scene `cues` and `beats`).
  - `render_short.py`: the `words` stage stops `--stage all` before the slow graphics render unless the re-transcription matches; `--stage rest`; music fade-out 1.0 s. Kept from the promo-01 session: `layout`, `pip`, `sfx_track`, `music`.
  - `build_captions.py`: no lone numbers or words; accent plate + dark band over `background` scenes. Kept: `caption_layout`, `orange_from`.
  - `build_graphics.py`: scene cues, `line_unread` stops the stage.
  - `qa.py`: splice-in-a-dip check; no more false failures on full-frame scenes and scene-internal changes; `--out`.
  - `inventory.py`: narrow-crop and screen-recorder flags and the `ask_client` list.
  - CLAUDE.md: cut whole sentences (both length options at Gate 1), the CTA keeps its tail, word anchors only, words before graphics, long stages in the background, "length cap vs. full sentences" on the brief checklist.
  - Checked without rendering video: `plan_shorts.py` on copies of promo-01's draft (and a v1-like variant: it flags the cut "200", the leaked syllable, the open ending, the mid-sentence trims and an SFX on "20,000"), the words stage on the v2 transcript, a graphics snapshot, `qa.py` on the approved `promo-01-v2.mp4` (report in a scratch folder), inventory on promo-01.
- **v0.1 (2026-10-27):** forked from Medellin Buzz Shorts Kit v0.5 for the Buzz Media agency. Multi-client layout (`clients\<client>\projects\<project>\`) with fallback rules; Buzz Media as client #1 with its 3 launch promos briefed (`clients\buzz-media\_instructions\brief-summary.md`); Medellin Buzz specifics archived (channel exclusions, Andrew-only voice → "real voices only", Medellin palette, Alejo's footage); shared `sfx\` and `music\` at the root; HyperFrames plugin pinned at project scope; Kallaway benchmark and craft rules; creative-license clause for B-roll substitution; 48-hour planning cadence; caption spec from the client's palette. Then, same day: the kit got its own `tools\` (WhisperX + face-tracking venvs, full copies from Alejo's kit), the Buzz Media fonts, `brand.json` per client, and every pipeline script moved onto `pipeline\kit.py` (project paths, client brand, SFX/music fallbacks, exclusions, length limits). Checked without rendering video; no Buzz Media reel rendered yet.
