"""Tower City level 0: cut vanilla collision along the lot outlines (plan/lot_polys.json).
Triangles are split along the lot edges first; every face / primitive whose centre is inside a lot is deleted (the roads and
the kept perimeter sidewalk stay). Ground triangles left touching a lot lose their procedural id (no weeds through our slab:
the Cloud 9 lesson). Run one file per Blender process:  blender -b --python l0_col.py -- <name without .ybn>
Input src/game/<name>.ybn  Output work/col/<name>.ybn
Exterior clean-up rules (plan/ext_cuts.json, ext_rules.py, the rules marked 'col'): cut zones (the San Andreas branch, the PARKING
block), the deck-edge clone across the branch mouth and the moved driveway pillar are applied to every file BEFORE the lot cut;
a box primitive that reaches any rule area is turned into triangles first. Moved / cloned faces are protected from the lot cut."""
import bpy, bmesh, sys, json
sys.path.insert(0, 'C:/Users/anton/Documents/Codex/TowerCity/work')
import ext_rules as ER
from pathlib import Path
from mathutils import Vector
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); SRC = T / 'src/game'; OUT = T / 'work/col'; OUT.mkdir(parents=True, exist_ok=True)
POLYS = [[Vector((x, y, 0)) for x, y in v] for v in json.load(open(T / 'plan/lot_polys.json')).values()]
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
# Road collision (dt1_rd1 files): the ELEVATED road structure - the freeway, the off-ramp and its guard rails - is never ours to cut
# (2026-10-23: the lot outline reaches over the off-ramp's edge and the rail lost its collision: cars drove through it). Inside a
# lot only the road's ground-level collision goes; above ELEV it goes only inside our own building / bridge outlines
# (plan/footprint_cuts.json - the podium wing, the apron, the bridge mouth). Those outlines are cut in the other files too.
ELEV = 34.5                                                                        # every lot's ground is below this (survey: 28.2-33.7)
FOOT = [[Vector((x, y, 0)) for x, y in p] for v in json.loads((T / 'plan/footprint_cuts.json').read_text()).values() for p in v]     if (T / 'plan/footprint_cuts.json').exists() else []
ROAD = 'rd1' in sys.argv[sys.argv.index('--') + 1]
# a vanilla interior l0_maps removed from a lot (work/l0_mlo_gone.json): its collision (the file named after it, in the interior's
# own space) still loads through the game's interior registry - 2026-10-23: the Maze Bank car park's walls stood in our garage.
# Nothing of it is ours to keep, so everything in it is cut.
GONE = sys.argv[sys.argv.index('--') + 1] in json.loads((T / 'work/l0_mlo_gone.json').read_text())
def in_any(p):                                                    # our building / bridge outlines (FOOT) are cut in every file
    if GONE: return True
    if ROAD and p.z > ELEV: return any(inside(q, p.x, p.y) for q in FOOT)
    return any(inside(q, p.x, p.y) for q in POLYS + FOOT)
_NAME = sys.argv[sys.argv.index('--') + 1]
EXT_AREAS = [q for r in ER.rules_for('cut', _NAME, True) for q in ER._polys(r)] + [r['src'] for r in ER.rules_for('clone', _NAME, True)]
EXT_CIRC = [(Vector((*r['centre'], 0.0)), r['r'] + 0.5) for r in ER.rules_for('move', _NAME, True)]
def in_ext(p): return any(ER.inside(q, p.x, p.y) for q in EXT_AREAS) or ER.on_kept(p, 0.3, 2.0) or any((p.xy - c.xy).length <= rr for c, rr in EXT_CIRC)
def near_any(p, d=0.6): return any(in_any(p + Vector((dx, dy, 0))) for dx in (-d, 0, d) for dy in (-d, 0, d))
name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ybn'}])
ybn = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_bound_composite' and o.parent is None)
prim = tri = deproc = 0; boxcut = [0]; EXTREP = {}
# keeper: a copy of one box / triangle object pushed 80 m under ground, used only if the cut leaves the file empty
src = next((o for o in ybn.children_recursive if o.type == 'MESH' and o.sollum_type.startswith('sollumz_bound_poly_') and o.data.vertices), None)
keeper = src.copy(); keeper.data = src.data.copy(); bpy.context.scene.collection.objects.link(keeper); keeper.parent = src.parent
keeper.matrix_world = src.matrix_world.copy(); keeper.name = 'TC_KEEPER'
kz = min((keeper.matrix_world @ v.co).z for v in keeper.data.vertices)
for v in keeper.data.vertices: v.co = v.co * 0.01
keeper.location.z -= 80
# A box primitive can be long (the old Maze Bank plaza's east edge: one 100 m box at z 41.8-44.0 lay across the parking bridge,
# 2026-10-23), so its centre alone can't say whether it is ours to cut. Its footprint is sampled: all inside -> deleted; partly
# inside -> turned into triangles (its own 12) and cut along the lot / outline edges below like any triangle collision.
def footprint_samples(vs, n=12):
    out = []
    a, b, c, d = sorted(vs, key=lambda v: v.z)[:4] if len(vs) >= 8 else (vs + vs)[:4]
    base = [a, b, c, d]; cen = sum(base, Vector()) / 4
    for p in base:                                                # the four base corners, pulled in a hair, and the lines to the centre
        for k in range(n + 1): out.append(p.lerp(cen, 0.02 + 0.98 * k / n))
    for i in range(4):
        for j in range(i + 1, 4):
            for k in range(1, n): out.append(base[i].lerp(base[j], k / n).lerp(cen, 0.02))
    return out
for nm in [o.name for o in ybn.children_recursive if o.name != 'TC_KEEPER']:
    ob = bpy.data.objects.get(nm)
    if ob is None or ob.type != 'MESH' or ob.sollum_type != 'sollumz_bound_poly_box' or not ob.data.vertices: continue
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]; smp = footprint_samples(vs); hit = [in_any(p) for p in smp]
    ext = any(in_ext(p) for p in smp)
    if all(hit) and not ext: bpy.data.objects.remove(ob, do_unlink=True); prim += 1
    elif any(hit) or ext:
        bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
        ob.data.transform(ob.matrix_basis); ob.matrix_basis.identity()     # bake its size / turn in: the cut planes below assume no scale
        ob.sollum_type = 'sollumz_bound_poly_triangle'; boxcut[0] += 1
bpy.context.view_layer.update()                                   # refresh matrix_world after the bakes
for nm in [o.name for o in ybn.children_recursive if o.name != 'TC_KEEPER']:
    ob = bpy.data.objects.get(nm)
    if ob is None or ob.type != 'MESH' or not ob.data.vertices: continue
    mw = ob.matrix_world
    if ob.sollum_type.startswith('sollumz_bound_poly_') and ob.sollum_type != 'sollumz_bound_poly_triangle':
        vs = [mw @ v.co for v in ob.data.vertices]; c = sum(vs, Vector()) / len(vs)
        if in_any(c) and not ER.on_kept(c, 0.6, 1.0): bpy.data.objects.remove(ob, do_unlink=True); prim += 1   # (a kept feature's sphere / capsule stays)
    elif ob.sollum_type == 'sollumz_bound_poly_triangle':
        bm = bmesh.new(); bm.from_mesh(ob.data)
        inv0 = mw.inverted(); inv03 = inv0.to_3x3(); cm = [m.name if m else '' for m in ob.data.materials]
        ER.apply(bm, lambda co: mw @ co, lambda p: inv0 @ p, lambda d: (inv03 @ d).normalized(),
                 lambda f: cm[f.material_index] if f.material_index < len(cm) else '', name=name, collision=True, report=EXTREP)
        keep = ER.keep_layer(bm)
        if not bm.verts: bm.to_mesh(ob.data); bm.free(); continue
        vs = [mw @ v.co for v in bm.verts]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), 0)); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), 0))
        inv = mw.inverted(); inv3 = inv.to_3x3()
        for poly in POLYS + FOOT:
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                if max(a.x, b.x) < lo.x - 1 or min(a.x, b.x) > hi.x + 1 or max(a.y, b.y) < lo.y - 1 or min(a.y, b.y) > hi.y + 1: continue
                d = (b - a).normalized(); nrm = Vector((-d.y, d.x, 0))
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=inv @ a, plane_no=(inv3 @ nrm).normalized())
        bmesh.ops.triangulate(bm, faces=bm.faces[:])          # collision must stay all triangles after the bisects
        dead = [f for f in bm.faces if not f[keep] and in_any(mw @ f.calc_center_median())]
        tri += len(dead); bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(ob.data); bm.free()
        me = ob.data; clean = {}
        for f in me.polygons:
            m = me.materials[f.material_index]
            if m is None or m.collision_properties.procedural_id == 0: continue
            if near_any(mw @ f.center):
                if m.name not in clean:
                    c2 = m.copy(); c2.collision_properties.procedural_id = 0; me.materials.append(c2); clean[m.name] = len(me.materials) - 1
                f.material_index = clean[m.name]; deproc += 1
alive = any(o.type == 'MESH' and o.name != 'TC_KEEPER' and o.data.polygons for o in ybn.children_recursive)
if alive: bpy.data.objects.remove(keeper, do_unlink=True)
# drop what the cut emptied: triangle meshes with no faces left, then geometry bounds with nothing left under them
for ob in [o for o in ybn.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_bound_poly_triangle' and not o.data.polygons]:
    bpy.data.objects.remove(ob, do_unlink=True)
for ob in [o for o in ybn.children_recursive if o.sollum_type in ('sollumz_bound_geometrybvh', 'sollumz_bound_geometry')]:
    if not any(c.type == 'MESH' and c.data.vertices for c in ob.children_recursive) and not (ob.type == 'MESH' and ob.data.vertices):
        for c in list(ob.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(ob, do_unlink=True)
BVH_MAX = 32000                                                    # Sollumz refuses a BVH child over 32,767 primitives
def split_bvh(bvh):
    """the exterior rules' cuts and clones (the bent kerb: cut every 0.5 m) can push one of Rockstar's BVH children over the limit:
    split it in two halves at the triangles' median x, as sibling children of the same composite (playbook 02, wow2easy site_col)."""
    tris = [c for c in bvh.children if c.type == 'MESH' and c.sollum_type == 'sollumz_bound_poly_triangle']
    if sum(len(c.data.polygons) for c in tris) <= BVH_MAX: return 0
    xs = sorted((c.matrix_world @ p.center).x for c in tris for p in c.data.polygons); cut = xs[len(xs) // 2]
    twin = bvh.copy()
    if bvh.data is not None: twin.data = bvh.data.copy()
    for col in bvh.users_collection: col.objects.link(twin)
    twin.parent = bvh.parent; twin.matrix_world = bvh.matrix_world.copy()
    for c in tris:
        part = c.copy(); part.data = c.data.copy()
        for col in c.users_collection: col.objects.link(part)
        part.parent = twin; part.matrix_world = c.matrix_world.copy()
        for ob_, keep_east in ((c, False), (part, True)):
            bm = bmesh.new(); bm.from_mesh(ob_.data); mw_ = ob_.matrix_world
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if ((mw_ @ f.calc_center_median()).x >= cut) != keep_east], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            bm.to_mesh(ob_.data); bm.free()
        if not part.data.polygons: bpy.data.objects.remove(part, do_unlink=True)
    return 1 + split_bvh(bvh) + split_bvh(twin)
splits = sum(split_bvh(o) for o in [o for o in ybn.children_recursive if o.sollum_type == 'sollumz_bound_geometrybvh'])
if splits: print('L0_COL_BVH_SPLITS', name, splits, flush=True)
ybn.name = name
bpy.ops.object.select_all(action='DESELECT'); ybn.select_set(True); bpy.context.view_layer.objects.active = ybn
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('L0_COL_EXT', name, json.dumps(EXTREP), flush=True)
print('L0_COL_PASS', json.dumps({name: [prim, tri, deproc, 'boxes cut ' + str(boxcut[0]), 'kept' if alive else 'EMPTY->keeper']}), flush=True)
