# -*- coding: utf-8 -*-
"""LEX · owns the words, counts of one.
A phone stream has no spaces and no dictionary. A word candidate = a chain of phones that
COMES BACK: at least min_count times, across at least min_utts different utterances.
We keep maximal chains (3-7 phones) and cut the stream greedily by the longest match.
Whatever matches nothing is 'heard only once' - it could mean anything.
(Morfessor was tried and dropped: on a continuous stream with no lexicon it either cuts at
every single phone or does not cut at all.)"""
import unicodedata
from collections import Counter, defaultdict

# stops · never guesses from context


def broad(phone):
    """Broad transcription: strip diacritics, length and aspiration. PHON keeps the narrow one,
    LEX matches on the skeleton - otherwise 'aː' and 'a' never meet and nothing repeats."""
    b = "".join(ch for ch in unicodedata.normalize("NFD", phone)
                if unicodedata.category(ch) not in ("Mn", "Lm", "Sk"))
    return b or phone


class Symbols:
    """Each (broad) phone → one private-use character: 'tʃ' must never be cut into 't'+'ʃ'."""
    def __init__(self):
        self.p2s, self.s2p = {}, {}

    def enc(self, phones):
        out = []
        for p in phones:
            p = broad(p)
            if p not in self.p2s:
                s = chr(0xE000 + len(self.p2s))
                self.p2s[p] = s; self.s2p[s] = p
            out.append(self.p2s[p])
        return "".join(out)

    def dec(self, s):
        return " ".join(self.s2p[ch] for ch in s)


def run(utts, log, nmin=3, nmax=7, min_count=3, min_utts=3):
    sym = Symbols()
    texts = [(u["id"], sym.enc(u.get("phones", []))) for u in utts]
    # 1. every n-gram: how many times, and across how many utterances
    cnt, inutt = Counter(), defaultdict(set)
    for uid, t in texts:
        for n in range(nmin, nmax + 1):
            for i in range(len(t) - n + 1):
                g = t[i:i + n]; cnt[g] += 1; inutt[g].add(uid)
    cand = {g: c for g, c in cnt.items() if c >= min_count and len(inutt[g]) >= min_utts}
    # 2. maximal only: a short chain is dropped if it almost always sits inside a longer one
    longer = sorted(cand, key=len, reverse=True)
    keep = {}
    for g in longer:
        inside = any(g in h and cand[h] >= 0.7 * cand[g] for h in keep)
        if not inside:
            keep[g] = cand[g]
    # 3. segmentation: greedy, longest match, left to right
    words, where = Counter(), defaultdict(list)
    loose = Counter()
    for uid, t in texts:
        segs, i, buf = [], 0, ""
        while i < len(t):
            hit = None
            for n in range(nmax, nmin - 1, -1):
                g = t[i:i + n]
                if len(g) == n and g in keep: hit = g; break
            if hit:
                if buf: segs.append(("?", buf)); buf = ""
                segs.append(("w", hit)); words[hit] += 1; where[hit].append(uid); i += len(hit)
            else:
                buf += t[i]; i += 1
        if buf: segs.append(("?", buf))
        for kind, s in segs:
            if kind == "?" and len(s) >= nmin: loose[s] += 1
        utts[uid]["words"] = [s for kind, s in segs if kind == "w"]
        utts[uid]["segments"] = [(kind, sym.dec(s)) for kind, s in segs]
    hapax = sum(1 for s, c in loose.items() if c == 1)
    covered = sum(len(w) * c for w, c in words.items()) / max(1, sum(len(t) for _, t in texts))
    log("LEX", f"{len(words)} word candidates (chains that come back ≥{min_count}× in ≥{min_utts} utterances) · {sum(words.values())} tokens · {covered*100:.0f}% of the tape covered · {hapax} stretches heard exactly once, so they could mean anything")
    top = [{"form": sym.dec(w), "count": c, "utts": sorted(set(where[w]))[:5]} for w, c in words.most_common(40)]
    return {"types": len(words), "tokens": sum(words.values()), "hapax": hapax, "covered": round(covered, 3),
            "top": top, "_sym": sym, "_counts": words, "_where": where}
