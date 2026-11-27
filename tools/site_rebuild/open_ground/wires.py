"""Power lines over the Block Boyz site. Rockstar's wires are merged meshes (cs4_rd_props_xwireNN), each holding many spans; a span is a
connected piece of the mesh. Its two ends = its two farthest points. An end is HELD when it is within HELD m in plan of a pole
(site_plan.poles(): every prop_telegraph near the site, the crossarm reaches ~2 m out); an end outside REGION (the site + 15 m)
counts as held (it is not ours to judge).
  * an end on a removed pole (site_plan.POLES_GONE) -> the span goes with the pole;
  * both ends held -> kept; but a drop (both ends on the same pole, one well below the other) on a pole on the site is kept only if
    another kept span starts at its foot (JOIN m): a drop whose feeder is gone would hang loose (drops on poles off the site are
    not ours to judge: their feeders may run outside the models we read);
  * an end free (on nothing) inside the cleared area -> it was fed to something the clearing took (the camp's lamps): the span goes.
    A free end outside the cleared area belongs to something that stays: kept.
Every kept span is checked: none may pass over the club (the roof + deck outline, site_plan.derived()['building']), none may come
within ARCH_CLEAR m of the arch (concept_v3.arch(), in world), and its lowest point over the site must stay SAG_MIN m over the new
grade (WIRES_SAG lines; the build fails on any).
Run:  blender -b --python wires.py -- <ydr name> [ends]
      ends: only lists the ends of this model's kept pole spans in ../site/wires/_ends/<name>.json (a drop's feeder can be in another
      model: wires_all.sh runs the ends pass over every model first, then the real pass)
Input ../vanilla/models/<name>.ydr (+ its placement, ../vanilla/models.tsv)   Output ../site/wires/<name>.ydr + <name>.json (every
span over the region: its ends and what happened to it); the .ydr only when something changed"""
import bpy, bmesh, sys, json, math
from pathlib import Path
from mathutils import Vector
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T)); import site_plan as SP, grade as GR, concept_v3 as C
M_ = T.parent; SRC = M_ / 'vanilla' / 'models'; OUT = M_ / 'site' / 'wires'; ENDS = OUT / '_ends'; ENDS.mkdir(parents=True, exist_ok=True)
xs = [p[0] for p in SP.SITE]; ys = [p[1] for p in SP.SITE]
REGION = (min(xs) - 15, max(xs) + 15, min(ys) - 15, max(ys) + 15)
HELD, DROP_DZ, JOIN, SAG_MIN, ARCH_CLEAR = 2.5, 1.5, 1.0, 5.0, 3.0
POLES = [(p[0], p[1], bool(p[4])) for p in SP.poles()]
BUILDING = SP.derived()['building']
ARCH = [Vector(SP.W(p)) for p in C.arch(120)]
args = sys.argv[sys.argv.index('--') + 1:]; name = args[0]; ENDS_ONLY = len(args) > 1 and args[1] == 'ends'
P = next(Vector([float(v) for v in r.split('\t')[2:5]]) for r in (M_ / 'vanilla' / 'models.tsv').read_text().splitlines() if r.split('\t')[0] == name)


def in_region(v): a, b, c, d = REGION; return a <= v.x <= b and c <= v.y <= d
def pole_of(v):
    """('pole', index) / ('gone', index) for the pole holding this end, ('out',) outside REGION, None if free."""
    if not in_region(v): return ('out',)
    d, i = min((math.hypot(v.x - x, v.y - y), i) for i, (x, y, _) in enumerate(POLES))
    return (('gone' if POLES[i][2] else 'pole'), i) if d <= HELD else None


bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ydr'}])
for m in bpy.data.materials:                                         # textures stay in Rockstar's dictionaries
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and hasattr(nd, 'texture_properties'): nd.texture_properties.embedded = False
FEED = [] if ENDS_ONLY else [Vector(e) for f in ENDS.glob('*.json') for e in json.load(open(f))]
if not ENDS_ONLY:
    for f in (OUT / f'{name}.ydr', OUT / f'{name}.json'): f.unlink(missing_ok=True)
report = []; ends = []; changed = 0; bad = []
for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.data.vertices]:
    mw = ob.matrix_world
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    # spans: connected pieces, joining vertices that share a position (the ribbon's two sides are separate vertices)
    key = {}; par = list(range(len(bm.verts)))
    def fd(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for v in bm.verts:
        k = tuple(round(c, 3) for c in v.co); j = key.setdefault(k, v.index); par[fd(v.index)] = fd(j)
    for e in bm.edges: par[fd(e.verts[0].index)] = fd(e.verts[1].index)
    comps = {}
    for v in bm.verts: comps.setdefault(fd(v.index), []).append(v)
    dead = []
    for comp in comps.values():
        W = [(mw @ u.co) + P for u in comp]
        step = max(1, len(W) // 40)
        i0, i1 = max(((i, j) for i in range(0, len(W), step) for j in range(0, len(W), step)), key=lambda ij: (W[ij[0]] - W[ij[1]]).length)
        e0, e1 = W[i0], W[i1]; p0, p1 = pole_of(e0), pole_of(e1)
        if not (in_region(e0) or in_region(e1) or any(in_region(w) for w in W[::step])): continue
        rec = {'ends': [[round(c, 2) for c in e] for e in (e0, e1)]}
        if any(p and p[0] == 'gone' for p in (p0, p1)): rec['fate'] = 'removed: on a removed pole'
        elif p0 is None or p1 is None:
            free = e0 if p0 is None else e1
            rec['fate'] = 'removed: its end was on something cleared' if SP.near_site(free.x, free.y, SP.CLEAR_MARGIN + 1.0) else 'kept: free end off the site'
        elif p0 == p1 and p0[0] == 'pole' and abs(e0.z - e1.z) > DROP_DZ and SP.near_site(*POLES[p0[1]][:2], SP.CLEAR_MARGIN + 1.0):
            foot = e0 if e0.z < e1.z else e1
            rec['fate'] = 'kept: drop' if ENDS_ONLY or any((foot - f).length <= JOIN for f in FEED) else 'removed: a drop whose feeder is gone'
        else: rec['fate'] = 'kept'
        if rec['fate'].startswith('removed'): dead.extend(comp); changed += 1
        else:
            if not rec['fate'].startswith('kept: drop'): ends.extend([list(e0), list(e1)])
            over = [w for w in W if SP.on_site(w.x, w.y)]
            if over:
                low = min(over, key=lambda w: w.z - GR.grade_z(w.x, w.y)); clr = low.z - GR.grade_z(low.x, low.y)
                rec['clearance_over_site'] = round(clr, 2)
                if clr < SAG_MIN: bad.append(f'WIRES_SAG {name} {rec["ends"]} {clr:.2f} m over the ground at {low.x:.1f},{low.y:.1f}')
            if any(SP.inpoly(w.x, w.y, BUILDING) for w in W): bad.append(f'WIRES_OVER_BUILDING {name} {rec["ends"]}')
            da = min((w - a).length for w in W[::max(1, step // 2)] for a in ARCH)
            rec['arch_clearance'] = round(da, 2)
            if da < ARCH_CLEAR: bad.append(f'WIRES_ARCH {name} {rec["ends"]} {da:.2f} m from the arch')
        report.append(rec)
    if dead: bmesh.ops.delete(bm, geom=list({u for u in dead}), context='VERTS')
    bm.to_mesh(ob.data); bm.free()
if ENDS_ONLY:
    json.dump([[round(c, 3) for c in e] for e in ends], open(ENDS / f'{name}.json', 'w')); print('WIRES_ENDS', name, len(ends), flush=True); sys.exit(0)
for b in bad: print(b, flush=True)
json.dump(report, open(OUT / f'{name}.json', 'w'), indent=1)
if not changed: print('WIRES_UNCHANGED', name, len(report), 'spans in the region', flush=True); sys.exit(0)
root = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable' and o.parent is None)
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('WIRES_PASS', name, sum(1 for r in report if r['fate'].startswith('removed')), 'removed', sum(1 for r in report if r['fate'].startswith('kept')), 'kept', flush=True)
