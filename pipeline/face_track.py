r"""
Buzz Media kit — step 6 helper: where is the speaker's face in each A-roll piece?

Runs in the kit's render venv (MediaPipe), with tools\render\cara.py (models in tools\models\):
  tools\venv_render\Scripts\python.exe -I pipeline/face_track.py \
      clients/<client>/projects/<project>/working/plans/s1_edl.json [--out <faces.json>]

For every aroll event in the EDL, samples a frame every 0.4 s (at 1280 px wide),
measures the eyes, and writes <project>\working\render\<short>\faces.json:
  {"<src>|<in>|<out>": {"eyes_x": 0.43, "eyes_y": 0.36, "face_h": 0.21, "n": 7,
                        "samples": [[src_t, eyes_x, eyes_y, face_h, forehead_y, chin_y], ...]}}
  (fractions of the source frame). The renderer crops on the medians; the face checks (frame_check.py) use the
  samples, so a graphic is checked against where the face really goes, not one mockup frame (promo-02).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

sys.path.insert(0, str(kit.FACE_DIR))
from cara import Medidor  # noqa: E402  (copied from Alejo's kit into tools\render\)

W, H = 1280, 720


def frame(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                       capture_output=True)
    if len(r.stdout) != W * H * 3:
        return None
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3)


def main(edl_path, out=None):
    edl = json.loads(Path(edl_path).read_text(encoding="utf-8"))
    proj = kit.Project(edl)
    inp = proj.input
    out_dir = proj.render_dir(edl["short"])
    out_dir.mkdir(parents=True, exist_ok=True)
    med = Medidor(segmentar=False)
    res, clock = {}, 0.0
    for e in edl["events"]:
        if e["kind"] != "aroll":
            continue
        key = f"{e['src']}|{e['in']}|{e['out']}"
        xs, ys, hs, samples = [], [], [], []
        for t in np.arange(e["in"] + 0.05, e["out"], 0.4):
            img = frame(inp / e["src"], t)
            clock += 400  # MediaPipe VIDEO mode wants increasing timestamps
            m = med.medir(img, clock) if img is not None else None
            if m:
                xs.append(m["ojos_x"] / W)
                ys.append(m["ojos_y"] / H)
                hs.append(m["alto_cara"] / H)
                samples.append([round(float(t), 3), round(m["ojos_x"] / W, 4), round(m["ojos_y"] / H, 4),
                                round(m["alto_cara"] / H, 4), round(m["frente_y"] / H, 4),
                                round(m["barbilla_y"] / H, 4)])
        res[key] = ({"eyes_x": round(float(np.median(xs)), 4), "eyes_y": round(float(np.median(ys)), 4),
                     "face_h": round(float(np.median(hs)), 4), "n": len(xs), "samples": samples}
                    if xs else {"n": 0})
        print(key, res[key], flush=True)
    dst = Path(out) if out else out_dir / "faces.json"
    dst.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None)
