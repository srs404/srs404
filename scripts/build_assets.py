"""Generate the animated SVG assets for the srs404 GitHub profile README.

All assets share the srs404.com palette (near-black canvas, teal -> violet
gradient) and only use system font stacks, because SVGs loaded through <img>
cannot fetch web fonts. Type sizes are chosen so the smallest text stays
legible when GitHub scales the image down on a ~340px-wide phone column.

Usage (from anywhere):  python scripts/build_assets.py
Edit the typing phrases in hero(), the PROJECTS list, or the buttons at the
bottom, re-run, and commit the regenerated files in assets/.
"""
import html
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

TEAL, VIOLET, MAGENTA = "#5EEAD4", "#8B7CF6", "#F472B6"
CANVAS, RAISED = "#05060B", "#0A0C16"
HI, MID, LOW = "#EDF0F7", "#A6ADC2", "#7C849C"

SERIF = "'Fraunces','Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif"
SANS = "Manrope,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',SFMono-Regular,ui-monospace,Menlo,Consolas,'Liberation Mono',monospace"

BASE_CSS = f"""
.serif{{font-family:{SERIF}}}
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.blink{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

GRAD_H = (f'<linearGradient id="gh" x1="0" y1="0" x2="1" y2="0">'
          f'<stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>')


def esc(s):
    return html.escape(s, quote=False)


def mono_len(text, fs, ls=0.0):
    """Width of monospace text at 0.6em advance plus letter spacing."""
    n = len(text)
    return n * fs * 0.6 + max(n - 1, 0) * ls


def svg_open(w, h, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>')


def write(name, svg):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"{name:<22} {os.path.getsize(path):>6} bytes")


def arrow(x, y, color, size=9, width=1.6):
    """A small north-east arrow whose lower-left corner sits at (x, y)."""
    return (f'<path d="M{x} {y} L{x + size} {y - size} M{x + size * 0.35:.1f} {y - size} '
            f'H{x + size} V{y - size * 0.35:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


# --------------------------------------------------------------------------- hero
def hero():
    W, H = 720, 340
    cx, cy = 548, 170
    rnd = random.Random(404)

    stars = []
    for _ in range(60):
        x, y = rnd.uniform(10, W - 10), rnd.uniform(10, H - 10)
        if x < 400 and 36 < y < 312 and rnd.random() < 0.75:
            continue  # keep the text column calm
        r = rnd.choice([0.6, 0.8, 1.0, 1.2, 1.5])
        stars.append(
            f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{HI}" opacity=".4" '
            f'style="animation-duration:{rnd.uniform(2.8, 6.5):.1f}s;'
            f'animation-delay:-{rnd.uniform(0, 6):.1f}s"/>')

    # Typing line: each phrase is revealed through a clip rect whose width
    # steps one character at a time (SMIL, so it animates inside <img>).
    phrases = ["IT Project Leader", "Full-Stack Developer",
               "Cloud migration wrangler", "Building at Leylance"]
    fs, tx, ty = 22, 72, 292
    cw = fs * 0.6
    type_dt, hold, del_dt, gap = 0.08, 2.1, 0.035, 0.5
    t, spans = 0.4, []
    for p in phrases:
        spans.append((t, p))
        t += len(p) * type_dt + hold + len(p) * del_dt + gap
    T = round(t, 3)

    clips, texts, caret = [], [], [(0.0, 0)]
    for i, (s, p) in enumerate(spans):
        n = len(p)
        ev = [(0.0, 0)]
        ev += [(s + k * type_dt, k) for k in range(1, n + 1)]
        hs = s + n * type_dt + hold
        ev += [(hs + j * del_dt, n - j) for j in range(1, n + 1)]
        caret += ev[1:]
        kt = ";".join(f"{e[0] / T:.4f}" for e in ev)
        vals = ";".join(f"{e[1] * cw:.1f}" for e in ev)
        clips.append(
            f'<clipPath id="c{i}"><rect x="{tx}" y="{ty - 24}" height="34" width="0">'
            f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        texts.append(
            f'<text class="mono" x="{tx}" y="{ty}" font-size="{fs}" fill="{HI}" '
            f'textLength="{n * cw:.1f}" lengthAdjust="spacingAndGlyphs" clip-path="url(#c{i})">{esc(p)}</text>')
    caret.sort()
    ckt = ";".join(f"{e[0] / T:.4f}" for e in caret)
    cvals = ";".join(f"{tx + e[1] * cw + 2:.1f}" for e in caret)

    def spin(dur, start, body):
        return (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'from="{start} {cx} {cy}" to="{start + 360} {cx} {cy}" dur="{dur}s" '
                f'repeatCount="indefinite"/>{body}</g>')

    p1x, p2x, p3x = cx + 58, cx + 96, cx + 134
    moon = (f'<circle cx="{p2x}" cy="{cy}" r="15" fill="none" stroke="#fff" stroke-opacity=".12"/>'
            f'<g><animateTransform attributeName="transform" type="rotate" from="0 {p2x} {cy}" '
            f'to="360 {p2x} {cy}" dur="3.4s" repeatCount="indefinite"/>'
            f'<circle cx="{p2x + 15}" cy="{cy}" r="2.2" fill="{HI}"/></g>')
    planets = (
        spin(11, 30, f'<circle cx="{p1x}" cy="{cy}" r="11" fill="{TEAL}" opacity=".16"/>'
                     f'<circle cx="{p1x}" cy="{cy}" r="5" fill="url(#pT)"/>')
        + spin(19, 205, f'<circle cx="{p2x}" cy="{cy}" r="17" fill="{VIOLET}" opacity=".14"/>'
                        f'<circle cx="{p2x}" cy="{cy}" r="8" fill="url(#pV)"/>{moon}')
        + spin(34, 115, f'<circle cx="{p3x}" cy="{cy}" r="10" fill="{MAGENTA}" opacity=".14"/>'
                        f'<circle cx="{p3x}" cy="{cy}" r="4.5" fill="url(#pM)"/>'
                        f'<circle cx="{cx - 134}" cy="{cy}" r="2.6" fill="{HI}" opacity=".8"/>')
    )

    def planet_grad(gid, light, base):
        # Highlight sits on the side facing the core, so it stays "sun-lit" while orbiting.
        return (f'<radialGradient id="{gid}" cx=".5" cy=".5" r=".6" fx=".2" fy=".5">'
                f'<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{base}"/></radialGradient>')

    pill_txt, pfs, pls = "OPEN TO NEW PROJECTS", 17, 1.8
    ptl = mono_len(pill_txt, pfs, pls)
    pill_w = 36 + ptl + 18

    svg = svg_open(W, H, "Sami Rahman (srs404)",
                   "IT Project Leader and full-stack developer. Open to new projects.")
    svg += f"""<style>{BASE_CSS}
.tw{{animation:tw 4s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.12}}50%{{opacity:.85}}}}
.shoot{{opacity:0;animation:shoot 11s ease-in 2.5s infinite}}
@keyframes shoot{{0%{{transform:translate(250px,-10px) rotate(24deg);opacity:0}}1.5%{{opacity:1}}9%{{transform:translate(520px,110px) rotate(24deg);opacity:0}}100%{{transform:translate(520px,110px) rotate(24deg);opacity:0}}}}
</style>
<defs>{GRAD_H}
<clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<radialGradient id="glowA"><stop offset="0" stop-color="{TEAL}" stop-opacity=".20"/><stop offset=".55" stop-color="{VIOLET}" stop-opacity=".07"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<radialGradient id="glowB"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".16"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<radialGradient id="coreGlow"><stop offset="0" stop-color="{TEAL}" stop-opacity=".55"/><stop offset=".5" stop-color="{VIOLET}" stop-opacity=".18"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<radialGradient id="core" cx=".5" cy=".5" r=".55" fx=".35" fy=".3"><stop offset="0" stop-color="#E6FFFA"/><stop offset=".45" stop-color="{TEAL}"/><stop offset="1" stop-color="{VIOLET}"/></radialGradient>
{planet_grad("pT", "#D5FFF7", TEAL)}{planet_grad("pV", "#D2CBFF", VIOLET)}{planet_grad("pM", "#FFD6EA", MAGENTA)}
<linearGradient id="trail" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="80" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>
{"".join(clips)}
</defs>
<rect width="{W}" height="{H}" rx="22" fill="{CANVAS}"/>
<g clip-path="url(#card)">
<circle cx="{cx}" cy="{cy}" r="250" fill="url(#glowA)"/>
<circle cx="40" cy="0" r="280" fill="url(#glowB)"/>
{"".join(stars)}
<g class="shoot"><line x1="0" y1="0" x2="80" y2="0" stroke="url(#trail)" stroke-width="1.6" stroke-linecap="round"/></g>
<g fill="none" stroke="#fff">
<circle cx="{cx}" cy="{cy}" r="58" stroke-opacity=".11"/>
<circle cx="{cx}" cy="{cy}" r="96" stroke-opacity=".12" stroke-dasharray="1.5 6" stroke-linecap="round"/>
<circle cx="{cx}" cy="{cy}" r="134" stroke-opacity=".07"/>
</g>
<circle cx="{cx}" cy="{cy}" r="46" fill="url(#coreGlow)"/>
<circle cx="{cx}" cy="{cy}" r="21" fill="url(#core)"/>
{planets}
<rect x="44" y="46" width="{pill_w:.1f}" height="36" rx="18" fill="{TEAL}" fill-opacity=".07" stroke="{TEAL}" stroke-opacity=".35"/>
<circle cx="64" cy="64" r="4.5" fill="none" stroke="{TEAL}" stroke-width="1.4"><animate attributeName="r" values="4.5;12" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>
<circle cx="64" cy="64" r="4.5" fill="{TEAL}"/>
<text class="mono" x="80" y="70" font-size="{pfs}" font-weight="600" fill="{TEAL}" textLength="{ptl:.1f}" lengthAdjust="spacing">{pill_txt}</text>
<text class="serif" x="40" y="166" font-size="82" fill="{HI}" letter-spacing="-1.5">Sami</text>
<text class="serif" x="40" y="244" font-size="82" fill="url(#gh)" letter-spacing="-1.5">Rahman</text>
<text class="mono" x="44" y="{ty}" font-size="{fs}" fill="{TEAL}">&#8250;</text>
{"".join(texts)}
<rect class="blink" x="{tx + 2}" y="{ty - 18}" width="2.5" height="23" fill="{TEAL}"><animate attributeName="x" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{ckt}" values="{cvals}"/></rect>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="none" stroke="#fff" stroke-opacity=".09"/>
</svg>"""
    write("hero.svg", svg)


# --------------------------------------------------------------------------- project cards
GX, GY = 350, 58  # glyph centre on every card


def glyph_ervun():
    return f"""<path d="M350 34 L370 41.5 V57 C370 70 361.5 79 350 83 C338.5 79 330 70 330 57 V41.5 Z"/>
<circle cx="350" cy="58" r="15" stroke="{TEAL}" stroke-width="1.2"><animate attributeName="r" values="3;15" dur="2.4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0" dur="2.4s" repeatCount="indefinite"/></circle>
<circle cx="350" cy="58" r="3.2" fill="{TEAL}" stroke="none"/>"""


def glyph_wistrie():
    dots = "".join(
        f'<circle cx="{x}" cy="55" r="2.6" fill="{TEAL}" stroke="none">'
        f'<animate attributeName="cy" values="55;50.5;55;55" keyTimes="0;.2;.4;1" dur="1.4s" begin="{b}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values=".45;1;.45;.45" keyTimes="0;.2;.4;1" dur="1.4s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for x, b in ((340, 0), (350, 0.18), (360, 0.36)))
    return (f'<path d="M336 38 H364 a10 10 0 0 1 10 10 v14 a10 10 0 0 1 -10 10 H345 l-9 8 v-8 '
            f'a10 10 0 0 1 -10 -10 v-14 a10 10 0 0 1 10 -10 Z"/>{dots}')


def glyph_storieme():
    return f"""<path d="M350 44 C342 38 332 38 326 40 V74 C332 72 342 72 350 78 C358 72 368 72 374 74 V40 C368 38 358 38 350 44 Z"/>
<path d="M350 44 V78"/>
<path d="M332 51 H344 M332 57 H344 M332 63 H340 M356 51 H368 M356 57 H364" stroke-opacity=".55"/>
<rect class="blink" x="365" y="58" width="1.8" height="10" fill="{TEAL}" stroke="none"/>"""


def glyph_nexus():
    nodes = [(330, 42), (368, 38), (376, 66), (350, 82), (326, 66)]
    edges = "".join(f"M350 58 L{x} {y} " for x, y in nodes)
    edges += "M330 42 L368 38 M376 66 L350 82 M326 66 L330 42"
    circles = "".join(
        f'<circle cx="{x}" cy="{y}" r="3" fill="{RAISED}">'
        f'<animate attributeName="r" values="3;4.6;3" dur="2.5s" begin="{i * 0.5}s" repeatCount="indefinite"/></circle>'
        for i, (x, y) in enumerate(nodes))
    return (f'<path d="{edges}" stroke-opacity=".55"/>{circles}'
            f'<circle cx="350" cy="58" r="5" fill="{TEAL}" stroke="none"/>')


def glyph_drops():
    steam = "".join(
        f'<path d="M{x} 47 c-3 -4 3 -6 0 -10" opacity="0">'
        f'<animateTransform attributeName="transform" type="translate" values="0 3;0 -4" dur="2.4s" begin="{b}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;.95;0" dur="2.4s" begin="{b}s" repeatCount="indefinite"/></path>'
        for x, b in ((341, 0), (348, 0.8), (355, 1.6)))
    return (f'<path d="M334 52 H362 V63 C362 72 356 78 348 78 C340 78 334 72 334 63 Z"/>'
            f'<path d="M362 56 H365 C371 56 371 67 365 67 H362"/><path d="M328 83 H368"/>{steam}')


def glyph_tripup():
    waves = ("M318 83 " + "q4 -3 8 0 " * 8)
    return f"""<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -1.8;0 0" dur="3.2s" repeatCount="indefinite"/>
<path d="M334 56 L350 42 L366 56"/><path d="M337 55 V70 H363 V55"/><path d="M347 70 V63 H353 V70"/>
<path d="M326 70 H374 L367 77 H333 Z"/></g>
<g clip-path="url(#wclip)"><path d="{waves}" stroke-opacity=".7"><animateTransform attributeName="transform" type="translate" from="0 0" to="8 0" dur="1.6s" repeatCount="indefinite"/></path></g>"""


PROJECTS = [
    dict(slug="ervun", title="Ervun", tag="Flagship · Remote access",
         desc=["Zero-knowledge anti-theft & remote", "control: lock, locate, transfer, wipe."],
         chips=["Zero-knowledge", "Remote"], cta="Live", glyph=glyph_ervun),
    dict(slug="wistrie", title="Wistrie", tag="AI · Google Play",
         desc=["An AI chat that learns how someone", "meaningful to you spoke and thought."],
         chips=["AI", "Android & iOS"], cta="Play", glyph=glyph_wistrie),
    dict(slug="storieme", title="Storieme", tag="Anonymous diary",
         desc=["Moods, people, places and tags with", "nothing social on top. Private-first."],
         chips=["Next.js", "Private-first"], cta="Details", glyph=glyph_storieme),
    dict(slug="nexus", title="Nexus", tag="People tracker",
         desc=["A local-first people graph with fuzzy", "& photo search and a global atlas."],
         chips=["Local-first", "Graph"], cta="Details", glyph=glyph_nexus),
    dict(slug="drops", title="Drops", tag="Coffee · Order & delivery",
         desc=["Customer, store, driver and admin", "apps, shipped end to end."],
         chips=["App suite", "AI-accelerated"], cta="Details", glyph=glyph_drops),
    dict(slug="tripup", title="TripUp", tag="Travel · Stays marketplace",
         desc=["Houseboats, resorts and hotels across", "Bangladesh: search, book and pay."],
         chips=["Marketplace", "Payments"], cta="Details", glyph=glyph_tripup),
]


def card(p):
    W, H = 400, 210
    tag = p["tag"].upper()
    tfs, tls = 12, 1.5
    chips_svg, x = [], 24
    for c in p["chips"]:
        c = c.upper()
        tl = mono_len(c, 11, 1)
        w = tl + 20
        chips_svg.append(
            f'<rect x="{x}" y="166" width="{w:.1f}" height="24" rx="12" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".12"/>'
            f'<text class="mono" x="{x + 10}" y="182" font-size="11" fill="{MID}" textLength="{tl:.1f}" lengthAdjust="spacing">{esc(c)}</text>')
        x += w + 8
    cta = p["cta"].upper()
    ctl = mono_len(cta, 11, 1.5)
    cx_end = W - 24 - 12  # leave room for the arrow
    desc = "".join(
        f'<text class="sans" x="24" y="{126 + i * 22}" font-size="15" fill="{MID}">{esc(line)}</text>'
        for i, line in enumerate(p["desc"]))
    svg = svg_open(W, H, f'{p["title"]}: {p["tag"]}', " ".join(p["desc"]))
    svg += f"""<style>{BASE_CSS}</style>
<defs>{GRAD_H}
<linearGradient id="gs" gradientUnits="userSpaceOnUse" x1="324" y1="32" x2="376" y2="84"><stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="{TEAL}" stop-opacity=".13"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<clipPath id="wclip"><rect x="324" y="76" width="52" height="12"/></clipPath>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="{RAISED}"/>
<g clip-path="url(#card)"><circle cx="{GX}" cy="{GY}" r="95" fill="url(#glow)"/></g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="#fff" stroke-opacity=".09"/>
<rect x="24" y="24" width="28" height="3" rx="1.5" fill="url(#gh)"/>
<text class="mono" x="24" y="54" font-size="{tfs}" font-weight="600" fill="{TEAL}" textLength="{mono_len(tag, tfs, tls):.1f}" lengthAdjust="spacing">{esc(tag)}</text>
<text class="serif" x="23" y="94" font-size="34" fill="{HI}" letter-spacing="-.5">{esc(p["title"])}</text>
{desc}
{"".join(chips_svg)}
<text class="mono" x="{cx_end - 6 - ctl:.1f}" y="182" font-size="11" font-weight="600" fill="{TEAL}" textLength="{ctl:.1f}" lengthAdjust="spacing">{cta}</text>
{arrow(cx_end, 182, TEAL, size=8, width=1.5)}
<g fill="none" stroke="url(#gs)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
{p["glyph"]()}
</g>
</svg>"""
    write(f'card-{p["slug"]}.svg', svg)


# --------------------------------------------------------------------------- buttons
def button(name, label, primary=False):
    fs, ls = 13, 1.4
    tl = mono_len(label, fs, ls)
    pad_l, gap, aw, pad_r = 20, 9, 9, 19
    W, H = round(pad_l + tl + gap + aw + pad_r), 44
    if primary:
        body = f'<rect width="{W}" height="{H}" rx="22" fill="url(#gh)"/>'
        tc, ac = CANVAS, CANVAS
    else:
        body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="{RAISED}" '
                f'stroke="#fff" stroke-opacity=".16"/>')
        tc, ac = HI, TEAL
    ax = pad_l + tl + gap
    svg = svg_open(W, H, label.title(), f"Open {label.title()}")
    svg += f"""<style>{BASE_CSS}</style><defs>{GRAD_H}</defs>{body}
<text class="mono" x="{pad_l}" y="27" font-size="{fs}" font-weight="600" fill="{tc}" textLength="{tl:.1f}" lengthAdjust="spacing">{esc(label)}</text>
{arrow(round(ax, 1), 26.5, ac, size=8, width=1.7)}
</svg>"""
    write(f"btn-{name}.svg", svg)


# --------------------------------------------------------------------------- footer
def footer():
    W, H = 600, 176
    cx, cy, rx, ry = 300, 82, 262, 56
    sig = "SRS404 · OSHAWA, ON · 43.90° N"
    sfs, sls = 14, 2
    stl = mono_len(sig, sfs, sls)
    svg = svg_open(W, H, "Rather than being indecisive, stay Absolute.", "Signed srs404, Oshawa, Ontario.")
    svg += f"""<style>{BASE_CSS}</style>
<defs>{GRAD_H}
<radialGradient id="glow"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".16"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<path id="orb" d="M{cx - rx} {cy} a{rx} {ry} 0 1 0 {2 * rx} 0 a{rx} {ry} 0 1 0 {-2 * rx} 0"/>
</defs>
<rect width="{W}" height="{H}" rx="20" fill="{CANVAS}"/>
<g clip-path="url(#card)"><ellipse cx="{cx}" cy="{cy}" rx="300" ry="120" fill="url(#glow)"/></g>
<use xlink:href="#orb" href="#orb" fill="none" stroke="#fff" stroke-opacity=".07"/>
<circle r="3.5" fill="{TEAL}"><animateMotion dur="18s" repeatCount="indefinite"><mpath xlink:href="#orb" href="#orb"/></animateMotion></circle>
<circle r="2.5" fill="{VIOLET}"><animateMotion dur="18s" begin="-9s" repeatCount="indefinite"><mpath xlink:href="#orb" href="#orb"/></animateMotion></circle>
<text class="serif" x="{cx}" y="76" font-size="30" font-style="italic" fill="{HI}" text-anchor="middle">Rather than being indecisive,</text>
<text class="serif" x="{cx}" y="114" font-size="30" font-style="italic" text-anchor="middle"><tspan fill="{HI}">stay </tspan><tspan fill="url(#gh)">Absolute.</tspan></text>
<text class="mono" x="{cx - stl / 2:.1f}" y="156" font-size="{sfs}" fill="{LOW}" textLength="{stl:.1f}" lengthAdjust="spacing">{esc(sig)}</text>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" fill="none" stroke="#fff" stroke-opacity=".09"/>
</svg>"""
    write("footer.svg", svg)


if __name__ == "__main__":
    hero()
    for p in PROJECTS:
        card(p)
    button("website", "WEBSITE", primary=True)
    button("email", "EMAIL")
    button("linkedin", "LINKEDIN")
    button("resume", "RÉSUMÉ")
    button("instagram", "INSTAGRAM")
    footer()
