"""Core tests - no audio, no models, no downloads.

The repo is here as evidence, and evidence has to run. The heavy parts (silero-vad,
allosaurus, praat) need models and a tape, so what is checked here is the logic every
number in the README rests on: how words are found, what counts as a fight between two
rules, and why the gate refuses.

    python3 -m pytest tests -q          # or: python3 tests/test_desk.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import lex, gram


def test_broad_strips_length_and_aspiration():
    """LEX matches on the broad skeleton: 'aː' and 'a' are the same, or nothing ever repeats."""
    assert lex.broad("aː") == "a"
    assert lex.broad("tʰ") == "t"
    assert lex.broad("ɒ") == "ɒ"          # a letter of its own, not a diacritic - stays


def test_symbols_keep_affricates_whole():
    """'tʃ' is one phone. Cut it into 't' and 'ʃ' and every rule falls apart."""
    s = lex.Symbols()
    enc = s.enc(["tʃ", "a", "tʃ"])
    assert len(enc) == 3                   # three characters, not five
    assert enc[0] == enc[2]                # same phone, same character
    assert s.dec(enc) == "tʃ a tʃ"


def test_one_phone_apart_is_a_fight():
    """A fight is two forms exactly one phone apart at equal length."""
    assert gram.one_phone_apart("ɒxɒ", "ɒʁɒ") is True
    assert gram.one_phone_apart("ɒxɒ", "ɒxɒ") is False      # identical - not a fight
    assert gram.one_phone_apart("ɒxɒ", "ɒxɒa") is False     # different length - not a fight
    assert gram.one_phone_apart("axb", "ayc") is False      # two phones apart - not a fight


def test_lex_finds_only_repeating_chains():
    """A word is a chain that COMES BACK. Said once, it never becomes a word."""
    # ids must match positions: LEX writes the segmentation back into utts[id]
    utts = [{"id": i, "phones": ["k", "a", "t", "a"]} for i in range(4)]
    utts.append({"id": 4, "phones": ["z", "e", "r", "o"]})    # heard exactly once
    out = lex.run(utts, log=lambda *a, **k: None, min_count=3, min_utts=3)
    forms = {w["form"] for w in out["top"]}
    assert any("k a t" in f for f in forms), "a repeating chain must end up in the words"
    assert not any(f.startswith("z e r") for f in forms), "heard once is not a word"
    assert out["hapax"] >= 1, "a one-off chain must land in the heard-once counter"


def test_gate_refuses_thin_evidence():
    """CHIEF's bar is higher than GRAM's: a thin rule gets written but never signed."""
    try:
        from agents import chief
    except ImportError as e:                      # chief pulls in tape reading
        print("   (skipped: no", str(e).split("'")[1] + ")")
        return
    rules = [{"id": 1, "form": "ʌ ɾ ɒ", "kind": "suffix", "support": 11, "stems": 10, "utts": list(range(11))},
             {"id": 2, "form": "ʔ ɒ tʂ", "kind": "suffix", "support": 5,  "stems": 2,  "utts": list(range(5))}]
    signed, refused = chief.run(rules, fights=[], voice={"shifts": []},
                                utts=[{"id": i} for i in range(60)],
                                log=lambda *a, **k: None)[:2]
    ids_signed = {r["id"] for r in signed}
    assert 1 in ids_signed, "a rule with support 11 across 10 stems must pass"
    assert 2 not in ids_signed, "a rule heard 5 times must be refused"
    assert any("6" in (r.get("why") or "") for r in refused), "a refusal must carry its reason"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn(); print("ok   ", name)
        except Exception as e:
            fails += 1; print("FAIL ", name, "-", str(e)[:120])
    print("\n%s" % ("all green" if not fails else "failed: %d" % fails))
    sys.exit(1 if fails else 0)
