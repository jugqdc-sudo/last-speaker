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
                                utts=[{"id": i, "start": float(i)} for i in range(60)],
                                log=lambda *a, **k: None)[:2]
    ids_signed = {r["id"] for r in signed}
    assert 1 in ids_signed, "a rule with support 11 across 10 stems must pass"
    assert 2 not in ids_signed, "a rule heard 5 times must be refused"
    assert any("6" in (r.get("why") or "") for r in refused), "a refusal must carry its reason"


def _tiny_desk():
    """A toy tape with a real paradigm gap.

    Four stems take both endings. A fifth stem is heard just as often, but only ever with
    the first ending and with a filler - so it IS a stem to the desk, and the pair
    (fifth stem + second ending) is the one thing the grammar allows and nobody said.

    The trap this test walked into twice: a stem that only ever appears before ONE ending
    never becomes a stem at all - LEX glues it into a single chain. A stem has to be heard
    in two different contexts before there is anything to derive from.
    """
    stems = [["k", "a", "t"], ["m", "o", "p"], ["s", "i", "l"], ["b", "u", "n"]]
    gap_stem = ["ɡ", "e", "r"]
    E1, E2, FILL = ["ʌ", "ɾ", "ɒ"], ["ɒ", "x", "ɒ"], ["z", "e", "w"]
    utts, i = [], 0
    for st in stems:
        for _ in range(2):
            utts.append({"id": i, "phones": st + E1}); i += 1
            utts.append({"id": i, "phones": st + E2}); i += 1
    # exactly twice with each: the stem itself is heard 4 times and becomes a word, while
    # the stem+ending chains stay under the threshold - otherwise greedy segmentation always
    # takes the longest chain and the stem is never split out at all
    for _ in range(2):
        utts.append({"id": i, "phones": gap_stem + E1}); i += 1      # but NEVER with the second
        utts.append({"id": i, "phones": gap_stem + FILL}); i += 1
    return utts


def test_derive_finds_the_form_nobody_said():
    """The point of DAY 7: a form the rules allow that is on no second of the tape."""
    from agents import derive
    utts = _tiny_desk()
    lx = lex.run(utts, log=lambda *a, **k: None, min_count=3, min_utts=3)
    rules, _ = gram.run(utts, lx, log=lambda *a, **k: None, min_support=4, min_stems=3)
    out = derive.run(utts, lx, rules, log=lambda *a, **k: None)
    never = {d["form"] for d in out["never"]}
    assert out["checked"] > 0, "with two endings and shared stems there must be something to derive"
    assert any("ɡ e r" in f and "ɒ x ɒ" in f for f in never), \
        "the one pair never said on the tape must come out of the derivation"
    for d in out["never"]:
        assert d["stem"] and d["rule_form"], "no form may be written without its stem and rule"


def test_derive_stays_silent_without_two_rules():
    """One rule cannot make an analogy. The desk must say so, not invent forms."""
    from agents import derive
    utts = [{"id": i, "phones": ["k", "a", "t", "ʌ", "ɾ", "ɒ"]} for i in range(6)]
    lx = lex.run(utts, log=lambda *a, **k: None, min_count=3, min_utts=3)
    rules, _ = gram.run(utts, lx, log=lambda *a, **k: None, min_support=3, min_stems=1)
    out = derive.run(utts, lx, rules, log=lambda *a, **k: None)
    assert out["checked"] == 0 and out["never"] == []


def test_queue_puts_the_unrebuildable_first():
    """A word the rules can rebuild is not the urgent one; a rare chain nothing produces is."""
    from agents import derive
    utts = _tiny_desk()
    lx = lex.run(utts, log=lambda *a, **k: None, min_count=3, min_utts=3)
    rules, _ = gram.run(utts, lx, log=lambda *a, **k: None, min_support=4, min_stems=3)
    dv = derive.run(utts, lx, rules, log=lambda *a, **k: None)
    q = derive.queue(lx, dv, log=lambda *a, **k: None)
    assert q["total"] > 0
    pri = [r["priority"] for r in q["top"]]
    assert pri == sorted(pri, reverse=True), "the queue must be sorted, most unrecoverable first"
    for r in q["top"]:
        if r["derivable"]:
            assert r["priority"] <= 1.0 / r["heard"], "a rebuildable word must never outrank an unrebuildable one of the same count"


def test_fatigue_reports_a_flat_line_as_a_result():
    """No fade is an answer. The measure must not go quiet when nothing is happening."""
    from agents import voice
    utts = [{"id": i, "start": i * 30.0, "end": i * 30.0 + 4.0, "rate": 10.0, "f0": 150.0,
             "phones": ["a"] * 40} for i in range(80)]
    out = voice.fatigue(utts, log=lambda *a, **k: None, window_min=10.0)
    assert len(out["windows"]) >= 3
    assert out["trend"] is not None
    assert abs(out["trend"]["rate"]["per_window_pct"]) < 1.0, "a flat tape must report a flat trend"


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
