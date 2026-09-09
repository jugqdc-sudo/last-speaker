# -*- coding: utf-8 -*-
"""DERIVE · owns the forms the language allows and nobody ever said on this tape.

The desk has signed rules (a chunk that attaches to many different stems) and it has the
stems those rules were seen on. Proportional analogy: if stem A takes ending 1 and stem B
takes ending 2, then A+2 and B+1 are forms this grammar allows.

Every generated form is then SEARCHED in the whole tape, as an exact phone chain across all
utterances. Whatever is not there is a form the language permits and nobody recorded - the
one thing on this desk that cannot be checked against the audio, because there is no audio.

Nothing is invented from nothing: a form is only written if both halves carry a tape
position. That is the provenance line, and it is the difference between a derivation and
a guess.

stops · never writes a form whose stem or rule has no position on the tape
"""
from collections import defaultdict


def _corpus_text(utts, sym):
    """Whole tape as encoded phone strings, one per utterance, plus a flat index for search."""
    return [(u["id"], sym.enc(u.get("phones", []))) for u in utts]


def _find(chain, texts, limit=3):
    """Where this exact phone chain occurs on the tape. Empty list = NOT FOUND."""
    hits = []
    for uid, t in texts:
        if chain in t:
            hits.append(uid)
            if len(hits) >= limit:
                break
    return hits


def _random_baseline(derived, texts, sym, n, seed=7):
    """Same number of chains, same lengths, phones drawn by how common they are on this tape.
    If random junk lands on the tape as often as our derivations, the derivation means nothing.
    """
    import random
    rng = random.Random(seed)
    alphabet = list(sym.s2p)
    weights = [sum(t.count(ch) for _, t in texts) for ch in alphabet]
    lengths = [len(d["form"].split()) for d in derived] or [6]
    hits = 0
    for i in range(n):
        L = lengths[i % len(lengths)]
        chain = "".join(rng.choices(alphabet, weights=weights, k=L))
        if any(chain in t for _, t in texts):
            hits += 1
    return {"n": n, "hits": hits, "pct": round(hits / max(1, n) * 100, 2)}


def run(utts, lex, rules, log, max_forms=20000):
    """rules here are the SIGNED ones - CHIEF has already thrown out the rest."""
    sym, counts = lex["_sym"], lex["_counts"]
    texts = _corpus_text(utts, sym)

    # which stems this desk actually heard next to each rule
    seen_pairs = set()
    stems_by_kind = defaultdict(set)
    rule_by_kind = defaultdict(list)
    for r in rules:
        w = r.get("_w")
        if w is None or not r.get("utts"):
            continue                                    # no tape position, no rule
        rule_by_kind[r["kind"]].append(r)
        for s in r.get("stem_set", ()):
            stems_by_kind[r["kind"]].add(s)
            seen_pairs.add((s, w))

    derived, checked = [], 0
    producible = set()          # everything the grammar can build, including what he already said
    for kind, rs in rule_by_kind.items():
        for stem in stems_by_kind[kind]:
            if counts.get(stem, 0) < 2:
                continue                                # a stem heard once is itself in doubt
            for r in rs:
                w = r["_w"]
                chain = stem + w if kind == "suffix" else w + stem
                producible.add(chain)
                if (stem, w) in seen_pairs:
                    continue                            # he said this pair: not a derivation
                checked += 1
                if checked > max_forms:
                    break
                hits = _find(chain, texts)
                derived.append({
                    "form": sym.dec(chain),
                    "stem": sym.dec(stem),
                    "rule": r["id"],
                    "rule_form": r["form"],
                    "kind": kind,
                    "stem_heard": counts.get(stem, 0),
                    "rule_heard": r["support"],
                    "on_tape": hits,                    # empty = on no second of the tape
                })

    never = [d for d in derived if not d["on_tape"]]
    on_tape = len(derived) - len(never)
    log("DERIVE", f"{checked} forms the signed rules allow · {on_tape} of them are on the tape after all · "
                  f"{len(never)} were never recorded by anybody")

    # ── the check against ourselves: would a random chain of the same length land too? ──
    # without this line the hits above mean nothing: maybe anything at all lands on this tape.
    if not derived:
        # never go quiet on an empty result: say why there is nothing to derive
        kinds = {k: len(v) for k, v in rule_by_kind.items()}
        log("DERIVE", f"nothing to derive · signed rules by kind: {kinds or 'none'} · analogy needs at least two "
                      f"rules of one kind sharing stems. that is not enough tape, not an empty language")
        baseline = {"n": 0, "hits": 0, "pct": 0.0}
    else:
        baseline = _random_baseline(derived, texts, sym, n=len(derived))
        log("DERIVE", f"control · {baseline['hits']} of {baseline['n']} RANDOM chains of the same lengths are on "
                      f"the tape ({baseline['pct']}%) against our {on_tape} ({round(on_tape/len(derived)*100,2)}%) - "
                      + ("the rules are predicting, not guessing" if on_tape > baseline["hits"]
                         else "no better than chance, do not trust the derivation"))
    if never:
        e = never[0]
        log("DERIVE", f"example: [{e['form']}] = stem [{e['stem']}] + rule {e['rule']} [{e['rule_form']}] · "
                      f"searched the whole tape, not there")
    return {"checked": checked, "on_tape": on_tape, "never": never,
            "baseline": baseline, "_producible": producible}


def queue(lex, derived, log, keep=400):
    """The queue: which words die with him.

    A word the rules can rebuild after he is gone is not the urgent one. A chain heard once
    or twice that no rule produces is the one nobody will ever recover. That ordering is the
    whole of DAY 8: priority is not importance, it is what cannot be rebuilt.
    """
    sym, counts, where = lex["_sym"], lex["_counts"], lex["_where"]
    producible = derived.get("_producible", set())   # everything the grammar can build on its own
    rows = []
    for w, c in counts.items():
        derivable = w in producible
        # the rarer it is and the less a rule can rebuild it, the higher it sits
        score = round((1.0 / c) * (0.25 if derivable else 1.0), 4)
        rows.append({"form": sym.dec(w), "heard": c, "utts": len(set(where.get(w, ()))),
                     "derivable": derivable, "priority": score})
    rows.sort(key=lambda r: (-r["priority"], r["heard"]))
    unrecoverable = sum(1 for r in rows if r["heard"] <= 2 and not r["derivable"])
    log("LEX", f"queue built · {len(rows)} words · {unrecoverable} of them heard twice or less and no rule "
               f"can rebuild them: those are the ones that go when he goes")
    return {"total": len(rows), "unrecoverable": unrecoverable, "top": rows[:keep]}
