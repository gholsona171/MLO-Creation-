"""(read-only) The vertex colour layers of drawables: per layer the mean / 10th / 90th percentile of R, G, B, A - what Rockstar
bakes into its ground (colour 0: R = natural ambient, G = artificial ambient, B = emissive, A = (unused / wind)).
Run: blender -b --python vcol_stats.py -- <ydr dir> name1,name2,..."""
import bpy, sys, numpy as np
from pathlib import Path
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
a = sys.argv[sys.argv.index('--') + 1:]; D = Path(a[0]).resolve()
for n in a[1].split(','):
    bpy.ops.wm.read_homefile(use_empty=True); bpy.ops.sollumz.import_assets(directory=str(D), files=[{'name': n + '.ydr'}])
    for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
        for at in ob.data.color_attributes:
            c = np.zeros(len(at.data) * 4, np.float32); at.data.foreach_get('color', c); c = c.reshape(-1, 4)
            print('VCOL', n, ob.name[:30], at.name, 'mean', np.round(c.mean(0), 2).tolist(), 'p10', np.round(np.percentile(c, 10, 0), 2).tolist(),
                  'p90', np.round(np.percentile(c, 90, 0), 2).tolist(), flush=True)
