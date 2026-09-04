# -*- coding: utf-8 -*-
"""PHON · owns the sounds, the vowel chart.
Reads phones off every utterance with a universal recognizer (allosaurus, ~2000 languages,
no lexicon for this language). Builds the sound inventory: what is actually on the tape."""
import os
from collections import Counter
from core import tape

# stops · never merges two sounds

VOWEL_CORE = set("aeiouyæɑɒɐɔəɘɚɛɜɝɞɤɨɪɯɵøœɶʉʊʌʏ")


def is_vowel(phone):
    base = "".join(ch for ch in phone if ch.isalpha() and ch in VOWEL_CORE)
    return len(base) > 0 and all((ch in VOWEL_CORE) for ch in phone if ch.isalpha())


def run(audio, utts, log, every=50):
    from allosaurus.app import read_recognizer
    model = read_recognizer()                       # 'latest' model, downloaded once
    inv = Counter()
    for u in utts:
        p = tape.slice_to_tmp(audio, u["start"], u["end"])
        try:
            out = model.recognize(p).strip()
        finally:
            os.unlink(p)
        phones = out.split() if out else []
        u["phones"] = phones
        inv.update(phones)
        if u["id"] % every == 0:
            log("PHON", f"utterance {u['id']} · {tape.pos(u['start'])} · {len(phones)} phones · inventory {len(inv)}")
    vowels = {p: c for p, c in inv.items() if is_vowel(p)}
    cons = {p: c for p, c in inv.items() if not is_vowel(p)}
    log("PHON", f"sound inventory from scratch: {len(inv)} phones · {len(vowels)} vowels · {len(cons)} consonants")
    return {"inventory": dict(inv.most_common()), "vowels": dict(sorted(vowels.items(), key=lambda x: -x[1])),
            "consonants": dict(sorted(cons.items(), key=lambda x: -x[1]))}
