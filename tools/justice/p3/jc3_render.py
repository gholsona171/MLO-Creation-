"""Phase 3 preview renders (Blender + Sollumz, Cycles): our built room drawable(s) from work/p3/out, every placed Rockstar prop and
door imported from its CodeWalker XML (work/p3/survey/vanilla, textures from the game in vanilla/_tex), and phase 2's exterior
models from work/p2/out (read only) placed at their centres - so the views show the room in its building, the glass, the
neighbours and the plaza. PREVIEW ONLY (nothing here is shipped): Rockstar's glass shaders are swapped for a Blender glass so
the curtain wall reads, and phase 2's curtain glass is cut where p2_changes.md item 3 will cut the door openings.
Run: blender -b --python jc3_render.py -- <out dir> [view ...]   (pass line JC3_RENDER_PASS)"""
import sys, json, math, shutil
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
P3 = Path(__file__).resolve().parent; WK = P3.parent
sys.path[:0] = [str(P3), str(WK / 'p2'), str(WK)]
import jc3_plan as JP
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUTD = Path(argv[0]) if argv else P3 / 'renders'; OUTD.mkdir(parents=True, exist_ok=True)
ONLY = set(argv[1:])
VAN = P3 / 'survey/vanilla'; TEX = VAN / '_tex'
L = json.load(open(P3 / 'out/jc3_layout.json')); L2 = json.load(open(WK / 'p2/out/p2_layout.json'))
bpy.ops.wm.read_homefile(use_empty=True)
scn = bpy.context.scene
def imp(directory, name):
    before = set(bpy.data.objects)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(directory), files=[{'name': name}])
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    return roots, new
# ---------------- our room(s) ----------------
for k, d in L['drawables'].items():
    imp(P3 / 'out', k + '.ydr')
# ---------------- phase 2 exteriors (read only), at their centres ----------------
EXT = ['jc_atrium', 'jc_tower', 'jc_police', 'jc_jail1', 'jc_site']
for n in EXT:
    roots, new = imp(WK / 'p2/out', n + '.ydr'); c = L2['drawables'][n]['centre']
    for r in roots: r.location = Vector(c)
    if n == 'jc_atrium':                                            # cut the door openings out of the curtain glass (render only)
        for o in new:
            if o.type != 'MESH': continue
            mw = o.matrix_world.copy(); bpy.context.view_layer.update(); mw = o.matrix_world
            bm = bmesh.new(); bm.from_mesh(o.data); dead = []
            for f in bm.faces:
                cw_ = mw @ f.calc_center_median()
                for _, _, s0, s1, z0, z1 in JP.door_openings():
                    if abs(cw_.x - JP.DOOR_U) < 0.25 and s0 < cw_.y < s1 and z0 - 0.01 < cw_.z < z1 + 0.6 and abs((mw.to_3x3() @ f.normal).x) > 0.9: dead.append(f); break
            if dead: bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(o.data)
            bm.free()
# ---------------- props: one import per model, linked copies per placement ----------------
SRC = {}
def model_obj(model):
    if model in SRC: return SRC[model]
    x = VAN / f'{model}.ydr.xml'
    if not x.exists(): SRC[model] = None; return None
    td = VAN / model; td.mkdir(exist_ok=True)
    if TEX.exists():
        for f in TEX.glob('*.dds'):
            if not (td / f.name).exists(): shutil.copy(f, td / f.name)
    roots, new = imp(VAN, f'{model}.ydr.xml'); r = roots[0]; r.location = (0, 0, -500); SRC[model] = r; return r
def place(model, u, v, z, h):
    r = model_obj(model)
    if r is None:                                                       # not exported: its bounds as a grey box (labelled in the report)
        return
    c = r.copy(); scn.collection.objects.link(c)
    for ch in r.children_recursive:
        cc = ch.copy(); scn.collection.objects.link(cc); cc.parent = c
    c.location = (u, v, z); c.rotation_euler = (0, 0, math.radians(h))
for p in L['props']: place(p['model'], *p['pos'], p['heading'])
# ---------------- preview glass: a Blender glass for every glass shader (Rockstar's glass shaders do not render here) ----------------
for m in bpy.data.materials:
    fn = getattr(getattr(m, 'shader_properties', None), 'filename', '') or ''
    if 'glass' in fn or 'glass' in m.name.lower():
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); g = nt.nodes.new('ShaderNodeBsdfGlass'); g.inputs['Roughness'].default_value = 0.02
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.25 if 'dark' not in m.name.lower() else 0.8
        tint = (0.55, 0.62, 0.62, 1) if 'atrium' in m.name.lower() or 'rail' in m.name.lower() else (0.1, 0.1, 0.1, 1)
        g.inputs['Color'].default_value = tint; nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(g.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
# missing textures (txds not extracted for a preview): neutral grey instead of Blender's magenta
for im in bpy.data.images:
    try: ok = im.has_data or (im.filepath and Path(bpy.path.abspath(im.filepath)).exists()) or im.packed_file
    except Exception: ok = False
    if not ok: im.source = 'GENERATED'; im.generated_color = (0.42, 0.41, 0.39, 1.0); im.generated_width = im.generated_height = 8
# ---------------- light: sky + sun (13:00-ish), the room's lamps as small area lights ----------------
w = bpy.data.worlds.new('sky'); scn.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(55); sky.sun_rotation = math.radians(200)
nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.35
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 2.5; so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(35), 0, math.radians(200))
for u, v, z, m in JP.wall_lights():
    l = bpy.data.lights.new('wl', 'AREA'); l.energy = 120; l.size = 0.6; o = bpy.data.objects.new('wl', l); scn.collection.objects.link(o)
    k = 0 if m[1] == 'u' else 1; sg = 1 if m[0] == '+' else -1; pos = [u, v, z]; pos[k] -= sg * 0.2; o.location = pos
    o.rotation_euler = (math.radians(90), 0, math.radians({'+u': 90, '-u': 270, '+v': 180, '-v': 0}[m]))
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 40; scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1600, 900; scn.view_settings.view_transform = 'AgX'; scn.view_settings.exposure = -0.9
VIEWS = {   # name: (camera lot-frame position, target, lens mm)
    'p3_a1_entry_inside':   ((36.6, 9.6, 30.45), (22.0, -1.0, 29.6), 18),
    'p3_a1_checkpoint':     ((20.5, 9.5, 30.45), (33.0, 1.0, 29.7), 18),
    'p3_a1_galleria':       ((-7.0, -6.0, 36.5), (20.0, 15.0, 29.0), 16),
    'p3_a1_wing_north':     ((11.8, 19.0, 30.45), (0.0, 45.0, 30.8), 18),
    'p3_a1_plaza':          ((54.0, 4.0, 30.4), (30.0, 4.0, 31.0), 24),
    'p3_a1_inscription':    ((8.0, 12.0, 30.45), (-8.2, 19.5, 33.5), 22),
}
done = []
for name, (pos, tgt, lens) in VIEWS.items():
    if ONLY and name not in ONLY: continue
    cam = bpy.data.cameras.new(name); cam.lens = lens; co = bpy.data.objects.new(name, cam); scn.collection.objects.link(co)
    co.location = pos; co.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    scn.camera = co; scn.render.filepath = str(OUTD / f'{name}.png'); bpy.ops.render.render(write_still=True); done.append(name)
    print('RENDERED', name, flush=True)
missing = sorted({p['model'] for p in L['props'] if SRC.get(p['model']) is None})
print('JC3_RENDER_PASS', json.dumps({'views': done, 'props_not_drawn': missing}), flush=True)
