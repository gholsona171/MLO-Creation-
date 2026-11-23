"""The site cut out of the distance models (LOD / SLOD) that site_clear.py had to leave in place (lod_list.py lists them,
lod_extract.ps1 pulls their dictionaries). Every face of a listed model whose centre lies where site_col.py clears (the site, the old
wall line, the old board's posts; never the pole barn) is deleted, except
  * ground (facing up, within GROUND_UP of the paving height): a land SLOD keeps its surface, or far views would show a hole;
  * the standing power poles (within POLE_R in plan of one: they all stay, Antonio).
Models with nothing over the site are left alone; a dictionary is written only when one of its models changed (the others in it go
through unchanged). Textures stay in Rockstar's dictionaries (not embedded).
Run: blender -b --python lod_cut.py -- <dictionary name>       (lod_all.sh runs every dictionary)
Input ../vanilla/lod/<dictionary>.ydd + targets.tsv + ../site/lod_targets.tsv. Output ../site/lodcut/<dictionary>.ydd"""
import bpy, bmesh, sys, math
from pathlib import Path
from mathutils import Vector, Quaternion
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, yard_plan as Y, pave_ground as PG
M_ = T.parent; SRC = M_ / 'vanilla' / 'lod'; OUT = M_ / 'site' / 'lodcut'; OUT.mkdir(parents=True, exist_ok=True)
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
GROUND_UP, POLE_R = 1.0, 0.6                                        # (1.5 m kept the bushes at the poles' feet)
SIGN = (2294.8, 2304.0, 3114.4, 3118.0)                       # (= site_col.py)
def in_barn(x, y): return SP.BARN[0] <= x <= SP.BARN[2] and SP.BARN[1] <= y <= SP.BARN[3] and Y.dist_to_loop(x, y) > 0.9
def in_sign(x, y): return SIGN[0] <= x <= SIGN[1] and SIGN[2] <= y <= SIGN[3]
def cleared(x, y): return (SP.on_site(x, y) or Y.dist_to_loop(x, y) <= 0.9 or in_sign(x, y)) and not in_barn(x, y)
POLES = [(float(r.split('\t')[1]), float(r.split('\t')[2])) for r in (M_ / 'site' / 'poles.tsv').read_text().splitlines() if r.strip()]
def by_pole(x, y): return any(math.hypot(x - px, y - py) <= POLE_R for px, py in POLES)
def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; return (h + (h << 15)) & 0xFFFFFFFF
def hash_of(name):
    n = name.lower().split('.')[0]
    return int(n[5:13], 16) if n.startswith('hash_') else joaat(n)

dname = sys.argv[sys.argv.index('--') + 1]
place = {}                                                           # drawable hash -> (position, rotation) of its one placement
for r in (M_ / 'site' / 'lod_targets.tsv').read_text().splitlines():
    a, x, y, z, qx, qy, qz, qw = r.split('\t')
    place[hash_of(a)] = (Vector((float(x), float(y), float(z))), Quaternion((float(qw), float(qx), float(qy), float(qz))).conjugated())   # (ymap stores the conjugate)
mine = {int(h, 16) for t, d, h in (r.split('\t') for r in (SRC / 'targets.tsv').read_text().splitlines()) if d == dname}
(OUT / f'{dname}.ydd').unlink(missing_ok=True)
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': dname + '.ydd'}])
for m in bpy.data.materials:
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and hasattr(nd, 'texture_properties'): nd.texture_properties.embedded = False
cut = {}
for dr in [o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable']:
    h = hash_of(dr.name)
    if h not in mine: continue
    pos, rot = place[h]; n = 0
    for ob in [o for o in dr.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model']:
        loc = dr.matrix_world.inverted() @ ob.matrix_world                # model -> drawable frame, then the entity's placement
        W = lambda co: pos + rot @ (loc @ co); r3 = rot.to_matrix() @ loc.to_3x3()
        for level in LODLevel:
            lod = ob.sz_lods.get_lod(level); me = lod.mesh if lod else None
            if me is None or not me.polygons: continue
            bm = bmesh.new(); bm.from_mesh(me); dead = []
            for f in bm.faces:
                c = W(f.calc_center_median())
                if not cleared(c.x, c.y) or by_pole(c.x, c.y): continue
                up = (r3 @ f.normal).normalized().z > 0.7
                if up and c.z < PG.pave_z(c.x, c.y) + GROUND_UP: continue       # ground
                dead.append(f)
            if dead:
                bmesh.ops.delete(bm, geom=dead, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
                bm.to_mesh(me); n += len(dead)
            bm.free()
    if n: cut[dr.name] = n
print('LOD_CUT_STATS', dname, cut, flush=True)
if not cut: print('LOD_CUT_UNCHANGED', dname, flush=True); sys.exit(0)
root = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable_dictionary')
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
assert (OUT / f'{dname}.ydd').exists(), 'export wrote no .ydd'
print('LOD_CUT_PASS', dname, sum(cut.values()), 'faces in', len(cut), 'models', flush=True)
