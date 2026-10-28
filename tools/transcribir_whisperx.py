"""Transcribe material GRABADO (vlogs, HISTORIA, entrevistas: lo que no está en YouTube) con WhisperX:
Whisper + alineación forzada (wav2vec2) → tiempo por palabra mucho más preciso que faster-whisper solo.
Para Lives sigue el transcript de YouTube + transcribir_tramo.py (reglas_equipo §3, Franco 23-oct-2026).

Uso (con el venv de WhisperX, usa la RTX 3060):
  CLAUDE\\tools\\venv_whisperx\\Scripts\\python.exe CLAUDE/tools/transcribir_whisperx.py <clip o carpeta> <carpeta_salida>
      [--inicio HH:MM:SS --fin HH:MM:SS] [--modelo large-v3] [--idioma en|es] [--prompt "..."]

Saca en <carpeta_salida>:
  - <clip>.words.json : formato de siempre. "segments" (w, s, e, p) como los clips de HISTORIA y "words" (w, start, end, p)
                        como transcribir_tramo.py. Tiempos en segundos del CLIP (con --inicio, del clip, no del tramo).
  - <clip>.txt        : texto por frases con su tiempo.
  - whisperx_transcript.json : salida cruda de todos los clips (con el puntaje de alineación de cada palabra).
Las palabras que el alineador no puede ubicar (cifras como «$3,000», «20») se interpolan entre sus vecinas y llevan
"interpolada": true. Se salta los clips ya hechos (reanudable). Un video largo: lanzarlo desprendido.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import torch
import whisperx

PROMPT = "Um, uh, so, like, you know, I mean, Medellín, Colombia, Antioquia, El Poblado, Laureles, pesos, paisas, Andrew."
EXT = {".mp4", ".mov", ".mkv", ".wav", ".mp3", ".m4a"}


def to_sec(tc):
    return sum(float(p) * 60 ** k for k, p in enumerate(reversed(tc.split(":")))) if tc else 0.0


def to_tc(sec):
    m, s = divmod(sec, 60)
    return f"{int(m // 60)}:{int(m % 60):02d}:{s:05.2f}"


def interpolar(palabras, ini, fin):
    """Rellena start/end de las palabras sin tiempo repartiendo el hueco entre sus vecinas."""
    i = 0
    while i < len(palabras):
        if "start" in palabras[i]:
            i += 1
            continue
        j = i
        while j < len(palabras) and "start" not in palabras[j]:
            j += 1
        a = palabras[i - 1]["end"] if i > 0 else ini
        b = palabras[j]["start"] if j < len(palabras) else fin
        paso = max(b - a, 0.0) / (j - i)
        for k in range(i, j):
            palabras[k]["start"], palabras[k]["end"] = a + (k - i) * paso, a + (k - i + 1) * paso
            palabras[k]["interpolada"] = True
        i = j
    return palabras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--inicio")
    ap.add_argument("--fin")
    ap.add_argument("--modelo", default="large-v3")
    ap.add_argument("--idioma", default="en")
    ap.add_argument("--prompt", default=PROMPT)
    a = ap.parse_args()

    src, out = Path(a.src), Path(a.out)
    (out / "audio").mkdir(parents=True, exist_ok=True)
    clips = sorted(c for c in src.iterdir() if c.suffix.lower() in EXT and "broll" not in c.name.lower()) if src.is_dir() else [src]
    ini, fin = to_sec(a.inicio), to_sec(a.fin)
    sufijo = f"_{a.inicio.replace(':', '')}_{a.fin.replace(':', '')}" if a.inicio and a.fin else ""
    pendientes = [c for c in clips if not (out / f"{c.stem}{sufijo}.words.json").exists()]
    print(f"{len(clips)} clips, {len(pendientes)} por transcribir", flush=True)
    if not pendientes:
        return

    gpu = torch.cuda.is_available()
    dev, ctype = ("cuda", "float16") if gpu else ("cpu", "int8")
    print(f"dispositivo: {dev} ({torch.cuda.get_device_name(0) if gpu else 'sin CUDA: va a ir lento'})", flush=True)
    modelo = whisperx.load_model(a.modelo, dev, compute_type=ctype, language=a.idioma,
                                 asr_options={"initial_prompt": a.prompt, "condition_on_previous_text": False})
    alin, meta = whisperx.load_align_model(language_code=a.idioma, device=dev)

    crudo_f = out / "whisperx_transcript.json"
    crudo = json.loads(crudo_f.read_text(encoding="utf-8")) if crudo_f.exists() else {}
    for c in pendientes:
        t0 = time.time()
        wav = out / "audio" / f"{c.stem}{sufijo}.wav"
        cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", str(ini)] if a.inicio else []) + ["-i", str(c)]
        cmd += (["-t", str(fin - ini)] if a.fin else []) + ["-vn", "-ac", "1", "-ar", "16000", str(wav)]
        subprocess.run(cmd, check=True)
        audio = whisperx.load_audio(str(wav))
        dur = len(audio) / 16000
        r = modelo.transcribe(audio, batch_size=16 if gpu else 4, language=a.idioma)
        r = whisperx.align(r["segments"], alin, meta, audio, dev, return_char_alignments=False)

        segs, todas, lineas, n_interp = [], [], [], 0
        for s in r["segments"]:
            pals = [dict(w) for w in s.get("words", []) if w.get("word", "").strip()]
            pals = interpolar(pals, s.get("start", 0.0), s.get("end", dur))
            ws = []
            for w in pals:
                item = {"w": w["word"].strip(), "s": round(ini + w["start"], 3), "e": round(ini + w["end"], 3),
                        "p": round(float(w.get("score", 0.0)), 3)}
                if w.get("interpolada"):
                    item["interpolada"] = True
                    n_interp += 1
                ws.append(item)
                todas.append({"w": item["w"], "start": item["s"], "end": item["e"], "p": item["p"],
                              **({"interpolada": True} if w.get("interpolada") else {})})
            if ws:
                segs.append({"start": ws[0]["s"], "end": ws[-1]["e"], "text": s["text"].strip(), "words": ws})
                lineas.append(f"[{to_tc(ws[0]['s'])}] {s['text'].strip()}")

        dst = out / f"{c.stem}{sufijo}.words.json"
        dst.write_text(json.dumps({"clip": c.name, "source": str(c), "start": ini, "end": ini + dur, "model": f"whisperx {a.modelo} + wav2vec2",
                                   "segments": segs, "words": todas}, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / f"{c.stem}{sufijo}.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
        crudo[f"{c.name}{sufijo}"] = {"inicio": ini, "segments": r["segments"]}
        crudo_f.write_text(json.dumps(crudo, ensure_ascii=False, default=float), encoding="utf-8")
        print(f"OK {c.name}: {len(todas)} palabras ({n_interp} interpoladas), {dur:.0f} s de audio en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
