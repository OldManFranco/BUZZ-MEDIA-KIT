# SOP v2.3 change requests — from the michael-jordan-01 run (2026-10-21)

## 1. Folder convention: `Narration/` sibling, not inside `Speech/`

**Observed:** Franco put the ElevenLabs hook at
`<Subject>\Narration\eleven labs mj hook.mp3` — a NEW subfolder sibling to
`Speech/`, `Scene Pack/`, `Music/` — rather than inside `Speech/` with the
keyword classifier (`eleven`/`hook`/`narration` in the basename).

**Why it's better:**
- Separates subject's real voice from AI-generated narration structurally,
  not by filename keyword.
- Removes a classifier edge case (what if the subject's own name starts
  with "Narr…" or a speech file happens to contain "hook").
- One less rule for Franco to remember on dropoff.

**SOP sections to update:**
- §Folder structure — add `Narration/` sibling, document.
- §Pipeline Step 1 (classifier rule) — `Narration/*` → hook. Keep the
  `Speech/*hook*|*eleven*|*narration*` fallback for legacy habit.
- §What Franco provides per video — "Hook mp3 (after Gate 1): dropped in
  `<Subject>\Narration\`" (not `Speech\`).

**Code change made:** `pipeline/inventory.py` classifier now checks
`Narration/` first and keeps the Speech-keyword fallback.

## 2. Delivery corruption bug: STILL PRESENT (confirmed in this run)

Re-tested on michael-jordan-01: a direct `device_commit_files` of the
21.4 MB delivery mp4 produced a file with **5,875 extra bytes** on Franco's
PC (sha mismatch). Identical byte-count delta to Jon Jones. Not a Jones-only
bug — it's a reliable corruption in the current commit path for large mp4.

**Workaround still correct:** split + gzip + commit pieces + reassemble
on PC. This run's `deliver.py` writes `reassemble.py` (pure stdlib) +
`reassemble.bat` (double-click wrapper) into `outbox\_parts\` — Franco runs
either and the file reassembles with sha256 verified against the chat-side
hash. Verified end-to-end on michael-jordan-01: committed parts
reassembled to sha `fa97ef…` = pristine source.

## 3. Transcription fallback for live-recording sources

**Observed:** The MJ Hall of Fame speech is a 23-minute live recording with
crowd ambience that never drops below the SOP's `-55 dBFS` island
threshold. The island method collapsed into one 23-min span and Parakeet
OOM'd silently on it (exit 137).

**Mitigation:** Added `pipeline/transcribe_chunks.py` — fixed-length 60s
chunks with 2s overlap, works on noisy sources. For precision cutting of
chosen thoughts, re-island narrow windows with a tighter `--dbfs` (we used
`-40` and `-38` for MJ's HOF).

**SOP update:** §Pipeline Step 2 should mention the live-recording
fallback and suggest `-dbfs -35..-40` for narrow-window re-islanding.

## 4. Music-drop detector: first-rise bias

**Observed:** The `Cutscene Crush` music has TWO legitimate drop candidates
— a smaller one at 12.6s (+9 dB rise) and a larger sustained drop at
21.3s (+14 dB) with a natural `-27 dBFS` pre-dip at 20s. First-pass
detector picked the strongest-rise (21.3s), which turns out to be the
musically correct choice for a motivational edit (pre-dip plays as the
music-only pause; drop lands on first speech word).

**Code change made:** `find_music_drop.py` now scores with a shorter
smoothing kernel (0.3s) and picks the FIRST rise within 3 dB of the max.
If the max is early, it wins; if the sustained drop later is bigger, it
still picks it. Worked for MJ. Franco can override `--search-start` /
`--search-end` per track as needed.

## 5. Caption fix-up map approach

**Observed:** Parakeet mishears on this track:
- "Leroy" → "E.W." or "Lero"
- "the fire in me" → "to fire at me"
- "wood" → "wool"
- "are often" → "Austin" (!)
- plus MJ's natural stutters ("can't win a can't win")

**Mitigation:** Captions now use **per-clip "desired text" from
cuts.json** distributed over Parakeet word timings proportionally within
each clip, rather than running Parakeet's raw text through a fix-up
substitution map. Captions stay faithful to the brief; timings stay
pinned to measured speech beats.

**SOP update:** §Pipeline Step 9 should note that each cut's "expected"
text is the caption source of truth, not the raw Parakeet pass.

## 6. v2 fixes (Franco's Gate 2 notes)

- **Music bed under the hook.** Music now runs from 0:00 under the narration
  (faint, −18 dB, 0.5s fade-in), still landing the drop on the subject's
  first word. New timeline.json keys: `hook_bed_db`, `music_fade_in_s`;
  set `hook_enter_before_end_s` = hook length to start music at 0:00.
  Proposal: make this the default in §The format / §Step 5.
- **Caption width bug.** The merge-short-chunks step glued chunks together
  without re-checking width ("GOOD AS MAGIC JOHNSON" rendered 1,883px wide).
  Fixed: merges only when the result fits (≤3 words, ≤900px); long single
  words are scaled down; a rebalance pass gives every caption ≥0.2s.
- **Caption timing alignment.** Brief words are now matched to Parakeet words
  by text (difflib) instead of by proportional index, so a stutter in the
  source doesn't drift every later caption.
- **Loudness/limiter.** With the music bed, AAC encode pushed true peak to
  −0.4 dBTP. mix_audio.py now targets I=−13.3, TP=−2 with a 0.79 limiter;
  delivery lands at −14.95 LUFS / −1.06 dBTP.
