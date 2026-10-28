# The Standard — TikTok Automation (v3.0, athlete micro-documentaries)

**Purpose:** The complete, executable procedure for producing a The Standard TikTok. **Every video is a ~90s micro-documentary: Declan Sage narrates a specific, lesser-known, verified true story about an athlete; the athlete's real voice lands once, at the climax; the lesson closes on the brand.** When Franco asks for a new The Standard video, follow this doc exactly.

**Supersedes:** v2.4 and everything earlier. Where this disagrees with earlier docs, **this doc wins.** Rollback anchor: git tag `v2.4` (github.com/OldManFranco/the-standard-kit).

**Channel:** @thestandard.daily · Tagline and brand line: *Hold the standard.*

**Language:** Franco works in English. All chat replies, status reports, briefs, QA output, and generated files are in English. Pipeline scripts and technical terminology stay as they are.

---

## What changed from v2.4 (read this first)

| Area | v2.4 | v3.0 |
|---|---|---|
| Format | ~4s AI hook + ~55s motivational speech | ~90s story: ~65–70s Declan Sage narration + 12–20s real speech at the climax |
| Hook | 5 rotating patterns (question / statement) | **Hook rule:** proper noun + specific detail (number, place, date, situation) in the first 2s. 3 text variants; any that fail the rule are rejected |
| Story | Franco provides the speech; Claude picks thoughts | Claude researches the angle, verifies every testable claim across ≥2 independent sources, writes a 150–175 word script |
| Gates | G1 brief + hook takes · G2 final | **G0** angle · **G1** hook + script · **G2** narration + storyboard · **G3** final |
| Footage | Generic highlight scene pack | Story-specific: legally-safe archival sourced automatically + a prioritized manual shot list for Franco + HyperFrames graphic beats where no footage exists |
| Graphics | Captions + watermark only | HyperFrames block library in `pipeline\graphics\` (era banners, stat callouts, quote cards, clippings, maps, timelines) |
| SFX | None (removed v2.3) | Back, sparingly: `assets\sfx\` (impact, whoosh, text_pop, archival, atmosphere) |
| Music | One YouTube Audio Library track, drop on first speech word | Bed under narration, drop on the climax speech clip, up to 2 music cues. Trending TikTok sound is added **in the TikTok app** over a `_nomusic` delivery file |
| Length | 62–66s (61–70 window) | **88–92s target** (QA window 60–95s) |
| Grade | `standard.cube` on every shot | `standard.cube` on modern footage; archival gets an era look in the **archival frame** (approved exception to no-letterboxing) |
| ElevenLabs | 2 hook takes | 1 full-script take (~1,150 credits), pickups only for broken beats. Free plan: attribution line in every caption file |
| Hashtags | Generic motivation | US-coded (#nba #nfl #goat #sportshighlights + athlete-specific) |
| Scripts | v2.4 behaviour | v2.4 stays the default. v3.0 is opt-in: `--format v3` flag, or a `_v3.py` file (§16) |

**Stays LOCKED from v2.4:** Declan Sage voice block · caption style (all caps, Anton, soft dark halo, fixed x=540 y=1380, one caption at a time) · watermark · sign-off card · 1080×1920 / 30fps / H.264 · limiter mastering (−14 LUFS, ~−1.6 dBTP) · subject folder structure (`Speech\ Narration\ Scene Pack\ Music\`) · English only · @thestandard.daily · island transcription method · verify-before-claim.

---

## Trigger

Franco says any of: "new Standard video: <Athlete>", "run v3 on <Athlete>", "next TikTok: <Athlete>", optionally with a constraint ("stay away from his Finals runs").

## Input

The only required input is **an athlete name.** Optional: `avoid` (topics to stay away from), `angle_hint`, `slug`, `allow_controversy` (set at G0). `start_video.py` writes `working\<slug>\request.json`:

```json
{"subject": "Michael Jordan", "slug": "michael-jordan-02",
 "avoid": ["Bulls Finals runs"], "angle_hint": null,
 "allow_controversy": false, "format": "v3", "created": "2026-10-24"}
```

---

## Preconditions (auto-check, report what's missing in the first reply)

1. `E:\FRANCO\The Standard\` exists with the templates at the root: `Anton-Regular.ttf`, `standard.cube`, `signoff_card.mp4`.
2. Declan Sage voice block unchanged (see "The Standard voice").
3. Tools: FFmpeg (PATH), Python with the pipeline packages (§17), Node.js 22+, HyperFrames (`npx hyperframes --version`), yt-dlp (pip or `pipeline\bin\yt-dlp.exe`).
4. `do_not_cover.md` present; `assets\sfx\` has ≥1 file per category (see `assets\sfx\README.md`); `pipeline\graphics\` present.
5. ElevenLabs credits: one full take costs ~1,150 credits. Report the balance if visible. Free plan ≈ 10,000/month → enough for 1 video/week.

---

## The format (LOCKED v3.0): 5 beats

| Beat | Time | Audio | Picture |
|---|---|---|---|
| **1. Hook claim** | 0:00–0:03 | Narration (proper noun + detail land before 2.0s) over music bed −18 dB, 0.5s fade-in from 0:00 | Strongest story-specific shot, or `hook_title` / `stat_callout` block |
| **2. Scene set** | 0:03–0:15 | Narration: where, when, stakes | `era_banner` + archival / map / photo |
| **3. Story unfolds** | 0:15–0:50 | Narration: challenge → twist → what they did | Archival + b-roll + 1–3 graphic beats (stat, clipping, timeline) |
| **4. Result + real voice** | 0:50–1:15 | Narration builds → music-only pause 1.0–1.5s → **music drop on the first word of the speech clip** → 12–20s of the athlete's real voice | On-camera a-roll (if speech is a video) + strongest shots |
| **5. Lesson + brand** | 1:15–1:29 | Narration: the lesson; the last narrated line is **"Hold the standard."** over the ring-out | `lesson_card` → `brand_lockup` ("HOLD THE STANDARD.") |
| Sign-off | last 1s | Music tail | `signoff_card.mp4` |

**Length:** target 88–92s. Floor 60s (Creator Rewards). Ceiling 95s.
**Narration:** **150–175 words** total (Declan Sage measures ~150 wpm). Never more — 200 words plus the speech clip runs past 95s.
**Real speech:** 12–20s total, 1–2 complete thoughts, only in beat 4. The narration never pre-states what the athlete is about to say.

---

## Story rules

### Angle (G0)
- **Lesser-known, specific, with a motivational arc:** challenge → response → outcome → lesson.
- Never anything in `do_not_cover.md` or Franco's `avoid` list.
- Must be **buildable**: footage or photos exist (or the beat can be a graphic), AND a real-speech clip of the athlete about *this* story or its lesson exists. Angles without a speech-clip candidate are not offered.
- Avoid recent personal tragedies.
- **Controversy (legal issues, doping, suspensions): opt-in per video at G0.** Tag every angle `controversy: yes/no`. A "yes" angle is used only when Franco picks it knowingly; record `allow_controversy: true` in request.json.

### Hook rule (STRICT, G1)
The first 2 seconds of narration must state a **factual, surprising, specific claim** containing:
- ≥1 **proper noun** (person, team, place, league, event), AND
- ≥1 **specific detail**: a number, a place, a date, or a concrete situation.
- The claim is **verified** in `claims.json` (≥2 independent sources).
- ≤14 words in total; the proper noun AND the detail sit in the first ~5 words.

Good (style examples — still verify before use): "Michael Jordan rode a bus through Birmingham for $850 a month." · "JJ Watt broke his hand in week 2 and still led the league in sacks."
Rejected automatically: "Limits are an illusion." · "He proved them all wrong."

`generate_hook_variants.py` rejects any variant that fails the rule. Franco sees 3 that pass, **as text only** — no audio for losing hooks.

### Claims
Every specific/testable claim (number, date, place, quote, ranking) in the script or on screen has an id in `claims.json` with **≥2 independent sources** (different publishers; not two Wikipedia mirrors; not one copying the other). The claim's snippet must actually appear on each fetched page. If a claim can't be verified, rewrite it at narrative level or cut it. Quote cards use verbatim quotes with a source.

### Script craft
- Confident, specific, past tense. US context (cities, leagues, dollars, miles).
- One idea per sentence. Short sentences at turns in the story.
- Beat 5 ends on "Hold the standard."
- Each sentence in `script.json` has a `spoken` form (ElevenLabs input: "eight hundred fifty dollars") and a `display` form (captions/graphics: "$850").
- Tag each sentence with its claim ids and the visual it needs (archival / broll / aroll / graphic block name).

---

## The Standard voice (LOCKED — do not modify)

Narration = **Declan Sage, always.** No substitutions, no "try a different voice for this one."

```
ELEVENLABS_VOICE_NAME:  Declan Sage
ELEVENLABS_VOICE_ID:    kqVT88a5QfII1HNAEPTJ
ELEVENLABS_MODEL:       eleven_multilingual_v2
STABILITY:              0.50
SIMILARITY_BOOST:       0.75
STYLE_EXAGGERATION:     0.20
```

**Generation (v3.0):**
1. After G1, generate **1 take of the full script** in the ElevenLabs connector (`creative_generate_speech`), paragraph breaks between beats. ~1,150 credits.
2. Give Franco the flow URL. Franco listens, downloads, drops it in `<Subject Name>\Narration\` (any filename).
3. If one beat is off, generate **only that beat** as a pickup take (Franco drops it in `Narration\` too). Never regenerate the whole script for one beat.
4. Never generate audio for hook variants that weren't picked.

**ElevenLabs notes:**
- Franco has the **restricted** ElevenLabs connector.
- **Plan: free.** Budget per video ~1,350–1,550 credits (1 take + pickups) → 1 video/week fits the free monthly credits. During kit testing, never generate full-length narration; reuse existing audio or short lines.
- **Free-plan attribution:** every caption file ends with the line `Voice: ElevenLabs` (deliver.py adds it).
- **Upgrade trigger:** upgrade to the cheapest paid ElevenLabs plan (commercial license) **when Creator Rewards earnings start.** Franco makes that purchase; never Claude.
- **Free-tier flag:** if generation fails with "Unusual activity detected / Free Tier access disabled," retry once with `generations_count=1`. If still blocked, hand off: give Franco the flow URL and ask him to generate on the web.
- **Narration pickup is ALWAYS a handoff.** The container cannot download from ElevenLabs' Google Storage URLs.
- Hook mispronounces a name → spell it phonetically in the ElevenLabs input only.

---

## Folder structure

```
E:\FRANCO\The Standard\
  CLAUDE.md                 ← this file (auto-read by Claude Code)
  hook_log.md               ← date | slug | hook type | subject | angle
  metrics_log.md            ← retention numbers per video (learning batch)
  do_not_cover.md           ← excluded angles, grouped by subject
  Anton-Regular.ttf · standard.cube · signoff_card.mp4   ← templates at ROOT
  assets\
    sfx\{impact,whoosh,text_pop,archival,atmosphere}\    ← audio files gitignored
    sfx\README.md           ← one row per file: source URL, author, license
    trending_sounds\_README.md, sounds.txt, downloads\ (gitignored)
    fonts\                  ← OFL fonts for graphics
  pipeline\
    *.py                    ← §16
    archival_sources.json   ← allow-listed sources/channels for source_archival.py
    graphics\               ← HyperFrames block library (§16b)
    looks\                  ← era looks for archival footage
    models\  bin\
  <Subject Name>\
    Speech\                 ← athlete interview/speech for the climax clip
    Narration\              ← Declan Sage full-script take (+ pickup takes)
    Scene Pack\             ← Franco's footage from the manual shot list
      _sourced\             ← auto-sourced archival, each file + .license.json sidecar
    Music\                  ← YouTube Audio Library bed (1–2 tracks, keep original filenames)
  working\<slug>\
    request.json · research.md · angles.json · claims.json · sources.md
    script.json · hooks.json · shot_list.md · graphics_plan.json · graphics\ (HF project)
    timeline.json · segments.json · cuts.json · captions .ass · master.mp4 · qa\
  outbox\
    <slug>_v<N>.mp4           ← full mix (YouTube Audio Library bed)
    <slug>_v<N>_nomusic.mp4   ← narration + speech + SFX; add the trending sound in-app
    <slug>_caption.txt · <slug>_sources.md · <slug>_sound.txt
```

**Narration classifier:** anything in `<Subject>\Narration\` is narration. Keep the legacy `Speech\*hook*|*eleven*|*narration*` fallback for pre-v2.4 folders.
**File swaps mid-run:** if Franco replaces a source file during the build, re-list the folder and re-stage. Don't reuse the old copy.

---

## What Franco provides per video

- **Athlete name + optional constraint** in chat.
- **G0:** picks the angle; drops the climax speech file into `<Subject>\Speech\` (or approves one of the candidate links).
- **G1:** picks the hook; edits/approves the script.
- **After G1:** downloads the narration take into `<Subject>\Narration\`.
- **G2:** adds the P1 (and ideally P2) shots from `shot_list.md` into `<Subject>\Scene Pack\`; confirms storyboard.
- **Music:** one or two YouTube Audio Library tracks in `<Subject>\Music\` (cinematic build / dark hybrid orchestral, with a clear drop).
- **Weekly:** bookmarks trending TikTok sounds in `assets\trending_sounds\sounds.txt`.
- **G3:** uploads; adds the trending sound in the TikTok app over `_nomusic`; fills in `metrics_log.md` at 48h / 7 days.

Franco does NOT provide: research, script, hooks, captions, graphics, grade, watermark, sign-off, TikTok caption, hashtags.

---

## The pipeline

Stack: Python + ffmpeg + sherpa-onnx (NVIDIA Parakeet) + soundfile + librosa + PIL + PySceneDetect + HyperFrames (Node) + research packages (§17). Claude Code's own WebSearch/WebFetch does the web searching; scripts do the checkable parts (fetching, matching, validating, bookkeeping).

### Step 0: Request + research → GATE 0
1. `start_video.py "<Athlete>" [--avoid ...]` → subject folder tree + `request.json`.
2. `research_athlete.py init` → `research.md` (Wikipedia summary + Wikidata facts: teams, years, places), exclusions loaded (`do_not_cover.md` + `avoid` + channel's covered angles).
3. Claude searches the web for **5–8 candidate angles**, logging every source URL in `research.md`.
4. `research_athlete.py check` → fuzzy-match every candidate against the exclusions; drop hits.
5. `research_athlete.py score` → `angles.json`: surprise · arc strength · source quality · footage feasibility · speech-clip availability. Keep the top 2–3.

**→ GATE 0: Story angle.** For each of 2–3 angles: one-line logline, arc (challenge → response → outcome → lesson), 3+ sources, why it's lesser-known, `controversy: yes/no`, footage feasibility (auto-sourceable / manual / graphics-only), and speech-clip candidates (links + timestamps). Franco picks one and supplies the speech file.

### Step 1: Facts, script, hooks → GATE 1
1. Every testable claim → `claims.json`. `verify_facts.py` fetches each source, confirms the snippet is on the page, checks independence. ≥2 independent sources or the claim is cut / rewritten at narrative level.
2. Write `script.json`: 5 beats, 150–175 words, sentences with `spoken`, `display`, `claims[]`, `visual`.
3. Write hook candidates; `generate_hook_variants.py` validates against the hook rule → `hooks.json` with 3 passing variants.
4. `check_script.py` → word count, time per beat at 150 wpm, total incl. speech clip, all claims verified, hook rule, no excluded angle.

**→ GATE 1: Hook + script.** Franco sees the 3 hooks (text), the full script, and the claim table. Franco picks a hook and approves/edits. Then Claude generates 1 ElevenLabs take of the full script and gives Franco the flow URL.

### Step 2: Sourcing (runs while Franco handles G1 / the narration download)
1. `source_archival.py` searches archive.org (explicit public-domain / CC0 / CC-BY license URLs only), Wikimedia Commons (free licenses), US-government public-domain works, and the allow-listed channels in `pipeline\archival_sources.json`. Every download gets a `.license.json` sidecar. Anything that looks like league broadcast footage is flagged, never trusted on an uploader's "public domain" label.
2. Anything not legally sourceable → `shot_list.md`, prioritized **P1 essential · P2 strong · P3 nice**, with search hints and the HyperFrames fallback block for each P1/P2 line.
3. Paid sources (Getty, Pond5, paid SFX) need Franco's OK every time.
4. `rotate_trending_sound.py` picks the in-app trending sound (§Step 10).

### Step 3: Narration in + storyboard → GATE 2
1. `inventory.py --format v3` → classify everything, ffprobe every video, check license sidecars.
2. Transcribe narration with `transcribe_islands.py` (clean TTS — island method is exact). Beat boundaries + word timings → `timeline.json` (`"format": "v3"`).
3. Cut the climax speech clip(s) with `cut_speech.py` (island method, `expected` text, `*emphasis*`). Use `transcribe_chunks.py` for noisy live sources (see v2.4 notes in Step 2 below).
4. Plan `segments.json` (shots) and `graphics_plan.json` (graphic beats); `build_graphics.py --stills` renders graphic stills.
5. `build_contact_sheet.py --plan … --format v3` → storyboard sheet per beat with the caption line at y=1380.

**→ GATE 2: Narration + storyboard.** Franco confirms the narration take (or asks for a beat pickup), the storyboard, and which P1/P2 manual shots are now in `Scene Pack\`.

#### Transcription notes (carried from v2.4)
Parakeet via sherpa-onnx (`sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8`, `model_type="nemo_transducer"`, cached in `pipeline\models\`). Whisper/Hugging Face downloads are blocked — don't try.

**Parakeet's word timestamps drift 0.1–0.4s. Don't cut on them directly.** Island method:
1. Split audio into speech islands with an energy threshold (−55 dB, 10ms frames, merge gaps <0.12s).
2. Re-run recognition per island for exact text.
3. Cut at island edges. For cuts inside an island, recognize the piece alone and nudge start/end by 0.05s until the text is clean.

**Live-recording fallback:** continuous crowd ambience never drops below −55 dB → islands collapse and Parakeet OOMs (exit 137). Use `transcribe_chunks.py` (60s chunks, 2s overlap). For precision cuts, re-island narrow windows with `--dbfs` −40 or −38.

Exclude every voice that isn't the athlete (interviewers, hosts, anyone reading the athlete's words).

**Speech clip rules:** complete thoughts only; never trim words that finish a thought. Remove fillers ("uh," "um," duplicated words, false starts, interviewer framing). Gaps inside a thought 0.3–0.6s.

**`cut_map.json` format** (unchanged):
```json
{
  "src_map": {"int": "E:/FRANCO/The Standard/<Subject>/Speech/<file>.mp4"},
  "clips": [
    {"name": "climax1", "src": "int", "start_s": 364.34, "end_s": 371.20,
     "expected": "People added *wood* to that fire."}
  ]
}
```

### Step 4: Audio mix (`mix_audio_v3.py`)

| Section | Music level |
|---|---|
| Under narration (beats 1–3) | −18 dB, 0.5s fade-in from 0:00 |
| Between beats (≤0.4s gaps) | −12 dB |
| Pre-climax pause (1.0–1.5s) | ramp −18 → 0 dB |
| Drop | first word of the climax speech clip |
| Under real speech | −9.5 dB |
| Under lesson narration | −14 dB |
| Ring-out under "Hold the standard." | −4 dB |
| Sign-off | fade out over 1s |

- **Up to 2 music cues** (`music.cues[]`, 1.5s crossfade): a bed for beats 1–3 and the drop track for beats 4–5. Needed because most YAL tracks drop at 20–30s and the climax sits at ~0:52.
- **SFX layer** from `timeline.json` `sfx[]`: whoosh on beat transitions, impact on the drop and stat callouts, text_pop on graphic entries, archival on archival cut-ins, atmosphere under the pre-climax pause. **Never on top of a narrated proper noun or number.** Average ≤1 SFX per 3s. SFX sit ~12 dB under the voice.
- **Voice and mastering (LOCKED from v2.4, `master_mode: "limiter"`):**
  1. Each voice clip and the narration normalized to −16 dBFS RMS.
  2. Gentle voice compression: threshold −22 dB, ratio 2:1, attack 5 ms, release 120 ms; voice peaks held to ≤14 dB above voice RMS; voice matched back to its original level.
  3. Master: normalize the full mix to **−14 LUFS**, then lookahead limiter at **0.75** (~−2.5 dBFS), one correction pass.
  4. Delivery lands ~−14.5 LUFS / ~−1.6 dBTP after AAC.
  Overrides: `"voice_comp": false` or a dict, `"master_target_lufs"`, `"master_limit"`, `"master_mode": "loudnorm"` (old chain).
- Also writes **`mix_nomusic.wav`**: same mix and mastering gain with music muted, for the `_nomusic` delivery.

### Step 5: Find the music drop
- **Check real track length** (`ffprobe` + RMS envelope). NEFFEX "Free Me" is 137s on disk but music ends at 87s.
- RMS envelope scan at 100ms, snap to nearest onset. **First-rise bias:** `find_music_drop.py` picks the first rise within 3 dB of the max (0.3s smoothing). Override with `--search-start` / `--search-end`.
- **Known drops:**
  - `Free Me (Instrumental) - NEFFEX.mp3`: **25.66s**, music ends 87s. **Use this value — the detector gets this track wrong** (82.5–83s silence then a hard hit fools it). Same risk for any track with dead silence before a late hit: sanity-check by ear.
  - `Density & Time.mp3`: 96.0s (near-silence 94.2–95.9s doubles as the pre-payoff pause). Good single-cue candidate for v3 — its drop is late enough.
  - `Cutscene Crush.mp3`: **21.3s** (pre-dip at 20s).
  - `Black Thorns - Jimena Contreras.mp3`: **15.523s** (detector correct). Music ends 97.2s.
  - `It's Only Worth It if You Work for It (Instrumental) - NEFFEX.mp3`: **22.628s** (detector correct, confirmed in michael-jordan-02 mix). Music ends 181.4s. Quiet intro 0–22s works as the pre-climax dip in cue 2.
- v3.0: `drop_tl` = video time of the **first word of the climax speech clip** (~0:50–0:55). `track_start = drop_point − drop_tl`. If that's negative, use 2 cues.
- If the track has a second hit near the end, time the ring-out so it lands on "Hold the standard."

### Step 6: B-roll, archival and graphics
- **Scene detection:** PySceneDetect `ContentDetector` threshold 27 (`scene_detect.py` → `shots.json`). Shots that open with a dissolve: offset start ~0.25s.
- **No face-detection model.** Frame by eye: contact sheets (midframe per shot, crop guides, 20 per image) → set `xc` per shot → re-check sheet of rendered crops at 20/50/80%.
- **Keyframe `xc`** as `[time, xc]` for moving subjects.
- **Avoid close-ups with the face in the lower 35%** — captions never move.
- **Cadence:** cut every 1.5–3s on beats/breaths. Graphic beats hold 2–4s; at most one graphic beat every ~10s.
- **Graphics safe zone:** key graphic text inside **y=380–1180** (below the watermark at 300, above the caption at 1380). Captions are muted while a `quote_card` or `newspaper_clipping` shows the same words.

**`segments.json` (v3 segment types):**
```json
{"format": "v3", "segments": [
  {"name": "b1_hook",  "type": "graphic", "block": "stat_callout", "out_dur_s": 2.6},
  {"name": "b2_era",   "type": "graphic", "block": "era_banner",   "out_dur_s": 2.4},
  {"name": "b2_arch1", "type": "archival", "src": "_sourced/ia_barons_1994.mp4",
   "src_offset_s": 12.0, "out_dur_s": 2.8, "speed": 0.9, "grade": "era_90s"},
  {"name": "b3_photo", "type": "still", "src": "_sourced/commons_1994.jpg",
   "out_dur_s": 3.0, "focus": [0.5, 0.35]},
  {"name": "b3_t1",    "type": "broll", "shot_idx": 7, "out_dur_s": 2.4, "xc": 0.58},
  {"name": "b4_oncam", "type": "aroll", "out_dur_s": 3.0, "xc": 0.48}
]}
```
- `broll` and `aroll`: exactly as v2.4 (`shot_idx`, `xc` number or keyframes, `speed` default 0.5, `src_offset_s`; a-roll at 1.0×, auto lip sync from `cuts.json` + `mix_debug.json`, must sit entirely inside one speech clip, low-res denoise/sharpen, `"enhance": false` to disable).
- `archival`: SD / 4:3 sources go in the **archival frame** treatment — never stretched or cropped to 9:16. Speed 0.8–1.0×.
- `still`: photo with a slow push-in (1.0 → 1.08) toward `focus`.
- `graphic`: pre-rendered HyperFrames block from `build_graphics.py`; not graded.
- If a shot is too short for `out_dur_s × speed`, the last frame is held and `render_shots.py` prints "frozen" — pick a longer shot.
- Pass `--target-dur-s <audio length − 1s sign-off>` so the video pads exactly to the audio.

### Step 7: Reframe, speed-ramp, grade

Output: 1080×1920, 30fps, H.264 yuv420p. No blurred background. No letterboxing — **except the approved archival frame** (v3.0).

Per-shot ffmpeg filter chain (b-roll / a-roll, LOCKED):
```
setpts=(PTS-STARTPTS)/SPEED,
fps=30,
crop=608:1080:X:0,
scale=1080:1920:flags=lanczos,
lut3d=file=E:\FRANCO\The Standard\standard.cube,
setsar=1,
format=yuv420p
```

**Crop math:** `X = xc × 1920 − 304`, clamped 0..1312. Sources not exactly 1080 tall are first scaled to 1080 tall (`scale=-2:1080`), then `X = xc × W − 304`, clamped 0..W−608. File paths inside ffmpeg filters use forward slashes with the drive colon escaped: `E\:/FRANCO/The Standard/standard.cube` (scripts do this).

**Speed ramps:** b-roll 0.5× · fast action 0.6–0.7× · hook shot 0.64× · a-roll 1.0× always · archival 0.8–1.0×.

**Grade:** `standard.cube` at full strength on b-roll and a-roll. Archival and stills use an era look from `pipeline\looks\` (`era_70s`, `era_90s`, `bw_film`) via the segment's `grade` field. Graphic segments are not graded.

**ffmpeg gotchas:** for slow-mo, `-t` goes BEFORE `-i`. Use `minterpolate=mi_mode=blend` + `tpad=stop_mode=clone` so slow-mo shots reach full frame count. Pad the last frame so video length = audio length before the sign-off.

### Step 8: Captions (LOCKED — one caption at a time)

**Timing:** forced-align on the FINAL mixed audio, never the script. Rebuild after any audio change.

**Caption source of truth (v3.0):** narration = `display` text from `script.json`; speech = `expected` text from `cuts.json`. Each is distributed over Parakeet word timings within its span, matched by text via difflib.

**Snap after silence:** any word after ≥120ms silence snaps to the first voiced sample (−55 dB detector; `--snap-dbfs −40` for noisy sources). Tolerance ±0.25s.

**One caption on screen at any moment:**
- Each chunk ends ≥1 frame (33ms) before the next starts. Never extend past the next one's start.
- Chunks shorter than ~0.2s merge with a neighbour only if the result fits (≤3 words AND ≤900px) — re-check width on merge. Long single words scale down to fit 960px. A rebalance pass lengthens captions still under 0.2s by borrowing from neighbours but never moves a start more than 0.14s from its word.
- Back-to-back chunks (gap <0.15s): no fade-out, hard cut. Keep the pop-in.
- **QA:** parse the final `.ass`, assert no two Main-layer events overlap.

**Chunking:** ≤3 words, ≤~900px at 200px Anton (PIL with the real font), break on punctuation and gaps >0.35s.

**Style (LOCKED):**
- ALL CAPS throughout. Font: Anton via `subtitles=overlay.ass:fontsdir=E:\FRANCO\The Standard\`.
- Two styles: W (normal 200px), P (emphasis 225px):
  ```
  Style: W,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0,0
  Style: P,Anton,225,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0,0
  ```
  (Last field is Encoding; the `[V4+ Styles]` Format line lists 23 fields.)
- **Emphasis:** `*asterisks*` in `script.json` display text / `cuts.json` expected text. Each emphasis word is its own P caption and never merges. Asterisks on small words (THE/A/I/WERE/TO…) are ignored. v3.0: emphasize the hook's proper noun and number, plus ≤1 peak word per beat.
- Every word is TWO Dialogue lines:
  ```
  Layer 0 (halo):
  {\pos(540,1380)\fad(60,80)\fscx78\fscy78\t(0,100,\fscx100\fscy100)\bord18\shad0\blur22\3c&H000000&\3a&H28&\1a&HFF&}WORD

  Layer 1 (text):
  {\pos(540,1380)\fad(60,80)\fscx78\fscy78\t(0,100,\fscx100\fscy100)\bord5\shad0\blur0.6}WORD
  ```
- **Position: x=540, y=1380, fixed every word, every video. Captions NEVER move.**
- No drop shadow, no colored text, no boxes or backgrounds.
- Abbreviations like P.M. keep their final period.

### Step 9: Watermark
`@thestandard.daily` · Anton 44px · white · **25% opacity** · no outline · centered, y=300 · static on every frame except the sign-off card.

### Step 10: Trending sound (in-app, never baked in)
`rotate_trending_sound.py` reads `assets\trending_sounds\sounds.txt`, downloads each bookmark into the gitignored `downloads\` **for analysis only** (length, BPM, RMS envelope, drop position), ranks fit for the 90s format (drop alignable with the ~0:52 climax, steady stretch for under narration, freshness, not used in the last 3 videos), and writes `outbox\<slug>_sound.txt`: which sound to pick in the TikTok app, start offset, suggested volume (~15%). Trending sounds are never mixed into a delivery file and never committed.

### Step 11: Sign-off + two-tier render
Append `signoff_card.mp4` (1s), music tail under it.

**Archive master** (`working\<slug>\master.mp4`): 1080×1920, 30fps, H.264 yuv420p, 10–12 Mbps, AAC stereo 48kHz, −14 LUFS.

**Delivery files:** `-b:v 2450k -maxrate 4000k -bufsize 8000k -c:a aac -b:a 160k`, 2-pass. `final_render.py --format v3` renders both `delivery.mp4` (full mix) and `delivery_nomusic.mp4` (from `mix_nomusic.wav`, same picture).

### Step 12: Automatic QA (`qa.py --format v3`)
Everything from v2.4:
- Loudness −14 ±1 LUFS, true peak below −1 dBTP
- ≥6 frame grabs, every one a full 9:16 frame with captions at x=540, y=1380
- No two Main-layer caption events overlap; every caption all-caps and starting within ±0.15s of its word; captions match script.json + cuts.json
- Watermark on every frame except the sign-off; sign-off card is the last 1s

Plus v3.0:
- Length 60–95s (warn outside 88–92s)
- Hook rule passes on the first 2.0s of the final narration transcript
- Narration transcript matches `script.json`; speech matches `cuts.json` and contains only the athlete
- Every claim id used in the script / graphics is `verified`
- Real speech total 12–20s, only in beat 4
- Every file from `_sourced\` has a `.license.json` sidecar
- Graphic text inside the safe zone (y=380–1180)
- No SFX onset overlaps a narrated proper noun or number
- `_nomusic` file present, same length, in sync
- `timeline.json` / `segments.json` carry `"format": "v3"`

### → GATE 3: Final

`deliver.py --format v3` puts everything in place:
1. `outbox\<slug>_v<N>.mp4` and `outbox\<slug>_v<N>_nomusic.mp4` (sha256-verified copies). Then send the video to Franco with SendUserFile.
2. `outbox\<slug>_caption.txt`:
   ```
   <one punchy line in the video's spirit — a statement, not the hook> <one emoji>

   #<athlete> #<nickname> #<league> #<sport> #goat #sportshighlights #thestandard #<story-specific> #<theme> #motivation

   Voice: ElevenLabs
   ```
   One line, one emoji, blank line, ~10 US-coded hashtags on one line. Always **#thestandard**. **Never #fyp or #viral.** The `Voice: ElevenLabs` line stays while on the free plan.
3. `outbox\<slug>_sources.md` (claims, sources, license notes) and `outbox\<slug>_sound.txt`.
4. `hook_log.md` entry: `<date> | <slug> | v3:<number|place|date|situation> | <Subject Name> | <angle>`.
5. The angle appended to `do_not_cover.md` under "## Covered by The Standard".
6. A row in `metrics_log.md` for Franco to fill in at 48h / 7 days (`log_metrics.py`).

If Franco wants a section-only change, re-render just that section first.

---

## Approval gates

| Gate | Franco sees | Franco decides |
|---|---|---|
| G0 Angle | 2–3 angles, sources, controversy tag, feasibility, speech-clip candidates | Which story; supplies the speech file |
| G1 Hook + script | 3 hook variants (text), full script, claim table | Hook, script edits. Then 1 ElevenLabs take is generated |
| G2 Narration + storyboard | Narration take, storyboard sheet, shot list status | Take OK (or a beat pickup), shot/graphic picks, manual shots added |
| G3 Final | Both delivery files, caption, sources, sound pick, QA report | Upload, or section fixes |

---

## §16 — The `pipeline\` folder

This doc is the source of truth; scripts implement it. Before using a script, verify it implements the current doc. If a rule here changed, update the script to match, never the other way around.

**v2.4 default rule:** every v2.4 script still runs v2.4 behaviour with no flag. v3.0 behaviour is opt-in: `--format v3` on an existing script, or a separate `_v3.py` file when the underlying model differs. `timeline.json` / `segments.json` carry `"format": "v3"`, and flagged scripts stop with an error if the flag and the file disagree. Never delete a v2.4 script.

**Status legend:** ✅ working · 🟡 v3 behaviour still to implement · 🔲 scaffold only (signatures + docstrings, not usable yet)

**New in v3.0:**
| Script | Status | Does |
|---|---|---|
| `start_video.py` | 🔲 | Subject folder tree + `request.json` + next slug |
| `research_athlete.py` | 🔲 | `init` (Wikipedia/Wikidata → research.md), `check` (fuzzy match vs exclusions), `score` (→ angles.json) |
| `verify_facts.py` | 🔲 | Fetch sources, confirm snippets, check independence → claims.json status + sources.md |
| `check_script.py` | 🔲 | Word count, beat timing, claims verified, hook rule, exclusions |
| `generate_hook_variants.py` | 🔲 | Validate hooks against the hook rule → hooks.json (3 passing variants) |
| `source_archival.py` | 🔲 | archive.org / Commons / gov / allow-listed channels with license sidecars → `_sourced\` + shot_list.md |
| `rotate_trending_sound.py` | 🔲 | Analyze bookmarked sounds, pick one for in-app use → `<slug>_sound.txt` |
| `build_graphics.py` | 🔲 | Fill HyperFrames blocks from graphics_plan.json, check, render mp4s / stills |
| `mix_audio_v3.py` | ✅ | Narration-led mix, 2 music cues, SFX layer, `mix_nomusic.wav`; v2.4 gain staging with a 4× oversampled limiter + 16 kHz low-pass (true-peak safe after AAC) |
| `log_metrics.py` | 🔲 | metrics_log.md rows + comparison with v2.4 baseline |
| `apply_look.py` | ✅ | Era looks from `pipeline\looks\looks.json` (era_70s, era_90s, bw_film) |

**Carried from v2.4:**
| Script | Status | v3 change |
|---|---|---|
| `inventory.py` | ✅ / 🟡 | `--format v3`: `_sourced\` + license sidecars, multiple narration files, SD archival not blocking |
| `transcribe_islands.py` | ✅ | none |
| `transcribe_chunks.py` | ✅ | none |
| `cut_speech.py` | ✅ | none |
| `find_music_drop.py` | ✅ | none |
| `mix_audio.py` | ✅ | none (v3 uses `mix_audio_v3.py`) |
| `scene_detect.py` | ✅ | none |
| `build_contact_sheet.py` | ✅ | v2.4 only. v3 storyboard: `build_contact_sheet_v3.py --slug <slug>` ✅ |
| `render_shots.py` | ✅ | `--format v3`: `broll` (src file), `still` (push-in + era look), `graphic` (cut from the HF reel). `archival` type still to add |
| `build_captions.py` | ✅ | `--format v3`: script.json + cuts.json text aligned on mix_nomusic.wav, `mute_captions` segments |
| `final_render.py` | ✅ | `--format v3`: `_nomusic` delivery |
| `deliver.py` | ✅ | `--format v3`: two videos, sources.md, sound.txt, attribution line, v3 hook_log, do_not_cover append, metrics row |
| `qa.py` | ✅ | `--format v3`: Step 12 additions |

**Defaults scripts find on their own:** Parakeet model in `pipeline\models\sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8\`; Anton at the root.

### §16b — Graphics library (`pipeline\graphics\`)

HyperFrames compositions (HTML + GSAP timeline, not .jsx), 1080×1920 @ 30fps, one block per file in `compositions\`, copy and colors as variables. `build_graphics.py` copies blocks into `working\<slug>\graphics\`, fills variables, runs `npx hyperframes check --json`, renders. See `pipeline\graphics\README.md` for each block's variables.

**Look (LOCKED v3.0):** black / off-white base, accent **white `#FFFFFF`** — monochrome. Emphasis comes from size, weight and underline, never color. Fonts: Anton (headlines, numbers), Playfair Display (quotes, OFL), IBM Plex Mono (datelines, OFL), all via `@font-face` from `assets\fonts\`. All key text inside y=380–1180.

| Block | Used for | SFX cue |
|---|---|---|
| `hook_title` | Beat 1 when there's no strong shot | impact |
| `era_banner` | "1994 · BIRMINGHAM, AL" | whoosh |
| `stat_callout` | Big number + label, count-up | text_pop + impact |
| `quote_card` | Verified quote + attribution | typewriter |
| `newspaper_clipping` | Real headline text under a **generic** masthead | film click |
| `location_map` | US state outline + city pin | tick |
| `timeline_strip` | 2–5 dates in order | tick per dot |
| `name_card` | Introduces another person | pop |
| `versus_card` | Before/after or A vs B stat | impact |
| `archival_frame` | SD 4:3 footage/photo in a frame with grain + date stamp | projector loop |
| `photo_push` | Commons photo, slow push-in | — |
| `beat_transition` | Light leak / whip between beats | whoosh |
| `lesson_card` | Beat 5 lesson line | swell |
| `brand_lockup` | "HOLD THE STANDARD." | impact |

**Never:** recreate a real publication's masthead or page (NYT, Sports Illustrated, etc.), invent a headline or quote, or use a team/league logo as decoration.

### §17 — Install
```
python -m pip install Wikipedia-API internetarchive trafilatura beautifulsoup4 rapidfuzz yt-dlp python-dateutil
```
Already used from v2.4: requests, numpy, librosa, soundfile, Pillow, scenedetect, sherpa-onnx. HyperFrames via `npx hyperframes`. Ask Franco before installing anything else.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Captions overlap each other | Enforce one-caption-at-a-time (§8); QA parses the .ass |
| Caption too wide after merge ("GOOD AS MAGIC JOHNSON" 1,883px) | Merge must re-check ≤900px before committing |
| Caption covered subject's chin | Leave it. Captions never move. Pick a different shot next time |
| Speech line cut wrong | Re-find words via island method, never raw Parakeet timestamps |
| Captions timed wrong because of a stutter | difflib match, not proportional index |
| ElevenLabs "Unusual activity" error | Retry once with `generations_count=1`; else hand off to Franco for web generation |
| Out of ElevenLabs credits mid-month | Stop; tell Franco the balance. Never generate test narration at full length |
| Narration mispronounces a name | Phonetic spelling in the ElevenLabs input only; pickup take for that beat |
| Hook rejected by generate_hook_variants.py | Add the missing proper noun / specific detail, or move them into the first ~5 words |
| Claim can't be verified (≥2 independent sources) | Rewrite at narrative level or cut. Never ship it |
| Angle has no speech-clip candidate | Don't offer it at G0 |
| Angle has no legal footage | Use graphic beats (§16b); P1 manual shots for Franco |
| Archival source labeled "public domain" looks like broadcast footage | Don't trust it; manual shot list or graphic fallback |
| Video under 60s | Script under 150 words or speech clip too short — fix at G1. Never pad with dead air |
| Video over 95s | Tighten script toward 150 words; never cut mid-thought in the speech clip |
| Music drop too early (`track_start` negative) | Use 2 music cues, or a late-drop track (Density & Time) |
| Music drop misses the climax word | Re-calc `track_start`; verify drop with RMS scan |
| Music drop detected in the wrong place | Silence gaps fool the scan (Free Me). Use the known-drops list or `--search-start/--search-end`, check by ear |
| Music keeps playing past content | Check real length with ffprobe (Free Me is silent from 87s) |
| Graphic text sits in the caption zone | Move it inside y=380–1180 in the block |
| HyperFrames render fails | `npx hyperframes check --json` and follow its `Fix:` lines |
| Trending sound muted by TikTok | It was baked in. Never bake trending sounds — use `_nomusic` + in-app |
| Scene pack low-res despite "4K" title | Report at inventory. Modern b-roll needs 1080p+; archival goes in the archival frame |
| Interviewer voice audible in the speech clip | Re-cut. Only the athlete's voice |
| Speech source has baked-in music | Try vocalremover.org / lalal.ai; else pick another line |
| Whisper model download fails | Blocked. Use Parakeet via sherpa-onnx |
| Parakeet OOMs on long live recording | `transcribe_chunks.py` |
| ElevenLabs download URL times out | Blocked. Franco handoff |
| ffmpeg slow-mo not applying | `-t` before `-i` |
| Slow-mo shot missing frames at end | `minterpolate=mi_mode=blend` + `tpad=stop_mode=clone` |
| Video length drifts from audio length | Pad last frame with tpad |
| True peak over −1 dBTP after AAC | Lower `"master_limit"` 0.75 → 0.71 |
| Loudness below −15 LUFS | Check `"master_mode"` isn't `"loudnorm"`; read the limiter stats; report unusually peaky sources |
| Speech sounds squashed or pumps | `"voice_comp": {"ratio": 3.0, "peak_crest_db": 12.0}` and listen again |
| `render_shots.py` prints "frozen" | Shot shorter than `out_dur_s × speed`; pick a longer one |
| "a-roll … is not inside one speech clip" | Shorten or shift the segment within the listed clip span |
| On-camera shot looks soft / shows the crowd | Expected on 480p; keep short. Crowd cut-away → pick another moment |
| Script ran a v2.4 render by mistake | The `--format v3` flag was missing; flagged scripts check `"format"` in timeline.json |

---

## What this doc does NOT cover

- Uploading to TikTok and adding the trending sound in-app (manual)
- Cover image / thumbnail (manual)
- Brand check / visual identity work (Franco, separately)
- Fully automated trending-sound discovery (later; manual bookmarks for now)
- Reference-reel style analysis (later)

---

## Working with Franco

- Franco works in English. All responses in English. Scripts and technical terms stay as they are.
- Franco is new to Claude Code. Explain in plain words, no jargon. Checklist format when giving steps.
- **Permissions:** ask before installing new programs, creating accounts, using a new music source, or any paid source. Downloads with clear legitimate reuse rights (Pexels, Pixabay, Mixkit, YouTube Audio Library, Wikimedia Commons with a libre license, public domain, official/government sources that allow reuse) are fine, each with a license note.
- **Purchases:** none. Franco stays on free plans until the channel earns.
- **Don't get stuck:** if a path blocks (antibot wall, dead site), find another legitimate route. Never bypass CAPTCHAs or skip security.
- **Accounts:** Franco's only. Never Alejo's or Andrew's.
- **Use:** maximum quality with minimum repeated work. Read only what the current step needs. Leave results in files.

---

## Measuring the learning batch

The first 3 v3.0 videos are a learning batch. Keep the format fixed across all 3. Log in `metrics_log.md` at 48h and 7 days: 2s / 5s / 10s / 30s retention, average watch time, % watched in full, views, likes, shares. Compare retention points (not average watch time — the lengths differ) with v2.4: jon-jones-01 (568 views, 24 likes), michael-jordan-01 (526 views, 26 likes, 2.49s average watch).

---

## Version history

- **v3.0 (Oct 2026):** Pivot to 90s athlete micro-documentaries. 5-beat format, narration-led (~65–70s Declan Sage + 12–20s real speech at the climax). Hook rule (proper noun + specific detail in first 2s), 3 text-only variants. Autonomous research with ≥2-source verification, `do_not_cover.md`. Four gates G0–G3. Archival sourcing with license sidecars + prioritized manual shot list. HyperFrames graphics library (monochrome, white accent). SFX back. Two music cues; trending sound added in-app over a `_nomusic` file. Archival frame exception to no-letterboxing / LUT-everywhere. Controversy angles opt-in per video. 150–175 word scripts. ElevenLabs free plan: 1 full take per video, attribution line, upgrade when earnings start. v2.4 behaviour preserved as script default; v3 via `--format v3` / `_v3.py`.
- **v2.4 (Oct 2026):** Claude Code port, on-camera shots, limiter mastering. Full doc at git tag `v2.4`.
- **v2.3 and earlier:** see git tag `v2.4`.

---

## Franco's Standard history

(fill in as videos ship)

- **kobe-bryant-01** (v1 of channel): 1 view (own). First upload, format v2.0.
- **tom-brady-01**: 1 view (own). Format v2.0–2.1.
- **jon-jones-01**: 568 views, 24 likes (~4.2%). First algorithm pickup. Format v2.3, 64.6s, −14.2 LUFS.
- **michael-jordan-01**: 526 views, 26 likes (~4.9%), 2.49s average watch. Format v2.3 + MJ change requests.
- **jj-watt-01**: shipped 2026-10-23 (stats TBD). Format v2.4, 66.3s, −14.6 LUFS. First on-camera shots and limiter mastering.
- **michael-jordan-02**: delivered 2026-10-24. First v3.0 video: 1994 Barons, first pro HR the night before his father's birthday. 89.1s, −14.2 LUFS, −2.2 dBTP. All picture from Commons photos + Mixkit stock + HF graphics (no manual shots).
