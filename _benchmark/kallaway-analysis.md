# Kallaway: what the craft actually is

Study of the **15 most recent Kallaway YouTube Shorts** (@kallawaytech, uploaded 2026-09-11 → 2026-10-19), pulled 2026-10-27 for **analysis only**. Andrew named Kallaway as the bar for cuts, music-beat syncing and SFX. Goal: Kallaway-level craft on Buzz Media reels, not Kallaway clones.

**Data:** `kallaway\scan.json` (per short: metadata, cut times, loudness, speech stats, beat-sync numbers) · `kallaway\sheets\*.jpg` (keyframes: 0–3 s every 0.5 s, then every 3 s) · `kallaway-transcripts\` (WhisperX, word level). Scripts: `pipeline\benchmark_scan.py`, `pipeline\beat_sync_scan.py`.

## How I worked, and what I can't see

I can't watch or listen. I worked from transcripts (word timing to ~20 ms), scene-cut detection (PySceneDetect), keyframe sheets (I looked at 6 of the 15 closely: 01, 05, 07, 09, 10, 14) and audio measures (loudness, a beat grid, percussive hits, high-frequency energy at cuts).

| Claim type | Confidence |
|---|---|
| Speech timing, pauses, words in the hook, script patterns | **High** (transcripts) |
| Cut rate, first cut, longest shot | **High**, one caveat: in split-screen shots a change in the top half counts as a cut |
| Layouts, caption look, text cards (from stills) | **Medium-high**: I see stills every 0.5–3 s, not motion |
| Animation style (how text enters, transitions, zooms) | **Low**: needs Franco's eyes |
| Music: present? which beats? | **Low**: the mix can't be split into voice/music/SFX |
| SFX: which, where | **Low**: only indirect evidence |

**Franco: please watch 3–4 of them with sound** (suggest 14, 11, 09, 07: the four with the most views) and fill the "To check by ear/eye" list at the end.

## The numbers

| | Median | Range |
|---|---|---|
| Length | **86 s** | 66–126 s |
| Views (YouTube, at download) | 12,000 | 620–397,000 |
| First spoken word | **0.11 s** | 0.07–0.17 s |
| Words in the first 3 s | **10** | 7–11 |
| Speaking rate | **207 wpm (3.5 words/s)** | 189–235 wpm |
| Gap between words | **40–60 ms** | longest pause per short typically 0.3–0.4 s |
| Picture changes per 10 s | **6.0** (one every **1.7 s**) | 4.1–7.7 |
| …in the first 10 s | **7.0** | 5–10 |
| …in the last 10 s | 6.0 | 3–8 |
| First cut | **1.1 s** | 0.8–3.8 s |
| Longest single shot | **4.9 s** | 2.6–15.5 s (the long ones are screen-recording demos) |
| Loudness | −14.3 LUFS, TP −0.8 dBTP (October uploads) | Sept uploads −18 to −24 LUFS |

Every one of these runs 66–126 s. He doesn't treat 60 s as a ceiling: the length is "as long as the story holds", and the pace is what holds it.

## 1. Hook construction (first 3 seconds)

**Spoken:** the first word lands at 0.1 s, every time. No breath, no greeting. Ten words in three seconds. The first sentence is always one of three shapes:

1. **"This [thing] is/does [superlative claim]."** "This factory in China is building a new robot every 10 minutes." · "This is a prosthetic hand that runs on signals from your brain." · "This company built a data center floating in the Pacific Ocean."
2. **"[Big name] just [did something]."** "Elon is now creating the biggest building in human history." · "OpenAI has officially launched dots." · "DoorDash just officially launched…"
3. **"These two guys just sold $7 million…"**: a person + a number.

Then, inside the first 5 seconds, a **second hook** that raises the stakes:
- "**And the crazy part is**, each new robot is being built by another robot."
- "**But here's the crazy part.** Neither of them are a real person."
- "**And I don't think people realize** just how insane this project actually is."

The two most-viewed shorts (14: 397K, 11: 223K) both use "This [specific object] + what's crazy about it", plus a twist in the second sentence.

**On screen (0–3 s), the default layout:**
- **Split screen:** the subject (the factory, the aircraft, the app) fills the **top half**; Kallaway at his desk fills the **bottom half**.
- A **2-line headline** sits on the seam between the halves: heavy condensed uppercase, line 1 white, line 2 **yellow**, often on a dark-red/ink plate ("CHINESE ROBOTS / BUILD THEMSELVES", "THE NEW ERA / OF AI AGENTS", "MILITARY AVIATION / BREAKTHROUGH"). It's on from ~0.5–1.0 s and stays through ~3 s.
- **The headline never repeats the spoken line.** It labels the category ("MILITARY AVIATION BREAKTHROUGH") while he says the specific ("This is a brand new type of military aircraft"). That's the triple-alignment rule done right.
- **Proof in the hook:** 09 shows a CNBC article with "$7 million" highlighted in yellow at 1.5 s, while he says "$7 million".
- First picture change at ~1.1 s.

## 2. Cut cadence

- **One picture change every 1.7 s**, faster in the first 10 s (one every 1.4 s). No shot over ~5 s except live screen demos.
- **Cuts follow the speech, not the music.** Cuts land on the start of a sentence or clause **3.3× more than chance** (33 % vs 10 %). Only **19 %** of cuts fall inside a word (chance: 42 %): he cuts in the gaps between words. The 19 % mid-word are mostly B-roll swaps in the top half while the voice carries on.
- **The voice is cut dead tight:** 40–60 ms between words, almost no pause over 0.4 s. Breaths and pauses are removed (jump cuts on the face layer), which is how 207 wpm feels natural.
- **Layouts rotate**, which counts as a "cut" for the eye even when the voice is continuous:
  1. Split screen: B-roll top, face bottom (the default, most of the runtime)
  2. Full-screen face, one big word on his chest (every ~10–15 s, on an emphasis word)
  3. Full-screen B-roll, small caption
  4. B-roll as a **rounded-corner card** floating on black, with his face in a **circle picture-in-picture** top-left
  5. Two or three stacked cards (a triptych: "8,000 / different / gestures"; "FORWARDS / BACKWARDS")
- Third-party footage carries a small **@handle credit** top-left (10: @rewind02, @ForwardEditor…).

## 3. Beat sync

**Honest result: I can't confirm beat-synced cutting from the audio.** On the beat grid I could extract (107–144 bpm), cuts land on a beat **less** often than random cutting would (median 14 % vs 26 % chance, ±2 frames). That's expected when the beat tracker hears mostly voice: cuts sit in the quiet gaps between words, away from the consonant spikes the tracker locks onto. So:

- What the data does show: **the edit is driven by the voice.** Sentence starts, clause starts, emphasis words.
- What it can't show: whether a music bed sits under the voice, and whether layout changes or the big emphasis words land on its beats. That needs ears. If there is a beat match, it's most likely on the **emphasis-word moments** (full-screen face + big word), not on the routine B-roll swaps.

## 4. SFX

- **There's no SFX on every cut.** High-frequency energy (where whooshes and risers live) at cut points is the same as at random points (ratio 0.99). If he used a whoosh per transition, it would be clearly higher.
- So SFX, if any, are **sparse accents**: likely on the hook headline, the big emphasis words and the data reveals ("3X BIGGER", "$7.6M REVENUE", "1700 football fields"). I can't confirm which sounds. **To check by ear.**

## 5. Captions

Two caption modes, and they switch with the layout:

- **Split screen:** small white bold sans, **1–3 words**, centered **on the seam** between the halves (y ≈ 50 %), off both faces. Sentence case. No plate, a soft shadow. Mostly no active-word color.
- **Full-screen face:** **one word at a time, large**, on his chest (y ≈ 60–65 %), and the font **alternates** between a heavy sans ("advantage", "massive", "available") and an **italic serif** ("insane", "major", "plan", "wildest", "coolest"). The serif marks the emotional words. Sometimes the word takes the accent color of the B-roll (14: "fly", "robotics" in the aircraft's neon yellow).
- Data callouts are their own type: big number + word in mixed fonts ("1700 *football fields*", "200 billion *AI chips per year*", "3X BIGGER" across a map).
- **Never** the 3-words-with-a-green-box Opus look. Captions stay small except when one word is the point.

## 6. Text cards and graphics

- **Hook headline** (above): every short.
- **Data reveals:** number + unit, set over the B-roll, not on a separate card: "3X BIGGER" on a Manhattan map, "$7.6M REVENUE" over the stream, "200 billion AI chips per year" over the factory.
- **Proof screenshots:** news articles with the key number highlighted in yellow (09), app UIs (05, 08, 10).
- **Analogies get their own picture:** "Think of it like a TV remote with no TV" (13); "This is a map of Manhattan" → map → "3X BIGGER" overlay (01).
- **Explainers:** stacked cards, product renders, a list built line by line (01's "master plan, in summary": 4 steps over 4 B-roll shots).

## 7. Pacing arc

Same skeleton in all 15 (≈85 s):

1. **0–3 s:** claim + headline + subject on screen.
2. **3–8 s:** the twist ("the crazy part is…").
3. **8–25 s:** what it is, in plain words, with one analogy ("Think of it like…", "It's like sitting in a car with no steering wheel").
4. **~20–30 s:** a **re-hook**: "But the wildest part isn't X, it's Y." / "But here's the craziest part." / "Of course, there's just one problem."
5. **Body:** how it works, one beat per sentence, a number every 10–15 s.
6. **Summary** ("So the master plan, in summary, is this…") or the big takeaway ("And that's the big takeaway.").
7. **Ending line** (below).

Script tics that drive retention: "See,…" (explanation begins), "Now,…" (new section), "Think of it like…" (analogy), "It's insane / It's pretty wild" (a 1-second beat that lets the picture land).

## 8. How shorts end

- **No outro, no end card, no logo.** The last word ends 0.1 s before the file does.
- Three ending types:
  - **The future-tense takeaway:** "…is gonna be normalized around the globe." · "…the first cookie ever eaten on Mars will have been made out of plastic."
  - **A punchline:** "Never bet against Elon."
  - **A keyword CTA (when there's something to give):** "Comment dots, and I'll send you more information…" (05) · "Comment Gemini and I'll send through the links…" (08). **Same mechanic as Buzz Media's "Comment EDIT"**.
  - Otherwise a follow line: "Follow for more stories like this on tech, AI, and robotics." (13, 14, 15)
- The ending is usually on his face, full screen, with the last word big (14: "robotics" in yellow).

## 9. What it means for Buzz Media

| Kallaway does | Buzz Media situation | Take |
|---|---|---|
| 66–126 s explainers | Andrew's promos: 30 s max; clients: 30–60 s | Keep his **density**, not his length. At 3.5 words/s, 30 s is ~100 words. |
| Split screen B-roll/face | Andrew at his desk, landscape → 9:16 | A natural fit: crop Andrew to the bottom half, proof on top. |
| Proof on screen in the hook | Promo 1's "200+ videos" and the Nomad Spanish stats | Exactly his pattern (09's CNBC highlight). |
| Keyword CTA | "Comment EDIT" | Same mechanic. He says it in the last line; keep it spoken *and* shown. |
| Red/yellow headline plate | Buzz Yellow is our one accent; red is logo-only | Use ink plate + yellow line. **Never a red plate** (brand rule). |
| Italic serif emphasis words | Brand fonts: Schibsted Grotesk + Plex Mono | Don't copy the serif. Our emphasis = Schibsted ExtraBold large + yellow (see rules). |

## To check by ear/eye (Franco)

1. Is there a **music bed**? How loud, what genre, does it change at the re-hook?
2. Do the **full-screen emphasis words** or layout switches land on music beats?
3. Which **SFX** are there: a whoosh on the headline? a hit on data reveals? a pop on the big words? risers before the twist?
4. How does the **hook headline animate in**? (slide, mask, scale, typewriter?)
5. Transitions between layouts: hard cut, or a move (slide, zoom, whip)?
6. Are there **zoom punch-ins** on the face layer between jump cuts?
7. Instagram reels: yt-dlp can't fetch Instagram without a login. Drop any you want studied into `_benchmark\kallaway-reels\` and I'll run the same scan.
