"""Justice Center phase 2: the site drawable jc_site (run inside Blender by p2_build.py) from plan/p2_site.json (p2_site.py):
podium (granite body, Rockstar's sidewalk flags on top with the old plaza's brick bands), steps (visual treads, one collision ramp
along the nosings as Rockstar builds them), the lawn and the sloped walk (one height function: p2_site_plan.lawn_z; drawn and
collision are the same mesh), the lawn's granite kerb, the secure-yard walls, the police wall with its letters, the Portal
sculpture (our own bent dark tube), the atrium's placeholder core (until the atrium MLO exists: p2_plan.MLO_BUILT)."""
import bpy, bmesh, math, json
from mathutils import Vector
import tc_kit as TK
import p2_plan as PL, p2_site_plan as SP
from p2_kit import col_box, col_mesh, quad, box_minus
S = SP.S; G = PL.G
def podium(key):
    bands = [(b - S['band_w'] / 2, b + S['band_w'] / 2) for b in S['bands_v']]
    for i, (u0, u1, v0, v1) in enumerate(S['podium']):
        TK.box(key, (u0, v0, PL.SLAB - 0.3), (u1, v1, G - 0.05), 'granite', col=False)
        col_box((u0, v0, PL.SLAB - 0.3), (u1, v1, G), 'concrete')
        plaza = u0 >= 37.0                                          # the street plaza (bands); the aprons round the buildings: plain flags
        holes = [(u0, u1, a, b) for a, b in bands if plaza and v0 < a and b < v1]
        for a, b, c, d in TK.rects_minus(u0, u1, v0, v1, holes): TK.box(key, (a, c, G - 0.05), (b, d, G), 'sidewalk', col=False)
        for a, b, c, d in holes: TK.box(key, (a, c, G - 0.05), (b, d, G), 'brick', col=False)
def steps(key):
    n, go = S['step']
    for ax, at, s0, s1, o, zl, zt in S['steps']:
        h = (zt - zl) / n
        def p(s, d, z): return (at + o * d, s, z) if ax == 'u' else (s, at + o * d, z)
        for i in range(n - 1):                                      # treads 1..n-1 (the top one is the podium / colonnade floor)
            a = p(s0, i * go, zl - 0.3); b = p(s1, (i + 1) * go, zt - (i + 1) * h)
            TK.box(key, tuple(min(x, y) for x, y in zip(a, b)), tuple(max(x, y) for x, y in zip(a, b)), 'granite', col=False)
        # collision: one ramp from one going in front of the bottom riser (on the slab) up to the top riser (doc 09, Rockstar's stairs)
        r0, r1 = p(s0, n * go, zl), p(s1, n * go, zl); t0, t1 = p(s0, -0.05, zt), p(s1, -0.05, zt)
        b0, b1 = p(s0, n * go, zl - 0.3), p(s1, n * go, zl - 0.3); c0, c1 = p(s0, -0.05, zl - 0.3), p(s1, -0.05, zl - 0.3)
        V = [r0, r1, t1, t0, b0, b1, c1, c0]
        col_mesh(V, [_w(V, (0, 1, 2, 3), (0, 0, 1)), _w(V, (4, 7, 6, 5), (0, 0, -1)), _w(V, (0, 4, 5, 1), _out(ax, o)), _w(V, (0, 3, 7, 4), _side(ax, -1)), _w(V, (1, 5, 6, 2), _side(ax, 1))], 'stone')
def _out(ax, o): return (o, 0, 0) if ax == 'u' else (0, o, 0)
def _side(ax, s): return (0, s, 0) if ax == 'u' else (s, 0, 0)
def _w(V, idx, toward):
    a, b, c = (Vector(V[i]) for i in idx[:3]); n = (b - a).cross(c - a)
    return tuple(idx) if n.dot(Vector(toward)) >= 0 else tuple(reversed(idx))
def surface(poly, zfun, grid=2.0):
    """a polygon (lot u, v) as a triangulated mesh cut on a `grid` m lattice, every vertex on zfun: [(verts, faces)]."""
    bm = bmesh.new(); vs = [bm.verts.new(Vector((u, v, 0.0))) for u, v in poly]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    us = [p[0] for p in poly]; ws = [p[1] for p in poly]
    for k in range(int(math.floor(min(us) / grid)) + 1, int(math.ceil(max(us) / grid))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((k * grid, 0, 0)), plane_no=Vector((1, 0, 0)))
    for k in range(int(math.floor(min(ws) / grid)) + 1, int(math.ceil(max(ws) / grid))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k * grid, 0)), plane_no=Vector((0, 1, 0)))
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    for v in bm.verts: v.co.z = zfun(v.co.x, v.co.y)
    out_v = [tuple(v.co) for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}; out_f = []
    for f in bm.faces:
        ids = [idx[v] for v in f.verts]; a, b, c = (Vector(out_v[i]) for i in ids)
        out_f.append(tuple(ids) if (b - a).cross(c - a).z > 0 else tuple(reversed(ids)))
    bm.free(); return out_v, out_f
def driveways(key):
    """area 3: the police garage driveways (p2_site DRIVEWAYS): Rockstar's concrete at the doors' threshold (slab + 5 cm) from the face to
    the lot edge, then the dipped kerb down KERB_DROP over KERB_OUT to the road; side skirts down to the slab; collision = the mesh."""
    import jc_frame as F
    for d in S['driveways']:
        v0, v1 = d['v']; u0, e = d['u0'], d['edge']; ko, kd = S['kerb_out'], S['kerb_drop']
        def z(u, v, e=e, ko=ko, kd=kd):
            return F.slab_z(*F.W(u, v)) + 0.05 - kd * min(1.0, max(0.0, (u - (e - ko)) / ko))
        e -= 0.02                                                         # (ends just inside the lot edge)
        poly = [(u0, v0), (e, v0), (e, v1), (u0, v1)]
        V, Fc = surface(poly, z, grid=1.0); TK.mesh(key, V, Fc, 'conc', False, 'driveway'); col_mesh(V, Fc, 'concrete')
        for vv, s_ in ((v0, -1), (v1, 1)):                                # the side skirts (the strip stands 5 cm over the slab)
            us = [u0 + i * 1.0 for i in range(int((e - u0) / 1.0))] + [e]
            for a_, b_ in zip(us, us[1:]):
                Q = [(a_, vv, z(a_, vv)), (b_, vv, z(b_, vv)), (b_, vv, z(b_, vv) - 0.25), (a_, vv, z(a_, vv) - 0.25)]
                TK.mesh(key, Q, [(0, 1, 2, 3) if s_ < 0 else (3, 2, 1, 0)], 'conc', False, 'driveway_side')
        vs_ = [v0 + i * 0.5 for i in range(int((v1 - v0) / 0.5))] + [v1]          # the street end's skirt (its 1.5 cm lip)
        for a_, b_ in zip(vs_, vs_[1:]):
            Q = [(e, a_, z(e, a_)), (e, a_, z(e, a_) - 0.25), (e, b_, z(e, b_) - 0.25), (e, b_, z(e, b_))]
            TK.mesh(key, Q, [(0, 1, 2, 3)], 'conc', False, 'driveway_end')
def lawn(key):
    for poly in S['lawn']:
        V, Fc = surface(poly, SP.lawn_z); TK.mesh(key, V, Fc, 'grass', False, 'lawn'); col_mesh(V, Fc, 'grass')
    for poly in S['walk']:
        V, Fc = surface(poly, SP.lawn_z); TK.mesh(key, V, Fc, 'sidewalk', False, 'walk'); col_mesh(V, Fc, 'concrete')
    # the granite kerb along the lawn's outer edge: 0.25 m wide (mitred at every bend: neighbours share their edges), its top on the
    # lawn edge (slab + 0.15), its face down into the slab. Runs = the outer ring's stretches that have lawn behind them.
    O = [tuple(p) for p in S['outer']][:-1]; z = PL.SLAB + SP.KERB_UP; n = len(O)
    area = sum(O[i][0] * O[(i + 1) % n][1] - O[(i + 1) % n][0] * O[i][1] for i in range(n)); sg = 1.0 if area > 0 else -1.0
    def keep(a, b):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); return m[1] > 60.35 and not (m[0] < -8.4 and m[1] < 63.7)
    def nrm(a, b):
        L = math.dist(a, b); return (sg * (b[1] - a[1]) / L, -sg * (b[0] - a[0]) / L)
    start = next(i for i in range(n) if not keep(O[i - 1], O[i]))
    runs, cur = [], []
    for k in range(n):
        i = (start + k) % n; a, b = O[i], O[(i + 1) % n]
        if keep(a, b) and math.dist(a, b) > 1e-3: cur.append((a, b))
        elif cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    for run in runs:
        pts = [run[0][0]] + [b for _, b in run]; N = [nrm(a, b) for a, b in run]; off = []
        for i, p in enumerate(pts):
            ns = [N[j] for j in (i - 1, i) if 0 <= j < len(N)]; mx, my = sum(q[0] for q in ns), sum(q[1] for q in ns); L = math.hypot(mx, my)
            mx, my = mx / L, my / L; c = max(0.5, mx * ns[0][0] + my * ns[0][1]); off.append((p[0] + mx * 0.25 / c, p[1] + my * 0.25 / c))
        V, Fc = [], []
        for i, (p, q) in enumerate(zip(pts, off)): V += [(p[0], p[1], z), (q[0], q[1], z), (q[0], q[1], PL.SLAB - 0.2)]
        for i in range(len(pts) - 1):
            a, b = 3 * i, 3 * (i + 1); nx, ny = N[i]
            Fc += [_w(V, (a, b, b + 1, a + 1), (0, 0, 1)), _w(V, (a + 1, b + 1, b + 2, a + 2), (nx, ny, 0))]
        TK.mesh(key, V, Fc, 'kerb', False, 'kerb'); col_mesh(V, Fc, 'stone')
def walls(key):
    gate = S['yard_gate']
    for u0, u1, v0, v1, h in S['yard_walls']:
        segs = [(v0, v1)]
        if u0 < -40 and gate[0] == 'W': segs = [(v0, gate[1] - gate[2] / 2), (gate[1] + gate[2] / 2, v1)]
        for a, b in segs:
            TK.box(key, (u0, a, PL.SLAB - 0.3), (u1, b, PL.SLAB + h), 'granite', col=False); col_box((u0, a, PL.SLAB - 0.3), (u1, b, PL.SLAB + h), 'stone')
            TK.box(key, (u0 - 0.06, a, PL.SLAB + h), (u1 + 0.06, b, PL.SLAB + h + 0.12), 'kerb', col=False); col_box((u0 - 0.06, a, PL.SLAB + h), (u1 + 0.06, b, PL.SLAB + h + 0.12), 'stone')
    u0, u1, v0, v1, h = S['police_wall']
    TK.box(key, (u0, v0, G - 0.05), (u1, v1, G + h), 'granite', col=False); col_box((u0, v0, G), (u1, v1, G + h), 'stone')
    bb = letters(key, 'CLEVELAND POLICE HEADQUARTERS', u1, (v0 + v1) / 2, G + h * 0.55, 0.30, 0.025, max_w=(v1 - v0) - 1.0)
    col_box((u1, bb[0], bb[2]), (u1 + 0.025, bb[1], bb[3]), 'metal')                       # the letters' band: raised letters collide too
def letters(key, text, u_face, v_c, z_c, cap, depth, max_w=None):
    """raised bronze letters on a +u facing wall (the real plaza wall's bronze letters on pink granite): Blender's own font turned
    into a mesh, cap height `cap`, `depth` proud of the wall, centred at (v_c, z_c); Rockstar's brass recipe (TK 'brass', from
    ba_trad_rails). No sign panel behind them: the granite shows between the letters."""
    cu = bpy.data.curves.new('jc_letters', 'FONT'); cu.body = text; cu.size = 1.0; cu.extrude = 0.5; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('jc_letters', cu); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.update()
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    V = [v.co.copy() for v in me.vertices]; zs = [p.y for p in V]; k = cap / 0.72          # Blender's default font: caps ~0.72 of size
    xs = [p.x for p in V]; cx = (min(xs) + max(xs)) / 2; cy = (min(zs) + max(zs)) / 2
    if max_w: k = min(k, max_w / (max(xs) - min(xs)))                                        # never wider than its wall stretch
    # font frame: x along the text, y up, z out of the wall -> lot frame (a cyclic swap: faces keep their winding): u = the wall + z,
    # v = +x (a reader on the +u side looking -u has +v on his right), z = y
    verts = [(u_face + (p.z + 0.5) * depth, v_c + (p.x - cx) * k, z_c + (p.y - cy) * k) for p in V]
    faces = [tuple(p.vertices) for p in me.polygons]
    TK.mesh(key, verts, faces, 'brass', False, 'letters')
    vs_ = [p[1] for p in verts]; zs_ = [p[2] for p in verts]
    ob.to_mesh_clear(); bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    return (min(vs_), max(vs_), min(zs_), max(zs_))
def portal(key):
    """our own model of the bent dark tube: one continuous round tube (16 sides) along a smooth path in a vertical plane - a leg up,
    the top bar with rounded bends, the other leg slanting down and running along the ground. Collision: square beams along it."""
    p = S['portal']; u = p['u']; v0 = p['v0']; h = p['h']; r = p['r']; z0 = G + r
    ctrl = [(v0, z0 - r + 0.02), (v0, z0 + h * 0.55), (v0 + 0.4, z0 + h * 0.86), (v0 + 1.6, z0 + h * 0.97), (v0 + 4.8, z0 + h * 0.99), (v0 + 6.4, z0 + h * 0.90),
            (v0 + 7.2, z0 + h * 0.66), (v0 + 8.6, z0 + h * 0.25), (v0 + 9.6, z0 + 0.05), (v0 + 10.6, z0 - 0.02), (v0 + 13.2, z0 - 0.02)]
    pts = _smooth(ctrl, 10)
    P = [Vector((u, s, z)) for s, z in pts]; seg = 16; V = []; Fc = []
    for i, c in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized(); a = Vector((1.0, 0.0, 0.0)); b = t.cross(a).normalized()
        for j in range(seg):
            th = 2 * math.pi * j / seg; V.append(tuple(c + (a * math.cos(th) + b * math.sin(th)) * r))
    for i in range(len(P) - 1):
        for j in range(seg):
            q = (i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j)
            cen = (P[i] + P[i + 1]) / 2; f = q
            vv = [Vector(V[x]) for x in q]
            if (vv[1] - vv[0]).cross(vv[2] - vv[0]).dot((vv[0] + vv[2]) / 2 - cen) < 0: f = tuple(reversed(q))
            Fc.append(f)
    Fc.append(tuple(range(seg))[::-1] if True else ()); Fc.append(tuple((len(P) - 1) * seg + j for j in range(seg)))
    TK.mesh(key, V, Fc, 'metal', False, 'portal'); col_mesh(V, Fc, 'metal')                     # the tube itself is its collision
    TK.box(key, (u - 0.9, v0 - 0.9, G - 0.05), (u + 0.9, v0 + 0.9, G + 0.02), 'kerb', col=False)          # a granite footing plate
def _smooth(ctrl, k):
    """Catmull-Rom through the control points, k samples per span."""
    out = []; C = [ctrl[0]] + ctrl + [ctrl[-1]]
    for i in range(1, len(C) - 2):
        p0, p1, p2, p3 = C[i - 1], C[i], C[i + 1], C[i + 2]
        for j in range(k):
            t = j / k; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[n]) + (-p0[n] + p2[n]) * t + (2 * p0[n] - 5 * p1[n] + 4 * p2[n] - p3[n]) * t2 + (-p0[n] + 3 * p1[n] - 3 * p2[n] + p3[n]) * t3) for n in range(2)))
    out.append(ctrl[-1]); return out
def core(key):
    """the atrium's placeholder interior (until phase 3's MLO: p2_plan.MLO_BUILT['atrium']): the galleria floor and the granite walls
    of the buildings round it, seen through the clear curtain wall and roof. Each side of each atrium rect is walked every 0.25 m;
    a run that stands against another building gets a 0.3 m granite wall inside the atrium (full rect extents: no slot at a split)."""
    import p2_facade as FA
    b = PL.B['atrium']; D = b['depth']; STRIPS = []
    for face in PL.face_list('atrium'):                             # the atrium's own facade stone: exposed stretches of its faces, D deep
        f, at, ax, s0, s1, o = face; s0f, s1f = (s0 - D, s1 + D) if ax == 'u' else (s0, s1); segs = [(s0f, s1f)]
        for a, c, *_ in PL.covered('atrium', face): segs = [x for p0, p1 in segs for x in ((p0, min(p1, a)), (max(p0, c), p1)) if x[1] - x[0] > 1e-6]
        for a, c in segs:
            p = PL.P(face, a, -D, PL.SLAB - 0.5); q = PL.P(face, c, 0.0, b['top'])
            STRIPS.append((min(p[0], q[0]), max(p[0], q[0]), min(p[1], q[1]), max(p[1], q[1]), p[2], q[2]))
    for u0, u1, v0, v1 in FA.atrium_pieces(): TK.box(key, (u0, v0, G - 0.3), (u1, v1, G), 'kerb', col=False)
    for r in PL.rects('atrium'):
        u0, u1, v0, v1 = r
        sides = (('v', v1, u0, u1, 1), ('v', v0, u0, u1, -1), ('u', u1, v0, v1, 1), ('u', u0, v0, v1, -1))
        for ax, at, a0, a1, o in sides:
            face = (None, at, ax, a0, a1, o); n = max(1, int(round((a1 - a0) / 0.25))); runs = []
            for i in range(n):
                s = a0 + (a1 - a0) * (i + 0.5) / n; nb = _neighbour_at('atrium', face, s)
                if runs and runs[-1][2] == nb: runs[-1][1] = a0 + (a1 - a0) * (i + 1) / n
                else: runs.append([a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n, nb])
            for s0, s1, nb in runs:
                if nb is None: continue
                p = PL.P(face, s0, -b['depth'], G - 0.3); q = PL.P(face, s1, 0.0, b['roof'] - 0.1)
                lo, hi = tuple(min(x, y) for x, y in zip(p, q)), tuple(max(x, y) for x, y in zip(p, q))
                for c in box_minus((lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]), STRIPS):      # never into the atrium's own facade stone
                    TK.box(key, (c[0], c[2], c[4]), (c[1], c[3], c[5]), 'granite', col=False)
def _internal(r, ax, at, s):
    """is this side of atrium rect r, at s, shared with the atrium's other rect (an inner split of the L)?"""
    for q in PL.rects('atrium'):
        if q == r: continue
        lo, hi = (q[0], q[1]) if ax == 'u' else (q[2], q[3]); a0, a1 = (q[2], q[3]) if ax == 'u' else (q[0], q[1])
        if (abs(lo - at) < 1e-6 or abs(hi - at) < 1e-6) and a0 <= s <= a1: return True
    return False
def _neighbour_at(k, face, s):
    f, at, ax, s0, s1, o = face
    for j in PL.B:
        if j == k: continue
        for (u0, u1, v0, v1) in PL.rects(j):
            lo, hi = (u0, u1) if ax == 'u' else (v0, v1); a0, a1 = (v0, v1) if ax == 'u' else (u0, u1)
            if (abs(lo - at) < 0.3 or abs(hi - at) < 0.3) and a0 <= s <= a1: return j
    return None
