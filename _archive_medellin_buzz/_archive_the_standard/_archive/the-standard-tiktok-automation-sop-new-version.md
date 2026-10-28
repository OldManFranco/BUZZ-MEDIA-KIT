# The Standard — TikTok Automation SOP (v2.3: Hook-Only Narration)

**Purpose:** The complete, executable procedure for producing a The Standard TikTok. **Every video is a short piece of AI-narrated hook followed by the subject's own real speech, with music and b-roll.** When any Claude chat is asked to produce a new The Standard video, follow this SOP exactly.

**Supersedes:** All earlier versions. Where this disagrees with earlier docs, **this SOP wins.**

**Channel:** @thestandard.daily · Tagline: *Hold the standard.*

---

## Trigger

Franco says any of: "run the pipeline on &lt;Subject&gt;," "new Standard video," "next TikTok," or drops a new subject folder into `E:\FRANCO\The Standard\` and asks for a build.

---

## §0 — Cold start (run on turn 1, before Preconditions)

A fresh chat has no tools loaded and no context from previous videos. Do this before anything else.

### 1. Load deferred MCP tools in ONE ToolSearch call

```
ToolSearch select:
  mcp__ElevenLabs__creative_generate_speech,
  mcp__ElevenLabs__creative_list_voices,
  mcp__ElevenLabs__creative_get_flow_run_status,
  mcp__ElevenLabs__creative_create_flow,
  mcp__remote-devices__device_list_dir,
  mcp__remote-devices__device_stage_files,
  mcp__remote-devices__device_commit_files,
  mcp__remote-devices__get_device_info,
  mcp__Dropbox__list_folder,
  mcp__Dropbox__search
```

### 2. Read the SOP, then check `pipeline\` matches it

- Load this SOP into context fully.
- Check `E:\FRANCO\The Standard\pipeline\` on Franco's computer. If scripts exist there, **the SOP is the source of truth, the scripts are the implementation.** Verify the scripts still implement this SOP's current rules before using them. If any rule here has drifted from the code, update the script to match this SOP (never the other way around).
- If `pipeline\` doesn't exist, create it as the chat goes and save each build script there (see §16).

### 3. ElevenLabs connector notes

- The user has the **restricted** ElevenLabs connector. `creative_generate_speech` is what we use for the hook. The "restricted-connector" notice in results is expected.
- **Free-tier flag:** account may be flagged as proxy/VPN. If generation fails with "Unusual activity detected / Free Tier access disabled," retry once with `generations_count=1`. If still blocked, hand off: give Franco the ElevenLabs flow URL and ask him to generate on the web.
- **Narration pickup is ALWAYS a handoff.** The container cannot download from ElevenLabs' Google Storage URLs. Franco listens to the takes, downloads his pick, and drops it in the subject's `Speech\` folder with `eleven`, `hook`, or `narration` in the basename.
- **Ask for 2 takes, not 4.** 2 of 4 takes failed with a rate-limit error on the Jon Jones run.

### 4. Device folder root

Franco's working root on his computer is `E:\FRANCO\The Standard\`. Dropbox mirrors `incoming\` at `/thestandard/incoming/<slug>/`. Check `get_device_info.connectedFolders` first; if `E:\FRANCO\The Standard\` isn't connected, ask Franco to add it via "+" → Add folder in the Claude desktop app.

### 5. Delivery

Write the finished .mp4 to `E:\FRANCO\The Standard\outbox\` with `device_commit_files` AND send it to the chat with `SendUserFile`. Use the gzip-and-split delivery workaround (§Delivery) to avoid the header-corruption bug — a plain copy of the first chunk can inject bytes into the file header.

---

## Preconditions (check BEFORE Gate 1)

Report what's missing in the first reply.

1. **Local folder access.** `E:\FRANCO\The Standard\` must be a connected local folder on Franco's computer.
2. **ElevenLabs voice LOCKED to Declan Sage.** See "The Standard voice" section. Do NOT touch the voice block.
3. **Templates present at the root** (`E:\FRANCO\The Standard\`): `Anton-Regular.ttf`, `standard.cube`, `signoff_card.mp4`.

---

## Pre-flight checklist (Franco runs this before saying "go")

Before the chat starts, Franco confirms:

- Subject folder exists at `E:\FRANCO\The Standard\<Subject Name>\` (e.g. "Jon Jones" — the subject's name, not the slug)
- Subject folder contains `Speech\`, `Scene Pack\`, and `Music\`, with at least one file in each
- Scene Pack is actually 1080p or higher (check with any media-info tool — titles like "4K UPSCALED" often lie; the Jon Jones pack was actually 1280×698)
- Speech source is a clean interview or speech with no music bed
- Then: "run the pipeline on &lt;Subject&gt;"

---

## The format (LOCKED v2.3)

Hook (Declan Sage) → music-only pause (1.3–1.6s) → subject speech → music ring-out (~3–4s) → sign-off card (1s)

| Segment | Time | Audio | What happens |
|---|---|---|---|
| **Hook** | 0–~4s | Declan Sage narration, dry → music enters | ONE direct question or short statement the speech answers. Over the strongest single shot of the subject. |
| **Pause** | ~1.3–1.6s | Music-only | On a quiet b-roll shot. Music drop lands on the first word of the speech. |
| **Speech** | ~54–58s | Subject's real voice + music ducked | 3–5 complete thoughts, reordered to answer the hook and build to the strongest line last. Fillers removed. |
| **Ring-out** | ~3–4s | Music ring-out | Last big music hit under the last/strongest shot. |
| **Sign-off** | 1s | Music tail | `signoff_card.mp4` |

**Target length: 62–66s** (hard floor 61s for TikTok Creator Rewards). Hard ceiling 70s.

**What this format replaces:** v2.2's 5-beat structure (Hook/Setup/Turn/Payoff/Close). No more narrated Setup/Turn/Close. No narrated "Hold the standard." The sign-off card carries the tagline; the subject carries the story.

---

## Story rules: the hook

### Hook patterns (rotate — pattern used last video is logged in `hook_log.md`)

1. **"How" question:** "How did a kid from Philadelphia become the most feared scorer in the world?"
2. **"Why" question:** "Why did Jon Jones know he'd be champion… before anyone else did?"
3. **"What made" question:** "What made Tom Brady different from every quarterback drafted ahead of him?"
4. **Contrast statement:** "Everyone said he was too small. He became a champion."
5. **Habit statement:** "He trained while everyone else was asleep. Here's why."

**Rule: pick whichever pattern fits the speech best, don't force one.** Rotate for variety across the channel. Log in `hook_log.md` every time.

### Hook craft (from Jon Jones run)

- **Simple, direct questions the speech answers.** Approved: "How did Jon Jones know he'd be champion... before anyone else did?"
- Don't build the hook on side facts the payoff never returns to. (Rejected: a Jon Jones hook built on his brothers' NFL careers — the speech didn't come back to that.)
- Avoid recent personal tragedies and controversies (legal issues, drug tests, retirement drama). Keep it a clean belief story.
- Hook can be one sentence or two. Keep it under ~4s of narration.

### Claims: narrative-level only

| Type | Example | Rule |
|---|---|---|
| **Narrative-level** | "He was overlooked." "He outworked everyone." | Free. No check. |
| **Specific / testable** | Numbers, dates, scores, draft position, specific quotes | Verify with web search before Gate 1 (brief). If not confirmable in 2 min, rewrite at narrative-level. |

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

**Pacing:** ~140 words per minute. The hook alone is ~4s, so **~9–12 words total.**

**Generation:**
1. Generate 2 takes in the ElevenLabs connector
2. Give Franco the flow URL
3. Franco listens, picks one, downloads, drops into `<Subject Name>\Speech\` with `eleven`, `hook`, or `narration` in the basename
4. Chat picks up via `device_stage_files`

Takes cost ~66 credits each for a ~4s line. Budget accordingly.

---

## Folder structure

**Local (Franco's computer):**
```
E:\FRANCO\The Standard\
  NEW the-standard-tiktok-automation-sop.md    ← this file
  hook_log.md                                   ← date | slug | pattern # | subject
  Anton-Regular.ttf                             ← templates at ROOT
  standard.cube
  signoff_card.mp4
  pipeline\                                     ← reusable Python scripts (see §16)
  <Subject Name>\                               ← subject's full name, not slug
    Speech\
      <subject>-speech-source.mp3 (or .mp4)
      eleven labs <subject> hook.mp3            ← Franco drops here after ElevenLabs
    Scene Pack\
      <subject-scene-pack>.mp4
    Music\
      <track original filename>.mp3             ← keep original filename
  working\<slug>\                               ← brief.md, transcript, word timings
  outbox\
    <slug>_v<N>.mp4                             ← finished video
    <slug>_caption.txt                          ← TikTok caption + hashtags
```

**Dropbox mirror** (optional, for backup/off-site):
```
/thestandard/incoming/<slug>/   ← slug-named (lowercase-dashes), mirrors subject folder contents
/thestandard/outbox/            ← mirrors local outbox
```

Local is the source of truth. Pipeline runs against local, not Dropbox.

**Classifier rule for `Speech\`:** basename contains `eleven`, `hook`, or `narration` → it's the hook narration. Everything else → subject audio.

**File swaps mid-run:** if Franco replaces a source file during the build, re-list the folder and re-stage. Don't reuse the old copy.

---

## What Franco provides per video

- **Subject name + optional angle** in the chat message
- **Speech source(s)** in `<Subject>\Speech\`: full-length interview/speech, clean audio, no music bed
- **Hook mp3** (after Gate 1): generated on ElevenLabs, dropped in `Speech\` with `eleven`/`hook`/`narration` in name
- **Music** in `<Subject>\Music\`: one YouTube Audio Library track, cinematic build or dark hybrid orchestral, must have a clear drop
- **Scene Pack** in `<Subject>\Scene Pack\`: real 1080p+ b-roll compilation of the subject (muted)

Franco does NOT provide: hook script, captions, grade, watermark, sign-off, TikTok caption, hashtags.

---

## The pipeline

Stack: Python + ffmpeg + sherpa-onnx (NVIDIA Parakeet) + soundfile + librosa + PIL + PySceneDetect. Install missing packages on first run.

### Step 1: Inventory and classify
- Walk `E:\FRANCO\The Standard\<Subject Name>\` recursively.
- **Check real media info**, not filenames. `ffprobe` every video for actual resolution, framerate, and codec. Report back to Franco if the scene pack is below 1080p (titles lie — "4K UPSCALED" was really 1280×698 on Jon Jones).
- Classify: `Speech\*eleven*|*hook*|*narration*` → hook; everything else in `Speech\` → subject audio; `Music\*` → music; `Scene Pack\*` → b-roll.
- Hash-dedupe audio files (md5 or sha256) before transcribing — Dropbox `(1)` dupes can double processing time.
- Confirm: ≥1 subject audio, 1 music file, ≥1 b-roll file. Hook comes later (after Gate 1).
- Print inventory to Franco before Step 2.

### Step 2: Transcribe the subject audio (NVIDIA Parakeet via sherpa-onnx)
Hugging Face and OpenAI model downloads are **blocked** in the cloud workspace and on Franco's machine. Whisper does not work here. Use NVIDIA Parakeet via sherpa-onnx (GitHub releases are allowed):

```
pip install sherpa-onnx soundfile librosa
# Download Parakeet model (one-time, cached):
# https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
# Run as: OfflineRecognizer.from_transducer(..., model_type="nemo_transducer")
```

**Parakeet's word timestamps drift 0.1–0.4s. Don't cut on them directly.** Use the **island method:**

1. Split audio into "islands" of speech using an energy threshold (−55 dB, 10ms frames, merge gaps <0.12s). Clean sources have digital silence (−83 dB) between phrases, so island edges are frame-accurate.
2. Re-run recognition on each island to get exact text per island. This also reveals fillers the full-file pass hides.
3. Cut at island edges where possible. For cuts inside an island, test each candidate cut by recognizing the piece alone and nudging start/end by 0.05s until the text is clean.

Run transcription in the cloud workspace (2 CPU, 7 GB). Franco's shell is smaller (2 CPU, 3 GB).

Exclude every voice that isn't the subject (interviewers, hosts, anyone reading subject's words).

### Step 3: Write the brief
Save to `working\<slug>\brief.md`:

```
SUBJECT:         <name>
ANGLE:           <one line: the story the speech tells>
HOOK PATTERN:    <#> (last used: <from hook_log>)
HOOK LINE:       <the exact narrated hook, 1–2 sentences, ~9–12 words>
SPEECH SELECTION:
  - Thought 1: "<words>" [source timestamp]
  - Thought 2: "<words>" [source timestamp]
  - Thought 3: "<words>" [source timestamp]
  ...
  (3–5 complete thoughts, reordered to answer the hook and build to the strongest line last)
ESTIMATED LENGTH: ~<N>s total (hook + pause + speech + ring-out + sign-off)
SPECIFIC CLAIMS: <list with verification result, or "none, narrative-level only">
```

**Speech selection rules:**
- Assemble 3–5 **complete thoughts**, never fragments. Never trim words that finish a thought.
- Reorder from anywhere in the source so they answer the hook and build to the strongest line last.
- End on a short button line if possible (Jon Jones: "Self-belief.").
- **Remove fillers:** "uh," "um," duplicated words ("on on", "an an", "just just"), false starts ("I think in order to... To"), interviewer-answer framing ("so, to answer your question").
- Skip off-topic sections (family, nutrition, favorite movie, sponsor reads).

### → GATE 1: Brief + hook takes
Send Franco the brief. In the same message:
- Generate 2 ElevenLabs takes of the hook line with Declan Sage.
- Give Franco the flow URL.
Franco approves the brief, listens to the takes, picks one, downloads, drops in `<Subject>\Speech\`. He confirms "approved, hook is in."

(Gates 1 and 2 from v2.2 merged into this single stop.)

### Step 4: Cut the speech
- Find each selected thought's words **in the actual file** (island method), never the raw Parakeet timestamps.
- Cut only at sentence boundaries (island edges), at the quietest point.
- Gaps inside a thought: 0.3–0.6s. Longer music-only pauses (1.3–1.6s) only between complete thoughts.
- Run recognition on every cut segment and confirm against the brief before continuing.

### Step 5: Build the audio timeline
- Hook narration from 0:00 (dry; music enters at the hook's last word).
- 1.3–1.6s music-only pause on a quiet shot.
- Speech starts; music drop lands on the first word of the speech.
- Music ducking through speech, up to ring-out, 1s fade under sign-off.

**Mix levels that worked on Jon Jones:**
| Section | Music level |
|---|---|
| Under hook | −15 dB |
| Pause (ramp-up) | −15 → 0 dB |
| Under speech | −9.5 dB |
| In short section pauses | −4 dB |
| Ring-out | −2.5 dB |
| Under sign-off | fade out over 1s |

Voice normalized to −16 LUFS. Final two-pass loudnorm → **−14 ±1 LUFS integrated, true peak below −1 dBTP**.

### Step 6: Find the music drop
- **Check real track length.** NEFFEX "Free Me" is 137s on disk but music ends at 87s (rest is silence). Scan with `ffprobe` + RMS envelope.
- Find drops with an RMS envelope scan at 100ms resolution. Snap to the nearest onset.
- **Known drops (log here as confirmed):**
  - `Free Me (Instrumental) - NEFFEX.mp3`: drop at **25.66s**. Music ends at 87s.
  - `Density & Time.mp3`: drop at 96.0s. Near-silence 94.2–95.9s doubles as the pre-payoff pause.
- Compute `track_start = drop_point − drop_tl` where `drop_tl` is the video-time of the speech's first word.
- If there's a second hit near the end of the track, time the ring-out so the final hit lands on the last shot before sign-off. On Jon Jones: hit at 83.2s in the track → 63.15s in the video.

### Step 7: Select, split, and assign b-roll
- **Scene detection:** PySceneDetect `ContentDetector` threshold 27. (Jon Jones: 78 shots from a 139s pack.)
- Some shots open with a dissolve from the previous shot — offset the start by ~0.25s when the first frame still shows the old scene.
- **No face-detection model is available.** Model downloads are blocked. Frame by eye instead:
  1. Build **contact sheets**: midframe of every shot with crop guides drawn on, 20 shots per image.
  2. Set `xc` (crop center x) per shot by looking at the sheet.
  3. Re-check with a sheet of rendered crops at 20/50/80% through each shot. On Jon Jones, 4 of 42 shots needed adjustment.
- **Keyframe `xc`** as `[time, xc]` points and interpolate linearly for shots where the subject moves across the frame.
- **Avoid close-ups where the face sits in the lower 35% of the frame** — captions can't move, so the caption would cover the face. Pick another shot for those lines.
- **Cut cadence:** every 1.5–3s on the beat / on speech breaths. Hook can be one long slo-mo shot (long-take exception). The pause before speech gets a quiet, music-only shot.

### Step 8: Reframe, speed-ramp, grade (LOCKED filter chain)

Output: 1080×1920, 30fps, H.264 yuv420p. No blurred background, no letterboxing.

Per-shot ffmpeg filter chain:
```
setpts=(PTS-STARTPTS)/SPEED,
fps=30,
crop=608:1080:X:0,
scale=1080:1920:flags=lanczos,
lut3d=file=/thestandard/templates/standard.cube,
setsar=1,
format=yuv420p
```

**Crop math:**
- `X = xc × 1920 − 304`, clamped between **0 and 1312**
- `xc` from Step 7

**Speed ramps:**
- Most b-roll: **0.5×** (slow-mo)
- Fast action: **0.6–0.7×**
- Hook shot: **0.64×** (worked on Jon Jones)

**LUT:** `standard.cube` at full strength on every shot.

**ffmpeg gotchas (don't lose an hour to these):**
- For slow-motion, `-t` must come **BEFORE** `-i`. After `-i` it caps the output and silently kills the slowdown.
- Use `minterpolate=mi_mode=blend` plus `tpad=stop_mode=clone` so slow-mo shots reach their full frame count.
- Rounding each shot to whole frames can drift the total by ~0.23s. Pad the last frame (tpad) so video length equals audio length before adding the sign-off.

### Step 9: Captions (LOCKED — one-caption-at-a-time)

**Timing:** forced-align on the FINAL cut audio, never the transcript. Rebuild after any audio change.

**Snap after silence:** any word following ≥120ms silence snaps to the first voiced sample (−55 dB voiced detector; the island method already gives you this). Tolerance ±0.25s. On Jon Jones, raw timestamps were up to 0.24s late; snapping fixed it.

**One caption on screen at any moment. This is the fix for the Jon Jones overlap bug:**
- Each chunk ends **at least 1 frame (33ms) before the next starts.** Never extend a chunk past the next one's start.
- If a chunk would be shorter than ~0.2s, **merge it with its neighbor** instead of extending it.
- When chunks are back-to-back (gap <0.15s), **no fade-out** — just hard-cut to the next chunk. Keep the pop-in.
- **QA check:** parse the final `.ass` file and assert no two Main-layer events overlap in time.

**Chunking that worked:** at most 3 words per chunk, at most ~900px wide at 200px Anton, break on punctuation and on gaps >0.35s. Measure widths with PIL using the real font. Scale overly long words down to fit 960px.

**Fix-up map for recognition errors** (keep this list; add entries per video as needed):
- `JOHN → JON`
- `GONE TO PAST → COME TO PASS`

**Style (LOCKED):**
- ALL CAPS throughout, no exceptions
- Font: Anton, loaded via `subtitles=overlay.ass:fontsdir=E:\FRANCO\The Standard\`
- Two styles: W (normal 200px), P (emphasis 225px, emotional peaks only, never small words like THE/WERE/I/A)
  ```
  Style: W,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0
  Style: P,Anton,225,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,5,0,5,40,40,0
  ```
- Every word is TWO ASS Dialogue lines (halo + text):
  ```
  Layer 0 (halo):
  {\pos(540,1380)\fad(60,80)\fscx78\fscy78\t(0,100,\fscx100\fscy100)\bord18\shad0\blur22\3c&H000000&\3a&H28&\1a&HFF&}WORD

  Layer 1 (text):
  {\pos(540,1380)\fad(60,80)\fscx78\fscy78\t(0,100,\fscx100\fscy100)\bord5\shad0\blur0.6}WORD
  ```
- **Position: x=540, y=1380, fixed every word, every video. Captions NEVER move.** Steady text matters more than clean chins. House rule.
- No drop shadow, no colored text, no boxes or backgrounds.

### Step 10: Watermark
- Text: `@thestandard.daily`
- Font: Anton, 44px, white, **25% opacity**, no outline
- Position: centered horizontally, y=300
- Static, every frame of the video except the sign-off card

### Step 11: Append sign-off card
Append `signoff_card.mp4` (1s). Music tail plays under it (fade from Step 5).

### Step 12: Render — two-tier

**Archive master** (keep locally in `working\<slug>\master.mp4`):

| Parameter | Value |
|---|---|
| Resolution | 1080×1920 (9:16) |
| Frame rate | 30fps |
| Codec | H.264 yuv420p |
| Bitrate | 10–12 Mbps |
| Audio | AAC stereo, 48kHz, −14 LUFS |

**Delivery file** (what goes to `outbox\` and the chat):

```
-b:v 2450k -maxrate 4000k -bufsize 8000k -c:a aac -b:a 160k
```
2-pass encode. Target ~20 MB for 65s. Fits under the 30 MB chat upload cap. TikTok re-encodes anyway; published quality is unchanged.

### Step 13: Automatic QA
- Length 61–70s
- Loudness −14 ±1 LUFS, true peak below −1 dBTP
- ≥6 frame grabs across the video — every one is a full 9:16 crop with text at x=540, y=1380
- **No two Main-layer caption events overlap** (parse the .ass file)
- Every caption all-caps, starts within ±0.15s of its word
- Watermark present on every frame except the sign-off card
- Hook narration matches approved brief; speech contains only subject's voice and matches approved brief
- Sign-off card is the last 1s
- Delivery file ≤30 MB

### → GATE 2: Final cut
Deliver three things:

1. **The delivery .mp4** (both to `outbox\<slug>_v<N>.mp4` via `device_commit_files` AND to the chat via `SendUserFile` — see §Delivery for the gzip workaround)
2. **TikTok caption file** (`outbox\<slug>_caption.txt`) in this exact shape:
   ```
   <one punchy line in the video's spirit — a statement, not the hook question> <one emoji>

   #<subject> #<subjectnickname> #<sport> #<league> #motivation #discipline #thestandard #<theme> #<mindset> #<extra>
   ```
   One line, one emoji, blank line, ~10 hashtags on one line. Always include **#thestandard**. **Never #fyp or #viral.**
   Example (Brady): `You don't have to be special. You just have to be what most people aren't. 🐐`
   Example (Jon Jones): `See it in your mind before anyone else sees it in the cage. 🧠`
3. **`hook_log.md` entry**: `<date> | <slug> | pattern #<N> | <Subject Name>`. Create the file with a header line if it doesn't exist.

If Franco wants a section-only change, re-render just that section first.

---

## Delivery (the gzip workaround — important)

The `device_commit_files` tool corrupts the first chunk of an .mp4 on large files. On Jon Jones, it injected 5,875 extra bytes into whichever piece contained the file header, and modified the staged copy in place. Checksum failed twice.

**The fix:**
1. Split the final .mp4 into ~12.5 MB pieces
2. **gzip the first piece** (gzip all pieces to be safe), generated fresh from the source
3. `device_commit_files` the pieces to `E:\FRANCO\The Standard\outbox\_parts\`
4. On Franco's computer (via `device_bash`):
   ```
   (gunzip -c part00.gz; cat part01 ... partN) > <slug>_v<N>.mp4
   ```
5. Verify `sha256sum` of the reassembled file matches the chat-side source hash before reporting done
6. Also `SendUserFile` the full delivery .mp4 to the chat (one 20 MB file, under the 30 MB cap)

Leftover piece files go in `outbox\_to_delete\` for Franco to clear — the AI can't delete files from Franco's computer.

---

## Approval gates

| Gate | Franco sees | Franco decides |
|---|---|---|
| 1: Brief + hook takes | Brief, speech selection, 2 ElevenLabs takes | Angle, hook line, speech selection, which take to use |
| 2: Final cut | Delivery .mp4 + caption file + hook log entry | Upload, or section fixes |

(Reduced from 3 gates in v2.2 → 2 gates in v2.3, since the narration script is now one line.)

---

## §16 — The `pipeline\` folder (reusable Python code)

The chat saves working build scripts to `E:\FRANCO\The Standard\pipeline\` so the next chat doesn't rewrite them. The SOP is always the source of truth; scripts implement it.

**Scripts to save there** (filenames descriptive, not frozen):
- `inventory.py` — walks subject folder, classifies files, prints inventory
- `transcribe_islands.py` — sherpa-onnx + Parakeet + island method
- `cut_speech.py` — cuts speech by sentence boundaries using island edges
- `find_music_drop.py` — RMS envelope scan + onset snap
- `mix_audio.py` — hook + pause + speech + ring-out, with ducking + two-pass loudnorm
- `scene_detect.py` — PySceneDetect wrapper
- `build_contact_sheet.py` — midframe + crop-guide images for `xc` selection
- `render_shots.py` — per-shot ffmpeg filter chain (crop, speed, LUT)
- `build_captions.py` — chunking + ASS layer code + overlap check
- `watermark.py` — the fixed `@thestandard.daily` overlay
- `render_master.py` — final concat + archive master encode
- `encode_delivery.py` — 2-pass low-bitrate encode
- `qa.py` — length, loudness, caption overlap, frame grabs
- `deliver.py` — gzip-split + commit + chat upload + checksum

**Guardrail (every cold start checks this):**
Before using a saved script, every new chat verifies the script implements the current SOP's rules. If a rule here changed, update the script to match this SOP, never the other way around. SOP wins.

If `pipeline\` doesn't exist on first run, create it as the chat goes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Captions overlap each other | Enforce "only one caption on screen" rule (§9). Parse the .ass and assert no overlap in QA |
| Caption covered subject's chin | Leave it. Captions never move. Fix by picking a different shot in §7 next time |
| Speech line cut wrong | Re-find words in actual file via island method, never raw Parakeet timestamps |
| ElevenLabs "Unusual activity" error | Retry once with `generations_count=1`; else hand off to Franco for web generation |
| Only 2 of 4 ElevenLabs takes succeeded | Request 2 takes next time, not 4 (rate-limited) |
| Hook mispronounces subject's name | Spell phonetically in ElevenLabs input only; re-generate that take |
| Video under 61s | Add one more thought to speech selection at Gate 1. Never pad with dead air |
| Video over 70s | Tighten speech, never cut mid-thought |
| Music drop misses first speech word | Re-calc `track_start`; verify drop point with RMS envelope scan |
| Music keeps playing past content | Check real music length with `ffprobe` — track may silence out early (NEFFEX Free Me is silent 87s onward) |
| Scene pack is low-res despite "4K" title | Report to Franco at inventory. Ask for a real 1080p+ pack before Gate 1 |
| Interviewer voice audible in subject speech | Re-cut. Only subject's voice allowed |
| Speech source has baked-in music | Try vocalremover.org / lalal.ai; if still dirty, pick another line |
| Whisper model download fails | Blocked. Use NVIDIA Parakeet via sherpa-onnx (§2) |
| Parakeet word timings drift 0.2–0.4s | Use island method, not raw timestamps |
| ElevenLabs download URL times out | Blocked. Franco handoff: generate → user downloads → user drops in `Speech\` |
| `device_commit_files` corrupts .mp4 header | Use gzip-and-split delivery workaround (§Delivery) |
| ffmpeg slow-mo not applying | `-t` must come BEFORE `-i`, not after |
| Slow-mo shot missing frames at end | Add `minterpolate=mi_mode=blend` + `tpad=stop_mode=clone` |
| Video length drifts from audio length | Round-off accumulation. Pad last frame with tpad |
| Can't delete files from Franco's computer | Move leftovers to `outbox\_to_delete\` for Franco to clear |

---

## What this SOP does NOT cover

- Uploading to TikTok (manual)
- Cover image / thumbnail (manual)
- Multi-subject or interview-format videos
- Sound effects (removed in v2.3 — not used)

---

## Version history

- **v2.3 (Oct 2026):** Format pivot — narration is now ONLY the hook (~4s); subject's real voice carries the rest. Target length 62–66s. Gates reduced from 3 to 2 (brief and script merged). SFX removed. `pipeline\` folder for reusable Python scripts, with SOP-as-source-of-truth guardrail. Local root moved to `E:\FRANCO\The Standard\` with templates at root; Dropbox is now a mirror, not primary. Voice ID locked (`kqVT88a5QfII1HNAEPTJ`, `eleven_multilingual_v2`). Caption overlap bug fixed (one-caption-at-a-time rule + .ass parse QA). NVIDIA Parakeet via sherpa-onnx replaces blocked Whisper. Island transcription method. Scene-pack real-resolution check at inventory. gzip-and-split delivery workaround for mp4 header corruption. TikTok caption format locked (one line + emoji + ~10 hashtags with #thestandard). Pre-flight checklist for Franco. Jon Jones run shipped at 64.6s, −14.2 LUFS.
- **v2.2 (Oct 2026):** Cold-start checklist. Voice locked to Declan Sage. Captions-never-move policy. Full ffmpeg filter chain, crop math, keyframing, speed ramps. ASS Dialogue layer code. RMS envelope scan for music drops. 0.1s silence padding on narration cuts. Sub-token alignment for low-accuracy recognizers. Two-tier render (archive + delivery). All five Brady operational kinks.
- **v2.1 (Oct 2026):** Preconditions block. Step 0 access check. Recursive walk + loose-file classifier + basename-dedupe + compilation flagging. Hash-dedupe. Recursive b-roll walk. Hook_log bootstrap.
- **v2.0 (Oct 2026):** Story format (5 beats, 70–80s, AI narration + real speech payoff).
- **v1.0 (Oct 2026):** Pure speech edits, 45–60s.
