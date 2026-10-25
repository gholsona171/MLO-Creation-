"""Tower City level 0: the exterior clean-up rules (plan/ext_cuts.json, written by ext_plan.py) applied to a bmesh in WORLD space.
Shared by l0_cut.py (drawables: x = mw @ co + entity position) and l0_col.py (collision: x = mw @ co). Run inside Blender.
Order per mesh (apply()):  move (faces leave their spot, protected)  ->  cut  ->  clone (copies protected)  ->  the caller's lot /
footprint cut, which must skip protected faces (keep_layer(bm)). Protected faces are ours by rule: no later cut may undo them."""
import json, re
from pathlib import Path
try:
    import bmesh
    from mathutils import Vector
except ImportError: bmesh = Vector = None             # plain Python (l0_maps.py): only the rules and inside() are used
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
P = T / 'plan/ext_cuts.json'
R = json.loads(P.read_text()) if P.exists() else {'cut': [], 'clone': [], 'move': [], 'ext_only': [], 'b_tarmac': []}
EXT_ONLY = set(R.get('ext_only', []))
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def _polys(r): return r['polys'] if 'polys' in r else [r['poly']]
def rules_for(kind, name, collision=False):
    """the rules of a kind that apply to a model (drawable name) / a collision file (collision=True: rules with 'col')."""
    out = []
    for r in R.get(kind, []):
        if collision:                                                  # name = the collision file (None: any)
            if r.get('col') and (name is None or not r.get('col_files') or re.search(r['col_files'], name)): out.append(r)
        elif re.search(r['models'], name): out.append(r)
    return out
def has_rules(name): return any(rules_for(k, name) for k in ('cut', 'clone', 'move'))
def _wnz(f, world):
    vs = [world(v.co) for v in f.verts[:3]]
    if len(vs) < 3: return 0.0
    n = (vs[1] - vs[0]).cross(vs[2] - vs[0]); return n.z / n.length if n.length > 1e-12 else 0.0
def keep_layer(bm): return bm.faces.layers.int.get('tc_keep') or bm.faces.layers.int.new('tc_keep')
_WORLD = [None]
def _bisect(bm, geom, poly, toloc, tonrm):
    """split along every edge of a polygon. With geom None only the faces whose world box reaches that edge's SEGMENT (+0.5 m) are
    cut (a long outline's 150 planes through a whole Rockstar mesh took the collision step from minutes to hours). Face boxes are
    computed once and kept up to date as the cuts make new faces."""
    world = _WORLD[0]
    def box(f):
        ps = [world(v.co) for v in f.verts]; return (min(p.x for p in ps), max(p.x for p in ps), min(p.y for p in ps), max(p.y for p in ps))
    fb = {f: box(f) for f in bm.faces} if geom is None else None
    for i in range(len(poly)):
        a, b = Vector((*poly[i], 0.0)), Vector((*poly[(i + 1) % len(poly)], 0.0)); d = (b - a).normalized()
        if geom is not None: g = [e for e in geom if e.is_valid]
        else:
            x0, x1 = min(a.x, b.x) - 0.5, max(a.x, b.x) + 0.5; y0, y1 = min(a.y, b.y) - 0.5, max(a.y, b.y) + 0.5
            fs = [f for f, (fx0, fx1, fy0, fy1) in fb.items() if f.is_valid and fx1 >= x0 and fx0 <= x1 and fy1 >= y0 and fy0 <= y1]
            if not fs: continue
            g = list({x for f in fs for x in [f] + list(f.edges) + list(f.verts)})
        res = bmesh.ops.bisect_plane(bm, geom=g, plane_co=toloc(a), plane_no=tonrm(Vector((-d.y, d.x, 0.0))))
        if geom is not None: geom = list(set(geom) | set(res['geom']))
        else:
            for f in fs:
                if f.is_valid: fb[f] = box(f)
            for f in bm.faces:                                       # (the faces the cut made)
                if f not in fb: fb[f] = box(f)
    return geom
def _move(bm, world, toloc, matname, r, zb, mat, nzm, top):
    """split off the faces of a move rule (centre + radius, height band, material, |normal z| <= nzm), shift them, lift vertices over
    top[0] to top[1]; they are protected from later cuts. Returns the face count."""
    keep = keep_layer(bm); c = Vector((*r['centre'], 0.0)); z0, z1 = zb
    cen = lambda f: world(f.calc_center_median())
    sel = [f for f in bm.faces if not f[keep] and (lambda p: (p.xy - c.xy).length <= r['r'] and z0 <= p.z <= z1)(cen(f))
           and (not mat or re.search(mat, matname(f).lower())) and abs(_wnz(f, world)) <= nzm]
    if not sel: return 0
    res = bmesh.ops.split(bm, geom=sel); faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
    sh = Vector(r['shift']); ztop, zto = top
    for v in {v for f in faces for v in f.verts}:
        p = world(v.co) + sh
        if p.z > ztop: p.z = zto
        v.co = toloc(p)
    for f in faces: f[keep] = 1
    return len(faces)
def lodcut_names(): return {n for r in R.get('lodcut', []) for n in r['names']}
def apply_lodcut(bm, world, toloc, tonrm, names, report=None):
    """'lodcut' rules on a LOD / SLOD drawable known by any of `names`: its faces inside the polygon + height band go (split first)."""
    rep = report if report is not None else {}; cen = lambda f: world(f.calc_center_median()); _WORLD[0] = world
    for r in R.get('lodcut', []):
        if not set(r['names']) & set(names): continue
        _bisect(bm, None, r['poly'], toloc, tonrm); z0, z1 = r['z']
        dead = [f for f in bm.faces if (lambda p: z0 <= p.z <= z1 and inside(r['poly'], p.x, p.y))(cen(f))]
        if dead: bmesh.ops.delete(bm, geom=dead, context='FACES'); rep[r['name']] = rep.get(r['name'], 0) + len(dead)
    return rep
def apply_lod(bm, world, toloc, matname, names, report=None):
    """the move rules' LOD entries ('lod': names / mat / nz_max / top) on a LOD or SLOD drawable known by any of `names` (its name or
    hash_xxxxxxxx): the LOD draws the moved piece where the HD model now has it. Used by l0_cut_lod.py."""
    rep = report if report is not None else {}
    for r in R.get('move', []):
        for l in r.get('lod', []):
            if not set(l['names']) & set(names): continue
            n = _move(bm, world, toloc, matname, r, r['z'], l.get('mat'), l.get('nz_max', 1.0), l['top'])
            if n: rep[r['name'] + ' (LOD)'] = rep.get(r['name'] + ' (LOD)', 0) + n
    return rep
KEEP_TRIS = [t for r in R.get('keep_col', []) for t in r['tris']]            # world triangles of the vanilla features kept whole
KEEP_EXCEPT = [q for r in R.get('keep_col', [])[:1] for q in r.get('except', [])]   # our own outlines: nothing kept inside them
_KT = None
def _kt():
    global _KT
    if _KT is None:
        import numpy as np
        A = np.array(KEEP_TRIS, dtype=float).reshape(-1, 3, 3) if KEEP_TRIS else np.zeros((0, 3, 3))
        _KT = (A, A[:, :, :2].min(1), A[:, :, :2].max(1), A[:, :, 2].min(1), A[:, :, 2].max(1))
        if len(A):                                                     # a 4 m bucket grid: each face looks at the triangles near it only
            B = {}
            for k in range(len(A)):
                for gx in range(int(_KT[1][k, 0] // 4) - 1, int(_KT[2][k, 0] // 4) + 2):
                    for gy in range(int(_KT[1][k, 1] // 4) - 1, int(_KT[2][k, 1] // 4) + 2): B.setdefault((gx, gy), []).append(k)
            _KT = _KT + ({k: np.array(v) for k, v in B.items()},)
        else: _KT = _KT + ({},)
    return _KT
def on_kept(p, pad=0.3, zpad=0.4):
    """is world point p on (within pad, in plan; within zpad, in height) a kept feature's drawn surface? (keep_col rules)"""
    A, lo, hi, zl, zh, G = _kt()
    ids = G.get((int(p.x // 4), int(p.y // 4)))
    if ids is None: return False
    if any(inside(q, p.x, p.y) for q in KEEP_EXCEPT): return False
    m = ids[(lo[ids, 0] - pad <= p.x) & (hi[ids, 0] + pad >= p.x) & (lo[ids, 1] - pad <= p.y) & (hi[ids, 1] + pad >= p.y) & (zl[ids] - zpad <= p.z) & (zh[ids] + zpad >= p.z)]
    for t in A[m]:
        (ax, ay), (bx, by), (cx, cy) = t[:, :2]
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) > 1e-9:
            l1 = ((by - cy) * (p.x - cx) + (cx - bx) * (p.y - cy)) / d; l2 = ((cy - ay) * (p.x - cx) + (ax - cx) * (p.y - cy)) / d
            if min(l1, l2, 1 - l1 - l2) >= -1e-6: return True
        for (x0, y0), (x1, y1) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)), ((cx, cy), (ax, ay))):   # near an edge (walls stand on them)
            dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
            s_ = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p.x - x0) * dx + (p.y - y0) * dy) / L2))
            if (p.x - x0 - s_ * dx) ** 2 + (p.y - y0 - s_ * dy) ** 2 <= pad * pad: return True
    return False
def _bend(bm, sel, B, world, toloc, tonrm, keep):
    """clone kind 'bend': the source strip (faces `sel`, laid along the straight line a -> b) copied along a curved path. Each copy
    covers one source length of the path; a vertex at distance s along a -> b and dl to its left goes to path(s + k L) + dl * the
    path's left normal there, its height shifted by path z - z0. The source is first cut every `step` m across the line so the copy
    bends smoothly; the last copy is cut at the path's end. Returns the face count made (all protected)."""
    import math
    a = Vector((*B['a'][:2], 0.0)); b = Vector((*B['b'][:2], 0.0)); t = (b - a); Ls = t.length; t.normalize(); nl = Vector((-t.y, t.x, 0.0))
    P = [Vector(p) for p in B['path']]; arc = [0.0]
    for p0, p1 in zip(P, P[1:]): arc.append(arc[-1] + (p1.xy - p0.xy).length)
    total = arc[-1]
    def at(sv):
        sv = min(max(sv, 0.0), total)
        for i in range(len(P) - 1):
            if arc[i + 1] >= sv or i == len(P) - 2:
                f = (sv - arc[i]) / max(arc[i + 1] - arc[i], 1e-9); q = P[i].lerp(P[i + 1], f); d = (P[i + 1] - P[i]); d.z = 0; d.normalize()
                return q, Vector((-d.y, d.x, 0.0))
    geom = list({g for f in sel for g in [f] + list(f.edges) + list(f.verts)})
    k = 1
    while k * B['step'] < Ls:                                                     # cut the source across its line every step
        res = bmesh.ops.bisect_plane(bm, geom=[g for g in geom if g.is_valid], plane_co=toloc(a + t * (k * B['step'])), plane_no=tonrm(t))
        geom = list({g for g in geom if g.is_valid} | set(res['geom'])); k += 1
    src = [g for g in geom if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    n = 0; copies = int(math.ceil(total / Ls))
    for c in range(copies):
        dup = bmesh.ops.duplicate(bm, geom=src)['geom']
        if (c + 1) * Ls > total:                                                  # the last copy ends where the path ends
            res = bmesh.ops.bisect_plane(bm, geom=dup, plane_co=toloc(a + t * (total - c * Ls)), plane_no=tonrm(t))
            dup = list(set(dup) | set(res['geom']))
            dead = [f for f in dup if isinstance(f, bmesh.types.BMFace) and f.is_valid and (world(f.calc_center_median()).xy - a.xy).dot(t.xy) > total - c * Ls]
            bmesh.ops.delete(bm, geom=dead, context='FACES')
        dv = {g for g in dup if isinstance(g, bmesh.types.BMVert) and g.is_valid}
        for v in dv:
            p = world(v.co); sv = (p.xy - a.xy).dot(t.xy); dl = (p.xy - a.xy).dot(nl.xy)
            q, nn = at(sv + c * Ls)
            zs = B['z0'] if B.get('z0') is not None else B['a'][2] + (B['b'][2] - B['a'][2]) * min(max(sv / Ls, 0.0), 1.0)   # his foot height there
            v.co = toloc(Vector((q.x + nn.x * dl, q.y + nn.y * dl, p.z - zs + q.z)))
        for f in dup:
            if isinstance(f, bmesh.types.BMFace) and f.is_valid: f[keep] = 1; n += 1
    return n
def apply(bm, world, toloc, tonrm, matname, name=None, collision=False, report=None):
    """world(co) -> world Vector; toloc(world point) -> local co; tonrm(world dir) -> local dir; matname(face) -> material name."""
    keep = keep_layer(bm); rep = report if report is not None else {}; _WORLD[0] = world
    cen = lambda f: world(f.calc_center_median())
    if collision and KEEP_TRIS:                                        # ---- keep: the collision of a feature we keep whole
        n = 0
        for f in bm.faces:
            if not f[keep] and on_kept(cen(f)): f[keep] = 1; n += 1
        if n: rep['keep: collision of kept features'] = rep.get('keep: collision of kept features', 0) + n
    for r in rules_for('move', name, collision):                       # ---- move
        if collision: n = _move(bm, world, toloc, matname, r, r['col_z'], None, r.get('col_nz_max', 1.0), r['top'])
        else: n = _move(bm, world, toloc, matname, r, r['z'], r.get('mat'), 1.0, r['top'])
        if n: rep[r['name']] = rep.get(r['name'], 0) + n
    for r in rules_for('cut', name, collision):                        # ---- cut
        z0, z1 = r['z']; mat = r.get('mat'); over = R.get('b_tarmac') if r.get('over') else None
        for poly in _polys(r):
            xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
            vs = [world(v.co) for v in bm.verts]
            if not vs or max(p.x for p in vs) < min(xs) or min(p.x for p in vs) > max(xs) or max(p.y for p in vs) < min(ys) or min(p.y for p in vs) > max(ys): continue
            _bisect(bm, None, poly, toloc, tonrm)
            dead = []
            for f in bm.faces:
                if f[keep]: continue
                p = cen(f)
                if not (z0 <= p.z <= z1 and inside(poly, p.x, p.y)): continue
                if mat and not re.search(mat, matname(f).lower()): continue
                if over is not None and not any(inside(q, p.x, p.y) for q in over): continue
                dead.append(f)
            if dead: bmesh.ops.delete(bm, geom=dead, context='FACES'); rep[r['name']] = rep.get(r['name'], 0) + len(dead)
    for r in rules_for('clone', name, collision):                      # ---- clone
        z0, z1 = r['z']; src = r['src']
        _bisect(bm, None, src, toloc, tonrm)
        sel = [f for f in bm.faces if not f[keep] and (lambda p: z0 <= p.z <= z1 and inside(src, p.x, p.y))(cen(f))]
        if not sel: continue
        if r.get('bend'):
            n = _bend(bm, sel, r['bend'], world, toloc, tonrm, keep); rep[r['name']] = rep.get(r['name'], 0) + n; continue
        for s in r['shifts']:
            dup = bmesh.ops.duplicate(bm, geom=sel)['geom']
            dv = [g for g in dup if isinstance(g, bmesh.types.BMVert)]
            for v in dv: v.co = toloc(world(v.co) + Vector((s[0], s[1], 0.0)))
            geom = _bisect(bm, dup, r['clip'], toloc, tonrm)
            df = [g for g in geom if isinstance(g, bmesh.types.BMFace) and g.is_valid]
            out = [f for f in df if not inside(r['clip'], *cen(f).xy)]
            bmesh.ops.delete(bm, geom=out, context='FACES')
            n = 0
            for f in df:
                if f.is_valid: f[keep] = 1; n += 1
            rep[r['name']] = rep.get(r['name'], 0) + n
    return rep
