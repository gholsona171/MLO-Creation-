"""Dump every material of vanilla drawables (shader, bucket, params, sampler texture names, metres per UV): the recipe source for p2.
Run: blender -b --python mat_dump.py -- <dir> <file.ydr> ..."""
import bpy, sys, json, math
from pathlib import Path
a = sys.argv[sys.argv.index('--') + 1:]; d = a[0]; out = {}
bpy.ops.wm.read_homefile(use_empty=True)
for f in a[1:]:
    before = set(bpy.data.materials)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=d, files=[{'name': f}])
    for m in bpy.data.materials:
        if m in before: continue
        sp = m.shader_properties; r = {'shader': sp.filename, 'bucket': sp.renderbucket, 'params': {}, 'tex': {}}
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE': r['tex'][n.name] = n.image.name if n.image else None
            elif hasattr(n, 'get_vec4'):
                try: r['params'][n.name] = [round(x, 3) for x in n.get_vec4()]
                except Exception: pass
            elif hasattr(n, 'get_value'):
                try: r['params'][n.name] = n.get_value()
                except Exception: pass
        # area-weighted face count / metres per uv
        tot = 0; mpu = []
        for o in bpy.data.objects:
            if o.type != 'MESH' or m.name not in [x.name for x in o.data.materials if x]: continue
            me = o.data; idx = [x.name if x else '' for x in me.materials].index(m.name); uv = me.uv_layers[0] if me.uv_layers else None
            for p in me.polygons:
                if p.material_index != idx: continue
                tot += p.area
                if uv and len(p.loop_indices) >= 3:
                    l = p.loop_indices; v0, v1 = me.vertices[me.loops[l[0]].vertex_index].co, me.vertices[me.loops[l[1]].vertex_index].co
                    du = (uv.data[l[0]].uv - uv.data[l[1]].uv).length
                    if du > 1e-5: mpu.append((v0 - v1).length / du)
        mpu.sort(); r['area'] = round(tot, 1); r['m_per_uv_med'] = round(mpu[len(mpu) // 2], 3) if mpu else None
        out[f + ':' + m.name] = r
print('MATDUMP ' + json.dumps(out))
