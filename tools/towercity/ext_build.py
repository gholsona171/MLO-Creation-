"""Tower City: the exterior clean-up's own pieces (ext_plan.py -> plan/ext_build.json), one exterior drawable 'tc_ext_fix' placed at the
tower lot's origin (lot frame) + its world-space collision 'tc_ext_fix_col':
  * the Power St plaza over the old car-park drives (ONE surface at the kerb's top, the street's kerb across the mouths is his own,
    cloned by level 0) + the PARKING block's footprint in front of / beside the portico steps (the notch: the plaza's height easing
    to the first riser's foot - the bottom step keeps its rise); the lot slab has holes there (ext_plan 'slab_holes')
  * the San Andreas deck's new west sidewalk (C), between the deck edge and the bent kerb
  * the old car-park pit under the San Andreas branch (opened when the branch goes): closed at the sidewalk's height
  * 'paving': Rockstar's own sidewalk (sidewalk_mat.py: his material, UV scale / direction and vertex colours; his textures bind
    through the archetype's txd, ext_meta.py) - one surface with the sidewalk round it, no second colour
The bollards and benches are vanilla props: plain map entities written by ext_meta.py.
Run: blender -b --python ext_build.py   (pass line EXT_BUILD_PASS). Outputs work/extfix: tc_ext_fix.ydr, tc_ext_fix_col.ybn, ext_layout.json"""
import sys, json, math
sys.path.insert(0, 'C:/Users/anton/Documents/Codex/TowerCity/work')
import bpy, bmesh, numpy as np
from mathutils import Vector
import tc_kit as TK
import ext_plan as EP
TK.set_origin(*EP.ORIGIN, EP.HEADING)
OUT = TK.T / 'work/extfix'
TK.init(OUT, {}, ext_keys=('ext',))
SP = json.load(open(TK.T / 'plan/ext_build.json'))
# ---------------- the paving material ----------------
import sidewalk_mat as SW                                      # Rockstar's own sidewalk (west lot: dc_sidewalk001), UVs + colours his
TK.MAT['paving'] = SW.load()[SW.LOT_MAT['west']]
def _paint(o, L2W):
    if not o.data.uv_layers: o.data.uv_layers.new()
    SW.paint(o, L2W @ o.matrix_world)
TK.POST_EXT.append(_paint)
# ---------------- B: the plaza over the old drives + the PARKING block's footprint (the notch) ----------------
def grid_mesh(poly, zf, step=1.0, name='mesh', skip=None):
    """a flat outline cut on a 1 m grid (the heights bend smoothly), its vertices at zf(u, v); faces whose centre skip(u, v) is true go."""
    bm = bmesh.new(); bm.faces.new([bm.verts.new(Vector((u, v, 0.0))) for u, v in poly])
    us = [u for u, v in poly]; vs_ = [v for u, v in poly]
    for k in range(int(math.floor(min(us))) + 1, int(math.ceil(max(us)))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((k * step, 0, 0)), plane_no=Vector((1, 0, 0)))
    for k in range(int(math.floor(min(vs_))) + 1, int(math.ceil(max(vs_)))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k * step, 0)), plane_no=Vector((0, 1, 0)))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    if skip: bmesh.ops.delete(bm, geom=[f for f in bm.faces if skip(*f.calc_center_median().xy)], context='FACES')
    for v in bm.verts: v.co.z = zf(v.co.x, v.co.y)
    V = [tuple(v.co) for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}
    F_ = [tuple(idx[v] for v in f.verts) for f in bm.faces]; bm.free()
    F_ = [t if (Vector(V[t[1]]) - Vector(V[t[0]])).cross(Vector(V[t[2]]) - Vector(V[t[0]])).z > 0 else (t[0], t[2], t[1]) for t in F_]
    TK.mesh('ext', V, F_, 'paving', col=True, name=name); return len(F_)
NPL = grid_mesh([tuple(p) for p in SP['plaza']], EP.plaza_z, name='b_plaza')
NNO = grid_mesh([tuple(p) for p in SP['notch']], EP.notch_z, name='b_notch')
# ---------------- under the San Andreas branch: the old car-park pit closed at the sidewalk's height ----------------
bm = bmesh.new(); bm.faces.new([bm.verts.new(Vector((u, v, 0.0))) for u, v in SP['a_patch']])
pu = [u for u, v in SP['a_patch']]; pv = [v for u, v in SP['a_patch']]
for k in range(int(math.floor(min(pv))) + 1, int(math.ceil(max(pv)))):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k, 0)), plane_no=Vector((0, 1, 0)))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
for v in bm.verts: v.co.z = EP.patch_z(v.co.x, v.co.y) - 0.004            # 4 mm under the sidewalk it meets
PV_ = [tuple(v.co) for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}
PF_ = [tuple(idx[v] for v in f.verts) for f in bm.faces]; bm.free()
PF_ = [t if (Vector(PV_[t[1]]) - Vector(PV_[t[0]])).cross(Vector(PV_[t[2]]) - Vector(PV_[t[0]])).z > 0 else (t[0], t[2], t[1]) for t in PF_]
TK.mesh('ext', PV_, PF_, 'paving', col=True, name='pit_patch')
# ---------------- C: the deck's new west sidewalk (between the deck edge and the bent kerb), Rockstar's sidewalk material ----------------
CP = [tuple(p) for p in SP['c_paving']]; KB = SP['c_kerb_back']
def c_z(v):                                                     # the kerb top beside it (the paving meets the kerb's back flush)
    for a, b in zip(KB, KB[1:]):
        if a[1] <= v <= b[1]: return a[2] + (v - a[1]) / max(b[1] - a[1], 1e-9) * (b[2] - a[2])
    return KB[0][2] if v < KB[0][1] else KB[-1][2]
bm = bmesh.new(); vs = [bm.verts.new(Vector((u, v, 0.0))) for u, v, z in CP]; bm.faces.new(vs)
v0 = min(p[1] for p in CP); v1 = max(p[1] for p in CP)
for k in range(int(math.floor(v0)) + 1, int(math.ceil(v1))):   # 1 m across the strip: the height follows the kerb
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k, 0)), plane_no=Vector((0, 1, 0)))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
edge = {(round(u, 3), round(v, 3)): z for u, v, z in CP}
for v in bm.verts: v.co.z = edge.get((round(v.co.x, 3), round(v.co.y, 3)), c_z(v.co.y))
CV = [tuple(v.co) for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}
CF = [tuple(idx[v] for v in f.verts) for f in bm.faces]; bm.free()
CF = [t if (Vector(CV[t[1]]) - Vector(CV[t[0]])).cross(Vector(CV[t[2]]) - Vector(CV[t[0]])).z > 0 else (t[0], t[2], t[1]) for t in CF]
TK.mesh('ext', CV, CF, 'paving', col=True, name='c_sidewalk')
info = TK.export_all({}, {'ext': 'tc_ext_fix'}, 'tc_ext_fix_int', 'tc_ext_fix_col')
lay = {'origin': list(EP.ORIGIN), 'heading': EP.HEADING, 'drawables': info, 'ext': {'tc_ext_fix': 'tc_ext_fix_col'},
       'bollards': SP['bollards'], 'benches': SP['benches'], 'tris': {'plaza': NPL, 'notch': NNO, 'pit': len(PF_), 'c_sidewalk': len(CF)}}
json.dump(lay, open(OUT / 'ext_layout.json', 'w'), indent=1)
print('EXT_BUILD_PASS', json.dumps({'plaza_tris': NPL, 'notch_tris': NNO, 'c_sidewalk_tris': len(CF), 'drawables': list(info)}), flush=True)
