"""Rockstar's static collision at the Block Boyz site, cut and regraded (one file per Blender process; col_all.sh runs them all).
  * On the site and within site_plan.CLEAR_MARGIN of it, every face goes except the ground: a face whose material is a ground
    surface (GROUND), or an up-facing face (nz > 0.7) within ON_GROUND of Rockstar's ground there (grade.raw_z). The camp's sheds,
    fences, rocks and junk all go. Primitives (box / sphere / capsule) centred there go too.
  * The ground left on the site is split along a 2 m world grid (the same grid ground.py draws the lot on), every vertex set to the
    new grade (grade.grade_z: flat at site_plan.PAD_Z under the club + apron), and given the lot's material
    (site_plan.LOT_MATERIAL, no procedural grass). So the ground can never stand above the club's floor.
  * A file with nothing to change is not written (and any old output of it is deleted): only edited collision ships.
  * A BVH child over 30,000 triangles is split in two (Sollumz refuses more than 32,767).
Run: blender -b --python site_col.py -- <name without .ybn>
Input ../vanilla/<name>.ybn  Output ../site/col/<name>.ybn"""
import bpy, bmesh, sys, json, re
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_plan as SP, grade as GR
M = Path(__file__).resolve().parents[1]; SRC = M / 'vanilla'; OUT = M / 'site' / 'col'; OUT.mkdir(parents=True, exist_ok=True)
GROUND = re.compile(r'sand|dirt|gravel|rock|soil|mud|clay|grass|stone|desert|hay|bushes|twigs|leaves|tarmac|concrete', re.I)
ON_GROUND, GRID, BVH_MAX = 0.4, 2.0, 30000
xs = [p[0] for p in SP.SITE]; ys = [p[1] for p in SP.SITE]
X0, X1, Y0, Y1 = min(xs) - 4, max(xs) + 4, min(ys) - 4, max(ys) + 4


def cleared(p): return SP.near_site(p.x, p.y)


def lot_material():
    from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index, collisionmats
    i = next(k for k, m in enumerate(collisionmats) if m.name.upper() == SP.LOT_MATERIAL)
    m = create_collision_material_from_index(i); m.collision_properties.procedural_id = 0; return m


name = sys.argv[sys.argv.index('--') + 1]
(OUT / f'{name}.ybn').unlink(missing_ok=True)
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ybn'}])
ybn = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_bound_composite' and o.parent is None)
st = {'prims': 0, 'faces_cut': 0, 'ground_graded': 0, 'grid_cuts': 0}
LM = None
for nm in [o.name for o in ybn.children_recursive]:
    ob = bpy.data.objects.get(nm)
    if ob is None or ob.type != 'MESH' or not ob.data.vertices: continue
    mw = ob.matrix_world; inv = mw.inverted(); inv3 = inv.to_3x3(); r3 = mw.to_3x3()
    if ob.sollum_type.startswith('sollumz_bound_poly_') and ob.sollum_type != 'sollumz_bound_poly_triangle':
        vs = [mw @ v.co for v in ob.data.vertices]; c = sum(vs, Vector()) / len(vs)
        if cleared(c): st['prims'] += 1; bpy.data.objects.remove(ob, do_unlink=True)
        continue
    if ob.sollum_type != 'sollumz_bound_poly_triangle': continue
    bm = bmesh.new(); bm.from_mesh(ob.data)
    vs = [mw @ v.co for v in bm.verts]
    if max(v.x for v in vs) < X0 or min(v.x for v in vs) > X1 or max(v.y for v in vs) < Y0 or min(v.y for v in vs) > Y1: bm.free(); continue
    mats = ob.data.materials
    def mname(f): return mats[f.material_index].name if mats and f.material_index < len(mats) and mats[f.material_index] else '?'
    def is_ground(f):
        c = mw @ f.calc_center_median(); nz = (r3 @ f.normal).normalized().z
        return bool(GROUND.search(mname(f))) or (nz > 0.7 and c.z < GR.raw_z(c.x, c.y) + ON_GROUND)
    # 1 cut what stands on the site (and in its margin)
    dead = [f for f in bm.faces if not is_ground(f) and cleared(mw @ f.calc_center_median())]
    st['faces_cut'] += len(dead)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    # 2 the ground left on the site: the 2 m grid, the new grade, the lot's material
    onsite = lambda f: SP.on_site(*(mw @ f.calc_center_median()).xy)
    if any(onsite(f) for f in bm.faces):
        assert all(abs(mw[i][j] - (i == j)) < 1e-6 for i in range(3) for j in range(3)), 'collision mesh not axis-aligned'
        off = mw.translation
        for ax, (a0, a1) in ((0, (X0, X1)), (1, (Y0, Y1))):
            for k in range(int(a0 // GRID), int(a1 // GRID) + 2):
                v = k * GRID; lv = v - off[ax]
                faces = [f for f in bm.faces if min(u.co[ax] for u in f.verts) < lv < max(u.co[ax] for u in f.verts)
                         and (onsite(f) or any(SP.on_site(*(u.co + off).xy) for u in f.verts))]
                if not faces: continue
                geom = list({e for f in faces for e in f.edges}) + faces + list({u for f in faces for u in f.verts})
                co = Vector((v, 0, 0)) if ax == 0 else Vector((0, v, 0)); no = Vector((1, 0, 0)) if ax == 0 else Vector((0, 1, 0))
                bmesh.ops.bisect_plane(bm, geom=geom, plane_co=inv @ co, plane_no=(inv3 @ no).normalized()); st['grid_cuts'] += 1
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        if LM is None: LM = lot_material()
        if LM.name not in [m.name for m in ob.data.materials if m]: ob.data.materials.append(LM)
        li = [m.name if m else '' for m in ob.data.materials].index(LM.name)
        lot = [f for f in bm.faces if onsite(f)]
        for f in lot: f.material_index = li
        for u in {u for f in lot for u in f.verts} | {u for u in bm.verts if u.link_faces and SP.on_site(*(mw @ u.co).xy)}:
            w = mw @ u.co; w.z = GR.grade_z(w.x, w.y); u.co = inv @ w        # (every vertex on the site too: the faces across the outline)
        st['ground_graded'] += len(lot)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data); bm.free()
print('SITE_COL_STATS', name, json.dumps(st), flush=True)
if not any(st.values()):
    print('SITE_COL_UNCHANGED', name, flush=True); sys.exit(0)
for ob in [o for o in ybn.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_bound_poly_triangle' and not o.data.polygons]:
    bpy.data.objects.remove(ob, do_unlink=True)
for ob in [o for o in ybn.children_recursive if o.sollum_type in ('sollumz_bound_geometrybvh', 'sollumz_bound_geometry')]:
    if not any(c.type == 'MESH' and c.data.vertices for c in ob.children_recursive) and not (ob.type == 'MESH' and ob.data.vertices):
        for c in list(ob.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(ob, do_unlink=True)


def split_bvh(bvh):
    tris = [c for c in bvh.children if c.type == 'MESH' and c.sollum_type == 'sollumz_bound_poly_triangle']
    if sum(len(c.data.polygons) for c in tris) <= BVH_MAX: return 0
    xs_ = sorted((c.matrix_world @ p.center).x for c in tris for p in c.data.polygons); cut = xs_[len(xs_) // 2]
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


st['bvh_splits'] = sum(split_bvh(o) for o in [o for o in ybn.children_recursive if o.sollum_type == 'sollumz_bound_geometrybvh'])
ybn.name = name
bpy.ops.object.select_all(action='DESELECT'); ybn.select_set(True); bpy.context.view_layer.objects.active = ybn
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('SITE_COL_PASS', name, json.dumps(st), flush=True)
