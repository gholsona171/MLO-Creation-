"""Tower City survey tool: Rockstar's own sidewalk faces round the lots - per corner: world position, vertex colour 0, UV - plus the
material itself (shader, sampler texture names) and its texel scale / direction. The lot paving copies all of it (sidewalk_mat.py):
a paving that reads as the base sidewalk must have its texture, its tint (vertex colour) and its scale.
Run: blender -b --python sidewalk_dump.py -- <dir> <out.json> <material regex> name1 name2 ...
Out: {'mats': {name: {'shader', 'textures', 'm_per_uv', 'uv_angle_deg' (lot frame)}}, 'corners': [[mat, x, y, z, r, g, b, a (sRGB, as stored), u, v], ...]}"""
import bpy, sys, json, glob, re, math
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
H = math.radians(69.5)
def entity_pos(name):
    for f in glob.glob(str(T / 'src/ymap/*.ymap.xml')):
        for e in E.parse(f).getroot().iter('Item'):
            if (e.findtext('archetypeName') or '').lower() == name:
                p = e.find('position'); return Vector((float(p.get('x')), float(p.get('y')), float(p.get('z'))))
    raise SystemExit('no entity for ' + name)
a = sys.argv[sys.argv.index('--') + 1:]; d, out, rx, names = Path(a[0]), a[1], re.compile(a[2]), a[3:]
mats = {}; corners = []
for name in names:
    org = entity_pos(name)
    bpy.ops.wm.read_homefile(use_empty=True)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(d), files=[{'name': name + '.ydr'}])
    root = bpy.data.objects.get(name) or [o for o in bpy.data.objects if o.parent is None and o.sollum_type == 'sollumz_drawable'][0]
    for m in [c for c in root.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        l = m.sz_lods.get_lod(LODLevel.HIGH)
        if l is None or l.mesh is None: continue
        me = l.mesh; mw = m.matrix_world; uvl = me.uv_layers[0] if me.uv_layers else None
        col = me.color_attributes[0] if me.color_attributes else None
        for i, mt in enumerate(me.materials):
            if not mt or not rx.search(mt.name.lower()): continue
            st = mats.setdefault(mt.name, {'shader': mt.shader_properties.filename, 'textures': {}, 'scales': [], 'angles': [], 'from': name})
            for n in mt.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image: st['textures'][n.name] = n.image.name.split('.')[0]
            for p in me.polygons:
                if p.material_index != i: continue
                L = list(p.loop_indices)
                for li in L:
                    v = mw @ me.vertices[me.loops[li].vertex_index].co + org
                    c = list(col.data[li].color_srgb) if col is not None and col.domain == 'CORNER' else [1, 1, 1, 1]   # (the stored GTA value)
                    uv = list(uvl.data[li].uv) if uvl is not None else [0, 0]
                    corners.append([mt.name, round(v.x, 3), round(v.y, 3), round(v.z, 3)] + [round(x, 4) for x in c] + [round(uv[0], 4), round(uv[1], 4)])
                if uvl is None or len(L) < 3 or abs(p.normal.z) < 0.8: continue
                p0, p1, p2 = [mw @ me.vertices[me.loops[li].vertex_index].co for li in L[:3]]
                u0, u1, u2 = [uvl.data[li].uv for li in L[:3]]
                e1, e2 = p1 - p0, p2 - p0; t1, t2 = u1 - u0, u2 - u0
                det = t1.x * t2.y - t2.x * t1.y
                if abs(det) < 1e-9: continue
                Tg = (e1 * t2.y - e2 * t1.y) / det                     # d(world)/d(u): the texture's u axis in the world, metres per UV
                if Tg.length < 1e-6: continue
                st['scales'].append(Tg.length); ang = math.degrees(math.atan2(Tg.y, Tg.x) - H) % 90.0
                st['angles'].append(ang)
for k, st in mats.items():
    s = sorted(st.pop('scales')); g = sorted(st.pop('angles'))
    st['m_per_uv'] = s[len(s) // 2] if s else None; st['uv_angle_deg'] = g[len(g) // 2] if g else None
json.dump({'mats': mats, 'corners': corners}, open(out, 'w'))
print('SIDEWALK_DUMP', json.dumps({k: {kk: v for kk, v in st.items() if kk != 'textures'} for k, st in mats.items()}), len(corners), flush=True)
