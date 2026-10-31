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
bpy.ops.wm.open_mainfile(filepath=str(P3 / 'out/jc3_scene.blend'))                  # the build's own scene (our rooms as built)
for o in list(bpy.data.objects):                                                      # the collision composites stay out of the picture
    if 'bound' in str(getattr(o, 'sollum_type', '')).lower() or o.name.startswith('col'): o.hide_render = True
scn = bpy.context.scene
def imp(directory, name):
    before = set(bpy.data.objects)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(directory), files=[{'name': name}])
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    return roots, new
# ---------------- our room(s) ----------------
# ---------------- phase 2 exteriors (read only), at their centres ----------------
EXT = ['jc_atrium', 'jc_tower', 'jc_police', 'jc_jail1', 'jc_site']                     # (the tower's model is needed: the rooms look out through its glass)
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
    x = next((VAN / f'{model}.{k}.xml' for k in ('ydr', 'yft') if (VAN / f'{model}.{k}.xml').exists()), None)   # yft: fragments (vending, TVs)
    if x is None: SRC[model] = None; return None
    td = VAN / model; td.mkdir(exist_ok=True)
    if TEX.exists():
        for f in TEX.glob('*.dds'):
            if not (td / f.name).exists(): shutil.copy(f, td / f.name)
    roots, new = imp(VAN, x.name); r = roots[0]; r.location = (0, 0, -500); SRC[model] = r
    for o in new:                                                       # a fragment's collision / bounds stay out of the picture
        if 'bound' in str(getattr(o, 'sollum_type', '')).lower() or o.name.lower().startswith('col'): o.hide_render = True
    return r
def place(model, u, v, z, h):
    r = model_obj(model)
    if r is None:                                                       # not exported: its bounds as a grey box (labelled in the report)
        return
    c = r.copy(); scn.collection.objects.link(c)
    for ch in r.children_recursive:
        cc = ch.copy(); scn.collection.objects.link(cc); cc.parent = c; cc.hide_render = ch.hide_render
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
for k, zs in L['zones'].items():                    # the tower rooms' lamps (the game's lights are not Blender lights in the saved scene):
    if k == 'galleria': continue                    # area lights on a 4 m grid under each room region's ceiling, pointing down
    for u0, u1, v0, v1, z0, z1 in zs:
        if (u1 - u0) < 1.4 or (v1 - v0) < 1.4: continue
        nu, nv = max(1, int((u1 - u0) // 4.0)), max(1, int((v1 - v0) // 4.0))
        for i in range(nu):
            for j in range(nv):
                l = bpy.data.lights.new('tl', 'AREA'); l.shape = 'RECTANGLE'; l.size, l.size_y = 1.2, 0.3; l.energy = 160
                o = bpy.data.objects.new('tl', l); scn.collection.objects.link(o)
                o.location = (u0 + (u1 - u0) * (i + 0.5) / nu, v0 + (v1 - v0) * (j + 0.5) / nv, z1 - 0.45)
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
import jc3_tower as JT
F3, F5 = JT.F3, JT.F5
VIEWS.update({   # area 2
    'p3_a2_courtroom_gallery': ((25.7, 23.6, F3 + 1.7), (25.3, 40.0, F3 + 1.4), 18),
    'p3_a2_courtroom_bench':   ((25.3, 39.3, F3 + 1.85), (25.3, 24.0, F3 + 0.9), 18),
    'p3_a2_courtroom_jury':    ((29.6, 33.0, F3 + 1.6), (20.0, 33.0, F3 + 0.9), 20),
    'p3_a2_lobby':             ((45.6, 22.4, JT.F1 + 1.7), (22.0, 45.0, JT.F1 + 2.5), 16),
    'p3_a2_vestibule':         ((27.0, 12.0, JT.F1 + 1.6), (27.0, 30.0, JT.F1 + 1.6), 20),
    'p3_a2_public_corridor':   ((15.4, 20.3, F3 + 1.7), (45.0, 20.6, F3 + 1.4), 18),
    'p3_a2_jury_room':         ((23.6, 43.8, F3 + 1.7), (16.0, 53.0, F3 + 0.8), 18),
    'p3_a2_chambers':          ((31.6, 43.8, F3 + 1.7), (26.0, 53.0, F3 + 0.8), 18),
    'p3_a2_holding':           ((31.95, 25.9, F3 + 1.6), (32.6, 36.0, F3 + 1.1), 18),
    'p3_a2_stair':             ((42.2, 32.9, JT.F1 + 1.6), (37.0, 32.9, JT.F1 + 2.6), 18),
    'p3_a2_courtroomB':        ((25.7, 23.6, F5 + 1.7), (25.3, 40.0, F5 + 1.4), 18),
})
VIEWS.update({   # area 3: the Police HQ and its B1 garage
    'p3_a3_lobby':       ((41.0, -38.5, 30.6), (34.0, -20.0, 30.0), 18),
    'p3_a3_counter':     ((38.0, -22.0, 30.5), (32.8, -22.0, 30.2), 20),
    'p3_a3_open_office': ((12.0, -28.0, 33.7), (20.0, -46.0, 32.8), 18),
    'p3_a3_interview':   ((12.0, -51.5, 33.6), (14.2, -53.0, 33.4), 18),
    'p3_a3_observe':     ((15.9, -52.8, 33.6), (12.0, -52.8, 33.3), 20),
    'p3_a3_garage':      ((12.5, -55.0, 27.4), (30.0, -20.0, 26.6), 16),
    'p3_a3_workshop':    ((25.0, -26.0, 27.3), (34.0, -16.0, 26.3), 18),
    'p3_a3_ramp':        ((22.5, -54.5, 26.8), (44.0, -54.5, 28.6), 20),
    'p3_a3_briefing': ((20.5, -25.5, 30.4), (14.0, -14.5, 29.9), 18),
    'p3_a3_captain': ((11.3, -17.3, 33.6), (19.0, -9.0, 33.0), 18),
    'p3_a3_lockers': ((11.3, -39.5, 30.4), (17.0, -30.0, 29.8), 18),
    'p3_a3_break': ((11.2, -13.0, 30.4), (16.8, -8.0, 29.9), 18),
    'p3_a3_records': ((25.0, -42.0, 33.6), (31.0, -55.0, 32.8), 18),
    'p3_a3_store': ((34.0, -41.5, 27.2), (43.0, -46.0, 26.2), 18),
})
SET = [a for a in ONLY if a in ('area1', 'area2', 'area3')]
if SET: ONLY = {k for k in VIEWS if k.startswith({'area1': 'p3_a1', 'area2': 'p3_a2', 'area3': 'p3_a3'}[SET[0]])}
if 'p3_a2_lobby' in ONLY or not ONLY: scn.cycles.samples = 24; scn.render.resolution_x, scn.render.resolution_y = 1280, 720
done = []
for name, (pos, tgt, lens) in VIEWS.items():
    if ONLY and name not in ONLY: continue
    cam = bpy.data.cameras.new(name); cam.lens = lens; co = bpy.data.objects.new(name, cam); scn.collection.objects.link(co)
    co.location = pos; co.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    scn.camera = co; scn.render.filepath = str(OUTD / f'{name}.png'); bpy.ops.render.render(write_still=True); done.append(name)
    print('RENDERED', name, flush=True)
missing = sorted({p['model'] for p in L['props'] if SRC.get(p['model']) is None})
print('JC3_RENDER_PASS', json.dumps({'views': done, 'props_not_drawn': missing}), flush=True)
