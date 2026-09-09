#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A terminal page built from a real run: docs/index.html out of runs/<name>/run.json + log.txt.
Every tape position is a link to that second of the recording on YouTube."""
import json, pathlib, re, sys, html

name = sys.argv[1] if len(sys.argv) > 1 else "torwali"
# a page is named after its run by default; index.html stays with torwali.
# without this, `make_site.py piedmontese` silently overwrites another tape's page
page_name = sys.argv[2] if len(sys.argv) > 2 else ("index" if sys.argv[1] == "torwali" else sys.argv[1])
root = pathlib.Path(__file__).parent
run = json.loads((root / "runs" / name / "run.json").read_text())
log = (root / "runs" / name / "log.txt").read_text().splitlines()
s, meta = run["summary"], run["summary"]["source"]
utts = {u["id"]: u for u in run["utterances"]}
lang = {"torwali": "Torwali", "piedmontese": "Piedmontese"}.get(name, name)
vid = re.search(r"v=([\w-]+)", meta["url"] or "")
vid = vid.group(1) if vid else ""


def yt(sec):
    return f"https://www.youtube.com/watch?v={vid}&t={int(sec)}s" if vid else "#"


def pos(sec):
    sec = int(sec); return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"


def link(uid):
    st = utts[uid]["start"]
    return f'<a class="pos" href="{yt(st)}" target="_blank">{pos(st)}</a>'


e = html.escape
words = run["words_top"][:21]
rules = run["rules"][:19]
fights = run["fights"][:9]
refused = run["refused"]
shifts = sorted(run["voice"]["shifts"], key=lambda x: -abs(x["z_pitch"]))[:12]
vow = list(run["inventory"]["vowels"].items())[:12]
vmax = max(c for _, c in vow) if vow else 1

cards = "".join(
    f'<div class="card"><div class="ipa">{e(w["form"])}</div><div class="cnt">×{w["count"]}</div>'
    f'<div class="where">{" ".join(link(u) for u in w["utts"][:2])}</div></div>' for w in words)
rule_rows = "".join(
    f'<tr><td class="n">{r["id"]}</td><td class="k">{r["kind"]}</td><td class="ipa">{e(r["form"])}</td>'
    f'<td>{r["support"]}× on {r["stems"]} stems</td><td>{" ".join(link(x["utt"]) for x in r["examples"][:3])}</td></tr>'
    for r in rules)
fight_rows = "".join(
    f'<tr><td class="ipa">{e(f["a_form"])}</td><td class="vs">vs</td><td class="ipa">{e(f["b_form"])}</td><td>{e(f["why"])}</td></tr>'
    for f in fights)
ref_rows = "".join(f'<li><span class="ipa">{e(x["form"])}</span> · {e(x["why"])}</li>' for x in refused[:10])
shift_rows = "".join(
    f'<tr><td>{link(v["utt"])}</td><td>{v["f0"]} Hz</td><td class="{"hi" if v["z_pitch"]>0 else "lo"}">z {v["z_pitch"]:+.1f}</td>'
    f'<td>{v["rate"]} phones/s</td></tr>' for v in shifts)
vow_bars = "".join(
    f'<div class="vb"><span class="ipa">{e(p)}</span><i style="width:{int(180*c/vmax)}px"></i><b>{c}</b></div>' for p, c in vow)
log_rows = "".join(f'<div>{e(l)}</div>' for l in log)

dv = run.get("derived") or {}
qu = run.get("queue") or {}
fat = (run.get("voice") or {}).get("fatigue") or {}
der_rows = "".join(
    f'<tr><td class="ipa">{e(d["form"])}</td><td class="ipa">{e(d["stem"])}</td>'
    f'<td class="n" style="white-space:nowrap">+ rule {d["rule"]}</td><td class="ipa">{e(d["rule_form"])}</td>'
    f'<td>stem {d["stem_heard"]}× · rule {d["rule_heard"]}×</td></tr>'
    for d in (dv.get("never_recorded") or [])[:14])
q_rows = "".join(
    f'<tr><td class="ipa">{e(r["form"])}</td><td>{r["heard"]}× in {r["utts"]} utterances</td>'
    f'<td class="{"mint" if r["derivable"] else "red"}">'
    f'{"rules can rebuild it" if r["derivable"] else "nothing can rebuild it"}</td></tr>'
    for r in (qu.get("top") or [])[:14])
fat_rows = "".join(
    f'<tr><td>{e(w["window"])}</td><td>{w["utterances"]}</td><td>{w["speech_share"]}</td>'
    f'<td>{w["rate"]}</td><td>{w["f0"]}</td><td>{w["utt_seconds"]} s</td></tr>'
    for w in (fat.get("windows") or []))
fat_trend = ", ".join(f'{k} {v["per_window_pct"]:+.1f}%' for k, v in (fat.get("trend") or {}).items())
b = dv.get("baseline") or {}

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE LAST SPEAKER · {e(name)} · case report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Instrument+Serif&display=swap" rel="stylesheet">
<style>
:root{{--paper:#f4f2ec;--card:#f7f6f1;--ink:#2b302a;--dim:#7b8378;--faint:#a8b0a3;--line:#c9cec6;--red:#c04a3c;--mint:#2f6b4a;--amber:#8a6a2a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:"JetBrains Mono",ui-monospace,Menlo,monospace;font-size:13px;line-height:1.6}}
a{{color:var(--mint)}} .wrap{{max-width:1080px;margin:0 auto;padding:22px 18px 60px}}
.top{{display:flex;gap:14px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px;letter-spacing:2px;font-size:11px}}
.top b{{letter-spacing:2px}} .pill{{border:1px solid var(--line);padding:2px 8px;border-radius:2px;font-size:10px;font-weight:700}}
.pill.red{{background:#f0dcd8;color:var(--red);border-color:#e6c6c0}} .pill.mint{{background:#d9ecdf;color:var(--mint);border-color:#c5dccb}}
h1{{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:44px;margin:26px 0 4px;line-height:1.05}}
.sub{{color:var(--dim);margin-bottom:22px}} .sub a{{color:var(--dim)}}
.strip{{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--line);background:var(--card);margin:18px 0 28px}}
.strip div{{padding:10px 16px;border-right:1px solid var(--line);font-size:11px;letter-spacing:1.5px;color:var(--dim)}}
.strip b{{display:block;font-size:22px;letter-spacing:0;color:var(--ink);font-family:"Instrument Serif",serif;font-weight:400}}
.strip b.red{{color:var(--red)}} .strip b.mint{{color:var(--mint)}}
h2{{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--dim);margin:34px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
.wall{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;background:#efece2;border:6px solid #9b8b72;padding:16px}}
.card{{background:var(--card);padding:10px 10px 8px;box-shadow:0 1px 0 #d8d3c6;position:relative}}
.card:before{{content:"";position:absolute;left:50%;top:-4px;width:6px;height:6px;margin-left:-3px;background:var(--red)}}
.card:nth-child(3n+2):before{{background:#57a07a}} .card:nth-child(3n):before{{background:#c8913a}}
.ipa{{font-weight:700;font-size:15px}} .cnt{{color:var(--dim);font-size:11px}} .where{{font-size:10px;margin-top:4px}}
.pos{{color:var(--mint);text-decoration:none;border-bottom:1px dotted var(--mint);margin-right:6px}}
table{{border-collapse:collapse;width:100%;background:var(--card)}} td{{padding:6px 10px;border-bottom:1px solid #e6e3da;vertical-align:top}}
td.n{{color:var(--dim);width:32px}} td.k{{color:var(--amber);width:70px}} td.vs{{color:var(--red);font-weight:700;width:30px}}
td.hi{{color:var(--red);font-weight:700}} td.lo{{color:var(--mint);font-weight:700}}
.vb{{display:flex;align-items:center;gap:10px;margin:3px 0}} .vb i{{display:block;height:10px;background:#c8913a}} .vb b{{color:var(--dim);font-weight:400;font-size:11px}}
.log{{background:#16190f;color:#cfd5c9;padding:14px 16px;font-size:11.5px;line-height:1.7;overflow:auto;white-space:nowrap}}
.note{{background:#fbf7ea;border-left:3px solid #c8913a;padding:10px 14px;color:#4a4f45}}
ul{{padding-left:18px}} li{{margin:3px 0}}
.foot{{margin-top:40px;color:var(--faint);font-size:11px}}
</style></head><body><div class="wrap">
<div class="top"><b>COLD.DESK</b><span>CASE 01 · THE LAST SPEAKER · REAL TAPE</span><span class="pill red">● ONE SPEAKER</span><span class="pill">NO DICTIONARY · NO TRANSLATION</span><span class="pill mint">EVERY LINE HAS A TAPE POSITION</span></div>
<h1>what six agents pulled out of {s['tape_hours']} hours of one man speaking {e(lang)}</h1>
<div class="sub">tape: <a href="{e(meta['url'])}" target="_blank">{e(meta['title'])}</a> · Wikitongues, CC BY · every timestamp below opens that second of the recording</div>
<div class="strip">
<div>WORDS SAVED<b>{s['words_saved']:,}</b></div><div>HEARD ONLY ONCE<b>{s['heard_only_once']:,}</b></div>
<div>RULES SIGNED<b class="mint">{s['rules_signed']}</b></div><div>RULES REFUSED<b class="red">{s['rules_refused']}</b></div>
<div>FIGHTS OPEN<b class="red">{s['fights_open']}</b></div><div>NOT HIS USUAL VOICE<b>{s['register_shifts']}</b></div>
<div>SOUNDS · CORE<b>{s['inventory']} · {s['core_inventory']}</b></div><div>SPEECH ON TAPE<b>{s['speech_hours']} h</b></div><div>SPEAKERS LEFT<b class="red">1</b></div>
{f'<div>NEVER RECORDED<b class="red">{s["derived_never_recorded"]:,}</b></div>' if s.get("derived_never_recorded") else ''}
{f'<div>DIE WITH HIM<b class="red">{s["die_with_him"]:,}</b></div>' if s.get("die_with_him") else ''}
</div>
<h2>the wall · chains that keep coming back</h2>
<div class="wall">{cards}</div>
<h2 id="rules">rules signed by CHIEF · a chain that attaches to many different neighbours</h2>
<table>{rule_rows}</table>
<h2 id="fights">fights · two answers, nobody alive to settle it</h2>
<table>{fight_rows}</table>
<h2>the gate · refused ({len(refused)})</h2>
<ul>{ref_rows}{'<li>… and ' + str(len(refused)-10) + ' more in report.md</li>' if len(refused) > 10 else ''}</ul>
<h2 id="voice">his voice · where the register shifts (median {s['median_f0']} Hz, {s['median_rate']} phones/s)</h2>
<table>{shift_rows}</table>
<h2>vowels nobody wrote down</h2>
{vow_bars}
<h2>case log</h2>
<div class="log">{log_rows}</div>
{f'''<h2 id="derived">forms this grammar allows that nobody ever said</h2>
<div class="note">run the signed rules the other way: if one stem takes an ending and another stem takes a different one, both crossings are forms the language permits. every one of them was then searched across all {s['utterances']:,} utterances as an exact phone chain. <b>{dv.get("checked",0):,} forms · {dv.get("on_tape",0)} turned out to be on the tape after all · {s.get("derived_never_recorded", 0):,} are on no second of it (first 14 below).</b><br><br><b>control:</b> {b.get("hits","-")} of {b.get("n","-"):,} RANDOM chains of the same lengths land anywhere on this tape. without that line the hits above would mean nothing.</div>
<table>{der_rows}</table>''' if der_rows else ''}
{f'''<h2 id="queue">the queue · what goes when he goes</h2>
<div class="note">a word the rules can rebuild after he is gone is not the urgent one. a chain heard once or twice that no rule produces is the one nobody recovers. <b>{qu.get("unrecoverable",0):,} of {qu.get("total",0):,}</b> word candidates are in that second group - that is the order to work through, not the frequency list.</div>
<table>{q_rows}</table>''' if q_rows else ''}
{f'''<h2 id="fade">does the voice fade across the tape</h2>
<div class="note">tempo, speech share and utterance length in 10-minute windows. trend per window: <b>{fat_trend or "not enough windows"}</b>. a flat line is a result, not a missing measurement - the serial's voice budget needs sessions months apart, and one recording cannot give that.</div>
<table><tr><td>window</td><td>utterances</td><td>speech share</td><td>phones/s</td><td>pitch</td><td>median utterance</td></tr>{fat_rows}</table>''' if fat_rows else ''}
<h2>what this is not</h2>
<div class="note">no dictionary of the language was used and nothing here is a translation. a "word" is a chain of phones that repeats, a "rule" is a chain that keeps attaching to different neighbours, a "fight" is two of them one phone apart. the register detector hears pitch and tempo, not meaning. a linguist would call this a starting point. that is what it is, and every line carries the second of tape it came from.</div>
<div class="foot">other tapes: <a href="index.html">torwali</a> · <a href="piedmontese.html">piedmontese</a> · desk.py run tape.wav · generated from runs/{e(name)}/run.json</div>
</div></body></html>"""
out = root / "docs"; out.mkdir(exist_ok=True)
(out / f"{page_name}.html").write_text(page, encoding="utf-8")
print(f"docs/{page_name}.html", len(page), "bytes ·", len(words), "cards ·", len(rules), "rules ·", len(shifts), "shifts")
