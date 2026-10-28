# Archived: The Standard kit (frozen 2026-10-27)

This is the complete The Standard kit (v3.0) this repo was forked from, moved here unchanged so it can be diffed.
Nothing in this folder applies to Medellin Buzz Shorts. See the root `CLAUDE.md`.

Archived because Medellin Buzz Shorts doesn't use them:
- ElevenLabs integration and the Declan Sage voice config (CLAUDE.md "The Standard voice"), narration writing, hook variants
- Athlete research / fact verification / archival sourcing (research_athlete.py, verify_facts.py, source_archival.py, ...)
- Subject folders (Kobe Bryant, Michael Jordan, Jon Jones, Tom Brady, J J Watt), outbox, working (footage gitignored)
- Anton captions, standard.cube, signoff_card.mp4, watermark, era looks, HyperFrames monochrome graphics library
- Parakeet (sherpa-onnx) transcription — replaced by WhisperX from Alejo's kit

Copied forward (not moved) into the new `pipeline\`: scene_detect.py, build_contact_sheet.py, bin\yt-dlp.exe.
Possible salvage later: build_captions.py (word timing, width checks, one-caption-at-a-time logic), render_shots.py (crop math), mix_audio.py (limiter mastering chain), qa.py.

Correction (2026-10-27, kit v0.4): HyperFrames itself was never meant to be dropped. Only The Standard's monochrome
block library stayed archived; Medellin Buzz Shorts now has its own brand HyperFrames library in pipeline\graphics\.
