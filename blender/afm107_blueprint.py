"""python afm107_blueprint.py : the AF M107A1's working blueprint (side and top view), as SVG and PNG.

All sizes in millimetres. x runs from the butt (0) forward; z is up from the bore axis.

Rev 3 (2026-11-23) is measured off the owner's reference picture (a side view of a 3D model, kept in
docs/img/m107_reference.webp; used for proportions only, nothing from it is copied into the mod).
That picture is close to a straight side view; its scale works out at about 1 px = 1 mm (the
manual's 1443 mm overall length puts the muzzle brake's end where the suppressor in the picture
covers it). Picture pixel (px, py) -> x = px - 25, z = 478 - py.
Widths (top view) are not in the picture and are estimates.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs", "img")
OUT = os.path.join(DOCS, "m107_blueprint.svg")
PNG = os.path.join(DOCS, "m107_blueprint.png")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

OVERALL = 1523.0                      # rev 4: the manual's 1443 plus 80 in the middle (owner)

# --- Parts, side view (mm). Polygons are (x, z) lists; boxes are (x0, x1, z0, z1). --------------
PARTS = {
    # Upper receiver: one long body from the butt to the nose; the front section is the handguard.
    "upper": [(15, 35), (250, 35), (262, 48), (560, 48), (560, -38), (515, -47), (475, -47), (475, -42), (15, -42)],   # bottom blends into the handguard
    # Handguard (owner): thinner than the receiver and squared off at the front, not tapering like a cone.
    "handguard": [(560, 48), (884, 48), (890, 42), (890, -32), (884, -38), (560, -38)],
    "rail": (265, 890, 48, 61),                      # M1913 rail on its 27 MOA base
    "cheek": [(70, 36), (205, 36), (220, 22), (220, 3), (85, 3), (70, 14)],    # ribbed cheek plate
    "window": (250, 475, -14, 21),                   # bolt carrier seen through the receiver
    "rear_sight": (55, 100, 35, 44),
    "butt": [(0, 31), (28, 34), (40, 22), (40, -125), (30, -137), (0, -137), (-6, -100), (-6, 0)],
    "stock_post": (40, 95, -137, -42),               # the stock's rear upright, carrying the monopod
    "rear_grip": [(95, -47), (180, -47), (180, -137), (95, -137)],   # open loop: the rear grip
    "rear_grip_hole": [(108, -57), (168, -57), (168, -112), (150, -122), (108, -122)],
    "lower": [(95, -42), (330, -42), (330, -94), (215, -94), (192, -62), (95, -62)],   # lower receiver and trigger housing
    "shroud": [(325, -27), (495, -27), (495, -82), (345, -122), (325, -60)],   # angled magazine-well plate
    "mag": (337, 483, -232, -82),                    # magazine: fits inside the well plate (owner), its top inside
    "grip": [(238, -90), (325, -90), (300, -205), (285, -217), (250, -217), (243, -205)],
    "trigger": [(296, -88), (318, -88), (312, -120), (300, -132)],
    "barrel_collar": (860, 905, -23, 23),
    "barrel": [(905, 11), (1338, 10), (1338, -10), (905, -11)],     # fluted
    "brake": (1338, 1443, -28, 28),
    "bipod_yoke": (685, 775, -60, -38),
}
# Rev 4 (owner): the middle of the body, from the rear grip to the handguard holes, 80 mm longer, and
# the rifle grows by as much (owner: "grow the rifle longer"): overall 1523, barrel and brake unchanged.
STRETCH = (180.0, 575.0, 80.0)          # x0, x1 of the stretched section, and the added length


def fx(x):
    x0, x1, d = STRETCH
    if x <= x0:
        return x
    if x <= x1:
        return x0 + (x - x0) * (x1 - x0 + d) / (x1 - x0)
    return x + d


def _stretch(v):
    if isinstance(v, tuple):
        x0, x1, z0, z1 = v
        return (fx(x0), fx(x1), z0, z1)
    return [(fx(x), z) for x, z in v]


def _move(v, anchor):
    d = fx(anchor) - anchor
    if isinstance(v, tuple):
        x0, x1, z0, z1 = v
        return (x0 + d, x1 + d, z0, z1)
    return [(x + d, z) for x, z in v]


# Parts inside the stretched section keep their size and move with it; only the body grows.
RIGID = {"grip": 282.0, "trigger": 282.0, "shroud": 425.0, "mag": 425.0}
PARTS = {k: (_move(v, RIGID[k]) if k in RIGID else _stretch(v)) for k, v in PARTS.items()}
HOLES_X = [fx(572 + 33 * k) for k in range(8)]          # handguard lightening holes, two rows
HOLE_ROWS = (21.0, -21.0)
MID_PIN = (fx(587.0), -59.0, 20.0)                  # ring hangs from a pin through the receiver's bottom                       # mid lock pin ring: x, z, radius
REAR_PIN = (fx(540.0), -50.0, 9.0)                       # small lever with its ring ahead of the shroud
MAG_RIBS = [x + fx(425.0) - 425.0 for x in (362, 386, 410, 434, 458)]                 # vertical ribs along the magazine's side

# --- Top view widths (estimates) -----------------------------------------------------------------
HALF = {"upper": 38.0, "handguard": 32.0, "rail": 10.6, "stock": 25.0, "mag": 32.0, "brake": 28.0, "barrel": 11.0, "collar": 23.0}

LABELS = [
    (140, 80, "cheek plate"), (575, 80, "M1913 rail, 705"), (360, 32, "receiver window / bolt carrier"),
    (690, 36, "handguard: 2 x 8 lightening holes"), (1120, 24, "fluted barrel, dia 22"),
    (1390, 40, "brake, dia 56"), (410, -250, "magazine 146 wide"), (410, -100, "mag-well plate"),
    (255, -235, "pistol grip"), (138, -152, "rear grip"), (10, 50, "butt"),
    (600, -125, "mid lock pin"), (78, 62, "rear sight"),
]
LABELS = [(fx(x), z, s) for x, z, s in LABELS]

S = 0.62
PAD = 70.0


def X(x):
    return PAD + x * S


def Z(z, base):
    return base - z * S


def poly(pts, base, cls="part"):
    return '<polygon class="%s" points="%s"/>' % (cls, " ".join("%.1f,%.1f" % (X(x), Z(z, base)) for x, z in pts))


def box(b, base, cls="part", rx=0.0):
    x0, x1, z0, z1 = b
    return '<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/>' % (
        cls, X(x0), Z(max(z0, z1), base), (x1 - x0) * S, abs(z1 - z0) * S, rx)


def text(x, z, base, s, cls="lab"):
    return '<text class="%s" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (cls, X(x), Z(z, base), s)


def dim_x(x0, x1, z, base, label):
    y = Z(z, base)
    return ('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" marker-start="url(#a)" marker-end="url(#a)"/>'
            '<text class="dimt" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (X(x0), y, X(x1), y, (X(x0) + X(x1)) / 2, y - 5, label))


def dim_z(x, z0, z1, base, label, right=True):
    return ('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" marker-start="url(#a)" marker-end="url(#a)"/>'
            '<text class="dimt" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (
                X(x), Z(z0, base), X(x), Z(z1, base), X(x) + (6 if right else -6), (Z(z0, base) + Z(z1, base)) / 2 + 4,
                "start" if right else "end", label))


def side(base):
    P = PARTS
    e = [poly(P["butt"], base, "rubber"), box(P["stock_post"], base), poly(P["rear_grip"], base, "soft"),
         poly(P["rear_grip_hole"], base, "bg"), poly(P["lower"], base), poly(P["upper"], base), poly(P["handguard"], base),
         box(P["window"], base, "hole"), poly(P["cheek"], base, "soft"), box(P["rail"], base, "rail"),
         box(P["rear_sight"], base), box(P["barrel_collar"], base, "part", 6), poly(P["barrel"], base),
         box(P["brake"], base, "part", 5), box(P["mag"], base), poly(P["shroud"], base), poly(P["grip"], base, "soft"),
         poly(P["trigger"], base, "fine"), box(P["bipod_yoke"], base)]
    for x in range(int(P["rail"][0]) + 6, int(P["rail"][1]) - 4, 10):
        e.append('<line class="fine" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(x), Z(61, base), X(x), Z(56, base)))
    for z in HOLE_ROWS:
        for x in HOLES_X:
            e.append(poly([(x - 10, z), (x - 4, z + 6), (x + 10, z + 6), (x + 4, z - 6), (x - 4, z - 6)], base, "hole"))
    for x in MAG_RIBS:
        e.append('<line class="fine" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(x), Z(-122, base), X(x), Z(-228, base)))
    for z in (3, -3):                                                  # barrel flutes
        e.append('<line class="fine" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(fx(910)), Z(z, base), X(fx(1330)), Z(z, base)))
    for k in range(2):                                                 # brake: two port chambers
        x = fx(1352 + 38 * k)
        e.append(box((x, x + 26, -18, 18), base, "hole", 4))
    for x, z, r in (MID_PIN, REAR_PIN):
        e.append('<circle class="fine" cx="%.1f" cy="%.1f" r="%.1f"/>' % (X(x), Z(z, base), r * S))
    e.append('<line class="axis" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(-10), Z(0, base), X(OVERALL + 10), Z(0, base)))
    for x, z, s in LABELS:
        e.append(text(x, z, base, s))
    e.append(dim_x(0, OVERALL, 120, base, "1523 overall (manual 1443 + 80)"))
    e.append(dim_x(15, fx(890), 96, base, "receiver 955"))
    e.append(dim_x(fx(890), fx(1338), -95, base, "exposed barrel 448"))
    e.append(dim_x(fx(1338), fx(1443), -45, base, "brake 105"))
    e.append(dim_z(-30, -137, 34, base, "butt 171", right=False))
    e.append(dim_z(fx(655), -232, 61, base, "293 rail to magazine"))
    e.append(dim_x(180, fx(575), -285, base, "middle body 475 (was 395)"))
    e.append(dim_z(fx(900), -38, 48, base, "86"))
    return e


def top(base):
    H = HALF
    e = [box((15, fx(560), -H["upper"], H["upper"]), base, "part", 4),
         box((fx(560), fx(890), -H["handguard"], H["handguard"]), base, "part", 3),
         box((-6, 40, -H["stock"], H["stock"]), base, "rubber", 4),
         box((40, 180, -H["stock"], H["stock"]), base, "soft", 3),
         box((fx(265), fx(890), -H["rail"], H["rail"]), base, "rail"),
         box((fx(860), fx(905), -H["collar"], H["collar"]), base, "part", 6),
         box((fx(905), fx(1338), -H["barrel"], H["barrel"]), base),
         box((fx(1338), fx(1443), -H["brake"], H["brake"]), base, "part", 5)]
    e.append('<line class="axis" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(-10), Z(0, base), X(OVERALL + 10), Z(0, base)))
    e.append(dim_z(-30, -H["upper"], H["upper"], base, "76 est.", right=False))
    e.append(dim_z(fx(1455), -H["brake"], H["brake"], base, "56"))
    e.append(text(fx(600), 18, base, "rail 21.2 wide (M1913)"))
    return e


def main():
    w = int(X(OVERALL) + PAD + 60)
    side_base, top_base = 250.0, 590.0
    h = int(top_base + 80)
    css = """
    .part{fill:#3a3d40;stroke:#c9d1d9;stroke-width:1.1}
    .soft{fill:#2f3336;stroke:#8fbf8f;stroke-width:1.1}
    .rubber{fill:#1f2224;stroke:#8f8f8f;stroke-width:1.1}
    .rail{fill:#4a4e52;stroke:#e0e6ec;stroke-width:1}
    .hole{fill:#101214;stroke:#c9d1d9;stroke-width:.8}
    .bg{fill:#0d1117;stroke:#8fbf8f;stroke-width:1}
    .fine{fill:none;stroke:#c9d1d9;stroke-width:.9}
    .axis{stroke:#e0a040;stroke-width:.8;stroke-dasharray:8 4}
    .dim{stroke:#58a6ff;stroke-width:1}
    .dimt{fill:#58a6ff;font:12px sans-serif}
    .lab{fill:#d0d7de;font:11px sans-serif}
    .ttl{fill:#f0f6fc;font:bold 18px sans-serif}
    .sub{fill:#8b949e;font:12px sans-serif}
    """
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h),
             '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse">'
             '<path d="M0,0 L8,4 L0,8 z" fill="#58a6ff"/></marker><style>%s</style></defs>' % css,
             '<rect width="100%" height="100%" fill="#0d1117"/>',
             '<text class="ttl" x="%d" y="30">AF M107A1 - working blueprint, rev 4 (mm): measured off the reference, middle body +80</text>' % PAD,
             '<text class="sub" x="%d" y="48">Side view measured from the owner&#39;s reference picture at 1 px = 1 mm (manual: 1443 overall); middle body lengthened 80 mm (owner). Top-view widths are estimates.</text>' % PAD,
             '<text class="sub" x="%d" y="%d">SIDE (right)</text>' % (PAD, side_base - 110),
             '<text class="sub" x="%d" y="%d">TOP</text>' % (PAD, top_base - 55)]
    parts += side(side_base) + top(top_base)
    parts.append("</svg>")
    os.makedirs(DOCS, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(parts))
    if os.path.exists(EDGE):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--screenshot=" + PNG, "--window-size=%d,%d" % (w, h),
                        "file:///" + OUT.replace("\\", "/")], capture_output=True)
    print("BLUEPRINT", OUT)


if __name__ == "__main__":
    main()
