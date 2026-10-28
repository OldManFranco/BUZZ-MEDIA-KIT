r"""
Buzz Media kit — step 3 (only when a client gives a finished long-form): map long-form moments to raw takes.

Reads WhisperX words.json for the long-form and every raw clip, finds the same
word sequences (5-gram anchors, chained into runs), and writes
<project>\working\map.json:
  runs:   {longform_in, longform_out, raw_file, raw_in, raw_out, n_words, match_score, text}
  unused: raw stretches (>= 4 words) the long-form never uses: alternate takes,
          lines cut from the edit, false starts. That's where better hooks live.

Usage:
  python pipeline/map_longform_raw.py --project clients/<client>/projects/<project> --longform-stem "<stem>"
  (archived layout: --slug el-hueco)
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I drops the script dir from sys.path
import kit  # noqa: E402

N = 5          # anchor n-gram size
MAX_GAP = 4    # words the chain may skip on either side (fillers, mis-hearings)


def norm(w):
    return re.sub(r"[^a-z0-9áéíóúñü]", "", w.lower())


def load_words(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for x in d["words"]:
        n = norm(x["w"])
        if n:
            out.append({"w": x["w"], "n": n, "s": x["start"], "e": x["end"],
                        "interp": bool(x.get("interpolada"))})
    return out


def chain(lf, raw_files):
    """Greedy: walk the long-form; at each position find an n-gram hit and extend it."""
    index = defaultdict(list)
    for name, ws in raw_files.items():
        for i in range(len(ws) - N + 1):
            index[tuple(w["n"] for w in ws[i:i + N])].append((name, i))
    runs, i = [], 0
    while i <= len(lf) - N:
        hits = index.get(tuple(w["n"] for w in lf[i:i + N]))
        if not hits:
            i += 1
            continue
        best = None
        for name, j in hits:
            ws = raw_files[name]
            a, b, matched, miss = i, j, 0, 0
            while a < len(lf) and b < len(ws):
                if lf[a]["n"] == ws[b]["n"]:
                    a, b, matched, miss = a + 1, b + 1, matched + 1, 0
                    continue
                # allow small skips on either side
                step = next(((da, db) for da in range(MAX_GAP + 1) for db in range(MAX_GAP + 1)
                             if (da or db) and a + da < len(lf) and b + db < len(ws)
                             and lf[a + da]["n"] == ws[b + db]["n"]), None)
                if not step:
                    break
                a, b = a + step[0], b + step[1]
                miss += 1
            if not best or matched > best[4]:
                best = (name, i, a, j, matched, b)
        name, a0, a1, b0, matched, b1 = best
        ws = raw_files[name]
        runs.append({
            "longform_in": round(lf[a0]["s"], 3), "longform_out": round(lf[a1 - 1]["e"], 3),
            "raw_file": name, "raw_in": round(ws[b0]["s"], 3), "raw_out": round(ws[b1 - 1]["e"], 3),
            "raw_word_idx": [b0, b1], "n_words": matched,
            "match_score": round(matched / max(a1 - a0, b1 - b0), 3),
            "text": " ".join(w["w"] for w in lf[a0:a1]),
        })
        i = a1
    return runs


def unused_spans(raw_files, runs, min_words=4):
    used = defaultdict(set)
    for r in runs:
        used[r["raw_file"]].update(range(*r["raw_word_idx"]))
    out = []
    for name, ws in raw_files.items():
        span = []
        for k, w in enumerate(ws + [None]):
            if w is not None and k not in used[name]:
                span.append(k)
                continue
            if len(span) >= min_words:
                out.append({"raw_file": name, "raw_in": round(ws[span[0]]["s"], 3),
                            "raw_out": round(ws[span[-1]]["e"], 3), "n_words": len(span),
                            "text": " ".join(ws[x]["w"] for x in span)})
            span = []
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", help="clients/<client>/projects/<project>")
    ap.add_argument("--slug", help="archived layout only")
    ap.add_argument("--longform-stem", required=True)
    a = ap.parse_args()

    wd = (kit.Project(project_dir=a.project) if a.project else kit.Project({}, slug=a.slug)).working
    tdir = wd / "transcripts"
    lf = load_words(tdir / f"{a.longform_stem}.words.json")
    raw_files = {p.name.replace(".words.json", ""): load_words(p)
                 for p in sorted(tdir.glob("*.words.json")) if not p.name.startswith(a.longform_stem + ".")}
    runs = chain(lf, raw_files)
    unused = unused_spans(raw_files, runs)
    covered = sum(r["n_words"] for r in runs)
    out = {"slug": a.slug or Path(a.project).name, "longform_words": len(lf), "matched_words": covered,
           "coverage": round(covered / max(len(lf), 1), 3), "runs": runs, "unused": unused}
    (wd / "map.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(runs)} runs, {covered}/{len(lf)} long-form words matched ({out['coverage']:.0%}), "
          f"{len(unused)} unused raw spans")
    print("wrote", wd / "map.json")


if __name__ == "__main__":
    main()
