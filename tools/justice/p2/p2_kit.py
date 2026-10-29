"""Justice Center phase 2: Blender helpers on top of Tower City's tc_kit (imported, never edited): face-frame boxes and quads,
and the exterior COLLISION, kept apart from tc_kit's merge (which sets every face to CONCRETE): here each piece keeps Rockstar's
material for its surface (STONE walls, GRASS lawn, CONCRETE paving, METAL) and the whole site's collision is ONE static ybn,
jc_ext_col, in world space, one BVH child per material (doc 02: few children, never one per box)."""
import bpy, math, numpy as np
from mathutils import Vector
import tc_kit as TK
import p2_plan as PL
from p2_plan import box_minus
COLM = {'concrete': 1, 'stone': 11, 'grass': 47, 'metal': 57, 'glass': 113}
COL = {k: [] for k in COLM}                                    # material -> [(verts, faces)] lot frame
def col_box(lo, hi, mat='stone'):
    (x0, y0, z0), (x1, y1, z1) = [tuple(min(a, b) for a, b in zip(lo, hi)), tuple(max(a, b) for a, b in zip(lo, hi))]
    if min(x1 - x0, y1 - y0, z1 - z0) <= 1e-4: return
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    COL[mat].append((v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]))
def col_mesh(verts, faces, mat): COL[mat].append(([tuple(v) for v in verts], [tuple(f) for f in faces]))
def fbox(key, face, s0, s1, d0, d1, z0, z1, mat):
    if s1 - s0 <= 1e-4 or abs(d1 - d0) <= 1e-4 or z1 - z0 <= 1e-4: return
    p = PL.P(face, s0, d0, z0); q = PL.P(face, s1, d1, z1)
    TK.box(key, tuple(min(a, b) for a, b in zip(p, q)), tuple(max(a, b) for a, b in zip(p, q)), mat, col=False)
def quad(key, pts, mat, toward, name='q'):
    """one face, wound so its normal points at `toward` (a direction vector)."""
    P = [Vector(p) for p in pts]; n = (P[1] - P[0]).cross(P[2] - P[0])
    if n.dot(Vector(toward)) < 0: P = P[::-1]
    TK.mesh(key, [tuple(p) for p in P], [tuple(range(len(P)))], mat, False, name)
def fquad(key, face, corners, mat, toward_d=None, toward=None, name='q'):
    """a quad given in face coordinates [(s, d, z)]; it faces +d (toward_d=+1), -d, or a lot-frame direction."""
    pts = [PL.P(face, s, d, z) for s, d, z in corners]
    if toward is None:
        o = PL.P(face, 0.0, toward_d, 0.0); b = PL.P(face, 0.0, 0.0, 0.0); toward = (o[0] - b[0], o[1] - b[1], 0.0)
    quad(key, pts, mat, toward, name)
def fdir(face, ds=0.0, dd=0.0, dz=0.0):
    """a direction in face coordinates -> lot frame."""
    a = PL.P(face, 0.0, 0.0, 0.0); b = PL.P(face, ds, dd, dz); return (b[0] - a[0], b[1] - a[1], b[2] - a[2])
def export_collision(name, out_dir, L2W):
    """COL -> one static bound `name` (world space): one mesh per material, split under 30,000 vertices (BVH child limits)."""
    from bl_ext.user_default.sollumz.sollumz_properties import SollumType
    from bl_ext.user_default.sollumz.ybn.collision_materials import create_collision_material_from_index
    from bl_ext.user_default.sollumz.tools.boundhelper import convert_objs_to_single_composite
    objs = []; tris = []
    for mat, parts in COL.items():
        chunk_v, chunk_f = [], []
        def flush():
            if not chunk_f: return
            me = bpy.data.meshes.new(f'col_{mat}_{len(objs)}'); me.from_pydata([tuple(L2W @ Vector(v)) for v in chunk_v], [], chunk_f)
            m = create_collision_material_from_index(COLM[mat]); m.update_tag(); me.materials.append(m); me.update()
            o = bpy.data.objects.new(me.name, me); bpy.data.collections['Collection'].objects.link(o); objs.append(o)
            W_ = np.array([tuple(L2W @ Vector(v)) for v in chunk_v], np.float32)
            for f in chunk_f:
                for i in range(1, len(f) - 1): tris.append((W_[f[0]], W_[f[i]], W_[f[i + 1]], COLM[mat]))
            chunk_v.clear(); chunk_f.clear()
        for vs, fs in parts:
            if len(chunk_v) + len(vs) > 30000: flush()
            b = len(chunk_v); chunk_v.extend(vs); chunk_f.extend([tuple(b + i for i in f) for f in fs])
        flush()
    bpy.context.view_layer.update()
    comp = convert_objs_to_single_composite(objs, SollumType.BOUND_GEOMETRYBVH, 'General (Default)'); comp.name = name
    for gb in comp.children:
        mtx = gb.matrix_local.copy()
        for ch in gb.children:
            if ch.type == 'MESH': ch.data.transform(mtx @ ch.matrix_local); ch.matrix_local.identity()
        gb.matrix_local.identity()
    TK._export(comp, out_dir)
    T_ = np.array([[t[0], t[1], t[2]] for t in tris], np.float32); M_ = np.array([t[3] for t in tris], np.int16)
    np.save(out_dir / f'coltris_{name}.npy', T_); np.save(out_dir / f'colmats_{name}.npy', M_)
    return {m: sum(len(fs) for _, fs in p) for m, p in COL.items()}, len(objs)
