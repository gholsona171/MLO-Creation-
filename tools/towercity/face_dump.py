"""Tower City survey tool: dump the faces of vanilla drawables (world space) for planning cuts.
Run: blender -b --python face_dump.py -- <dir> <out.json> name1 name2 ...   (dir = src/native or work/cut)
Each face: [model, material name, cx, cy, cz, nz, area, zmin, zmax]. Entity position from src/ymap (l0_cut.entity_pos rule)."""
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
        me = l.mesh; mw = m.matrix_world
        for f in me.polygons:
            vs = [(mw @ me.vertices[i].co) + org for i in f.vertices]
            c = sum(vs, Vector()) / len(vs); n = (mw.to_3x3() @ f.normal).normalized()
            mat = me.materials[f.material_index].name if me.materials else ''
            rows.append([name, mat, round(c.x, 3), round(c.y, 3), round(c.z, 3), round(n.z, 3), round(f.area, 3), round(min(v.z for v in vs), 3), round(max(v.z for v in vs), 3)])
json.dump(rows, open(out, 'w'))
print('FACE_DUMP', len(rows), flush=True)
