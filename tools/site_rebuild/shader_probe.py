"""(read-only) A vanilla drawable's recipe through Sollumz: per mesh, each material's shader file, its texture samplers, and the
vertex colour / UV layers with their channel statistics (what drives a terrain blend). Run:
blender -b --python shader_probe.py -- <ydr dir> name1,name2"""
import bpy, sys, numpy as np
from pathlib import Path
a = sys.argv[sys.argv.index('--') + 1:]; D = Path(a[0]).resolve()
for n in a[1].split(','):
    bpy.ops.wm.read_homefile(use_empty=True); bpy.ops.sollumz.import_assets(directory=str(D), files=[{'name': n + '.ydr'}])
    for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
        me = ob.data; print('MESH', n, ob.name[:40], 'faces', len(me.polygons), flush=True)
        for m in me.materials:
            if not m: continue
            sh = getattr(m, 'shader_properties', None); fn = sh.filename if sh else '?'
            texs = [f'{nd.name}={nd.image.name if nd.image else None}' for nd in m.node_tree.nodes if nd.type == 'TEX_IMAGE']
            print('  MAT', m.name, 'shader', fn, '|', ' '.join(texs), flush=True)
        for at in me.color_attributes:
            c = np.zeros(len(at.data) * 4, np.float32); at.data.foreach_get('color', c); c = c.reshape(-1, 4)
            print('  COL', at.name, at.domain, 'mean', np.round(c.mean(0), 2).tolist(), 'p10', np.round(np.percentile(c, 10, 0), 2).tolist(), 'p90', np.round(np.percentile(c, 90, 0), 2).tolist())
        for uv in me.uv_layers:
            u = np.zeros(len(uv.data) * 2, np.float32); uv.data.foreach_get('uv', u); u = u.reshape(-1, 2)
            print('  UV', uv.name, 'range', np.round(u.min(0), 2).tolist(), np.round(u.max(0), 2).tolist())
        xs = [v.co for v in me.vertices]; print('  SIZE', [round(max(v[k] for v in xs) - min(v[k] for v in xs), 1) for k in range(3)])
