"""Justice Center phase 1: the cleared lot's ground (drawable jc_lot + collision jc_lot_col) and the shared empty model jc_empty swapped
in for every removed vanilla entity. Adapted from Tower City work/l0_slab.py; rebuilt from source every run (work/slab is wiped).
EDGE: the lot outline is Rockstar's own back-of-sidewalk line (lot_outline.py: every vertex of his edge, z = his sidewalk's height there),
split every <= 1 m along his straight edge lines (jc_frame.edge_pts). The slab's edge therefore lies exactly on his sidewalk's edge, at his
height, vertex for vertex: no step, no slit, no overlap (doc 02: a 1 cm step at an open edge reads as a crack).
INSIDE: draped from the edge on a 2 m grid (jc_frame.slab_z: inverse-distance d^-3 mean of the edge heights): the lot stays at the
sidewalks' grade (z 28.24 - 28.43); the planned ground floor (z 28.8) is the next phase's. A 0.6 m skirt runs down the drawn edge.
SURFACE: Rockstar's own sidewalk im_sidewalk012 (sidewalk_mat.py: his material, texture names, UV scale + direction, vertex colours);
his textures bind through the archetype's txd sc1_rd_road (p1_maps.py).
COLLISION: the same draped mesh (game material 1 CONCRETE, his sidewalk's), plus a 0.5 m apron outward under the sidewalk, 3 cm below
the edge: wherever his street collision stops short of his drawn edge (Tower City: 0.35 m) the foot still meets ground; where his
collision is there, it is higher and wins.
Authored in world space, then moved so the drawable is centred on its own origin (entity origin = lot centre).
Run: blender -b --python p1_slab.py"""
import bpy, bmesh, sys, json, shutil, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter'); OUT = J / 'work/slab'
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
W = Path(r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work'); sys.path.insert(0, str(W))
bpy.ops.wm.read_homefile(use_empty=True)
coll = bpy.data.collections.new('Collection'); bpy.context.scene.collection.children.link(coll)
import v13_kit as K, v13_materials as M
from bl_ext.user_default.sollumz.sollumz_properties import SollumType
from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index
from bl_ext.user_default.sollumz.tools.boundhelper import convert_objs_to_single_composite
sys.path.insert(0, str(J / 'work')); import sidewalk_mat as SW, jc_frame as F
SWM = SW.load()
def export(root):
    bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
GRID = 2.0
def slab_mesh(pts, mat, skirt=0.0, apron=0.0):
    bm = bmesh.new(); vs = [bm.verts.new(Vector(p)) for p in pts]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for k in range(int(np.floor(min(xs) / GRID)) + 1, int(np.ceil(max(xs) / GRID))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((k * GRID, 0, 0)), plane_no=Vector((1, 0, 0)))
    for k in range(int(np.floor(min(ys) / GRID)) + 1, int(np.ceil(max(ys) / GRID))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k * GRID, 0)), plane_no=Vector((0, 1, 0)))
    edge = {v for e in bm.edges if e.is_boundary for v in e.verts}           # on his edge lines: linear between his vertices already
    for v in bm.verts:
        if v not in edge: v.co.z = F.slab_z(v.co.x, v.co.y)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    if skirt or apron:
        be = [e for e in bm.edges if e.is_boundary]
        out = {}                                                          # outward horizontal normal per boundary vertex (ccw outline)
        for e in be:
            fc = e.link_faces[0].calc_center_median(); a, b = e.verts; d = (b.co - a.co); d.z = 0; d.normalize()
            n = Vector((d.y, -d.x, 0))
            if n.dot(fc - a.co) > 0: n = -n
            for v in (a, b): out[v] = out.get(v, Vector()) + n
        res = bmesh.ops.extrude_edge_only(bm, edges=be)
        newv = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
        for v in newv:
            src = min(out, key=lambda q: (q.co - v.co).length)               # its twin on the boundary (same position)
            if skirt: v.co.z -= skirt
            else: v.co += out[src].normalized() * apron; v.co.z -= 0.03
        bm.normal_update()
        if apron:
            for f in bm.faces:
                if f.normal.z < 0: f.normal_flip()
    me = bpy.data.meshes.new('slab'); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new('slab', me); bpy.context.scene.collection.objects.link(o); return o
pts = F.edge_pts(1.0)
c = Vector((float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts])), float(np.mean([p[2] for p in pts]))))
vis = slab_mesh(pts, SWM[SW.LOT_MAT['lot']], skirt=0.6); vis.data.transform(Matrix.Translation(-c))
root, lo, hi = K.new_drawable('jc_lot', [vis], uv=0.25)
n = 0
for o in root.children_recursive:
    if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model':
        if not o.data.uv_layers: o.data.uv_layers.new()
        n += SW.paint(o, Matrix.Translation(c) @ o.matrix_world)
assert n, 'no sidewalk faces painted'
export(root)
tri = []
for o in root.children_recursive:
    if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model':
        me = o.data; me.calc_loop_triangles(); M4 = Matrix.Translation(c) @ o.matrix_world
        V = np.array([tuple(M4 @ v.co) for v in me.vertices], np.float32)
        if len(me.loop_triangles): tri.append(V[np.array([t.vertices[:] for t in me.loop_triangles], np.int64)])
np.save(OUT / 'tris_jc_lot.npy', np.concatenate(tri))
col = slab_mesh(pts, create_collision_material_from_index(1), apron=0.5)      # 1 = CONCRETE (his sidewalk collision's material)
comp = convert_objs_to_single_composite([col], SollumType.BOUND_GEOMETRYBVH, 'General (Default)')
comp.name = 'jc_lot_col'
export(comp)
info = {'lot': {'origin': [c.x, c.y, c.z], 'bb_lo': list(lo), 'bb_hi': list(hi)}}
tiny = np.full((8, 8, 4), .5, np.float32); tn = np.full((8, 8, 4), .5, np.float32); tn[:, :, 2] = 1
emptym = M.material('JC empty', 'jc_empty_px', tiny, tn, M.spec_from(np.full((8, 8, 4), .5, np.float32), .0, .0), .8, .0, 2)
root, lo, hi = K.new_drawable('jc_empty', [K.box((0, 0, -5.01), (.01, .01, -5.0), emptym)]); export(root)
info['jc_empty'] = {'bb_lo': list(lo), 'bb_hi': list(hi)}
json.dump(info, open(OUT / 'slab_info.json', 'w'), indent=1)
print('P1_SLAB_PASS', json.dumps(info), 'painted faces', n, flush=True)
