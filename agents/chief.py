# -*- coding: utf-8 -*-
"""CHIEF · runs the case. Signs nothing without the audio attached.
The gate: a rule passes only if (1) it has tape positions, (2) support is at or above the
threshold, (3) it does NOT live only where the voice is not his own. The third one matters:
a pattern that shows up only when he is doing somebody else's voice is not his grammar."""
from core import tape

# stops · never signs without the tape


def run(rules, fights, voice, utts, log, min_support=6, min_stems=4, foreign_share=0.6):
    shifted = {s["utt"] for s in voice["shifts"]}
    signed, refused = [], []
    for r in rules:
        n = len(r["utts"])
        in_shift = sum(1 for uid in r["utts"] if uid in shifted)
        share = in_shift / n if n else 0
        r["in_shifted_voice"] = in_shift
        r["examples"] = [{"utt": uid, "pos": tape.pos(utts[uid]["start"])} for uid in r["utts"][:4]]
        if n == 0:
            refused.append({"rule": r["id"], "form": r["form"], "why": "no tape position"}); continue
        if r["support"] < min_support:
            refused.append({"rule": r["id"], "form": r["form"], "why": f"heard {r['support']} times, the gate wants {min_support}"}); continue
        if r["stems"] < min_stems:
            refused.append({"rule": r["id"], "form": r["form"], "why": f"attaches to {r['stems']} stems, the gate wants {min_stems}"}); continue
        if share >= foreign_share and n >= 3:
            refused.append({"rule": r["id"], "form": r["form"],
                            "why": f"{in_shift} of {n} occurrences are in a shifted register: not his own voice",
                            "pos": [tape.pos(utts[uid]["start"]) for uid in r["utts"][:3]]})
            continue
        signed.append(r)
    keep = {r["id"] for r in signed}
    fights = [f for f in fights if f["a"] in keep and f["b"] in keep]
    for r in signed:
        r.pop("stem_set", None); r.pop("_w", None)
    log("CHIEF", f"signed {len(signed)} rules · refused {len(refused)} · {len(fights)} fights stay open, nobody alive to settle them")
    for x in refused[:6]:
        log("CHIEF", f"refused rule {x['rule']} [{x['form']}] · {x['why']}")
    if len(refused) > 6:
        log("CHIEF", f"... and {len(refused)-6} more refusals, all in report.md with the reason")
    return signed, refused, fights
