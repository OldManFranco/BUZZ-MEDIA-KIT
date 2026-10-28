"""
The Standard — Steps 10, 11, 12: Watermark + sign-off append + delivery render

CLAUDE.md v2.4 §Pipeline Steps 10/11/12 (source of truth)

Step 10: Watermark
  Text: @thestandard.daily
  Font: Anton, 44px, white, 25% opacity, no outline
  Position: centered horizontally, y=300
  Static, every frame EXCEPT the sign-off card.

Step 11: Append signoff_card.mp4 (1s). Music tail plays under it (handled
  in the mix in Step 5).

Step 12: Two-tier render.
  Archive master: 10-12 Mbps, keeps full fidelity.
  Delivery: `-b:v 2450k -maxrate 4000k -bufsize 8000k -c:a aac -b:a 160k`
            2-pass encode. Target ~20MB for 65s.

This script:
  1. Takes the muxed-less b-roll video, captions .ass, audio wav, Anton font,
     and signoff_card path.
  2. Overlays captions AND watermark on b-roll, muxes with audio.
  3. Appends signoff_card (which already carries music tail from Step 5 mix).
  4. Produces (a) archive master, (b) delivery mp4.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def ff_path(p: str) -> str:
    """Path for use inside an ffmpeg filter option: forward slashes, colon escaped."""
    return str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:")


def ffprobe_duration(p: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", p],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--broll", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--captions", required=True)
    ap.add_argument("--signoff", required=True)
    ap.add_argument("--anton-font", required=True)
    ap.add_argument("--fonts-dir", required=True,
                    help="directory containing Anton-Regular.ttf")
    ap.add_argument("--out-master", required=True)
    ap.add_argument("--out-delivery", required=True)
    ap.add_argument("--signoff-dur-s", type=float, default=1.0)
    ap.add_argument("--format", default="v2.4", choices=["v2.4", "v3"])
    ap.add_argument("--audio-nomusic", help="v3: mix_nomusic.wav (same mastering gain, music muted)")
    ap.add_argument("--out-delivery-nomusic", help="v3: delivery_nomusic.mp4 (same picture)")
    args = ap.parse_args()
    if args.format == "v3" and not (args.audio_nomusic and args.out_delivery_nomusic):
        ap.error("--format v3 needs --audio-nomusic and --out-delivery-nomusic")

    broll_dur = ffprobe_duration(args.broll)
    signoff_dur = ffprobe_duration(args.signoff)
    total_dur = broll_dur + args.signoff_dur_s
    print(f"broll: {broll_dur:.3f}s + signoff: {args.signoff_dur_s:.3f}s = {total_dur:.3f}s")

    # Stage 1: Overlay captions + watermark on b-roll, mux with speech+music
    # The audio file is longer than the b-roll alone — it covers the whole
    # final video including the sign-off. So mux up to the b-roll duration
    # here and the signoff concat picks up the audio from the correct offset.
    #
    # Easier approach: mux the WHOLE audio with the FULL b-roll+signoff
    # concat video.  We'll do:
    #   A: concat videos (b-roll + signoff with scale normalization)
    #   B: overlay captions + watermark on the b-roll portion only (via
    #      enable='between(t,0,broll_dur)')
    #   C: mux with audio
    #   D: produce master and delivery encodes.

    # Build a tmp concat list for videos
    tmp = Path(args.out_master).parent
    concat_list = tmp / "_vconcat.txt"
    normalized_signoff = tmp / "_signoff_norm.mp4"

    # Normalize signoff to same size/fps as b-roll (1080x1920 @ 30fps)
    norm_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", args.signoff,
        "-vf", "scale=1080:1920:flags=lanczos,fps=30,setsar=1,format=yuv420p",
        "-t", f"{args.signoff_dur_s:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        str(normalized_signoff),
    ]
    r = subprocess.run(norm_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("signoff normalize failed:", r.stderr); sys.exit(2)

    with open(concat_list, "w", encoding="utf-8") as f:
        f.write(f"file '{Path(args.broll).resolve().as_posix()}'\n")
        f.write(f"file '{normalized_signoff.resolve().as_posix()}'\n")

    # Caption-overlay segment: only apply between 0 and broll_dur.
    # ffmpeg subtitles filter is applied globally so we use timeline edits
    # by filter_complex: split, subs-and-wm on main until broll_dur, then
    # concat with the sign-off portion unmodified.
    #
    # Simpler: apply captions filter globally; the .ass events already end
    # before broll_dur (last caption ends well inside the ring-out).  For
    # watermark, use enable='lt(t,{broll_dur})' so it drops over sign-off.
    fonts_dir_esc = ff_path(args.fonts_dir)
    ass_esc = ff_path(args.captions)
    wm_text = "@thestandard.daily"
    font_esc = ff_path(args.anton_font)

    # Pass 1: concat and overlay. First make the archive master.
    master_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", args.audio,
        "-filter_complex",
        f"[0:v]"
        f"subtitles='{ass_esc}':fontsdir='{fonts_dir_esc}',"
        f"drawtext=fontfile='{font_esc}':text='{wm_text}':fontsize=44:"
        f"fontcolor=white@0.25:x=(w-text_w)/2:y=300:"
        f"enable='lt(t,{broll_dur:.3f})'"
        f"[vout]",
        "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        "-shortest",
        args.out_master,
    ]
    print("rendering master…")
    r = subprocess.run(master_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("master render failed:", r.stderr); sys.exit(2)
    print(f"wrote {args.out_master}")

    # Delivery two-pass encode from the master
    passlog = str(Path(args.out_delivery).with_suffix(".passlog"))
    pass1 = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", args.out_master,
        "-c:v", "libx264", "-b:v", "2450k", "-maxrate", "4000k",
        "-bufsize", "8000k", "-pass", "1", "-passlogfile", passlog,
        "-pix_fmt", "yuv420p",
        "-an",
        "-f", "mp4", os.devnull,  # NUL on Windows
    ]
    pass2 = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", args.out_master,
        "-c:v", "libx264", "-b:v", "2450k", "-maxrate", "4000k",
        "-bufsize", "8000k", "-pass", "2", "-passlogfile", passlog,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart",
        args.out_delivery,
    ]
    print("delivery pass 1 …")
    r = subprocess.run(pass1, capture_output=True, text=True)
    if r.returncode != 0:
        print("pass 1 failed:", r.stderr); sys.exit(2)
    print("delivery pass 2 …")
    r = subprocess.run(pass2, capture_output=True, text=True)
    if r.returncode != 0:
        print("pass 2 failed:", r.stderr); sys.exit(2)

    if args.format == "v3":
        # Same picture and the same pass-1 stats; audio from mix_nomusic.wav
        pass2_nm = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", args.out_master, "-i", args.audio_nomusic,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-b:v", "2450k", "-maxrate", "4000k",
            "-bufsize", "8000k", "-pass", "2", "-passlogfile", passlog,
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-movflags", "+faststart", "-shortest",
            args.out_delivery_nomusic,
        ]
        print("delivery (no music) pass 2 …")
        r = subprocess.run(pass2_nm, capture_output=True, text=True)
        if r.returncode != 0:
            print("nomusic pass 2 failed:", r.stderr); sys.exit(2)
        print(f"wrote {args.out_delivery_nomusic} ({os.path.getsize(args.out_delivery_nomusic) / 1e6:.1f} MB)")

    # Clean up pass log
    for ext in (".log", "-0.log", "-0.log.mbtree"):
        p = Path(passlog + ext)
        if p.exists(): p.unlink()

    deliv_sz = os.path.getsize(args.out_delivery) / 1e6
    print(f"wrote {args.out_delivery} ({deliv_sz:.1f} MB)")


if __name__ == "__main__":
    main()
