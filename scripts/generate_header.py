"""Generate assets/header.svg: a subtle animated "Senior Test Engineer" header.

Usage: python3 scripts/generate_header.py assets/header.svg

Timeline (repeats every PERIOD seconds, after a one-off typing intro):
  * The text types in once with a cursor that then fades away.
  * A Python-coloured snake slithers along under the text; each letter hops
    up as the snake passes beneath it.
  * The snake carries straight on under a little homelab server sitting in
    line with the text, whose LEDs flash as it passes, and off the right edge.
  * A green test tick appears briefly after "Engineer", then fades.

The snake's body is a tapered polygon whose wave shape is morphed with SMIL
(<animate attributeName="d">), which GitHub-rendered <img> SVGs support in all
major browsers. Movement across the header uses CSS keyframes.
"""

import math
import sys

TEXT = "Senior Test Engineer"
FONT = 18
CHAR_W = 11.0           # fixed advance per character (monospace look)
BASE_Y = 30.0           # text baseline
TEXT_MID_Y = BASE_Y - 6.5   # visual middle of the capital letters
SNAKE_Y = 45.0          # snake centre line (below the text)
TEXT_W = CHAR_W * len(TEXT)
SERVER_GAP = 34.0       # space between text end and server
SERVER_W, UNIT_H, UNIT_GAP = 24.0, 8.0, 2.0
W, H = 440, 62
# Centre text + server horizontally.
TEXT_X = round((W - (TEXT_W + SERVER_GAP + SERVER_W)) / 2, 1)
TEXT_END = TEXT_X + TEXT_W
SERVER_X = TEXT_END + SERVER_GAP
SERVER_H = UNIT_H * 2 + UNIT_GAP
SERVER_Y = TEXT_MID_Y - SERVER_H / 2

TYPE_START, TYPE_STEP = 0.3, 0.07
INTRO = 3.0             # loop starts this many seconds after load
PERIOD = 12.0           # loop length (s)
SPEED = 80.0            # px/s along the ground
SNAKE_FROM = -60.0

GREY = "#8B949E"
GREEN = "#22C55E"
SNAKE_BLUE = "#3776AB"
SNAKE_DARK = "#2B5B84"
SNAKE_YELLOW = "#FFD43B"

# ---- timing -----------------------------------------------------------------
BODY_L = 48.0
SNAKE_TO = W + BODY_L + 10     # head x once the tail is off the right edge
TRAVEL = (SNAKE_TO - SNAKE_FROM) / SPEED
type_end = TYPE_START + TYPE_STEP * len(TEXT)


def pct(seconds: float) -> str:
    return f"{seconds / PERIOD * 100:.3f}%"


css = []
body = []

# ---- typing + letters -------------------------------------------------------
css.append(f"""
.t{{font:500 {FONT}px 'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{GREEN}}}
.ch{{opacity:0;animation:type .01s linear forwards}}
@keyframes type{{to{{opacity:1}}}}
.hop{{animation:hop {PERIOD}s ease-in-out infinite}}
@keyframes hop{{0%,4%,100%{{transform:translateY(0)}}2%{{transform:translateY(-4px)}}}}
.cur{{fill:{GREEN};animation:curmove {type_end - TYPE_START:.2f}s steps({len(TEXT)}) {TYPE_START}s forwards,
  blink .5s step-end {type_end:.2f}s 4,curfade .3s {type_end + 2:.2f}s forwards}}
@keyframes curmove{{from{{transform:translateX(0)}}to{{transform:translateX({TEXT_W:.1f}px)}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes curfade{{to{{opacity:0}}}}
""")

for i, ch in enumerate(TEXT):
    if ch == " ":
        continue
    x = TEXT_X + i * CHAR_W
    centre = x + CHAR_W / 2
    t_pass = (centre - SNAKE_FROM) / SPEED          # head under this letter
    hop_delay = INTRO + t_pass - PERIOD * 0.02      # hop peaks as head passes
    type_delay = TYPE_START + i * TYPE_STEP
    body.append(
        f'<g class="hop" style="animation-delay:{hop_delay:.3f}s">'
        f'<text class="t ch" x="{x:.1f}" y="{BASE_Y}" style="animation-delay:{type_delay:.2f}s">{ch}</text></g>'
    )

body.append(f'<rect class="cur" x="{TEXT_X:.1f}" y="{BASE_Y - 14}" width="2" height="17" rx="1"/>')

# ---- snake body geometry ----------------------------------------------------
N_PTS = 28
N_FRAMES = 10
WAVE_LEN = 26.0  # px per full wave along the body


def amp(s: float) -> float:
    """Sideways amplitude: small at the head, fuller along the body."""
    return 3.2 * min(1.0, 0.25 + s / 16)


def half_w(s: float) -> float:
    """Body half-width: thick neck tapering to a pointed tail."""
    return 0.35 + 2.9 * (1 - s / BODY_L) ** 0.8


def centre(s: float, phase: float) -> tuple[float, float]:
    return -s, amp(s) * math.sin(2 * math.pi * s / WAVE_LEN - phase)


def frame(phase: float) -> tuple[str, str, float]:
    ss = [BODY_L * k / (N_PTS - 1) for k in range(N_PTS)]
    top, bot, mid = [], [], []
    for s in ss:
        x, y = centre(s, phase)
        # Normal to the centre line.
        x2, y2 = centre(s + 0.5, phase)
        dx, dy = x2 - x, y2 - y
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        w = half_w(s)
        top.append((x + nx * w, y + ny * w))
        bot.append((x - nx * w, y - ny * w))
        mid.append((x, y))
    pts = top + bot[::-1]
    outline = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in pts) + " Z"
    stripe = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in mid[2:-3])
    return outline, stripe, centre(0, phase)[1]


frames = [frame(2 * math.pi * f / N_FRAMES) for f in range(N_FRAMES)]
frames.append(frames[0])  # seamless loop
WAVE_DUR = "0.9s"
outline_vals = ";".join(f[0] for f in frames)
stripe_vals = ";".join(f[1] for f in frames)
head_vals = ";".join(f"0 {f[2]:.2f}" for f in frames)

snake = (
    f'<path fill="{SNAKE_BLUE}" stroke="{SNAKE_DARK}" stroke-width=".6" stroke-linejoin="round" d="{frames[0][0]}">'
    f'<animate attributeName="d" dur="{WAVE_DUR}" repeatCount="indefinite" values="{outline_vals}"/></path>'
    f'<path fill="none" stroke="{SNAKE_YELLOW}" stroke-width="1.1" stroke-linecap="round" '
    f'stroke-dasharray="2.6 2.4" d="{frames[0][1]}">'
    f'<animate attributeName="d" dur="{WAVE_DUR}" repeatCount="indefinite" values="{stripe_vals}"/></path>'
    # Head: slightly wider than the neck, with eyes and a flicking tongue.
    f'<g><animateTransform attributeName="transform" type="translate" dur="{WAVE_DUR}" '
    f'repeatCount="indefinite" values="{head_vals}"/>'
    f'<path class="tongue" d="M6.2 0h3M9.2 0l1.4 -1.1M9.2 0l1.4 1.1" stroke="#E5534B" '
    f'stroke-width=".7" stroke-linecap="round" fill="none"/>'
    f'<path d="M-2.5 -3.1 C1.5 -4.2 6.8 -2.6 7 0 C6.8 2.6 1.5 4.2 -2.5 3.1 Z" '
    f'fill="{SNAKE_BLUE}" stroke="{SNAKE_DARK}" stroke-width=".6"/>'
    f'<circle cx="3.4" cy="-1.6" r="1" fill="#fff"/><circle cx="3.7" cy="-1.6" r=".5" fill="#111"/>'
    f'<circle cx="3.4" cy="1.6" r="1" fill="#fff"/><circle cx="3.7" cy="1.6" r=".5" fill="#111"/>'
    f'</g>'
)

# ---- snake path across the header -------------------------------------------
def tf(x: float) -> str:
    return f"transform:translateX({x:.1f}px)"


css.append(f"""
.snake{{opacity:0;animation:slither {PERIOD}s linear {INTRO}s infinite}}
@keyframes slither{{
  0%{{opacity:1;{tf(SNAKE_FROM)}}}
  {pct(TRAVEL)}{{opacity:1;{tf(SNAKE_TO)}}}
  {pct(TRAVEL + 0.05)},100%{{opacity:0;{tf(SNAKE_TO)}}}}}
.tongue{{animation:flick 1.1s step-end infinite}}
@keyframes flick{{0%,55%{{opacity:0}}56%,72%{{opacity:1}}73%,100%{{opacity:0}}}}
""")

body.append(
    f'<g transform="translate(0 {SNAKE_Y})"><g class="snake">{snake}</g></g>'
)

# ---- server (in line with the text) -----------------------------------------
arrive = INTRO + (SERVER_X + SERVER_W / 2 - SNAKE_FROM) / SPEED  # head under the server
css.append(f"""
.led{{fill:{GREEN};animation:idle 2.4s ease-in-out infinite}}
@keyframes idle{{0%,100%{{opacity:.35}}50%{{opacity:.9}}}}
.burst{{fill:{GREEN};opacity:0;animation:burst {PERIOD}s linear {arrive:.2f}s infinite}}
@keyframes burst{{0%,2%,4%,6%{{opacity:1}}1%,3%,5%,7%,100%{{opacity:0}}}}
""")
u1, u2 = SERVER_Y, SERVER_Y + UNIT_H + UNIT_GAP
server = [
    f'<g fill="none" stroke="{GREY}" stroke-width="1.3">'
    f'<rect x="{SERVER_X:.1f}" y="{u1:.1f}" width="{SERVER_W}" height="{UNIT_H}" rx="2"/>'
    f'<rect x="{SERVER_X:.1f}" y="{u2:.1f}" width="{SERVER_W}" height="{UNIT_H}" rx="2"/>'
    f'<line x1="{SERVER_X + 11:.1f}" y1="{u1 + UNIT_H / 2:.1f}" x2="{SERVER_X + 19:.1f}" y2="{u1 + UNIT_H / 2:.1f}"/>'
    f'<line x1="{SERVER_X + 11:.1f}" y1="{u2 + UNIT_H / 2:.1f}" x2="{SERVER_X + 19:.1f}" y2="{u2 + UNIT_H / 2:.1f}"/></g>'
]
for j, uy in enumerate([u1, u2]):
    cx, cy = SERVER_X + 5, uy + UNIT_H / 2
    server.append(f'<circle class="led" cx="{cx:.1f}" cy="{cy:.1f}" r="1.5" style="animation-delay:{-j * 1.1:.1f}s"/>')
    server.append(f'<circle class="burst" cx="{cx:.1f}" cy="{cy:.1f}" r="1.8" style="animation-delay:{arrive + j * 0.06:.2f}s"/>')
body.append("".join(server))

# ---- test tick ---------------------------------------------------------------
tick_start = INTRO + (TEXT_END + BODY_L - SNAKE_FROM) / SPEED + 0.2  # tail clear of the text
css.append(f"""
.tick{{opacity:0;transform-box:fill-box;transform-origin:center;animation:tick {PERIOD}s ease-out {tick_start:.2f}s infinite}}
@keyframes tick{{0%{{opacity:0;transform:scale(.4)}}3%{{opacity:1;transform:scale(1.1)}}5%,16%{{opacity:1;transform:scale(1)}}22%,100%{{opacity:0;transform:scale(1)}}}}
""")
tx = TEXT_END + 7
body.append(
    f'<path class="tick" d="M{tx:.1f} {TEXT_MID_Y:.1f} l3.5 3.5 l7 -8" '
    f'stroke="{GREEN}" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
)

# ---- reduced motion ----------------------------------------------------------
css.append("""
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  .ch{opacity:1}.snake,.tick,.burst,.cur{opacity:0}
}
""")

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'role="img" aria-labelledby="title">'
    f'<title id="title">Senior Test Engineer</title>'
    f'<style>{"".join(css)}</style>'
    f'{"".join(body)}</svg>\n'
)

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write(svg)
print(
    f"wrote {sys.argv[1]} ({len(svg)} bytes); text x {TEXT_X}-{TEXT_END}, "
    f"server x {SERVER_X} y {SERVER_Y:.1f}-{SERVER_Y + SERVER_H:.1f}; travel {TRAVEL:.2f}s of {PERIOD}s"
)
