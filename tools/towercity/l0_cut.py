"""Tower City level 0: cut vanilla ground / plaza / decal drawables along the lot outlines (plan/lot_polys.json).
Faces inside a lot are deleted, faces outside it (the kept perimeter sidewalk, the roads) stay. Every face that crosses the
lot edge is first split along the edge so only its inside part goes (no wedges, no gaps). Run headless:
  blender -b --factory-startup? (no: Sollumz is a user extension) -> blender -b --python l0_cut.py -- name1 name2 ...
Also cuts model-specific polygons from plan/curb_cuts.json (e.g. the kerb + gutter under the level-1 driveway apron).
Models listed in plan/footprint_cuts.json (written by tower_garage.py) are cut by THEIR polygons only, never by the lot outlines
(the west lot's outline takes in the freeway off-ramp: the freeway road inside the podium is cut by the podium's outline).
Dry run (no export, nothing written; prints each model's dead / kept faces and where the dead ones lie):  ... -- --dry name1 ...
Input: src/native/<name>.ydr  (+ its entity position from src/ymap)  Output: work/cut/<name>.ydr (shaders put back after);
the dead/kept face counts are recorded in work/l0_cut_result.json 'cut' (the list assemble.sh streams).
Exterior clean-up rules (plan/ext_cuts.json from ext_plan.py, applied by ext_rules.py before the lot cut): model-specific cuts in a
polygon + height band (+ material), clones of Rockstar's own geometry across a closed gap, moved faces (the driveway pillar).
Faces a rule moved or cloned are protected from every later cut. Models in its 'ext_only' list are cut by these rules only."""
import bpy, bmesh, sys, json, re, glob
sys.path.insert(0, 'C:/Users/anton/Documents/Codex/TowerCity/work')
import ext_rules as ER
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); SRC = T / 'src/native'; OUT = T / 'work/cut'; OUT.mkdir(parents=True, exist_ok=True)
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
POLYS = [[Vector((x, y, 0)) for x, y in v] for v in json.load(open(T / 'plan/lot_polys.json')).values()]
CURB = {k: [[Vector((x, y, 0)) for x, y in p] for p in v] for k, v in json.load(open(T / 'plan/curb_cuts.json')).items()}
FOOT = {k: [[Vector((x, y, 0)) for x, y in p] for p in v] for k, v in json.load(open(T / 'plan/footprint_cuts.json')).items()} if (T / 'plan/footprint_cuts.json').exists() else {}
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
def entity_pos(name):
    for f in glob.glob(str(T / 'src/ymap/*.ymap.xml')):
        for e in E.parse(f).getroot().iter('Item'):
            if (e.findtext('archetypeName') or '').lower() == name:
                p = e.find('position'); return Vector((float(p.get('x')), float(p.get('y')), float(p.get('z'))))
    if name.startswith('hei_'): return entity_pos(name[4:])
    raise SystemExit('no entity for ' + name)
names = sys.argv[sys.argv.index('--') + 1:]
DRY = '--dry' in names; names = [n for n in names if n != '--dry']
rep = {}; DEAD = {}; EXTREP = {}
for name in names:
    org = entity_pos(name); polys = (FOOT[name] if name in FOOT else ([] if name in ER.EXT_ONLY else POLYS)) + CURB.get(name, [])
    bpy.ops.wm.read_homefile(use_empty=True)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ydr'}])
    root = bpy.data.objects[name]; meshes = set()
    for m in [c for c in root.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        for lv in (LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW):
            l = m.sz_lods.get_lod(lv)
            if l is not None and l.mesh is not None: meshes.add((m.name, l.mesh.name))
    dead_n = kept_n = 0; dlo = [1e9] * 3; dhi = [-1e9] * 3
    for mn, me_name in meshes:
        me = bpy.data.meshes[me_name]; mw = bpy.data.objects[mn].matrix_world
        bm = bmesh.new(); bm.from_mesh(me)
        if not bm.verts: bm.free(); continue
        inv0 = mw.inverted(); inv03 = inv0.to_3x3()
        mats = [m.name if m else '' for m in me.materials]
        ER.apply(bm, lambda co: (mw @ co) + org, lambda p: inv0 @ (p - org), lambda d: (inv03 @ d).normalized(),
                 lambda f: mats[f.material_index] if f.material_index < len(mats) else '', name=name, report=EXTREP.setdefault(name, {}))
        keep = ER.keep_layer(bm)
        if not bm.verts: bm.to_mesh(me); bm.free(); continue          # the exterior rules took the whole mesh
        lo = Vector((min((mw @ v.co).x for v in bm.verts), min((mw @ v.co).y for v in bm.verts), 0)) + org
        hi = Vector((max((mw @ v.co).x for v in bm.verts), max((mw @ v.co).y for v in bm.verts), 0)) + org
        inv = mw.inverted(); inv3 = inv.to_3x3()
        for poly in polys:
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                if max(a.x, b.x) < lo.x - 1 or min(a.x, b.x) > hi.x + 1 or max(a.y, b.y) < lo.y - 1 or min(a.y, b.y) > hi.y + 1: continue
                d = (b - a).normalized(); nrm = Vector((-d.y, d.x, 0))
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=inv @ (a - org), plane_no=(inv3 @ nrm).normalized())
        dead = [f for f in bm.faces if not f[keep] and any(inside(p, *((mw @ f.calc_center_median()) + org).xy) for p in polys)]
        dead_n += len(dead); kept_n += len(bm.faces) - len(dead)
        for f in dead:
            c = (mw @ f.calc_center_median()) + org
            for k in range(3): dlo[k] = min(dlo[k], c[k]); dhi[k] = max(dhi[k], c[k])
            DEAD.setdefault(name, []).append([round(c.x, 3), round(c.y, 3), round(c.z, 3)])
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free()
    rep[name] = (dead_n, kept_n)
    if DRY: print('L0_CUT_EXT', name, json.dumps(EXTREP.get(name, {})), flush=True)
    if DRY: print('L0_CUT_DRY', name, 'footprint' if name in FOOT else 'lot', 'dead', dead_n, 'kept', kept_n, 'dead centres', [round(x, 2) for x in dlo], [round(x, 2) for x in dhi], flush=True); continue
    bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
if DRY: json.dump(DEAD, open(T / 'work/l0_cut_dry.json', 'w')); raise SystemExit(0)   # the dead faces' centres, for checking
R = T / 'work/l0_cut_result.json'; res = json.load(open(R)); res['cut'].update(rep); json.dump(res, open(R, 'w'), indent=1)
print('L0_CUT_EXT', json.dumps({k: v for k, v in EXTREP.items() if v}), flush=True)
print('L0_CUT_PASS', json.dumps(rep), flush=True)
