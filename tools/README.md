# tools\ — the kit's own transcription and face-tracking setup

Copied from Alejo's kit (`E:\FRANCO\MEDELLIN_BUZZ CLAUDE KIT\CLAUDE\tools\`) on 2026-10-27 so the Buzz Media kit owns its tools instead of borrowing them. The pipeline only points here (`pipeline\kit.py`: `WHISPERX_PY`, `WHISPERX`, `RENDER_PY`, `FACE_DIR`).

| Path | What | How it got here |
|---|---|---|
| `transcribir_whisperx.py` | WhisperX transcription (large-v3 + wav2vec2 alignment) → `<clip>.words.json` + `<clip>.txt` | copied |
| `venv_whisperx\` | Python 3.12 venv: whisperx 3.8.6, torch 2.8.0+cu128 (CUDA, RTX 3060). 7.8 GB | copied |
| `venv_render\` | Python 3.12 venv: mediapipe 1.0.1, used by `pipeline\face_track.py`. 0.6 GB | copied |
| `render\cara.py` | Face/eye measurement (MediaPipe face landmarker) | copied |
| `models\` | `face_landmarker.task`, `selfie_segmenter.tflite` (gitignored) | copied |
| `requirements_*.lock.txt` | `pip freeze` of each venv, to rebuild them | generated |

Both venvs' `pyvenv.cfg` are real copies pointing at this folder. Their `home` is the system Python 3.12 (`C:\Users\USUARIO\AppData\Local\Programs\Python\Python312`), so that Python must stay installed.

On another computer the venvs and models are rebuilt from the lock files and Google's model links: `_setup\SETUP.md` steps 3–4.

## History

On 2026-10-27 drive E: first had only 5.3 GB free, so `venv_whisperx` started as NTFS hard links to Alejo's copy. Franco freed space the same day and it was replaced with a full copy (robocopy, 46,404 files, 0 failed). Every file now has a single link: nothing in `tools\` shares data with Alejo's kit. The old hard-linked folder is in `_to_delete\venv_whisperx_hardlinks\` (deleting it frees no space and doesn't touch Alejo's kit).

## Not in this folder (machine-wide caches)

The model weights download into the user profile, not into either kit: `C:\Users\USUARIO\.cache\huggingface\` (faster-whisper large-v3, 4.4 GB) and `C:\Users\USUARIO\.cache\torch\` (wav2vec2 aligners, 0.7 GB). They're shared by every program on this PC. On a new machine they download on first run.

## Run

```
tools\venv_whisperx\Scripts\python.exe -I tools\transcribir_whisperx.py <clip or folder> <out dir>
tools\venv_render\Scripts\python.exe -I pipeline\face_track.py <edl>
```

The startup warning about torchcodec is harmless. Verified 2026-10-27: a 66 s clip transcribed in 7 s on the GPU (CUDA on), and `cara.Medidor` loads its model from `tools\models\`.
