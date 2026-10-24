"""Tower City survey tool: which collision objects of a ybn reach a lot-frame box.
Run: blender -b --python col_near.py -- <dir> <u0> <u1> <v0> <v1> <z0> <z1> name1 name2 ...   (names without .ybn)
Prints per object: file, object name, sollum type, primitive count / faces, world bbox (lot frame u/v + z), materials."""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector
H = math.radians(69.5); O = (-78.897, -827.328)
def L(p): dx, dy = p.x - O[0], p.y - O[1]; return dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H)
a = sys.argv[sys.argv.index('--') + 1:]; d = a[0]; U0, U1, V0, V1, Z0, Z1 = map(float, a[1:7]); names = a[7:]
for name in names:
    bpy.ops.wm.read_homefile(use_empty=True)
    if 'FINISHED' not in bpy.ops.sollumz.import_assets(directory=d, files=[{'name': name + '.ybn'}]): print('COL_NEAR fail', name); continue
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.data.vertices: continue
        mw = ob.matrix_world
        if ob.sollum_type == 'sollumz_bound_poly_triangle':
            for f in ob.data.polygons:
                vs = [mw @ ob.data.vertices[i].co for i in f.vertices]; c = sum(vs, Vector()) / len(vs); u, v = L(c)
                if U0 <= u <= U1 and V0 <= v <= V1 and Z0 <= c.z <= Z1:
                    m = ob.data.materials[f.material_index]
                    print('COL_NEAR', name, ob.name, 'tri', round(u, 2), round(v, 2), round(c.z, 2), 'nz', round(f.normal.z, 2), m.name if m else '')
        else:
            vs = [mw @ v.co for v in ob.data.vertices]; c = sum(vs, Vector()) / len(vs); u, v = L(c)
            lo = min(p.z for p in vs); hi = max(p.z for p in vs)
            if U0 <= u <= U1 and V0 <= v <= V1 and hi >= Z0 and lo <= Z1:
                print('COL_NEAR', name, ob.name, ob.sollum_type, round(u, 2), round(v, 2), 'z', round(lo, 2), round(hi, 2), [m.name for m in ob.data.materials][:2])
