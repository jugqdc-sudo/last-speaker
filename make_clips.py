#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cut every tape position the site links to into a short mp3, so a claim can be heard
on the page instead of on YouTube.

A link that takes the reader away from the page is not a proof anyone follows. A 4-second
clip under the cursor is. Clips are small (mono, 56k) and only cover positions the page
actually shows.

    python3 make_clips.py torwali        -> docs/clips/<run>/u<id>.mp3 + clips.json
"""
import json, pathlib, subprocess, sys, shutil

name = sys.argv[1] if len(sys.argv) > 1 else "torwali"
MAX = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5      # seconds per clip
root = pathlib.Path(__file__).parent
run = json.loads((root / "runs" / name / "run.json").read_text())
wav = root / "data" / f"{name}.wav"

if not shutil.which("ffmpeg"):
    raise SystemExit("ffmpeg not found - brew install ffmpeg")
if not wav.exists():
    raise SystemExit(f"no tape at {wav} - clips cannot be cut without the source audio")

utts = {u["id"]: u for u in run["utterances"]}

# exactly the positions the page renders, nothing else - keeps the folder small
wanted = []
for w in run["words_top"][:21]:
    wanted += w["utts"][:2]
for r in run["rules"][:19]:
    wanted += [x["utt"] for x in r["examples"][:3]]
for v in sorted(run["voice"]["shifts"], key=lambda x: -abs(x["z_pitch"]))[:12]:
    wanted.append(v["utt"])
wanted = [u for u in dict.fromkeys(wanted) if u in utts]

out = root / "docs" / "clips" / name
out.mkdir(parents=True, exist_ok=True)
index, total = {}, 0
for uid in wanted:
    u = utts[uid]
    start = float(u["start"])
    dur = min(MAX, float(u.get("end", start + MAX)) - start) or MAX
    f = out / f"u{uid}.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                    "-i", str(wav), "-ac", "1", "-ar", "22050", "-b:a", "56k", str(f)], check=True)
    sz = f.stat().st_size
    total += sz
    index[str(uid)] = {"f": f.name, "start": round(start, 2), "dur": round(dur, 2)}

(out / "clips.json").write_text(json.dumps(index, indent=1))
print(f"docs/clips/{name}/ · {len(index)} clips · {total/1024/1024:.1f} MB")
if total > 40 * 1024 * 1024:
    print("!! over 40 MB - trim MAX or cut fewer positions before pushing", file=sys.stderr)
