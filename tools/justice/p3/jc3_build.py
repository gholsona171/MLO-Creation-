"""Justice Center phase 3, area 1: the atrium galleria (MLO jc_courts), rebuilt from jc3_plan every run (work/p3/out is wiped).
Tower City's tc_kit is the shared kit (imported, never edited); MLO-local = the lot frame (jc_frame origin + heading).
Outputs (work/p3/out): jc_courts_galleria.ydr (the room), jc_courts.ybn (interior collision, MLO-local, one BVH child per room),
tris_*.npy / mats_*.npy (the gates), zfight.json (the sweep), signs.json, anchors.json, jc3_layout.json (rooms, portals, props, doors,
seats, lights, zones for jc3_meta.py and the mlo-data writer).
Vertex colours: Rockstar's interiors, measured (tools/vcol_stats.py over work/p3/survey/vanilla): Colour0 R = natural ambient,
G = artificial ambient, B a third term; never the 1.0 default (it lit the exterior walls at night). Per room and surface (VCOL).
Run: blender -b --python jc3_build.py   (pass line JC3_BUILD_PASS)"""
import sys, json, math, shutil, time
from pathlib import Path
P3 = Path(__file__).resolve().parent; WK = P3.parent
sys.path[:0] = [r'C:\Users\anton\Documents\Codex\TowerCity\work', str(P3), str(WK / 'p2'), str(WK)]
import bpy, numpy as np
import tc_kit as TK
import jc_frame as F
import jc3_plan as JP
TK.set_origin(F.OX, F.OY, F.HDEG)
OUT = P3 / 'out'; shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
t0 = time.time()
TK.init(OUT, JP.ROOMS)
# ---------------- Rockstar's vertex colours per room / surface (sRGB 0..1, what Sollumz stores) ----------------
# galleria = a glazed room: Rockstar's glazed interiors (apa_mp_h_01_shell floor 154/107/255, walls 114/115/255; the Pacific
# Standard shell walls 47-116 / 106-176 / 255) -> natural ambient well up, artificial ambient mid. Emissive faces keep 1.0.
VCOL = {'galleria': {'floor': (0.60, 0.42, 1.0, 1.0), 'wall': (0.45, 0.45, 1.0, 1.0), 'ceiling': (0.40, 0.45, 1.0, 1.0)}}
DRAW2ROOM = {}
_orig_new = TK.K.new_drawable
def _new_drawable(name, parts, *a, **kw):
    root, lo, hi = _orig_new(name, parts, *a, **kw)
    room = DRAW2ROOM.get(name)
    if room:
        for o in root.children:
            if o.type != 'MESH': continue
            me = o.data; attr = me.color_attributes[0]; mats = [m.name if m else '' for m in me.materials]
            emis = ['emissive' in (m.shader_properties.filename if m else '') for m in me.materials]     # lamps, lit signs: 1.0
            col = np.zeros((len(me.loops), 4), np.float32)
            for p in me.polygons:
                nz = p.normal.z; c = (1, 1, 1, 1) if emis[p.material_index] else VCOL[room]['floor' if nz > .7 else 'ceiling' if nz < -.7 else 'wall']
                for li in p.loop_indices: col[li] = c
            if attr.domain == 'CORNER': attr.data.foreach_set('color_srgb', col.ravel())
            else:
                vc = np.zeros((len(me.vertices), 4), np.float32)
                for li, l in enumerate(me.loops): vc[l.vertex_index] = col[li]
                attr.data.foreach_set('color_srgb', vc.ravel())
            VC_DONE[name] = attr.name
    return root, lo, hi
VC_DONE = {}
TK.K.new_drawable = _new_drawable
# ---------------- materials: Rockstar's recipes (textures extracted to work/p3/tex_rs) ----------------

TEX = P3 / 'tex_rs'
def _img(name, noncolor):
    p = TEX / (name + '.dds')
    if not p.exists(): p = WK / 'p2' / 'tex_rs' / (name + '.dds')          # phase 2's extracted textures (read, never written)
    assert p.exists(), f'{name}.dds missing (work/p3/tex_rs or work/p2/tex_rs)'
    im = bpy.data.images.load(str(p), check_existing=True); im.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    if not im.packed_file: im.pack()
    return im
def rs(key, shader, samplers, params):
    m = TK.create_shader(shader); m.name = 'JC3 ' + key
    for s, tname in samplers.items():
        nd = m.node_tree.nodes.get(s); assert nd is not None, (key, s); nd.image = _img(tname, s != 'DiffuseSampler'); nd.texture_properties.embedded = True
    for s in ('BumpSampler', 'SpecSampler'):
        nd = m.node_tree.nodes.get(s)
        if nd is not None and s not in samplers:
            nn = np.ones((8, 8, 4), np.float32); nn[:, :, :2] = .5 if s == 'BumpSampler' else .3
            nd.image = TK.dds(f'jc3_{s.lower()}_{key}', nn, TK.OUT / 'tex', True); nd.texture_properties.embedded = True
    for p, v in params.items():
        q = m.node_tree.nodes.get(p)
        if q is not None: q.set_float(v)
    TK.MAT[key] = m; return m
rs('granite', 'normal.sps', {'DiffuseSampler': 'ko_gv_wall', 'BumpSampler': 'ko_gv_wall02_n'},            # = the exterior's granite (p2_mats)
   {'bumpiness': 1.0, 'specularIntensityMult': 0.4, 'specularFalloffMult': 100.0, 'specularFresnel': 0.95})
rs('marble', 'spec_reflect.sps', {'DiffuseSampler': 'gz_dlc_bfloormrble1', 'SpecSampler': 'gz_dlc_bfloormrble1_s',     # Pacific Standard's
   'EnvironmentSampler': 'v_tl_sky_r'},                                                                       # main floor (hei_obankbank_shell
   {'reflectivePower': 0.15, 'specularIntensityMult': 1.0, 'specularFalloffMult': 320.0, 'specularFresnel': 0.96})   # shader 19): grey travertine tiles
rs('band', 'default_spec.sps', {'DiffuseSampler': 'gz_dlc_bfloormrble2'},                                   # his border strip texture (shader 2):
   {'specularIntensityMult': 0.7, 'specularFalloffMult': 320.0, 'specularFresnel': 0.97})                   # the band faces sample its green marble strip
BAND_V = (0.13, 0.42)                                    # the strip's rows in his texture (v from the bottom; rows 288-456 of 512)
M_PER_UV = {'granite': 4.05, 'marble': 2.4}             # bfloormrble1 = 2 x 2 tiles: 1.2 m tiles
# ---------------- helpers ----------------
R = 'galleria'
ARCH = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
def bb(model):
    a = ARCH[model.lower()]; f = lambda s: [float(x[2:]) for x in s.split()]
    return f(a['bbMin']), f(a['bbMax'])
def place(model, u, v, base, heading, room=R, flags=None, centre=False):
    """a prop standing on `base`: z = base + max(0, -bbMin.z) (mid-height pivots, playbook 03); centre=True puts the CENTRE of its
    bounds (not its pivot) at (u, v)."""
    lo, hi = bb(model); z = base + max(0.0, -lo[2])
    if centre:
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; h = math.radians(heading)
        u -= cx * math.cos(h) - cy * math.sin(h); v -= cx * math.sin(h) + cy * math.cos(h)
    TK.prop(room, model, u, v, z, heading, flags)
    PLACED.append({'room': room, 'model': model, 'u': round(u, 3), 'v': round(v, 3), 'z': round(z, 3), 'heading': heading, 'base': base})
PLACED = []
def B(lo, hi, mat, col=True): TK.box(R, lo, hi, mat, col)
G = JP.G
# ---------------- floor ----------------
for u0, u1, v0, v1, kind in JP.floor_rects():
    B((u0, v0, G - JP.SLAB_T), (u1, v1, G), 'marble' if kind == 'field' else 'band')
# ---------------- the linings (granite), skirting, fins ----------------
def wall_box(w, a0, a1, z0, z1, dn=0.0, mat='granite', col=True):
    """a piece of wall w between a0 .. a1 along it; dn > 0 = that far proud of its room face (fins, skirting)."""
    axis, (lo, hi), *_ = JP.WALLS[w]
    room_side_hi = not ((axis == 'u' and lo < 0) or w == 'police')         # the room is on the hi side of the lining?
    if dn:
        lo, hi = (lo - dn, lo) if room_side_hi else (hi, hi + dn)
    if axis == 'u': B((lo, a0, z0), (hi, a1, z1), mat, col)
    else: B((a0, lo, z0), (a1, hi, z1), mat, col)
for w, (axis, (lo, hi), a0, a1, b) in JP.WALLS.items():
    wall_box(w, a0, a1, G - JP.SLAB_T, JP.ROOF)
    F_ = JP.fins(w); cuts = [(c - JP.FIN_W / 2, c + JP.FIN_W / 2) for c in F_]
    for c0, c1 in cuts: wall_box(w, c0, c1, G, JP.ROOF, dn=JP.FIN_P, col=True)
    xs = [a0] + [x for c in cuts for x in c] + [a1]
    for s0, s1 in zip(xs[0::2], xs[1::2]):                                     # skirting between the fins
        # a wall meeting this one at its end: the skirting stops at that wall's face (skirting is 2 cm proud)
        s0 += 0.0; s1 -= 0.0
        if s1 - s0 > 0.05: wall_box(w, s0 + (JP.SKIRT_P if s0 == a0 else 0), s1 - (JP.SKIRT_P if s1 == a1 else 0), G, G + JP.SKIRT_H, dn=JP.SKIRT_P, mat='band', col=False)
# ---------------- the perimeter's collision + the portals' clear zones ----------------
for lo, hi in JP.perimeter_col(): TK.colbox(R, lo, hi)
# ---------------- the screen line (glass in steel frames, 2.4 m) ----------------
def screen(axis, at, a0, a1, z0=G, h=JP.SCREEN_H, t=JP.SCREEN_T):
    """a glass screen on the line axis = at, from a0 to a1: steel posts at both ends and every <= 1.5 m, head and base rails,
    one glass pane per bay (never two layers), one collision slab."""
    def bx(p0, p1, q0, q1, z_0, z_1, mat, col=False):
        if axis == 'u': B((p0, q0, z_0), (p1, q1, z_1), mat, col)
        else: B((q0, p0, z_0), (q1, p1, z_1), mat, col)
    n = max(1, math.ceil((a1 - a0) / 1.5)); xs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]; pw = 0.06
    for i, x in enumerate(xs):
        x0 = x if i == 0 else (x - pw if i == n else x - pw / 2); x1 = x + pw if i == 0 else (x if i == n else x + pw / 2)
        bx(at - t / 2, at + t / 2, x0, x1, z0, z0 + h, 'steel')
    for i in range(n):
        x0 = xs[i] + (pw if i == 0 else pw / 2); x1 = xs[i + 1] - (pw if i == n - 1 else pw / 2)
        bx(at - t / 2, at + t / 2, x0, x1, z0, z0 + 0.10, 'steel')                     # base rail
        bx(at - t / 2, at + t / 2, x0, x1, z0 + h - 0.06, z0 + h, 'steel')             # head rail
        if axis == 'u': TK.glass_pane(R, [(at, x0, z0 + 0.10), (at, x1, z0 + 0.10), (at, x1, z0 + h - 0.06), (at, x0, z0 + h - 0.06)], 'railglass')
        else: TK.glass_pane(R, [(x0, at, z0 + 0.10), (x1, at, z0 + 0.10), (x1, at, z0 + h - 0.06), (x0, at, z0 + h - 0.06)], 'railglass')
    if axis == 'u': TK.colbox(R, (at - t / 2, a0, z0), (at + t / 2, a1, z0 + h))
    else: TK.colbox(R, (a0, at - t / 2, z0), (a1, at + t / 2, z0 + h))
for v0, v1 in JP.screen_runs():
    v0 = max(v0, JP.VA0 + JP.SKIRT_P); v1 = min(v1, JP.VA1 - JP.SKIRT_P)
    if v1 - v0 > 0.13: screen('u', JP.SCREEN_U, v0, v1)
screen('v', JP.EXIT_SPLIT_V, JP.EXIT_SPLIT_U[0] + JP.SCREEN_T / 2, JP.EXIT_SPLIT_U[1])
# ---------------- the screening lanes ----------------
for bv, dv in JP.LANES:
    place(JP.XRAY, JP.SCREEN_U, bv, G, 90.0)                         # the belt runs along u through the screen line
    place(JP.WTMD, JP.SCREEN_U, dv, G, 90.0)                         # walk through along -u
    for k, du in enumerate((0.9, -0.9)): place('ch_prop_ch_tray_01a', JP.SCREEN_U + du, bv, G + 1.0 + 0.02 * k, 90.0)   # trays on the belt bed
    TK.clear(f'lane {dv}', (JP.SCREEN_U - 2.0, dv - 0.42, G + 0.1), (JP.SCREEN_U - 0.6, dv + 0.42, G + 2.0))           # walk-out stays clear
# rope queue (Pacific Standard's stanchions)
for u, v, h, n in JP.QUEUE:
    du, dv = math.cos(math.radians(h)), math.sin(math.radians(h))
    for i in range(n + 1):
        place(JP.ROPE, u + du * JP.ROPE_L * i, v + dv * JP.ROPE_L * i, G, h if i < n else (h + 180.0) % 360.0)
# ---------------- the security desk (kit counter: collision) + Rockstar's props ----------------
d = JP.DESK; u0, u1 = d['u']; v0, v1 = d['v']; top = G + d['top']
B((u0 + 0.05, v0 + 0.05, G), (u1 - 0.05, v1 - 0.05, top - 0.04), 'granite')                        # body
B((u0, v0, top - 0.04), (u1, v1, top), 'band')                                                       # top
B((u0 - 0.45, v0 + 0.05, G + 0.72), (u0 + 0.05, v1 - 0.05, G + 0.76), 'band', col=False)              # the staff's work surface (west)
TK.colbox(R, (u0 - 0.45, v0 + 0.05, G + 0.72), (u0, v1 - 0.05, G + 0.76))
for k, vv in enumerate((-1.3, 1.3)):
    place('prop_off_chair_05', u0 - 0.95, vv, G, 90.0 + 180.0)                                           # chairs face +u (the lanes)
    place('prop_monitor_01a', u0 - 0.2, vv, G + 0.76, 90.0)                                               # screens face the staff (-u)
    place('prop_keyboard_01a', u0 - 0.38, vv, G + 0.76, 90.0)
place('prop_cctv_mon_02', u0 - 0.2, 0.0, G + 0.76, 90.0)
place('prop_police_radio_main', u0 + 0.35, -0.4, top, 90.0)
place('p_amb_clipboard_01', u0 + 0.4, 0.6, top, 100.0)
place('v_ret_gc_phone', u0 - 0.25, 2.2, G + 0.76, 90.0)
# the exit lane's guard podium (kit, collision)
p = JP.PODIUM; B((p['u'][0], p['v'][0], G), (p['u'][1], p['v'][1], G + 1.12), 'granite'); B((p['u'][0] - 0.03, p['v'][0] - 0.03, G + 1.12), (p['u'][1] + 0.03, p['v'][1] + 0.03, G + 1.16), 'band')
place('prop_cs_walkie_talkie', sum(p['u']) / 2, sum(p['v']) / 2, G + 1.16, 90.0)
# ---------------- the lobby ----------------
SEATS = []
def bench(u, v, h):
    place(JP.BENCH, u, v, G, h); SEATS.extend(JP.seat_points(JP.BENCH, u, v, G, h))
for cu, cv in JP.ISLANDS:                                                         # two benches back to back, a planter at each end
    bench(cu, cv - 0.5, 0.0); bench(cu, cv + 0.5, 180.0)
    for du in (-2.35, 2.35): place(JP.PLANTER, cu + du, cv, G, 0.0, centre=True)
for u, v, h in JP.WALL_BENCHES: bench(u, v, h)
for u, v in JP.WALL_PLANTERS: place(JP.PALM, u, v, G, 0.0, centre=True)
for i, m in enumerate(JP.FLAGS):
    u, va, vb = JP.FLAG_SPOT; place(m, u, va + (vb - va) * i / 2, G, 90.0)
for u, v, h in ((-7.75, 13.0, 90.0), (12.95, 44.0, 270.0)): place('prop_watercooler', u, v, G, h)
place('prop_vend_coffe_01', JP.UB1 - 0.56, 36.5, G, 270.0); place('prop_vend_soda_02', JP.UB1 - 0.72, 38.0, G, 270.0)
for u, v in ((JP.UA0 + 0.55, JP.VA0 + 0.55), (JP.UB1 - 0.55, 18.0), (36.9, JP.VA0 + 0.55), (36.9, JP.VA1 - 0.55)): place('prop_bin_11b', u, v, G, 0.0)
# extinguishers hang on a wall (pivot at the hook; back plane y +0.007): back 1.2 cm off the wall face
for u, v, h in ((JP.UA0 + 0.019, 1.0, 90.0), (JP.UB1 - 0.019, 30.0, 270.0), (30.0, JP.VA0 + 0.019, 180.0)): place('prop_fire_exting_2a', u, v, G + 0.4, h)
# ---------------- signs ----------------
ins = JP.INSCRIPTION; zc = sum(ins['z']) / 2
TK.sign(R, (JP.UA0 + 0.0, sum(ins['a']) / 2, zc), '+u', ins['a'][1] - ins['a'][0], ins['z'][1] - ins['z'][0], ins['lines'], 'TC sign jc inscription',
        bg=(58, 44, 30), fg=(214, 178, 110), emis=False, scale=1.0)
TK.sign(R, (27.0, JP.VA1, G + 5.0), '-v', 4.8, 1.6, ['COURTS TOWER', 'COURTROOMS  -  CLERK OF COURTS', 'JURY ASSEMBLY'], 'TC sign jc courts', bg=(30, 30, 34), fg=(232, 214, 170), scale=0.9)
TK.sign(R, (20.0, JP.VA0, G + 3.6), '+v', 3.6, 0.9, ['POLICE HEADQUARTERS'], 'TC sign jc police', bg=(30, 30, 34), fg=(232, 214, 170), scale=0.9)
TK.sign(R, (33.0, JP.VA0, G + 3.2), '+v', 5.0, 1.1, ['SECURITY SCREENING', 'ALL PERSONS AND BAGS ARE SUBJECT TO SEARCH'], 'TC sign jc screening', bg=(20, 34, 70), fg=(255, 255, 255), scale=0.85)
TK.sign(R, (p['u'][1], sum(p['v']) / 2, G + 0.75), '+u', 0.8, 0.5, ['EXIT ONLY'], 'TC sign jc exit only', bg=(150, 20, 20), fg=(255, 255, 255), scale=1.0)
# ---------------- lights (wall washers between the fins, two tiers) ----------------
for u, v, z, mount in JP.wall_lights():
    TK.lamp(R, u, v, z, energy=0.9, falloff=16.0, size=(0.9, 0.12) if mount[1] == 'v' else (0.12, 0.9), mount=mount)
TK.LCOL[R] = (1.0, 0.95, 0.86)
# ---------------- UVs at Rockstar's texel density for his textures ----------------
def uv_pass():
    for o in TK.PARTS[R]:
        me = o.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap 0')
        uv = me.uv_layers[0]; names = [m.name if m else '' for m in me.materials]
        for p_ in me.polygons:
            n = names[p_.material_index]
            if n == 'JC3 band':                                    # a strip: across its short side -> his strip rows, along it -> tiling
                cs = [o.matrix_world @ me.vertices[me.loops[li].vertex_index].co for li in p_.loop_indices]
                ax = max(range(3), key=lambda i: abs(p_.normal[i])); axes = [i for i in range(3) if i != ax]
                ext = [max(c[i] for c in cs) - min(c[i] for c in cs) for i in axes]; L_, S_ = (0, 1) if ext[0] >= ext[1] else (1, 0)
                lo_s = min(c[axes[S_]] for c in cs); w_ = max(ext[S_], 1e-3)
                for li, c in zip(p_.loop_indices, cs):
                    t = (c[axes[S_]] - lo_s) / w_; uv.data[li].uv = (c[axes[L_]] / (2.0 * w_ / (BAND_V[1] - BAND_V[0])), BAND_V[0] + t * (BAND_V[1] - BAND_V[0]))
                continue
            mpu = M_PER_UV.get(n[4:]) if n.startswith('JC3 ') else None
            if not mpu: continue
            ax = max(range(3), key=lambda i: abs(p_.normal[i])); axes = [i for i in range(3) if i != ax]
            for li in p_.loop_indices:
                co = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (co[axes[0]] / mpu, co[axes[1]] / mpu)
        for m in me.materials:
            if m and m.name.startswith('JC3 '): m['preserve_authored_uv'] = True
uv_pass()
# ---------------- export ----------------
DRAW2ROOM['jc_courts_galleria'] = R
pieces = len(TK.COLS)
info = TK.export_all({R: 'jc_courts_galleria'}, {}, JP.MLO, 'jc_courts_extcol')
assert VC_DONE.get('jc_courts_galleria'), 'vertex colours were not written'
ports = []
for a, b, kind, P in JP.portals():
    if P[0] == 'z': corners = TK.portal_z(P[1], P[2][0], P[2][1], P[3][0], P[3][1], P[4])
    else: axis, plane, a0, a1, z0, z1, into = P; corners = (TK.portal_u if axis == 'u' else TK.portal_v)(plane, a0, a1, z0, z1, into)
    ports.append({'from': a, 'to': b, 'kind': kind, 'corners': [[round(x, 4) for x in c] for c in corners]})
props = [dict(p_) for p_ in TK.PROPS]
door_ents = []
for name, model, u, v, z, h in JP.doors():
    props.append({'room': JP.ROOMS[R], 'model': model, 'pos': [u, v, z], 'heading': h, 'flags': TK.DOOR_FLAGS, 'portal': JP.DOOR_PORTAL})
    door_ents.append({'name': name, 'model': model, 'pos': [u, v, z], 'heading': h})
lay = {'mlo': JP.MLO, 'origin': [F.OX, F.OY, 0.0], 'heading': F.HDEG, 'drawables': info, 'bound': JP.MLO,
       'rooms': [{'key': k, 'name': JP.ROOM_NAME[k], 'id': i, 'drawable': 'jc_courts_' + k, 'timecycle': JP.TCYC[k]} for k, i in JP.ROOMS.items()],
       'portals': ports, 'props': props, 'placed': PLACED, 'doors': door_ents, 'seats': [[round(x, 3) for x in s] for s in SEATS],
       'lights': len(TK.LIGHTS[R]), 'vcol': {k: VCOL[DRAW2ROOM[k]] for k in VC_DONE},
       'mlo_box': [[JP.RA[0], JP.RA[2], G - JP.SLAB_T], [JP.RA[1], JP.RB[3], JP.ROOF]],
       'zones': {'galleria': [[JP.UA0, JP.UA1, JP.VA0, JP.VA1, G, JP.ROOF], [JP.UB0, JP.UB1, JP.VB0, JP.VB1, G, JP.ROOF]]},
       'collision': {'children': len(TK.COLS), 'pieces_merged': pieces}}
json.dump(lay, open(OUT / 'jc3_layout.json', 'w'), indent=1)
print('JC3_BUILD_PASS', json.dumps({'props': len(props), 'doors': len(door_ents), 'seats': len(SEATS), 'portals': len(ports), 'lights': lay['lights'],
      'col_children': len(TK.COLS), 'pieces': pieces, 'zfight': {k: len(v) for k, v in TK.ZF.items() if v}, 's': round(time.time() - t0)}), flush=True)
