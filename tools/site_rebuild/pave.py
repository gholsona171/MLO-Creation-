"""The ground surface of the whole site (site_plan.PAVED), draped 3 cm over the paving height (pave_ground.pave_z) on the 2 m grid
site_col.py cuts the collision on, each grid cell clipped exactly to the site's outlines.
  * asphalt: brand-new blacktop (the client, Nov 23: "looks like it was just built ... no oil"): terrain_cb_w_4lyr_pxm_spm, the
    game's 4-layer ground shader, Rockstar's freshly laid road tarmac as the base with soft broad patches of two other fresh
    blacktops (vanilla_tex.LOT_LAYERS), which layer shows painted into vertex colour 2 (green picks pair 0/1 or 2/3, blue the
    layer within it) from smooth noise in world space so nothing repeats. Height maps flat: no relief, no cracks. No wear
    decals of any kind (no oil, stains, patches or sand);
  * parking paint (parking_plan.py: stalls, keep-clear hatching, arrows, the accessible symbol) in Rockstar's crisp car-park
    markings (vanilla_tex.PAINT), 1.5 cm over the blacktop;
  * lawn: the house lot north of site_plan.LAWN_Y bar the driveway and front path (site_plan.in_lawn), the game's own lawn
    texture (vanilla_tex.lawn), with a 15 cm concrete edging where lawn meets asphalt. (Its grass blades: lawn_grass.py.)
No collision of its own (the vanilla ground under it is graded by site_col.py). Drawables: one per 40 m tile (jy_pave_<i>_<j>).
Textures are NOT embedded: they go into one shared dictionary, jy_pave.ytd (ytd_build.ps1), that every tile names as its
textureDictionary (site_place.py). Rockstar's textures are copied byte for byte (their own compression) under our names.
Run: blender -b --python pave.py     Output ../site/pave/*.ydr + pave_info.json + tex/compressed/*.dds (for ytd_build.ps1)"""
import bpy, bmesh, sys, json, math, shutil, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, pave_ground as PG, proc_tex as PT, vanilla_tex as VT, parking_plan as PK
M_ = T.parent; OUT = M_ / 'site' / 'pave'
W = Path(r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work'); sys.path.insert(0, str(W))
bpy.ops.wm.read_homefile(use_empty=True)
coll = bpy.data.collections.new('Collection'); bpy.context.scene.collection.children.link(coll)
import v13_kit as K
from mlo_surface import dds
from bl_ext.user_default.sollumz.ydr.shader_materials import create_shader
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True); TEX = OUT / 'tex'; (TEX / 'compressed').mkdir(parents=True)
CELL, TILE, LIFT = 2.0, 40.0, 0.03
LOT_UV, LAWN_UV = 6.0, 4.0                                        # metres per texture repeat (shorter repeats read as a grid from the air)
PAINT_Z, PAINT_REP = .015, 4.0                                     # paint over the blacktop; its strip repeats every 4 m


def mat(name, stem, d, n=None, r=None, shader='normal_spec.sps', dfmt='BC3_UNORM', bump=1.0, spec_mult=.2, falloff=20):
    """a material on our own pixels, written as DDS (TEX/compressed) and referenced by name (not embedded: jy_pave.ytd)."""
    m = create_shader(shader); m.name = name; m['preserve_authored_uv'] = True
    flat_n = np.ones((8, 8, 4), np.float32); flat_n[..., :2] = .5
    spec = np.ones((8, 8, 4), np.float32) if r is None else np.concatenate([1 - r[..., :3] * .9, np.ones(r.shape[:2] + (1,))], -1).astype(np.float32)
    for sampler, suf, px, nc, fmt in (('DiffuseSampler', 'd', d, False, dfmt), ('BumpSampler', 'n', n if n is not None else flat_n, True, 'BC3_UNORM'),
                                      ('SpecSampler', 's', spec, True, 'BC3_UNORM')):
        nd = m.node_tree.nodes.get(sampler)
        if nd is None: continue
        nd.image = dds(f'{stem}_{suf}', px, TEX, nc, fmt); nd.texture_properties.embedded = False
    for p, v in (('bumpiness', bump), ('specularIntensityMult', spec_mult), ('specularFalloffMult', falloff)):
        q = m.node_tree.nodes.get(p)
        if q: q.set_float(v)
    return m


def native(name, shader, tex, params):
    """a material on Rockstar's own textures: {sampler: (name@dict spec, our texture name)}, each DDS copied unchanged."""
    m = create_shader(shader); m.name = name; m['preserve_authored_uv'] = True
    for sampler, (spec, stem) in tex.items():
        dst = TEX / 'compressed' / f'{stem}.dds'; shutil.copyfile(VT.path(spec), dst)
        im = bpy.data.images.load(str(dst), check_existing=False)
        im.colorspace_settings.name = 'sRGB' if sampler.startswith(('Texture', 'Diffuse')) else 'Non-Color'; im.pack()
        nd = m.node_tree.nodes[sampler]; nd.image = im; nd.texture_properties.embedded = False
    for p, v in params.items():
        q = m.node_tree.nodes.get(p); assert q, (name, p); q.set_float(v)
    return m


lot_tex = {}
for k, (dif, nrm) in enumerate(VT.LOT_LAYERS):
    lot_tex[f'TextureSampler_layer{k}'] = (dif, f'jy_lot_l{k}'); lot_tex[f'BumpSampler_layer{k}'] = (nrm, f'jy_lot_l{k}_n')
LOT = native('JY lot', 'terrain_cb_w_4lyr_pxm_spm.sps', lot_tex,
             {**{f'heightScale{k}': 0.0 for k in range(4)}, **{f'heightBias{k}': 0.0 for k in range(4)}, 'bumpiness': .7,
              'parallaxSelfShadowAmount': 0.0, 'bumpSelfShadowAmount': .2, 'specularIntensityMult': .02, 'specularFalloffMultSpecMap': 40})
flat_h = np.full((8, 8, 4), .5, np.float32); flat_h[..., 3] = 1
for k in range(4):                                                              # flat height maps: no parallax relief on new blacktop
    nd = LOT.node_tree.nodes[f'heightMapSamplerLayer{k}']; nd.image = dds('jy_lot_flat_h', flat_h, TEX, True, 'BC3_UNORM'); nd.texture_properties.embedded = False
d, n, r = VT.lawn(); LAWN = mat('JY lawn', 'jy_pave_lawn', d, n, r, bump=1.5, spec_mult=.08)
e = np.ones((64, 64, 4), np.float32); e[..., :3] = np.clip(.62 + PT.band(64, 1, 4, 3)[..., None] * .03, 0, 1)
EDGE = mat('JY lawn edging', 'jy_pave_edging', e, spec_mult=.1)
PAINT = {c: native(f'JY paint {c}', 'decal.sps', {'DiffuseSampler': (VT.PAINT[c], f'jy_paint_{c}')}, {'specularIntensityMult': .1}) for c in VT.PAINT}
MATS = [LOT, LAWN, EDGE, PAINT['white'], PAINT['yellow']]
MI = {m: i for i, m in enumerate(MATS)}


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman: the polygon clipped to the axis-aligned cell (convex clipper; any simple subject)."""
    def edge(pts, inside, cut):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a): out.append(cut(a, b))
                out.append(b)
            elif inside(a): out.append(cut(a, b))
        return out
    lerp_x = lambda xv: (lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0])))
    lerp_y = lambda yv: (lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv))
    pts = list(poly)
    for inside, cut in ((lambda p: p[0] >= x0, lerp_x(x0)), (lambda p: p[0] <= x1, lerp_x(x1)),
                        (lambda p: p[1] >= y0, lerp_y(y0)), (lambda p: p[1] <= y1, lerp_y(y1))):
        if not pts: break
        pts = edge(pts, inside, cut)
    return pts


def z_at(x, y, off=0.0): return PG.pave_z(x, y) + LIFT + off
def tkey(x, y): return (int(math.floor(x / TILE)), int(math.floor(y / TILE)))
tiles = {}
def bm_of(key):
    if key not in tiles:
        bm = bmesh.new(); tiles[key] = (bm, bm.loops.layers.uv.new('UVMap'))
    return tiles[key]
def face(key, pts, mi, uvs):
    bm, uvl = bm_of(key)
    try: f = bm.faces.new([bm.verts.new(Vector(p)) for p in pts])
    except ValueError: return
    f.material_index = mi; f.smooth = True
    for lp, uv in zip(f.loops, uvs): lp[uvl].uv = uv


# ---- the surface: every 2 m cell, clipped to each outline, asphalt or lawn by its centre ----
kind = {}                                                                       # (i, j) -> 'asph' | 'lawn' (cells with any surface)
for poly in SP.PAVED:
    px = [p[0] for p in poly]; py = [p[1] for p in poly]
    for i in range(int(math.floor(min(px) / CELL)), int(math.ceil(max(px) / CELL))):
        for j in range(int(math.floor(min(py) / CELL)), int(math.ceil(max(py) / CELL))):
            x0, y0 = i * CELL, j * CELL; cx, cy = x0 + CELL / 2, y0 + CELL / 2
            piece = clip(poly, x0, y0, x0 + CELL, y0 + CELL)
            vs = []
            for (x, y) in piece:
                if not vs or abs(vs[-1][0] - x) > 1e-5 or abs(vs[-1][1] - y) > 1e-5: vs.append((x, y))
            if len(vs) >= 3 and abs(vs[0][0] - vs[-1][0]) < 1e-5 and abs(vs[0][1] - vs[-1][1]) < 1e-5: vs.pop()
            if len(vs) < 3: continue
            area = 0.5 * sum(vs[k - 1][0] * vs[k][1] - vs[k][0] * vs[k - 1][1] for k in range(len(vs)))
            if abs(area) < 1e-4: continue
            if area < 0: vs = vs[::-1]
            lawn = SP.in_lawn(cx, cy); kind[(i, j)] = 'lawn' if lawn else 'asph'; s = LAWN_UV if lawn else LOT_UV
            face(tkey(x0, y0), [(x, y, z_at(x, y)) for x, y in vs], MI[LAWN] if lawn else MI[LOT], [(x / s, y / s) for x, y in vs])

# ---- concrete edging where a lawn cell meets an asphalt cell (15 cm wide, 5 cm proud) ----
EW, EH = 0.075, 0.05
nedge = 0
for (i, j), k in kind.items():
    if k != 'lawn': continue
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if kind.get((i + di, j + dj)) != 'asph': continue
        x0, y0 = i * CELL, j * CELL
        if di: xs = x0 + (CELL if di > 0 else 0); a, b = (xs - EW, y0), (xs + EW, y0 + CELL); top = [(a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1])]
        else: ys = y0 + (CELL if dj > 0 else 0); a, b = (x0, ys - EW), (x0 + CELL, ys + EW); top = [(a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1])]
        key = tkey(x0, y0)
        face(key, [(x, y, z_at(x, y, EH)) for x, y in top], MI[EDGE], [(x, y) for x, y in top])
        for (p, q) in zip(top, top[1:] + top[:1]):                                   # its four sides, down into the surface
            face(key, [(p[0], p[1], z_at(*p, -.02)), (q[0], q[1], z_at(*q, -.02)), (q[0], q[1], z_at(*q, EH)), (p[0], p[1], z_at(*p, EH))], MI[EDGE],
                 [(0, 0), (1, 0), (1, .1), (0, .1)])
        nedge += 1


# ---- the layer blend (vertex colour 2), from smooth value noise in world space: broad, low-contrast batches of fresh blacktop
def vnoise(x, y, s, seed):
    gx, gy = x / s, y / s; i, j = math.floor(gx), math.floor(gy); u, v = gx - i, gy - j
    h = lambda a, b: ((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) % 1000003 / 1000003
    u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
    return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v
def fbm(x, y, s, seed): return .62 * vnoise(x, y, s, seed) + .38 * vnoise(x, y, s / 2.3, seed + 7)
def ss(a, b, t): t = min(1.0, max(0.0, (t - a) / (b - a))); return t * t * (3 - 2 * t)
def blend(x, y):
    """(green, blue) of vertex colour 2: layer 0 = (0, 0), 1 = (0, 1), 2 = (1, 0), 3 = (1, 1). Mostly layer 0, soft patches of
    layers 1 and 2 at most half strength (layer 3 never)."""
    w1 = .5 * ss(.50, .78, fbm(x, y, 29, 1)); w2 = .45 * ss(.52, .80, fbm(x, y, 41, 2))
    return w2, (1 - w2) * w1


# ---- parking paint (parking_plan.py), on any asphalt cell (the buildings' planning rects do not apply)
placed = {}
def paved(x, y): return kind.get((int(math.floor(x / CELL)), int(math.floor(y / CELL)))) == 'asph'
def paint_quad(m, cx, cy, L, Wd, ang, uv_of, seg=1.0):
    """a painted quad L long (along ang) and Wd wide, cut into seg pieces so it follows the ground; uv_of(s, t) -> (u, v)
    for s along the length (0..1, tail to tip) and t across (0..1)."""
    ca, sa = math.cos(ang), math.sin(ang)
    def P(s, t): return (cx + ca * (s - .5) * L - sa * (t - .5) * Wd, cy + sa * (s - .5) * L + ca * (t - .5) * Wd)
    if not all(paved(*P(s, t)) for s in (0, .5, 1) for t in (0, 1)): return 0
    nu = max(1, int(math.ceil(L / seg)))
    for a in range(nu):
        q = [(a / nu, 0), ((a + 1) / nu, 0), ((a + 1) / nu, 1), (a / nu, 1)]
        face(tkey(cx, cy), [(x, y, z_at(x, y, PAINT_Z)) for x, y in (P(s, t) for s, t in q)], MI[m], [uv_of(s, t) for s, t in q])
    return 1
LU0, LU1 = VT.PAINT_UV['line']; AU0, AU1, AV_TAIL, AV_TIP = VT.PAINT_UV['arrow']; SU0, SV0, SU1, SV1 = VT.PAINT_UV['sign']
for it in PK.paint():
    if it[0] == 'line':
        _, x0, y0, x1, y1, colour, w = it; L = math.hypot(x1 - x0, y1 - y0)
        ok = paint_quad(PAINT[colour], (x0 + x1) / 2, (y0 + y1) / 2, L, w, math.atan2(y1 - y0, x1 - x0),
                        lambda s, t, L=L: (LU0 + t * (LU1 - LU0), s * L / PAINT_REP))
    elif it[0] == 'arrow':
        _, x, y, h, L = it
        ok = paint_quad(PAINT['white'], x, y, L, L * .34, math.radians(h), lambda s, t: (AU0 + t * (AU1 - AU0), AV_TAIL + s * (AV_TIP - AV_TAIL)))
    else:                                                                       # the wheelchair: upright (+v) along the heading
        _, x, y, h, sz = it
        ok = paint_quad(PAINT['white'], x, y, sz, sz * .9, math.radians(h) + math.pi / 2, lambda s, t: (SU0 + (1 - t) * (SU1 - SU0), SV0 + s * (SV1 - SV0)))
    placed[it[0]] = placed.get(it[0], 0) + ok
want = {k: sum(1 for it in PK.paint() if it[0] == k) for k in ('line', 'arrow', 'sign')}
assert placed.get('line', 0) >= want['line'] - 1 and placed.get('arrow', 0) == want['arrow'] and placed.get('sign', 0) == want['sign'], (placed, want)

# ---- one drawable per tile ----
info = {}; share = np.zeros(4)
for (ti, tj), (bm, uvl) in sorted(tiles.items()):
    name = f'jy_pave_{ti - 58}_{tj - 75}'                                     # (x 2320 = tile 58, y 3000 = tile 75)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    me = bpy.data.meshes.new(name + '_mesh'); bm.to_mesh(me); bm.free()
    for m in MATS: me.materials.append(m)
    used = sorted({p.material_index for p in me.polygons})
    o = bpy.data.objects.new(name + '_mesh', me); bpy.context.scene.collection.objects.link(o)
    vs = [v.co for v in me.vertices]
    origin = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, 47.0))
    me.transform(Matrix.Translation(-origin))
    root, lo, hi = K.new_drawable(name, [o], cols=[], uv=1.0, keep_uv={m.name for m in MATS})
    for ob in root.children_recursive:
        if ob.type != 'MESH' or ob.sollum_type != 'sollumz_drawable_model': continue
        md = ob.data
        for nm in ('Color 1', 'Color 2'):
            if nm not in md.color_attributes: md.color_attributes.new(nm, 'BYTE_COLOR', 'CORNER')
        world = [ob.matrix_world @ v.co + origin for v in md.vertices]
        c1 = np.ones((len(md.vertices), 4), np.float32); c2 = np.zeros((len(md.vertices), 4), np.float32); c2[:, 3] = 1
        for k, w in enumerate(world):
            g, b = blend(w.x, w.y); c2[k, 1], c2[k, 2] = g, b
        lot_v = {md.loops[li].vertex_index for p in md.polygons if p.material_index == MI[LOT] for li in p.loop_indices}
        for k in lot_v:
            g, b = c2[k, 1] > .5, c2[k, 2] > .5; share[int(g) * 2 + int(b)] += 1
        for nm, c in (('Color 1', c1), ('Color 2', c2)):
            at = md.color_attributes[nm]
            vals = c if at.domain == 'POINT' else c[[lp.vertex_index for lp in md.loops]]
            at.data.foreach_set('color', np.ascontiguousarray(vals, np.float32).ravel())
        for p in md.polygons: p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
    info[name] = {'origin': list(origin), 'bb_lo': list(lo), 'bb_hi': list(hi), 'faces': len(me.polygons), 'materials': used}
json.dump(info, open(OUT / 'pave_info.json', 'w'), indent=1)
print('PAVE_PASS', len(info), 'tiles', sum(v['faces'] for v in info.values()), 'faces;', sum(1 for k in kind.values() if k == 'lawn'), 'lawn cells;',
      nedge, 'edging runs; lot layers 0..3 share', [round(float(s), 2) for s in share / max(1, share.sum())], '; paint', placed, 'of', want, flush=True)
