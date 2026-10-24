"""Tower City level 0: the ground of each cleared lot (drawable tc_lot_<lot> + collision tc_lot_<lot>_col) and the shared empty
model tc_empty swapped in for every removed vanilla entity.
EDGE (2026-10-24, Antonio: a tan strip round the building bases hovering over the sidewalk): the edge is plan/lot_edge_dense.json
(lot_ground.py: every 0.5 m, the height of the ground 0.25 m outside - our exterior paving or Rockstar's own sidewalk). The old
edge had a height at the outline's corners only (up to 99 m apart): on Alta St it stood up to 1 m over the sidewalk.
INSIDE: draped from the edge on a 2 m grid - each inner node takes the inverse-distance (d^-3) mean of the edge heights, so the
strip between a building and the street is the street's own height, rising or falling with it (playbook: drape a lot on its
own ground). The edge itself is never moved. A 0.6 m skirt runs down the drawn edge (no slit where a kerb dips).
SURFACE: paving_mat.py (light grey 1 m flags, the read of the sidewalk round it - the old tan concrete read as a ring).
Authored in world space, then moved so each drawable is centred on its own origin (entity origin = lot centre).
Run: blender -b --python l0_slab.py"""
import bpy, bmesh, sys, json, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); OUT = T / 'work/slab'; OUT.mkdir(parents=True, exist_ok=True)
W = Path(r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work'); sys.path.insert(0, str(W))
bpy.ops.wm.read_homefile(use_empty=True)
coll = bpy.data.collections.new('Collection'); bpy.context.scene.collection.children.link(coll)
import v13_kit as K, v13_materials as M
from bl_ext.user_default.sollumz.sollumz_properties import SollumType
from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index
from bl_ext.user_default.sollumz.tools.boundhelper import convert_objs_to_single_composite
sys.path.insert(0, str(T / 'work')); import paving_mat
conc = paving_mat.make(M)
EDGE = json.load(open(T / 'plan/lot_edge_dense.json'))
def export(root):
    bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
GRID = 2.0
def slab_mesh(pts, mat, skirt, holes=()):
    bm = bmesh.new(); vs = [bm.verts.new(Vector((x, y, z + 0.01))) for x, y, z in pts]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for k in range(int(np.floor(min(xs) / GRID)) + 1, int(np.ceil(max(xs) / GRID))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((k * GRID, 0, 0)), plane_no=Vector((1, 0, 0)))
    for k in range(int(np.floor(min(ys) / GRID)) + 1, int(np.ceil(max(ys) / GRID))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k * GRID, 0)), plane_no=Vector((0, 1, 0)))
    edge = {v for e in bm.edges if e.is_boundary for v in e.verts}           # the outline (bisect points on it are linear between samples)
    E = np.array(pts, np.float64)
    inner = [v for v in bm.verts if v not in edge]
    if inner:
        P = np.array([tuple(v.co.xy) for v in inner])
        d = np.sqrt(((P[:, None, :] - E[None, :, :2]) ** 2).sum(-1)) + 0.05
        w = d ** -3; z = (w * E[None, :, 2]).sum(1) / w.sum(1) + 0.01
        for v, zz in zip(inner, z): v.co.z = float(zz)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    if skirt:                                                              # down the drawn edge, following its (subdivided) outline
        be = [e for e in bm.edges if e.is_boundary]
        res = bmesh.ops.extrude_edge_only(bm, edges=be)
        for v in [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]: v.co.z -= skirt
        bm.normal_update()
    for hole in holes:                                      # openings for later levels (plan/slab_holes.json)
        hp = [Vector((x, y, 0)) for x, y in hole]
        for i in range(len(hp)):
            a, b = hp[i], hp[(i + 1) % len(hp)]; dd = (b - a).normalized()
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=a, plane_no=Vector((-dd.y, dd.x, 0)))
        dead = [f for f in bm.faces if f.normal.z > 0.5 and in_poly(hp, f.calc_center_median())]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    me = bpy.data.meshes.new('slab'); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new('slab', me); bpy.context.scene.collection.objects.link(o); return o
def in_poly(poly, p):
    c = False; n_ = len(poly)
    for i in range(n_):
        a, b = poly[i], poly[(i + 1) % n_]
        if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
HOLES = json.load(open(T / 'plan/slab_holes.json')) if (T / 'plan/slab_holes.json').exists() else {}
info = {}
for lot, raw in EDGE.items():
    pts = [tuple(p) for p in raw]
    c = Vector((float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts])), float(np.mean([p[2] for p in pts]))))
    vis = slab_mesh(pts, conc, 0.6, HOLES.get(lot, [])); vis.data.transform(Matrix.Translation(-c))
    root, lo, hi = K.new_drawable(f'tc_lot_{lot}', [vis], uv=0.25)
    for o in root.children_recursive:                       # exterior model: vertex colour 1 (interior values crush outdoor light)
        if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model':
            for a in o.data.color_attributes: cc = np.ones(len(a.data) * 4, np.float32); a.data.foreach_set('color', cc)
    export(root)
    tri = []                                                # its triangles (world space) for the sweep / fly checks (tc_kit exports the same)
    for o in root.children_recursive:
        if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model':
            me = o.data; me.calc_loop_triangles(); M4 = Matrix.Translation(c) @ o.matrix_world
            V = np.array([tuple(M4 @ v.co) for v in me.vertices], np.float32)
            if len(me.loop_triangles): tri.append(V[np.array([t.vertices[:] for t in me.loop_triangles], np.int64)])
    if tri: np.save(OUT / f'tris_tc_lot_{lot}.npy', np.concatenate(tri))
    col = slab_mesh(pts, create_collision_material_from_index(1), 0, HOLES.get(lot, []))      # 1 = CONCRETE
    comp = convert_objs_to_single_composite([col], SollumType.BOUND_GEOMETRYBVH, 'General (Default)')
    comp.name = f'tc_lot_{lot}_col'
    for o in comp.children_recursive: pass
    export(comp)
    info[lot] = {'origin': [c.x, c.y, c.z], 'bb_lo': list(lo), 'bb_hi': list(hi)}
tiny = np.full((8, 8, 4), .5, np.float32); tn = np.full((8, 8, 4), .5, np.float32); tn[:, :, 2] = 1
emptym = M.material('TC empty', 'tc_empty_px', tiny, tn, M.spec_from(np.full((8, 8, 4), .5, np.float32), .0, .0), .8, .0, 2)
root, lo, hi = K.new_drawable('tc_empty', [K.box((0, 0, -5.01), (.01, .01, -5.0), emptym)]); export(root)
info['tc_empty'] = {'bb_lo': list(lo), 'bb_hi': list(hi)}
json.dump(info, open(T / 'work/slab/slab_info.json', 'w'), indent=1)
print('L0_SLAB_PASS', json.dumps(info), flush=True)
