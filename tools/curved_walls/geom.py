"""Curved-building helpers over Tower City's tc_kit (run inside Blender; tc_kit imported, never edited).
The building's outer face is ONE closed counter-clockwise polyline (outside = right of travel) made of named runs (club_plan.RUNS +
the faceted glass front). Walls, linings, glass, frames and portals are pieces of it between two run positions s and two heights,
built on mitred offset lines, so curved and angled walls meet without gaps or overlaps. Also: polygon slabs (floors / roofs / ceilings,
flat or sloped), convex clipping, collision-only solids."""
import math
import bpy
from mathutils import Vector
import tc_kit as TK


# ---------------- 2D ----------------
def rnorm(a, b):
    """unit normal to the right of a -> b."""
    ex, ey = b[0] - a[0], b[1] - a[1]; L = math.hypot(ex, ey); return (ey / L, -ex / L)


def offset_edges(pts, ds):
    """closed polygon pts; edge i (pts[i] -> pts[i+1]) moved ds[i] to its right; returns the mitred vertices (vertex i = edges i-1, i)."""
    n = len(pts); out = []
    for i in range(n):
        a, p, b = pts[i - 1], pts[i], pts[(i + 1) % n]
        n1, n2 = rnorm(a, p), rnorm(p, b); d1, d2 = ds[i - 1], ds[i]
        e1 = (p[0] - a[0], p[1] - a[1]); e2 = (b[0] - p[0], b[1] - p[1])
        q1 = (a[0] + n1[0] * d1, a[1] + n1[1] * d1); q2 = (p[0] + n2[0] * d2, p[1] + n2[1] * d2)
        den = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(den) < 1e-9: out.append((p[0] + n2[0] * d2, p[1] + n2[1] * d2)); continue          # straight on
        t = ((q2[0] - q1[0]) * e2[1] - (q2[1] - q1[1]) * e2[0]) / den
        out.append((q1[0] + e1[0] * t, q1[1] + e1[1] * t))
    return out


def clip_poly(subject, clipper):
    """subject clipped by a convex counter-clockwise clipper (Sutherland-Hodgman)."""
    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9
        def cut(p, q):
            dp = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]); dq = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
            t = dp / (dp - dq); return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        src, out = out, []
        for j, p in enumerate(src):
            q = src[j - 1]
            if side(p):
                if not side(q): out.append(cut(q, p))
                out.append(p)
            elif side(q): out.append(cut(q, p))
        if not out: return []
    return out


def rect(x0, x1, y0, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------- the outline ----------------
class Outline:
    """runs = [(name, pts)] in order round the building (each run starts where the last ended); vertex k -> vertex k+1 is segment k."""
    def __init__(self, runs):
        self.pts, self.seg = [], []                       # seg[k] = (run name, s at vertex k, s at vertex k+1)
        for name, pts in runs:
            s = 0.0
            if self.pts: assert math.dist(self.pts[-1], pts[0]) < 1e-6, (name, self.pts[-1], pts[0])
            P = pts if not self.pts else pts[1:]
            if self.pts: prev = self.pts[-1]
            else: prev = P[0]; self.pts.append(P[0]); P = P[1:]
            for q in P:
                L = math.dist(prev, q); self.seg.append((name, s, s + L)); s += L; self.pts.append(q); prev = q
        assert math.dist(self.pts[0], self.pts[-1]) < 1e-6, 'the outline must close'
        self.pts.pop()                                     # (the closing vertex = the first)
        assert len(self.pts) == len(self.seg)
        self._off = {}

    def off(self, d):
        if d not in self._off: self._off[d] = offset_edges(self.pts, [d] * len(self.pts))
        return self._off[d]

    def at(self, k, s, d):
        """point at run position s on segment k, d metres right of the outer face (inside: d < 0): at the segment's ends the mitred
        corner, inside it a square cut (outer point + d x the segment's right normal)."""
        name, s0, s1 = self.seg[k]; O = self.off(d)
        if abs(s - s0) < 1e-6: return O[k]
        if abs(s - s1) < 1e-6: return O[(k + 1) % len(O)]
        a, b = self.pts[k], self.pts[(k + 1) % len(self.pts)]; t = (s - s0) / (s1 - s0); n = rnorm(a, b)
        return (a[0] + (b[0] - a[0]) * t + n[0] * d, a[1] + (b[1] - a[1]) * t + n[1] * d)

    def segs(self, run):
        return [k for k, (n, _, _) in enumerate(self.seg) if n == run]

    def heading(self, k):
        a, b = self.pts[k], self.pts[(k + 1) % len(self.pts)]; return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


# ---------------- solids ----------------
def piece(room, O, k, sa, sb, d0, d1, z0, z1, mat, col=True):
    """a wall piece on segment k from run position sa to sb, between offsets d0 and d1, z0..z1 (z1 a number or f(x, y))."""
    if sb - sa < 1e-4 or (not callable(z1) and z1 - z0 < 1e-4): return
    P = [O.at(k, sa, d0), O.at(k, sb, d0), O.at(k, sb, d1), O.at(k, sa, d1)]
    zt = z1 if callable(z1) else (lambda x, y: z1)
    vs = [(x, y, z0) for x, y in P] + [(x, y, zt(x, y)) for x, y in P]
    TK.mesh(room, vs, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat, col, 'wall')


def colsolid(room, vs, faces):
    """collision only (an arbitrary closed solid)."""
    me = bpy.data.meshes.new('col'); me.from_pydata([Vector(v) for v in vs], [], faces); me.materials.append(TK.colmat(room))
    o = bpy.data.objects.new('col', me); TK.coll().objects.link(o); TK._sink(room, o)


def slab(room, poly, z0, z1, mat, col=True, top_only=False):
    """a prism over a counter-clockwise polygon; z0 / z1 numbers or functions f(x, y) (sloped roofs and ceilings)."""
    f0 = z0 if callable(z0) else (lambda x, y, z=z0: z); f1 = z1 if callable(z1) else (lambda x, y, z=z1: z); n = len(poly)
    vs = [(x, y, f0(x, y)) for x, y in poly] + [(x, y, f1(x, y)) for x, y in poly]
    fs = [tuple(range(n, 2 * n))] if top_only else ([tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)])
    TK.mesh(room, vs, fs, mat, False, 'slab')
    if col:
        cf = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        colsolid(room, vs, cf)


def panel_down(room, poly, f, mat):
    """a ceiling: one face over the polygon at height f(x, y), facing down."""
    vs = [(x, y, f(x, y)) for x, y in poly]; TK.mesh(room, vs, [tuple(range(len(poly) - 1, -1, -1))], mat, False, 'ceil')


# ---------------- walls with openings ----------------
EX, LN = 0.25, 0.05
PORTALS, PROPS, DOORS_EXT = [], [], []
PORTAL_MAX, PORTAL_TURN = 8.0, 35.0             # one portal spans consecutive facets of an opening up to this chord / this much turn


def _top(O, k, sa, sb, f):
    """a top (number or f(x, y)) on segment k: (its lowest value at the segment's ends, the callable or None)."""
    if not callable(f): return f, None
    return min(f(*O.at(k, s, 0.0)) for s in (sa, sb)), f


def _pieces(sa, sb, zb, zt, holes, ztf):
    """the solid rectangles of a wall face minus its holes; the ones that reach zt take the callable top ztf (they follow the roof)."""
    for a, b, z, w in TK.rects_minus(sa, sb, zb, zt, holes):
        yield a, b, z, (ztf if ztf is not None and abs(w - zt) < 1e-6 else w)


def run_walls(O, run, room, room_id, top, lin, mat, lmat, ops, floors, lin_s=(-1e9, 1e9), band=None):
    """the outer wall of one run (ext, 0 .. -EX) and its lining (room, -EX .. -EX-LN) over the z ranges lin = [(zb, zt)], minus the
    openings ops = [(s0, s1, z0, z1, kind)] (s on the run). top and the lining tops: numbers or f(x, y) (the pieces under a sloped
    roof follow it). band = (f(x, y) its bottom, mat): the wall above that height in another material (the fascia band under the
    roof). lin_s trims the lining where another zone's wall takes over. Every opening piece gets its glass / frame / collision;
    portals cover each opening over runs of facets (PORTAL_MAX, PORTAL_TURN); leaves go to PROPS / DOORS_EXT."""
    cut = {}                                                                   # op index -> [(k, a, b)] the pieces of that opening
    for k in O.segs(run):
        _, sa, sb = O.seg[k]
        holes = [(i, max(s0, sa), min(s1, sb), z0, z1, kd) for i, (s0, s1, z0, z1, kd) in enumerate(ops) if s0 < sb - 1e-6 and s1 > sa + 1e-6]
        H = [h[1:5] for h in holes]
        zt, ztf = _top(O, k, sa, sb, top)
        if band:
            bz = min(band[0](*O.at(k, s, 0.0)) for s in (sa, sb)); assert all(h[3] < bz - .05 for h in H), (run, k, 'an opening reaches the band')
            for a, b, z, w in _pieces(sa, sb, -0.4, bz, H, None): piece('ext', O, k, a, b, 0.0, -EX, z, w, mat)
            piece('ext', O, k, sa, sb, 0.0, -EX, bz, ztf if ztf else zt, band[1])
        else:
            for a, b, z, w in _pieces(sa, sb, -0.4, zt, H, ztf): piece('ext', O, k, a, b, 0.0, -EX, z, w, mat)
        la, lb = max(sa, lin_s[0]), min(sb, lin_s[1])
        if lb - la > 1e-4:
            for zb, zl in lin:
                zl, zlf = _top(O, k, sa, sb, zl)
                for a, b, z, w in _pieces(la, lb, zb, zl, H, zlf): piece(room, O, k, a, b, -EX, -EX - LN, z, w, lmat, col=False)
        for i, a, b, z0, z1, kind in holes:
            s0, s1 = ops[i][:2]; cut.setdefault(i, []).append((k, a, b))
            opening(O, k, a, b, z0, z1, kind, (a - s0 < 1e-6, s1 - b < 1e-6), floors)
    for i, P in cut.items():                                                   # the portals
        z0, z1, kind = ops[i][2:5]; groups = [[P[0]]]
        for q in P[1:]:
            g = groups[-1]; A_ = O.at(g[0][0], g[0][1], -EX - LN); B_ = O.at(q[0], q[2], -EX - LN)
            turn = abs((O.heading(q[0]) - O.heading(g[0][0]) + 180) % 360 - 180)
            if math.dist(A_, B_) <= PORTAL_MAX and turn <= PORTAL_TURN: g.append(q)
            else: groups.append([q])
        for g in groups: add_portal(O, g[0][0], g[0][1], g[-1][0], g[-1][2], z0, z1, room_id, kind)


def add_portal(O, k0, a, k1, b, z0, z1, room_id, kind):
    """room -> outside (0) over an opening from (segment k0, s a) to (segment k1, s b), on the lining's inner face; its winding faces
    out (counter-clockwise outline: the right of travel). A door leaf listed for that opening gets this portal."""
    A_, B_ = O.at(k0, a, -EX - LN), O.at(k1, b, -EX - LN)
    PORTALS.append({'from': room_id, 'to': 0, 'corners': [(A_[0], A_[1], z0), (B_[0], B_[1], z0), (B_[0], B_[1], z1), (A_[0], A_[1], z1)], 'kind': kind})
    for p in PROPS:
        if p.get('_seg') == (k0, a): p['portal'] = len(PORTALS) - 1; p['room'] = room_id; del p['_seg']


def opening(O, k, a, b, z0, z1, kind, ends, floors):
    """glass, frame and collision of one opening piece (segment k, s a .. b); door leaves listed in PROPS (their portal and room are
    set by add_portal) / DOORS_EXT."""
    m0, m1 = -EX / 2 + .05, -EX / 2 - .05
    if kind in ('glass', 'ribbon', 'slider'):
        g1 = b - 1.6 if kind == 'slider' and ends[1] else b                   # a slider's last 1.6 m is its door bay
        P0, P1 = O.at(k, a, -EX / 2), O.at(k, g1, -EX / 2)
        TK.glass_pane('ext', [(P0[0], P0[1], z0), (P1[0], P1[1], z0), (P1[0], P1[1], z1), (P0[0], P0[1], z1)], 'winglass')
        Q = [O.at(k, a, -EX / 2 + .03), O.at(k, g1, -EX / 2 + .03), O.at(k, g1, -EX / 2 - .03), O.at(k, a, -EX / 2 - .03)]
        colsolid('ext', [(x, y, z0) for x, y in Q] + [(x, y, z1) for x, y in Q], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    w0 = .06 if ends[0] else .03; w1 = .06 if ends[1] else .03                 # a joint inside a ribbon: two halves of one mullion
    piece('ext', O, k, a, a + w0, m0, m1, z0, z1, 'charcoal', False); piece('ext', O, k, b - w1, b, m0, m1, z0, z1, 'charcoal', False)
    piece('ext', O, k, a + w0, b - w1, m0, m1, z1 - .06, z1, 'charcoal', False)
    if kind in ('glass', 'ribbon') and not any(abs(z0 - f) < .01 for f in floors): piece('ext', O, k, a + w0, b - w1, m0, m1, z0, z0 + .06, 'charcoal', False)
    if kind in ('glass', 'ribbon') and b - a > 3.0:                            # mullions every ~1.7 m on a wide pane
        n = round((b - a) / 1.7)
        for i in range(1, n): m = a + (b - a) * i / n; piece('ext', O, k, m - .03, m + .03, m0, m1, z0 + .06, z1 - .06, 'charcoal', False)
    hd = O.heading(k); mid = lambda s: O.at(k, s, -EX / 2)
    if kind in ('door', 'backdoor'):
        p = mid(a + .04); hz = 1.30 if kind == 'door' else 1.075
        PROPS.append({'model': 'bb_frontdoor' if kind == 'door' else 'bb_backdoor', 'pos': (p[0], p[1], z0 + hz), 'heading': hd,
                      'flags': TK.DOOR_FLAGS, '_seg': (k, a)})
    elif kind == 'slider' and ends[1]:
        p = O.at(k, b, -EX / 2 - .12)
        PROPS.append({'model': 'bb_slider', 'pos': (p[0], p[1], z0), 'heading': hd, 'flags': TK.DOOR_FLAGS, '_seg': (k, a)})
    elif kind in ('bay', 'glassbay'):
        p = mid((a + b) / 2); DOORS_EXT.append({'model': 'bb_' + kind, 'pos': [p[0], p[1], z0 + (z1 - z0) / 2], 'heading': hd, 'width': b - a})


def ring_grid(room, poly, c, f, mat, down=False, rings=(.25, .5, .7, .85, .95, 1.0), name='grid'):
    """a surface over a star-shaped polygon (seen from c) at height f(x, y): rings scaled from c toward the polygon, a fan at c.
    down: it faces down (a ceiling). Returns (verts, faces)."""
    n = len(poly); vs = [(c[0], c[1], f(*c))]
    for t in rings:
        for x, y in poly: X, Y = c[0] + (x - c[0]) * t, c[1] + (y - c[1]) * t; vs.append((X, Y, f(X, Y)))
    fs = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for r in range(len(rings) - 1):
        o = 1 + r * n
        for i in range(n): a, b = o + i, o + (i + 1) % n; fs.append((a, a + n, b + n, b))
    if down: fs = [tuple(reversed(q)) for q in fs]
    TK.mesh(room, vs, fs, mat, False, name)
    return vs, fs


def coping(O, run, z):
    for k in O.segs(run):
        _, sa, sb = O.seg[k]; piece('ext', O, k, sa, sb, .02, -EX - .02, z, z + .05, 'charcoal', False)


def poly_rail(room, pts, z0, col=True, inset=.03):
    """a glass balustrade along a polyline (2D points) on a floor at z0: ONE continuous bronze shoe and brass top rail (no two pieces
    meet at a corner), brass posts at the corners and every <= 1.2 m, glass between them; its ends stop `inset` short (of a wall)."""
    P = [list(p) for p in pts]
    for i, j in ((0, 1), (-1, -2)):
        dx, dy = P[j][0] - P[i][0], P[j][1] - P[i][1]; L = math.hypot(dx, dy); P[i][0] += dx / L * inset; P[i][1] += dy / L * inset
    up = lambda p: (0.0, 0.0, 1.0)
    TK.sweep(room, [(x, y, z0 + .035) for x, y in P], .08, 'bronze', up, name='shoe')      # (5 mm into the floor: no face on its face)
    TK.sweep(room, [(x, y, z0 + 1.035) for x, y in P], .07, 'brass', up, name='toprail')
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, math.ceil(L / 1.2)); ux, uy = (bx - ax) / L, (by - ay) / L
        posts = [i * L / n for i in range(n + 1)]
        for t in posts[:-1] + ([posts[-1]] if (bx, by) == tuple(P[-1]) else []):
            TK.beam(room, (ax + ux * t, ay + uy * t, z0 + .08), (ax + ux * t, ay + uy * t, z0 + 1.0), .05, 'brass')
        for t0, t1 in zip(posts, posts[1:]):
            p0 = (ax + ux * (t0 + .03), ay + uy * (t0 + .03)); p1 = (ax + ux * (t1 - .03), ay + uy * (t1 - .03))
            TK.glass_pane(room, [(p0[0], p0[1], z0 + .08), (p1[0], p1[1], z0 + .08), (p1[0], p1[1], z0 + 1.0), (p0[0], p0[1], z0 + 1.0)], 'railglass')
        if col:
            nx, ny = -uy * .04, ux * .04; Q = [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]
            colsolid(room, [(x, y, z0) for x, y in Q] + [(x, y, z0 + 1.07) for x, y in Q], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
