"""Tower City level 0: cut the two lots out of district LOD models (drawable dictionaries .ydd or single .ydr).
Every mesh of the named drawables (all drawables if none named) is split along the lot edges and faces inside a lot are
deleted. Each drawable is placed by its entity in dt1_lod.ymap or dt1_rd1.ymap (the road ymap holds the prop-combo SLOD1 / LOD
entities whose models live in the district dictionaries: l0_maps.py lists the partly removed ones in work/l0_lod_partial.json).
Exterior clean-up (plan/ext_cuts.json, ext_rules.apply_lod): a 'move' rule's 'lod' entries move the same piece in the LOD / SLOD
models that draw it from a distance (the driveway pillar: fwy02's LOD + the SLOD1 over it), before the lot cut; moved faces are
protected from the lot cut (the pillar's new spot straddles the lot edge).
Run: blender -b --python l0_cut_lod.py -- <file.ydd|file.ydr> [drawable names...]   Output: work/lodcut/<file>"""
import bpy, bmesh, sys, json
sys.path.insert(0, 'C:/Users/anton/Documents/Codex/TowerCity/work')
import ext_rules as ER
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); SRC = T / 'src/lod'; OUT = T / 'work/lodcut'; OUT.mkdir(parents=True, exist_ok=True)
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
POLYS = [[Vector((x, y, 0)) for x, y in v] for v in json.load(open(T / 'plan/lot_polys.json')).values()]
def joaat(t):
    h = 0
    for ch in t.lower().encode():
        h = (h + ch) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF; return h
ORG = {}
for ym in ('dt1_lod', 'dt1_rd1'):
    for e in E.parse(T / f'src/ymap/{ym}.ymap.xml').getroot().iter('Item'):
        a = (e.findtext('archetypeName') or '').lower(); p = e.find('position')
        if a and p is not None and a not in ORG:
            v = Vector((float(p.get('x')), float(p.get('y')), float(p.get('z')))); ORG[a] = v; ORG['hash_%08x' % joaat(a)] = v
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
def in_any(x, y): return any(inside(p, x, y) for p in POLYS)
args = sys.argv[sys.argv.index('--') + 1:]; fname, want = args[0], set(a.lower() for a in args[1:])
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': fname}])
top = [o for o in bpy.data.objects if o.parent is None][0]
drawables = [o for o in ([top] + list(top.children_recursive)) if o.sollum_type == 'sollumz_drawable']
rep = {}; EXTREP = {}
LODN = {n for r in ER.R.get('move', []) for l in r.get('lod', []) for n in l['names']}
for d in drawables:
    dn = d.name.split('.')[0].lower()
    if want and dn not in want and not any(dn == 'hash_%08x' % joaat(w) for w in want): continue
    org = ORG.get(dn)
    if org is None: rep[dn] = 'no entity'; continue
    meshes = set()
    for m in [c for c in d.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        for lv in (LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW):
            l = m.sz_lods.get_lod(lv)
            if l is not None and l.mesh is not None: meshes.add((m.name, l.mesh.name))
    dead_n = kept_n = 0
    for mn, me_name in meshes:
        me = bpy.data.meshes[me_name]; mw = bpy.data.objects[mn].matrix_world
        bm = bmesh.new(); bm.from_mesh(me)
        if not bm.verts: bm.free(); continue
        inv0 = mw.inverted(); mats = [m.name if m else '' for m in me.materials]
        names = {dn} | {w for w in want if 'hash_%08x' % joaat(w) == dn}
        ER.apply_lod(bm, lambda co: (mw @ co) + org, lambda p: inv0 @ (p - org),
                     lambda f: mats[f.material_index] if f.material_index < len(mats) else '', names, report=EXTREP.setdefault(dn, {}))
        keep = ER.keep_layer(bm)
        if names & LODN: bm.to_mesh(me); bm.free(); continue          # an exterior rule's LOD (its HD model is ext_only): moved, never lot-cut
        vs = [(mw @ v.co) + org for v in bm.verts]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), 0)); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), 0))
        inv = mw.inverted(); inv3 = inv.to_3x3()
        for poly in POLYS:
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                if max(a.x, b.x) < lo.x - 1 or min(a.x, b.x) > hi.x + 1 or max(a.y, b.y) < lo.y - 1 or min(a.y, b.y) > hi.y + 1: continue
                dd = (b - a).normalized(); nrm = Vector((-dd.y, dd.x, 0))
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=inv @ (a - org), plane_no=(inv3 @ nrm).normalized())
        dead = [f for f in bm.faces if not f[keep] and in_any(*((mw @ f.calc_center_median()) + org).xy)]
        dead_n += len(dead); kept_n += len(bm.faces) - len(dead)
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free()
    rep[dn] = [dead_n, kept_n]
bpy.ops.object.select_all(action='DESELECT'); top.select_set(True); bpy.context.view_layer.objects.active = top
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('L0_LODCUT_EXT', fname, json.dumps({k: v for k, v in EXTREP.items() if v}), flush=True)
print('L0_LODCUT_PASS', fname, json.dumps(rep), flush=True)
