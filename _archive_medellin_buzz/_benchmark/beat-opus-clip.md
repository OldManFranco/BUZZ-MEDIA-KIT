# Beat Opus Clip — what this kit does differently

Built from `opus-clip-analysis.md`. Each item names the weakness it fixes. These are defaults, not suggestions. Break one only with a reason written in the EDL.

The core difference: **Opus Clip picks windows from a finished long-form. We build shorts from ideas, using the long-form as the map and the raw footage as the material.**

---

## 1. Selection: ideas, not windows

**Fixes:** mid-story openings (09, 13, 15, 16), endings before the payoff (10, 11, 14), off-limits topics (half the current set).

- **One short = one idea with a setup and a payoff** that both fit in 30–60 s. If the payoff is at 70 s of Andrew talking, compress (cut the middle) or don't make it. Never ship a window that stops before the point.
- **Find the payoff first, then the hook.** Read the transcript for the line that lands ("But Medellín did.", "It's probably from right here."). Work backwards to the shortest setup that earns it.
- **Run the exclusion scan before anything else.** Topic-level exclusions kill the candidate; a single sentence gets cut around (17's dating-app passage).
- **Topic priority from the data:** money / prices / the dollar, a number, a US comparison, a "most people don't know" local secret, a place with a story. Those are the top performers (09, 11, 17, 14). Personal anecdotes and advice ("you definitely want to strategize") are the bottom.
- 3–5 candidates per long-form. Rank them for Franco by hook strength, self-containment and topic, and say which one we'd post first.

## 2. Hook construction: every short gets a built hook

**Fixes:** "Walking around El Hueco, my bet is that", "Couple of years ago", "When someone comes to me and I say, oh". 10 of 19 current hooks.

- **Cold-open pull-forward is the default move.** Take the sharpest line in the clip (usually the number or the contradiction) and play it at 0:00 for 2–4 s, hard cut, then start the story. Example from #14: open on "Today, that property could easily be sold for over a million dollars." → cut → "Most people who party here don't know this…". The pulled line isn't repeated later.
- **Reverse the question-hooks.** "Why did this happen?" (09) becomes the answer-first version: "The peso just had one of the best years of any money in the world." (his own words, from 0:01.7). Remove the dangling question.
- **Delete lead-in phrases.** "According to the latest census, there are over 8,000" → start at "Over 8,000 people live on the streets of Medellín" if Andrew says it that way anywhere (raw takes often have a cleaner version). If not, trim to "there are over 8,000…" with the title card carrying the context.
- **Title card hook at 0.0–2.5 s** when the spoken hook is good but needs the frame: ink plate, Poppins ExtraBold, one orange number. Example for 04: `70,000 PESOS` / `$22` orange / eyebrow `EL HUECO · MEDELLÍN` while Andrew says "This shirt costs about 70,000 pesos". Silent-autoplay viewers get the hook too.
- **Triple alignment:** spoken line, title card and first shot all point at the same thing and don't repeat each other's words.
- **Visual-first when we have the shot:** the bird (07) should open on a tight, moving raw shot of the bombed bronze bird, not a wide where it's out of frame. Andrew's "You see this bird?" lands over it.
- **Hard check:** if the first 3 s don't contain a number, a place, money, a contradiction or a clear question with stakes, the plan isn't done.

## 3. Use the raw footage (the advantage Opus can't have)

**Fixes:** every B-roll shot being the long-form's 16:9 B-roll in a blurred letterbox; no vertical shots of the actual places.

- **B-roll comes from `raw\` first**, the vertical or croppable vlog footage of the place he's talking about: El Hueco's crowds, the shoe stores, the bird, Parque Lleras. Long-form B-roll is second choice and must crop cleanly to 9:16 or it doesn't go in.
- **Better takes:** when the long-form uses take 3 of a line, check takes 1–2 and the lines around it in raw. Shorter, punchier versions of hooks are often sitting there unused.
- **Natural sound:** the raw clips carry the market noise, the street, the crowd. Use it under B-roll at −18 to −24 dB so cuts don't drop into silence.
- **Never a blurred-background letterbox.** If a 16:9 asset can't be cropped, it goes in a designed frame (ink background, the asset as a framed panel in the upper-middle, a warm-gray source line) or it doesn't go in.

## 4. Rebuild the brand cards for 9:16, never crop them

**Fixes:** "IET PARK OF FAM", "STAURAN… GHTCLUE", "bia's #2 eign million"; double captions over cards.

- Alejo's 16:9 data cards are the most branded thing in the long-form. In shorts we **re-lay them for 1080×1920** with the same system (cream/ink, Poppins ExtraBold, one orange element, ease-out masked reveals, rolling counters) using the card spec in `brand-notes.md` §3. Same data, vertical layout. Never center-crop a 16:9 card.
- **Captions mute while a card shows the same words.** One text layer at a time.
- Cards stay 2–4 s. One card per ~10 s max.

## 5. Captions that look like Medellin Buzz

**Fixes:** green/yellow highlights, random emojis, "UH"/"UM" captions, logo covered.

- Poppins ExtraBold, white, ink outline. **Active word on an orange `#D95633` plate** (the long-form chip, word by word). Spec in `brand-notes.md` §4.
- **No emojis.** Ever. (💊 on a homelessness story is a brand risk, not a style.)
- **Fillers removed from the audio first**, so they never reach the captions.
- 2–4 words, one line where possible, two max. Lower-middle third (y ≈ 1250), clear of the platform UI, and clear of Andrew's mouth.
- Numbers formatted for reading: `$22`, `8,000`, `14.5%`, `1.2M`.

## 6. Pacing: tighter than Andrew talks, never faster than he thinks

**Fixes:** dead air up to 4.35 s; 30–50 s static studio frames; uneven cadence inherited from the long-form.

- **Remove every pause > 0.35 s** inside a thought, every "uh/um", false start and repeated word, by splicing on WhisperX word boundaries (never on interpolated words), with 2–3 frames of room tone on each side. Not jump-cut chopping for its own sake: keep his breaths before a payoff.
- **Studio shorts get visual change every 3–5 s:** alternate two crops of the same 4K/1080 frame (medium ↔ tight, 108–115%) on sentence boundaries, plus chips and cards. A 30 s static frame is banned.
- **Street shorts:** a visual change every 2–4 s (B-roll, card, chip, punch-in), but hold on Andrew's face for the hook line and the payoff line. Faces sell those.
- **Match cuts over hard cuts where the footage allows:** cut on Andrew's gesture to the B-roll of what he's pointing at; cut on the word "this" to the object; whip-pan in raw → whip-pan out. Hard cuts otherwise. No dissolves, no zoom transitions, no glitch.

## 7. Endings that land (or loop)

**Fixes:** 0.00–0.10 s tails on 17 of 19; 12 flat endings; "stick around by the end of this video".

- **End on the payoff line**, then hold 0.4–0.8 s on Andrew's face or the strongest B-roll with a music button or a soft hit. The beat after the line is what makes it land.
- **Or loop:** build the last line so it flows into the first frame (07: "…a little bit of both of these birds." → back to the bird). Loops lift completion and replays.
- **Never end on:** a long-form teaser ("stick around", "by the end of this video"), a list item, a tangent, "Right.", the intro bio.
- **Comment prompt only if it's Andrew's own line** and it asks something real ("would you shop here in person or online?" in 02 is a good one, but it was buried at 0:35 with 12 s of tangent after it). Place it as the last line, not before a tangent.
- **Long-form link:** use YouTube's native "Related video" link to the long-form on every Short (Franco sets it on upload; the package tells him which). Not "Full video on YouTube: MedellinBuzz" as dead text.

## 8. Sound design

**Fixes:** quiet masters (−17 to −19 LUFS); (to confirm by ear) flat audio.

- Voice cleaned and leveled across splices; **master to −14 LUFS, ≤ −1 dBTP.** We'll be as loud as everything around us in the feed.
- Room tone and natural sound under every B-roll cut.
- Soft hit on the title card, pop on chips, whoosh on B-roll entrances, tick on counters. ≤1 SFX per 3 s, never on a number or a name he's saying.
- Music bed optional, low (−22 to −26 dB under voice), ducked; rises in the 0.4–0.8 s ending hold. Licensed and noted.

## 9. Packaging

**Fixes:** "Medellin's Bird of Peace: A Symbol of Resilience #shorts".

- Titles: specific, curious, honest, ≤ 50 chars. A number, "you", a contradiction, or a first-person witness ("I've seen…") when it's true. Example for 04: "This $22 shirt costs 4× at the mall" instead of "Medellín's Hidden Shopping Bargains". No colon-subtitle SEO headers.
- Description: one plain line in Andrew's voice + 3–5 specific hashtags. No AI summary paragraphs. Brand voice rules apply (no "testament to", no "here's the thing", no dramatic dashes).
- Cover frame chosen on purpose (Andrew's face + the number on the title card).
- Posting cadence: spread them out, never 3+ on one day (−17%).

## 10. Quality gates Opus doesn't have

- **Gate 1:** Franco sees the hook words, hook type and EDL before anything renders.
- **QA re-transcribes the final file:** catches cut-off words, leftover fillers, exclusion keywords, captions out of the safe zone.
- **Brand check:** one orange element at a time, no green, no emojis, no cropped cards, no letterboxes.

---

## Scorecard — check every short before Gate 2

| # | Check | Opus Clip today |
|---|---|---|
| 1 | Hook in 0–3 s has a number / money / place / contradiction / stakes question, and makes sense with zero context | 5 of 19 |
| 2 | Title card or visual hook when the spoken line needs help | 0 of 20 |
| 3 | No pause > 0.35 s inside a thought, no audible "uh/um" | 0 of 19 |
| 4 | Visual change at least every 5 s | 0 of 19 (longest hold per short: 7.6–37 s) |
| 5 | No letterbox, no cropped card | at most 9 of 19 (10 seen failing) |
| 6 | Brand captions, no emojis, no green | 0 of 19 |
| 7 | Ends on a payoff or loops, with a 0.4–0.8 s landing | 3 of 19 |
| 8 | −14 LUFS ±1 | 0 of 20 |
| 9 | Clear of the content exclusions | 11 of 20 |
| 10 | Uses raw footage the long-form didn't | 0 of 20 |

Target: **10 of 10 on every short.**
