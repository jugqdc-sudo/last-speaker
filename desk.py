#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE LAST SPEAKER · the desk.
Six agents pull the sound system, the words and the recurring patterns out of raw tape of one
speaker. Nothing gets written without a tape position. Nothing gets translated.

    python3 desk.py run tape.wav --name torwali --title "..." --url "..." [--limit-min 10]
"""
import argparse, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from core import tape
from agents import scout, phon, lex, gram, voice, chief, scribe, derive


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("wav")
    r.add_argument("--name", required=True)
    r.add_argument("--title", default="")
    r.add_argument("--url", default="")
    r.add_argument("--limit-min", type=float, default=None, help="only the first N minutes of tape")
    r.add_argument("--reuse", action="store_true", help="reuse the cuts and phones from runs/<name>/phones.json instead of recognizing again")
    v = sub.add_parser("voice", help="VOICE only: where on the tape he is not using his usual voice")
    v.add_argument("wav")
    v.add_argument("--limit-min", type=float, default=None)
    v.add_argument("--top", type=int, default=10)
    a = ap.parse_args()

    if a.cmd == "voice":
        audio = tape.load(a.wav, a.limit_min)
        log = lambda who, text: print(f"{who:<6} {text}", flush=True)
        utts = scout.run(audio, log)
        for u in utts: u["phones"] = []                       # without phones we only measure pitch, not tempo
        vc = voice.run(audio, utts, log)
        top = sorted(vc["shifts"], key=lambda x: -abs(x["z_pitch"]))[:a.top]
        print(f"\nmedian pitch {vc['median_f0']} Hz · {len(vc['shifts'])} moments off his usual register · top {len(top)}:")
        for s in top:
            print(f"  {s['pos']}  {s['f0']:>6} Hz  z {s['z_pitch']:+.1f}")
        return

    out = pathlib.Path(__file__).parent / "runs" / a.name
    out.mkdir(parents=True, exist_ok=True)
    log = scribe.Log(out)
    t0 = time.time()
    audio = tape.load(a.wav, a.limit_min)
    meta = {"title": a.title, "url": a.url, "file": pathlib.Path(a.wav).name, "seconds": round(len(audio) / tape.SR, 1)}
    log("CHIEF", f"case open · {meta['file']} · {tape.hours(meta['seconds'])} h of tape · one speaker · no dictionary, no translation")

    cache = out / "phones.json"
    if a.reuse and cache.exists():
        utts = json.loads(cache.read_text())
        log("SCOUT", f"reusing {len(utts)} cut utterances from {cache.name}")
        from collections import Counter
        inv = Counter(p for u in utts for p in u["phones"])
        ph = {"inventory": dict(inv.most_common()),
              "vowels": {p: c for p, c in inv.most_common() if phon.is_vowel(p)},
              "consonants": {p: c for p, c in inv.most_common() if not phon.is_vowel(p)}}
        log("PHON", f"reusing inventory: {len(inv)} phones · {len(ph['vowels'])} vowels")
    else:
        utts = scout.run(audio, log)
        if not utts:
            raise SystemExit("SCOUT found zero utterances - the tape is empty or not 16k mono")
        ph = phon.run(audio, utts, log)
        cache.write_text(json.dumps([{k: u[k] for k in ("id", "start", "end", "phones")} for u in utts], ensure_ascii=False))
    lx = lex.run(utts, log)
    rules, fights = gram.run(utts, lx, log)
    vc = voice.run(audio, utts, log)
    signed, refused, fights = chief.run(rules, fights, vc, utts, log)
    dv = derive.run(utts, lx, signed, log)
    qu = derive.queue(lx, dv, log)
    fat = voice.fatigue(utts, log)
    vc["fatigue"] = fat
    summary = scribe.write(out, meta, utts, ph, lx, signed, refused, fights, vc, log, dv, qu)
    log("CHIEF", f"done in {(time.time()-t0)/60:.1f} min · WORDS SAVED {summary['words_saved']} · RULES {summary['rules_signed']} · FIGHTS {summary['fights_open']} · SHIFTS {summary['register_shifts']} · SPEAKERS LEFT 1")
    if a.reuse and (out / "log.txt").exists():
        (out / "log_reuse.txt").write_text("\n".join(log.lines) + "\n", encoding="utf-8")   # never overwrite the log of a full run
    else:
        log.save()
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
