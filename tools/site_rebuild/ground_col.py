"""The site's own ground collision (site_col.py cuts everything Rockstar had on the site: the Vinewood Bowl's seating rows were box
primitives with no ground under them). One static collision file, bb_site_col.ybn:
  * a GRID m lattice over the site (site_plan.SITE) grown by REACH, two triangles per cell, every vertex on the new grade (1 m,
    the drawn ground's own cells: on a 2 m grid the collision parted from the drawn ground by up to 0.6 m where the flat lot
    bends into a bank)
    (grade.grade_z: flat at site_plan.PAD_Z under the club + apron, the lot's plane, the banks and the seating slope). Past the
    outline the grade is Rockstar's own ground, so the strip outside meets the collision left there without a step.
  * each triangle's material: site_plan.LOT_MATERIAL (the blacktop) when its centre is on the paved lot, else
    site_plan.VERGE_MATERIAL (the banks and the old seating slope), no procedural grass.
  * one BVH child per TILE m square (Sollumz refuses more than 32,767 triangles in one).
Run: blender -b --python ground_col.py     Output ../site/col/bb_site_col.ybn (+ ground_col.json)"""
import bpy, bmesh, sys, json, math
from pathlib import Path
from mathutils import Vector
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, grade as GR
from bl_ext.user_default.sollumz.sollumz_properties import SollumType
from bl_ext.user_default.sollumz.tools.boundhelper import convert_objs_to_single_composite
from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index, collisionmats
M = T.parent; OUT = M / 'site' / 'col'; OUT.mkdir(parents=True, exist_ok=True)
GRID, REACH, TILE, NAME = 1.0, 1.5, 64.0, 'bb_site_col'
OFF = json.load(open(M / 'site' / 'grade.json'))['origin'][0] % GRID   # nodes ON the grade's lattice (half a metre off): no re-cut bends
(OUT / f'{NAME}.ybn').unlink(missing_ok=True)
bpy.ops.wm.read_homefile(use_empty=True)
coll = bpy.data.collections.new('Collection'); bpy.context.scene.collection.children.link(coll)


def material(nm):
    i = next(k for k, m in enumerate(collisionmats) if m.name.upper() == nm)
    m = create_collision_material_from_index(i); m.collision_properties.procedural_id = 0; return m


MAT = {'lot': material(SP.LOT_MATERIAL), 'verge': material(SP.VERGE_MATERIAL)}
S = SP.SITE; xs = [p[0] for p in S]; ys = [p[1] for p in S]
def reached(x, y): return SP.on_site(x, y) or SP.seg_dist(x, y, S) <= REACH
i0, i1 = int(math.floor((min(xs) - REACH) / GRID)), int(math.ceil((max(xs) + REACH) / GRID))
j0, j1 = int(math.floor((min(ys) - REACH) / GRID)), int(math.ceil((max(ys) + REACH) / GRID))
tiles, Z = {}, {}
def z(i, j):
    if (i, j) not in Z: Z[(i, j)] = GR.grade_z(i * GRID + OFF, j * GRID + OFF)
    return Z[(i, j)]
st = {'cells': 0, 'lot_tris': 0, 'verge_tris': 0}
for i in range(i0, i1):
    for j in range(j0, j1):
        cx, cy = (i + .5) * GRID + OFF, (j + .5) * GRID + OFF
        if not any(reached(x + OFF, y + OFF) for x, y in ((cx - OFF, cy - OFF), (i * GRID, j * GRID), ((i + 1) * GRID, j * GRID), (i * GRID, (j + 1) * GRID), ((i + 1) * GRID, (j + 1) * GRID))):
            continue
        key = (int(math.floor(cx / TILE)), int(math.floor(cy / TILE)))
        if key not in tiles: tiles[key] = bmesh.new()
        bm = tiles[key]; st['cells'] += 1
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        V = [bm.verts.new(Vector((a * GRID + OFF, b * GRID + OFF, z(a, b)))) for a, b in q]
        for tri in ((0, 1, 2), (0, 2, 3)):
            f = bm.faces.new([V[k] for k in tri]); c = sum((V[k].co for k in tri), Vector()) / 3
            lot = SP.on_lot(c.x, c.y); f.material_index = 0 if lot else 1; st['lot_tris' if lot else 'verge_tris'] += 1
objs = []
for (ti, tj), bm in sorted(tiles.items()):
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    me = bpy.data.meshes.new(f'{NAME}_{ti}_{tj}'); bm.to_mesh(me); bm.free()
    me.materials.append(MAT['lot']); me.materials.append(MAT['verge'])
    o = bpy.data.objects.new(me.name, me); coll.objects.link(o); objs.append(o)
    assert len(me.polygons) <= 30000, f'tile {ti}, {tj}: {len(me.polygons)} triangles'
comp = convert_objs_to_single_composite(objs, SollumType.BOUND_GEOMETRYBVH, 'General (Default)'); comp.name = NAME
for gb in comp.children:
    mtx = gb.matrix_local.copy()
    for ch in gb.children:
        if ch.type == 'MESH': ch.data.transform(mtx @ ch.matrix_local); ch.matrix_local.identity()
    gb.matrix_local.identity()
bpy.ops.object.select_all(action='DESELECT'); comp.select_set(True); bpy.context.view_layer.objects.active = comp
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
assert (OUT / f'{NAME}.ybn').stat().st_size > 10000, f'{NAME}.ybn came out empty'
st['tiles'] = len(objs); json.dump(st, open(M / 'site' / 'ground_col.json', 'w'), indent=1)
print('GROUND_COL_PASS', json.dumps(st), flush=True)
