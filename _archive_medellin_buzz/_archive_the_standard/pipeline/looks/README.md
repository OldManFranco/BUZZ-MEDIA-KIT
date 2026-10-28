# Era looks for archival footage

CLAUDE.md v3.0 §Step 7. Used by `render_shots.py --format v3` through a segment's
`"grade"` field (`archival` and `still` segments only; b-roll and a-roll keep
`standard.cube`). Applied via `npx hyperframes media-treatment` or an ffmpeg chain.

| Look | Intended treatment | Status |
|---|---|---|
| `era_70s` | warm, lifted blacks, fine grain | built (looks.json) |
| `era_90s` | slightly cool, video softness, light grain | built (looks.json) |
| `bw_film` | black and white, film grain, gentle vignette | built (looks.json) |
