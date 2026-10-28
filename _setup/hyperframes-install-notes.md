# HyperFrames: install notes (Buzz Media kit)

Checked 2026-10-27.

## What's installed

| | |
|---|---|
| How | Claude Code **plugin** `hyperframes@hyperframes`, from the `heygen-com/hyperframes` marketplace, user scope |
| Version | **0.8.186** (installed 2026-10-23; 0.8.193 is available, see "Updating") |
| Where | `C:\Users\USUARIO\.claude\plugins\cache\hyperframes\hyperframes\0.8.186\` |
| Skills it gives Claude | `/hyperframes:hyperframes` (read first), `/hyperframes:hyperframes-cli`, `/hyperframes:hyperframes-registry`, `/hyperframes:media-use`, plus `figma`, `slideshow`, `remotion-to-hyperframes` |
| CLI | `node <plugin>\skills\hyperframes\scripts\plugin-cli.mjs <command>`. `pipeline\build_graphics.py` finds it with `hf_cli()` (or set `HF_CLI` to that file) |

The kit also pins it at **project scope** in `.claude\settings.json` (`extraKnownMarketplaces` + `enabledPlugins`), so Claude Code opened in this folder on another machine offers to install it.

## Why the plugin and not `npx skills add`

The HyperFrames README (v0.8.186, "Quick Start") gives two routes:

```
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
```
is the route it names **for Claude Code**. `npx skills add heygen-com/hyperframes` is for standalone skills (OpenCode, other agents).

The plugin was already installed on this machine, so `npx skills add` was **not** run: it would install a second, unversioned copy of the same skills into `.claude\skills\` next to the plugin's, and Claude would see every skill twice.

## Verified working (2026-10-27)

1. `plugin-cli.mjs --version` → `0.8.186`
2. `hyperframes doctor`: Node 24.22.1, FFmpeg/FFprobe 9.0.2, headless Chrome cached → OK. Missing but optional: whisper-cpp (we use WhisperX), Kokoro TTS and MusicGen (never used: real voices and licensed music only), Docker.
3. In the scratchpad (not in the kit): `init hf-smoke --example blank --resolution portrait --non-interactive` → `check` (0 errors, 0 warnings) → `snapshot` (5 PNG frames). No video was rendered.
4. The `/hyperframes:hyperframes` skill and its siblings show up in Claude Code's skill list in this folder.

## Gotchas

- **Slash command name:** plugin skills are namespaced. Type `/hyperframes:hyperframes`; plain `/hyperframes` only exists with the standalone `npx skills add` install.
- **`init` touches skills:** `hyperframes init` checks AI skills against GitHub and can install the standalone copies. Run it with `HYPERFRAMES_SKIP_SKILLS=1` (as above) so it doesn't duplicate the plugin.
- **No network at render time:** `build_graphics.py` copies GSAP (`pipeline\graphics\vendor\gsap.min.js`) and the fonts into every project, so renders never fetch anything.
- **Seek-back trap:** a GSAP `fromTo` that starts visible shows its start state before its start time, because frames render out of order. See `pipeline\graphics\README.md`.
- **Brand fonts and colors:** `build_graphics.py` fills `pipeline\graphics\brand.css` from the client's `_brand\brand.json` and copies its font files into each project (Buzz Media: Schibsted Grotesk variable + IBM Plex Mono, in `_brand_assets\fonts\`). Checked with a snapshot on 2026-10-27.
- **Path length:** HyperFrames' snapshot folder fails past Windows' 260-character path limit. Projects under `clients\` are fine; a deep temp folder isn't.

## Updating

```
claude plugin marketplace update hyperframes
claude plugin update hyperframes@hyperframes
```
Or turn on auto-update for the `hyperframes` marketplace in `/plugin` → Marketplaces (interactive terminal only). `hf_cli()` always picks the newest installed version. After an update, run `snapshot` on a known plan before the next render and record the new version here.
