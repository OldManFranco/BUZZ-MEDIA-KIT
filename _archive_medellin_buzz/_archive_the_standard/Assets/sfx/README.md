# SFX library

Audio files in these folders are **not committed to git** (Pixabay's license forbids
redistributing the files on their own). This README is tracked: it records where every
file came from, so the library can be rebuilt.

Allowed sources: Pixabay (Pixabay Content License), Mixkit (Mixkit free SFX license),
Freesound **CC0 only** (CC-BY would need credits in every caption). Anything else: ask Franco.

Use: SFX sit ~12 dB under the voice, average ≤1 per 3s, never on top of a narrated
proper noun or number (CLAUDE.md §Step 4).

## Starter pack — still to download (pick, listen, then record the exact URL below)

| Folder | Wanted | Search |
|---|---|---|
| impact | deep cinematic boom (2–3s tail) · short sub hit · trailer hit with metal | https://pixabay.com/sound-effects/search/cinematic%20boom/ · https://mixkit.co/free-sound-effects/impact/ |
| whoosh | soft air whoosh (0.5s) · fast swish · reverse whoosh | https://pixabay.com/sound-effects/search/whoosh/ · https://mixkit.co/free-sound-effects/whoosh/ |
| text_pop | soft UI pop · clock tick · typewriter key | https://pixabay.com/sound-effects/search/pop/ · https://mixkit.co/free-sound-effects/click/ |
| archival | projector loop (10s+) · film-reel click · VHS static burst · camera shutter | https://pixabay.com/sound-effects/search/film%20projector/ · https://freesound.org/search/?q=projector&f=license:%22Creative+Commons+0%22 |
| atmosphere | slow heartbeat · reverse cymbal (2s) · short riser · distant crowd bed | https://pixabay.com/sound-effects/search/heartbeat/ · https://mixkit.co/free-sound-effects/heartbeat/ |

## Files

Every file needs a row before it is used. Mixkit: free for commercial use, no attribution, never redistribute the raw files.
Pixabay blocks scripted downloads (HTTP 403): Pixabay files are added by hand, and their Content ID flag is checked on the item page. Check Pixabay's "Content ID Registered" flag
(registered = can trigger claims on TikTok/YouTube → don't use). Wanted for v3 (from Alejo's library shape):
impact (hook hit, drop), whoosh (beat transitions), text_pop (pop-ins, clock tick for dates),
atmosphere (riser into the 0:50 climax), archival (camera shutter, projector/film click).

| File | Source URL | Author | License | Content ID | Downloaded | Notes |
|---|---|---|---|---|---|---|
| archival/mixkit_1137_old_camera_shutter_click.wav | https://mixkit.co/free-sound-effects/download/1137/ (file: https://assets.mixkit.co/active_storage/sfx/1137/1137.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Old camera shutter click", 0.46s |
| archival/mixkit_1438_vintage_camera_shutter.wav | https://mixkit.co/free-sound-effects/download/1438/ (file: https://assets.mixkit.co/active_storage/sfx/1438/1438.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Vintage camera shutter", 1.16s |
| archival/mixkit_1441_vintage_film_projector.wav | https://mixkit.co/free-sound-effects/download/1441/ (file: https://assets.mixkit.co/active_storage/sfx/1441/1441.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Vintage film projector working", 24.98s |
| atmosphere/mixkit_497_cinematic_heartbeat_ambience.wav | https://mixkit.co/free-sound-effects/download/497/ (file: https://assets.mixkit.co/active_storage/sfx/497/497.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Cinematic heartbeat ambience", 5.86s |
| atmosphere/mixkit_632_cinematic_drama_riser.wav | https://mixkit.co/free-sound-effects/download/632/ (file: https://assets.mixkit.co/active_storage/sfx/632/632.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Cinematic drama riser", 31.00s |
| atmosphere/mixkit_790_cinematic_trailer_riser.wav | https://mixkit.co/free-sound-effects/download/790/ (file: https://assets.mixkit.co/active_storage/sfx/790/790.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Cinematic trailer riser", 2.57s |
| impact/mixkit_1143_whoosh_deep_impact.mp3 | https://mixkit.co/free-sound-effects/download/1143/ (file: https://assets.mixkit.co/active_storage/sfx/1143/1143.mp3) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Cinematic whoosh deep impact", 4.08s |
| impact/mixkit_563_drum_deep_impact.wav | https://mixkit.co/free-sound-effects/download/563/ (file: https://assets.mixkit.co/active_storage/sfx/563/563.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Drum deep impact", 5.50s |
| impact/mixkit_788_big_cinematic_impact.mp3 | https://mixkit.co/free-sound-effects/download/788/ (file: https://assets.mixkit.co/active_storage/sfx/788/788.mp3) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Big cinematic impact", 7.94s |
| text_pop/mixkit_1061_clock_ticker_single.wav | https://mixkit.co/free-sound-effects/download/1061/ (file: https://assets.mixkit.co/active_storage/sfx/1061/1061.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Clock ticker single", 0.85s |
| text_pop/mixkit_1125_typewriter_soft_click.wav | https://mixkit.co/free-sound-effects/download/1125/ (file: https://assets.mixkit.co/active_storage/sfx/1125/1125.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Typewriter soft click", 0.22s |
| text_pop/mixkit_3005_light_pop.wav | https://mixkit.co/free-sound-effects/download/3005/ (file: https://assets.mixkit.co/active_storage/sfx/3005/3005.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Explainer video pops whoosh light pop", 0.18s |
| whoosh/mixkit_1489_air_woosh.wav | https://mixkit.co/free-sound-effects/download/1489/ (file: https://assets.mixkit.co/active_storage/sfx/1489/1489.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Air woosh", 2.32s |
| whoosh/mixkit_1490_fast_whoosh_transition.wav | https://mixkit.co/free-sound-effects/download/1490/ (file: https://assets.mixkit.co/active_storage/sfx/1490/1490.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Fast whoosh transition", 1.76s |
| whoosh/mixkit_1492_cinematic_fast_transition.wav | https://mixkit.co/free-sound-effects/download/1492/ (file: https://assets.mixkit.co/active_storage/sfx/1492/1492.wav) | Mixkit | Mixkit Sound Effects Free License | n/a (Mixkit has no Content ID flag) | 2026-10-24 | "Cinematic whoosh fast transition", 1.33s |

Parked in `_unverified\` (not used, 2026-10-24): 9 files added without per-file URLs
(cinematic_hit, soft_hit, whoosh, swoosh, pop, click, tick, riser_2.5, riser_3.0).
Move one back only after its row is filled in.
