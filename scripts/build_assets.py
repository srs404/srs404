"""Generate the animated SVG assets for the srs404 GitHub profile README.

All assets share the srs404.com palette (near-black canvas, teal -> violet
gradient) and only use system font stacks, because SVGs loaded through <img>
cannot fetch web fonts. Type sizes are chosen so the smallest text stays
legible when GitHub scales the image down on a ~340px-wide phone column.

The LeyLance banner uses the studio's own palette and embeds its official
wordmark and the Wistrie mark from scripts/brand/ (copied from leylance.com).

Usage (from anywhere):  python scripts/build_assets.py
Edit the typing phrases in hero(), the PROJECTS or LEYLANCE_VENTURES lists,
or the buttons at the bottom, re-run, and commit the regenerated assets/.
"""
import base64
import html
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(HERE, "brand")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
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
               "Cloud migration wrangler", "Founder of LeyLance"]
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


def glyph_peolie():
    # An open diary: writing on the left page, a padlock on the right (end-to-end encrypted).
    return f"""<path d="M350 44 C342 38 332 38 326 40 V74 C332 72 342 72 350 78 C358 72 368 72 374 74 V40 C368 38 358 38 350 44 Z"/>
<path d="M350 44 V78"/>
<path d="M332 51 H344 M332 57 H344 M332 63 H339" stroke-opacity=".55"/>
<rect class="blink" x="341" y="58" width="1.8" height="9" fill="{TEAL}" stroke="none"/>
<path d="M358.5 56 v-3.5 a3.5 3.5 0 0 1 7 0 v3.5"/>
<rect x="356" y="56" width="12" height="10" rx="2"/>
<circle cx="362" cy="61" r="1.3" fill="{TEAL}" stroke="none"/>"""


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


# Venture status, as shown on leylance.com: label and accent colour.
STATUS = {
    "live": ("Live", TEAL),
    "beta": ("Beta", VIOLET),
    "private": ("Private beta", VIOLET),
    "prelaunch": ("Pre-launch", MAGENTA),
}

PROJECTS = [
    dict(slug="ervun", title="Ervun", tag="Security & privacy", status="live",
         desc=["Zero-knowledge anti-theft & remote", "control. Keys never leave your devices."],
         chips=["Zero-knowledge", "Windows"], glyph=glyph_ervun),
    dict(slug="wistrie", title="Wistrie", tag="AI companionship", status="live",
         desc=["AI that learns how someone close to you", "spoke, so the conversation can go on."],
         chips=["AI", "Android & iOS"], glyph=glyph_wistrie),
    dict(slug="peolie", title="Peolie", tag="Private journaling", status="live",
         desc=["An end-to-end encrypted, anonymous", "diary. The server can't read a word."],
         chips=["E2E encrypted", "Web"], glyph=glyph_peolie),
    dict(slug="tripup", title="TripUp", tag="Travel marketplace", status="beta",
         desc=["Houseboats, resorts and hotels across", "Bangladesh: search, bid, book and pay."],
         chips=["Marketplace", "Payments"], glyph=glyph_tripup),
    dict(slug="nexus", title="Nexus", tag="Personal software", status="private",
         desc=["A private, local-first console for the", "people in your life. No server at all."],
         chips=["Local-first", "Encrypted"], glyph=glyph_nexus),
    dict(slug="drops", title="drops", tag="Coffee · After dark", status="prelaunch",
         desc=["Late-night coffee delivery for Dhaka:", "four connected apps, one backend."],
         chips=["4 apps", "Real-time"], glyph=glyph_drops),
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
    label, scol = STATUS[p["status"]]
    label = label.upper()
    stl = mono_len(label, 11, 1.5)
    ax = W - 24 - 8                 # arrow ends at the right padding
    st_x = ax - 7 - stl             # status text sits left of the arrow
    dot_x = st_x - 10
    ping = (f'<circle cx="{dot_x:.1f}" cy="178" r="3.5" fill="none" stroke="{scol}" stroke-width="1.2" opacity="0">'
            f'<animate attributeName="r" values="3.5;9" dur="2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>'
            if p["status"] == "live" else "")
    status_svg = (f'{ping}<circle cx="{dot_x:.1f}" cy="178" r="3.5" fill="{scol}"/>'
                  f'<text class="mono" x="{st_x:.1f}" y="182" font-size="11" font-weight="600" fill="{scol}" '
                  f'textLength="{stl:.1f}" lengthAdjust="spacing">{esc(label)}</text>'
                  f'{arrow(ax, 182, scol, size=8, width=1.5)}')
    desc = "".join(
        f'<text class="sans" x="24" y="{126 + i * 22}" font-size="15" fill="{MID}">{esc(line)}</text>'
        for i, line in enumerate(p["desc"]))
    svg = svg_open(W, H, f'{p["title"]}: {p["tag"]} ({STATUS[p["status"]][0].lower()})', " ".join(p["desc"]))
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
{status_svg}
<g fill="none" stroke="url(#gs)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
{p["glyph"]()}
</g>
</svg>"""
    write(f'card-{p["slug"]}.svg', svg)


# --------------------------------------------------------------------------- LeyLance banner
LL_NAVY, LL_AZURE, LL_BRAND, LL_BRAND2, LL_SOFT = "#050B1A", "#2FA8FF", "#3B10EE", "#7C2FF2", "#8FB8FF"

LEYLANCE_VENTURES = [  # (slug, name, status) in leylance.com portfolio order
    ("ervun", "Ervun", "live"), ("wistrie", "Wistrie", "live"), ("peolie", "Peolie", "live"),
    ("tripup", "TripUp", "beta"), ("nexus", "Nexus", "private"), ("drops", "drops", "prelaunch"),
]


def b64(name):
    with open(os.path.join(BRAND, name), "rb") as f:
        return base64.b64encode(f.read()).decode()


def venture_logo(slug, cx, cy, s):
    """Each venture's own mark (from leylance.com), lightened where needed for a dark badge."""
    x, y = cx - s / 2, cy - s / 2
    box = f'x="{x:.1f}" y="{y:.1f}" width="{s}" height="{s}"'
    if slug == "ervun":
        return (f'<svg {box} viewBox="0 0 96 96"><defs><linearGradient id="ervun-g" gradientUnits="userSpaceOnUse" '
                f'x1="12" y1="12" x2="84" y2="84"><stop offset="0" stop-color="#818CF8"/><stop offset="1" stop-color="#A78BFA"/>'
                f'</linearGradient></defs><path d="M22 28 L48 56 L74 28" fill="none" stroke="url(#ervun-g)" stroke-width="14" '
                f'stroke-linecap="round" stroke-linejoin="round"/><circle cx="48" cy="78" r="8" fill="#E0E7FF"/></svg>')
    if slug == "wistrie":
        # The mark is purple line art on transparent, so give it a light disc like its app icon.
        uri = "data:image/png;base64," + b64("wistrie-mark.png")
        return f'<circle cx="{cx}" cy="{cy:.1f}" r="{s / 2 - 1:.1f}" fill="#F5F3FF"/><image {box} href="{uri}"/>'
    if slug == "peolie":
        return (f'<svg {box} viewBox="13 12 40 40"><path fill="#F3EDE4" fill-rule="evenodd" '
                f'd="M20 14H34A12 12 0 0 1 34 38H28V50H20ZM28 22H34A4 4 0 0 1 34 30H28Z"/></svg>')
    if slug == "tripup":
        return (f'<svg {box} viewBox="0 0 24 24" fill="none"><defs><linearGradient id="tripup-g" x1="2" y1="2" x2="22" y2="22" '
                f'gradientUnits="userSpaceOnUse"><stop stop-color="#10B5A6"/><stop offset=".5" stop-color="#1AA6C4"/>'
                f'<stop offset="1" stop-color="#2E73E8"/></linearGradient></defs>'
                f'<circle cx="12" cy="12" r="10" stroke="url(#tripup-g)" stroke-width="2.2"/>'
                f'<polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88" stroke="url(#tripup-g)" '
                f'stroke-width="2.2" stroke-linejoin="round"/></svg>')
    if slug == "nexus":  # the site shows Nexus as a lettermark
        return (f'<text class="sans" x="{cx}" y="{cy + s * 0.29:.1f}" font-size="{s * 0.8:.0f}" font-weight="700" '
                f'fill="#22D3EE" text-anchor="middle">N</text>')
    if slug == "drops":
        return (f'<svg {box} viewBox="0 0 24 24" fill="none"><defs><linearGradient id="drops-g" x1="6" y1="3" x2="18" y2="20" '
                f'gradientUnits="userSpaceOnUse"><stop stop-color="#F0B873"/><stop offset="1" stop-color="#C2703A"/>'
                f'</linearGradient></defs><path d="M12 2.5c3.7 4.5 6 7.7 6 11a6 6 0 1 1-12 0c0-3.3 2.3-6.5 6-11Z" '
                f'fill="url(#drops-g)"/><path d="M9.2 13.4c0 1.9 1.2 3.2 2.9 3.5" stroke="#fff6ea" stroke-opacity=".55" '
                f'stroke-width="1.4" stroke-linecap="round"/></svg>')
    raise ValueError(slug)


def leylance():
    """Studio banner: the official wordmark, with ley lines running from the
    LeyLance mark to every venture. Live ventures pulse; ventures still in the
    works wear a slowly turning dashed ring."""
    W, H = 720, 400
    hub_x, hub_y = 360, 166
    xs = [80, 192, 304, 416, 528, 640]

    def arc_y(x):
        return 262 - 30 * math.sin(math.pi * (x - 80) / 560)

    ley = "M" + " L".join(f"{x} {arc_y(x):.1f}" for x in range(24, 697, 12))

    fans, nodes, labels = [], [], []
    for i, ((slug, name, st), x) in enumerate(zip(LEYLANCE_VENTURES, xs)):
        y = arc_y(x)
        live = st == "live"
        label, _ = STATUS[st]
        scol = TEAL if live else LL_SOFT
        fans.append(f'<path class="flow" d="M{hub_x} {hub_y + 16} L{x} {y - 30:.1f}"/>')
        if live:
            ring = (f'<circle cx="{x}" cy="{y:.1f}" r="40" fill="none" stroke="{TEAL}" stroke-width="1.2" opacity="0">'
                    f'<animate attributeName="r" values="27;40" dur="3s" begin="{i * 0.9}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".55;0" dur="3s" begin="{i * 0.9}s" repeatCount="indefinite"/></circle>'
                    f'<circle cx="{x}" cy="{y:.1f}" r="27" fill="url(#node)" stroke="url(#llg)" stroke-width="1.8"/>')
        else:
            ring = (f'<circle cx="{x}" cy="{y:.1f}" r="27" fill="url(#node)"/>'
                    f'<g><animateTransform attributeName="transform" type="rotate" from="0 {x} {y:.1f}" '
                    f'to="360 {x} {y:.1f}" dur="16s" repeatCount="indefinite"/>'
                    f'<circle cx="{x}" cy="{y:.1f}" r="27" fill="none" stroke="{LL_SOFT}" stroke-opacity=".65" '
                    f'stroke-width="1.5" stroke-dasharray="4 5.425" stroke-linecap="round"/></g>')
        nodes.append(ring + venture_logo(slug, x, y, 34 if slug == "wistrie" else 28))
        labels.append(
            f'<text class="sans" x="{x}" y="{y + 54:.1f}" font-size="21" font-weight="600" fill="#EEF1F6" '
            f'text-anchor="middle">{esc(name)}</text>'
            f'<text class="mono st" x="{x}" y="{y + 75:.1f}" font-size="12.5" font-weight="600" fill="{scol}" '
            f'text-anchor="middle" letter-spacing="1.6">{esc(label.upper())}</text>')

    def wave(a, b, dur, op, width):
        return (f'<path d="{a}" fill="none" stroke="url(#wave)" stroke-width="{width}" stroke-opacity="{op}">'
                f'<animate attributeName="d" values="{a};{b};{a}" dur="{dur}s" repeatCount="indefinite" '
                f'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></path>')

    w1 = ("M-20 372 C160 330 330 404 520 354 S700 330 740 346", "M-20 358 C170 402 360 332 530 372 S710 352 740 336")
    w2 = ("M-20 388 C200 360 380 410 560 370 S710 360 740 372", "M-20 380 C190 400 400 362 560 388 S700 368 740 380")
    wordmark = "data:image/png;base64," + b64("leylance-wordmark-white.png")
    tag = "A VENTURE STUDIO FOR WHAT’S NEXT"

    svg = svg_open(W, H, "LeyLance: a venture studio for what's next",
                   "Ventures: Ervun, Wistrie and Peolie are live; TripUp is in beta, "
                   "Nexus in private beta, and drops is pre-launch.")
    svg += f"""<style>{BASE_CSS}
.flow{{fill:none;stroke:{LL_SOFT};stroke-opacity:.32;stroke-width:1.2;stroke-dasharray:2 7;stroke-linecap:round;animation:flow 1.8s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-18}}}}
@media (max-width:480px){{.st{{display:none}}}}
</style>
<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<linearGradient id="llg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{LL_AZURE}"/><stop offset="1" stop-color="{LL_BRAND2}"/></linearGradient>
<linearGradient id="wave" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0"><stop offset="0" stop-color="{LL_AZURE}" stop-opacity="0"/><stop offset=".3" stop-color="{LL_AZURE}"/><stop offset=".65" stop-color="{LL_BRAND2}"/><stop offset="1" stop-color="{LL_BRAND2}" stop-opacity="0"/></linearGradient>
<linearGradient id="leyg" gradientUnits="userSpaceOnUse" x1="24" y1="0" x2="696" y2="0"><stop offset="0" stop-color="{LL_AZURE}" stop-opacity="0"/><stop offset=".15" stop-color="{LL_AZURE}" stop-opacity=".7"/><stop offset=".85" stop-color="{LL_BRAND2}" stop-opacity=".7"/><stop offset="1" stop-color="{LL_BRAND2}" stop-opacity="0"/></linearGradient>
<radialGradient id="top" cx=".5" cy="0" r=".75"><stop offset="0" stop-color="#2F6BFF" stop-opacity=".30"/><stop offset="1" stop-color="#2F6BFF" stop-opacity="0"/></radialGradient>
<radialGradient id="node" cx=".5" cy=".4" r=".65"><stop offset="0" stop-color="#16285A"/><stop offset="1" stop-color="#0A1330"/></radialGradient>
<filter id="soft" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="2.4"/></filter>
<filter id="glow" x="-10%" y="-100%" width="120%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>
<rect width="{W}" height="{H}" rx="22" fill="{LL_NAVY}"/>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#top)"/>
<g filter="url(#glow)">{wave(*w1, 11, .55, 6)}</g>
{wave(*w1, 11, .9, 1.4)}{wave(*w2, 14, .5, 1)}
{"".join(fans)}
<path d="{ley}" fill="none" stroke="url(#leyg)" stroke-width="1.6"/>
<circle r="3" fill="#CFE6FF" filter="url(#soft)"><animateMotion dur="9s" repeatCount="indefinite" path="{ley}"/><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.92;1" dur="9s" repeatCount="indefinite"/></circle>
<circle r="3" fill="#CFE6FF" filter="url(#soft)"><animateMotion dur="9s" begin="-4.5s" repeatCount="indefinite" path="{ley}"/><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.92;1" dur="9s" begin="-4.5s" repeatCount="indefinite"/></circle>
<image x="125" y="38" width="470" height="{470 * 170 / 1556:.1f}" href="{wordmark}"/>
<ellipse rx="10" ry="2.2" fill="#fff" filter="url(#soft)" opacity="0"><animateMotion dur="5s" repeatCount="indefinite" rotate="auto" calcMode="linear" keyPoints="0;1;1" keyTimes="0;.35;1" path="M355 84 Q425 48 492 87"/><animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.17;.35;1" dur="5s" repeatCount="indefinite"/></ellipse>
<path d="M52 126 H96 M624 126 H668" stroke="#C9D4EE" stroke-opacity=".35"/>
<text class="sans" x="{W / 2}" y="132" font-size="17" font-weight="500" fill="#C9D4EE" text-anchor="middle" textLength="500" lengthAdjust="spacing">{tag}</text>
<svg x="{hub_x - 19}" y="{hub_y - 21}" width="38" height="38" viewBox="0 0 96 96"><defs><linearGradient id="ll-grad" x1="30" y1="14" x2="78" y2="82" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#D8E2F1"/><stop offset=".55" stop-color="#9EB2D4"/><stop offset="1" stop-color="#6E82A8"/></linearGradient></defs><g fill="url(#ll-grad)"><rect x="33.5" y="17" width="11" height="51" rx="5.5"/><rect x="33.5" y="57" width="45" height="11" rx="5.5"/></g><path d="M39 19 L73 62.5" fill="none" stroke="url(#ll-grad)" stroke-width="2.4" stroke-linecap="round" opacity=".5"/><g fill="#EAF0FA"><circle cx="39" cy="19" r="6"/><circle cx="73" cy="62.5" r="6"/></g></svg>
{"".join(nodes)}
{"".join(labels)}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="none" stroke="#fff" stroke-opacity=".09"/>
</svg>"""
    write("leylance.svg", svg)


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
    leylance()
    footer()
