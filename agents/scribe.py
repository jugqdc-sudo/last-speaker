# -*- coding: utf-8 -*-
"""SCRIBE · owns the log, tape positions.
Writes the case log, run.json and report.md. Nothing without a source: every line carries a tape position."""
import json, time
from core import tape

# stops · never writes without a source


class Log:
    def __init__(self, out):
        self.lines = []
        self.out = out
        self.t0 = time.time()

    def __call__(self, who, text):
        line = f"{time.strftime('%H:%M:%S')}  {who:<6} {text}"
        self.lines.append(line)
        print(line, flush=True)

    def save(self):
        (self.out / "log.txt").write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def write(out, meta, utts, phon, lex, rules, refused, fights, voice, log, derived=None, queue=None):
    for r in rules:                     # DERIVE's working fields never go into the json
        r.pop("stem_set", None); r.pop("_w", None)
    spoken = sum(u["end"] - u["start"] for u in utts)
    total_ph = sum(phon["inventory"].values()) or 1
    core = [(p, c) for p, c in phon["inventory"].items() if c / total_ph >= 0.005]
    core_v = [p for p, _ in core if p in phon["vowels"]]
    summary = {
        "source": meta,
        "tape_hours": tape.hours(meta["seconds"]),
        "speech_hours": tape.hours(spoken),
        "utterances": len(utts),
        "phones": sum(len(u.get("phones", [])) for u in utts),
        "inventory": len(phon["inventory"]),
        "vowels": len(phon["vowels"]),
        "consonants": len(phon["consonants"]),
        "core_inventory": len(core),
        "core_vowels": len(core_v),
        "core_share": round(sum(c for _, c in core) / total_ph, 3),
        "words_saved": lex["types"],
        "word_tokens": lex["tokens"],
        "heard_only_once": lex["hapax"],
        "rules_written": len(rules) + len(refused),
        "rules_signed": len(rules),
        "rules_refused": len(refused),
        "fights_open": len(fights),
        "register_shifts": len(voice["shifts"]),
        "median_f0": voice["median_f0"],
        "median_rate": voice["median_rate"],
        "speakers_left": 1,
    }
    if derived:
        summary["forms_the_rules_allow"] = derived["checked"]
        summary["derived_found_on_tape"] = derived["on_tape"]
        summary["derived_never_recorded"] = len(derived["never"])
        summary["control_random_on_tape"] = derived.get("baseline", {}).get("hits")
    if queue:
        summary["queue_words"] = queue["total"]
        summary["die_with_him"] = queue["unrecoverable"]
    fat = (voice or {}).get("fatigue") or {}
    if fat.get("trend") is not None:
        summary["fade_across_tape"] = fat["trend"]
    run = {
        "summary": summary,
        "inventory": {"vowels": phon["vowels"], "consonants": phon["consonants"]},
        "words_top": lex["top"],
        "rules": rules, "refused": refused, "fights": fights,
        "voice": voice,
        "derived": ({"checked": derived["checked"], "on_tape": derived["on_tape"],
                     "baseline": derived.get("baseline"),
                     "never_recorded": [{k: v for k, v in d.items() if k != "on_tape"}
                                        for d in derived["never"][:500]]} if derived else None),
        "queue": queue,
        "utterances": [{k: v for k, v in u.items() if k in ("id", "start", "end", "phones", "words", "f0", "rate", "register")} for u in utts],
    }
    (out / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
    s = summary
    md = [f"# THE LAST SPEAKER · case report", "",
          f"source: {meta['title']} ({meta['url']})", "",
          f"| what | number |", "|---|---|",
          f"| tape | {s['tape_hours']} h |", f"| speech on it | {s['speech_hours']} h |",
          f"| utterances | {s['utterances']} |", f"| phones heard | {s['phones']} |",
          f"| sounds heard (narrow) | {s['inventory']} ({s['vowels']} vowels, {s['consonants']} consonants) |",
          f"| core inventory (≥0.5% of the tape) | {s['core_inventory']} sounds, {s['core_vowels']} vowels, carrying {s['core_share']*100:.0f}% of everything said |",
          f"| words saved | {s['words_saved']} |", f"| heard only once | {s['heard_only_once']} |",
          f"| rules written | {s['rules_written']} |", f"| rules signed by CHIEF | {s['rules_signed']} |",
          f"| rules refused | {s['rules_refused']} |", f"| fights open | {s['fights_open']} |",
          f"| register shifts (not his usual voice) | {s['register_shifts']} |",
          f"| speakers left | 1 |", "",
          "## vowels nobody wrote down", ", ".join(f"{p} ×{c}" for p, c in list(phon["vowels"].items())[:12]), "",
          "## most frequent word candidates", ""]
    md += [f"- `{w['form']}` ×{w['count']}" for w in lex["top"][:15]]
    md += ["", "## rules signed"]
    md += [f"- rule {r['id']} · {r['kind']} `{r['form']}` · {r['support']} times on {r['stems']} stems · e.g. {', '.join(e['pos'] for e in r['examples'][:3])}" for r in rules[:15]]
    md += ["", "## fights (the language gives two answers, nobody alive to settle it)"]
    md += [f"- rule {f['a']} `{f['a_form']}` vs rule {f['b']} `{f['b_form']}` · {f['why']}" for f in fights[:12]]
    md += ["", "## refused by CHIEF"]
    md += [f"- rule {x['rule']} `{x['form']}` · {x['why']}" for x in refused[:20]]
    if derived:
        b = derived.get("baseline") or {}
        md += ["", "## forms the grammar allows and nobody ever said", "",
               f"| what | number |", "|---|---|",
               f"| forms the signed rules produce | {derived['checked']} |",
               f"| of those, actually on the tape | {derived['on_tape']} |",
               f"| never recorded by anybody | {len(derived['never'])} |",
               f"| control: RANDOM chains of the same lengths found on the tape | {b.get('hits','-')} of {b.get('n','-')} |",
               "",
               "the control line is the point. if random junk landed on the tape as often as these forms,",
               "the derivation would mean nothing. each form below carries the stem and the rule it came",
               "from, and both of those carry tape positions - that is the whole provenance.", ""]
        md += [f"- `{d['form']}` = stem `{d['stem']}` + rule {d['rule']} `{d['rule_form']}`"
               f" (stem heard {d['stem_heard']}×, rule {d['rule_heard']}×)" for d in derived["never"][:15]]
    if queue:
        md += ["", "## the queue · what goes when he goes", "",
               f"{queue['unrecoverable']} of {queue['total']} word candidates were heard twice or less AND no",
               "signed rule can rebuild them. those are the ones with nobody to ask.", ""]
        md += [f"- `{r['form']}` heard {r['heard']}× in {r['utts']} utterances"
               + (" · rules can rebuild it" if r["derivable"] else " · **nothing can rebuild it**")
               for r in queue["top"][:15]]
    if fat.get("windows"):
        md += ["", "## does the voice fade across the tape", "",
               "| window | utterances | speech share | phones/s | pitch | median utterance |", "|---|---|---|---|---|---|"]
        md += [f"| {w['window']} | {w['utterances']} | {w['speech_share']} | {w['rate']} | {w['f0']} | {w['utt_seconds']} s |"
               for w in fat["windows"]]
        if fat.get("trend"):
            md += ["", "trend per window: " + ", ".join(f"{k} {v['per_window_pct']:+.1f}%" for k, v in fat["trend"].items()),
                   "", "a flat line here is a result: on this tape he does not slow down. the serial's",
                   "voice budget needs sessions months apart, and one recording cannot give that."]
    md += ["", "## what this is not",
           "no dictionary of the language was used, nothing here is a translation, and a 'rule' is a chain that",
           "keeps attaching to different neighbours, not a grammar. every line above carries a tape position so you can go and listen."]
    md += ["", "## register shifts (where he is not using his own voice)"]
    md += [f"- {v['pos']} · pitch {v['f0']} Hz (z {v['z_pitch']}) · {v['rate']} phones/s (z {v['z_rate']})" for v in voice["shifts"][:15]]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    log("SCRIBE", f"filed run.json, report.md, log.txt in {out}")
    return summary
