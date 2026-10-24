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
def _bisect(bm, geom, poly, toloc, tonrm):
    for i in range(len(poly)):
        a, b = Vector((*poly[i], 0.0)), Vector((*poly[(i + 1) % len(poly)], 0.0)); d = (b - a).normalized()
        g = [e for e in geom if e.is_valid] if geom is not None else bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=g, plane_co=toloc(a), plane_no=tonrm(Vector((-d.y, d.x, 0.0))))
        if geom is not None: geom = list(set(geom) | set(res['geom']))
    return geom
def apply(bm, world, toloc, tonrm, matname, name=None, collision=False, report=None):
    """world(co) -> world Vector; toloc(world point) -> local co; tonrm(world dir) -> local dir; matname(face) -> material name."""
    keep = keep_layer(bm); rep = report if report is not None else {}
    cen = lambda f: world(f.calc_center_median())
    for r in rules_for('move', name, collision):                       # ---- move
        c = Vector((*r['centre'], 0.0)); z0, z1 = r['col_z'] if collision else r['z']; mat = None if collision else r.get('mat')
        nzm = r.get('col_nz_max', 1.0) if collision else 1.0
        sel = [f for f in bm.faces if not f[keep] and (lambda p: (p.xy - c.xy).length <= r['r'] and z0 <= p.z <= z1)(cen(f))
               and (not mat or re.search(mat, matname(f).lower())) and abs(_wnz(f, world)) <= nzm]
        if not sel: continue
        res = bmesh.ops.split(bm, geom=sel); faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
        sh = Vector(r['shift']); ztop, zto = r['top']
        for v in {v for f in faces for v in f.verts}:
            p = world(v.co) + sh
            if p.z > ztop: p.z = zto
            v.co = toloc(p)
        for f in faces: f[keep] = 1
        rep[r['name']] = rep.get(r['name'], 0) + len(faces)
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
