"""Clean-topology builders for the AF weapons (owner 2026-11-24: "hand made clean topology").

The first models were extruded side profiles (one large n-gon per side) with openings cut by Boolean
modifiers. After the cuts the M107A1 had 998 n-gons and 5,977 sliver triangles, 2,432 of them on the
handguard alone. These builders lay the topology out by hand instead: every face a quad, grid lines
placed on the edges of every opening, so an opening is whole cells left out with four straight walls,
and round caps closed with a quad grid rather than a triangle fan. The bevel modifier then rounds the
openings' edges cleanly (af7_vanguard_detailed.make weights every edge sharper than 30 degrees).

  coons_cap(bm, ring)            close a ring of 4k vertices with a k x k quad grid
  lathe(bm, prof, sides, ...)    af7_vanguard_detailed.bm_lathe with quad caps (sides a multiple of 4)
  slotted_tube(bm, ...)          a hollow tube with slanted slots through its wall (the M107A1 handguard)
"""
import math

import bmesh


def coons_cap(bm, ring, flip=False, apex=None):
    """Fill a closed ring of 4k vertices (in order) with a k x k grid of quads. The interior points are a
    Coons patch of the four sides, so the grid follows the ring's shape (round, oval or square)."""
    n = len(ring)
    assert n % 4 == 0 and n >= 4, n
    k = n // 4
    # The ring walks the square's boundary: bottom (i, 0) left to right, right (k, j) up, top (i, k)
    # right to left, left (0, j) down.
    grid = {}
    for t in range(k):
        grid[(t, 0)] = ring[t]
        grid[(k, t)] = ring[k + t]
        grid[(k - t, k)] = ring[2 * k + t]
        grid[(0, k - t)] = ring[3 * k + t]
    P = lambda i, j: grid[(i, j)].co
    centre = sum((v.co for v in ring), ring[0].co * 0.0) / n
    lift = (apex - centre) if apex is not None else None     # a pointed or domed end: raise the middle
    for i in range(1, k):
        for j in range(1, k):
            u, v = i / k, j / k
            c = ((1 - v) * P(i, 0) + v * P(i, k) + (1 - u) * P(0, j) + u * P(k, j)
                 - ((1 - u) * (1 - v) * P(0, 0) + u * (1 - v) * P(k, 0) + (1 - u) * v * P(0, k) + u * v * P(k, k)))
            if lift is not None:
                c = c + lift * (1.0 - 2.0 * max(abs(u - 0.5), abs(v - 0.5)))
            grid[(i, j)] = bm.verts.new(c)
    faces = []
    for i in range(k):
        for j in range(k):
            q = [grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]]
            faces.append(bm.faces.new(q[::-1] if flip else q))
    return faces


def lathe(bm, prof, sides=32, axis="Y", c=(0.0, 0.0), closed=False, smooth=True, flat_ends=False):
    """Revolve [(pos, radius), ...]. A radius of 0 at either end is closed with a quad cap (not a
    fan); with flat_ends, an end ring that is not at radius 0 is closed flat with a quad cap too. sides
    is rounded up to a multiple of 4."""
    sides = max(8, 4 * math.ceil(sides / 4))

    def P(pos, r, t):
        a, b = r * math.cos(t), r * math.sin(t)
        if axis == "Y":
            return (c[0] + a, pos, c[1] + b)
        if axis == "X":
            return (pos, c[0] + a, c[1] + b)
        return (c[0] + a, c[1] + b, pos)
    ang = [2 * math.pi * (i + 0.5) / sides for i in range(sides)]
    pts = [(p, r) for p, r in prof]
    cap0 = pts and pts[0][1] <= 1e-7
    cap1 = pts and pts[-1][1] <= 1e-7
    from mathutils import Vector
    apex0 = Vector(P(pts[0][0], 0.0, 0.0)) if cap0 and abs(pts[0][0] - pts[1][0]) > 1e-7 else None
    apex1 = Vector(P(pts[-1][0], 0.0, 0.0)) if cap1 and abs(pts[-1][0] - pts[-2][0]) > 1e-7 else None
    if cap0:
        pts = pts[1:]
    if cap1:
        pts = pts[:-1]
    rings = [[bm.verts.new(P(p, r, t)) for t in ang] for p, r in pts]
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for A, B in pairs:
        for i in range(sides):
            j = (i + 1) % sides
            f = bm.faces.new((A[i], A[j], B[j], B[i]))
            f.smooth = smooth
    if not closed and (cap0 or flat_ends):
        coons_cap(bm, rings[0], apex=apex0)
    if not closed and (cap1 or flat_ends):
        coons_cap(bm, rings[-1], flip=True, apex=apex1)
    return rings


def _angles(fixed, step):
    """Angles (degrees, 0..360) through every fixed one, no gap wider than `step`."""
    fixed = sorted(set(round(a % 360.0, 6) for a in fixed))
    out = []
    for a, b in zip(fixed, fixed[1:] + [fixed[0] + 360.0]):
        n = max(1, math.ceil((b - a) / step - 1e-9))
        out += [a + (b - a) * s / n for s in range(n)]
    return [math.radians(a) for a in out]


def slotted_tube(bm, y0, slots, r_out, r_in, front, c=(0.0, 0.0), step=8.0, gap=0.017):
    """A hollow tube along +Y from y0 (metres), walls r_out / r_in, with slanted slots through the wall
    on both flanks. Every face is a quad.
    slots: [(y_left, y_right, z_low, z_high, shift), ...]: a slot spans z_low..z_high (metres from the
      axis, the same on the left and right flank); its left and right edges are at y_left / y_right at
      z_low and moved by `shift` along Y at z_high (a parallelogram, as on the M107A1).
    front: (y_face, r_face, r_hole, depth): the outer wall chamfers down to r_face at y_face, the front
      face closes to the bore r_hole, the bore runs `depth` back and steps out to the inner wall.
    Rows (angles) pass through the top and bottom of every slot band; columns (lines along the tube) run
    through every slot edge, slanted inside the bands, so each opening is whole cells left out."""
    cx, cz = c
    bands = sorted(set((s[2], s[3]) for s in slots))
    fixed = [0.0, 90.0, 180.0, 270.0]
    for zl, zh in bands:
        for z in (zl, zh):
            a = math.degrees(math.asin(max(-1.0, min(1.0, z / r_out))))
            fixed += [a, 180.0 - a]
    ang = _angles(fixed, step)
    zs = [r_out * math.sin(t) for t in ang]
    n = len(ang)

    def slanted(yb, shift):
        knots = []
        for zl, zh in bands:
            knots += [(zl, yb), (zh, yb + shift)]

        def y_at(z):
            if z <= knots[0][0]:
                return knots[0][1]
            for (za, ya), (zb, yb2) in zip(knots, knots[1:]):
                if z <= zb:
                    return ya + (yb2 - ya) * (z - za) / max(zb - za, 1e-9)
            return knots[-1][1]
        return y_at
    edges = sorted(set((round(sl[k], 6), sl[4]) for sl in slots for k in (0, 1)))
    cols = [(y0, lambda z, v=y0: v)]
    for yb, shift in edges:
        prev = cols[-1][0]
        if yb - prev > gap * 1.5:                        # a plain line between distant slot edges
            mid = (prev + yb) / 2
            cols.append((mid, lambda z, v=mid: v))
        cols.append((yb, slanted(yb, shift)))
    yf, rf, rh, depth = front
    yo_end, yi_end = yf - (r_out - rf), yf - depth
    last = cols[-1][0] + max(sl[4] for sl in slots)
    while yi_end - last > 2 * gap:
        last += gap
        cols.append((last, lambda z, v=last: v))

    def ring(y_fn, r):
        return [bm.verts.new((cx + r * math.cos(t), y_fn(z), cz + r * math.sin(t))) for t, z in zip(ang, zs)]
    outer = [ring(f, r_out) for _, f in cols] + [ring(lambda z: yo_end, r_out)]
    inner = [ring(f, r_in) for _, f in cols] + [ring(lambda z: yi_end, r_in)]
    holes = set()
    for yl, yr, zl, zh, shift in slots:
        ci = min(range(len(cols)), key=lambda k: abs(cols[k][0] - round(yl, 6)))
        cj = min(range(len(cols)), key=lambda k: abs(cols[k][0] - round(yr, 6)))
        for i in range(n):
            zm = (zs[i] + zs[(i + 1) % n]) / 2
            if zl < zm < zh:
                for k in range(ci, cj):
                    holes.add((k, i))
    for surf in (outer, inner):
        for k in range(len(surf) - 1):
            for i in range(n):
                if (k, i) not in holes:
                    j = (i + 1) % n
                    bm.faces.new((surf[k][i], surf[k][j], surf[k + 1][j], surf[k + 1][i]))
    for (k, i) in holes:
        j = (i + 1) % n
        for (a, b), nb in ((((k, i), (k, j)), (k - 1, i)), (((k + 1, i), (k + 1, j)), (k + 1, i)),
                           (((k, i), (k + 1, i)), (k, (i - 1) % n)), (((k, j), (k + 1, j)), (k, j))):
            if nb not in holes:
                bm.faces.new((outer[a[0]][a[1]], outer[b[0]][b[1]], inner[b[0]][b[1]], inner[a[0]][a[1]]))
    for i in range(n):                                  # rear end: the annulus between the walls
        j = (i + 1) % n
        bm.faces.new((inner[0][i], inner[0][j], outer[0][j], outer[0][i]))
    chamf, face_in = ring(lambda z: yf, rf), ring(lambda z: yf, rh)
    if abs(rh - r_in) < 1e-6:                          # the bore is the inner wall: it runs straight on
        seq = ((outer[-1], chamf), (chamf, face_in), (face_in, inner[-1]))
    else:
        bore_back = ring(lambda z: yi_end, rh)
        seq = ((outer[-1], chamf), (chamf, face_in), (face_in, bore_back), (bore_back, inner[-1]))
    for R0, R1 in seq:
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((R0[i], R0[j], R1[j], R1[i]))
    return outer, inner


# --- Openings and pockets by loop cuts ----------------------------------------------------------------
# A modeller cuts an opening by running edge loops through its edges, then removing or pushing in the
# cells between them. These do the same on a bmesh, so the result is quads with straight walls instead
# of the scraps a Boolean leaves.

AX = {"X": 0, "Y": 1, "Z": 2}


def loop_cuts(bm, axis, values):
    """Edge loops right round the mesh at axis = each value (a bisect of every face it crosses)."""
    from mathutils import Vector
    k = AX[axis]
    no = Vector((0.0, 0.0, 0.0))
    no[k] = 1.0
    for v in values:
        co = Vector((0.0, 0.0, 0.0))
        co[k] = v
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no)


MIN_DOT = 0.99      # how square to the axis a face must be to count as facing it (a curved top: lower)


def _cells(bm, axis, sign, rect):
    """Faces facing `sign` along `axis`, on the outermost layer that way, inside rect (a0, a1, b0, b1
    on the other two axes in order)."""
    k = AX[axis]
    o = [i for i in range(3) if i != k]
    a0, a1, b0, b1 = rect
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])     # outward, whatever order the faces were made in
    bm.normal_update()
    out = []
    for f in bm.faces:
        if f.normal[k] * sign < MIN_DOT:
            continue
        c = f.calc_center_median()
        if a0 < c[o[0]] < a1 and b0 < c[o[1]] < b1:
            out.append(f)
    if out:                                   # keep only the outermost layer (the visible face)
        top = max(f.calc_center_median()[k] * sign for f in out)
        out = [f for f in out if f.calc_center_median()[k] * sign > top - 1e-5]
    return out


def _weigh(bm, edges, w):
    """Bevel weight for the rims of an opening (a fraction of the part's bevel width)."""
    if w is None:
        return
    layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    for e in edges:
        if e.is_valid:
            e[layer] = w


def pocket(bm, axis, sign, rects, depth, weight=None, vec=None):
    """Push the cells inside each rect in by `depth`: walls round each, its floor the same cells.
    Run loop_cuts through every rect edge first (openings() does both)."""
    from mathutils import Vector
    k = AX[axis]
    for rect in rects:
        faces = _cells(bm, axis, sign, rect)
        if not faces:
            continue
        rim = set(e for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in faces) == 1)
        res = bmesh.ops.extrude_face_region(bm, geom=faces)
        verts = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
        move = Vector((0.0, 0.0, 0.0))
        move[k] = -sign * depth
        if vec is not None:                     # a slanted pocket (a raked magazine well)
            move = Vector(vec)
        bmesh.ops.translate(bm, verts=verts, vec=move)
        bmesh.ops.delete(bm, geom=faces, context="FACES")
        new_rim = set(e for v in verts for e in v.link_edges)
        _weigh(bm, list(rim) + list(new_rim), weight)


def through(bm, axis, rects, weight=None):
    """Holes right through: the cells inside each rect on both sides (+ and -) are removed and their
    edges bridged with walls."""
    for rect in rects:
        loops = []
        for sign in (1, -1):
            faces = _cells(bm, axis, sign, rect)
            edges = set()
            for f in faces:
                for e in f.edges:
                    if sum(1 for g in e.link_faces if g in faces) == 1:
                        edges.add(e)
            bmesh.ops.delete(bm, geom=faces, context="FACES_ONLY")
            loops += list(edges)
        if loops:
            res = bmesh.ops.bridge_loops(bm, edges=loops)
            _weigh(bm, loops + [e for e in res.get("edges", [])], weight)


def openings(bm, axis, rects, depth=None, sign=1, weight=None, vec=None):
    """Loop cuts through the edges of every rect (a0, a1, b0, b1 on the two other axes), then pockets
    `depth` deep on the `sign` side, or holes right through when depth is None."""
    k = AX[axis]
    o = [n for n in "XYZ" if AX[n] != k]
    loop_cuts(bm, o[0], sorted(set(v for r in rects for v in r[:2])))
    loop_cuts(bm, o[1], sorted(set(v for r in rects for v in r[2:])))
    if depth is None:
        through(bm, axis, rects, weight)
    else:
        pocket(bm, axis, sign, rects, depth, weight, vec)


def tidy(bm):
    """Every face over four sides: beauty-triangulated and joined back into quads."""
    import math as _m
    big = [f for f in bm.faces if len(f.verts) > 4]
    if not big:
        return
    tri = bmesh.ops.triangulate(bm, faces=big, quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.join_triangles(bm, faces=tri["faces"], angle_face_threshold=_m.radians(5.0),
                             angle_shape_threshold=_m.radians(180.0), cmp_seam=False, cmp_sharp=False,
                             cmp_uvs=False, cmp_vcols=False, cmp_materials=False)


# --- Outlines and special shapes -------------------------------------------------------------------------

def clip_poly(pts, z, above=True):
    """The part of a closed outline [(x, z), ...] above (or below) the line at height z."""
    keep = (lambda p: p[1] >= z) if above else (lambda p: p[1] <= z)
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if keep(a):
            out.append(a)
        if keep(a) != keep(b):
            t = (z - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, z))
    # A cut point a hair from a corner makes a sliver: merge points closer than 0.5 mm (sum of the two offsets).
    clean = []
    for p in out:
        if not clean or abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 0.0005:
            clean.append(p)
    if len(clean) > 2 and abs(clean[0][0] - clean[-1][0]) + abs(clean[0][1] - clean[-1][1]) <= 0.0005:
        clean.pop()
    return clean


def _inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def notch_outline(pts, circles, step_deg=15.0):
    """Cut round notches (finger grooves) into a closed outline: each circle (cx, cy, r) that crosses
    the outline twice replaces the stretch inside it by its arc."""
    pts = list(pts)
    for cx, cy, r in circles:
        n = len(pts)
        hits = []
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            dx, dy = x2 - x1, y2 - y1
            fx, fy = x1 - cx, y1 - cy
            a = dx * dx + dy * dy
            b = 2 * (fx * dx + fy * dy)
            c = fx * fx + fy * fy - r * r
            disc = b * b - 4 * a * c
            if a == 0 or disc < 0:
                continue
            for sgn in (-1, 1):
                t = (-b + sgn * math.sqrt(disc)) / (2 * a)
                if 0.0 <= t < 1.0:
                    hits.append((i, t, (x1 + dx * t, y1 + dy * t)))
        if len(hits) != 2:
            continue
        (i0, t0, p0), (i1, t1, p1) = sorted(hits)
        a0 = math.atan2(p0[1] - cy, p0[0] - cx)
        a1 = math.atan2(p1[1] - cy, p1[0] - cx)
        # The arc that lies inside the outline.
        def arc(s0, s1):
            span = (s1 - s0) % (2 * math.pi)
            k = max(2, int(math.degrees(span) / step_deg))
            return [(cx + r * math.cos(s0 + span * j / k), cy + r * math.sin(s0 + span * j / k)) for j in range(1, k)]
        mid_a = (a0 + ((a1 - a0) % (2 * math.pi)) / 2)
        mid = (cx + r * math.cos(mid_a), cy + r * math.sin(mid_a))
        path = arc(a0, a1) if _inside(mid, pts) else arc(a1, a0)[::-1]
        # Outline: up to the first hit, the arc, from the second hit on (the stretch between is dropped).
        pts = pts[:i0 + 1] + [p0] + path + [p1] + pts[i1 + 1:]
    return pts


def fluted_barrel(bm, stations, flutes=6, depth=0.0016, width_deg=22.0, sides=96, c=(0.0, 0.0), axis_offset=0.0):
    """A barrel along +Y as rings of `sides` vertices: stations [(y, radius, flute 0..1), ...]. Flutes are
    rounded grooves `width_deg` wide (at full depth in the middle), faded in and out by the third
    value. Quad caps at both ends."""
    sides = 4 * math.ceil(sides / 4)
    ang = [2 * math.pi * (i + 0.5) / sides for i in range(sides)]
    pitch = 2 * math.pi / flutes
    half = math.radians(width_deg) / 2

    def groove(t):
        d = abs(((t - axis_offset + pitch / 2) % pitch) - pitch / 2)
        return 0.5 * (1 + math.cos(math.pi * d / half)) if d < half else 0.0
    rings = []
    for y, r, f in stations:
        rings.append([bm.verts.new((c[0] + (r - depth * f * groove(t)) * math.sin(t), y,
                                    c[1] + (r - depth * f * groove(t)) * math.cos(t))) for t in ang])
    for A, B in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((A[i], A[j], B[j], B[i]))
    coons_cap(bm, rings[0])
    coons_cap(bm, rings[-1], flip=True)
    return rings


def round_pockets(bm, axis, sign, centres, r, depth, weight=None):
    """Round pockets (witness holes, screw recesses) in a flat face: a 3 x 3 block of cells per hole by
    loop cuts, its outline pulled onto the circle (the circle-in-a-grid layout), then pushed in."""
    k = AX[axis]
    o = [n for n in "XYZ" if AX[n] != k]
    a_vals = sorted(set(v for a, b in centres for v in (a - r, a - r / 3, a + r / 3, a + r)))
    b_vals = sorted(set(v for a, b in centres for v in (b - r, b - r / 3, b + r / 3, b + r)))
    loop_cuts(bm, o[0], a_vals)
    loop_cuts(bm, o[1], b_vals)
    bm.normal_update()
    ka, kb = AX[o[0]], AX[o[1]]
    plane = max(v.co[k] * sign for v in bm.verts) * sign
    for a, b in centres:
        for v in bm.verts:
            if abs(v.co[k] - plane) > 1e-6:
                continue
            u, w = (v.co[ka] - a) / r, (v.co[kb] - b) / r
            if abs(u) <= 1 + 1e-6 and abs(w) <= 1 + 1e-6:
                v.co[ka] = a + r * u * math.sqrt(max(0.0, 1 - w * w / 2))
                v.co[kb] = b + r * w * math.sqrt(max(0.0, 1 - u * u / 2))
    pocket(bm, axis, sign, [(a - r, a + r, b - r, b + r) for a, b in centres], depth, weight)


def ladder(pts, tol=0.0005):
    """A flat cap as a ladder of quads: the outline [(a, b), ...] is split at its two ends along its long
    axis into two chains, and every corner of either chain gets a rung straight across to the other
    (a point is added there unless the other chain has a corner within `tol`). Returns the new outline
    and the cap's faces as index lists into it, or None when a chain doubles back along the axis (then
    the caller fills the cap another way)."""
    n = len(pts)
    if n < 4:
        return None
    ax = 0 if (max(p[0] for p in pts) - min(p[0] for p in pts)) >= (max(p[1] for p in pts) - min(p[1] for p in pts)) else 1
    lo = min(range(n), key=lambda i: (pts[i][ax], pts[i][1 - ax]))
    hi = max(range(n), key=lambda i: (pts[i][ax], -pts[i][1 - ax]))
    fwd = [(lo + k) % n for k in range((hi - lo) % n + 1)]
    bwd = [(lo - k) % n for k in range((lo - hi) % n + 1)]
    for ch in (fwd, bwd):
        if any(pts[ch[k + 1]][ax] < pts[ch[k]][ax] - 1e-7 for k in range(len(ch) - 1)):
            return None

    def at(ch, t):
        for k in range(len(ch) - 1):
            a, b = pts[ch[k]], pts[ch[k + 1]]
            if a[ax] - 1e-9 <= t <= b[ax] + 1e-9 and b[ax] > a[ax]:
                u = (t - a[ax]) / (b[ax] - a[ax])
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        return pts[ch[-1]]
    # Rungs: walk both chains together; corners within tol of each other share a rung.
    A, B = [pts[fwd[0]]], [pts[bwd[0]]]
    i, j = 1, 1
    while i < len(fwd) or j < len(bwd):
        ta = pts[fwd[i]][ax] if i < len(fwd) else float("inf")
        tb = pts[bwd[j]][ax] if j < len(bwd) else float("inf")
        if abs(ta - tb) <= tol:
            A.append(pts[fwd[i]]); B.append(pts[bwd[j]]); i += 1; j += 1
        elif ta < tb:
            if ta <= A[-1][ax] + 1e-9 and A[-1] != pts[fwd[i]]:      # a step straight across the axis
                A.append(pts[fwd[i]]); B.append(B[-1]); i += 1
                continue
            A.append(pts[fwd[i]]); B.append(at(bwd, ta)); i += 1
        else:
            if tb <= B[-1][ax] + 1e-9 and B[-1] != pts[bwd[j]]:
                B.append(pts[bwd[j]]); A.append(A[-1]); j += 1
                continue
            B.append(pts[bwd[j]]); A.append(at(fwd, tb)); j += 1
    # Outline: chain A forward, then chain B back (its ends are the same points as A's ends, or not).
    outline, ia, ib = [], [], []
    def add(p):
        if outline and abs(outline[-1][0] - p[0]) + abs(outline[-1][1] - p[1]) < 1e-9:
            return len(outline) - 1
        outline.append(p)
        return len(outline) - 1
    for p in A:
        ia.append(add(p))
    for p in reversed(B):
        ib.append(add(p))
    ib = ib[::-1]
    if len(outline) > 1 and abs(outline[0][0] - outline[-1][0]) + abs(outline[0][1] - outline[-1][1]) < 1e-9:
        outline.pop()
        ib = [0 if x == len(outline) else x for x in ib]
    faces = []
    for k in range(len(A) - 1):
        q = [ia[k], ia[k + 1], ib[k + 1], ib[k]]
        q2 = []
        for x in q:
            if x not in q2:
                q2.append(x)
        if len(q2) >= 3:
            faces.append(q2)
    return outline, faces


def slotted_prism(bm, outer, inner, y0, y1, slots, shear=0.0, zref=0.0, gap=0.012):
    """A hollow prism along +Y: outer and inner are closed sections [(x, z), ...] with the same number
    of corners (inner usually a scaled outer). Slots through the wall: (face, t0, t1, y_a, y_b), face i
    being the side from corner i to corner i + 1, t0..t1 the slot's share across that side. The front
    end is slanted by `shear` (y moves by shear * (z - zref)). Every face is a quad."""
    n = len(outer)
    cuts = {i: {0.0} for i in range(n)}
    for f, t0, t1, ya, yb in slots:
        cuts[f] |= {t0, t1}
    ring_t = [(i, t) for i in range(n) for t in sorted(cuts[i]) if t < 1.0]

    def pt(poly, i, t):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        return (x0 + (x1 - x0) * t, z0 + (z1 - z0) * t)
    ys = sorted(set([y0] + [round(s[3], 6) for s in slots] + [round(s[4], 6) for s in slots]))
    cols = []
    for y in ys:
        if cols and y - cols[-1] > 2 * gap:
            k = math.ceil((y - cols[-1]) / gap)
            cols += [cols[-1] + (y - cols[-1]) * s / k for s in range(1, k)]
        cols.append(y)
    while y1 - cols[-1] > 2 * gap:
        cols.append(cols[-1] + gap)
    m = len(ring_t)

    def ring(poly, y, sh):
        out = []
        for i, t in ring_t:
            x, z = pt(poly, i, t)
            out.append(bm.verts.new((x, y + sh * (z - zref), z)))
        return out
    O = [ring(outer, y, 0.0) for y in cols] + [ring(outer, y1, shear)]
    I = [ring(inner, y, 0.0) for y in cols] + [ring(inner, y1, shear)]
    holes = set()
    for f, t0, t1, ya, yb in slots:
        segs = [j for j, (i, t) in enumerate(ring_t) if i == f and t0 - 1e-9 <= t < t1 - 1e-9]
        ks = [k for k in range(len(cols)) if ya - 1e-7 <= cols[k] < yb - 1e-7]
        for j in segs:
            for k in ks:
                holes.add((k, j))
    for S in (O, I):
        for k in range(len(S) - 1):
            for j in range(m):
                if (k, j) not in holes:
                    j2 = (j + 1) % m
                    bm.faces.new((S[k][j], S[k][j2], S[k + 1][j2], S[k + 1][j]))
    for (k, j) in holes:
        j2 = (j + 1) % m
        for (a, b), nb in ((((k, j), (k, j2)), (k - 1, j)), (((k + 1, j), (k + 1, j2)), (k + 1, j)),
                           (((k, j), (k + 1, j)), (k, (j - 1) % m)), (((k, j2), (k + 1, j2)), (k, j2))):
            if nb not in holes:
                bm.faces.new((O[a[0]][a[1]], O[b[0]][b[1]], I[b[0]][b[1]], I[a[0]][a[1]]))
    for k in (0, len(O) - 1):
        for j in range(m):
            j2 = (j + 1) % m
            bm.faces.new((O[k][j], O[k][j2], I[k][j2], I[k][j]))
    return O, I


def _ray_hit(poly, c, ang):
    """Nearest point where a ray from c at angle `ang` crosses the closed outline."""
    dx, dz = math.cos(ang), math.sin(ang)
    best = None
    n = len(poly)
    for i in range(n):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        ex, ez = x1 - x0, z1 - z0
        den = dx * ez - dz * ex
        if abs(den) < 1e-12:
            continue
        s = ((x0 - c[0]) * ez - (z0 - c[1]) * ex) / den
        u = ((x0 - c[0]) * dz - (z0 - c[1]) * dx) / den
        if s > 1e-9 and -1e-9 <= u <= 1 + 1e-9 and (best is None or s < best[0]):
            best = (s, (c[0] + dx * s, c[1] + dz * s))
    return best[1] if best else None


def holed_profile(bm, outer, hole, width, x=0.0, merge_deg=1.5):
    """A side profile [(y, z), ...] extruded across X with a hole right through, both sides filled with
    a ring of quads between the outline and the hole: every corner of either shape gets a spoke from
    the hole's centre out to the other shape. The outline must be star-shaped seen from the hole."""
    cy = sum(p[0] for p in hole) / len(hole)
    cz = sum(p[1] for p in hole) / len(hole)
    angs = sorted(math.atan2(p[1] - cz, p[0] - cy) % (2 * math.pi) for p in list(outer) + list(hole))
    keep = []
    for a in angs:
        if not keep or a - keep[-1] > math.radians(merge_deg):
            keep.append(a)
    if len(keep) > 1 and keep[0] + 2 * math.pi - keep[-1] <= math.radians(merge_deg):
        keep.pop()
    O = [_ray_hit(outer, (cy, cz), a) for a in keep]
    H = [_ray_hit(hole, (cy, cz), a) for a in keep]
    if any(p is None for p in O + H):
        raise ValueError("holed_profile: outline not star-shaped from the hole")
    n = len(keep)
    sides = []
    for sx in (-1, 1):
        xo = x + sx * width / 2
        sides.append(([bm.verts.new((xo, y, z)) for y, z in O], [bm.verts.new((xo, y, z)) for y, z in H]))
    for (o, h) in sides:
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((o[k], o[k2], h[k2], h[k]))
    (oa, ha), (ob, hb) = sides
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((oa[k], oa[k2], ob[k2], ob[k]))
        bm.faces.new((ha[k], hb[k], hb[k2], ha[k2]))


def windowed_tube(bm, y0, y1, r_out, r_in, windows, c=(0.0, 0.0), step=10.0, gap=0.012, extra_ys=()):
    """A hollow round tube along +Y with windows through its wall at any angle: windows
    [(angle0, angle1, y_a, y_b), ...], angles in degrees from +X towards +Z (0 right, 90 top, 180 left,
    270 bottom; angle1 may pass 360). Rows run through every window's angle edges and columns through
    its y edges, so each window is whole cells left out with four walls. Every face is a quad.
    r_out may be a function of y (a stepped tube: put its steps in extra_ys)."""
    rof = r_out if callable(r_out) else (lambda y: r_out)
    windows = [(a0, a1, max(ya, y0), min(yb, y1)) for a0, a1, ya, yb in windows]   # clipped to the tube
    fixed = [0.0, 90.0, 180.0, 270.0]
    for a0, a1, ya, yb in windows:
        fixed += [a0 % 360.0, a1 % 360.0]
    ang = _angles(fixed, step)
    n = len(ang)
    ys = sorted(set([round(y0, 6), round(y1, 6)] + [round(w[2], 6) for w in windows] + [round(w[3], 6) for w in windows]
                    + [round(y, 6) for y in extra_ys]))
    cols = []
    for y in ys:
        if cols and y - cols[-1] > 2 * gap:
            k = math.ceil((y - cols[-1]) / gap)
            cols += [cols[-1] + (y - cols[-1]) * s / k for s in range(1, k)]
        cols.append(y)
    O = [[bm.verts.new((c[0] + rof(y) * math.cos(t), y, c[1] + rof(y) * math.sin(t))) for t in ang] for y in cols]
    I = [[bm.verts.new((c[0] + r_in * math.cos(t), y, c[1] + r_in * math.sin(t))) for t in ang] for y in cols]
    holes = set()
    for a0, a1, ya, yb in windows:
        lo, span = math.radians(a0 % 360.0), math.radians((a1 - a0) % 360.0 or 360.0)
        for j in range(n):
            mid = (ang[j] + (ang[(j + 1) % n] + (2 * math.pi if j == n - 1 else 0.0))) / 2
            if (mid - lo) % (2 * math.pi) < span:
                for k in range(len(cols) - 1):
                    if ya - 1e-7 <= cols[k] and cols[k + 1] <= yb + 1e-7:
                        holes.add((k, j))
    for S in (O, I):
        for k in range(len(S) - 1):
            for j in range(n):
                if (k, j) not in holes:
                    j2 = (j + 1) % n
                    bm.faces.new((S[k][j], S[k][j2], S[k + 1][j2], S[k + 1][j]))
    for (k, j) in holes:
        j2 = (j + 1) % n
        for (a, b), nb in ((((k, j), (k, j2)), (k - 1, j)), (((k + 1, j), (k + 1, j2)), (k + 1, j)),
                           (((k, j), (k + 1, j)), (k, (j - 1) % n)), (((k, j2), (k + 1, j2)), (k, j2))):
            if a[0] == b[0] and a[0] in (0, len(O) - 1):
                continue                        # an opening that runs out through an end stays open
            if nb not in holes:
                bm.faces.new((O[a[0]][a[1]], O[b[0]][b[1]], I[b[0]][b[1]], I[a[0]][a[1]]))
    for k, cell in ((0, 0), (len(O) - 1, len(O) - 2)):
        for j in range(n):
            if (cell, j) in holes:
                continue
            j2 = (j + 1) % n
            bm.faces.new((O[k][j], O[k][j2], I[k][j2], I[k][j]))
    return O, I


def scanline(pts):
    """A flat cap for any simple outline [(a, b), ...]: cut into slices along its long axis at every
    corner, each slice filled with one quad (or triangle) per stretch of inside, so the whole cap is
    quads with straight rungs. Returns the outline with the rung ends added and the faces as index
    lists into it."""
    n = len(pts)
    ax = 0 if (max(p[0] for p in pts) - min(p[0] for p in pts)) >= (max(p[1] for p in pts) - min(p[1] for p in pts)) else 1
    T = sorted(set(round(p[ax], 9) for p in pts))
    key = lambda p: (round(p[0], 8), round(p[1], 8))

    def on_edge(e, t):
        a, b = pts[e], pts[(e + 1) % n]
        if abs(a[ax] - t) < 1e-9:
            return a
        if abs(b[ax] - t) < 1e-9:
            return b
        u = (t - a[ax]) / (b[ax] - a[ax])
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    faces_pts = []
    for t0, t1 in zip(T, T[1:]):
        tm = (t0 + t1) / 2
        cross = []
        for e in range(n):
            a, b = pts[e], pts[(e + 1) % n]
            if min(a[ax], b[ax]) < tm < max(a[ax], b[ax]):
                cross.append((on_edge(e, tm)[1 - ax], e))
        cross.sort()
        for k in range(0, len(cross) - 1, 2):
            e1, e2 = cross[k][1], cross[k + 1][1]
            faces_pts.append([on_edge(e1, t0), on_edge(e1, t1), on_edge(e2, t1), on_edge(e2, t0)])
    # Outline with every rung end on its edge, in order.
    outline = []
    for e in range(n):
        a, b = pts[e], pts[(e + 1) % n]
        outline.append(a)
        if abs(b[ax] - a[ax]) > 1e-12:
            ts = [t for t in T if min(a[ax], b[ax]) + 1e-9 < t < max(a[ax], b[ax]) - 1e-9]
            ts.sort(reverse=b[ax] < a[ax])
            outline += [on_edge(e, t) for t in ts]
    index = {}
    out = []
    for p in outline:
        k = key(p)
        if k not in index:
            index[k] = len(out)
            out.append(p)
    # No T-junctions: a face's side along a slice line takes in every corner of the next slice that
    # lies on it (the face then has more than four corners; the caller joins those back into quads).
    on_line = {}
    for fp in faces_pts:
        for p in fp:
            on_line.setdefault(round(p[ax], 9), set()).add(key(p))
    fixed = []
    for fp in faces_pts:
        full = []
        for i in range(len(fp)):
            a, b = fp[i], fp[(i + 1) % len(fp)]
            full.append(a)
            if abs(a[ax] - b[ax]) < 1e-9:
                lo_, hi_ = sorted((a[1 - ax], b[1 - ax]))
                mids = [kk for kk in on_line.get(round(a[ax], 9), ()) if lo_ + 1e-9 < kk[1 - ax] < hi_ - 1e-9]
                mids.sort(key=lambda kk: kk[1 - ax], reverse=b[1 - ax] < a[1 - ax])
                full += [tuple(kk) for kk in mids]
        fixed.append(full)
    faces_pts = fixed
    faces = []
    for fp in faces_pts:
        idx = []
        for p in fp:
            i = index.get(key(p))
            if i is None:
                break
            if i not in idx:
                idx.append(i)
        else:
            if len(idx) >= 3:
                faces.append(idx)
    return out, faces
