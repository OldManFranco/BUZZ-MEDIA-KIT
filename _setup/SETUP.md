# Setting up the kit on a new computer

For Claude: when someone opens this kit for the first time (or `python _setup\check_setup.py` shows anything MISSING), walk them through the steps below **one at a time, in plain words**. Before each install or download, say what it is, how big it is, and ask; run it only on a clear yes (CLAUDE.md §10). Skip steps `check_setup.py` already shows as OK.

For people: open this folder in Claude Code and say **"set up the kit on this computer"**. Claude does the rest and asks before each step. You need about **20 GB free** and an hour, mostly downloads.

**Windows only for now** (the tools use Windows paths). An NVIDIA graphics card makes transcription fast; without one it still works, just slower.

---

## 0. See what's missing

```
python _setup\check_setup.py
```
(On a computer with no Python yet, start at step 1.)

## 1. Programs

Python 3.12, Git, ffmpeg and Node.js (HyperFrames needs Node). With Windows' own installer:
```
winget install --id Python.Python.3.12 -e
winget install --id Git.Git -e
winget install --id Gyan.FFmpeg -e
winget install --id OpenJS.NodeJS.LTS -e
```
Close and reopen Claude Code afterwards so the new programs are on the PATH.

## 2. Python packages for the pipeline (~150 MB)

```
py -3.12 -m pip install -r _setup\requirements_system.txt
```

## 3. The two tool environments (~9 GB)

WhisperX (transcription), 8 GB:
```
py -3.12 -m venv tools\venv_whisperx
tools\venv_whisperx\Scripts\python.exe -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -r tools\requirements_whisperx.lock.txt
```
Face tracking and cutouts, 0.6 GB:
```
py -3.12 -m venv tools\venv_render
tools\venv_render\Scripts\python.exe -m pip install -r tools\requirements_render.lock.txt
```
If a pinned version won't install on this machine, install the main packages and let pip pick the rest: `whisperx==3.8.6` with `torch==2.8.0+cu128 torchaudio==2.8.0+cu128` (same index URL), and `mediapipe==1.0.1 opencv-contrib-python`. Note what changed in `tools\README.md`.

## 4. Face models (4 MB, from Google's MediaPipe)

```
mkdir tools\models
curl -L -o tools\models\face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
curl -L -o tools\models\selfie_segmenter.tflite https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite
```

## 5. yt-dlp (18 MB, optional: only for downloading reference videos)

```
mkdir pipeline\bin
curl -L -o pipeline\bin\yt-dlp.exe https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
```

## 6. HyperFrames (the graphics engine)

Claude Code offers to install it when the kit opens (it's pinned in `.claude\settings.json`). If it didn't:
```
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
```
Then restart Claude Code and run its own check (it downloads a headless Chrome the first time):
```
node %USERPROFILE%\.claude\plugins\cache\hyperframes\hyperframes\<version>\skills\hyperframes\scripts\plugin-cli.mjs doctor
```
Whisper-cpp, Kokoro, MusicGen and Docker show as missing there: the kit doesn't use them. Details: `_setup\hyperframes-install-notes.md`.

## 7. Sound effects and music (~385 MB)

```
python _setup\fetch_library.py
```
Downloads the 105 Mixkit files the catalogs list, each from Mixkit under its free license (the files can't go on GitHub). It then lists 48 optional ones (Pixabay, YouTube Audio Library) to download by hand from their pages. The kit works without them; `sfx\_synth\` comes with the repo. Licenses: CLAUDE.md §8.

## 8. Who's using the kit

Create `kit.local.json` in the kit folder with your name (it stays on this computer, never on GitHub):
```json
{"user": "Rocio"}
```
Wherever CLAUDE.md says "Franco approves", it means this person.

## 9. Check

```
python _setup\check_setup.py
```
Everything OK → done. The first transcription downloads WhisperX's models (~5 GB, once, into your user folder).

---

## After setup: your first client

Every reel belongs to a client in `clients\<name>\` (CLAUDE.md §2, "New client checklist"). Making reels for yourself? **You're your own first client.** Put your brand guide, logo, colors and any notes about you into `clients\<your-name>\_brand\` and `_instructions\`, then tell Claude: **"set me up as a new client and interview me."** It reads what you added and asks about you, your audience, your style, your platforms and your call to action, one question at a time, then writes your brief and brand files. Until you have a brand, reels use a plain black-and-white look.
