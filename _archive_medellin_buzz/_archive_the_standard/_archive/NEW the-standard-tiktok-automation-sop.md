# The Standard — TikTok Automation SOP (v2.1: Story Format)

**Purpose:** The complete, executable procedure for producing a The Standard TikTok. Every video follows the story format below: AI narration tells a short story about a sports figure, then the figure's own real speech pays it off. When any Claude chat is asked to produce a new The Standard video, follow this SOP exactly.

**Supersedes:** SOP v1 (pure speech edits) and any conflicting lines in *The Standard — Video Template Spec*. Where the template and this SOP disagree (length, caption case, structure), **this SOP wins.**

> ## ⚠ v2.2 FORMAT OVERRIDE (Oct 19, 2026, Franco): this wins over everything below
> - **ElevenLabs narration = the HOOK ONLY** (one question, ~3–4s). No narrated Setup, Turn, or Close, and no narrated "Hold the standard."
> - **Everything after the hook is the subject's real speech audio**, built from complete thoughts, ~55–60s of it.
> - **Structure:** Hook (Declan Sage) → music-only pause 1.3–1.6s → subject speech with the music drop on its first word → music ring-out → sign-off card.
> - **Length:** ~62–66s total (hard floor 61s still applies).
> - Gate 1 = hook + speech selection (with timestamps). Gate 2 = hook wording only. Narration word target (~120–130) no longer applies.

**Channel:** @thestandard.daily · Tagline: *Hold the standard.*

---

## Trigger

Use this SOP when Franco says anything like: "run the pipeline on [slug]," "new Standard video," "next TikTok," or drops a new folder into `/thestandard/incoming/` and asks for a build.

---

## Preconditions (check BEFORE starting)

If any of these aren't met, the pipeline can't finish. Report what's missing in the first reply, before Gate 1, so Franco doesn't waste work.

1. **Local folder access.** The slug's `incoming/<slug>` folder must be reachable through a locally connected folder on Franco's computer — the Dropbox connector alone will NOT work (the egress proxy blocks `dl.dropboxusercontent.com`, so direct Dropbox downloads fail). Franco adds the folder via Claude desktop app → "+" → his local Dropbox sync folder (e.g. `C:\Users\...\Dropbox\thestandard\incoming\<slug>` on Windows, `~/Dropbox/thestandard/incoming/<slug>` on Mac).

2. **ElevenLabs voice is locked.** The voice block in "The Standard voice" section (below) must have real values, not `[TO BE LOCKED]` placeholders. If it's still unlocked, STOP IMMEDIATELY and tell Franco to pick the voice first (see "Voice selection"). Do not run Gate 1 or Gate 2 — all narration work will be wasted until the voice is locked.

3. **Templates folder has all three assets:** `Anton-Regular.ttf`, `standard.cube`, `signoff_card.mp4`. If any are missing, say which and ask Franco to drop them in before continuing.

---

## The format: 5 beats, 70–80 seconds

Target **~75 seconds**. Hard floor **61 seconds** (TikTok Creator Rewards requires videos over 60s). Hard ceiling **85 seconds**.

| Beat | Time | Audio | What happens |
|------|------|-------|--------------|
| **1. Hook** | 0–3s | Narration (dry or very low music) | One narrated question or statement that opens a loop. Over the strongest single shot of the subject. Must make the viewer ask "what happened?" or "how?" |
| **2. Setup** | 3–25s | Narration + music bed | Narration builds the story: where they came from, what stood in the way, why it was hard. B-roll of early career / the struggle. |
| **3. Turn** | 25–47s | Narration + music building | "So what did he do?" The change: the work, the mindset, the decision. B-roll of training, grind, the rise. |
| **4. Payoff** | 47–65s | **The subject's own real voice** + music drop | Music-only pause (1.3–1.6s) on a quiet shot, then the drop lands on the first word of the real speech clip. 15–20 seconds of the subject. This is the emotional peak. |
| **5. Close** | 65–74s | Narration + music ring-out | One takeaway line, then the signature tag: **"Hold the standard."** |
| Sign-off | last 1s | Music tail | `signoff_card.mp4` |

Timings are targets, not hard cuts. Beats flex ±3s to land on complete sentences. The payoff must never be cut mid-thought to hit a time.

---

## Story rules: the hook and claims

### Hook patterns (rotate, never use the same one twice in a row)

1. **The "how" question:** "How did a kid from Philadelphia become the most feared scorer in the world?"
2. **The "why" question:** "Why did Kobe Bryant refuse to take a single day off?"
3. **The "what made" question:** "What made Tom Brady different from every quarterback drafted ahead of him?"
4. **The contrast statement:** "Everyone said he was too small. He became a champion." (narrative-level, not a stat)
5. **The habit statement:** "He trained while everyone else was asleep. Here's why."

Keep a running log of which pattern each video used (`/thestandard/hook_log.md`, one line per video: date, slug, pattern #). Check it before writing a new hook.

### Claims: what needs checking and what doesn't

The story is told at the **narrative level**, not the statistics level. That keeps it fast and keeps it accurate.

| Type | Example | Rule |
|------|---------|------|
| **Narrative-level** | "He was overlooked." "He outworked everyone." "He became one of the greatest ever." | **Free.** No check needed. Widely known, not testable. |
| **Specific / testable** | Numbers, dates, scores, draft position, team names tied to a moment, quotes attributed to someone else | **Must be checked** with a quick web search before Gate 1. If it can't be confirmed in 2 minutes, cut it or rewrite it at the narrative level. |

**Never invent a specific moment.** If you don't know exactly what happened, say it in general terms. "He missed shots that would have ended most careers" is fine. "He went 0-for-4 in his rookie debut" is not, unless it's verified.

The pipeline reports at Gate 1: "Specific claims in this brief: [list], all verified" or "none, narrative-level only."

---

## The Standard voice (locked)

All narration uses **one ElevenLabs voice, forever.** That voice is part of the brand. Do not change it, substitute it, or "try a different one for this video."

```
ELEVENLABS_VOICE_NAME:  Declan Sage
ELEVENLABS_VOICE_ID:    kqVT88a5QfII1HNAEPTJ
ELEVENLABS_MODEL:       eleven_multilingual_v2  (to confirm/lock after first approved video)
STABILITY:              0.50
SIMILARITY_BOOST:       0.75
STYLE_EXAGGERATION:     0.20
```

**Voice character:** gritty, mid-range male, documentary feel. Measured pace, not hype-man, not smooth podcast host.

**Voice selection (one-time, before the first story video):** Franco picks 3–4 candidates on elevenlabs.io, generates the same test line in each ("How did a kid nobody believed in become the hardest worker in the league?"), picks one, and fills in the block above. Until it's filled in, the pipeline stops at Gate 2 and asks.

**How narration gets generated (check in this order):**
1. **ElevenLabs connector available in the chat:** pipeline generates narration directly with the locked voice and settings.
2. **No connector:** after Gate 2 approval, the pipeline gives Franco the final narration script as one clean block of text. Franco pastes it into ElevenLabs with the locked voice, downloads it, and drops `narration.mp3` into the video's folder. Pipeline continues from there.

**Pacing:** write for ~140 words per minute. Narration covers Hook + Setup + Turn + Close (about 55s), so **~120–130 words total.** Control pauses with punctuation and line breaks, not special markup.

---

## Folder structure

```
/thestandard/
  hook_log.md                  # one line per video: date, slug, hook pattern #
  /incoming/
    /[slug]/                   # e.g. "kobe-mamba-02", lowercase, dashes, no spaces
      notes.txt                # optional: subject, angle ideas, anything specific
      /speech/                 # the subject's REAL voice: raw interviews/speeches are fine
        source1.mp4 (or .mp3/.m4a)
        source2.mp4 ...
      music.mp3                # one YouTube Audio Library track
      narration.mp3            # only if generated manually (see "The Standard voice")
      /broll/                  # EITHER sorted into beats...
        /hook/  /setup/  /turn/  /payoff/
                               # ...OR one or more long compilations dropped loose in /broll/
  /working/[slug]/             # pipeline workspace, auto-created
  /outbox/                     # finished videos
  /templates/
    Anton-Regular.ttf
    standard.cube
    signoff_card.mp4
```

**B-roll sorting is optional.** If Franco drops one long compilation, the pipeline splits it into shots automatically (scene detection) and assigns shots to beats itself. Sorted subfolders just give Franco more control.

---

## What Franco provides per video

- **Subject** (and optionally an angle: "how he outworked everyone," "the comeback," etc.) in the chat message or `notes.txt`
- **Speech source(s)** in `/speech/`: raw interviews, speeches, pressers. Full-length originals preferred over compilations (compilations have baked-in music). If a line only exists in a compilation, try a vocal remover first (vocalremover.org, lalal.ai).
- **Music** (`music.mp3`): YouTube Audio Library. Cinematic build or dark hybrid orchestral. Needs a clear drop or swell.
- **B-roll** in `/broll/`: subject footage covering early career/struggle, training/grind, peak moments. Muted scene packs are ideal.

Franco does **not** provide: narration script, captions, grade, watermark, sign-off, SFX, TikTok caption, hashtags.

---

## The pipeline

Stack: Python + ffmpeg + whisper (or faster-whisper) + librosa + scene detection + face/subject detection. Install what's missing on first run.

### Step 0: Access check
Before anything else:
- Confirm `incoming/<slug>` is reachable through a connected local folder (not through the Dropbox connector — see Preconditions #1). If only the Dropbox connector is available, stop and ask Franco to add the folder in the desktop app.
- Confirm the templates folder is reachable with all three assets.
- Confirm the ElevenLabs voice block is locked (not `[TO BE LOCKED]`).

If any of these fail, report what's missing and stop. Do not proceed to Step 1.

### Step 1: Discover and classify inputs
- **Walk `/incoming/<slug>/` recursively** (files may be nested in subfolders like `tom brady files/`, `Tom Brady Rare Clips/`, etc. — don't assume files sit at the slug root).
- **Classify loose files** when `/speech/` or `/broll/` subfolders aren't present:
  - `.mp3` / `.m4a` / `.wav` / `.aif` → treat as speech source, except any file whose basename matches `music*` (case-insensitive) → that's the music track.
  - `.mp4` / `.mov` / `.webm` without a speech-like basename → b-roll.
  - `.mp4` with a speech-like basename (interview, speech, press, podcast, etc.) → speech source (extract audio).
- **Deduplicate** by basename pattern: files whose names differ only by `" (1)"`, `" (2)"`, `" copy"`, `" copy 2"`, trailing numbers, etc. are duplicates. Keep one, log the dupes.
- **Flag compilations.** File names containing `compilation`, `mindset`, `motivation`, `best of`, `top X`, `moments` → likely have baked-in music, interviewer voices, or music beds under the speech. Use only if a clean subject-only line can be isolated; otherwise skip and tell Franco.
- Read `notes.txt` if present.
- Read `hook_log.md` if it exists. If it doesn't exist yet, that's fine — Gate 3 will create it with this video's entry.
- Confirm the discovery produced: at least one speech source, a music file, at least one b-roll clip. If anything's missing, stop and tell Franco exactly what.
- Before moving to Step 2, print the inventory (classified files, dupes dropped, compilations flagged) so Franco can sanity-check it.

### Step 2: Transcribe the speech sources
- **Dedupe first.** Hash each audio source (sha256 or md5 of the file bytes). Skip exact duplicates before transcribing — on the Brady run, Dropbox "Add to folder" produced two 51 MB and two 117 MB dupes that would have burned transcription time. The basename-pattern dedupe in Step 1 catches most but not all; this is the final filter.
- Run speech recognition on every remaining source **as downloaded**, with word-level timestamps. **Never trust YouTube caption timestamps** for the downloaded file (a 2-second drift caused a wrong cut on the first run).
- If whisper can't download its model: pull the YouTube transcript for line selection, force-align that text to the actual audio for word timings, then confirm by recognition.
- Identify and exclude every voice that isn't the subject: interviewers, hosts, anyone reading the subject's words aloud.

### Step 3: Write the story brief
Save to `/working/[slug]/brief.md`:

```
SUBJECT:         [name]
ANGLE:           [one line: the story this video tells]
HOOK PATTERN:    [# from the pattern list] (last used: [from hook_log])
HOOK LINE:       [the exact narrated hook]
SETUP:           [3–5 bullet story points, narrative-level]
TURN:            [3–5 bullet story points, narrative-level]
PAYOFF CLIP:     [the subject's real words, grouped as complete thoughts,
                  with source file + timestamps, ~15–20s total]
CLOSE LINE:      [one takeaway line] + "Hold the standard."
SPECIFIC CLAIMS: [list with verification result, or "none, narrative-level only"]
```

**Payoff selection rules:**
- Group lines into **complete thoughts**, never isolated fragments.
- **Never trim the words that finish a thought.** (First run: cutting "we were" and "will never be retired" broke the lines and they had to go back in.) Keep the whole sentence unless Franco says otherwise.
- Pick lines that pay off the specific story told in Setup/Turn, not just the most famous quote.

### → GATE 1: Brief
Send the brief. Franco approves, edits the angle, or swaps the payoff clip.

### Step 4: Write the narration script
Save to `/working/[slug]/script.md`. Hook + Setup + Turn + Close, ~120–130 words, written to be heard (short sentences, concrete images, no lists). Show the estimated time per beat. Include the payoff clip text in place (marked as SUBJECT VOICE) so Franco reads the full flow.

### → GATE 2: Script
Franco approves or edits wording. Once approved, the narration text is frozen.

### Step 5: Generate narration
Per "The Standard voice" section (connector, or Franco drops `narration.mp3`). Run recognition on the narration and confirm it matches the approved script word-for-word. Re-generate any line with a mispronunciation (names especially).

### Step 6: Cut the payoff clip
- Find each payoff line's words **in the actual file** before cutting.
- Cut **only at sentence boundaries**, at the quietest point near the word boundary.
- Gaps inside a thought: **0.3–0.6s**.
- After cutting, run recognition on every segment and compare against the approved brief before going further.

### Step 7: Build the audio timeline
- Narration from 0:00 (Hook through Turn), then a **music-only pause of 1.3–1.6s**, then the payoff clip, then narration Close.
- **Longer music-only pauses (1.3–1.6s) only between complete thoughts.** Best spots: after the hook, and right before the payoff. Never mid-sentence. Don't add long pauses at every join (pushes length over target).
- **Music:** enters right after the hook. Find the track's biggest drop and **align it to the first word of the payoff clip**; start the track at whatever offset makes that happen, so its build sits under the Turn.
- **Ducking:** music sits −8 to −10 dB under narration, −6 to −8 dB under the payoff speech, comes up during music-only pauses, rings out under the Close.
- **Loudness:** final mix −14 LUFS integrated, true peak below −1 dBTP.

### Step 8: Select and assign b-roll
- **Walk `/broll/` recursively** too — compilations are often nested two levels deep inside subfolders Franco didn't flatten (e.g. `/broll/tom brady files 2/Tom Brady Rare High Quality Clips.mp4`). Discover all video files under `/broll/` regardless of depth.
- Split compilations into shots with scene detection. Frame each shot around the subject using the middle of the shot; the crop follows the subject through the shot.
- Assign shots to beats by content: struggle/early footage for Setup, training/grind for Turn, peak/iconic moments for Payoff.
- **Hook:** the single strongest image of the subject.
- **Cut cadence:** every 1.5–3s, on narration breaths or music beats.
- **Long-take exception:** a single take over 3s is allowed when the scene tells the story (first run: the 8s fall-and-wave scene). Time its key moments to the words.
- **The pause before the payoff** gets a quiet, music-only shot (first run: the shot clock hitting 0.0).

### Step 9: Reframe, grade
- Reframe everything to 1080×1920.
- Apply `/templates/standard.cube` identically to every shot.

### Step 10: Captions (locked style, applies to narration AND speech)
- Timing comes from word timings of the **final cut audio**. Rebuild captions every time a cut changes.
- **ALL CAPS throughout.** No switching to sentence case, ever.
- **Font:** Anton (`/templates/Anton-Regular.ttf`) at **200px**.
- **Peak words:** **225px** (+12%) instead of a case change. Small words ("were," "tried," "I," "the," "a," "and") never count as peaks.
- **Treatment:** 5px black outline + soft dark halo behind the text (wide blurred dark border, ~85% opacity). No hard drop shadow. No colored text.
- **Position: one fixed spot for every word, every video: lower third, y = 1380 (of 1920), centered.** Text never moves between shots.
- **Animation:** 60ms fade in, 80ms fade out, quick pop from 78% → 100% scale over 100ms.
- **QA:** each line's first caption starts within ±0.15s of the spoken word (slightly early is fine).

### Step 11: Watermark
- **Text:** `@thestandard.daily`
- **Font:** Anton, 44px, white, **25% opacity**, no outline
- **Position:** centered horizontally, **y = 300** (below TikTok's top tabs, well clear of the side icons and the caption line at 1380). Centered placement can't be cropped out without cropping the video itself.
- **Static:** same spot, every frame, every video.
- **Visible for the whole video except the sign-off card.**

### Step 12: SFX
- Subtle whoosh on major beat transitions (Setup→Turn, Turn→Payoff pause). None during the hook.
- One impact hit on the payoff drop.
- Keep it subtle. Voice is the hero.

### Step 13: Append sign-off card
Append `/templates/signoff_card.mp4` (1s). Music tail plays under it.

### Step 14: Render
| Parameter | Value |
|-----------|-------|
| Resolution | 1080 × 1920 (9:16) |
| Frame rate | **30fps** |
| Codec | H.264, .mp4 |
| Bitrate | **10–12 Mbps** |
| Audio | AAC stereo, 48kHz, −14 LUFS |
| Length | 70–80s (floor 61s, ceiling 85s) |
| Expected file size | ~90–120 MB for 75s (normal; TikTok accepts up to 287 MB) |

### Step 15: Automatic QA
Report pass/fail on each:
- Length is between 61s and 85s
- Loudness −14 ±1 LUFS, true peak below −1 dBTP
- Every caption at y = 1380, all caps, starts within ±0.15s of its word
- No caption covers the subject's face (reframe the shot, never move the caption)
- Watermark present on every frame except the sign-off card
- No shot over 3s except approved long-take exceptions
- Narration matches approved script (recognition check)
- Payoff clip contains only the subject's voice and matches the approved brief
- Sign-off card is the last 1s
- File plays cleanly start to finish

### → GATE 3: Final cut
Deliver:
1. **The final .mp4**
2. **TikTok caption:** the hook line or payoff line as the opener, optional source credit ("Speech: [event, year]"), and **5–10 relevant hashtags** (subject, sport, team, mindset/discipline tags). **No #fyp, no #viral.**
3. **One-line log entry** for `hook_log.md`. **If `hook_log.md` doesn't exist yet** (first story-format video), create it with a one-line header plus this video's entry: `date | slug | hook pattern # | subject`.

If Franco requests changes that only affect one section, re-render and send a preview of **just that section** before re-rendering the full video.

---

## Delivery

The Dropbox connection can't write video files, so finished .mp4s reach Franco one of two ways:

1. **Linked computer (preferred):** write the final to Franco's local `/thestandard/outbox/`. Files over 30 MB must be split into chunks, sent, rejoined on his computer, and **verified with a checksum match** before reporting done.
2. **In the chat:** send the .mp4 as a file in the conversation. Franco downloads it on any device.

Always tell Franco which route was used and where the file is.

---

## Approval gates summary

| Gate | Franco sees | Franco decides |
|------|-------------|----------------|
| 1: Brief | Story brief + claim check | Angle, hook, payoff clip |
| 2: Script | Full narration script with timings | Wording, final. Frozen after approval |
| 3: Final | .mp4 + TikTok caption + hashtags | Upload, or section fixes |

All three gates stay strict for the first 10 story-format videos. After that, Franco may combine Gates 1 and 2.

---

## Tunable parameters (pass via notes.txt or chat)

- Angle / story focus
- Hook pattern (default: next in rotation)
- Target length (default 75s, range 70–80s)
- Payoff length (default 15–20s)
- Specific b-roll shot for a specific moment
- Music choice if several are provided

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Payoff line cut wrong / wrong words | Re-find the words in the actual file (not YouTube timestamps), re-cut, re-run recognition |
| Narration mispronounces a name | Re-generate that line; spell it phonetically in the ElevenLabs input only |
| Video under 61s | Extend Setup/Turn narration slightly at Gate 2. Never pad with dead air |
| Video over 85s | Tighten narration first, then payoff, never mid-thought |
| Music drop misses the payoff | Re-calculate the track offset so the drop lands on the payoff's first word |
| Caption covers face | Reframe the shot. Caption position never moves |
| Interviewer voice audible in payoff | Re-cut. Only the subject's voice is allowed |
| Speech source has baked-in music | Try a vocal remover; if still dirty, choose another line |

---

## What this SOP does not cover

- Uploading to TikTok (manual)
- Cover image / thumbnail (manual)
- Choosing the ElevenLabs voice (one-time, Franco)
- Multi-subject or interview-format videos

---

## Version history

- **v2.2 (Oct 19, 2026):** Narration cut to the hook only; rest of the video is the subject's real speech, ~1 minute total. Per-video folders use /Speech/, /Scene Pack/, /Music/ (original filenames). Voice locked: Declan Sage.

- **v2.1 (Oct 2026):** Operational fixes from first story-format run (tom-brady-01). Preconditions block (local folder access, voice lock, templates) checked before Gate 1. New Step 0 access check. Step 1 recursive walk + loose-file classifier + basename-dedupe + compilation flagging. Step 2 hash-dedupe before transcription. Step 8 recursive b-roll walk. Gate 3 bootstraps `hook_log.md` on first run.
- **v2.0 (Oct 2026):** Story format (5 beats, 70–80s, AI narration + real speech payoff). Locked Standard voice. Narrative-level claims rule. Watermark. All fixes from the first run (kobe-mamba-01): source-audio handling, complete-thought payoff selection, pause rules, locked caption style and fixed position, music-drop alignment, scene detection for compilations, 30fps, bitrate/size conflict resolved, TikTok caption + hashtags at Gate 3, chunked delivery with checksum.
- **v1.0 (Oct 2026):** Pure speech edits, 45–60s.
