# -*- coding: utf-8 -*-
"""GRAM · owns the rules, the exceptions.
A rule here = a chunk that attaches to MANY different neighbours (suffix/prefix candidate).
A fight = one stem takes two different endings: the language gives two answers."""
from collections import defaultdict, Counter

# stops · never drops a contradiction


def one_phone_apart(a, b):
    """Forms differ by exactly one phone at equal length: 'ɒ x ɒ' against 'ɒ ʁ ɒ'."""
    if len(a) != len(b): return False
    return sum(1 for x, y in zip(a, b) if x != y) == 1


def run(utts, lex, log, min_support=4, min_stems=3):
    """GRAM writes anything that looks like a rule (low bar); CHIEF signs it (high bar)."""
    sym, counts = lex["_sym"], lex["_counts"]
    left, right = defaultdict(Counter), defaultdict(Counter)   # morph → neighbours on the left / right
    occ = defaultdict(list)                                    # morph → [(utt, idx)]
    for u in utts:
        ws = u.get("words", [])
        for i, w in enumerate(ws):
            occ[w].append((u["id"], i))
            if i > 0: left[w][ws[i - 1]] += 1
            if i < len(ws) - 1: right[w][ws[i + 1]] += 1
    rules = []
    for w, c in counts.items():
        if c < min_support: continue
        stems_l, stems_r = len(left[w]), len(right[w])
        # suffix: many different neighbours on the left, few on the right; prefix is the mirror
        if stems_l >= min_stems and stems_l >= 1.6 * max(1, stems_r):
            kind, stems = "suffix", left[w]
        elif stems_r >= min_stems and stems_r >= 1.6 * max(1, stems_l):
            kind, stems = "prefix", right[w]
        else:
            continue
        rules.append({"form": sym.dec(w), "_w": w, "kind": kind, "support": c, "stems": len(stems),
                      "stem_set": set(stems), "utts": sorted({uid for uid, _ in occ[w]})})
    rules.sort(key=lambda r: (-r["stems"], -r["support"]))
    rules = rules[:60]
    for i, r in enumerate(rules): r["id"] = i + 1
    # fights: (a) two endings share ≥2 stems - one stem takes both;
    #        (b) two rules of the same kind differ by one phone - the language answers twice
    fights = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            a, b = rules[i], rules[j]
            if a["kind"] != b["kind"]: continue
            shared = a["stem_set"] & b["stem_set"]
            if len(shared) >= 2:
                fights.append({"a": a["id"], "b": b["id"], "a_form": a["form"], "b_form": b["form"],
                               "why": f"same stem takes both ({len(shared)} stems shared)",
                               "example_stem": sym.dec(next(iter(shared)))})
            elif one_phone_apart(a["_w"], b["_w"]):
                fights.append({"a": a["id"], "b": b["id"], "a_form": a["form"], "b_form": b["form"],
                               "why": "one phone apart, both come back: two answers"})
    log("GRAM", f"{len(rules)} rules written ({sum(r['kind']=='suffix' for r in rules)} endings, {sum(r['kind']=='prefix' for r in rules)} prefixes) · {len(fights)} of them fight each other")
    return rules, fights
