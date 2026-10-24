"""Tower City: the exterior clean-up's own pieces (ext_plan.py -> plan/ext_build.json), one exterior drawable 'tc_ext_fix' placed at the
tower lot's origin (lot frame) + its world-space collision 'tc_ext_fix_col':
  * the Power St plaza paving over the old car-park drives: Rockstar's own tarmac triangles (the faces level 0 cuts), 12 mm up,
    so the paving meets every kerb and planter exactly; plus the PARKING block's footprint in front of / beside the portico steps
    (draped: the drives' height at their north end, easing to the first riser's foot - the bottom step keeps its rise)
  * the old car-park pit under the San Andreas branch (opened when the branch goes): closed at the sidewalk's height
  * 'paving': light grey 1 m concrete flags with dark joints - the same read as the vanilla sidewalk around it
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
DZ = 0.012                                                     # over the drives' own (cut) surface
SP = json.load(open(TK.T / 'plan/ext_build.json'))
# ---------------- the paving material ----------------
import paving_mat
TK.MAT['paving'] = paving_mat.make(TK.M)
# ---------------- the drives: Rockstar's tarmac triangles, raised ----------------
V, F = [], []
for poly in SP['tarmac']:
    i0 = len(V); V += [(p[0], p[1], p[2] + DZ) for p in poly]
    F += [(i0, i0 + k, i0 + k + 1) for k in range(1, len(poly) - 1)]
TK.mesh('ext', V, F, 'paving', col=True, name='paving_drives')
# ---------------- the block's footprint: the notch ----------------
TAR = [[tuple(p) for p in poly] for poly in SP['tarmac']]
def over_tarmac(u, v, eps=1e-4):
    return EP.drive_z(u, v, TAR) is not None
bm = bmesh.new()
vs = [bm.verts.new(Vector((u, v, 0.0))) for u, v in SP['notch']]
bm.faces.new(vs)
u0 = min(u for u, v in SP['notch']); u1 = max(u for u, v in SP['notch']); v0 = min(v for u, v in SP['notch']); v1 = max(v for u, v in SP['notch'])
for k in range(int(u0) + 1, int(u1) + 1):                       # a 1 m grid: the draped heights bend smoothly
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((k, 0, 0)), plane_no=Vector((1, 0, 0)))
for k in range(int(math.floor(v0)) + 1, int(math.ceil(v1))):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, k, 0)), plane_no=Vector((0, 1, 0)))
near = [poly for poly in TAR if max(p[1] for p in poly) > EP.NOTCH_SOUTH - 0.5]   # tarmac reaching into the notch: cut it out of the notch
for poly in near:
    for i in range(len(poly)):
        a, b = Vector(poly[i][:2] + (0,)), Vector(poly[(i + 1) % len(poly)][:2] + (0,)); dd = (b - a)
        if dd.length < 1e-6: continue
        dd.normalize(); bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=a, plane_no=Vector((-dd.y, dd.x, 0)))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
dead = [f for f in bm.faces if over_tarmac(*f.calc_center_median().xy)]
bmesh.ops.delete(bm, geom=dead, context='FACES')
for v in bm.verts:
    z = EP.drive_z(v.co.x, v.co.y, TAR)
    v.co.z = (z if z is not None else EP.notch_z(v.co.x, v.co.y, TAR)) + DZ
NV = [tuple(v.co) for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}
NF = [tuple(idx[v] for v in f.verts) for f in bm.faces]
for f in bm.faces: f.normal_update()
NF = [t if (Vector(NV[t[1]]) - Vector(NV[t[0]])).cross(Vector(NV[t[2]]) - Vector(NV[t[0]])).z > 0 else (t[0], t[2], t[1]) for t in NF]
bm.free()
TK.mesh('ext', NV, NF, 'paving', col=True, name='paving_notch')
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
info = TK.export_all({}, {'ext': 'tc_ext_fix'}, 'tc_ext_fix_int', 'tc_ext_fix_col')
lay = {'origin': list(EP.ORIGIN), 'heading': EP.HEADING, 'drawables': info, 'ext': {'tc_ext_fix': 'tc_ext_fix_col'},
       'bollards': SP['bollards'], 'benches': SP['benches'], 'tris': {'drives': len(F), 'notch': len(NF), 'pit': len(PF_)}}
json.dump(lay, open(OUT / 'ext_layout.json', 'w'), indent=1)
print('EXT_BUILD_PASS', json.dumps({'drive_tris': len(F), 'notch_tris': len(NF), 'drawables': list(info)}), flush=True)
