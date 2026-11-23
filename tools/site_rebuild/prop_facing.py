"""(read-only) Which way a vanilla prop faces in its own frame, measured from its mesh instead of guessed. For seats, beds, toilets,
sinks with a splash back: the tall part (the top 35 % of its height) sits at the BACK, so the back is the side the tall part's
centre leans to, and the prop faces the opposite way. Prints per prop: its extents, the back side (+x / -x / +y / -y), how clearly
(lean in m; under ~0.1 m it is a guess: check a photo), the extents (lo / hi: where the origin sits), and the heading that turns its front to face +y (north) in GTA terms (heading = degrees anticlockwise from north).
Run: blender -b --python prop_facing.py -- <ydr dir> name1,name2,...     -> FACING lines"""
import bpy, sys, math
from pathlib import Path
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
a = sys.argv[sys.argv.index('--') + 1:]; D = Path(a[0]).resolve(); names = a[1].split(',')
FRONT_HEADING = {'-y': 180.0, '+x': 90.0, '+y': 0.0, '-x': 270.0}     # heading that turns a front pointing this way to point +y
for n in names:
    if not (D / f'{n}.ydr').exists(): print('FACING', n, 'no ydr'); continue
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.sollumz.import_assets(directory=str(D), files=[{'name': n + '.ydr'}])
    V = []
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model']:
        lod = ob.sz_lods.get_lod(LODLevel.HIGH); me = lod.mesh if lod else ob.data
        V += [ob.matrix_world @ v.co for v in me.vertices]
    if not V: print('FACING', n, 'no mesh'); continue
    lo = [min(v[k] for v in V) for k in range(3)]; hi = [max(v[k] for v in V) for k in range(3)]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; zt = lo[2] + .65 * (hi[2] - lo[2])
    top = [v for v in V if v.z >= zt]
    tx = sum(v.x for v in top) / len(top) - cx; ty = sum(v.y for v in top) / len(top) - cy
    back = ('+x' if tx > 0 else '-x') if abs(tx) > abs(ty) else ('+y' if ty > 0 else '-y')
    front = {'+x': '-x', '-x': '+x', '+y': '-y', '-y': '+y'}[back]
    print('FACING', n, 'size', [round(hi[k] - lo[k], 2) for k in range(3)], 'lo', [round(c, 2) for c in lo], 'hi', [round(c, 2) for c in hi], 'back', back, 'lean', round(max(abs(tx), abs(ty)), 2),
          'front', front, 'face_north_heading', FRONT_HEADING[front], flush=True)
