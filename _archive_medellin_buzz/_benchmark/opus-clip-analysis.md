# Opus Clip Benchmark — the 20 most recent Medellin Buzz Shorts

Pulled 2026-10-27 from https://www.youtube.com/@MedellinBuzz/shorts with yt-dlp (20 most recent, uploaded 2026-10-15 → 2026-10-27).
Method: WhisperX large-v3 transcripts with word timings (`transcripts/`), PySceneDetect ContentDetector at threshold 27 (`scan.json`), ffmpeg EBU R128 loudness, and a keyframe sheet per short (`sheets/<file>.jpg`: the first 3 s every 0.5 s, then every 3 s). `hooks_all.jpg` shows the first 3 s of all 20 side by side. Raw numbers for everything below are in `scan.json`.

Purpose: understand what we've been shipping. **This is the floor to clear, not a template.**

---

## 0. What I can and can't assess (read first)

I worked from transcripts, cut timestamps, loudness numbers, metadata and still frames. I did not watch these as video.

**Solid from my data:** what's said in the first 3 s, when the first word lands, where it ends, words per minute, pauses, number and timing of hard cuts, loudness, caption *look* (font, colors, emojis, position, words per line), framing, how B-roll and cards are placed, titles and descriptions, views/likes.

**I can't assess — Franco, please watch for these:**
1. **Caption animation and timing feel** (pop-in? bounce? are highlights on the beat of his voice?). Stills only show the look.
2. **Music and audio mix.** I measured loudness, not whether there's a music bed, how it's ducked, or whether cuts click/pop. Listen to 09, 14 and 17.
3. **Jump cuts inside the same framing.** Scene detection misses cuts where the framing barely changes (the studio shorts show 0 cuts; they may have micro-jump-cuts). Watch 10 and 11.
4. **Auto-reframe tracking** when Andrew moves (the street shorts). Stills look centered; motion might hunt.
5. **Retention and swipe-away.** The real verdict. YouTube Studio → each Short → "Viewed vs. swiped away" and the retention curve. I only have public view counts on shorts 0–12 days old, so view comparisons below are weak.
6. **Whether all 20 are actually Opus Clip.** #05 clearly isn't (a native ciclovía montage with music, no talking). The rest have the same caption template and look like Opus output.

---

## 1. The 20 at a glance

Views as of 2026-10-27. Age in days. **Shorts this young are still accumulating views; treat views as a rough signal only.** #01 was posted today.

| # | Title | Len (s) | Age | Views | Likes | Set | Shots | First 3 s (spoken) |
|---|---|---|---|---|---|---|---|---|
| 01 | Colombia Tax Residency: The 183-Day Rule Explained | 39.6 | 0 | 0 | – | Studio | 1 | "Here's the rule. If you spend more than 183 days in Colombia" |
| 02 | El Hueco Survives One Handshake at a Time | 46.9 | 1 | 611 | 21 | Street | 18 | "Walking around El Hueco, my bet is that" |
| 03 | Why Shoe Stores Cluster Downtown | 48.8 | 1 | 941 | 23 | Street | 15 | "Why would you put your shoe store next to a hundred other shoe stores?" |
| 04 | Medellín's Hidden Shopping Bargains | 40.0 | 1 | 501 | 13 | Street | 8 | "This shirt costs about 70,000 pesos, which" |
| 05 | Wouldn't want to be anywhere else! | 11.7 | 1 | 953 | 19 | Montage | 3 | (music, crowd; no talking) |
| 06 | The Crisis of Homelessness in Medellin | 49.7 | 6 | 1,125 | 29 | Street | 9 | "According to the latest census, there are over 8,000" |
| 07 | Medellin's Bird of Peace: A Symbol of Resilience | 52.3 | 6 | 905 | 24 | Street | 13 | "You see this bird back here? It was built by Colombia's" |
| 08 | The Dark Side of Medellin's Downtown | 36.3 | 6 | 761 | 23 | Street | 5 | "While the rest of the city is pretty much booming" |
| 09 | Why the Colombian Peso Surged Against the Dollar | 37.3 | 7 | **2,303** | 45 | Studio | 1 | "Why did this happen? The peso had one of" |
| 10 | Why Americans Are Flocking to Medellin | 44.7 | 7 | 1,358 | 31 | Studio | 1 | "Prices are up and the dollar is down." |
| 11 | New Medellin Regulations for Airbnb Rentals | 52.0 | 7 | 1,815 | 40 | Studio | 2 | "Under these new rules, the wrong street could kill your plan" |
| 12 | Medellin's Shifting Economy: Downtown vs. Parque Lleras | 54.0 | 9 | 1,225 | 37 | Street | 16 | "Last year alone, 2025, we had 1.2" |
| 13 | The Vlogger Loop: Tourism Boom or Exploitation? | 53.3 | 9 | 373 | 9 | Street | 24 | "The travel vloggers came and started" |
| 14 | Medellín's Parque Lleras: From Quiet Homes to Party Central | 54.0 | 9 | 1,602 | 41 | Street | 16 | "Most people who party here don't know this about Parque Lleras, but" |
| 15 | Pablo Escobar's Rise & Reign of Terror | 45.6 | 10 | 634 | 12 | Street | 16 | "The money came with blood. So then come the 1970s," |
| 16 | Medellin Dating App Scams: From Theft to Crypto Heists | 51.6 | 10 | 1,745 | 32 | Street | 9 | "At first, the crimes were simple. They would slip something into their" |
| 17 | Medellin's Danger: What Changed After Escobar? | 54.0 | 10 | 1,815 | 47 | Street | 12 | "Everybody thinks killing the bad guy fixed Medellín." |
| 18 | Investing in Colombia: Visa & Real Estate Secrets Revealed | 29.3 | 12 | 1,120 | 20 | Studio | 3 | "You definitely want to strategize before you buy out here." |
| 19 | Short-Term Rental Market Shift | 34.4 | 12 | 367 | 6 | Studio | 3 | "Couple of years ago, before the market got oversaturated" |
| 20 | The Real Cost of Rental Income | 41.5 | 12 | 579 | 13 | Studio | 7 | "When someone comes to me and I say, oh, let me see the report" |

"Studio" = Andrew seated at the podcast mic with plants behind. "Street" = walking vlog, selfie-held, with long-form B-roll and cards inserted. "Shots" counts detected hard cuts + 1.

---

## 2. Hook timing — what happens in the first 3 seconds

**Timing is fine; content is the problem.** In 18 of 19 talking shorts the first word lands within 0.07 s (09 at 0.27 s). There's no dead air at the top. Opus starts on a word every time.

What the first 3 seconds actually *say* is weak in most of them:

| Hook quality | Shorts | Pattern |
|---|---|---|
| **Strong** — stakes, a number, a contradiction, self-contained | 03, 04, 11, 14, 17 | "Why would you put your shoe store next to a hundred other shoe stores?" · "This shirt costs 70,000 pesos" · "the wrong street could kill your plan" · "Most people who party here don't know this" · "Everybody thinks killing the bad guy fixed Medellín" |
| **OK but slow** — the good part arrives after a lead-in | 01, 06, 10, 12 | "According to the latest census, there are over 8,000…" (the number lands at ~2.5 s, after a filler phrase) |
| **Mid-story / needs the long-form** — makes no sense cold | 09, 13, 15, 16 | "Why did this happen?" (what happened?) · "The travel vloggers came…" · "At first, the crimes were simple" · "So then come the 1970s" |
| **No stakes** — a walk, an anecdote setup, generic advice | 02, 07, 08, 18, 19, 20 | "Walking around El Hueco, my bet is that" · "Couple of years ago" · "When someone comes to me and I say, oh" · "You definitely want to strategize before you buy" |

**Visual hooks: none.** Every short opens on Andrew talking or on the start of the long-form shot that happened to be there. #07 says "You see this bird back here?" over a wide shot where the bird is half out of frame on the right edge. #02 and #03 open on 16:9 street footage shrunk into a blurred letterbox. #12 opens with a long-form data card center-cropped so hard it reads "bia's #2 / eign / million". #15 opens on a Forbes cover in a blurred letterbox.

**On-screen text in the first 3 s:** only the captions. No title card, no number callout. One short (#07) has an Opus header pill ("NARCO VIOLENCE IN COLOMBIA") pinned top-center for the whole video, which isn't what the short is about (a Botero statue story).

---

## 3. Caption style

Consistent across all 19 talking shorts (see any sheet):
- Heavy geometric sans, ALL CAPS, white with a thick black stroke.
- **Green and yellow keyword highlights**, alternating, applied to whole words, not tracking the voice word-by-word.
- 2–4 words per group, stacked on 2–3 lines.
- Position: lower third, around y ≈ 78–85% of frame height. On the street shorts it lands over Andrew's chest, half-covering the "medellín LIVING" logo on his shirt.
- **Emojis dropped in at random:** 💰 under "COLOMBIA CAN TAX EVERYTHING", 😂 under "GRINGOS", ✈️ over "27.6%" (covering the number), 🎉 under "MOST PEOPLE WHO PARTY", 👍 under "COLOMBIA'S MOST FAMOUS ARTIST", 💊 under "THE DRUGS ARE DIRT CHEAP" (a homelessness story), 😩 under "COUPLE OF YEARS AGO".
- **Fillers captioned:** "UH" and "UM" appear as standalone captions (09, 10, 11, 01). The fillers are also left in the audio.
- **Double text over Alejo's cards:** when a long-form card is on screen, Opus captions sit on top of it saying the same thing in a different font and color (green Opus caption over Alejo's orange chip "70,000 PES" in #04; "THE MAYOR OF MEDELLIN / HALF OF THEM AREN'T" over a Spanish news clipping in #06).
- Palette clash: green/yellow captions on top of Alejo's cream/ink/orange cards. The brand disappears.

---

## 4. Cut cadence and framing

**Two very different products:**
- **Studio shorts (01, 09, 10, 11, 18, 19, 20):** one continuous framing for 29–52 s. 0–6 detected cuts. Average "shot" 10–37 s. No punch-ins, no B-roll, no cards, no visual change. #11 is 32.6 s on one frame. (Possible micro-jump-cuts I can't see; see §0.)
- **Street shorts (02–04, 06–08, 12–17):** 5–24 shots; average shot 2.2–7.3 s. B-roll and cards come from the long-form, so the cadence is the long-form's cadence, not a short's. Clusters of fast cuts (13 has cuts every 0.6–1.5 s at 37–41 s) next to long holds (06 holds 19.9 s on Andrew).

**16:9 assets are handled badly:**
- Long-form B-roll and news clippings → shrunk into a **blurred-background letterbox** (02, 06, 07, 13, 15, 17). Half the vertical frame is blur.
- Alejo's 16:9 **data cards are center-cropped**, cutting words off at both edges: "IET PARK OF FAM", "STAURAN… GHTCLUE", "IE LAST FAMILY HOME", "ALK TO A REAL PERSO", "bia's #2 eign million" (02, 12, 14). The cards Alejo designed are the most branded asset in the long-form and they arrive broken.
- Andrew himself is framed fine: the face sits in the upper half in both setups.

**Pacing of speech:** Andrew talks fast. 150–218 wpm (median ~165). The El Hueco and homelessness shorts run 201–218 wpm. Long pauses (>0.6 s) are left in, up to 3.4 s (09) and 4.35 s (10): dead air in the middle of a Short.

---

## 5. Length distribution

- Talking shorts: 29.3–54.0 s, median ~46 s. Six of nineteen are 52–54 s (Opus pushes toward the 55 s ceiling).
- #05 montage: 11.7 s.
- Length isn't chosen by the idea. It's whatever window Opus picked; several stop mid-idea at ~54 s.

---

## 6. Endings

**Tail after the last word: 0.00–0.10 s on 17 of 19.** Every short is cut the instant Andrew stops talking, with no breath, no button, no loop. Only 3 land a real payoff, 4 are neutral, and 12 end flat:
- **Good:** 17 ("Most cities with a past like this don't bounce back. But Medellín did."), 07 ("…downtown is a little bit of both of these birds."), 03 ("It's probably from right here.").
- **Flat or broken:**
  - Mid-thought / before the payoff: 10 ("…it's not just backpackers anymore." — the next sentence is the point), 11 (stops mid-rule), 14 (stops before "and now it's party central"), 15, 16, 18, 19 ("…and a property manager. Right."), 20 (mid-list).
  - Ends on a setup: 06 ("And on top of that, the drugs are dirt cheap.").
  - Ends on a tangent: 02 ("He wants to be a policeman this year for Halloween.").
  - **Ends on the long-form's own teaser:** 04 ("Stick around because by the end of this video, you're going to find out how business really works in Colombia." — in a 40 s Short, promising a payoff that never comes).
  - **Ends on the long-form's intro bio, including the deportation backstory:** 08.

---

## 7. Title and description patterns

- Titles: Title Case, descriptive, `Topic: Subtitle #shorts`. "The Crisis of Homelessness in Medellin", "Medellin's Bird of Peace: A Symbol of Resilience", "Investing in Colombia: Visa & Real Estate Secrets Revealed". They read like SEO article headers. Only 1 of 20 titles has a number (183 days), no "you", no tension, no first-person witness. (Alejo's long-form data says loss/warning and "you" titles win; none here use them.)
- Descriptions: an AI summary paragraph ("…stands as a testament to defiance", "…drenched in blood") + 3–5 hashtags. "Full video on YouTube: MedellinBuzz" as plain text with no link and no related-video link.
- No pinned comment strategy visible from the metadata.

---

## 8. Loudness

Integrated −15.6 to −19.3 LUFS (target for Shorts ≈ −14). The studio shorts are the quietest (−17 to −19 LUFS), so they play noticeably softer than the next video in the feed. #05 is −9.7 LUFS with a true peak of +0.6 dBFS (clipping).

---

## 9. What got views and what didn't

Caveat again: 19 data points, all 1–12 days old, public counts only. This is a hint, not a finding.

- **Top by total views:** 09 peso vs. dollar (2,303), 11 Airbnb rules (1,815), 17 danger after Escobar (1,815), 16 dating-app scams (1,745), 14 Parque Lleras history (1,602), 10 Americans flocking (1,358).
- **Bottom:** 19 rental returns (367, 12 days), 13 vlogger loop (373, 9 days), 20 rental income costs (579, 12 days), 15 Escobar (634, 10 days).
- **Topic beats craft.** #09 has a weak, context-dependent hook ("Why did this happen?"), a single static frame, and 3.4 s of dead air, and it's the top performer, because it's about money and the dollar. This matches Alejo's channel analysis: Shorts win with money, a number, or a US comparison in the first line.
- **Real estate investment shorts sit at the bottom.** Views per day: 19 → 31 and 20 → 48 are two of the three worst in the set; 18 → 93 is fifth-worst. Our exclusion of RE investment analysis costs almost nothing.
- **Dating/scam and legal-warning topics did get views** (16: 1,745; 11: 1,815). Excluding them is a real reach trade-off, not a free one. The rule stands; Franco should know what it costs.
- **Strong hook + strong ending = top tier among street shorts:** 17 and 14 have the two clearest contradiction hooks of the street set and are its top two. 13 and 15 open mid-story and are its bottom two.
- **Studio vs street:** no clear difference once age is accounted for. A static studio frame didn't kill #09 or #11; topic carried them.
- For scale (not comparable): Alejo's channel analysis counts 357 Shorts in 12 months for 1.1 M views (~3,100 per Short lifetime). These are well under that so far, but they're young.

---

## 10. Content exclusions vs. what's live

Under the new hard exclusions, **about half of these 20 wouldn't be made:**
- Real estate investment analysis: 18, 19, 20 (and 11 is RE regulation aimed at investors)
- Visa or legal warnings: 01 (tax residency), 18 (investor visa), 11 (zoning rules)
- Scam content: 16
- Dating / sex-tourism: 12, 13, 16; 17 has a dating-app safety passage in the middle (cut around it, keep the short)
- Deportation backstory: 08 (ends on it), 13 (ends on "He got deported", about a third party; borderline, flag it)

---

## 11. Weaknesses, ranked by how much they hurt

1. **Weak openings.** 10 of 19 hooks are mid-story or have no stakes; 4 only make sense if you watched the long-form. Opus picks windows, not ideas.
2. **Endings cut mid-thought or on teasers.** 12 of 19 talking shorts end flat; one ends on "stick around by the end of this video".
3. **Broken 16:9 assets.** Clipped data cards, blurred letterboxes. The most premium part of the long-form looks cheap in the short.
4. **Off-brand captions.** Green/yellow highlights, random emojis, captioned "UH"s, double text over brand cards. Nothing says Medellin Buzz.
5. **Zero visual change in studio shorts.** 30–50 s of one static frame.
6. **No hook construction at all.** No title card, no pulled-forward line, no visual open. Whatever Andrew said first is the hook.
7. **Dead air and fillers left in** (pauses to 4.35 s, "uh", "um").
8. **Quiet masters** (−17 to −19 LUFS on studio shorts).
9. **Generic SEO titles; descriptions with no real link.**
10. **Never uses the raw footage.** Opus only sees the long-form, so every B-roll shot is the long-form's B-roll, letterboxed. The vlog footage of the actual places (the bird, El Hueco's crowds, Parque Lleras) is never used in vertical.
