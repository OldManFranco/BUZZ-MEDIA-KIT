# SOP Change Request: lessons from jon-jones-01 (Oct 19, 2026)

**For:** the maintenance chat that owns `NEW the-standard-tiktok-automation-sop.md`
**Ask:** Fold everything below into a clean **v2.3**. The current file has a "v2.2 FORMAT OVERRIDE" block pasted at the top. Merge it into the body, delete every section the override replaced, and keep one source of truth.
**Result of this run:** Shipped. 64.6s, −14.2 LUFS, uploaded by Franco. The one visible flaw was captions overlapping each other (section 6).

---

## 1. Format change (DECIDED by Franco, rewrite the SOP around it)

- **ElevenLabs narration is the hook question only (~4s). Everything else is the subject's real speech.**
- No narrated Setup, Turn, or Close. No narrated "Hold the standard."
- Structure: **Hook (Declan Sage) → 1.3–1.6s music-only pause → subject speech (music drop lands on the first word) → music ring-out (~3–4s) → sign-off card (1s).**
- Target length **62–66s** (floor 61s). The speech portion needs **~54–58s** of the subject's words.
- Remove or replace in the SOP:
  - The 5-beat table
  - Story rules about Setup and Turn
  - The 120–130 word narration target
  - The "story brief" Setup/Turn bullets
- **Merge Gate 1 and Gate 2.** The script is now one line, so a single gate covers it: hook line + speech selection with timestamps + estimated length.
- **Hook rules learned:**
  - Franco prefers **simple, direct questions** that the speech answers. Approved: "How did Jon Jones know he'd be champion... before anyone else did?"
  - Don't build the hook on side facts the payoff never returns to. A "his brothers were in the NFL" hook was rejected.
  - Avoid recent personal tragedies and controversies (legal issues, drug testing, retirement drama). Keep it a clean belief story.
- **Speech selection rules:**
  - Assemble 3–5 complete thoughts from anywhere in the source, reordered so they answer the hook and build to the strongest line last.
  - It's fine to end on a short button line (here: "Self-belief.").
  - **Remove fillers and disfluencies:** "uh," "um," duplicated words ("on on," "an an," "just just"), false starts ("I think in order to... To"), and interviewer-answer framing ("so, to answer your question").
  - Skip off-topic sections (daughters, nutrition, favorite movie, sponsor reads).

## 2. Folder conventions (DECIDED by Franco)

Local root is `E:\FRANCO\The Standard\`. Dropbox mirrors it at `/thestandard/incoming/<slug>/`.

```
The Standard\
  NEW the-standard-tiktok-automation-sop.md
  hook_log.md                       # created this run: date | slug | pattern # | subject
  Anton-Regular.ttf  standard.cube  signoff_card.mp4   # templates live at ROOT, not /templates/
  <Subject Name>\                   # e.g. "Jon Jones" (not the slug)
    Speech\                         # subject audio + the ElevenLabs hook file
    Scene Pack\                     # b-roll compilation(s)
    Music\                          # one YouTube Audio Library track, ORIGINAL filename
  working\<slug>\                   # brief.md, transcript.txt, speech_words.json
  outbox\                           # final .mp4 + <slug>_caption.txt
```

- Franco drops the downloaded ElevenLabs hook into **`Speech\`** (named like `eleven labs jon jons hook.mp3`). Classifier rule: any file in `Speech\` whose name contains `eleven`, `hook`, or `narration` is the hook. Everything else in `Speech\` is subject audio.
- If Franco replaces a source file mid-run, re-list the folder and re-stage. Don't reuse the old copy.

## 3. Voice and ElevenLabs (lock these values)

```
ELEVENLABS_VOICE_NAME:  Declan Sage
ELEVENLABS_VOICE_ID:    kqVT88a5QfII1HNAEPTJ
ELEVENLABS_MODEL:       eleven_multilingual_v2   ← generated the first approved video, LOCK IT
STABILITY / SIMILARITY / STYLE: 0.50 / 0.75 / 0.20
```

- **The connector can generate, but the AI cannot download the result.** The audio file links (storage.googleapis.com) are blocked from both the cloud workspace and Franco's computer.
  - The procedure: generate in the connector, give Franco the flow link, Franco listens, downloads his pick, and drops it in `Speech\`. Write this into the SOP as the normal path, not a fallback.
- **Ask for 2 takes, not 4.** 2 of 4 takes failed with a rate-limit error on this run.
- Takes run ~66 credits each for a ~4s line.
- Spell names the way they should sound. Recognition heard "John Jones" for "Jon Jones"; that's a homophone, fine.

## 4. Transcription (the SOP's Whisper path does not work here)

- Hugging Face and OpenAI model downloads are **blocked** in the cloud workspace and on Franco's machine. faster-whisper and openai-whisper both fail.
- **What worked:** `pip install sherpa-onnx soundfile librosa`, then download the NVIDIA Parakeet model from GitHub releases. GitHub is allowed.
  `https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2` (~480 MB)
  Run it as `OfflineRecognizer.from_transducer(..., model_type="nemo_transducer")`.
- **Its word timestamps drift 0.1–0.4s.** Don't cut on them directly. Method that worked:
  1. Split the audio into **"islands"** of speech using an energy threshold (−55 dB, 10ms frames, merge gaps < 0.12s). Clean sources have digital silence (−83 dB) between phrases, so island edges are exact.
  2. Re-run recognition on each island to get exact text per island. This also reveals the fillers the first full pass hides.
  3. Cut at island edges where possible. For cuts inside an island, test each candidate cut by recognizing the piece alone, and nudge the start or end by 0.05s until the text is clean.
- Run it in the cloud workspace (2 CPU, 7 GB). Franco's computer shell is smaller (2 CPU, 3 GB).

## 5. Music

- **Check the track's real length.** "Free Me – NEFFEX" is 137s on disk, but the music ends at **87s**; the rest is silence.
- Find drops with a loudness-jump scan, then snap to the nearest onset. Here the best drop was at **25.66s**: a quiet break before it sits under the hook, and full energy lands on the first speech word.
- If there's a second break-and-hit near the end of the track, time the ring-out so the final hit lands on the last shot before the sign-off card. That worked well here (hit at 83.2s in the track → 63.15s in the video).
- **Mix levels that worked:**
  - Voice normalized to −16 LUFS.
  - Music −15 dB under the hook, ramping up through the pause.
  - Music −9.5 dB under speech, about −4 dB in 1s section pauses.
  - Music −2.5 dB in the ring-out, then a 1s fade under the sign-off.
  - Final pass with two-pass loudnorm → −14.2 LUFS, true peak −1.4.
- **SFX are synthesized**, since there's no SFX library in templates: a band-passed noise whoosh (0.7s) into the drop, a low sine-sweep impact on the drop, and quieter whooshes at the 1s section pauses.
  - **Suggestion:** Franco adds `whoosh.wav` and `impact.wav` to the templates for a consistent sound.

## 6. Captions: the overlap bug (Franco noticed it, fix in v2.3)

**Symptom:** "a caption would appear behind another caption" a few times during fast speech.

**Cause (from the build script):**
1. Each chunk was forced to last at least 0.25s (`if end - start < 0.25: end = start + 0.25`). Quick chunks then ran past the start of the next chunk, so two captions were on screen at once.
2. The 80ms fade-out overlapped the next chunk's 60ms fade-in plus the 100ms pop. Even correctly timed chunks briefly showed two captions.
3. Every chunk has two layers (halo + main). A lingering halo sits behind the new word, which makes it read as "behind."

**Required fix (put in the SOP as a rule):**
- **Only one caption on screen at any moment.** Each chunk ends at least 1 frame (33ms) before the next starts. Never extend a chunk past the next one's start.
- If a chunk would be shorter than about 0.2s, **merge it with its neighbor** instead of extending it.
- When chunks are back-to-back (gap < 0.15s), **no fade-out**; just hard-cut to the next chunk. Keep the pop-in.
- QA check: parse the .ass file and assert that no two Main events overlap in time.

**Other caption notes:**
- **Snap the first word after every pause to the island start.** Raw timestamps were up to 0.24s late. With snapping, line starts landed within ±0.15s.
- Chunking that worked: at most 3 words, at most ~900px wide at 200px Anton, break on punctuation and on gaps over 0.35s. Measure widths with PIL using the real font. Scale overly long words down to fit 960px.
- Fix-up map for recognition errors in captions: JOHN→JON, "GONE TO PAST"→"COME TO PASS".
- **Faces under the caption line:** with a 1280×698 source, the vertical crop already uses the full height, so you can't reframe up or down. Two short moments had the caption over part of the face.
  - Fix: during shot selection, avoid close-ups where the face sits in the lower 35% of the frame, or use a different shot for those lines.

## 7. Video and scene pack

- **Check real resolution at inventory, not by filename.** "JON JONES 4K 60 FPS ... UPSCALED WITH TOPAZ" is actually **1280×698 at 30fps**. Cropping to 9:16 means a 393×698 slice blown up 2.75×, which looks soft. Report this to Franco before Gate 1 so he can find a better pack.
  - **Pre-flight ask for Franco:** prefer real 1080p+ packs. Check with any media-info tool.
- **No face-detection model is available** (OpenCV Haar files and MediaPipe solutions are missing, and model downloads are blocked). Framing method that worked:
  1. Build **contact sheets**: the middle frame of every shot with crop guides drawn on, 20 per image.
  2. Look at them and set a crop center x per shot by hand.
  3. Re-check with a sheet of rendered crops at 20/50/80% through each shot. Fixed 4 of 42 shots this way.
- **Scene detection:** PySceneDetect, ContentDetector threshold 27 → 78 shots from a 139s pack.
  - Some shots open with a dissolve from the previous shot. Offset the start by ~0.25s when a shot's first frame shows the old scene.
- **ffmpeg gotchas:**
  - For slow-motion, `-t` must come **before** `-i`. After `-i` it caps the output and silently kills the slowdown.
  - Use `minterpolate=mi_mode=blend` plus `tpad=stop_mode=clone` so slow-mo shots reach their full frame count.
  - Rounding each shot to whole frames drifted the total by 0.23s. Pad the last frame (tpad) so video length equals audio length before adding the sign-off.
- **Shot cadence that worked:** 42 shots in 63.6s.
  - The hook is one shot slowed to 0.64× (approved long-take exception).
  - The music-only pause is the subject walking into the cage.
  - Belt and celebration shots go under "see your beliefs come to pass."

## 8. Delivery to Franco's computer (important, cost real time)

- **The file-copy tool corrupts the first chunk of an .mp4.** It injected 5,875 extra bytes into whichever piece contained the file's header, and it also changed the staged copy in place. The checksum failed twice.
- **Fix that worked:**
  1. Split the final file into 12.5 MB pieces.
  2. **gzip the first piece** (gzip all of them to be safe), generated fresh from the source file.
  3. Copy them over, then on the computer: `(gunzip -c part00.gz; cat part01 ... partN) > final.mp4`.
  4. Verify sha256 matches before reporting done.
- Files on Franco's computer can't be deleted by the AI. Leftover pieces go in `outbox\_to_delete\` for Franco to clear.

## 9. TikTok caption format (DECIDED by Franco, use exactly this shape)

```
<one punchy line in the video's spirit (a statement, not the hook question)> <one emoji>

#subject #subjectnickname #sport #league #motivation #discipline #thestandard #theme #mindset #extra
```

- One line, one emoji, blank line, then **about 10 hashtags on one line**. Always include **#thestandard**. No #fyp or #viral.
- Approved example (Brady): "You don't have to be special. You just have to be what most people aren't. 🐐"
- This run's caption: "See it in your mind before anyone else sees it in the cage. 🧠" + `#jonjones #bonesjones #ufc #mma #motivation #discipline #thestandard #selfbelief #mindset #champion`

## 10. Make the next run faster

1. **Franco's pre-flight checklist** (put at the top of the SOP):
   - Subject folder has `Speech\`, `Scene Pack\`, and `Music\`, with one file minimum each.
   - The scene pack is really 1080p or higher (check it, don't trust the title).
   - The speech source is a clean interview or speech with no music bed.
   - Say "run the pipeline on <Subject>."
2. **Two stops for Franco, not four:**
   - **Stop 1:** hook line + speech selection, with the hook takes already generated in ElevenLabs so he approves and downloads in one visit.
   - **Stop 2:** the final cut.
3. **Save the build scripts** (island transcription, speech cutter, mixer, shot plan, caption builder, delivery) into `The Standard\pipeline\` so the next chat reuses them instead of rewriting them. Ask Franco to approve that folder.
4. Keep the per-run `working\<slug>\` files (brief, transcript, word timings) for re-cuts.
5. Update the `Troubleshooting` table with: blocked Whisper downloads, blocked ElevenLabs downloads, rate-limited takes, header corruption on .mp4 copies, mislabeled 4K packs, and the caption overlap.

## 11. Open questions for Franco (maintenance chat should ask)

- Keep synthesized SFX, or will he add `whoosh.wav` and `impact.wav` to templates?
- OK to create `The Standard\pipeline\` for reusable scripts?
- Should the hook-pattern rotation (5 patterns) stay, now that the hook is the only narrated line?
