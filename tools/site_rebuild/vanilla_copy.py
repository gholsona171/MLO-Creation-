"""The second pole barn (site_plan.BARN2; the client, Nov 23): a copy of the kept pole barn as our own model jy_pole_barn2.
  * Drawing: wallc_cut.py's barn model (../site/barn/cs4_02_sy_wallc.ydr, the old wall already cut out), every LOD, only the faces
    of the barn itself (inside site_plan.BARN, clear of the old wall line), moved so the model's origin is the barn rect's centre at
    paving height. Its textures stay in Rockstar's dictionary cs4_02_airscrap_2 (the archetype names it; not embedded).
  * Collision: the barn's own collision from the game's area file lr_cs4_02_14.ybn (its poly boxes, and any non-ground triangles,
    inside site_plan.BARN), same materials, embedded in the model.
  * site_place.py puts it at the centre of BARN2, turned 180 degrees, at the paving height there.
Run: blender -b --python barn_copy.py     Output ../site/barn2/jy_pole_barn2.ydr + barn2_info.json"""
import bpy, bmesh, sys, json, re
from pathlib import Path
from mathutils import Vector, Matrix
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, yard_plan as Y, pave_ground as PG
M_ = T.parent; OUT = M_ / 'site' / 'barn2'
for f in OUT.glob('*') if OUT.exists() else []: f.unlink()
OUT.mkdir(parents=True, exist_ok=True)
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel, SollumType
from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index
from bl_ext.user_default.sollumz.tools.boundhelper import convert_objs_to_single_composite
NAME, SRC_ENT, COL_SRC, TXD = 'jy_pole_barn2', Vector((2356.66, 3065.61, 48.84)), 'lr_cs4_02_14', 'cs4_02_airscrap_2'
GROUND = re.compile(r'sand|dirt|gravel|rock|soil|mud|clay|grass|stone|desert|hay|bushes|twigs|leaves|tarmac', re.I)
B = SP.BARN; C = Vector(((B[0] + B[2]) / 2, (B[1] + B[3]) / 2, 0)); C.z = PG.pave_z(C.x, C.y)
def in_barn(p): return B[0] <= p.x <= B[2] and B[1] <= p.y <= B[3] and Y.dist_to_loop(p.x, p.y) > 0.9

# ---- the drawing
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(M_ / 'site' / 'barn'), files=[{'name': 'cs4_02_sy_wallc.ydr'}])
root = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable' and o.parent is None); root.name = NAME
for o in [o for o in root.children_recursive if o.sollum_type.startswith('sollumz_bound')]: bpy.data.objects.remove(o, do_unlink=True)
for m in bpy.data.materials:
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and hasattr(nd, 'texture_properties'): nd.texture_properties.embedded = False
kept, cut, lo, hi = 0, 0, Vector((1e9,) * 3), Vector((-1e9,) * 3)
shift = Matrix.Translation(SRC_ENT - C)
for ob in [o for o in root.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model']:
    for level in LODLevel:
        lod = ob.sz_lods.get_lod(level); me = lod.mesh if lod else None
        if me is None or not me.polygons: continue
        bm = bmesh.new(); bm.from_mesh(me)
        dead = [f for f in bm.faces if not in_barn(ob.matrix_world @ f.calc_center_median() + SRC_ENT)]
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(me); bm.free(); me.transform(ob.matrix_world.inverted() @ shift @ ob.matrix_world); cut += len(dead)
        if level == LODLevel.HIGH:
            kept += len(me.polygons)
            for v in me.vertices:                                    # (model space: the mesh is moved already)
                w = ob.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
assert kept > 100, f'barn faces kept: {kept}'

# ---- the collision, from the game's area file
bpy.ops.sollumz.import_assets(directory=str(M_ / 'vanilla'), files=[{'name': COL_SRC + '.ybn'}])
src = [o for o in bpy.data.objects if o.type == 'MESH' and o.sollum_type.startswith('sollumz_bound_poly') and o.parent and not o.parent.name.startswith(NAME)]
cols = []
for o in src:
    mw = o.matrix_world
    if o.sollum_type == 'sollumz_bound_poly_triangle':
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(mw)
        mats = o.data.materials
        dead = [f for f in bm.faces if not in_barn(f.calc_center_median()) or GROUND.search(mats[f.material_index].name if f.material_index < len(mats) else '')]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        if not bm.faces: bm.free(); continue
        bm.transform(Matrix.Translation(-C)); me = bpy.data.meshes.new('barn_tris'); bm.to_mesh(me); bm.free()
        for m in mats: me.materials.append(m)
    else:
        if not in_barn(mw.translation): continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(Matrix.Translation(-C) @ mw)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        me = bpy.data.meshes.new('barn_box'); bm.to_mesh(me); bm.free()
        me.materials.append(o.data.materials[0] if o.data.materials else create_collision_material_from_index(0))
    n = bpy.data.objects.new('collision', me); bpy.context.scene.collection.objects.link(n); cols.append(n)
assert len(cols) > 10, f'barn collision pieces: {len(cols)}'
for o in src: bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o.sollum_type == 'sollumz_bound_composite' and not o.children]: bpy.data.objects.remove(o, do_unlink=True)
bound = convert_objs_to_single_composite(cols, SollumType.BOUND_GEOMETRYBVH, 'General (Default)'); bound.parent = root
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
B2 = SP.BARN2; at = ((B2[0] + B2[2]) / 2, (B2[1] + B2[3]) / 2); at = (*at, PG.pave_z(*at))
info = {'bb_lo': list(lo), 'bb_hi': list(hi), 'at': at, 'heading': 180.0, 'txd': TXD}
json.dump(info, open(OUT / 'barn2_info.json', 'w'), indent=1)
print('BARN_COPY_PASS', {'faces': kept, 'faces_cut': cut, 'collision_pieces': len(cols), 'size': [round(v, 2) for v in hi - lo], 'at': [round(v, 2) for v in at]}, flush=True)
