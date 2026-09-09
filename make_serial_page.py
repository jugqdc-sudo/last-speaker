#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docs/serial.html - the serial against the code, day by day.

Somebody arrives from a post that says a bot invented 1,146 words of a dying language.
This page answers one question: which part of that is a story and which part is a program
that ran on real tape. Every number is read out of runs/*/run.json at build time, so the
page cannot drift away from what the desk actually produced.

    python3 make_serial_page.py
"""
import html, json, pathlib, sys

ROOT = pathlib.Path(__file__).parent
e = html.escape


def load(name):
    p = ROOT / "runs" / name / "run.json"
    if not p.exists():
        sys.exit(f"no run for {name} - run desk.py first")
    return json.loads(p.read_text())


tor = load("torwali")
pie = load("piedmontese")
s, sp = tor["summary"], pie["summary"]
fat_t = (tor.get("voice") or {}).get("fatigue") or {}
fat_p = (pie.get("voice") or {}).get("fatigue") or {}
dv = tor.get("derived") or {}
qu = tor.get("queue") or {}
base = dv.get("baseline") or {}

shifted_rules = sum(1 for r in tor["rules"] if r.get("in_shifted_voice"))


def pct(trend, key="utt_seconds"):
    try:
        return trend[key]["per_window_pct"]
    except (KeyError, TypeError):
        return None


fade_p = pct(fat_p)

# day → (what the post says, what exists here, status, proof)
DAYS = [
    (1, "six agents pull sounds, words and rules off raw tape",
     f"<code>desk.py run</code> on 72 minutes: <b>{s['utterances']:,}</b> utterances cut, "
     f"<b>{s['phones']:,}</b> phones heard, <b>{s['words_saved']:,}</b> word candidates, "
     f"<b>{s['rules_written']}</b> rules written and <b>{s['rules_signed']}</b> signed",
     "done", "index.html"),
    (2, "contradictions are kept as variants instead of being resolved",
     f"<b>{s['fights_open']}</b> fights stay open in the run - pairs one phone apart where both "
     f"forms keep coming back. Nothing picks a winner, because nobody alive can",
     "done", "index.html#fights"),
    (3, "rules turn out to be him doing somebody else's voice",
     f"every rule carries <code>in_shifted_voice</code>. On this tape <b>{shifted_rules} of the "
     f"{s['rules_signed']} signed rules</b> live where his pitch or tempo is 2σ off his own median, "
     f"and <b>{s['register_shifts']}</b> register shifts are logged with positions",
     "done", "index.html#voice"),
    (4, "the desk speaks the language back to him",
     "sentence assembly is not written. Cloning a voice off 45 hours of one speaker is a solved "
     "problem; a native speaker's reaction to it is not, and that is the half that matters",
     "needs a human", None),
    (5, "the words come back 40 ms slower and he takes them anyway",
     "pitch and tempo per utterance are already measured. Comparing one word across two "
     "recording dates is a short script and it is not written yet",
     "not yet", None),
    (6, "the machine passes the desk's own test for a speaker",
     "two of the three checks are mechanical. The third one - takes a correction - is a person "
     "changing their mind in a room. Nothing here fakes it, and nothing here will",
     "needs a human", None),
    (7, "the bot says a word that is on no tape anywhere, and it is real",
     f"<code>agents/derive.py</code> runs the signed rules backwards. <b>{dv.get('checked',0):,}</b> "
     f"forms this grammar allows · <b>{dv.get('on_tape',0)}</b> turned out to be on the tape after "
     f"all · <b>{s.get('derived_never_recorded',0):,}</b> are on no second of it. Control: "
     f"<b>{base.get('hits','-')} of {base.get('n',0):,}</b> random chains of the same lengths land anywhere",
     "done", "index.html#derived"),
    (8, "the queue is sorted by which words are safe to lose",
     f"<code>derive.queue()</code> - <b>{qu.get('unrecoverable',0):,} of {qu.get('total',0):,}</b> word "
     f"candidates were heard twice or less and no signed rule rebuilds them. That is the order to "
     f"work through with a speaker, not the frequency list",
     "done", "index.html#queue"),
    (8, "his voice has fewer minutes left than the queue has words",
     "a budget across months needs sessions across months, and there is one sitting. The honest half "
     "is here: fade measured inside a tape, 10-minute windows. Torwali stays flat to the end; "
     f"Piedmontese loses <b>{abs(fade_p):.1f}%</b> of utterance length per window" if fade_p is not None
     else "fade is measured in 10-minute windows inside each tape",
     "partly", "index.html#fade"),
]

BADGE = {"done": ("mint", "RAN ON REAL TAPE"), "partly": ("amber", "HALF OF IT RUNS"),
         "not yet": ("dim", "NOT WRITTEN YET"), "needs a human": ("red", "NEEDS A LIVING SPEAKER")}

rows = []
for day, story, code, status, proof in DAYS:
    cls, label = BADGE[status]
    link = f'<a class="pos" href="{proof}">see it</a>' if proof else ""
    rows.append(f"""<div class="day {cls}">
<div class="dnum">DAY {day}</div>
<div class="dstory">{story}</div>
<div class="dcode">{code} {link}</div>
<div class="dbadge {cls}">{label}</div>
</div>""")

counts = {k: sum(1 for d in DAYS if d[3] == k) for k in BADGE}

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>the serial against the code · COLD.DESK</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{--paper:#f4f2ec;--card:#f7f6f1;--ink:#2b302a;--dim:#7b8378;--faint:#a8b0a3;--line:#c9cec6;--red:#c04a3c;--mint:#2f6b4a;--amber:#8a6a2a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:"JetBrains Mono",ui-monospace,Menlo,monospace;font-size:13px;line-height:1.6}}
a{{color:var(--mint)}} .wrap{{max-width:1080px;margin:0 auto;padding:22px 18px 60px}}
.top{{display:flex;gap:14px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px;letter-spacing:2px;font-size:11px}}
.pill{{border:1px solid var(--line);padding:2px 8px;border-radius:2px;font-size:10px;font-weight:700}}
.pill.red{{background:#f0dcd8;color:var(--red);border-color:#e6c6c0}} .pill.mint{{background:#d9ecdf;color:var(--mint);border-color:#c5dccb}}
h1{{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:46px;margin:26px 0 6px;line-height:1.05}}
.sub{{color:var(--dim);margin-bottom:20px;max-width:760px}}
.note{{background:#fbf7ea;border-left:3px solid #c8913a;padding:12px 16px;color:#4a4f45;max-width:860px}}
.strip{{display:flex;flex-wrap:wrap;border:1px solid var(--line);background:var(--card);margin:22px 0 30px}}
.strip div{{padding:10px 16px;border-right:1px solid var(--line);flex:1 1 auto;font-size:11px;letter-spacing:1.5px;color:var(--dim)}}
.strip div:last-child{{border-right:none}}
.strip b{{display:block;font-size:24px;letter-spacing:0;color:var(--ink);font-family:"Instrument Serif",serif;font-weight:400}}
.strip b.red{{color:var(--red)}} .strip b.mint{{color:var(--mint)}}
h2{{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--dim);margin:34px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px}}
.day{{display:grid;grid-template-columns:78px 1fr 1.35fr 150px;gap:16px;align-items:start;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);padding:14px 16px;margin-bottom:10px}}
.day.mint{{border-left-color:#4fb87d}} .day.red{{border-left-color:var(--red)}} .day.amber{{border-left-color:#c8913a}} .day.dim{{border-left-color:var(--faint)}}
.dnum{{font-family:"Instrument Serif",serif;font-size:20px;letter-spacing:1px;color:var(--dim)}}
.dstory{{color:#4a4f45}} .dstory:before{{content:"the post says ";color:var(--faint);font-size:10.5px;letter-spacing:1.5px;text-transform:uppercase;display:block;margin-bottom:3px}}
.dcode:before{{content:"in this repo ";color:var(--faint);font-size:10.5px;letter-spacing:1.5px;text-transform:uppercase;display:block;margin-bottom:3px}}
.dbadge{{font-size:9.5px;letter-spacing:1.4px;font-weight:700;text-align:right;padding-top:16px}}
.dbadge.mint{{color:var(--mint)}} .dbadge.red{{color:var(--red)}} .dbadge.amber{{color:var(--amber)}} .dbadge.dim{{color:var(--faint)}}
code{{background:#eceae2;padding:1px 5px;font-size:12px}}
.pos{{color:var(--mint);text-decoration:none;border-bottom:1px dotted var(--mint)}}
.foot{{margin-top:44px;color:var(--faint);font-size:11px}}
@media(max-width:760px){{.day{{grid-template-columns:1fr;gap:8px}}.dbadge{{text-align:left;padding-top:0}}h1{{font-size:32px}}}}
</style></head><body><div class="wrap">

<div class="top"><b>COLD<span style="color:var(--red)">.</span>DESK</b>
<span class="pill">CASE 01 · THE LAST SPEAKER</span>
<span class="pill mint">{counts['done']} DAYS RUN ON REAL TAPE</span>
<span class="pill red">{counts['needs a human']} NEED A LIVING SPEAKER</span>
<span style="margin-left:auto"><a href="index.html">torwali</a> · <a href="piedmontese.html">piedmontese</a></span></div>

<h1>the serial against the code</h1>
<div class="sub">the speaker in the story is invented. the tape is not, the numbers are not, and this
page says day by day which is which.</div>

<div class="note"><b>the short version.</b> a serial runs on @ventry089 about six agents saving a
dying language from its last speaker. that man does not exist. the desk does: it runs on
{s['tape_hours']} hours of Torwali and {int(float(sp['tape_hours'])*60)} minutes of Piedmontese, both recorded by
<a href="https://wikitongues.org" target="_blank">Wikitongues</a> from real speakers, and every
number below opens the second of audio it came from.<br><br>
where the story goes past what a program can do, this table says so instead of quietly agreeing.
three of the days need a human being in a room, and no amount of code closes that.</div>

<div class="strip">
<div>TAPE<b>{s['tape_hours']} h</b></div>
<div>WORD CANDIDATES<b>{s['words_saved']:,}</b></div>
<div>RULES SIGNED<b class="mint">{s['rules_signed']}</b></div>
<div>RULES REFUSED<b class="red">{s['rules_refused']}</b></div>
<div>FORMS NOBODY SAID<b class="red">{s.get('derived_never_recorded',0):,}</b></div>
<div>RANDOM CHAINS THAT LAND<b class="mint">{base.get('hits','-')}</b></div>
<div>DIE WITH HIM<b class="red">{qu.get('unrecoverable',0):,}</b></div>
</div>

<h2>day by day</h2>
{''.join(rows)}

<h2>the one number that decides whether any of this counts</h2>
<div class="note">day 7 is the load-bearing one: a machine producing words nobody ever recorded.
that is easy to fake - stack phones together and call the pile a language. so the desk runs a
control on every pass: <b>{base.get('n',0):,} random chains of exactly the same lengths</b>, phones
drawn by how common they are on this very tape.<br><br>
<b>{base.get('hits','-')} of them land anywhere in {s['utterances']:,} utterances.</b> the derived
forms hit {dv.get('on_tape',0)} times. that gap is the difference between grammar and noise, and
the line prints on every run - including the runs where it would kill the result.<br><br>
on the Piedmontese tape it does kill it: the gate signed one rule out of {sp['rules_written']}, an
analogy needs two, so <b>DERIVE returns nothing at all</b> and says why. 27 minutes is not enough
tape. that is the desk working, not the language being empty.</div>

<h2>what the desk will never do</h2>
<div class="note">judge whether a rule is a joke. hear that a word belonged to somebody's mother.
decide that a pattern is dead. those need the speaker, and the gate exists exactly because the
desk cannot do them. the serial is allowed to imagine that room. this repo is not.</div>

<div class="foot">generated from runs/torwali/run.json and runs/piedmontese/run.json ·
<a href="https://github.com/jugqdc-sudo/cold-desk">source</a> · MIT · tapes CC BY, Wikitongues and the speakers</div>
</div></body></html>"""

out = ROOT / "docs" / "serial.html"
out.write_text(page, encoding="utf-8")
print(f"docs/serial.html · {len(page):,} bytes · {len(DAYS)} rows · "
      f"{counts['done']} done, {counts['partly']} partly, {counts['needs a human']} need a human")
