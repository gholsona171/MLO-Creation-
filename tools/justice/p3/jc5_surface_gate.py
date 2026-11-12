"""Surface gate (Blender, on the build's own scene out/jc3_scene.blend + out/solids.npy): the three things Antonio found on the police
side (2026-11-11: "walls that are not connected, walls at weird angles, weird lips ... it didn't texture everything properly").
  SLIT    two opaque solids of one room facing each other 1 mm .. 6 cm apart over more than 10 x 10 cm: a wall joint that does not meet
  ANGLE   a wall-sized vertical face (>= 0.3 m2, >= 1 m tall) whose normal is not on the lot axes (every wall of this complex is on the
          grid; arch segments, ramps and treads are smaller or not vertical)
  FLAT    a face whose material is a flat paint (diffuse texture 64 px or less, no bump map) - untextured to the eye; signs, art and lit
          glass are exempt
  UV      a textured face of 0.25 m2 or more whose UV density is off its material's metres-per-repeat by more than 3x (stretched /
          squashed texture)
blender -b out/jc3_scene.blend --python jc5_surface_gate.py -- [--plant] [--rooms prefix,...]   pass line JC5_SURFACE_PASS"""
import sys, json
from pathlib import Path
import bpy, numpy as np
P3 = Path(__file__).resolve().parent
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PLANT = '--plant' in argv
ROOMS = argv[argv.index('--rooms') + 1].split(',') if '--rooms' in argv else None
EXEMPT_MAT = ('sign', 'placard', 'art', 'insignia', 'lamp', 'glow', 'sconce', 'glass', 'mirror', 'floor', 'decal', 'lift', 'crystal', 'cove', 'plate')
MPU = None
def mpu():
    global MPU
    if MPU is None: MPU = json.load(open(P3 / 'out' / 'mpu.json'))           # written by jc3_build (its M_PER_UV: one source)
    return MPU
def flat(m):
    if m is None or m.name.endswith('_d') or any(k in m.name.lower() for k in EXEMPT_MAT): return False     # (decals: markings over a floor)
    nt = m.node_tree
    if nt is None: return False
    d = nt.nodes.get('DiffuseSampler'); b = nt.nodes.get('BumpSampler')
    if d is None or d.image is None: return True
    small = max(d.image.size) <= 64
    nob = b is None or b.image is None or max(b.image.size) <= 8
    return small and nob
def run(objs, solids):
    bad = {'SLIT': [], 'ANGLE': [], 'FLAT': [], 'UV': []}
    M = mpu()
    for o in objs:
        rn = o.parent.name if o.parent else o.name; me = o.data; W = o.matrix_world; mats = list(me.materials); uv = me.uv_layers[0].data if me.uv_layers else None
        for p in me.polygons:
            m = mats[p.material_index] if p.material_index < len(mats) else None; n = (W.to_3x3() @ p.normal).normalized()
            c = W @ p.center; at = [round(c.x, 2), round(c.y, 2), round(c.z, 2)]
            if abs(n.z) < 0.2 and min(abs(n.x), abs(n.y)) > 0.02 and p.area >= 0.3:          # a wall-sized face off the lot grid
                zs = [(W @ me.vertices[i].co).z for i in p.vertices]
                if max(zs) - min(zs) >= 1.0: bad['ANGLE'].append((rn, at, [round(n.x, 3), round(n.y, 3)]))
            if p.area < 0.01: continue
            if flat(m): bad['FLAT'].append((rn, m.name, at))
            key = m.name[4:] if m and m.name.startswith('JC3 ') else None
            if uv and key in M and p.area >= 0.25:                                # (surfaces you read a texture on; trims are too small to tell)
                us = [uv[li].uv for li in p.loop_indices]; a = 0.0
                for i in range(1, len(us) - 1):
                    a += abs((us[i].x - us[0].x) * (us[i + 1].y - us[0].y) - (us[i + 1].x - us[0].x) * (us[i].y - us[0].y)) / 2
                want = p.area / (M[key] ** 2)
                if a <= 0 or not (want / 3 <= a <= want * 3): bad['UV'].append((rn, m.name, at, round(a / max(want, 1e-9), 3)))
    S = solids
    for ax in (0, 1):                                                     # faces across x / y (floors and ceilings are the gap check's)
        o = [k for k in range(3) if k != ax]
        order = np.argsort(S[:, ax]); lo_sorted = S[order, ax]
        for i in range(len(S)):
            a = S[i]
            j0, j1 = np.searchsorted(lo_sorted, [a[ax + 3] + 0.001, a[ax + 3] + 0.06])
            for j in order[j0:j1]:
                b = S[j]; gap = b[ax] - a[ax + 3]
                ov = [min(a[k + 3], b[k + 3]) - max(a[k], b[k]) for k in o]
                if min(ov) <= 0.10: continue
                lo_o = [max(a[k], b[k]) for k in o]; hi_o = [min(a[k + 3], b[k + 3]) for k in o]
                mid = (a[ax + 3] + b[ax]) / 2                                     # sample the gap's mid plane: is every point inside a solid?
                g = [np.linspace(lo_o[n] + 0.01, hi_o[n] - 0.01, max(2, min(16, int((hi_o[n] - lo_o[n]) / 0.05)))) for n in range(2)]
                G0, G1 = np.meshgrid(*g, indexing='ij'); pts = np.zeros((G0.size, 3)); pts[:, ax] = mid; pts[:, o[0]] = G0.ravel(); pts[:, o[1]] = G1.ravel()
                near = S[(S[:, ax] <= mid) & (S[:, ax + 3] >= mid) & (S[:, o[0]] < hi_o[0]) & (S[:, o[0] + 3] > lo_o[0]) & (S[:, o[1]] < hi_o[1]) & (S[:, o[1] + 3] > lo_o[1])]
                inside = np.zeros(len(pts), bool)
                for q in near: inside |= np.all((pts >= q[:3] - 1e-4) & (pts <= q[3:] + 1e-4), 1)
                cell = ((hi_o[0] - lo_o[0]) / len(g[0])) * ((hi_o[1] - lo_o[1]) / len(g[1]))
                if (~inside).sum() * cell >= 0.01:                                  # an open slit of 10 x 10 cm or more
                    bad['SLIT'].append(([round(float(x), 3) for x in a], [round(float(x), 3) for x in b], round(float(gap), 3)))
    return bad
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent and o.parent.name.startswith('jc_courts_') and not o.name.startswith('col')
        and (ROOMS is None or any(o.parent.name[len('jc_courts_'):].startswith(r) for r in ROOMS))]
solids = np.load(P3 / 'out' / 'solids.npy')
if PLANT:                                                                 # prove each check finds its defect first
    import bmesh
    me = bpy.data.meshes.new('planted'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.5); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(0.2, 3, 'Z'), verts=bm.verts)
    bm.to_mesh(me)
    src = next(m for m in bpy.data.materials if m.node_tree and m.node_tree.nodes.get('DiffuseSampler') and m.node_tree.nodes.get('BumpSampler'))
    fm = src.copy(); fm.name = 'planted paint'; fm.node_tree.nodes['DiffuseSampler'].image = bpy.data.images.new('planted_flat', 16, 16)
    fm.node_tree.nodes['BumpSampler'].image = None
    me.materials.append(fm); me.uv_layers.new(name='UVMap 0'); po = bpy.data.objects.new('planted', me); bpy.context.scene.collection.objects.link(po)
    planted_solids = np.array([[0, 0, 0, 1, 1, 3], [1.02, 0, 0, 1.3, 1, 3]], np.float64)
    r = run([po], planted_solids)
    ok = r['ANGLE'] and r['SLIT'] and r['FLAT']
    print('JC5_SURFACE_PLANT_FOUND' if ok else f'JC5_SURFACE_PLANT_MISSED {[(k, len(v)) for k, v in r.items()]}'); sys.exit(0 if ok else 1)
r = run(objs, solids)
out = {k: v for k, v in r.items()}
json.dump(out, open(P3 / 'out' / 'surface_gate.json', 'w'), indent=1)
by_room = {}
for k, v in r.items():
    for e in v:
        nm = e[0] if isinstance(e[0], str) else 'solids'; by_room.setdefault(k, {}).setdefault(nm.split('.')[0], 0); by_room[k][nm.split('.')[0]] += 1
print('JC5_SURFACE', json.dumps({k: len(v) for k, v in r.items()}))
for k, d in by_room.items(): print(' ', k, sorted(d.items(), key=lambda x: -x[1])[:12])
print('JC5_SURFACE_PASS' if not any(r.values()) else 'JC5_SURFACE_FAIL')
