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

# A run that lost its tape metadata would render every timestamp as a dead "#" link - the page
# would still look right and quietly stop being checkable. Fall back to data/sources.json, and
# shout if neither has it, instead of publishing a page full of dead links.
if not (meta.get("url") or "").strip():
    known = json.loads((root / "data" / "sources.json").read_text()).get(name) or {}
    if known.get("url"):
        meta["url"] = known["url"]
        meta["title"] = meta.get("title") or known.get("title", "")
        print(f"  note: run.json had no tape url, took it from data/sources.json ({name})")
    else:
        print(f"!! NO TAPE URL for '{name}' - every timestamp on this page will be a dead link.\n"
              f"   Add it to data/sources.json before publishing.", file=sys.stderr)
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

# адрес контракта показывается, только если он задан: COLD_DESK_CA=... python3 make_site.py
# пустая переменная = блока на странице нет, чтобы не висела заглушка
ca = (__import__("os").environ.get("COLD_DESK_CA") or "").strip()
ca_block = (f'<div class="ca"><span class="lbl">CONTRACT</span><code>{e(ca)}</code>'
            f'<span class="lbl" style="margin-left:auto">THE DESK DOES NOT TRADE · IT READS TAPE</span></div>'
            ) if ca else ""

# ── фактура и движение ──────────────────────────────────────────────────────────
# Всё, что ниже, сделано тем же языком, что и ролики сериала: зерно печати, лента плёнки,
# курсор воспроизведения. Смысл не в украшении - страница должна читаться как продолжение
# видео, а не как лендинг. Обычные строки, не f-строки: иначе пришлось бы удваивать
# каждую скобку в CSS и JS.
ANIM_CSS = """
/* ── фактура: зерно печати поверх всего, как на плёнке ── */
body:before{content:"";position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.55;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='3'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='.42'/%3E%3C/svg%3E")}
/* тёплая виньетка по краям - бумага под лампой, а не белый экран */
body:after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
  background:radial-gradient(120% 80% at 50% 0%,rgba(255,252,242,.55),transparent 60%),
             radial-gradient(100% 60% at 50% 100%,rgba(120,110,88,.09),transparent 60%)}
.wrap{position:relative;z-index:2}
.bar{z-index:30}

/* ── лента плёнки под шапкой: идёт всегда, как ticker в роликах ── */
.film{position:sticky;top:44px;z-index:25;margin:0 -18px;height:20px;overflow:hidden;
  background:#16190f;display:flex;align-items:center}
.film .strip2{display:flex;gap:0;animation:roll 26s linear infinite;will-change:transform}
.film i{display:block;width:13px;height:9px;margin-right:13px;background:#8d7b5f;flex:none}
.film i:nth-child(5n+1){background:#c8913a}
.film .pos2{position:absolute;right:12px;color:#cfd5c9;font-size:9px;letter-spacing:1.6px}
@keyframes roll{to{transform:translateX(-520px)}}

/* ── герой: живая дорожка под заголовком ── */
.wavewrap{position:relative;margin:18px 0 2px;height:64px}
.wavewrap canvas{display:block;width:100%;height:64px}
.wavewrap .cap{position:absolute;right:0;bottom:-14px;font-size:9.5px;letter-spacing:1.8px;color:var(--faint)}

/* логотип дышит вместе с дорожкой */
.hero .mark{animation:breathe 6.5s ease-in-out infinite}
@keyframes breathe{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}

/* ── появление секций при прокрутке ── */
.rv{opacity:0;transform:translateY(14px);transition:opacity .7s cubic-bezier(.2,.7,.3,1),transform .7s cubic-bezier(.2,.7,.3,1)}
.rv.on{opacity:1;transform:none}

/* ── таймкоды: подсветка как у живой позиции на плёнке ── */
.pos{position:relative;padding:1px 3px;transition:background .18s,color .18s}
.pos:hover{background:#d9ecdf;color:#1d4a33;border-bottom-style:solid}
.pos:before{content:"";position:absolute;left:-3px;top:50%;width:3px;height:3px;margin-top:-1.5px;
  background:var(--mint);opacity:0;transition:opacity .18s}
.pos:hover:before{opacity:1}

/* ── карточки стены слегка оживают ── */
.card{transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-2px);box-shadow:0 6px 14px rgba(70,64,48,.14)}
.wall{position:relative}
.wall:after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 40%,rgba(255,255,255,.28) 47%,transparent 54%);
  background-size:280% 100%;animation:sheen 9s ease-in-out infinite}
@keyframes sheen{0%,72%{background-position:120% 0}100%{background-position:-40% 0}}

/* ── метрики: тянутся на всю ширину, иначе справа зияет пустая ячейка ── */
.strip div{flex:1 1 auto;min-width:122px}
.strip div:last-child{border-right:none}
html{scroll-behavior:smooth}

/* цифра набегает, ячейка чуть тёплая */
.strip div{position:relative;transition:background .2s}
.strip div:hover{background:#fbf7ea}
.strip b{font-variant-numeric:tabular-nums}

/* ── мигающая точка записи в шапке ── */
.rec{width:6px;height:6px;border-radius:50%;background:var(--red);display:inline-block;
  animation:blink 1.9s steps(1,end) infinite}
@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:.25}}

@media(prefers-reduced-motion:reduce){
  .film .strip2,.hero .mark,.wall:after,.rec{animation:none}
  .rv{opacity:1;transform:none}
}

/* ── телефон: под токен половина трафика оттуда, страница не должна ехать вбок ── */
html,body{overflow-x:hidden}
@media(max-width:760px){
  /* отрицательные поля шапки и ленты должны совпадать с padding обёртки, иначе они
     ровно на эту разницу шире экрана и тащат всю страницу вбок */
  .bar,.film{margin-left:-14px;margin-right:-14px}
  .bar{gap:8px;padding:8px 14px;flex-wrap:nowrap}
  .bar .cs{display:none}                    /* длинная подпись рвала шапку в столбик */
  .bar .sp{gap:12px;font-size:9.5px;white-space:nowrap;overflow:hidden}
  .bar .sp a:nth-child(2),.bar .sp a:nth-child(3){display:none}   /* RULES/FIGHTS есть ниже по странице */
  .film{top:40px}
  .wrap{padding:16px 14px 48px}
  /* широкие таблицы прокручиваются внутри себя, а не тащат за собой всю страницу */
  table{display:block;overflow-x:auto;white-space:nowrap}
  .strip div{min-width:44%}
  .hero h1{font-size:30px}
  .wall{border-width:4px;padding:10px}
}
"""

ANIM_JS = """
// дорожка в герое: не декор, а тот же курсор воспроизведения, что идёт в роликах
(function(){
  var c=document.getElementById('wv'); if(!c) return;
  var g=c.getContext('2d'), dpr=Math.min(2,window.devicePixelRatio||1), W=0,H=64;
  function size(){ W=c.clientWidth; c.width=W*dpr; c.height=H*dpr; g.setTransform(dpr,0,0,dpr,0,0); }
  size(); addEventListener('resize',size);
  var seed=function(i){ var v=Math.sin(i*12.9898)*43758.5453; return v-Math.floor(v); };
  var t=0, slow=matchMedia('(prefers-reduced-motion:reduce)').matches;
  function frame(){
    t+=slow?0:1;
    g.clearRect(0,0,W,H);
    var bw=3, gap=3, n=Math.floor(W/(bw+gap)), cur=(t*0.0016)%1;
    for(var i=0;i<n;i++){
      var u=i/n;
      // огибающая речи: пачки высказываний с паузами, как на настоящей плёнке
      var env=Math.max(0,Math.sin(u*26)*0.5+0.5)*Math.max(0,Math.sin(u*7.3+1.1)*0.6+0.55);
      var a=env*(0.35+seed(i+((t*0.02)|0))*0.65);
      var h=Math.max(1,a*(H-10));
      var past=u<cur;
      g.fillStyle = past ? (u>cur-0.02 ? '#c8913a' : 'rgba(43,48,42,.62)') : 'rgba(43,48,42,.16)';
      g.fillRect(i*(bw+gap), (H-h)/2, bw, h);
    }
    g.fillStyle='rgba(192,74,60,.75)';
    g.fillRect(cur*W, 4, 1, H-8);
    requestAnimationFrame(frame);
  }
  frame();
})();

// секции проявляются один раз, без дёрганья при обратной прокрутке
(function(){
  var els=document.querySelectorAll('.rv');
  if(!('IntersectionObserver' in window)){ els.forEach(function(e){e.classList.add('on');}); return; }
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add('on'); io.unobserve(en.target); } });
  },{rootMargin:'0px 0px -8% 0px',threshold:.08});
  els.forEach(function(e){ io.observe(e); });
})();

// цифры метрик набегают, когда полоса появляется в кадре
(function(){
  var strip=document.querySelector('.strip'); if(!strip) return;
  var done=false;
  function run(){
    if(done) return; done=true;
    strip.querySelectorAll('b').forEach(function(b){
      var raw=b.textContent.trim(), m=raw.replace(/,/g,'').match(/^(\\d+(?:\\.\\d+)?)(.*)$/);
      if(!m) return;
      var end=parseFloat(m[1]), tail=m[2]||'', dec=(m[1].split('.')[1]||'').length;
      var grp=raw.indexOf(',')>=0, t0=performance.now(), dur=900;
      function step(now){
        var k=Math.min(1,(now-t0)/dur), e=1-Math.pow(1-k,3), v=end*e;
        var txt=dec?v.toFixed(dec):Math.round(v).toString();
        if(grp) txt=txt.replace(/\\B(?=(\\d{3})+(?!\\d))/g,',');
        b.textContent=txt+tail;
        if(k<1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }
  if(matchMedia('(prefers-reduced-motion:reduce)').matches) return;
  new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting) run(); }); },
    {threshold:.3}).observe(strip);
})();

// позиция плёнки в ленте: тикает, как счётчик магнитофона
(function(){
  var el=document.getElementById('tapepos'); if(!el) return;
  var n=0;
  setInterval(function(){ n=(n+37)%99999; el.textContent='TAPE POSITION '+String(n).padStart(5,'0'); },140);
})();
"""

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE LAST SPEAKER · {e(name)} · case report</title>
<link rel="icon" href="logo.svg">
<meta property="og:title" content="THE LAST SPEAKER · COLD.DESK">
<meta property="og:description" content="six agents, {s['tape_hours']} hours of a language with no alphabet, {s['words_saved']:,} words and {s['rules_signed']} rules - every one of them opens the second of tape it came from">
<meta property="og:image" content="https://jugqdc-sudo.github.io/cold-desk/desk.gif">
<meta name="twitter:card" content="summary_large_image">
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

/* ── шапка: логотип едет с прокруткой, чтобы имя было видно всегда ── */
.bar{{position:sticky;top:0;z-index:20;background:rgba(244,242,236,.94);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);margin:0 -18px 0;padding:9px 18px;display:flex;align-items:center;gap:12px}}
.bar img{{width:26px;height:26px;display:block}}
.bar .nm{{font-weight:700;letter-spacing:2.5px;font-size:12px}}
.bar .cs{{color:var(--dim);letter-spacing:2px;font-size:10px}}
.bar .sp{{margin-left:auto;display:flex;gap:14px;font-size:10.5px;letter-spacing:1.6px}}
.bar .sp a{{color:var(--dim);text-decoration:none;border-bottom:1px solid transparent}}
.bar .sp a:hover{{color:var(--ink);border-bottom-color:var(--line)}}

/* ── герой ── */
.hero{{display:grid;grid-template-columns:196px 1fr;gap:34px;align-items:center;
  padding:44px 0 30px;border-bottom:1px solid var(--line)}}
.hero .mark{{width:196px;height:196px}}
.hero h1{{margin:0 0 10px;font-size:52px}}
.hero .lead{{color:var(--dim);font-size:14px;line-height:1.7;max-width:62ch}}
.hero .lead b{{color:var(--ink);font-weight:700}}
.tags{{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}}
@media(max-width:760px){{.hero{{grid-template-columns:1fr;gap:18px}}.hero .mark{{width:128px;height:128px}}.hero h1{{font-size:34px}}}}

/* ── три шага проверки ── */
.checks{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:14px 0 6px}}
.chk{{background:var(--card);border:1px solid var(--line);padding:14px 16px}}
.chk .no{{font-family:"Instrument Serif",serif;font-size:30px;color:var(--amber);line-height:1}}
.chk h3{{margin:6px 0 5px;font-size:12px;letter-spacing:1.6px;text-transform:uppercase}}
.chk p{{margin:0;color:var(--dim);font-size:11.5px;line-height:1.65}}
@media(max-width:760px){{.checks{{grid-template-columns:1fr}}}}

/* ── контракт токена ── */
.ca{{margin:26px 0 0;background:#16190f;color:#e7eae0;padding:16px 18px;display:flex;
  gap:14px;align-items:center;flex-wrap:wrap}}
.ca .lbl{{letter-spacing:2.5px;font-size:10px;color:#9aa693}}
.ca code{{font-size:13px;letter-spacing:.4px;word-break:break-all;color:#e7eae0}}
{ANIM_CSS}
</style></head><body><div class="wrap">

<div class="bar">
  <img src="logo.svg" alt="">
  <span class="nm">COLD.DESK</span>
  <span class="cs"><span class="rec"></span> CASE 01 · THE LAST SPEAKER</span>
  <span class="sp">
    <a href="#check">HOW TO CHECK</a>
    <a href="#rules">RULES</a>
    <a href="#fights">FIGHTS</a>
    <a href="https://github.com/jugqdc-sudo/cold-desk" target="_blank">CODE</a>
    <a href="https://x.com/ventry089" target="_blank">X</a>
  </span>
</div>

<div class="film">
  <div class="strip2">{'<i></i>' * 90}</div>
  <span class="pos2" id="tapepos">TAPE POSITION 00000</span>
</div>

<div class="hero">
  <img class="mark" src="logo.svg" alt="THE LAST SPEAKER">
  <div>
    <h1>a language with no alphabet, and one man left who speaks it</h1>
    <div class="lead">six agents listened to <b>{s['tape_hours']} hours</b> of raw tape and pulled out
      <b>{s['words_saved']:,} word candidates</b> and <b>{s['rules_signed']} grammar rules</b> - with no dictionary,
      no translation and nobody alive who could tell them they got it wrong.<br><br>
      nothing is written without a source: <b>every single number on this page opens the exact second
      of the recording it came from.</b> the {s['rules_refused']} rules the desk threw out are published too,
      with the reason each one died.</div>
    <div class="tags">
      <span class="pill red">● ONE SPEAKER LEFT</span>
      <span class="pill">NO DICTIONARY · NO TRANSLATION</span>
      <span class="pill mint">EVERY LINE HAS A TAPE POSITION</span>
      <span class="pill">OPEN SOURCE · MIT</span>
    </div>
  </div>
</div>

<div class="wavewrap">
  <canvas id="wv"></canvas>
  <span class="cap">{s['speech_hours']} H OF SPEECH · {s['utterances']:,} UTTERANCES</span>
</div>

<h2 id="check">how to check this yourself · takes about a minute</h2>
<div class="checks rv">
  <div class="chk"><div class="no">1</div><h3>click any timestamp</h3>
    <p>every green position on this page is a link. it opens the recording at that exact second,
       so you hear the word instead of reading a claim about it.</p></div>
  <div class="chk"><div class="no">2</div><h3>read what got refused</h3>
    <p>the desk wrote {s['rules_signed'] + s['rules_refused']} rules and signed {s['rules_signed']}.
       the other {s['rules_refused']} are listed below with the reason each one failed the gate.</p></div>
  <div class="chk"><div class="no">3</div><h3>run it on your own tape</h3>
    <p>the code is open. <code>desk.py run tape.wav</code>, about a minute of cpu per hour of audio.
       same pipeline, your recording.</p></div>
</div>

<div class="sub" style="margin-top:22px">tape: <a href="{e(meta['url'])}" target="_blank">{e(meta['title'])}</a> · Wikitongues, CC BY · every timestamp below opens that second of the recording</div>
<div class="strip">
<div>WORDS SAVED<b>{s['words_saved']:,}</b></div><div>HEARD ONLY ONCE<b>{s['heard_only_once']:,}</b></div>
<div>RULES SIGNED<b class="mint">{s['rules_signed']}</b></div><div>RULES REFUSED<b class="red">{s['rules_refused']}</b></div>
<div>FIGHTS OPEN<b class="red">{s['fights_open']}</b></div><div>NOT HIS USUAL VOICE<b>{s['register_shifts']}</b></div>
<div>SOUNDS · CORE<b>{s['inventory']} · {s['core_inventory']}</b></div><div>SPEECH ON TAPE<b>{s['speech_hours']} h</b></div><div>SPEAKERS LEFT<b class="red">1</b></div>
{f'<div>NEVER RECORDED<b class="red">{s["derived_never_recorded"]:,}</b></div>' if s.get("derived_never_recorded") else ''}
{f'<div>DIE WITH HIM<b class="red">{s["die_with_him"]:,}</b></div>' if s.get("die_with_him") else ''}
</div>
<h2 class="rv">the wall · chains that keep coming back</h2>
<div class="wall rv">{cards}</div>
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
{ca_block}
<div class="foot">other tapes: <a href="index.html">torwali</a> · <a href="piedmontese.html">piedmontese</a>
 · <a href="https://github.com/jugqdc-sudo/cold-desk" target="_blank">code</a>
 · <a href="https://x.com/ventry089" target="_blank">the serial</a>
 · desk.py run tape.wav · generated from runs/{e(name)}/run.json</div>
</div>
<script>{ANIM_JS}</script>
</body></html>"""
out = root / "docs"; out.mkdir(exist_ok=True)
(out / f"{page_name}.html").write_text(page, encoding="utf-8")
print(f"docs/{page_name}.html", len(page), "bytes ·", len(words), "cards ·", len(rules), "rules ·", len(shifts), "shifts")
