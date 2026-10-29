r"""
Buzz Media kit — what this computer has and what it's missing (_setup\SETUP.md). Standard library only, so it
runs on a fresh machine with nothing but Python installed. Changes nothing: it only looks.

  python _setup\check_setup.py            (from the kit folder)
  python _setup\check_setup.py --quick    skip loading the two venvs (~20 s)

Each line is OK, MISSING or NOTE, with the SETUP.md step that fixes it.
"""
import argparse
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
MODELS = {"face_landmarker.task": 3758596, "selfie_segmenter.tflite": 249537}
SYSTEM_MODULES = {"cv2": "opencv-python", "librosa": "librosa", "numpy": "numpy", "PIL": "pillow",
                  "scenedetect": "scenedetect", "scipy": "scipy", "soundfile": "soundfile"}
rows = []


def add(state, what, detail="", step=""):
    rows.append((state, what, detail, step))


def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def first_line(text):
    return text.splitlines()[0][:70] if text else ""


def programs():
    v = sys.version_info
    add("OK" if (v.major, v.minor) == (3, 12) else "MISSING", "Python 3.12 (system)",
        f"running {v.major}.{v.minor}.{v.micro}", "1")
    for name, args, step in (("git", ["--version"], "1"), ("ffmpeg", ["-version"], "1"),
                             ("ffprobe", ["-version"], "1"), ("node", ["--version"], "1")):
        if shutil.which(name):
            add("OK", name, first_line(run([name] + args)[1]), step)
        else:
            add("MISSING", name, "not on PATH", step)
    if shutil.which("nvidia-smi"):
        code, out = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
        add("OK" if code == 0 else "NOTE", "NVIDIA graphics card", first_line(out), "")
    else:
        add("NOTE", "NVIDIA graphics card", "none found: transcription runs on the CPU (slower, still works)", "")


def system_packages():
    missing = [pkg for mod, pkg in SYSTEM_MODULES.items() if importlib.util.find_spec(mod) is None]
    add("MISSING" if missing else "OK", "Python packages for the pipeline",
        "missing: " + ", ".join(missing) if missing else "all " + str(len(SYSTEM_MODULES)), "2")


def venvs(quick):
    checks = (("venv_whisperx", "WhisperX (transcription)",
               "import torch, whisperx; print('cuda' if torch.cuda.is_available() else 'cpu')", "3"),
              ("venv_render", "Face tracking + cutouts",
               "import mediapipe, cv2; cv2.ximgproc; print(mediapipe.__version__)", "3"))
    for folder, what, code, step in checks:
        py = TOOLS / folder / "Scripts" / "python.exe"
        if not py.exists():
            add("MISSING", what, f"tools\\{folder}\\ not built", step)
        elif quick:
            add("OK", what, f"tools\\{folder}\\ exists (not loaded: --quick)", step)
        else:
            rc, out = run([str(py), "-I", "-c", code], timeout=300)
            last = out.splitlines()[-1] if out else ""
            add("OK" if rc == 0 else "MISSING", what, last if rc == 0 else "won't load: " + last[:80], step)


def models():
    bad = [n for n, size in MODELS.items()
           if not (TOOLS / "models" / n).exists() or (TOOLS / "models" / n).stat().st_size != size]
    add("MISSING" if bad else "OK", "Face models (tools\\models\\)", "missing: " + ", ".join(bad) if bad else "both", "4")


def ytdlp():
    exe = ROOT / "pipeline" / "bin" / "yt-dlp.exe"
    if exe.exists():
        add("OK", "yt-dlp", first_line(run([str(exe), "--version"])[1]), "5")
    else:
        add("MISSING", "yt-dlp", "pipeline\\bin\\yt-dlp.exe (only for downloading reference videos)", "5")


def hyperframes():
    found = sorted(glob.glob(os.path.expanduser(
        "~/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs")))
    if os.environ.get("HF_CLI"):
        found.append(os.environ["HF_CLI"])
    if not found:
        add("MISSING", "HyperFrames plugin (graphics)", "not installed for Claude Code", "6")
    elif shutil.which("node"):
        add("OK", "HyperFrames plugin (graphics)", first_line(run(["node", found[-1], "--version"])[1]), "6")
    else:
        add("MISSING", "HyperFrames plugin (graphics)", "installed, but Node.js is missing", "1")


def library():
    sfx = json.loads((ROOT / "sfx" / "catalogo_sfx.json").read_text(encoding="utf-8"))["sfx"]
    have = sum((ROOT / "sfx" / v["archivo"].replace("\\", "/")).exists() for v in sfx.values())
    synth = len(list((ROOT / "sfx" / "_synth").glob("*.wav")))
    music = json.loads((ROOT / "music" / "catalogo_musica.json").read_text(encoding="utf-8"))["pistas"]
    mh = sum((ROOT / "music" / k).exists() for k in music)
    add("OK" if have == len(sfx) else "NOTE", "Sound effects", f"{have}/{len(sfx)} catalogued + {synth} synth", "7")
    add("OK" if mh == len(music) else "NOTE", "Music", f"{mh}/{len(music)} catalogued tracks", "7")


def user():
    f = ROOT / "kit.local.json"
    try:
        name = json.loads(f.read_text(encoding="utf-8")).get("user") if f.exists() else None
    except ValueError:
        name = None
    add("OK" if name else "MISSING", "Kit user (kit.local.json)", name or "not set: who approves plans and cuts", "8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    for f in (programs, system_packages, lambda: venvs(a.quick), models, ytdlp, hyperframes, library, user):
        try:
            f()
        except Exception as e:  # one broken check shouldn't hide the others
            add("NOTE", getattr(f, "__name__", "check"), f"check failed: {e}", "")
    w = max(len(r[1]) for r in rows)
    for state, what, detail, step in rows:
        print(f"{state:8} {what:{w}}  {detail}" + (f"   (SETUP.md step {step})" if state != "OK" and step else ""))
    missing = sum(r[0] == "MISSING" for r in rows)
    print(f"\n{missing} missing." if missing else "\nReady: everything the kit needs is here.")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
