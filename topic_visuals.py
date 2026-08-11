"""
topic_visuals.py — AI4Kids.pk
Hand-drawn SVG teaching visuals. NO API, NO images on disk, Rs 0 forever.

Har function ek self-contained SVG string return karta hai jo seedha
st.markdown(..., unsafe_allow_html=True) se render ho jata hai.
Sab labels Roman Urdu mein.
"""
import math
import os as _os          # module level — raaste (paths) yahan bhi chahiye

# ---- palette (kid-friendly, matches school theme) ----
C_ORANGE = "#e67e22"; C_LIGHT = "#fdf2e2"; C_BROWN = "#8b4513"
C_GREEN  = "#27ae60"; C_BLUE   = "#3498db"; C_RED    = "#e74c3c"
C_PURPLE = "#9b59b6"; C_DARK   = "#2c3e50"; C_GREY   = "#bdc3c7"

def _wrap(inner, w, h, title=""):
    cap = (f'<div style="text-align:center;font-size:15px;color:{C_DARK};'
           f'font-weight:700;margin-top:6px">{title}</div>') if title else ""
    return (f'<div style="text-align:center;margin:10px 0">'
            f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px;height:auto">'
            f'{inner}</svg>{cap}</div>')


# =====================================================================
#  FRACTIONS — aadhi roti, paun pizza
# =====================================================================
def _pie(cx, cy, r, num, den, fill=C_ORANGE, empty=C_LIGHT, stroke=C_BROWN):
    out = []
    if den <= 1:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill if num >= 1 else empty}" '
                   f'stroke="{stroke}" stroke-width="3"/>')
        return "".join(out)
    for i in range(den):
        a0 = 2 * math.pi * i / den - math.pi / 2
        a1 = 2 * math.pi * (i + 1) / den - math.pi / 2
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if (a1 - a0) > math.pi else 0
        col = fill if i < num else empty
        out.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} '
                   f'A{r},{r} 0 {large},1 {x1:.1f},{y1:.1f} Z" '
                   f'fill="{col}" stroke="{stroke}" stroke-width="2.5"/>')
    return "".join(out)

def svg_fraction(num=1, den=2, caption=None):
    """Ek fraction — bhara hua hissa rangeen."""
    w, h = 260, 240
    inner = _pie(130, 110, 95, num, den)
    inner += (f'<text x="130" y="200" text-anchor="middle" font-size="34" '
              f'font-weight="800" fill="{C_DARK}">{num}/{den}</text>')
    return _wrap(inner, w, h, caption or f"{num}/{den} hissa rangeen hai")

def svg_fraction_set():
    """Aadha, tihai, paun — teenon ek saath (roti/pizza style)."""
    parts, labels = [], [(1, 2, "Aadha"), (1, 4, "Chauthai"), (3, 4, "Paun (3/4)")]
    w, h = 660, 250
    for i, (n, d, lab) in enumerate(labels):
        cx = 110 + i * 220
        parts.append(_pie(cx, 105, 82, n, d))
        parts.append(f'<text x="{cx}" y="215" text-anchor="middle" font-size="26" '
                     f'font-weight="800" fill="{C_DARK}">{n}/{d}</text>')
        parts.append(f'<text x="{cx}" y="243" text-anchor="middle" font-size="19" '
                     f'fill="{C_ORANGE}" font-weight="700">{lab}</text>')
    return _wrap("".join(parts), w, h + 20, "Roti ke hisse — kasr (fractions)")


# =====================================================================
#  ASHKAAL — shapes
# =====================================================================
def svg_shapes():
    s = []
    w, h = 660, 230
    # circle
    s.append(f'<circle cx="90" cy="90" r="62" fill="{C_RED}" opacity="0.85" stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<text x="90" y="185" text-anchor="middle" font-size="21" font-weight="800" fill="{C_DARK}">Gol</text>')
    s.append(f'<text x="90" y="208" text-anchor="middle" font-size="15" fill="#666">Circle</text>')
    # square
    s.append(f'<rect x="205" y="30" width="120" height="120" rx="6" fill="{C_BLUE}" opacity="0.85" stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<text x="265" y="185" text-anchor="middle" font-size="21" font-weight="800" fill="{C_DARK}">Murabba</text>')
    s.append(f'<text x="265" y="208" text-anchor="middle" font-size="15" fill="#666">Square</text>')
    # triangle
    s.append(f'<polygon points="440,28 505,150 375,150" fill="{C_GREEN}" opacity="0.85" stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<text x="440" y="185" text-anchor="middle" font-size="21" font-weight="800" fill="{C_DARK}">Musallas</text>')
    s.append(f'<text x="440" y="208" text-anchor="middle" font-size="15" fill="#666">Triangle</text>')
    # rectangle
    s.append(f'<rect x="545" y="48" width="100" height="84" rx="6" fill="{C_PURPLE}" opacity="0.85" stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<text x="595" y="185" text-anchor="middle" font-size="21" font-weight="800" fill="{C_DARK}">Mustateel</text>')
    s.append(f'<text x="595" y="208" text-anchor="middle" font-size="15" fill="#666">Rectangle</text>')
    return _wrap("".join(s), w, h, "Ashkaal — shapes pehchano")


# =====================================================================
#  GHADI — clock
# =====================================================================
def svg_clock(hour=3, minute=0):
    w = h = 300
    cx = cy = 150
    r = 128
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fffdf5" stroke="{C_DARK}" stroke-width="6"/>']
    for n in range(1, 13):
        a = math.pi * 2 * (n / 12) - math.pi / 2
        tx, ty = cx + (r - 26) * math.cos(a), cy + (r - 26) * math.sin(a)
        s.append(f'<text x="{tx:.1f}" y="{ty + 8:.1f}" text-anchor="middle" '
                 f'font-size="24" font-weight="800" fill="{C_DARK}">{n}</text>')
        # tick
        x1, y1 = cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a)
        x2, y2 = cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{C_DARK}" stroke-width="3"/>')
    # hands
    ma = math.pi * 2 * (minute / 60) - math.pi / 2
    ha = math.pi * 2 * ((hour % 12) / 12 + minute / 720) - math.pi / 2
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 62 * math.cos(ha):.1f}" '
             f'y2="{cy + 62 * math.sin(ha):.1f}" stroke="{C_DARK}" stroke-width="10" stroke-linecap="round"/>')
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 96 * math.cos(ma):.1f}" '
             f'y2="{cy + 96 * math.sin(ma):.1f}" stroke="{C_RED}" stroke-width="6" stroke-linecap="round"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{C_DARK}"/>')
    return _wrap("".join(s), w, h,
                 f"Ghadi: {hour} baj kar {minute} minute — chhoti sooi ghanta, "
                 f"lambi laal sooi minute")


# =====================================================================
#  GINTI — counting + number line
# =====================================================================
def svg_counting(n=5, emoji="🥭", label="Ginti karo"):
    per_row = 5
    rows = math.ceil(n / per_row)
    w, h = 560, 90 * rows + 60
    s = []
    for i in range(n):
        r, c = divmod(i, per_row)
        x = 70 + c * 105
        y = 60 + r * 90
        s.append(f'<text x="{x}" y="{y}" font-size="56" text-anchor="middle">{emoji}</text>')
        s.append(f'<text x="{x}" y="{y + 26}" font-size="20" text-anchor="middle" '
                 f'font-weight="800" fill="{C_BLUE}">{i + 1}</text>')
    s.append(f'<text x="{w/2}" y="{h - 12}" text-anchor="middle" font-size="30" '
             f'font-weight="800" fill="{C_DARK}">Total = {n}</text>')
    return _wrap("".join(s), w, h, label)

def svg_number_line(start=0, end=10, mark=None):
    w, h = 660, 130
    x0, x1 = 40, w - 40
    y = 60
    step = (x1 - x0) / (end - start)
    s = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{C_DARK}" stroke-width="4"/>']
    for i in range(start, end + 1):
        x = x0 + (i - start) * step
        s.append(f'<line x1="{x:.1f}" y1="{y - 12}" x2="{x:.1f}" y2="{y + 12}" '
                 f'stroke="{C_DARK}" stroke-width="3"/>')
        s.append(f'<text x="{x:.1f}" y="{y + 38}" text-anchor="middle" font-size="20" '
                 f'font-weight="700" fill="{C_DARK}">{i}</text>')
    if mark is not None and start <= mark <= end:
        mx = x0 + (mark - start) * step
        s.append(f'<circle cx="{mx:.1f}" cy="{y}" r="13" fill="{C_RED}" opacity="0.9"/>')
        s.append(f'<text x="{mx:.1f}" y="{y - 24}" text-anchor="middle" font-size="22" '
                 f'font-weight="800" fill="{C_RED}">{mark}</text>')
    return _wrap("".join(s), w, h, f"Number line: {start} se {end} tak")


# =====================================================================
#  JAMA / MINUS — visual grouping
# =====================================================================
def _dots(x, y, n, colour, per_row=5, rad=17, gap=42):
    s = []
    for i in range(n):
        r, c = divmod(i, per_row)
        s.append(f'<circle cx="{x + c * gap}" cy="{y + r * gap}" r="{rad}" '
                 f'fill="{colour}" stroke="{C_DARK}" stroke-width="2"/>')
    return "".join(s)

def svg_addition(a=3, b=2):
    w, h = 620, 190
    s = [_dots(50, 60, a, C_RED)]
    s.append(f'<text x="{50 + 5 * 42 - 10}" y="72" font-size="46" font-weight="800" fill="{C_DARK}">+</text>')
    s.append(_dots(300, 60, b, C_BLUE))
    s.append(f'<text x="500" y="72" font-size="46" font-weight="800" fill="{C_DARK}">=</text>')
    s.append(f'<text x="560" y="78" font-size="52" font-weight="800" fill="{C_GREEN}">{a + b}</text>')
    s.append(f'<text x="{w/2}" y="165" text-anchor="middle" font-size="30" font-weight="800" '
             f'fill="{C_DARK}">{a} + {b} = {a + b}</text>')
    return _wrap("".join(s), w, h, "Jama — dono group mila do")

def svg_subtraction(a=5, b=2):
    w, h = 620, 190
    s = []
    for i in range(a):
        gone = i >= (a - b)
        col = C_GREY if gone else C_RED
        x = 60 + i * 52
        s.append(f'<circle cx="{x}" cy="62" r="19" fill="{col}" stroke="{C_DARK}" stroke-width="2"/>')
        if gone:   # cross out the removed ones
            s.append(f'<line x1="{x - 15}" y1="47" x2="{x + 15}" y2="77" stroke="{C_RED}" stroke-width="4"/>')
            s.append(f'<line x1="{x + 15}" y1="47" x2="{x - 15}" y2="77" stroke="{C_RED}" stroke-width="4"/>')
    s.append(f'<text x="{w/2}" y="140" text-anchor="middle" font-size="30" font-weight="800" '
             f'fill="{C_DARK}">{a} - {b} = {a - b}</text>')
    s.append(f'<text x="{w/2}" y="172" text-anchor="middle" font-size="19" fill="#666">'
             f'{b} cheezein hata dein — {a - b} bach gayin</text>')
    return _wrap("".join(s), w, h, "Minus — kitne bach gaye?")


# =====================================================================
#  CIRCUIT — battery, taar, bulb
# =====================================================================
def svg_circuit(closed=True):
    w, h = 560, 300
    on = closed
    wire = C_DARK
    s = []
    # wires (rectangle loop)
    s.append(f'<rect x="80" y="70" width="400" height="160" fill="none" '
             f'stroke="{wire}" stroke-width="6"/>')
    # battery (left side)
    s.append(f'<rect x="55" y="120" width="50" height="60" fill="#fff" stroke="none"/>')
    s.append(f'<line x1="80" y1="120" x2="80" y2="180" stroke="#fff" stroke-width="8"/>')
    s.append(f'<line x1="62" y1="128" x2="98" y2="128" stroke="{C_DARK}" stroke-width="7"/>')
    s.append(f'<line x1="70" y1="150" x2="90" y2="150" stroke="{C_DARK}" stroke-width="4"/>')
    s.append(f'<line x1="62" y1="172" x2="98" y2="172" stroke="{C_DARK}" stroke-width="7"/>')
    s.append(f'<text x="80" y="110" text-anchor="middle" font-size="19" '
             f'font-weight="800" fill="{C_DARK}">Cell</text>')
    # switch (top)
    s.append(f'<circle cx="240" cy="70" r="7" fill="{C_DARK}"/>')
    s.append(f'<circle cx="310" cy="70" r="7" fill="{C_DARK}"/>')
    s.append(f'<line x1="230" y1="70" x2="320" y2="70" stroke="#fff" stroke-width="9"/>')
    if closed:
        s.append(f'<line x1="240" y1="70" x2="310" y2="70" stroke="{C_DARK}" stroke-width="6"/>')
    else:
        s.append(f'<line x1="240" y1="70" x2="300" y2="38" stroke="{C_DARK}" stroke-width="6"/>')
    s.append(f'<text x="243" y="28" font-size="18" font-weight="800" fill="{C_DARK}">Switch</text>')
    # bulb (right)
    glow = C_ORANGE if on else "#ecf0f1"
    s.append(f'<line x1="480" y1="130" x2="480" y2="170" stroke="#fff" stroke-width="9"/>')
    if on:
        s.append(f'<circle cx="480" cy="150" r="46" fill="{C_ORANGE}" opacity="0.25"/>')
    s.append(f'<circle cx="480" cy="150" r="30" fill="{glow}" stroke="{C_DARK}" stroke-width="4"/>')
    s.append(f'<path d="M470,158 L476,140 L484,158 L490,140" fill="none" '
             f'stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<text x="480" y="215" text-anchor="middle" font-size="19" '
             f'font-weight="800" fill="{C_DARK}">Bulb</text>')
    msg = ("Switch BAND hai — current ghoom raha hai, bulb JAL raha hai! 💡"
           if closed else "Switch KHULA hai — current nahi ja sakta, bulb BUJHA hai.")
    s.append(f'<text x="{w/2}" y="272" text-anchor="middle" font-size="18" '
             f'font-weight="700" fill="{C_DARK}">{msg}</text>')
    return _wrap("".join(s), w, h, "Bijli ka circuit — cell, taar, switch, bulb")


# =====================================================================
#  MADDAH — solid / liquid / gas
# =====================================================================
def svg_states():
    w, h = 660, 250
    s = []
    boxes = [
        (30,  "Thos (Solid)",  "Zarrat bohat qareeb, jam kar", C_BLUE),
        (250, "Maye (Liquid)", "Zarrat qareeb, magar behte hain", C_GREEN),
        (470, "Gas",           "Zarrat door door, urte hain", C_PURPLE),
    ]
    for bx, title, sub, col in boxes:
        s.append(f'<rect x="{bx}" y="30" width="160" height="130" rx="10" '
                 f'fill="#fff" stroke="{C_DARK}" stroke-width="3"/>')
        if "Solid" in title:
            for r in range(4):
                for c in range(4):
                    s.append(f'<circle cx="{bx + 38 + c * 28}" cy="{58 + r * 28}" r="11" fill="{col}"/>')
        elif "Liquid" in title:
            pts = [(35, 70), (72, 58), (110, 72), (48, 104), (88, 100), (125, 88),
                   (40, 132), (80, 130), (118, 122)]
            for px, py in pts:
                s.append(f'<circle cx="{bx + px}" cy="{py}" r="11" fill="{col}"/>')
        else:
            pts = [(30, 50), (95, 42), (135, 62), (55, 88), (118, 100), (35, 128),
                   (88, 138), (140, 130)]
            for px, py in pts:
                s.append(f'<circle cx="{bx + px}" cy="{py}" r="10" fill="{col}"/>')
        s.append(f'<text x="{bx + 80}" y="188" text-anchor="middle" font-size="20" '
                 f'font-weight="800" fill="{C_DARK}">{title}</text>')
        s.append(f'<text x="{bx + 80}" y="212" text-anchor="middle" font-size="13" '
                 f'fill="#666">{sub}</text>')
    s.append(f'<text x="{w/2}" y="240" text-anchor="middle" font-size="15" fill="{C_DARK}">'
             f'Misal: barf = thos, paani = maye, bhaap = gas</text>')
    return _wrap("".join(s), w, h, "Maddah ki teen halatein")


# =====================================================================
#  PAKISTANI PAISA — stylised coins + notes (G1 Math: "pehchano")
#  NOTE: yeh asli notes ki tasveer NAHI — simplified drawings hain.
#  Rang aur number asli jaise rakhe gaye hain taake bachay pehchan saken.
#  Teacher: asli note/sikka bhi dikhaana behtar hai.
# =====================================================================
# Har note: (qeemat, rang, dusra rang, Urdu hindsa, peeche wali jagah)
# Landmarks tasdeeq-shuda: Rs10 Bab-ul-Khyber, Rs20 Mohenjo-daro,
# Rs50 K2, Rs100 Quaid-e-Azam Residency Ziarat. Sab par Quaid ki tasveer.
PK_NOTES = [
    (10,  "#9ec49a", "#6d9b74", "١٠",  "Bab-ul-Khyber"),
    (20,  "#e0b070", "#c08a4a", "٢٠",  "Mohenjo-daro"),
    (50,  "#88b98f", "#5b8f68", "٥٠",  "K2 pahaar"),
    (100, "#cf8f9c", "#a86070", "١٠٠", "Ziarat Residency"),
]

def _landmark(kind, x, y, col):
    """Chhota sa landmark silhouette — note ke peeche wali tasveer."""
    if kind == "Bab-ul-Khyber":          # gate with two towers + arch
        return (f'<rect x="{x}" y="{y-4}" width="8" height="26" fill="{col}"/>'
                f'<rect x="{x+34}" y="{y-4}" width="8" height="26" fill="{col}"/>'
                f'<path d="M{x+8},{y+22} L{x+8},{y+6} Q{x+21},{y-8} {x+34},{y+6} '
                f'L{x+34},{y+22} Z" fill="{col}"/>')
    if kind == "Mohenjo-daro":           # stupa mound + walls
        return (f'<rect x="{x}" y="{y+10}" width="42" height="12" fill="{col}"/>'
                f'<rect x="{x+12}" y="{y-2}" width="18" height="14" fill="{col}"/>'
                f'<circle cx="{x+21}" cy="{y-4}" r="7" fill="{col}"/>')
    if kind == "K2 pahaar":              # twin peaks
        return (f'<polygon points="{x},{y+22} {x+16},{y-8} {x+30},{y+22}" fill="{col}"/>'
                f'<polygon points="{x+20},{y+22} {x+32},{y+2} {x+44},{y+22}" fill="{col}"/>')
    # Ziarat Residency — wooden house with roof
    return (f'<rect x="{x+4}" y="{y+6}" width="36" height="16" fill="{col}"/>'
            f'<polygon points="{x},{y+6} {x+44},{y+6} {x+22},{y-8}" fill="{col}"/>')

def svg_money():
    """Pakistani sikkay + note.
    NOTE: yeh pehchan-ne ki MASHQ ke liye simplified drawing hai — asli note ki
    photo nahi. Rang, hindse aur peeche wali jagah asli jaisi rakhi gayi hain.
    Sab se behtar: asli note haath mein pakra kar dikhayein, ya SBP ka
    'Rupay ko Pehchano' page kholein."""
    w, h = 700, 470
    s = []
    # ---- coins ----
    s.append(f'<text x="{w/2}" y="24" text-anchor="middle" font-size="20" '
             f'font-weight="800" fill="{C_DARK}">Sikkay (Coins)</text>')
    coins = [(1, 40, "#c9ccd1"), (2, 46, "#c9ccd1"), (5, 52, "#d9b45b"), (10, 58, "#d9b45b")]
    x = 105
    for val, r, col in coins:
        s.append(f'<circle cx="{x}" cy="92" r="{r}" fill="{col}" stroke="{C_DARK}" stroke-width="3"/>')
        s.append(f'<circle cx="{x}" cy="92" r="{r-6}" fill="none" stroke="{C_DARK}" '
                 f'stroke-width="1.5" opacity="0.5"/>')
        s.append(f'<text x="{x}" y="104" text-anchor="middle" font-size="{r*0.82:.0f}" '
                 f'font-weight="800" fill="{C_DARK}">{val}</text>')
        s.append(f'<text x="{x}" y="{92+r+20}" text-anchor="middle" font-size="15" '
                 f'font-weight="700" fill="{C_ORANGE}">Rs {val}</text>')
        x += 160
    # ---- notes ----
    s.append(f'<text x="{w/2}" y="196" text-anchor="middle" font-size="20" '
             f'font-weight="800" fill="{C_DARK}">Note — rang aur number dekho</text>')
    nx = 22
    for val, c1, c2, urdu, place in PK_NOTES:
        NW, NH, NY = 158, 84, 214
        s.append(f'<rect x="{nx}" y="{NY}" width="{NW}" height="{NH}" rx="6" fill="{c1}" '
                 f'stroke="{C_DARK}" stroke-width="2.5"/>')
        s.append(f'<rect x="{nx+6}" y="{NY+6}" width="{NW-12}" height="{NH-12}" rx="3" '
                 f'fill="none" stroke="#ffffff" stroke-width="1.4" opacity="0.8"/>')
        # Quaid-e-Azam portrait (silhouette, left side — jaise asli note par)
        s.append(f'<ellipse cx="{nx+30}" cy="{NY+46}" rx="17" ry="22" fill="#ffffff" opacity="0.55"/>')
        s.append(f'<circle cx="{nx+30}" cy="{NY+38}" r="9" fill="{c2}" opacity="0.9"/>')
        s.append(f'<path d="M{nx+18},{NY+62} Q{nx+30},{NY+46} {nx+42},{NY+62} Z" fill="{c2}" opacity="0.9"/>')
        # landmark
        s.append(_landmark(place, nx + 96, NY + 24, c2))
        # numerals — English + Urdu (jaise note par likha hota hai)
        s.append(f'<text x="{nx+72}" y="{NY+34}" font-size="30" font-weight="800" '
                 f'fill="#ffffff">{val}</text>')
        s.append(f'<text x="{nx+NW-12}" y="{NY+NH-12}" text-anchor="end" font-size="22" '
                 f'font-weight="800" fill="#ffffff">{urdu}</text>')
        s.append(f'<text x="{nx+NW/2}" y="{NY+NH+21}" text-anchor="middle" font-size="16" '
                 f'font-weight="800" fill="{C_DARK}">Rs {val}</text>')
        s.append(f'<text x="{nx+NW/2}" y="{NY+NH+39}" text-anchor="middle" font-size="12" '
                 f'fill="#666">{place}</text>')
        nx += 170
    s.append(f'<text x="{w/2}" y="392" text-anchor="middle" font-size="16" '
             f'font-weight="700" fill="{C_DARK}">Har note par Quaid-e-Azam ki tasveer hoti hai.</text>')
    s.append(f'<text x="{w/2}" y="416" text-anchor="middle" font-size="15" fill="{C_DARK}">'
             f'Rang alag, number alag — dono dekh kar pehchano.</text>')
    s.append(f'<text x="{w/2}" y="440" text-anchor="middle" font-size="14" fill="#666">'
             f'2 sikkay Rs 5 = Rs 10   |   Rs 50 + Rs 50 = Rs 100</text>')
    s.append(f'<text x="{w/2}" y="462" text-anchor="middle" font-size="12" fill="#999">'
             f'(Simplified drawing — asli note bhi haath mein dekho)</text>')
    return _wrap("".join(s), w, h, "Pakistani Paisa — sikkay aur note pehchano")


# =====================================================================
#  AI-generated lesson illustrations (Grade 1-2 SIMPLE mode)
#  generate_lesson_images.py inhe banata hai; app sirf padhta hai.
# =====================================================================
LESSON_IMAGE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "lesson_images")

def lesson_image_slug(grade, subject_key, title):
    import re as _re
    s = _re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:40]
    return f"g{grade}_{subject_key}_{s}"

def lesson_image_path(grade, subject_key, title):
    """Return the on-disk path if an illustration exists, else None."""
    import os as _os
    base = _os.path.join(LESSON_IMAGE_DIR,
                         lesson_image_slug(grade, subject_key, title))
    for ext in (".png", ".jpg", ".webp"):
        if _os.path.exists(base + ext):
            return base + ext
    return None


# --- Asli note ki photos (agar teacher ne rakhi hon) ---
# note_images/rs10.jpg, rs20.jpg, rs50.jpg, rs100.jpg, coins.jpg
# Agar yeh files maujood hon to app SVG ki jagah ASLI tasveer dikhata hai.
NOTE_IMAGE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "note_images")

def real_note_images():
    """Return [(label, filepath)] for any real note photos the teacher added."""
    import os as _os
    if not _os.path.isdir(NOTE_IMAGE_DIR):
        return []
    wanted = [("Sikkay", "coins"), ("Rs 10", "rs10"), ("Rs 20", "rs20"),
              ("Rs 50", "rs50"), ("Rs 100", "rs100")]
    out = []
    for label, stem in wanted:
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = _os.path.join(NOTE_IMAGE_DIR, stem + ext)
            if _os.path.exists(p):
                out.append((label, p)); break
    return out


# =====================================================================
#  PICTURE DESCRIBE KARO (G2 English) — ek scene jise dekh kar bola jaye
# =====================================================================
def svg_scene():
    w, h = 680, 400
    s = []
    s.append(f'<rect x="0" y="0" width="{w}" height="255" fill="#cfe9f7"/>')      # sky
    s.append(f'<rect x="0" y="255" width="{w}" height="105" fill="#9ed08a"/>')    # grass
    s.append(f'<circle cx="600" cy="60" r="38" fill="#ffd166"/>')                 # sun
    for cx, cy in ((120, 60), (300, 45)):                                          # clouds
        s.append(f'<ellipse cx="{cx}" cy="{cy}" rx="42" ry="22" fill="#ffffff"/>')
        s.append(f'<ellipse cx="{cx+30}" cy="{cy+6}" rx="30" ry="17" fill="#ffffff"/>')
    s.append(f'<text x="470" y="95" font-size="30">🐦</text>')                     # birds
    s.append(f'<text x="520" y="72" font-size="24">🐦</text>')
    s.append(f'<rect x="78" y="150" width="18" height="108" fill="#8b5a2b"/>')     # tree
    s.append(f'<circle cx="87" cy="140" r="52" fill="#4f9e4f"/>')
    s.append(f'<circle cx="55" cy="160" r="34" fill="#5cb85c"/>')
    s.append(f'<circle cx="120" cy="162" r="34" fill="#5cb85c"/>')
    s.append(f'<rect x="250" y="140" width="180" height="118" fill="#f2c14e" '     # shop
             f'stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<polygon points="238,140 442,140 340,96" fill="{C_RED}" stroke="{C_DARK}" stroke-width="3"/>')
    s.append(f'<rect x="315" y="192" width="52" height="66" fill="#8b5a2b" stroke="{C_DARK}" stroke-width="2"/>')
    s.append(f'<text x="340" y="132" text-anchor="middle" font-size="16" font-weight="800" fill="#fff">DUKAAN</text>')
    s.append(f'<text x="272" y="182" font-size="26">🍎</text>')                    # fruit
    s.append(f'<text x="392" y="182" font-size="26">🍌</text>')
    s.append(f'<text x="180" y="252" font-size="46">🧒</text>')                    # people
    s.append(f'<text x="470" y="252" font-size="46">👧</text>')
    s.append(f'<text x="545" y="255" font-size="42">🚲</text>')                    # bicycle
    s.append(f'<text x="210" y="300" font-size="30">🌸</text>')
    s.append(f'<text x="600" y="305" font-size="30">🌼</text>')
    s.append(f'<text x="20" y="386" font-size="16" font-weight="800" fill="{C_DARK}">'
             f'Batao: Tasveer mein kya kya hai? Kitne bachay hain? Sooraj kahan hai?</text>')
    return _wrap("".join(s), w, h, "Tasveer dekho aur batao — picture describe karo")


# =====================================================================
#  TOPIC -> VISUAL MAPPING
# =====================================================================
def get_topic_visual(subject_key, grade, topic_title):
    """Return an SVG string for this topic, ya None agar koi visual na ho.
    Keyword-based taake KB titles badalne par bhi kaam kare."""
    t = (topic_title or "").lower()
    try:
        g = int(grade)
    except (TypeError, ValueError):
        g = 3

    # --- Topics that CANNOT be taught without a picture ---
    if "paisa" in t or "paise" in t or "money" in t or "currency" in t or "sikka" in t:
        return svg_money()
    if "picture" in t or "tasveer" in t:
        return svg_scene()

    # --- Math ---
    if "fraction" in t or "kasr" in t or "kasoor" in t:
        return svg_fraction_set()
    if "ashkaal" in t or "shape" in t or "geometry" in t:
        return svg_shapes()
    if "ghadi" in t or "clock" in t:
        return svg_clock(3, 0)
    if "jama" in t or "addition" in t:
        return svg_addition(3, 2)
    if "minus" in t or "subtraction" in t or "manfi" in t:
        return svg_subtraction(5, 2)
    if "ginti" in t or "counting" in t:
        return svg_counting(5, "🥭", "Aam gino") + svg_number_line(0, 10, 5)
    if "number" in t and g <= 2:
        return svg_number_line(0, 10, 5)

    # --- Science / Robotics ---
    if "circuit" in t or "bijli" in t or "battery" in t or "switch" in t:
        return svg_circuit(True)
    if "solid" in t or "liquid" in t or "gas" in t or "matter" in t or "maddah" in t:
        return svg_states()
    return None


VISUAL_TOPICS_HINT = (
    "Fractions, Ashkaal/Shapes, Ghadi, Ginti, Jama, Minus, Circuits, "
    "Solid-Liquid-Gas — in topics par tasveer khud ban jati hai (Rs 0)."
)
