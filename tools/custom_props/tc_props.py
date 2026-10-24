"""Tower City custom props (run in Blender + Sollumz): models the game has no good version of, exported as CW XML into work/props/
for props_meta.py (render-target patch, import, ytyp). Each model: front = -Y, back plane y = 0 (sits flush on a wall), z = 0 at its
bottom (the TV) or at the floor (the urinal), centred on x.
  tc_prop_tv      4.00 x 2.25 m screen (181 in), 10 mm bezel, 95 mm deep: piano-black bezel, brushed titanium edge band,
                  graphite back housing with vents, steel wall bracket, glass cover, standby LED, chin logo. The screen samples
                  script_rt_tc_tvscreen: RegisterNamedRendertarget('tc_tvscreen') + LinkNamedRendertarget(`tc_prop_tv`).
                  Placed at any scale (entity scaleXY/Z): 1.0 = 4 m, 1.3 = 5.2 m cinema wall, 0.6 = 2.4 m bedroom.
  tc_prop_urinal  wall-hung vitreous-china urinal (0.36 w, 0.34 d, 0.47-1.17 m): solid body, bowl carved by a boolean, chrome valve + trap.
  tc_prop_faucet  chrome gooseneck basin mixer (0.30 m column, 0.17 m reach) for the inset vanity basins."""
import bpy, bmesh, math, sys, json, numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).parent))
import tc_kit as TK
OUT = Path(__file__).parent / 'props'
TK.init(OUT, {})
from bl_ext.user_default.sollumz.sollumz_properties import SollumType
rng = np.random.default_rng(7)

def mesh_obj(name, verts, faces, mats, fmat, uvs=None):
    """verts [(x,y,z)], faces [(i..)], fmat [material index per face], uvs {face index: [(u,v) per corner]} (others: kit projection)."""
    me = bpy.data.meshes.new(name); me.from_pydata([Vector(v) for v in verts], [], faces)
    for m in mats: me.materials.append(m)
    for i, p in enumerate(me.polygons): p.material_index = fmat[i]
    if uvs:
        uv = me.uv_layers.new(name='UVMap 0'); li = 0
        for fi, p in enumerate(me.polygons):
            for k in range(p.loop_total):
                uv.data[p.loop_start + k].uv = uvs[fi][k] if fi in uvs else (0.0, 0.0)
    me.update(); o = bpy.data.objects.new(name, me); TK.coll().objects.link(o); return o

def keep(m): m['preserve_authored_uv'] = True; return m

def shader_mat(name, shader, px, params, emb_name=None):
    """a Sollumz material on `shader` with an embedded diffuse (px); emb_name renames the diffuse texture (render targets)."""
    m = TK.create_shader(shader); m.name = name; key = (emb_name or 'tc_' + name.lower().replace(' ', '_'))
    nd = m.node_tree.nodes['DiffuseSampler']; nd.image = TK.dds(key, px, OUT / 'tex', False, 'B8G8R8A8_UNORM'); nd.texture_properties.embedded = True
    if emb_name: nd.image.name = emb_name
    for s in ('BumpSampler', 'SpecSampler'):
        q = m.node_tree.nodes.get(s)
        if q:
            nn = np.ones((8, 8, 4), np.float32); nn[:, :, :2] = .5 if s == 'BumpSampler' else 1
            q.image = TK.dds(f'{key}_{s[:4].lower()}', nn, OUT / 'tex', True); q.texture_properties.embedded = True
    for p, v in params.items():
        q = m.node_tree.nodes.get(p)
        if q: q.set_float(v)
    return m

# ---------------- materials ----------------
def px_flat(rgb, k=32, grain=0.0):
    p = np.ones((k, k, 4), np.float32); p[:, :, :3] = np.clip(np.array(rgb)[None, None] * (1 + grain * rng.normal(0, 1, (k, k, 1))), 0, 1); return p
def px_brushed(rgb, k=256):
    p = np.ones((k, k, 4), np.float32); streak = rng.normal(0, 1, (k, 1)) * .06 + rng.normal(0, 1, (k, k)) * .015
    p[:, :, :3] = np.clip(np.array(rgb)[None, None] * (1 + streak[:, :, None] if streak.ndim == 2 else 1), 0, 1); return p
def px_vents(k=256):
    p = px_flat((.075, .076, .082), k, .03)
    for r0 in (40, 200):                                                           # two vent bands, slot rows
        for r in range(r0, r0 + 24, 6): p[r:r + 3, 24:k - 24, :3] *= .35
    return p
SCREEN = keep(shader_mat('TC tv screen', 'normal_spec_emissive.sps', np.zeros((512, 1024, 4), np.float32) + [.004, .004, .006, 1],
                         {'specularIntensityMult': .3, 'specularFalloffMult': 100.0, 'specularFresnel': .965, 'emissiveMultiplier': 1.1, 'bumpiness': .02},
                         emb_name='script_rt_tc_tvscreen'))
GLASS = keep(TK.clear_glass('TC tv glass', (.02, .02, .025), .05))
BEZEL = TK.tex_mat('TC tv bezel', px_flat((.012, .012, .014)), spec=.9)
BAND = TK.tex_mat('TC tv band', px_brushed((.30, .305, .32)), spec=.7)
BACK = TK.tex_mat('TC tv back', px_vents(), spec=.15)
STEEL = TK.tex_mat('TC tv bracket', px_brushed((.20, .20, .21), 64), spec=.4)
LED = keep(TK.tex_mat('TC tv led', px_flat((1.0, .08, .04)), emis=True, mult=3.0))
import subprocess
LOGO = keep(TK.tex_mat('TC tv logo', TK.sign_px(['TOWER  CITY'], 0.28, 0.014, (3, 3, 4), (150, 152, 158), 1.0), emis=True, mult=0.6))
CERAMIC = TK.tex_mat('TC urinal ceramic', px_flat((.93, .93, .91), 64, .01), spec=.85)
CHROME = TK.tex_mat('TC urinal chrome', px_brushed((.62, .63, .66), 64), spec=.95)

# ---------------- the TV ----------------
SW, SH, B, CHIN = 4.00, 2.25, 0.010, 0.022                     # screen w / h, bezel, bottom chin
YF, YB, YS = -0.095, -0.067, -0.0935                           # front face, panel back, recessed screen plane
X0, X1, Z0, Z1 = -SW / 2 - B, SW / 2 + B, 0.0, CHIN + SH + B    # panel outline
R, SEG = 0.008, 4                                                # outer corner radius
def outline():
    """rounded-rect outline in XZ, anticlockwise seen from the front (-y): returns points + per-corner arc index ranges."""
    pts = []; arcs = []
    for cx, cz, a0 in ((X1 - R, Z0 + R, -90), (X1 - R, Z1 - R, 0), (X0 + R, Z1 - R, 90), (X0 + R, Z0 + R, 180)):
        s = len(pts)
        for k in range(SEG + 1):
            a = math.radians(a0 + 90 * k / SEG); pts.append((cx + R * math.cos(a), cz + R * math.sin(a)))
        arcs.append((s, len(pts) - 1))
    return pts, arcs
def tv():
    V, F, FM, UV = [], [], [], {}
    def add(vs, f, m, uv=None):
        b = len(V); V.extend(vs); F.append(tuple(b + i for i in f)); FM.append(m)
        if uv: UV[len(F) - 1] = uv
    O, arcs = outline(); n = len(O)
    sx0, sx1, sz0, sz1 = -SW / 2, SW / 2, CHIN, CHIN + SH
    inner = [(sx1, sz0), (sx1, sz1), (sx0, sz1), (sx0, sz0)]      # inner corners matching the arcs' order (BR, TR, TL, BL)
    # front bezel: fans at the corners + strips between them
    for c, (s, e) in enumerate(arcs):
        ix, iz = inner[c]
        for k in range(s, e): add([(ix, YF, iz), (O[k + 1][0], YF, O[k + 1][1]), (O[k][0], YF, O[k][1])], (0, 1, 2), 1)
        ns, ne = arcs[(c + 1) % 4]; jx, jz = inner[(c + 1) % 4]
        add([(ix, YF, iz), (jx, YF, jz), (O[ns][0], YF, O[ns][1]), (O[e][0], YF, O[e][1])], (0, 3, 2, 1), 1)
    # recess lip (bezel inner edge down to the screen plane)
    for c in range(4):
        (ax, az), (bx, bz) = inner[c], inner[(c + 1) % 4]
        add([(ax, YF, az), (bx, YF, bz), (bx, YS, bz), (ax, YS, az)], (0, 1, 2, 3), 1)
    # screen (render target; Blender v up = the target's top - checked on the rig 2026-10-22) + the glass cover 1 mm in front of it
    add([(sx0, YS, sz0), (sx1, YS, sz0), (sx1, YS, sz1), (sx0, YS, sz1)], (0, 1, 2, 3), 0, [(0, 0), (1, 0), (1, 1), (0, 1)])
    add([(sx0, YS - .001, sz0), (sx1, YS - .001, sz0), (sx1, YS - .001, sz1), (sx0, YS - .001, sz1)], (0, 1, 2, 3), 7, [(0, 0), (1, 0), (1, 1), (0, 1)])
    # edge band (outline extruded front -> back) and the panel's back cap
    for k in range(n):
        a, b = O[k], O[(k + 1) % n]
        add([(a[0], YF, a[1]), (a[0], YB, a[1]), (b[0], YB, b[1]), (b[0], YF, b[1])], (0, 1, 2, 3), 2)
    add([(x, YB, z) for x, z in O], tuple(reversed(range(n))), 3)
    # logo on the chin, standby LED bottom right
    add([(-.14, YF - .0003, .004), (.14, YF - .0003, .004), (.14, YF - .0003, .018), (-.14, YF - .0003, .018)], (0, 1, 2, 3), 5, [(0, 0), (1, 0), (1, 1), (0, 1)])
    add([(1.93, YF - .0003, .009), (1.936, YF - .0003, .009), (1.936, YF - .0003, .015), (1.93, YF - .0003, .015)], (0, 1, 2, 3), 6, [(0, 0), (1, 0), (1, 1), (0, 1)])
    o = mesh_obj('tv_panel', V, F, [SCREEN, BEZEL, BAND, BACK, STEEL, LOGO, LED, GLASS], FM, UV)
    # back housing (chamfered) and the wall bracket
    hb = box_bevel('tv_housing', (-1.30, YB, 0.36), (1.30, -0.030, 1.86), 0.02, BACK)
    br = box_bevel('tv_bracket', (-0.60, -0.030, 0.80), (0.60, 0.0, 1.30), 0.004, STEEL)
    for x in (-0.45, 0.45): pass
    return [o, hb, br]
def box_bevel(name, lo, hi, bev, mat):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector([lo[i] + (v.co[i] + .5) * (hi[i] - lo[i]) for i in range(3)])
    if bev > 0: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=2, affect='EDGES', profile=0.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); TK.coll().objects.link(o); return o

# ---------------- the urinal ----------------
def urinal():
    """a solid vitreous-china body (rounded block: big radii on the front corners and the underside) with the bowl CARVED out of
    its front by a boolean ellipsoid, smooth-shaded; a chrome flush valve over it, a trap under it, a drain in the bowl."""
    W, D, ZB, ZT = 0.36, 0.34, 0.47, 1.17
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * W, -D / 2 + v.co.y * D, (ZB + ZT) / 2 + v.co.z * (ZT - ZB)))
    bm.edges.ensure_lookup_table()
    def edges(pred): return [e for e in bm.edges if pred(e.verts[0].co, e.verts[1].co)]
    front_vert = edges(lambda a, b: abs(a.y + D) < 1e-6 and abs(b.y + D) < 1e-6 and abs(a.x - b.x) < 1e-6)       # the two front corners
    bmesh.ops.bevel(bm, geom=front_vert, offset=0.13, segments=8, affect='EDGES', profile=0.5)
    bot_front = edges(lambda a, b: abs(a.z - ZB) < 1e-6 and abs(b.z - ZB) < 1e-6 and min(a.y, b.y) < -D + 0.14)
    bmesh.ops.bevel(bm, geom=bot_front, offset=0.10, segments=6, affect='EDGES', profile=0.5)
    top_front = edges(lambda a, b: abs(a.z - ZT) < 1e-6 and abs(b.z - ZT) < 1e-6 and min(a.y, b.y) < -D + 0.14)
    bmesh.ops.bevel(bm, geom=top_front, offset=0.025, segments=3, affect='EDGES', profile=0.5)
    me = bpy.data.meshes.new('urinal_body'); bm.to_mesh(me); bm.free(); me.materials.append(CERAMIC)
    body = bpy.data.objects.new('urinal_body', me); TK.coll().objects.link(body)
    cut = bpy.data.objects.new('urinal_cut', bpy.data.meshes.new('urinal_cut')); TK.coll().objects.link(cut)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * 0.135, -0.30 + v.co.y * 0.215, 0.90 + v.co.z * 0.30))
    bm.to_mesh(cut.data); bm.free()
    m = body.modifiers.new('bowl', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cut; m.solver = 'EXACT'
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier='bowl'); bpy.data.objects.remove(cut, do_unlink=True)
    for poly in body.data.polygons: poly.use_smooth = True
    for poly in body.data.polygons: poly.material_index = 0
    parts = [body, cyl('drain', (0, -0.17, 0.605), (0, -0.17, 0.61), 0.03, CHROME),
             cyl('flush_pipe', (0, -0.06, ZT), (0, -0.06, ZT + 0.32), 0.016, CHROME), cyl('flush_elbow', (0, -0.06, ZT + 0.32), (0, 0.0, ZT + 0.32), 0.016, CHROME),
             box_bevel('flush_valve', (-0.05, -0.115, ZT + 0.20), (0.05, -0.03, ZT + 0.30), 0.01, CHROME),
             cyl('flush_handle', (0.05, -0.08, ZT + 0.25), (0.13, -0.08, ZT + 0.25), 0.007, CHROME),
             cyl('trap_down', (0, -0.10, ZB + 0.01), (0, -0.10, ZB - 0.09), 0.022, CHROME), cyl('trap_wall', (0, -0.10, ZB - 0.09), (0, 0.0, ZB - 0.09), 0.022, CHROME),
             box_bevel('wall_plate', (-0.06, -0.006, ZB - 0.15), (0.06, 0.0, ZB - 0.03), 0.002, CHROME)]
    return parts
# ---------------- the faucet ----------------
def faucet():
    """a chrome gooseneck basin mixer: round base on the counter (z 0), a 0.30 m column, a smooth arc forward (-Y) ending in a
    down-pointing spout 0.17 m out, a side lever. Origin = the base centre on the counter top."""
    parts = [cyl('f_base', (0, 0, 0), (0, 0, 0.03), 0.028, CHROME, 24), cyl('f_col', (0, 0, 0.03), (0, 0, 0.30), 0.0135, CHROME, 20)]
    R, cz, n = 0.085, 0.30, 10                                                    # the arc: a half circle from the column top forward
    pts = [(0.0, -R + R * math.cos(math.pi * k / n), cz + R * math.sin(math.pi * k / n)) for k in range(n + 1)]
    for k in range(n): parts.append(cyl(f'f_arc{k}', pts[k], pts[k + 1], 0.0135, CHROME, 20))
    tip = pts[-1]; parts.append(cyl('f_spout', tip, (tip[0], tip[1], tip[2] - 0.035), 0.0145, CHROME, 20))
    parts += [cyl('f_lever_hub', (0.0135, 0, 0.16), (0.04, 0, 0.16), 0.012, CHROME, 16), cyl('f_lever', (0.04, 0, 0.16), (0.04, 0.06, 0.19), 0.006, CHROME, 12)]
    return parts
def cyl(name, p0, p1, r, mat, seg=16):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for v in bm.verts: v.co = q @ v.co + (p0 + p1) / 2
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); TK.coll().objects.link(o); return o

# ---------------- export ----------------
def export(name, parts):
    root, lo, hi = TK.K.new_drawable(name, parts, uv=0.5, keep_uv=TK.KEEP)
    assert 'FINISHED' in bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'CWXML'}, target_versions={'GEN8'}, limit_to_selected=True)
    return {'bb_lo': [round(v, 4) for v in lo], 'bb_hi': [round(v, 4) for v in hi]}
INFO = {'tc_prop_tv': export('tc_prop_tv', tv()), 'tc_prop_urinal': export('tc_prop_urinal', urinal()), 'tc_prop_faucet': export('tc_prop_faucet', faucet())}
json.dump(INFO, open(OUT / 'props.json', 'w'), indent=1)
print('TC_PROPS_PASS', json.dumps(INFO), flush=True)
