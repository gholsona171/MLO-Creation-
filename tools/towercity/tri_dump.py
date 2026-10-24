"""Tower City survey tool: world-space triangles of vanilla drawables (HIGH lod) for exact geometry work.
Run: blender -b --python tri_dump.py -- <dir> <out.json> name1 name2 ...  -> [[model, material, [x,y,z]*3], ...]"""
import bpy, bmesh, sys, json, glob
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
def entity_pos(name):
    for f in glob.glob(str(T / 'src/ymap/*.ymap.xml')):
        for e in E.parse(f).getroot().iter('Item'):
            if (e.findtext('archetypeName') or '').lower() == name:
                p = e.find('position'); return Vector((float(p.get('x')), float(p.get('y')), float(p.get('z'))))
    if name.startswith('hei_'): return entity_pos(name[4:])
    raise SystemExit('no entity for ' + name)
a = sys.argv[sys.argv.index('--') + 1:]; d, out, names = Path(a[0]), a[1], a[2:]
rows = []
for name in names:
    org = entity_pos(name)
    bpy.ops.wm.read_homefile(use_empty=True)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(d), files=[{'name': name + '.ydr'}])
    root = bpy.data.objects.get(name) or [o for o in bpy.data.objects if o.parent is None and o.sollum_type == 'sollumz_drawable'][0]
    for m in [c for c in root.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        l = m.sz_lods.get_lod(LODLevel.HIGH)
        if l is None or l.mesh is None: continue
        me = l.mesh; mw = m.matrix_world; me.calc_loop_triangles()
        for t in me.loop_triangles:
            vs = [(mw @ me.vertices[i].co) + org for i in t.vertices]
            mat = me.materials[t.material_index].name if me.materials else ''
            rows.append([name, mat] + [[round(v.x, 3), round(v.y, 3), round(v.z, 3)] for v in vs])
json.dump(rows, open(out, 'w'))
print('TRI_DUMP', len(rows), flush=True)
