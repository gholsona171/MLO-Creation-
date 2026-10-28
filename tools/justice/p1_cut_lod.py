"""Justice Center phase 1: cut the block out of Rockstar's district LOD models (drawable dictionaries .ydd or single .ydr), from Tower City
work/l0_cut_lod.py. Every mesh of the named drawables (all drawables if none named) is split along the polygon's edges (bmesh
bisect) and the faces inside are deleted; nothing is added.
  default polygon: the lot outline (plan/lot_poly.json) - the block's SLOD2 sc1_lod_19, the district SLOD3 sc1_lod_slod4, the night
                   emissive SLOD2 / SLOD3s
  --inner:         the lot shrunk by the 4 m band (plan/lot_poly.json 'inner_world', lot_outline.py) - the road ymap's prop-combo LOD / SLOD1 models that p1_maps found partly
                   removed (work/p1_lod_partial.json): the props they still draw in the band are kept props, the ones inside are gone
  --dry:           nothing written; prints each drawable's dead / kept faces (use it to check which drawables of a dictionary reach in)
Each drawable is placed by its entity in the LOD ymaps (lr_sc1_lod, lr_sc1_rd, lr_sc1_19, src/ymap); hash-only names match by Jenkins hash.
Run: blender -b --python p1_cut_lod.py -- <file.ydd|file.ydr> [--inner] [--dry] [drawable names...]   Output: work/lodcut/<file>"""
import bpy, bmesh, sys, json
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter'); SRC = J / 'src/lod'; OUT = J / 'work/lodcut'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(J / 'work')); import jc_frame as F
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
args = sys.argv[sys.argv.index('--') + 1:]
INNER = '--inner' in args; DRY = '--dry' in args; args = [a for a in args if not a.startswith('--')]
fname, want = args[0], set(a.lower() for a in args[1:])
LP = json.load(open(J / 'plan/lot_poly.json'))
POLY = [Vector((p[0], p[1], 0)) for p in (LP['inner_world'] if INNER else LP['world'])]
def joaat(t):
    h = 0
    for ch in t.lower().encode():
        h = (h + ch) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF; return h
ORG = {}
for ym in ('lr_sc1_lod', 'lr_sc1_rd', 'lr_sc1_19'):
    for e in E.parse(J / f'src/ymap/{ym}.ymap.xml').getroot().iter('Item'):
        a = (e.findtext('archetypeName') or '').lower(); p = e.find('position')
        if a and p is not None and a not in ORG:
            v = Vector((float(p.get('x')), float(p.get('y')), float(p.get('z')))); ORG[a] = v; ORG['hash_%08x' % joaat(a)] = v
def inside(x, y):
    c = False; n = len(POLY)
    for i in range(n):
        a, b = POLY[i], POLY[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': fname}])
top = [o for o in bpy.data.objects if o.parent is None][0]
drawables = [o for o in ([top] + list(top.children_recursive)) if o.sollum_type == 'sollumz_drawable']
rep = {}
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
    dead_n = kept_n = 0; zr = [1e9, -1e9]
    for mn, me_name in meshes:
        me = bpy.data.meshes[me_name]; mw = bpy.data.objects[mn].matrix_world
        bm = bmesh.new(); bm.from_mesh(me)
        if not bm.verts: bm.free(); continue
        vs = [(mw @ v.co) + org for v in bm.verts]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), 0)); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), 0))
        inv = mw.inverted(); inv3 = inv.to_3x3()
        for i in range(len(POLY)):
            a, b = POLY[i], POLY[(i + 1) % len(POLY)]
            if max(a.x, b.x) < lo.x - 1 or min(a.x, b.x) > hi.x + 1 or max(a.y, b.y) < lo.y - 1 or min(a.y, b.y) > hi.y + 1: continue
            dd = (b - a).normalized(); nrm = Vector((-dd.y, dd.x, 0))
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=inv @ (a - org), plane_no=(inv3 @ nrm).normalized())
        dead = [f for f in bm.faces if inside(*((mw @ f.calc_center_median()) + org).xy)]
        dead_n += len(dead); kept_n += len(bm.faces) - len(dead)
        for f in dead: zz = ((mw @ f.calc_center_median()) + org).z; zr[0] = min(zr[0], zz); zr[1] = max(zr[1], zz)
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free()
    rep[dn] = [dead_n, kept_n] + ([round(zr[0], 1), round(zr[1], 1)] if dead_n else [])
if not DRY:
    bpy.ops.object.select_all(action='DESELECT'); top.select_set(True); bpy.context.view_layer.objects.active = top
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('P1_LODCUT_DRY' if DRY else 'P1_LODCUT_PASS', fname, 'inner' if INNER else 'lot', json.dumps(rep), flush=True)
