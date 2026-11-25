"""Worn metal finish for any AF weapon: the StG 44's tested finish layers (afstg44_detailed._phosphate,
checked in game in four lights), with the colours of the coating as a setting so the same method fits
Cerakote, anodising and blued steel (owner 2026-11-24: "add the StG 44's method to all the weapons").

  worn(mat, muzzle_y, zones, palette="phosphate", sheets=(), axis=1)

- mat: a material made by af7_vanguard_detailed.material() (create it with wear=0 and scratches=0:
  these layers replace that older edge wear).
- muzzle_y: where the muzzle is along the weapon (soot); a large number for parts without one.
- zones: ((centre xyz, half sizes xyz, strength 0..1), ...) where hands, kit and slings work the
  finish, in the weapon's own working frame: polish, use scratches and more edge wear there.
- palette: one of PALETTES, the colours the layers mix towards.
- sheets: pressed-detail height sheets, as afstg44_detailed._phosphate takes them.

Layers, as on the StG 44: cloudy mottling and oily patches; gloss breakup and rag wipes (flat, even
gloss is what makes a surface look computer-made in sunlight); grime, rust specks and dust in the
corners; edge wear rubbed thin and, on the sharpest and most exposed edges, through to bare steel
(told by its shine, not by a white line); polish and directional scratches in the handled zones; a
few long faint scratches anywhere; soot at the muzzle.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import afm41_pathfinder_detailed as m41  # noqa: E402
import afstg44_detailed as stg  # noqa: E402

# Colours each layer mixes towards. light / dark / oil: the mottling; soft: an edge rubbed thin;
# top: a handled, wiped flat; bare: steel showing through.
PALETTES = {
    "phosphate": dict(light=(0.040, 0.041, 0.037), dark=(0.0080, 0.0085, 0.0090), oil=(0.0070, 0.0075, 0.0080),
                      soft=(0.070, 0.069, 0.066), top=(0.034, 0.034, 0.033), bare=(0.22, 0.22, 0.225)),
    # Black hard anodising on aluminium (the AF-7's receivers): neutral, a touch cool; worn edges go
    # to bright grey aluminium.
    "anodized": dict(light=(0.036, 0.037, 0.040), dark=(0.0085, 0.0088, 0.0095), oil=(0.0075, 0.0078, 0.0085),
                     soft=(0.075, 0.076, 0.080), top=(0.036, 0.037, 0.040), bare=(0.30, 0.30, 0.31)),
    # Bluing (rust or hot salt blue): blue-black, plum-brown where it has thinned.
    "blued": dict(light=(0.030, 0.032, 0.040), dark=(0.0060, 0.0065, 0.0085), oil=(0.0060, 0.0062, 0.0075),
                  soft=(0.060, 0.052, 0.050), top=(0.032, 0.033, 0.040), bare=(0.24, 0.24, 0.245)),
    # Dark Parkerized / black oxide small parts.
    "oxide": dict(light=(0.034, 0.034, 0.034), dark=(0.0070, 0.0070, 0.0072), oil=(0.0065, 0.0065, 0.0068),
                  soft=(0.068, 0.068, 0.068), top=(0.032, 0.032, 0.032), bare=(0.24, 0.24, 0.245)),
}
DUST = (0.060, 0.052, 0.042)
GRIME = (0.022, 0.017, 0.012)


def worn(mat, muzzle_y, zones=(), palette="phosphate", sheets=(), axis=1):
    # The finish code finds the material's taps (<prefix>COLOR, ...) by the prefix of the model that
    # made it: read it off the material.
    tap = next(n.name for n in mat.node_tree.nodes if n.name.endswith("COLOR") and n.type == "REROUTE")
    old_prefix, m41.PREFIX = m41.PREFIX, tap[:-len("COLOR")]
    try:
        return _worn(mat, muzzle_y, zones, palette, sheets, axis)
    finally:
        m41.PREFIX = old_prefix


def _worn(mat, muzzle_y, zones, palette, sheets, axis):
    C = PALETTES[palette]
    P = m41._Post(mat)
    N = P.N
    pos = (P.px, P.py, P.pz)[axis]           # the weapon's long axis (soot at the muzzle)
    # 1. Mottled finish and oily patches; gloss breakup and rag wipes.
    cloud = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(7.0, 4.0), 0.42), 2.6, clamp=True)
    P.color(N.math("MULTIPLY", cloud, 0.85), C["light"])
    blot = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(32.0, 3.0), 0.56), 4.0, clamp=True)
    P.color(N.math("MULTIPLY", blot, 0.70), C["dark"])
    oily = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(9.0, 2.0), 0.50), 5.0, clamp=True)
    P.color(N.math("MULTIPLY", oily, 0.55), C["oil"])
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", cloud, 0.5), 0.10))
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", P.noise(11.0, 3.0), 0.5), 0.85))
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", stg._wipe(P, axis, 55.0), 0.5), 0.42))
    # 2. Grime, rust specks and dust in the corners.
    cav = stg._cavity(P, 0.010)
    grime = N.math("MULTIPLY", cav, N.math("ADD", 0.55, N.math("MULTIPLY", P.noise(60.0, 3.0), 0.6)), clamp=True)
    P.color(N.math("MULTIPLY", grime, 0.70), GRIME)
    P.rough(N.math("MULTIPLY", grime, 0.14))
    rust = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.12, P.cells(380.0)), 18.0, clamp=True), cav)
    P.color(N.math("MULTIPLY", rust, 0.85), (0.095, 0.040, 0.016))
    P.rough(N.math("MULTIPLY", rust, 0.25))
    P.dent(N.math("MULTIPLY", rust, -1.0), 0.00010)
    dusty = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(19.0, 4.0), 0.48), 4.0, clamp=True)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", cav, dusty), 0.22), DUST)
    chip = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(48.0, 6.0), 0.40), 3.5, clamp=True)
    # Exposure: a broad noise picks worn stretches; the handled zones and the muzzle always are.
    gt = lambda a, b: N.math("GREATER_THAN", a, b)
    exposed = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(5.0, 2.0), 0.36), 3.2, clamp=True)
    exposed = N.math("MAXIMUM", exposed, gt(pos, muzzle_y - 0.050))
    handled = None
    for centre, half, k in zones:
        z = N.math("MULTIPLY", stg._spot(P, centre, tuple(h * 0.6 for h in half)), k)
        handled = z if handled is None else N.math("MAXIMUM", handled, z)
    if handled is not None:
        exposed = N.math("MAXIMUM", exposed, handled)
    # 2b. Pressed detail: dirt in the pressings, finish rubbed off their rims.
    holes = []
    for img, side, window, x_min in sheets:
        dirt, rub, hole = stg._sheet(P, img, side, window, x_min)
        P.color(N.math("MULTIPLY", dirt, 0.60), GRIME)
        P.color(N.math("MULTIPLY", N.math("MULTIPLY", dirt, dusty), 0.30), DUST)
        P.rough(N.math("MULTIPLY", dirt, 0.14))
        P.color(N.math("MULTIPLY", N.math("MULTIPLY", rub, chip), 0.55), C["soft"])
        w = N.math("MULTIPLY", N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", rub, 0.35), 2.2, clamp=True), chip),
                   N.math("ADD", 0.25, N.math("MULTIPLY", exposed, 0.75)))
        P.color(N.math("MULTIPLY", w, 0.8), C["bare"])
        P.rough(N.math("MULTIPLY", w, -0.25))
        stg._set_metal(P, w, 1.0)
        holes.append(hole)
    # 3. Edge wear: rubbed thin round the edges, through to bare steel on the sharpest, broken up.
    flake = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(48.0, 6.0), 0.30), 3.0, clamp=True)
    soft = N.math("MULTIPLY", N.math("MULTIPLY", stg._edge(P, 0.0024, 4.0), flake),
                  N.math("ADD", 0.45, N.math("MULTIPLY", exposed, 0.55)))
    P.color(N.math("MULTIPLY", soft, 0.70), C["soft"])
    P.rough(N.math("MULTIPLY", soft, -0.10))
    bare = N.math("MULTIPLY", N.math("MULTIPLY", N.math("MULTIPLY", stg._edge(P, 0.0012, 9.0), flake), 1.0, clamp=True),
                  N.math("ADD", 0.25, N.math("MULTIPLY", exposed, 0.75)))
    P.color(bare, C["bare"])
    P.rough(N.math("MULTIPLY", bare, -0.30))
    stg._set_metal(P, bare, 1.0)
    if handled is not None:
        # 4. Use wear in the handled zones: polished thin, scratches the way the hand moves.
        patchy = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(26.0, 5.0), 0.30), 2.5, clamp=True)
        polish = N.math("MULTIPLY", N.math("MULTIPLY", handled, patchy), stg._edge(P, 0.0040, 2.5))
        P.color(N.math("MULTIPLY", polish, 0.25), C["top"])
        P.rough(N.math("MULTIPLY", polish, -0.22))
        used = N.math("MULTIPLY", N.math("MAXIMUM", stg._streaks(P, 1, 120.0, 0.76), stg._streaks(P, 2, 130.0, 0.78)),
                      N.math("MULTIPLY", handled, handled))
        P.color(N.math("MULTIPLY", used, 0.30), C["bare"])
        P.rough(N.math("MULTIPLY", used, -0.20))
        stg._set_metal(P, N.math("MULTIPLY", used, 0.8), 1.0)
        P.dent(N.math("MULTIPLY", used, -0.8), 0.00005)
    # 5. Long faint scratches anywhere, soot at the muzzle.
    P.color(N.math("MULTIPLY", stg._streaks(P, 1, 90.0, 0.78), 0.35), (0.10, 0.10, 0.104))
    soot = N.math("MULTIPLY", P.band(pos, muzzle_y, 0.030), 0.75)
    P.color(soot, (0.007, 0.0065, 0.006))
    P.rough(N.math("MULTIPLY", soot, 0.12))
    for hole in holes:
        P.color(hole, (0.002, 0.002, 0.002))
        P.rough(N.math("MULTIPLY", hole, 0.40))
        stg._set_metal(P, hole, 0.0)
    return P


def pro_export(g, soft_set_base=None):
    """The StG 44's export settings (afstg44_dayz_export._gun_tables, checked in game), set in the
    globals `g` of af7_vanguard_dayz_export as a weapon's export uses them:
    - normal and ambient maps baked from a finer rebuild (twice the sides on round parts, edges
      rounded in up to six steps, fillets every 7.5 degrees), 64 rays per texel;
    - specular that follows the gloss and darkens in corners, bare steel that shines, steel at the
      level settled against vanilla guns; texture edges padded against dark seams at range;
    - normals weighted by flat-panel area, so flat sides with holes in them shade flat.
    soft_set_base: {texture set: specular base} for furniture sets (wood, polymer)."""
    g["HIGH_DETAIL"] = ("high", 4.0, 6, 7.5, True)
    g["HIGH_EDGE_STEPS"] = ((0.0010, 6), (0.0005, 4), (0.0002, 2))
    g["HIGH_CAGE"], g["HIGH_RAY"] = 0.0008, 0.0016
    g["SAMPLES"] = dict(g["SAMPLES"], NORMAL=64)
    g["SPEC_VAR"], g["SPEC_CAVITY"], g["SPEC_SET_BASE"] = 0.60, 0.35, dict(soft_set_base or {})
    g["SPEC_BASE"], g["SPEC_METAL"], g["GLOSS_SCALE"], g["CO_SCALE"] = 0.06, 0.18, 0.88, 0.90
    g["SPEC_WORN"], g["AO_FLOOR"] = 0.30, 0.30
    g["EDGE_PAD"] = True
    g["REGION_WEIGHTS"] = True
