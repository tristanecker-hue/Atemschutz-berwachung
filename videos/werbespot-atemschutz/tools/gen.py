#!/usr/bin/env python3
"""Generates the scene sub-compositions for the ATEMSCHUTZ promo spot.

Run from the project root:  python3 tools/gen.py
Every scene is written to compositions/<id>.html. Numbers shown in the app UI
follow the app's real formulas (index.html v2.28):
  Start 14:12:07 @ 300 bar, reading 14:22:07 @ 230 bar  -> Verbrauch 7.0 bar/min
  Einsatzziel erreicht nach 9.6 min -> Rueckzug ab 9.6 * 7.0 * 1.1 = 74 bar
  Umkehrdruck (Alarm) 50 bar, Druckabfrage alle 10 min.
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "compositions")

# ---------------------------------------------------------------- palette
C = dict(
    bg="#12151A", card="#1A1D21", line="#262B32", line2="#3A424B",
    fg="#E4E7EB", muted="#9AA1A9", red="#D9483D", orange="#E8912D",
    green="#3E8E41", blue="#3D7BFF", night="#07090C",
)

COMMON_CSS = """
#%ID% { position:absolute; inset:0; overflow:hidden; background:%NIGHT%; color:%FG%;
  font-family:Inter, sans-serif; }
#%ID% .full { position:absolute; inset:0; }
#%ID% .mono { font-family:'IBM Plex Mono', monospace; }
#%ID% .osw { font-family:Oswald, sans-serif; }
#%ID% .slate { position:absolute; left:64px; bottom:56px; font-family:'IBM Plex Mono', monospace;
  font-size:20px; letter-spacing:0.08em; color:#C7CDD3; display:flex; gap:16px; align-items:center; z-index:50; }
#%ID% .slate b { color:%NIGHT%; background:%FG%; padding:4px 10px; font-weight:600; }
#%ID% .lb { position:absolute; left:0; right:0; height:120px; background:#000; z-index:40; }
#%ID% .lb.t { top:0; } #%ID% .lb.b { bottom:0; }
#%ID% .drop { position:absolute; width:2px; border-radius:2px;
  background:linear-gradient(180deg, rgba(180,200,255,0), rgba(190,210,255,0.55)); }
#%ID% .spark { position:absolute; width:6px; height:6px; border-radius:50%;
  background:#FFB765; box-shadow:0 0 12px 4px rgba(255,140,40,0.7); }
#%ID% .smoke { position:absolute; border-radius:50%;
  background:radial-gradient(circle, rgba(120,128,140,0.55) 0%, rgba(70,76,86,0.25) 45%, rgba(0,0,0,0) 70%); }
#%ID% .blue { position:absolute; border-radius:50%;
  background:radial-gradient(circle, rgba(61,123,255,0.85) 0%, rgba(40,80,220,0.35) 35%, rgba(0,0,0,0) 70%); }
#%ID% .shot { position:absolute; inset:0; opacity:0; }
#%ID% .flash { position:absolute; inset:0; background:#DCE6FF; opacity:0; z-index:45; }
#%ID% .ico { filter: drop-shadow(0 0 18px rgba(61,123,255,0.65)); }
#%ID% .big { font-family:Oswald, sans-serif; font-weight:700; text-transform:uppercase;
  letter-spacing:0.01em; line-height:0.95; }
#%ID% .card { background:%CARD%; border:3px solid %LINE%; border-radius:28px; }
#%ID% .chip { display:inline-flex; align-items:center; padding:14px 26px; border-radius:999px;
  border:3px solid %LINE2%; font-size:26px; font-weight:600; color:%FG%; background:%BG%; }
#%ID% .btnp { display:flex; align-items:center; justify-content:center; border-radius:20px;
  background:%RED%; color:#fff; font-weight:700; font-size:30px; letter-spacing:0.02em; }
#%ID% .lbl { font-family:'IBM Plex Mono', monospace; font-size:20px; letter-spacing:0.14em;
  text-transform:uppercase; color:%MUTED%; }
#%ID% .ch { display:inline-block; }
#%ID% .vid { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
#%ID% .ripple { position:absolute; width:120px; height:120px; margin:-60px 0 0 -60px; border-radius:50%;
  border:4px solid rgba(255,255,255,0.9); opacity:0; }
"""

JS_HELPERS = r"""
function rng(seed){return function(){seed|=0;seed=seed+0x6D2B79F5|0;var t=Math.imul(seed^seed>>>15,1|seed);
  t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function pad(n){return String(Math.floor(n)).padStart(2,"0");}
function mmss(s){s=Math.max(0,s);return pad(s/60)+":"+pad(s%60);}
function clock(s){s=Math.floor(s);return pad(s/3600%24)+":"+pad(s/60%60)+":"+pad(s%60);}
function count(tl,el,from,to,at,dur,fmt,ease){var o={v:from};if(!el)return;el.textContent=fmt(from);
  tl.to(o,{v:to,duration:dur,ease:ease||"none",onUpdate:function(){el.textContent=fmt(o.v);}},at);}
function type(tl,el,text,at,dur){var o={v:0};if(!el)return;el.textContent="";
  tl.to(o,{v:text.length,duration:dur,ease:"none",onUpdate:function(){el.textContent=text.slice(0,Math.round(o.v));}},at);}
function rainLoop(tl,sel,total){document.querySelectorAll(sel).forEach(function(d,i){
  var cyc=0.45+(i%7)*0.05;var n=Math.max(0,Math.floor(total/cyc)-1);
  tl.fromTo(d,{y:-260},{y:1340,duration:cyc,ease:"none",repeat:n},(i%11)*0.04);});}
function sparkLoop(tl,sel,total,seed){var r=rng(seed);document.querySelectorAll(sel).forEach(function(d){
  var cyc=1.6+r()*1.6;var n=Math.max(0,Math.floor(total/cyc)-1);
  tl.fromTo(d,{y:0,x:0,opacity:0},{keyframes:[{opacity:1,duration:cyc*0.15},{opacity:0,duration:cyc*0.85}],
   y:-(380+r()*420),x:(r()-0.5)*260,duration:cyc,ease:"none",repeat:n},r()*1.2);});}
function smokeDrift(tl,sel,total,seed){var r=rng(seed);document.querySelectorAll(sel).forEach(function(d){
  tl.fromTo(d,{x:0,y:0,scale:0.9},{x:(r()-0.3)*260,y:-(160+r()*260),scale:1.35+r()*0.4,duration:total,ease:"none"},0);});}
function gauge(tl,id,from,to,at,dur,ease){var o={v:from};var L=GL;
  var arc=document.getElementById(id+"-arc"),nd=document.getElementById(id+"-needle"),tx=document.getElementById(id+"-val");
  function draw(v){var p=Math.max(0,Math.min(1,v/300));if(arc)arc.style.strokeDashoffset=String(L*(1-p));
    if(nd)nd.setAttribute("transform","rotate("+(-135+270*p)+" 150 150)");if(tx)tx.textContent=String(Math.round(v));
    if(arc)arc.style.stroke=v<=50?"#D9483D":(v<=74?"#E8912D":"#3E8E41");}
  draw(from);tl.to(o,{v:to,duration:dur,ease:ease||"none",onUpdate:function(){draw(o.v);}},at);}
"""

# --------------------------------------------------------------- helpers

def arc_path(cx, cy, r, a0, a1):
    def pol(a):
        t = math.radians(a - 90)
        return cx + r * math.cos(t), cy + r * math.sin(t)
    x0, y0 = pol(a0)
    x1, y1 = pol(a1)
    large = 1 if (a1 - a0) > 180 else 0
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"

GAUGE_R = 118
GAUGE_L = round(GAUGE_R * math.radians(270), 2)


def gauge_svg(gid, size=300, value=300, marker=74):
    """App-style pressure gauge (270 deg sweep), driven by JS gauge()."""
    track = arc_path(150, 150, GAUGE_R, -135, 135)
    ticks = []
    for i in range(0, 31):
        a = -135 + 270 * i / 30
        t = math.radians(a - 90)
        r1, r2 = (100, 88) if i % 5 == 0 else (100, 94)
        ticks.append(
            f'<line x1="{150 + r1 * math.cos(t):.1f}" y1="{150 + r1 * math.sin(t):.1f}" '
            f'x2="{150 + r2 * math.cos(t):.1f}" y2="{150 + r2 * math.sin(t):.1f}" '
            f'stroke="#5A636E" stroke-width="{3 if i % 5 == 0 else 2}"/>')
    ma = -135 + 270 * marker / 300
    mt = math.radians(ma - 90)
    mk = (f'<line x1="{150 + 108 * math.cos(mt):.1f}" y1="{150 + 108 * math.sin(mt):.1f}" '
          f'x2="{150 + 132 * math.cos(mt):.1f}" y2="{150 + 132 * math.sin(mt):.1f}" stroke="{C["orange"]}" stroke-width="6" stroke-linecap="round"/>')
    a5 = -135 + 270 * 50 / 300
    t5 = math.radians(a5 - 90)
    mk += (f'<line x1="{150 + 108 * math.cos(t5):.1f}" y1="{150 + 108 * math.sin(t5):.1f}" '
           f'x2="{150 + 132 * math.cos(t5):.1f}" y2="{150 + 132 * math.sin(t5):.1f}" stroke="{C["red"]}" stroke-width="6" stroke-linecap="round"/>')
    return f'''<svg viewBox="0 0 300 300" width="{size}" height="{size}" style="display:block">
  <path d="{track}" fill="none" stroke="{C['line']}" stroke-width="18" stroke-linecap="round"/>
  <path id="{gid}-arc" d="{track}" fill="none" stroke="{C['green']}" stroke-width="18" stroke-linecap="round"
    style="stroke-dasharray:{GAUGE_L};stroke-dashoffset:0"/>
  {''.join(ticks)}{mk}
  <line id="{gid}-needle" x1="150" y1="150" x2="150" y2="62" stroke="{C['fg']}" stroke-width="6" stroke-linecap="round"
    transform="rotate(135 150 150)"/>
  <circle cx="150" cy="150" r="12" fill="{C['fg']}"/>
</svg>'''


def rain(n, seed, opacity=1.0):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        x = r.uniform(0, 1920)
        h = r.uniform(60, 160)
        o = r.uniform(0.25, 0.9) * opacity
        out.append(f'<div class="drop" style="left:{x:.0f}px;top:0;height:{h:.0f}px;opacity:{o:.2f}"></div>')
    return "".join(out)


def sparks(n, seed, x0=500, x1=1400, y=820):
    r = random.Random(seed)
    return "".join(
        f'<div class="spark" style="left:{r.uniform(x0, x1):.0f}px;top:{y + r.uniform(-60, 60):.0f}px;'
        f'transform:scale({r.uniform(0.5, 1.2):.2f})"></div>' for _ in range(n))


def smoke(n, seed, x0=300, x1=1600, y0=200, y1=700, s0=380, s1=760):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        s = r.uniform(s0, s1)
        out.append(f'<div class="smoke" style="left:{r.uniform(x0, x1) - s / 2:.0f}px;top:{r.uniform(y0, y1) - s / 2:.0f}px;'
                   f'width:{s:.0f}px;height:{s:.0f}px"></div>')
    return "".join(out)


def slate(code, text):
    return f'<div class="slate"><b>PLATZHALTER {code}</b><span>{text}</span></div>'


# --------------------------------------------------------------- icons (line art)
STK = f'fill="none" stroke="{C["fg"]}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"'

ICONS = {
    "helmet": f'''<svg viewBox="0 0 400 300" width="720" height="540"><g {STK}>
<path d="M60 220 Q60 70 200 60 Q340 70 340 220"/><path d="M20 222 L380 222 Q372 250 330 252 L70 252 Q28 250 20 222Z"/>
<path d="M200 60 L200 220"/><path d="M130 82 Q118 150 120 220"/><path d="M270 82 Q282 150 280 220"/>
<path d="M110 252 Q200 300 290 252" stroke="{C['red']}"/></g></svg>''',
    "mask": f'''<svg viewBox="0 0 400 400" width="620" height="620"><g {STK}>
<path d="M200 30 Q330 40 345 170 Q350 290 260 360 L140 360 Q50 290 55 170 Q70 40 200 30Z"/>
<ellipse cx="200" cy="165" rx="112" ry="92"/><circle cx="200" cy="300" r="42"/><circle cx="200" cy="300" r="16"/>
<path d="M55 150 L10 120 M345 150 L390 120"/></g>
<ellipse id="%ID%-fog" cx="200" cy="165" rx="104" ry="84" fill="rgba(220,230,255,0.55)" opacity="0"/></svg>''',
    "radio": f'''<svg viewBox="0 0 300 460" width="400" height="610"><g {STK}>
<rect x="60" y="120" width="180" height="320" rx="26"/><path d="M90 120 L90 20"/><rect x="80" y="150" width="140" height="70" rx="8"/>
<path d="M100 260 h100 M100 290 h100 M100 320 h100 M100 350 h100"/><path d="M240 230 h22 v70 h-22" stroke="{C['red']}"/></g>
<circle id="%ID%-led" cx="200" cy="395" r="12" fill="{C['red']}" opacity="0.2"/></svg>''',
    "truck": f'''<svg viewBox="0 0 900 360" width="1500" height="600"><g {STK}>
<path d="M40 280 L40 110 L560 110 L560 280"/><path d="M560 280 L560 140 L700 140 L790 210 L860 220 L860 280 Z"/>
<path d="M600 160 L690 160 L750 210 L600 210 Z"/><circle cx="170" cy="290" r="44"/><circle cx="440" cy="290" r="44"/>
<circle cx="740" cy="290" r="44"/><path d="M70 140 h460 M70 190 h460" stroke-width="4"/>
<path d="M30 280 h80 M214 280 h182 M484 280 h212 M784 280 h90"/></g>
<rect id="%ID%-bar" x="600" y="118" width="120" height="18" rx="6" fill="{C['blue']}"/>
<text x="300" y="250" fill="{C['red']}" font-family="Oswald" font-size="40" font-weight="700" text-anchor="middle">FEUERWEHR</text></svg>''',
    "house": f'''<svg viewBox="0 0 900 600" width="1350" height="900"><g {STK}>
<path d="M120 560 L120 260 L450 70 L780 260 L780 560 Z"/><path d="M60 560 h780"/><path d="M400 560 v-140 h100 v140"/></g>
<g fill="#FF8A2B" opacity="0.9"><rect x="190" y="310" width="110" height="90" rx="6"/><rect x="600" y="310" width="110" height="90" rx="6"/>
<rect x="395" y="200" width="110" height="80" rx="6" fill="#FFB25A"/></g>
<g {STK}><rect x="190" y="310" width="110" height="90" rx="6"/><rect x="600" y="310" width="110" height="90" rx="6"/>
<rect x="395" y="200" width="110" height="80" rx="6"/></g></svg>''',
    "calc": f'''<svg viewBox="0 0 200 280" width="220" height="308"><g {STK}><rect x="20" y="20" width="160" height="240" rx="18"/>
<rect x="44" y="44" width="112" height="50" rx="6"/><path d="M50 130h20M90 130h20M130 130h20M50 170h20M90 170h20M130 170h20M50 210h20M90 210h20M130 210h20"/></g></svg>''',
    "board": f'''<svg viewBox="0 0 300 400" width="330" height="440"><g {STK}><rect x="30" y="40" width="240" height="340" rx="14"/>
<rect x="105" y="20" width="90" height="40" rx="10"/><path d="M60 110h180M60 160h150M60 210h170M60 260h120M60 310h160" stroke-width="4"/></g></svg>''',
    "watch": f'''<svg viewBox="0 0 200 260" width="190" height="247"><g {STK}><rect x="60" y="10" width="80" height="50" rx="10"/>
<rect x="60" y="200" width="80" height="50" rx="10"/><circle cx="100" cy="130" r="74"/><path d="M100 130 L100 82 M100 130 L136 150"/></g></svg>''',
}


def icon(name, sid):
    return ICONS[name].replace("%ID%", sid)


def person(x, scale=1.0, fill="#05070A"):
    """Firefighter silhouette with SCBA (flat, for backlit shots)."""
    return f'''<svg viewBox="0 0 200 520" width="{200 * scale:.0f}" height="{520 * scale:.0f}" style="position:absolute;left:{x}px;bottom:0">
<g fill="{fill}"><ellipse cx="100" cy="60" rx="46" ry="40"/><rect x="40" y="60" width="120" height="14" rx="6"/>
<path d="M50 100 Q100 86 150 100 L166 290 L34 290 Z"/><rect x="138" y="110" width="38" height="150" rx="16"/>
<path d="M44 286 L90 286 L84 510 L46 510 Z"/><path d="M110 286 L156 286 L154 510 L116 510 Z"/>
<path d="M50 110 L20 250 L40 256 L66 140Z"/><path d="M150 110 L180 250 L160 256 L134 140Z"/></g></svg>'''


# --------------------------------------------------------------- app UI parts
ICON_PEOPLE = f'<svg viewBox="0 0 24 24" width="40" height="40"><g fill="none" stroke="{C["muted"]}" stroke-width="2"><circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-4 3-6 7-6s7 2 7 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14c3 0 6 1.5 6 5"/></g></svg>'
ICON_CLOCK = f'<svg viewBox="0 0 24 24" width="40" height="40"><g fill="none" stroke="{C["muted"]}" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></g></svg>'
ICON_PIN = f'<svg viewBox="0 0 24 24" width="40" height="40"><g fill="none" stroke="{C["muted"]}" stroke-width="2"><path d="M12 21s7-6.5 7-12a7 7 0 0 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/></g></svg>'
ICON_RADIO = f'<svg viewBox="0 0 24 24" width="40" height="40"><g fill="none" stroke="{C["muted"]}" stroke-width="2"><rect x="6" y="7" width="12" height="15" rx="2"/><path d="M9 7V2M9 12h6M9 16h6"/></g></svg>'

APP_CSS = """
#%ID% .acard { position:absolute; width:1180px; padding:40px 44px; background:%CARD%; border:3px solid %LINE%;
  border-radius:32px; box-shadow:0 40px 120px rgba(0,0,0,0.6); }
#%ID% .acard.warn { border-color:%ORANGE%; }
#%ID% .ahead { display:flex; justify-content:space-between; align-items:center; margin-bottom:22px; }
#%ID% .aname { font-family:Oswald, sans-serif; font-size:52px; font-weight:700; }
#%ID% .astatus { font-family:'IBM Plex Mono', monospace; font-size:24px; font-weight:600; padding:10px 22px;
  border-radius:999px; color:#fff; background:%GREEN%; }
#%ID% .agrid { display:flex; gap:44px; }
#%ID% .agauge { position:relative; width:380px; display:flex; flex-direction:column; align-items:center; }
#%ID% .agval { position:absolute; top:104px; left:0; right:0; text-align:center; font-family:Oswald, sans-serif;
  font-size:104px; font-weight:700; line-height:1; }
#%ID% .agunit { position:absolute; top:250px; left:0; right:0; text-align:center; font-size:24px; color:%MUTED%; }
#%ID% .athr { font-family:'IBM Plex Mono', monospace; font-size:21px; color:%MUTED%; text-align:center; margin-top:8px; }
#%ID% .aside { flex:1; display:flex; flex-direction:column; gap:20px; }
#%ID% .anext { background:%BG%; border:3px solid %LINE%; border-radius:22px; padding:22px 26px; }
#%ID% .anext .t { font-family:'IBM Plex Mono', monospace; font-size:64px; font-weight:600; line-height:1.05; }
#%ID% .ainp { display:flex; gap:14px; margin-top:14px; }
#%ID% .ainp .f { flex:1; border:3px solid %LINE2%; border-radius:16px; padding:14px 18px; font-size:28px; color:%MUTED%; }
#%ID% .ainp .f.on { color:%FG%; border-color:%FG%; }
#%ID% .ainp .b { border-radius:16px; padding:14px 22px; font-weight:700; font-size:26px; background:%RED%; color:#fff;
  font-family:'IBM Plex Mono', monospace; letter-spacing:0.06em; }
#%ID% .arow { display:flex; gap:18px; align-items:flex-start; }
#%ID% .arow .m { font-size:30px; font-weight:600; }
#%ID% .arow .s { font-size:23px; color:%MUTED%; margin-top:2px; }
#%ID% .aacts { display:flex; gap:16px; margin-top:26px; }
"""


def app_card(gid, name="Müller", status="Im Einsatz", nextq="07:12", val=210, einsatz="12:48",
             thr="Verbrauch 7.0 bar/min · Rückzug ab 74 bar · Alarm ab 50 bar", acts=True, style=""):
    a = ""
    if acts:
        a = ('<div class="aacts"><span class="chip" id="%s-c1">Rückzug gemeldet</span>'
             '<span class="chip" style="border-color:#D9483D;color:#F08A80">Einsatz Ende</span>'
             '<span class="chip">✎ Bearbeiten</span></div>') % gid
    return f'''<div class="acard" id="{gid}" style="{style}">
 <div class="ahead"><div class="aname">Trupp {name}</div><div class="astatus" id="{gid}-st">{status}</div></div>
 <div class="agrid">
  <div class="agauge">{gauge_svg(gid)}<div class="agval" id="{gid}-val">{val}</div><div class="agunit">bar · vor 0:12</div>
   <div class="athr">{thr}</div></div>
  <div class="aside">
   <div class="anext"><div class="lbl">Nächste Abfrage</div><div class="t" id="{gid}-nq">{nextq}</div>
    <div class="ainp"><div class="f" id="{gid}-in">Druck (bar)</div><div class="b" id="{gid}-er">ERFASSEN</div></div></div>
   <div class="arow">{ICON_PEOPLE}<div><div class="m">Müller</div><div class="s">Keller, Brunner · Überwacher: Weber</div></div></div>
   <div class="arow">{ICON_CLOCK}<div><div class="m" id="{gid}-ez">{einsatz}</div><div class="s">Einsatzzeit</div></div></div>
   <div class="arow">{ICON_PIN}<div><div class="m">Hauptstrasse 12, Zuchwil</div><div class="s">Brandbekämpfung 1. OG</div></div></div>
   <div class="arow">{ICON_RADIO}<div><div class="m">Kanal 3</div><div class="s">Seil: rot</div></div></div>
  </div>
 </div>{a}
</div>'''


# --------------------------------------------------------------- file writer

def write_scene(sid, dur, html, css, js):
    style = (COMMON_CSS + APP_CSS + css)
    for k, v in dict(ID=sid, NIGHT=C["night"], FG=C["fg"], CARD=C["card"], LINE=C["line"], LINE2=C["line2"],
                     BG=C["bg"], RED=C["red"], MUTED=C["muted"], ORANGE=C["orange"], GREEN=C["green"]).items():
        style = style.replace("%" + k + "%", v)
    html = html.replace("%ID%", sid)
    js = js.replace("%ID%", sid)
    doc = f'''<!doctype html>
<html lang="de">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>{style}</style>
      <div id="{sid}" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur}">
{html}
      </div>
      <script>
(function(){{
var GL={GAUGE_L};
{JS_HELPERS}
var tl = gsap.timeline({{ paused: true }});
var Q = function(s){{ return "#{sid} " + s; }};
{js}
window.__timelines["{sid}"] = tl;
}})();
      </script>
    </template>
  </body>
</html>
'''
    with open(os.path.join(OUT, sid + ".html"), "w", encoding="utf-8") as f:
        f.write(doc)


SCENES = []


def scene(fn):
    SCENES.append(fn)
    return fn


# ================================================================ S01 COLD OPEN (8s)
@scene
def s01():
    sid, dur = "s01-cold-open", 8
    html = f'''
<div class="full" id="%ID%-radio" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px">
  <svg viewBox="0 0 1200 200" width="1200" height="200"><polyline id="%ID%-wave" fill="none" stroke="{C['fg']}" stroke-width="4"
   points="{' '.join(f'{x},{100 + (math.sin(x * 0.11) * math.sin(x * 0.013) * 60 if 260 < x < 940 else 0):.0f}' for x in range(0, 1201, 6))}"/></svg>
  <div class="mono" id="%ID%-sub" style="font-size:34px;letter-spacing:0.06em;color:#C7CDD3">FUNK · «Einsatz für Atemschutztrupp.»</div>
</div>
<div class="shot" id="%ID%-sh1">
  <div class="blue" id="%ID%-b1" style="left:260px;top:-200px;width:1400px;height:1400px"></div>
  {rain(70, 11)}
  <div class="full" style="display:flex;align-items:center;justify-content:center">
   <div id="%ID%-beam" style="width:1700px;height:1700px;border-radius:50%;
    background:conic-gradient(from 0deg, rgba(61,123,255,0) 0deg, rgba(120,170,255,0.75) 18deg, rgba(61,123,255,0) 40deg,
     rgba(61,123,255,0) 180deg, rgba(120,170,255,0.75) 198deg, rgba(61,123,255,0) 220deg)"></div></div>
  {slate("S1.2", "Blaulicht schaltet ein · Makro Rundumleuchte, Regen")}
</div>
<div class="shot" id="%ID%-sh2"><div class="blue" style="left:-300px;top:-300px;width:1300px;height:1300px;opacity:.5"></div>
  <div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico" id="%ID%-i2">{icon('helmet', sid)}</div></div>
  {slate("S1.3", "Helm wird aufgesetzt · Kinnriemen klickt")}</div>
<div class="shot" id="%ID%-sh3"><div class="blue" style="right:-300px;top:-200px;width:1300px;height:1300px;opacity:.5"></div>
  <div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico" id="%ID%-i3">{icon('mask', sid)}</div></div>
  {slate("S1.4", "Atemschutzmaske · Atemzug beschlägt das Sichtfenster")}</div>
<div class="shot" id="%ID%-sh4"><div class="blue" style="left:500px;top:-500px;width:1100px;height:1100px;opacity:.45"></div>
  <div class="full" style="display:flex;align-items:center;justify-content:center;gap:80px">
   <div style="position:relative;width:560px;height:560px">{gauge_svg('%ID%-g', 560, 300, 74).replace('%ID%', sid)}</div>
   <div><div class="big" id="%ID%-g-val" style="font-size:260px">0</div><div class="lbl" style="font-size:34px;color:{C['fg']}">bar · Flasche angeschlossen</div></div>
  </div>
  {slate("S1.5", "Lungenautomat rastet ein · Manometer springt auf 300 bar")}</div>
<div class="shot" id="%ID%-sh5"><div class="blue" style="left:600px;top:-200px;width:1300px;height:1300px;opacity:.45"></div>
  <div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico" id="%ID%-i5">{icon('radio', sid)}</div></div>
  {slate("S1.6", "Hand greift Funkgerät · Daumen drückt PTT")}</div>
<div class="shot" id="%ID%-sh6">
  <div class="blue" id="%ID%-tb" style="left:700px;top:60px;width:1100px;height:900px"></div>
  <div id="%ID%-road" class="full">{''.join(f'<div class="rl" style="left:{x}px"></div>' for x in range(-200, 2400, 260))}</div>
  <div class="full" style="display:flex;align-items:center;justify-content:center;padding-top:40px"><div class="ico" id="%ID%-truck">{icon('truck', sid)}</div></div>
  <div style="position:absolute;left:0;right:0;top:830px;height:130px;background:linear-gradient(180deg,rgba(61,123,255,0.28),rgba(0,0,0,0))"></div>
  {rain(50, 12, 0.8)}
  {slate("S1.7", "TLF fährt mit Blaulicht · Kamera auf Radhöhe, nasser Asphalt, Speed Ramp")}</div>
<div class="flash" id="%ID%-fl"></div>
<div class="lb t"></div><div class="lb b"></div>'''
    css = """
#%ID% .rl { position:absolute; top:900px; width:150px; height:10px; border-radius:5px; background:#C7CDD3; opacity:.65; }
"""
    js = """
var R=document.getElementById("%ID%-radio");
tl.fromTo("#%ID%-wave",{opacity:0,scaleY:0.2,transformOrigin:"50% 50%"},{opacity:1,scaleY:1,duration:0.25,ease:"power2.out"},0.15);
tl.to("#%ID%-wave",{scaleY:0.35,duration:0.08,yoyo:true,repeat:11,ease:"steps(2)"},0.4);
tl.fromTo("#%ID%-sub",{opacity:0,y:12},{opacity:1,y:0,duration:0.3,ease:"power2.out"},0.35);
tl.to(R,{opacity:0,duration:0.08},1.45);
// shot 1 blue light
var shots=[["#%ID%-sh1",1.5,2.2],["#%ID%-sh2",2.2,2.76],["#%ID%-sh3",2.76,3.32],["#%ID%-sh4",3.32,4.3],["#%ID%-sh5",4.3,5.0],["#%ID%-sh6",5.0,8.0]];
shots.forEach(function(s){tl.set(s[0],{opacity:1},s[1]);tl.set(s[0],{opacity:0},s[2]);
  tl.fromTo("#%ID%-fl",{opacity:0.75},{immediateRender:false,opacity:0,duration:0.12,ease:"power2.out"},s[1]);});
tl.fromTo("#%ID%-beam",{rotation:0,opacity:0},{rotation:300,opacity:1,duration:0.7,ease:"none"},1.5);
tl.fromTo("#%ID%-b1",{scale:0.3,opacity:0},{scale:1.1,opacity:1,duration:0.25,ease:"expo.out"},1.5);
rainLoop(tl,"#%ID%-sh1 .drop",0.8);
tl.fromTo("#%ID%-i2",{scale:1.25,y:-40},{scale:1.05,y:0,duration:0.56,ease:"power3.out"},2.2);
tl.fromTo("#%ID%-i3",{scale:0.92},{scale:1.08,duration:0.56,ease:"none"},2.76);
tl.fromTo("#%ID%-fog",{opacity:0},{keyframes:[{opacity:0.8,duration:0.2},{opacity:0.15,duration:0.3}]},2.86);
gauge(tl,"%ID%-g",0,300,3.42,0.45,"power4.out");
count(tl,document.getElementById("%ID%-g-val"),0,300,3.42,0.45,function(v){return String(Math.round(v));},"power4.out");
tl.fromTo("#%ID%-i5",{scale:1.0,x:60},{scale:1.12,x:0,duration:0.7,ease:"power2.out"},4.3);
tl.fromTo("#%ID%-led",{opacity:0.2},{opacity:1,duration:0.05,repeat:5,yoyo:true},4.55);
// truck run with speed ramp: road lines speed 1 -> 0.4 -> 1.2
var o={p:0};document.querySelectorAll("#%ID%-road .rl").forEach(function(l){});
tl.fromTo("#%ID%-road",{x:0},{x:-1560,duration:1.0,ease:"none"},5.0);
tl.to("#%ID%-road",{x:-1950,duration:1.0,ease:"sine.inOut"},6.0);
tl.to("#%ID%-road",{x:-3900,duration:1.0,ease:"power2.in"},7.0);
tl.fromTo("#%ID%-truck",{x:-140,y:6},{x:40,y:0,duration:3,ease:"sine.inOut"},5.0);
tl.fromTo("#%ID%-tb",{opacity:0.2},{opacity:1,duration:0.18,yoyo:true,repeat:15,ease:"steps(1)"},5.0);
tl.fromTo("#%ID%-bar",{attr:{fill:"#3D7BFF"}},{attr:{fill:"#DCE6FF"},duration:0.18,yoyo:true,repeat:15,ease:"steps(1)"},5.0);
rainLoop(tl,"#%ID%-sh6 .drop",3);
// whip pan out
tl.to("#%ID%-sh6",{x:-1400,filter:"blur(24px)",duration:0.25,ease:"power3.in"},7.75);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S02 IM EINSATZ (7s)
@scene
def s02():
    sid, dur = "s02-einsatz", 7
    html = f'''
<div class="full" id="%ID%-w">
<div class="shot" id="%ID%-a" style="opacity:1">
  <div class="blue" id="%ID%-bl" style="left:-200px;top:200px;width:1200px;height:1200px"></div>
  <div class="blue" id="%ID%-br" style="left:1000px;top:200px;width:1200px;height:1200px;opacity:.3"></div>
  <div class="full" style="display:flex;align-items:flex-end;justify-content:center;padding-bottom:110px"><div id="%ID%-house" class="ico" style="transform-origin:50% 100%">{icon('house', sid)}</div></div>
  <div id="%ID%-sm">{smoke(9, 21, 500, 1450, 60, 420)}</div>
  {sparks(26, 22, 600, 1300, 380)}
  {slate("S2.1", "Drohne · Wohnhaus, Dachstock raucht, Funken, Blaulicht auf Fassade")}
</div>
<div class="shot" id="%ID%-c1"><div class="full" style="display:flex;align-items:center;justify-content:center">
  <div id="%ID%-door" style="width:520px;height:640px;border:8px solid {C['fg']};border-radius:18px;transform-origin:0% 50%;
   background:linear-gradient(160deg,rgba(217,72,61,0.5),rgba(217,72,61,0.1))"></div></div>{slate("S2.2", "Fahrzeugtür fliegt auf")}</div>
<div class="shot" id="%ID%-c2"><div class="full" style="display:flex;align-items:center;justify-content:center">
  {''.join(f'<div class="rip" style="width:{w}px;height:{w // 3}px"></div>' for w in (300, 600, 900))}</div>{slate("S2.3", "Stiefel in Pfütze · Zeitlupe 50 %")}</div>
<div class="shot" id="%ID%-c3"><div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico" id="%ID%-mk">{icon('mask', sid)}</div></div>{slate("S2.4", "Trupp schliesst Masken · Reissverschluss, Ventil")}</div>
<div class="shot" id="%ID%-c4"><svg class="full" viewBox="0 0 1920 1080"><path id="%ID%-rope" d="M-40 900 C 400 700, 700 1000, 1000 760 S 1600 520, 1980 640"
  fill="none" stroke="{C['red']}" stroke-width="22" stroke-linecap="round" style="stroke-dasharray:2600;stroke-dashoffset:2600"/></svg>{slate("S2.5", "Seil wird ausgelegt · Seilfarbe rot")}</div>
<div class="shot" id="%ID%-c5"><div class="full" id="%ID%-hl"><video id="%ID%-v-maske" class="clip vid" data-hf-media-start-basis="local" src="assets/footage/maske.mp4" muted playsinline data-start="3.5" data-duration="0.5" data-track-index="3"></video></div></div>
<div class="shot" id="%ID%-go">
  <div id="%ID%-crew" class="full"><video id="%ID%-v-tuer" class="clip vid" data-hf-media-start-basis="local" src="assets/footage/trupp-tuer.mp4" muted playsinline data-start="4.0" data-duration="3.0" data-track-index="3"></video></div>
  <div id="%ID%-sm2" style="opacity:.5">{smoke(6, 23, 300, 1600, 500, 1000, 500, 900)}</div>
</div>
</div>
<div class="flash" id="%ID%-fl"></div>
<div class="full" id="%ID%-vig" style="background:radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,0.95) 75%);opacity:0;z-index:44"></div>
<div class="lb t"></div><div class="lb b"></div>'''
    css = """
#%ID% .rip { position:absolute; border-radius:50%; border:5px solid rgba(190,210,255,0.8); }
#%ID% .beam { position:absolute; top:230px; width:160px; height:900px; transform-origin:50% 0%;
  background:linear-gradient(180deg, rgba(255,240,210,0.5), rgba(255,240,210,0)); filter:blur(14px); }
"""
    js = """
tl.fromTo("#%ID%-a",{x:1400,filter:"blur(24px)"},{x:0,filter:"blur(0px)",duration:0.3,ease:"power3.out"},0);
tl.fromTo("#%ID%-house",{scale:1.0},{scale:1.08,duration:1.5,ease:"none"},0);
tl.fromTo("#%ID%-bl",{opacity:0.25},{opacity:1,duration:0.2,yoyo:true,repeat:7,ease:"steps(1)"},0);
tl.fromTo("#%ID%-br",{opacity:1},{opacity:0.2,duration:0.2,yoyo:true,repeat:7,ease:"steps(1)"},0);
smokeDrift(tl,"#%ID%-sm .smoke",1.6,5);
sparkLoop(tl,"#%ID%-a .spark",1.5,7);
var cuts=[["#%ID%-a",0,1.5],["#%ID%-c1",1.5,2.0],["#%ID%-c2",2.0,2.5],["#%ID%-c3",2.5,3.0],["#%ID%-c4",3.0,3.5],["#%ID%-c5",3.5,4.0],["#%ID%-go",4.0,7.0]];
cuts.forEach(function(c,i){if(i>0)tl.set(c[0],{opacity:1},c[1]);tl.set(c[0],{opacity:0},c[2]);
 if(i>0)tl.fromTo("#%ID%-fl",{opacity:0.45},{immediateRender:false,opacity:0,duration:0.1},c[1]);});
tl.set("#%ID%-go",{opacity:1},4.0);
tl.fromTo("#%ID%-door",{rotationY:0,transformPerspective:1600},{rotationY:-70,duration:0.4,ease:"power3.out"},1.55);
tl.fromTo("#%ID%-c2 .rip",{scale:0.2,opacity:1},{scale:1.3,opacity:0,duration:0.5,stagger:0.08,ease:"power1.out"},2.0);
tl.fromTo("#%ID%-mk",{scale:1.15,rotation:-4},{scale:1.0,rotation:0,duration:0.5,ease:"power3.out"},2.5);
tl.fromTo("#%ID%-rope",{strokeDashoffset:2600},{strokeDashoffset:0,duration:0.5,ease:"power2.out"},3.0);
tl.fromTo("#%ID%-hl",{scale:1.12},{scale:1.02,duration:0.5,ease:"power2.out"},3.5);
// walk into smoke
tl.fromTo("#%ID%-crew",{scale:1.0},{scale:1.12,duration:2.6,ease:"none"},4.0);
smokeDrift(tl,"#%ID%-sm2 .smoke",3,9);
tl.fromTo("#%ID%-sm2",{opacity:0.3},{opacity:0.6,duration:2.6},4.0);
// freeze at 6.6: desaturate + vignette closes
tl.to("#%ID%-w",{filter:"grayscale(0.9) brightness(0.55)",duration:0.12,ease:"none"},6.6);
tl.fromTo("#%ID%-vig",{opacity:0},{opacity:1,duration:0.4,ease:"power2.in"},6.6);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S03 PROBLEM (8s)
@scene
def s03():
    sid, dur = "s03-problem", 8
    qs = [
        ("WO IST DER TRUPP?", '<div class="hud mono">FUNK <span class="wv"></span><span class="wv"></span><span class="wv"></span><span class="wv"></span><span class="wv"></span><span class="wv"></span> KANAL ?</div>'),
        ("WIE LANGE SCHON DRIN?", '<div class="hud mono">EINSATZZEIT <span id="%ID%-sw" style="color:#E4E7EB">00:00</span></div>'),
        ("WIE VIEL LUFT NOCH?", '<div class="hud mono">FLASCHENDRUCK <span id="%ID%-pz" style="color:#E4E7EB">180</span> BAR</div>'),
        ("WANN MUSS ER RAUS?", f'<div class="hud mono">RÜCKZUG AB <span style="color:{C["red"]}">??? BAR</span></div>'),
        ("WELCHE MELDUNG KAM WANN?", '<div class="hud mono"><span id="%ID%-ts">14:2?:?? · 14:3?:?? · ??:??:??</span></div>'),
    ]
    blocks = "".join(f'<div class="qb" id="%ID%-q{i}"><div class="big q">{q}</div>{h}</div>' for i, (q, h) in enumerate(qs))
    html = f'''
<div class="full" id="%ID%-bgf" style="opacity:.32;filter:grayscale(1) brightness(.6)">
  <div class="full" style="display:flex;align-items:flex-end;justify-content:center">{icon('house', sid)}</div>
  <div class="full">{person(760, 0.8)}{person(880, 0.85)}{person(1000, 0.78)}</div></div>
<div class="full" style="background:radial-gradient(ellipse at center, rgba(7,9,12,0.55), rgba(7,9,12,0.96) 70%)"></div>
<div class="full" id="%ID%-qs">{blocks}</div>
<div class="full" id="%ID%-stack" style="opacity:0" data-layout-allow-overlap data-layout-allow-occlusion>
 {''.join(f'<div class="big sq" data-layout-allow-overlap data-layout-allow-occlusion style="left:{x}px;top:{y}px;font-size:{s}px">{q}</div>' for (q, _), x, y, s in zip(qs, (90, 560, 160, 840, 300), (150, 330, 520, 640, 800), (120, 96, 132, 104, 110)))}
</div>
<div class="full" id="%ID%-k" style="background:{C['night']};opacity:0;display:flex;align-items:center;justify-content:center">
  <div class="big" data-layout-allow-overlap style="font-size:150px;text-align:center;max-width:1600px">KEINE ZEIT FÜR KOPFRECHNEN.</div></div>'''
    css = f"""
#%ID% .qb {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:36px; opacity:0; }}
#%ID% .q {{ font-size:170px; text-align:center; max-width:1760px; }}
#%ID% .hud {{ font-size:36px; letter-spacing:0.12em; color:{C['muted']}; display:flex; gap:14px; align-items:center; }}
#%ID% .wv {{ display:inline-block; width:10px; height:44px; background:{C['red']}; border-radius:4px; }}
#%ID% .sq {{ position:absolute; color:{C['fg']}; opacity:0.85; white-space:nowrap;
  text-shadow: -6px 0 rgba(217,72,61,0.7), 6px 0 rgba(61,123,255,0.6); }}
"""
    js = """
tl.fromTo("#%ID%-bgf",{scale:1.0},{scale:1.12,duration:8,ease:"none"},0);
for(var i=0;i<5;i++){var t=i*1.2;
 tl.fromTo("#%ID%-q"+i,{opacity:0,scale:1.12},{opacity:1,scale:1,duration:0.14,ease:"power4.out"},t);
 tl.to("#%ID%-q"+i,{opacity:0,duration:0.06},t+1.14);
 tl.fromTo("#%ID%-qs",{x:-14,y:8},{x:0,y:0,duration:0.12,ease:"rough"},t);}
tl.fromTo("#%ID% .wv",{scaleY:0.2},{scaleY:1,duration:0.09,stagger:{each:0.03,repeat:5,yoyo:true},ease:"steps(3)"},0.05);
count(tl,document.getElementById("%ID%-sw"),0,877,1.2,1.0,mmss,"power2.in");
var pz=document.getElementById("%ID%-pz");var po={v:0};pz.textContent="180";
tl.to(po,{v:1,duration:1.1,ease:"none",onUpdate:function(){pz.textContent=String(Math.round(160+20*Math.sin(po.v*40)));}},2.4);
var ts=document.getElementById("%ID%-ts");var to={v:0};var opts=["14:2?:?? · 14:3?:?? · ??:??:??","14:21:?? · 1?:4?:3? · ??:??","??:??:?? · 14:4?:?? · 14:3?"];
tl.to(to,{v:2.99,duration:1.1,ease:"steps(9)",onUpdate:function(){ts.textContent=opts[Math.floor(to.v)];}},4.8);
// everything stacks, then a single glitch
tl.set("#%ID%-stack",{opacity:1},6.0);
tl.fromTo("#%ID% .sq",{opacity:0,scale:1.2},{opacity:0.85,scale:1,duration:0.12,stagger:0.12,ease:"power4.out"},6.0);
tl.fromTo("#%ID%-stack",{x:0},{x:12,duration:0.05,yoyo:true,repeat:9,ease:"steps(1)"},6.5);
tl.fromTo("#%ID%-stack",{filter:"none"},{filter:"blur(2px) contrast(1.8)",duration:0.13,yoyo:true,repeat:1,ease:"steps(1)"},6.82);
tl.set("#%ID%-k",{opacity:1},7.0);
tl.set("#%ID%-k",{opacity:0},7.7);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S04 REVEAL (7s)
@scene
def s04():
    sid, dur = "s04-reveal", 7
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 50% 55%, rgba(217,72,61,0.16), rgba(18,21,26,0) 55%), {C['bg']}" id="%ID%-bg"></div>
<div id="%ID%-line" style="position:absolute;left:0;right:0;top:539px;height:3px;background:{C['red']}"></div>
<div class="full" id="%ID%-persp" style="perspective:1800px">
 <div class="full" id="%ID%-start" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px">
  <div class="mono" id="%ID%-clk" style="font-size:76px;font-weight:600;letter-spacing:0.04em">14:12:00</div>
  <div id="%ID%-ring" style="width:250px;height:250px;border-radius:50%;border:8px solid {C['red']};overflow:hidden;position:relative;
     box-shadow:0 0 70px rgba(217,72,61,0.45);background:#fff">
   <img src="assets/logo.jpg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain" />
   <div id="%ID%-sweep" style="position:absolute;top:-40px;bottom:-40px;width:80px;left:-140px;
     background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,0.85),rgba(255,255,255,0))"></div></div>
  <div class="lbl" id="%ID%-eyebrow" style="font-size:26px;color:{C['fg']}">Feuerwehr Zuchwil</div>
  <div class="big" id="%ID%-title" style="font-size:150px;display:flex"><span class="ch">A</span><span class="ch">T</span><span class="ch">E</span><span class="ch">M</span><span class="ch">S</span><span class="ch">C</span><span class="ch">H</span><span class="ch">U</span><span class="ch">T</span><span class="ch">Z</span></div>
  <div id="%ID%-btn" class="btnp" style="width:720px;height:104px;margin-top:10px">Atemschutzüberwachung</div>
  <div id="%ID%-btn2" style="width:720px;height:92px;border:3px solid {C['line2']};border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:600">Atemschutz Infos</div>
 </div>
 <div class="full" id="%ID%-op" style="opacity:0">
  <div id="%ID%-opin" class="full">
   <div style="position:absolute;left:150px;top:110px;display:flex;align-items:center;gap:30px">
     <div class="big" style="font-size:72px">Atemschutzüberwachung</div><div class="lbl">● Online</div></div>
   <div class="card" style="position:absolute;left:150px;top:240px;width:1620px;height:110px;display:flex;align-items:center;justify-content:center;
     font-size:36px;font-weight:700;border-style:dashed" id="%ID%-add">+ Trupp hinzufügen</div>
   {''.join(f"""<div class="card tk" style="position:absolute;left:{150 + i * 548}px;top:400px;width:524px;height:520px;padding:34px">
     <div style="display:flex;justify-content:space-between"><div class="osw" style="font-size:44px;font-weight:700">Trupp {n}</div>
     <div class="mono" style="font-size:20px;padding:6px 14px;border-radius:999px;background:{c};color:#fff;height:36px">{s}</div></div>
     <div class="osw" style="font-size:150px;font-weight:700;margin-top:20px;line-height:1.2">{v}<span style="font-size:30px;font-weight:400;color:{C['muted']};margin-left:12px">bar</span></div>
     <div style="margin-top:30px;height:14px;border-radius:7px;background:{C['line']}"><div style="height:14px;border-radius:7px;width:{v / 3:.0f}%;background:{c}"></div></div>
     <div class="mono" style="font-size:22px;color:{C['muted']};margin-top:18px">Rückzug ab {rz} bar</div></div>"""
       for i, (n, s, v, c, rz) in enumerate((("Müller", "IM EINSATZ", 210, C['green'], 74), ("Frei", "IM EINSATZ", 254, C['green'], 50), ("Schaad", "BEREIT", 300, "#4B5563", 50))))}
  </div>
 </div>
</div>
<div class="mono" id="%ID%-cap" style="position:absolute;left:0;right:0;bottom:64px;text-align:center;font-size:24px;letter-spacing:0.18em;color:#C7CDD3;opacity:0">ATEMSCHUTZÜBERWACHUNG · FEUERWEHR ZUCHWIL</div>'''
    js = """
tl.fromTo("#%ID%-line",{scaleX:0},{scaleX:1,duration:0.3,ease:"expo.out"},0.05);
tl.to("#%ID%-line",{opacity:0,duration:0.3},0.45);
tl.fromTo("#%ID%-bg",{opacity:0},{opacity:1,duration:0.8},0.2);
count(tl,document.getElementById("%ID%-clk"),51120,51127,0.3,6.5,clock);
tl.fromTo("#%ID%-clk",{opacity:0,y:20},{opacity:1,y:0,duration:0.5,ease:"power3.out"},0.3);
tl.fromTo("#%ID%-ring",{opacity:0,scale:0.6},{opacity:1,scale:1,duration:0.7,ease:"back.out(1.6)"},0.45);
tl.fromTo("#%ID%-sweep",{x:0},{x:520,duration:0.8,ease:"power2.inOut"},0.9);
tl.fromTo("#%ID%-eyebrow",{opacity:0,y:10},{opacity:1,y:0,duration:0.4},0.9);
tl.fromTo("#%ID%-title .ch",{opacity:0,x:function(i){return (i-4.5)*70;}},{opacity:1,x:0,duration:1.0,ease:"expo.out"},1.0);
tl.fromTo("#%ID%-btn",{opacity:0,y:30},{opacity:1,y:0,duration:0.45,ease:"power3.out"},1.7);
tl.fromTo("#%ID%-btn2",{opacity:0,y:30},{opacity:1,y:0,duration:0.45,ease:"power3.out"},1.82);
tl.fromTo("#%ID%-cap",{opacity:0},{opacity:1,duration:0.5},2.0);
// layers drift apart in depth
tl.to("#%ID%-clk",{y:-60,z:-300,opacity:0.5,duration:1.2,ease:"power2.inOut"},2.5);
tl.to("#%ID%-ring",{z:-200,y:-30,duration:1.2,ease:"power2.inOut"},2.5);
tl.to("#%ID%-title",{z:150,duration:1.2,ease:"power2.inOut"},2.5);
tl.to("#%ID%-btn",{z:320,y:20,duration:1.2,ease:"power2.inOut"},2.5);
// dive through the primary button
tl.to("#%ID%-start",{scale:9,y:-2200,opacity:0,duration:0.75,ease:"power3.in",transformOrigin:"50% 82%"},3.7);
tl.set("#%ID%-op",{opacity:1},4.25);
tl.fromTo("#%ID%-opin",{rotationX:24,rotationY:-10,scale:0.7,z:-600,opacity:0},{rotationX:14,rotationY:-6,scale:0.86,z:0,opacity:1,duration:1.1,ease:"expo.out"},4.25);
tl.fromTo("#%ID%-opin .tk",{y:80},{y:0,duration:0.9,stagger:0.08,ease:"power3.out"},4.3);
tl.to("#%ID%-opin",{rotationX:6,rotationY:4,duration:1.2,ease:"sine.inOut"},5.35);
tl.to("#%ID%-cap",{opacity:0,duration:0.3},6.3);
// zoom into + Trupp hinzufuegen
tl.to("#%ID%-opin",{scale:3.2,y:820,rotationX:0,rotationY:0,duration:0.4,ease:"power3.in",transformOrigin:"50% 27%"},6.6);
"""
    write_scene(sid, dur, html, "", js)


# ================================================================ S05 TRUPP IN SEKUNDEN (7s)
@scene
def s05():
    sid, dur = "s05-trupp", 7
    fields = [("Truppführer", "Müller", "f1"), ("AdF 1", "Keller", "f2"), ("AdF 2", "Brunner", "f3"),
              ("Einstiegsdruck (bar)", "300", "f4"), ("Strasse", "Hauptstrasse 12", "f5"), ("Ort", "Zuchwil", "f6"),
              ("Funkkanal", "3", "f7"), ("Seilfarbe", "rot", "f8")]
    fhtml = "".join(f'''<div class="fld" id="%ID%-{k}w"><div class="lbl">{l}</div><div class="inp" id="%ID%-{k}">&nbsp;</div></div>''' for l, v, k in fields)
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 50% 40%, rgba(61,123,255,0.18), rgba(0,0,0,0) 60%), {C['night']}"></div>
{rain(40, 31, 0.35)}
<div class="full" style="perspective:2200px">
<div id="%ID%-cam" class="full">
 <div id="%ID%-dev" style="position:absolute;left:260px;top:60px;width:1400px;height:960px;border-radius:56px;background:#05070A;
   border:4px solid #2A3038;box-shadow:0 60px 160px rgba(0,0,0,0.8), 0 0 0 14px #0B0E12">
  <div id="%ID%-scr" style="position:absolute;inset:28px;border-radius:34px;background:{C['bg']};overflow:hidden">
   <div style="position:absolute;left:44px;top:34px;right:44px;display:flex;justify-content:space-between;align-items:center">
     <div class="big" style="font-size:52px">Atemschutzüberwachung</div><div class="lbl">14:12:01</div></div>
   <div id="%ID%-add" class="card" style="position:absolute;left:44px;right:44px;top:120px;height:96px;display:flex;align-items:center;justify-content:center;
     font-size:34px;font-weight:700;border-style:dashed">+ Trupp hinzufügen</div>
   <div id="%ID%-tcard" class="card" style="position:absolute;left:44px;right:44px;top:250px;height:250px;padding:30px 36px;opacity:0">
     <div style="display:flex;justify-content:space-between;align-items:center"><div class="osw" style="font-size:52px;font-weight:700">Trupp Müller</div>
       <div class="mono" id="%ID%-tst" style="font-size:24px;padding:8px 20px;border-radius:999px;background:#4B5563;color:#fff">BEREIT</div></div>
     <div style="font-size:26px;color:{C['muted']};margin-top:10px">Keller, Brunner · 300 bar · Hauptstrasse 12, Zuchwil · Kanal 3 · Seil rot</div>
     <div style="display:flex;gap:30px;align-items:center;margin-top:26px">
       <div id="%ID%-go" class="btnp" style="width:300px;height:84px;background:{C['green']}">▶ Einsatz</div>
       <div class="mono" style="font-size:52px;font-weight:600" id="%ID%-ez">00:00</div><div class="lbl">Einsatzzeit</div></div></div>
   <div id="%ID%-form" class="card" style="position:absolute;left:44px;right:44px;top:250px;bottom:30px;padding:30px 36px;background:{C['card']}">
     <div class="osw" style="font-size:40px;font-weight:700;margin-bottom:18px">Trupp einteilen</div>
     <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px 30px">{fhtml}</div>
     <div style="display:flex;gap:20px;margin-top:22px">
      <div class="lbl" id="%ID%-gps" style="padding:14px 22px;border:3px solid {C['line2']};border-radius:16px;color:{C['fg']}">📍 GPS</div>
      <div style="flex:1"></div>
      <div id="%ID%-ok" class="btnp" style="width:400px;height:76px">Trupp einteilen</div></div>
   </div>
  </div>
 </div>
 <div class="ripple" id="%ID%-r1"></div>
</div></div>
<div id="%ID%-mg" style="position:absolute;left:1180px;top:300px;opacity:0">{gauge_svg('%ID%-g', 420).replace('%ID%', sid)}</div>
<div class="full" id="%ID%-txt" data-layout-allow-overlap style="display:flex;align-items:center;justify-content:center;opacity:0;background:rgba(7,9,12,0.72)">
 <div class="big" data-layout-allow-overlap style="font-size:150px;text-align:center">IN SEKUNDEN<span data-layout-allow-overlap style="color:{C['red']}"> EINSATZBEREIT.</span></div></div>
<div class="flash" id="%ID%-fl" style="background:{C['red']}"></div>'''
    css = f"""
#%ID% .fld {{ display:flex; flex-direction:column; gap:8px; }}
#%ID% .inp {{ border:3px solid {C['line2']}; border-radius:14px; padding:12px 18px; font-size:30px; font-weight:600; min-height:62px; }}
#%ID% .inp.on {{ border-color:{C['fg']}; }}
"""
    js = """
// camera helper: move the device so (x,y) of the canvas lands center with scale s
function cam(at,x,y,s,d,ease){tl.to("#%ID%-cam",{x:(960-x)*s,y:(540-y)*s,scale:s,duration:d||0.35,ease:ease||"power3.inOut"},at);}
tl.fromTo("#%ID%-cam",{scale:3.0,x:0,y:2000,rotationX:0},{scale:1.0,x:0,y:0,duration:0.45,ease:"expo.out"},0);
tl.fromTo("#%ID%-dev",{rotationX:10,rotationY:-8},{rotationX:4,rotationY:6,duration:7,ease:"sine.inOut"},0);
function tap(at,x,y){tl.set("#%ID%-r1",{left:x,top:y},at);tl.fromTo("#%ID%-r1",{scale:0.3,opacity:1},{scale:1.6,opacity:0,duration:0.4,ease:"power2.out"},at);}
// 1 + Trupp hinzufuegen
tap(0.25,960,250);
tl.fromTo("#%ID%-form",{y:900,opacity:0},{y:0,opacity:1,duration:0.4,ease:"expo.out"},0.4);
// 2 names
cam(1.0,760,520,1.3);
var F=function(k){return document.getElementById("%ID%-"+k);};
type(tl,F("f1"),"Müller",1.2,0.3);type(tl,F("f2"),"Keller",1.45,0.3);type(tl,F("f3"),"Brunner",1.7,0.3);
// 3 Einstiegsdruck with gauge match cut
cam(2.2,1040,600,1.3);
tl.fromTo("#%ID%-mg",{opacity:0,scale:1.4,x:0,y:0},{opacity:1,scale:1,duration:0.2,ease:"power3.out"},2.25);
gauge(tl,"%ID%-g",0,300,2.3,0.35,"power4.out");
tl.to("#%ID%-mg",{scale:0.12,x:-420,y:160,opacity:0,duration:0.35,ease:"power3.in"},2.75);
type(tl,F("f4"),"300",2.95,0.15);
// 4 Strasse / Ort via GPS, Funk, Seil
cam(3.3,860,720,1.3);
tap(3.4,480,860);
tl.fromTo("#%ID%-gps",{backgroundColor:"rgba(61,123,255,0)"},{backgroundColor:"rgba(61,123,255,0.45)",duration:0.15,yoyo:true,repeat:1},3.4);
type(tl,F("f5"),"Hauptstrasse 12",3.55,0.35);type(tl,F("f6"),"Zuchwil",3.6,0.25);
type(tl,F("f7"),"3",3.9,0.05);type(tl,F("f8"),"rot",3.95,0.12);
["f1","f2","f3","f4","f5","f6","f7","f8"].forEach(function(k,i){var t=[1.2,1.45,1.7,2.95,3.55,3.6,3.9,3.95][i];
 tl.fromTo(F(k),{borderColor:"#3A424B"},{borderColor:"#E4E7EB",duration:0.05},t);tl.to(F(k),{borderColor:"#3A424B",duration:0.2},t+0.4);});
// 5 Trupp einteilen
cam(4.3,1280,880,1.35);
tap(4.55,1430,945);
tl.to("#%ID%-form",{y:900,opacity:0,duration:0.3,ease:"power3.in"},4.65);
tl.fromTo("#%ID%-tcard",{opacity:0,y:-160},{opacity:1,y:0,duration:0.35,ease:"bounce.out"},4.85);
cam(4.9,800,500,1.25);
// 6 Einsatz starten
tap(5.55,480,670);
tl.fromTo("#%ID%-fl",{opacity:0.35},{immediateRender:false,opacity:0,duration:0.2},5.55);
tl.to("#%ID%-tst",{backgroundColor:"#3E8E41",duration:0.05},5.6);
var st=document.getElementById("%ID%-tst");var so={v:0};
tl.to(so,{v:1,duration:0.01,onUpdate:function(){st.textContent=so.v>0.5?"IM EINSATZ":"BEREIT";}},5.6);
count(tl,document.getElementById("%ID%-ez"),0,1.4,5.6,1.4,mmss);
tl.fromTo("#%ID%-cam",{rotation:0},{immediateRender:false,keyframes:[{rotation:0.6,duration:0.05},{rotation:0,duration:0.15}]},5.55);
// 7 overlay text
tl.fromTo("#%ID%-txt",{opacity:0},{opacity:1,duration:0.15},6.0);
tl.fromTo("#%ID%-txt .big",{scale:1.15},{scale:1,duration:0.4,ease:"power4.out"},6.0);
tl.to("#%ID%-txt",{y:-1100,filter:"blur(20px)",duration:0.25,ease:"power3.in"},6.75);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S06 LIVE (6s)
@scene
def s06():
    sid, dur = "s06-live", 6
    labels = [("EINSATZZEIT", "%ID%-l1", 70, 200), ("ATEMLUFT", "%ID%-l2", 70, 620),
              ("NÄCHSTE ABFRAGE", "%ID%-l3", 1500, 200), ("TRUPPSTATUS", "%ID%-l4", 1500, 450), ("RÜCKZUG AB", "%ID%-l5", 1500, 700)]
    vals = {"%ID%-l1": '<span id="%ID%-v1">12:48</span>', "%ID%-l2": '<span id="%ID%-v2">210</span> bar',
            "%ID%-l3": '<span id="%ID%-v3">07:12</span>', "%ID%-l4": f'<span style="color:{C["green"]}">IM EINSATZ</span>',
            "%ID%-l5": f'<span style="color:{C["orange"]}">74 bar</span>'}
    lab = "".join(f'<div class="tag" id="{i}" style="left:{x}px;top:{y}px"><div class="lbl">{t}</div><div class="osw tv">{vals[i]}</div></div>' for t, i, x, y in labels)
    stats = [("0", "Alarm", C['red']), ("0", "Rückzug", C['orange']), ("2", "Im Einsatz", C['green']), ("1", "Bereit", "#8B95A1")]
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 50% 50%, rgba(61,123,255,0.16), rgba(0,0,0,0) 60%), {C['night']}"></div>
<div class="full" id="%ID%-a">
 <div class="full" style="perspective:2000px;display:flex;align-items:center;justify-content:center">
  <div id="%ID%-holder" style="width:1180px;height:900px;position:relative;transform:scale(0.8)">{app_card('%ID%-card', acts=False, style='left:0;top:60px;transform-origin:50% 50%')}</div></div>
 {lab}
 <div class="lbl" style="position:absolute;right:70px;bottom:60px;color:#C7CDD3">ZEITRAFFER ×12</div>
</div>
<div class="full" id="%ID%-lead" style="opacity:0;background:{C['bg']}">
 <div style="position:absolute;left:120px;top:90px"><div class="big" style="font-size:76px">Einsatzleiter-Ansicht</div>
  <div class="lbl" style="margin-top:26px" id="%ID%-lc">14:26:07 · nur Übersicht, keine Bedienung</div></div>
 <div style="position:absolute;left:120px;right:120px;top:270px;display:flex;gap:30px">
  {''.join(f'<div class="card st" style="flex:1;padding:26px 30px;border-color:{c}"><div class="osw" style="font-size:96px;font-weight:700;color:{c};line-height:1">{n}</div><div style="font-size:30px;font-weight:600">{l}</div></div>' for n, l, c in stats)}</div>
 <div style="position:absolute;left:120px;right:120px;top:540px;display:flex;gap:30px">
  {''.join(f"""<div class="card lc" style="flex:1;padding:30px;border-color:{c}"><div style="display:flex;justify-content:space-between"><div class="osw" style="font-size:46px;font-weight:700">{n}</div>
   <div class="mono" style="font-size:22px;color:{c}">{s}</div></div><div style="font-size:24px;color:{C['muted']};margin-top:8px">{m}</div>
   <div style="margin-top:26px;height:16px;border-radius:8px;background:{C['line']}"><div style="height:16px;border-radius:8px;width:{p:.0f}%;background:{c}"></div></div>
   <div class="mono" style="font-size:22px;color:{C['muted']};margin-top:14px;display:flex;justify-content:space-between"><span>{v} bar</span><span>Rückzug ab {r} bar</span></div></div>"""
     for n, s, m, p, v, r, c in (("Müller", "Im Einsatz", "Keller, Brunner · Brandbekämpfung 1. OG", 202 / 3, 202, 74, C['green']),
                                 ("Frei", "Im Einsatz", "Roth, Studer · Personensuche DG", 251 / 3, 251, 50, C['green']),
                                 ("Schaad", "Bereit", "Kunz, Meier · Reserve", 100, 300, 50, "#8B95A1")))}</div>
</div>'''
    css = f"""
#%ID% .tag {{ position:absolute; padding:18px 26px; border-left:6px solid {C['red']}; background:rgba(18,21,26,0.86); }}
#%ID% .tv {{ font-size:64px; font-weight:700; line-height:1.25; margin-top:4px; }}
"""
    js = """
tl.fromTo("#%ID%-a",{y:1100,filter:"blur(20px)"},{y:0,filter:"blur(0px)",duration:0.3,ease:"power3.out"},0);
tl.fromTo("#%ID%-card",{rotationY:-28,rotationX:10,z:-200},{rotationY:22,rotationX:4,z:0,duration:4.6,ease:"sine.inOut"},0);
var T=12;
count(tl,document.getElementById("%ID%-v1"),768,768+4.4*T,0.2,4.4,mmss);
count(tl,document.getElementById("%ID%-card-ez"),768,768+4.4*T,0.2,4.4,mmss);
count(tl,document.getElementById("%ID%-v3"),432,432-4.4*T,0.2,4.4,mmss);
count(tl,document.getElementById("%ID%-card-nq"),432,432-4.4*T,0.2,4.4,mmss);
count(tl,document.getElementById("%ID%-v2"),210.4,210.4-7*4.4*T/60,0.2,4.4,function(v){return String(Math.round(v));});
gauge(tl,"%ID%-card",210.4,210.4-7*4.4*T/60,0.2,4.4);
["#%ID%-l1","#%ID%-l2","#%ID%-l3","#%ID%-l4","#%ID%-l5"].forEach(function(s,i){
 tl.fromTo(s,{opacity:0,x:i<2?-60:60},{opacity:1,x:0,duration:0.35,ease:"expo.out"},0.35+i*0.62);});
// pull out into Einsatzleiter-Ansicht
tl.to("#%ID%-a",{scale:0.55,opacity:0,duration:0.45,ease:"power3.in"},4.5);
tl.set("#%ID%-lead",{opacity:1},4.85);
tl.fromTo("#%ID%-lead",{scale:1.25},{scale:1,duration:0.6,ease:"expo.out"},4.85);
tl.fromTo("#%ID% .st",{y:40,opacity:0},{y:0,opacity:1,duration:0.4,stagger:0.06,ease:"power3.out"},4.9);
tl.fromTo("#%ID% .lc",{y:60,opacity:0},{y:0,opacity:1,duration:0.45,stagger:0.07,ease:"power3.out"},5.0);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S07 DIE APP RECHNET (8s)
@scene
def s07():
    sid, dur = "s07-rechnet", 8
    nodes = [("FLASCHENDRUCK", '<span id="%ID%-n0">230</span> bar', "erfasst 14:22:07"),
             ("VERBRAUCH", "7,0 bar/min", "300 → 230 bar in 10:00 min"),
             ("RESTDRUCK", '<span id="%ID%-n2">230</span> bar', "läuft live mit"),
             ("EINSATZZIEL ERREICHT", "nach 9,6 min", "14:21:43"),
             ("RÜCKZUG AB", f'<span style="color:{C["orange"]}">74 bar</span>', "9,6 min × 7,0 bar/min × 1,1"),
             ("UMKEHRDRUCK", f'<span style="color:{C["red"]}">50 bar</span>', "fester Alarmwert")]
    nh = "".join(f'''<div class="node" id="%ID%-k{i}"><div class="dot"></div><div><div class="lbl">{t}</div>
      <div class="osw nv">{v}</div><div class="mono ns">{s}</div></div></div>''' for i, (t, v, s) in enumerate(nodes))
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 70% 50%, rgba(217,72,61,0.14), rgba(0,0,0,0) 55%), {C['bg']}"></div>
<div class="full" id="%ID%-a">
 <div id="%ID%-chain" style="position:absolute;left:110px;top:70px;width:760px">
   <div id="%ID%-rail" style="position:absolute;left:21px;top:30px;width:4px;height:840px;background:{C['line2']};transform-origin:50% 0%"></div>
   <div id="%ID%-pk" style="position:absolute;left:12px;top:30px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 0 24px 8px rgba(217,72,61,0.8)"></div>
   {nh}
 </div>
 <div style="position:absolute;left:880px;top:0;bottom:0;right:0;perspective:2000px">
  <div id="%ID%-h" style="position:absolute;left:-40px;top:150px;width:1060px;height:820px;transform-origin:50% 50%">{app_card('%ID%-card', nextq="10:00", val=230, einsatz="10:00", style='left:0;top:0;width:1060px')}</div></div>
 <div class="lbl" id="%ID%-tr" style="position:absolute;right:70px;bottom:50px;color:#C7CDD3;opacity:0">ZEITRAFFER</div>
 <div id="%ID%-push" style="position:absolute;left:1000px;top:40px;width:820px;padding:24px 30px;border-radius:24px;background:rgba(36,40,47,0.97);
   border:3px solid {C['orange']};box-shadow:0 30px 80px rgba(0,0,0,0.6);opacity:0;display:flex;gap:22px;align-items:center">
   <div style="width:58px;height:58px;border-radius:50%;background:{C['orange']}"></div>
   <div><div style="font-size:30px;font-weight:700">Rückzugsdruck – Müller</div><div style="font-size:26px;color:#C7CDD3">Rückzugsdruck erreicht.</div></div></div>
</div>
<div class="full" id="%ID%-words" data-layout-allow-overlap style="display:flex;align-items:flex-end;justify-content:center;gap:50px;padding-bottom:70px;pointer-events:none">
 {''.join(f'<div class="big w" data-layout-allow-overlap style="font-size:64px;opacity:0;background:{C["night"]};padding:6px 18px">{w}</div>' for w in ("AUTOMATISCH.", "SCHNELL.", "ÜBERSICHTLICH."))}</div>'''
    css = f"""
#%ID% .node {{ position:relative; display:flex; gap:30px; align-items:flex-start; height:142px; opacity:0; }}
#%ID% .dot {{ width:46px; height:46px; border-radius:50%; border:5px solid {C['red']}; background:{C['bg']}; flex:none; }}
#%ID% .nv {{ font-size:58px; font-weight:700; line-height:1.05; }}
#%ID% .ns {{ font-size:22px; color:{C['muted']}; }}
"""
    js = """
tl.fromTo("#%ID%-a",{x:1500,filter:"blur(22px)"},{x:0,filter:"blur(0px)",duration:0.3,ease:"power3.out"},0);
tl.fromTo("#%ID%-card",{rotationY:-18,rotationX:6},{rotationY:-6,rotationX:2,duration:8,ease:"sine.inOut"},0);
tl.fromTo("#%ID%-rail",{scaleY:0},{scaleY:1,duration:4.6,ease:"none"},0.3);
// typing 230 + ERFASSEN on the card
var inp=document.getElementById("%ID%-card-in");
tl.to({},{duration:0.01,onUpdate:function(){}},0);
var io={v:0};inp.textContent="Druck (bar)";
tl.to(io,{v:3,duration:0.3,ease:"none",onUpdate:function(){inp.textContent=io.v<0.5?"Druck (bar)":"230".slice(0,Math.round(io.v));inp.classList.toggle("on",io.v>=0.5);}},0.35);
tl.fromTo("#%ID%-card-er",{scale:1},{scale:0.9,duration:0.08,yoyo:true,repeat:1},0.75);
for(var i=0;i<6;i++){var t=0.4+i*0.82;
 tl.fromTo("#%ID%-k"+i,{opacity:0,x:-40},{opacity:1,x:0,duration:0.35,ease:"expo.out"},t);
 tl.fromTo("#%ID%-k"+i+" .dot",{scale:0.4,backgroundColor:"#D9483D"},{scale:1,backgroundColor:"#12151A",duration:0.4,ease:"back.out(2)"},t);
 tl.to("#%ID%-pk",{y:i*142,duration:0.3,ease:"power2.inOut"},t-0.2);}
// Restdruck live, then timelapse to 74 -> card turns orange, push notification
count(tl,document.getElementById("%ID%-n2"),230,226,0.8,4.8,function(v){return String(Math.round(v));});
count(tl,document.getElementById("%ID%-card-nq"),600,575,0.8,4.8,mmss);
count(tl,document.getElementById("%ID%-card-ez"),600,625,0.8,4.8,mmss);
tl.to("#%ID%-h",{x:-120,scale:1.12,duration:0.6,ease:"power3.inOut"},5.6);
tl.to("#%ID%-chain",{opacity:0.25,duration:0.5},5.6);
tl.fromTo("#%ID%-tr",{opacity:0},{opacity:1,duration:0.2},5.8);
gauge(tl,"%ID%-card",226,74,5.8,1.2,"power1.in");
count(tl,document.getElementById("%ID%-card-ez"),625,1937,5.8,1.2,mmss,"power1.in");
count(tl,document.getElementById("%ID%-card-nq"),575,400,5.8,1.2,mmss,"power1.in");
gauge(tl,"%ID%-card",230,226,0.8,4.8);
tl.to("#%ID%-card",{borderColor:"#E8912D",boxShadow:"0 0 90px rgba(232,145,45,0.55)",duration:0.15},7.0);
tl.fromTo("#%ID%-push",{opacity:0,y:-120},{opacity:1,y:0,duration:0.35,ease:"expo.out"},7.05);
// voice-over words
tl.fromTo("#%ID% .w",{opacity:0,y:30},{opacity:1,y:0,duration:0.22,stagger:0.5,ease:"power3.out"},3.2);
tl.to("#%ID% .w",{opacity:0,duration:0.2},5.5);
tl.to("#%ID%-a",{y:-1100,filter:"blur(20px)",duration:0.25,ease:"power3.in"},7.75);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S08 MELDUNGEN (6s)
@scene
def s08():
    sid, dur = "s08-meldungen", 6
    ev = [("14:12:07", "Start", "300 bar"), ("14:21:43", "Einsatzziel erreicht", ""), ("14:22:07", "Druckabfrage", "230 bar"),
          ("14:32:10", "Druckabfrage", "160 bar"), ("14:44:31", "Rückzug gemeldet", ""), ("14:48:55", "Einsatz Ende", "60 bar")]
    evh = "".join(f'''<div class="ev" id="%ID%-e{i}" style="left:{140 + i * 430}px"><div class="tick"></div><div class="mono et">{t}</div>
      <div class="ek">{k}</div><div class="mono ep">{p}</div></div>''' for i, (t, k, p) in enumerate(ev))
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 30% 40%, rgba(61,123,255,0.14), rgba(0,0,0,0) 55%), {C['bg']}"></div>
<div class="full" id="%ID%-a">
 <div id="%ID%-funk" style="position:absolute;left:120px;top:160px;width:640px">
   <div class="ico" style="transform:scale(0.75);transform-origin:0 0">{icon('radio', sid)}</div></div>
 <div id="%ID%-sub" class="mono" style="position:absolute;left:120px;top:690px;width:700px;font-size:34px;color:#C7CDD3">FUNK · «Trupp Müller, Einsatzziel erreicht.»</div>
 <div class="card" style="position:absolute;left:880px;top:140px;width:920px;padding:36px 40px" id="%ID%-pan">
  <div class="osw" style="font-size:48px;font-weight:700">Trupp Müller</div>
  <div style="display:flex;gap:18px;margin-top:22px"><span class="chip" id="%ID%-b1">Einsatzziel erreicht</span><span class="chip" id="%ID%-b2">Rückzug gemeldet</span></div>
  <div class="lbl" style="margin-top:34px">Meldungen</div>
  <div id="%ID%-list" style="margin-top:10px">
   <div class="li"><span class="mono">14:12:07</span><span>Einsatz gestartet · 300 bar</span></div>
   <div class="li hl" id="%ID%-m1"><span class="mono">14:21:43</span><span>Einsatzziel erreicht</span></div>
   <div class="li hl mid"><span class="mono">14:22:07</span><span>230 bar</span></div>
   <div class="li hl mid"><span class="mono">14:32:10</span><span>160 bar</span></div>
   <div class="li hl" id="%ID%-m2"><span class="mono">14:44:31</span><span>Rückzug gemeldet</span></div>
  </div></div>
</div>
<div class="full" id="%ID%-tlw" style="opacity:0;perspective:1600px">
 <div class="lbl" style="position:absolute;left:140px;top:120px;font-size:24px;color:{C['fg']}">Protokoll · Trupp Müller</div>
 <div id="%ID%-tl" style="position:absolute;left:0;top:300px;width:2800px;height:560px">
  <div id="%ID%-axis" style="position:absolute;left:140px;top:110px;width:2400px;height:6px;background:{C['red']};transform-origin:0 50%"></div>
  {evh}</div>
</div>
<div class="ripple" id="%ID%-r"></div>'''
    css = f"""
#%ID% .li {{ display:flex; gap:28px; font-size:30px; padding:14px 0; border-bottom:2px solid {C['line']}; }}
#%ID% .li .mono {{ color:{C['muted']}; }}
#%ID% .li.hl {{ opacity:0; }}
#%ID% .ev {{ position:absolute; top:60px; width:400px; opacity:0; }}
#%ID% .tick {{ width:34px; height:34px; border-radius:50%; background:{C['bg']}; border:6px solid {C['red']}; margin:33px 0 26px; }}
#%ID% .et {{ font-size:40px; font-weight:600; }}
#%ID% .ek {{ font-size:36px; font-weight:700; margin-top:6px; }}
#%ID% .ep {{ font-size:28px; color:{C['muted']}; margin-top:4px; }}
"""
    js = """
tl.fromTo("#%ID%-a",{y:1100,filter:"blur(22px)"},{y:0,filter:"blur(0px)",duration:0.3,ease:"power3.out"},0);
tl.fromTo("#%ID%-led",{opacity:0.2},{opacity:1,duration:0.06,yoyo:true,repeat:9},0.2);
tl.fromTo("#%ID%-sub",{opacity:0},{opacity:1,duration:0.2},0.25);
function tap(at,x,y){tl.set("#%ID%-r",{left:x,top:y},at);tl.fromTo("#%ID%-r",{scale:0.3,opacity:1},{scale:1.6,opacity:0,duration:0.4},at);}
tap(1.1,1110,282);
tl.fromTo("#%ID%-b1",{backgroundColor:"#12151A"},{backgroundColor:"#3E8E41",duration:0.1},1.1);
tl.fromTo("#%ID%-m1",{opacity:0,x:80},{opacity:1,x:0,duration:0.35,ease:"expo.out"},1.25);
tl.fromTo("#%ID%-m1",{backgroundColor:"rgba(217,72,61,0.35)"},{immediateRender:false,backgroundColor:"rgba(217,72,61,0)",duration:0.8},1.3);
var sub=document.getElementById("%ID%-sub");var so={v:0};
tl.to(so,{v:1,duration:0.01,onUpdate:function(){sub.textContent=so.v>0.5?"FUNK · «Rückzug.»":"FUNK · «Trupp Müller, Einsatzziel erreicht.»";}},2.4);
tl.fromTo("#%ID%-led",{opacity:0.2},{immediateRender:false,opacity:1,duration:0.06,yoyo:true,repeat:7},2.4);
tl.fromTo("#%ID% .mid",{opacity:0,x:80},{opacity:1,x:0,duration:0.25,stagger:0.15,ease:"expo.out"},2.0);
tap(2.9,1440,282);
tl.fromTo("#%ID%-b2",{backgroundColor:"#12151A"},{backgroundColor:"#E8912D",duration:0.1},2.9);
tl.fromTo("#%ID%-m2",{opacity:0,x:80},{opacity:1,x:0,duration:0.35,ease:"expo.out"},3.05);
// timeline in 3D
tl.to("#%ID%-a",{opacity:0,scale:0.9,duration:0.3},3.7);
tl.set("#%ID%-tlw",{opacity:1},3.85);
tl.fromTo("#%ID%-tl",{rotationX:40,x:260,y:0},{rotationX:22,x:-380,duration:2.15,ease:"power1.inOut"},3.85);
tl.fromTo("#%ID%-axis",{scaleX:0},{scaleX:1,duration:1.8,ease:"power2.out"},3.9);
for(var i=0;i<6;i++){tl.fromTo("#%ID%-e"+i,{opacity:0,y:30},{opacity:1,y:0,duration:0.3,ease:"power3.out"},3.95+i*0.27);}
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S09 SPLIT (6s)
@scene
def s09():
    sid, dur = "s09-split", 6
    r = random.Random(41)
    scr = ["300 − 230 = ?", "70 : 10 = 7?", "14:22 ?", "Rückzug ??", "9,6 × 7 × 1,1", "Kanal 3 / 5 ?", "Müller 160?", "Ziel 14:21?"]
    notes = "".join(f'<div class="note mono" data-layout-allow-overlap data-layout-allow-occlusion style="left:{r.uniform(40, 560):.0f}px;top:{r.uniform(170, 820):.0f}px;transform:rotate({r.uniform(-12, 12):.1f}deg)">{s}</div>' for s in scr)
    html = f'''
<div class="full" style="background:{C['bg']}"></div>
<div id="%ID%-L" style="position:absolute;left:0;top:0;width:960px;height:1080px;overflow:hidden;
  background:radial-gradient(ellipse at 40% 50%, rgba(232,145,45,0.28), rgba(30,22,14,0.9) 70%)">
 <div id="%ID%-Lin" class="full" data-layout-allow-overlap data-layout-allow-occlusion>
  <div style="position:absolute;left:120px;top:250px">{icon('board', sid)}</div>
  <div style="position:absolute;left:520px;top:520px">{icon('calc', sid)}</div>
  <div style="position:absolute;left:560px;top:180px">{icon('watch', sid)}</div>
  <div style="position:absolute;left:300px;top:640px;transform:scale(0.5);transform-origin:0 0">{icon('radio', sid)}</div>
  {notes}</div>
 <div class="lbl" style="position:absolute;left:60px;top:60px;font-size:28px;color:{C['fg']}">FRÜHER</div>
 <div class="slate" style="top:110px;bottom:auto"><b>PLATZHALTER S9</b><span>Klemmbrett im Regen, Stift, Rechner</span></div>
</div>
<div id="%ID%-div" style="position:absolute;left:957px;top:0;width:6px;height:1080px;background:{C['fg']};z-index:5"></div>
<div id="%ID%-R" style="position:absolute;left:960px;top:0;width:960px;height:1080px;overflow:hidden">
 <div id="%ID%-Rin" style="position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 50%">
  <div class="lbl" style="position:absolute;left:60px;top:60px;font-size:28px;color:{C['fg']}">HEUTE</div>
  <div style="position:absolute;left:60px;top:180px;display:flex;gap:22px">
   {''.join(f'<div class="card" style="width:190px;padding:20px;border-color:{c}"><div class="osw" style="font-size:72px;font-weight:700;color:{c};line-height:1">{n}</div><div style="font-size:24px;font-weight:600">{l}</div></div>' for n, l, c in (("0", "Alarm", C['red']), ("0", "Rückzug", C['orange']), ("2", "Im Einsatz", C['green']), ("1", "Bereit", "#8B95A1")))}</div>
  {''.join(f"""<div class="card" style="position:absolute;left:60px;top:{400 + i * 190}px;width:836px;padding:24px 30px;border-color:{c}">
   <div style="display:flex;justify-content:space-between"><div class="osw" style="font-size:40px;font-weight:700">{n}</div><div class="mono" style="font-size:24px;color:{c}">{v} bar · {s}</div></div>
   <div style="margin-top:16px;height:14px;border-radius:7px;background:{C['line']}"><div style="height:14px;border-radius:7px;width:{p:.0f}%;background:{c}"></div></div></div>"""
     for i, (n, s, v, p, c) in enumerate((("Müller", "Im Einsatz", 202, 67, C['green']), ("Frei", "Im Einsatz", 251, 84, C['green']), ("Schaad", "Bereit", 300, 100, "#8B95A1"))))}
 </div></div>
<div class="full" style="display:flex;align-items:flex-end;justify-content:center;padding-bottom:60px;pointer-events:none;z-index:8">
 <div style="position:relative;height:110px;width:1700px">
 {''.join(f'<div class="big sl" style="position:absolute;left:0;right:0;text-align:center;font-size:84px;opacity:0;background:rgba(7,9,12,0.85);padding:8px 0">{w}</div>' for w in ("WENIGER AUFWAND.", "MEHR ÜBERSICHT.", "MEHR FOKUS AUF DEN EINSATZ."))}</div></div>'''
    css = f"""
#%ID% .note {{ position:absolute; font-size:34px; color:#FFE2B8; background:rgba(40,28,16,0.85); padding:6px 14px; opacity:0;
  text-decoration:line-through; text-decoration-color:rgba(217,72,61,0.9); }}
"""
    js = """
tl.fromTo("#%ID%-L",{x:-960},{x:0,duration:0.35,ease:"expo.out"},0);
tl.fromTo("#%ID%-R",{x:960},{x:0,duration:0.35,ease:"expo.out"},0);
tl.fromTo("#%ID%-div",{scaleY:0},{scaleY:1,duration:0.4,ease:"expo.out"},0.1);
tl.fromTo("#%ID% .note",{opacity:0,scale:1.4},{opacity:1,scale:1,duration:0.15,stagger:0.42,ease:"power4.out"},0.4);
var sh={v:0};var Lin=document.getElementById("%ID%-Lin");
tl.to(sh,{v:1,duration:3.6,ease:"power2.in",onUpdate:function(){var a=sh.v*16;var p=Math.sin(sh.v*180)*a;Lin.style.transform="translate("+p+"px,"+(Math.cos(sh.v*140)*a*0.6)+"px) rotate("+(p*0.05)+"deg)";}},0.4);
tl.to("#%ID%-Rin",{y:-6,duration:2,yoyo:true,repeat:1,ease:"sine.inOut"},0.3);
// wipe the chaos away
tl.to("#%ID%-div",{x:-960,duration:0.6,ease:"power3.inOut"},4.0);
tl.to("#%ID%-L",{x:-960,duration:0.6,ease:"power3.inOut"},4.0);
tl.to("#%ID%-R",{x:-960,width:1920,duration:0.6,ease:"power3.inOut"},4.0);
tl.to("#%ID%-Rin",{scale:1.0,x:480,duration:0.6,ease:"power3.inOut"},4.0);
var S=document.querySelectorAll("#%ID% .sl");
[1.0,2.3,3.7].forEach(function(t,i){tl.fromTo(S[i],{opacity:0,y:20},{opacity:1,y:0,duration:0.25,ease:"power3.out"},t);
 if(i<2)tl.to(S[i],{opacity:0,duration:0.15},[2.3,3.7][i]-0.05);});
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S10 PDF (5s)
@scene
def s10():
    sid, dur = "s10-pdf", 5
    meta = [("Truppführer", "Müller"), ("Truppüberwacher", "Weber"), ("Mannschaft", "Keller, Brunner"), ("Strasse", "Hauptstrasse 12, Zuchwil"),
            ("Auftrag", "Brandbekämpfung 1. OG"), ("Funkkanal", "3"), ("Seilfarbe", "rot"), ("Einstiegsdruck", "300 bar"),
            ("Start", "14:12:07"), ("Ende", "14:48:55"), ("Gesamtdauer", "36:48"), ("Einsatzziel erreicht", "nach 9.6 min")]
    rows = [("14:12:07", "300 bar", "Einsatz gestartet"), ("14:21:43", "", "Einsatzziel erreicht"), ("14:22:07", "230 bar", ""),
            ("14:32:10", "160 bar", ""), ("14:44:31", "", "Rückzug gemeldet"), ("14:48:55", "60 bar", "Einsatz Ende")]
    mh = "".join(f'<div class="pm"><span>{k}</span><b>{v}</b></div>' for k, v in meta)
    rh = "".join(f'<div class="pr"><span>{a}</span><span>{b}</span><span>{c}</span></div>' for a, b, c in rows)
    html = f'''
<div class="full" style="background:radial-gradient(ellipse at 50% 30%, rgba(255,255,255,0.10), rgba(0,0,0,0) 60%), {C['bg']}"></div>
<div id="%ID%-list" class="card" style="position:absolute;left:150px;top:300px;width:1620px;padding:40px 46px">
 <div class="lbl">Vergangene Einsätze</div>
 <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px">
  <div><div class="osw" style="font-size:52px;font-weight:700">Hauptstrasse 12, Zuchwil</div><div style="font-size:28px;color:{C['muted']}">3 Trupps · 14:12 – 14:59</div></div>
  <div style="display:flex;gap:16px"><span class="chip">Ansehen</span><span class="chip" id="%ID%-pdf" style="border-color:{C['red']};color:#fff">PDF (alle)</span></div></div></div>
<div class="ripple" id="%ID%-r"></div>
<div class="full" style="perspective:2400px">
 <div id="%ID%-page" style="position:absolute;left:510px;top:70px;width:900px;height:1270px;background:#FBFBF9;color:#20242B;border-radius:6px;
   box-shadow:0 50px 140px rgba(0,0,0,0.7);padding:60px 64px;opacity:0;transform-origin:50% 0%">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid {C['red']};padding-bottom:20px">
   <div><div style="font-family:Oswald;font-size:46px;font-weight:700">Atemschutzüberwachungsprotokoll</div>
    <div style="font-size:22px;color:#4B5563">Feuerwehr Zuchwil · Trupp Müller (Auftrag 1/1)</div></div>
   <img src="assets/logo.jpg" style="width:70px;height:92px;object-fit:contain"/></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 36px;margin-top:22px" id="%ID%-meta">{mh}</div>
  <div style="margin-top:26px" id="%ID%-tab"><div class="pr ph"><span>Zeit</span><span>Druck</span><span>Meldung</span></div>{rh}</div>
  <div style="display:flex;gap:24px;margin-top:26px" id="%ID%-calc">
   <div class="pc"><span>Luftverbrauch (berechnet)</span><b>7.0 bar/min</b></div>
   <div class="pc"><span>Rückzugsdruck (berechnet)</span><b>74 bar</b></div></div>
 </div></div>'''
    css = f"""
#%ID% .pm {{ display:flex; justify-content:space-between; font-size:22px; padding:7px 0; border-bottom:2px solid #E5E7EB; }}
#%ID% .pm span {{ color:#4B5563; }}
#%ID% .pr {{ display:grid; grid-template-columns:180px 160px 1fr; font-size:22px; padding:8px 12px; border-bottom:2px solid #E5E7EB;
  font-family:'IBM Plex Mono', monospace; }}
#%ID% .ph {{ background:#20242B; color:#fff; font-weight:600; }}
#%ID% .pc {{ flex:1; border:3px solid #20242B; border-radius:10px; padding:14px 18px; display:flex; flex-direction:column; font-size:20px; color:#4B5563; }}
#%ID% .pc b {{ font-family:Oswald; font-size:44px; color:#20242B; }}
"""
    js = """
tl.fromTo("#%ID%-list",{opacity:0,y:60},{opacity:1,y:0,duration:0.35,ease:"expo.out"},0);
tl.set("#%ID%-r",{left:1610,top:446},0.5);
tl.fromTo("#%ID%-r",{scale:0.3,opacity:1},{scale:1.6,opacity:0,duration:0.4},0.5);
tl.fromTo("#%ID%-pdf",{backgroundColor:"rgba(217,72,61,0)"},{backgroundColor:"rgba(217,72,61,1)",duration:0.1},0.5);
tl.to("#%ID%-list",{opacity:0,scale:0.92,duration:0.3},0.75);
tl.fromTo("#%ID%-page",{opacity:0,rotationX:30,y:300,z:-400},{opacity:1,rotationX:12,y:0,z:0,duration:0.7,ease:"expo.out"},0.8);
tl.fromTo("#%ID% .pm",{opacity:0,x:-20},{opacity:1,x:0,duration:0.2,stagger:0.05,ease:"power2.out"},1.0);
tl.fromTo("#%ID% .pr",{opacity:0,y:10},{opacity:1,y:0,duration:0.2,stagger:0.08,ease:"power2.out"},1.6);
tl.fromTo("#%ID% .pc",{opacity:0,scale:0.9},{opacity:1,scale:1,duration:0.3,stagger:0.12,ease:"back.out(2)"},2.3);
tl.to("#%ID%-page",{y:-330,rotationX:4,duration:2.0,ease:"sine.inOut"},2.0);
tl.to("#%ID%-page",{rotationY:-95,x:-500,opacity:0,duration:0.4,ease:"power3.in"},4.6);
"""
    write_scene(sid, dur, html, css, js)


# ================================================================ S11 FINALE (7s)
@scene
def s11():
    sid, dur = "s11-finale", 7
    html = f'''
<div class="shot" id="%ID%-a" style="opacity:1">
 <div id="%ID%-crew" class="full"><video id="%ID%-v-raus" class="clip vid" data-hf-media-start-basis="local" src="assets/footage/trupp-raus.mp4" muted playsinline data-start="0" data-duration="2.2" data-track-index="3"></video></div>
 <div class="full" style="background:radial-gradient(ellipse at 50% 30%, rgba(120,170,255,0.30), rgba(0,0,0,0) 55%)" id="%ID%-back"></div>
 <div id="%ID%-sm" style="opacity:.45">{smoke(6, 51, 200, 1700, 500, 1000, 500, 900)}</div>
 {sparks(18, 52, 300, 1600, 900)}
</div>
<div class="shot" id="%ID%-b">
 <div class="full" style="background:radial-gradient(ellipse at 60% 50%, rgba(61,123,255,0.3), rgba(0,0,0,0) 60%)"></div>
 <div style="position:absolute;left:260px;top:180px;width:1400px;height:760px;border-radius:44px;background:#05070A;border:4px solid #2A3038;
   box-shadow:0 0 140px rgba(120,170,255,0.25)" id="%ID%-tab">
  <div style="position:absolute;inset:24px;border-radius:26px;background:{C['bg']};padding:50px 60px">
   <div class="big" style="font-size:54px">Einsatzleiter-Ansicht</div>
   <div class="card" style="margin-top:40px;padding:34px 40px;border-color:{C['green']}" id="%ID%-done">
    <div style="display:flex;justify-content:space-between;align-items:center"><div class="osw" style="font-size:60px;font-weight:700">Trupp Müller</div>
     <div class="mono" style="font-size:28px;padding:10px 24px;border-radius:999px;background:{C['green']};color:#fff">✓ ABGESCHLOSSEN</div></div>
    <div style="font-size:30px;color:{C['muted']};margin-top:14px">Keller, Brunner · Gesamtdauer 36:48 · Ende 60 bar</div></div>
   <div class="card" style="margin-top:24px;padding:28px 40px"><div style="display:flex;justify-content:space-between"><div class="osw" style="font-size:46px;font-weight:700">Trupp Frei</div>
     <div class="mono" style="font-size:26px;color:{C['green']}">Rückweg · 118 bar</div></div></div>
  </div></div>
 {slate("S11.2", "Einsatzleiter schaut auf das Tablet · Gesicht vom Display beleuchtet")}
</div>
<div class="shot" id="%ID%-c1"><div class="blue" style="left:360px;top:-160px;width:1200px;height:1200px"></div>{slate("S11.3", "Blaulicht · Zeitlupe")}</div>
<div class="shot" id="%ID%-c2"><video id="%ID%-v-lampe" class="clip vid" data-hf-media-start-basis="local" src="assets/footage/lampe.mp4" muted playsinline data-start="4.4" data-duration="0.4" data-track-index="3"></video>{smoke(5, 53, 200, 1700, 200, 900, 600, 1000)}</div>
<div class="shot" id="%ID%-c3"><div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico">{icon('truck', sid).replace(sid + '-bar', sid + '-bar2')}</div></div>{slate("S11.5", "Fahrzeug")}</div>
<div class="shot" id="%ID%-c4"><div class="full" style="display:flex;align-items:center;justify-content:center"><div style="width:560px;height:560px">{gauge_svg('%ID%-g', 560).replace('%ID%', sid)}</div></div>{slate("S11.6", "Atemschutzgerät")}</div>
<div class="shot" id="%ID%-c5"><div class="full" style="display:flex;align-items:center;justify-content:center"><div class="ico" id="%ID%-hel">{icon('helmet', sid)}</div></div>{slate("S11.7", "Helm")}</div>
<div class="shot" id="%ID%-c6"><div class="full" style="display:flex;align-items:center;justify-content:center">
  <div style="width:250px;height:250px;border-radius:50%;border:8px solid {C['red']};overflow:hidden;position:relative;background:#fff;box-shadow:0 0 90px rgba(217,72,61,0.55)">
   <img src="assets/logo.jpg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain" /></div></div></div>
<div class="flash" id="%ID%-fl"></div>
<div class="lb t"></div><div class="lb b"></div>'''
    js = """
tl.fromTo("#%ID%-a",{opacity:0},{opacity:1,duration:0.4},0);
tl.fromTo("#%ID%-crew",{scale:1.0},{scale:1.1,duration:2.2,ease:"none"},0);
tl.fromTo("#%ID%-back",{opacity:0.4},{opacity:1,duration:1.1,yoyo:true,repeat:1,ease:"sine.inOut"},0);
smokeDrift(tl,"#%ID%-sm .smoke",2.2,3);
sparkLoop(tl,"#%ID%-a .spark",2.2,13);
var cuts=[["#%ID%-a",0,2.2],["#%ID%-b",2.2,4.0],["#%ID%-c1",4.0,4.4],["#%ID%-c2",4.4,4.8],["#%ID%-c3",4.8,5.2],["#%ID%-c4",5.2,5.6],["#%ID%-c5",5.6,6.0],["#%ID%-c6",6.0,6.6]];
cuts.forEach(function(c,i){if(i>0){tl.set(c[0],{opacity:1},c[1]);tl.fromTo("#%ID%-fl",{opacity:0.4},{immediateRender:false,opacity:0,duration:0.12},c[1]);}tl.set(c[0],{opacity:0},c[2]);});
tl.fromTo("#%ID%-tab",{scale:1.08,x:60},{scale:1.0,x:0,duration:1.8,ease:"sine.out"},2.2);
tl.fromTo("#%ID%-done",{boxShadow:"0 0 0 rgba(62,142,65,0)"},{boxShadow:"0 0 70px rgba(62,142,65,0.6)",duration:0.6,yoyo:true,repeat:1},2.6);
tl.fromTo("#%ID%-c1 .blue",{scale:0.7},{scale:1.1,duration:0.4},4.0);
smokeDrift(tl,"#%ID%-c2 .smoke",0.4,4);
gauge(tl,"%ID%-g",300,300,5.2,0.1);
tl.fromTo("#%ID%-hel",{scale:1.15},{scale:1.05,duration:0.4},5.6);
tl.fromTo("#%ID%-c3 .ico",{scale:1.12,x:80},{scale:1.0,x:-40,duration:0.4,ease:"power2.out"},4.8);
tl.fromTo("#%ID%-c4 svg",{scale:0.92,rotation:-6},{scale:1.04,rotation:0,duration:0.4,ease:"power2.out"},5.2);
tl.fromTo("#%ID%-c6 .full > div",{scale:0.85},{scale:1.08,duration:0.6,ease:"power2.out"},6.0);
"""
    write_scene(sid, dur, html, "", js)


# ================================================================ S12 SCHLUSS + ENDCARD (9s)
@scene
def s12():
    sid, dur = "s12-ende", 9
    html = f'''
<div class="full" style="background:{C['night']}"></div>
<div class="full ln" id="%ID%-t1"><div class="big" style="font-size:190px">KEINE ZETTEL.</div></div>
<div class="full ln" id="%ID%-t2"><div class="big" style="font-size:190px">KEIN KOPFRECHNEN.</div></div>
<div class="full ln" id="%ID%-t3"><div class="big" style="font-size:150px;text-align:center;max-width:1700px">VOLLER FOKUS AUF DEN <span style="color:{C['red']}">EINSATZ.</span></div></div>
<div class="full" id="%ID%-end" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;
   background:radial-gradient(ellipse at 50% 42%, rgba(217,72,61,0.18), rgba(0,0,0,0) 55%)">
 <div id="%ID%-ring" style="width:230px;height:230px;border-radius:50%;border:8px solid {C['red']};overflow:hidden;position:relative;background:#fff;
   box-shadow:0 0 80px rgba(217,72,61,0.5)"><img src="assets/logo.jpg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain" />
   <div id="%ID%-sweep" style="position:absolute;top:-40px;bottom:-40px;width:80px;left:-140px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,0.85),rgba(255,255,255,0))"></div></div>
 <div class="big" id="%ID%-name" style="font-size:140px;display:flex"><span class="ch">A</span><span class="ch">T</span><span class="ch">E</span><span class="ch">M</span><span class="ch">S</span><span class="ch">C</span><span class="ch">H</span><span class="ch">U</span><span class="ch">T</span><span class="ch">Z</span></div>
 <div id="%ID%-slogan" style="font-size:52px;font-weight:300;letter-spacing:0.02em">Jede Sekunde. Jedes Bar. Im Blick.</div>
 <div id="%ID%-cta" style="margin-top:20px;padding:20px 44px;border-radius:999px;background:{C['red']};color:#fff;font-size:36px;font-weight:700">Jetzt im Übungsmodus testen.</div>
 <div class="lbl" id="%ID%-fw" style="margin-top:6px;color:#C7CDD3">Atemschutzüberwachung · Feuerwehr Zuchwil</div>
</div>'''
    css = """
#%ID% .ln { display:flex; align-items:center; justify-content:center; opacity:0; }
"""
    js = """
[["#%ID%-t1",0.2,1.75],["#%ID%-t2",1.8,3.35],["#%ID%-t3",3.4,5.0]].forEach(function(t,i){
 tl.set(t[0],{opacity:1},t[1]);tl.set(t[0],{opacity:0},t[2]);
 tl.fromTo(t[0]+" .big",{scale:i==2?1.0:1.18},{scale:i==2?1.08:1.0,duration:i==2?1.6:0.35,ease:i==2?"none":"power4.out"},t[1]);});
tl.fromTo("#%ID%-end",{opacity:0},{opacity:1,duration:0.01},5.5);
tl.fromTo("#%ID%-ring",{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.7,ease:"back.out(1.5)"},5.5);
tl.fromTo("#%ID%-sweep",{x:0},{x:520,duration:0.9,ease:"power2.inOut"},5.9);
tl.fromTo("#%ID%-name .ch",{opacity:0,x:function(i){return (i-4.5)*60;}},{opacity:1,x:0,duration:0.9,ease:"expo.out"},6.0);
tl.fromTo("#%ID%-slogan",{opacity:0,y:16},{opacity:1,y:0,duration:0.6,ease:"power3.out"},6.5);
tl.fromTo("#%ID%-cta",{opacity:0,scale:0.9},{opacity:1,scale:1,duration:0.5,ease:"back.out(2)"},7.4);
tl.fromTo("#%ID%-fw",{opacity:0},{opacity:1,duration:0.5},7.6);
"""
    write_scene(sid, dur, html, css, js)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn in SCENES:
        fn()
    print("wrote", len(SCENES), "scenes")
