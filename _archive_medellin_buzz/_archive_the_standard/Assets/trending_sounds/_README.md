# Trending sounds — how to add

Once a week, bookmark the TikTok sounds you see trending in the US.

1. In TikTok, open the sound's page → Share → Copy link.
2. Add one line to `sounds.txt` in this folder:
   `2026-10-24 | https://www.tiktok.com/music/... | short note (mood, where you saw it)`
3. That's it. `rotate_trending_sound.py` downloads them into `downloads\` for analysis
   and tells you, per video, which one to add in the TikTok app and where to start it.

Rules:
- These sounds are copyrighted. They are **never** mixed into a delivery file and
  **never** committed to git (`downloads\` and `sounds.txt` are gitignored).
- You add the picked sound in the TikTok app over the `_nomusic` delivery file
  (suggested volume ~15%, start offset in `outbox\<slug>_sound.txt`).
