"""The ground surface of the whole site (site_plan.PAVED), draped 3 cm over the paving height (pave_ground.pave_z) on the 2 m grid
site_col.py cuts the collision on, each grid cell clipped exactly to the site's outlines.
The lot is laid the way Rockstar lays the Harmony used-car lot (cs6_03_usedlotmc + its decal mesh _d001; vanilla_tex.LOT_*),
Antonio 2026-11-23: one flat blacktop with drawn-on cracks "doesn't look realistic":
  * asphalt: terrain_cb_w_4lyr_pxm_spm, the game's 4-layer ground shader with parallax height maps, Harmony's four textures and
    parameters: worn dark tarmac (layer 0, most of the lot), alligator-cracked tarmac and older grey cracked road (layers 1, 2,
    soft patches), gravel and dirt (layer 3, along the site's open rim; a rare patch inside - more read as a dirt yard). Which layer shows is vertex colour 2
    (green picks pair 0/1 or 2/3, blue the layer within it), painted from smooth noise in world space so nothing repeats;
  * decals over it, Harmony's own, faded at their rims by vertex colour 1 alpha the way Rockstar fades them: busted patched
    tarmac, sand drifts along the open edges, oil splats (more where vehicles stand: the shop's bays, the house garage), brown
    ground stains. Never under the buildings (site_plan.NO_DECALS), never off the asphalt;
  * lawn: the house lot north of site_plan.LAWN_Y bar the driveway and front path (site_plan.in_lawn), the game's own lawn
    texture (vanilla_tex.lawn), with a 15 cm concrete edging where lawn meets asphalt. (Its grass blades: lawn_grass.py.)
No collision of its own (the vanilla ground under it is graded by site_col.py). Drawables: one per 40 m tile (jy_pave_<i>_<j>).
Textures are NOT embedded: they go into one shared dictionary, jy_pave.ytd (ytd_build.ps1), that every tile names as its
textureDictionary (site_place.py). Rockstar's textures are copied byte for byte (their own compression) under our names.
Run: blender -b --python pave.py     Output ../site/pave/*.ydr + pave_info.json + tex/compressed/*.dds (for ytd_build.ps1)"""
import bpy, bmesh, sys, json, math, shutil, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, kdtree
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, pave_ground as PG, proc_tex as PT, vanilla_tex as VT
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
LOT_UV, LAWN_UV = 5.5, 4.0                                        # metres per texture repeat (Harmony's ~3.1 m read as a grid from the air)
rng = np.random.default_rng(20261123)


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
for k, (dif, nrm, hgt) in enumerate(VT.LOT_LAYERS):
    lot_tex[f'TextureSampler_layer{k}'] = (dif, f'jy_lot_l{k}'); lot_tex[f'BumpSampler_layer{k}'] = (nrm, f'jy_lot_l{k}_n')
    lot_tex[f'heightMapSamplerLayer{k}'] = (hgt, f'jy_lot_l{k}_h')
LOT = native('JY lot', 'terrain_cb_w_4lyr_pxm_spm.sps', lot_tex,                  # Harmony's parameters
             {**{f'heightScale{k}': .03 for k in range(4)}, **{f'heightBias{k}': .015 for k in range(4)}, 'bumpiness': 1.1,
              'parallaxSelfShadowAmount': .95, 'bumpSelfShadowAmount': .3, 'specularIntensityMult': .01, 'specularFalloffMultSpecMap': 48})
d, n, r = VT.lawn(); LAWN = mat('JY lawn', 'jy_pave_lawn', d, n, r, bump=1.5, spec_mult=.08)
e = np.ones((64, 64, 4), np.float32); e[..., :3] = np.clip(.62 + PT.band(64, 1, 4, 3)[..., None] * .03, 0, 1)
EDGE = mat('JY lawn edging', 'jy_pave_edging', e, spec_mult=.1)
DC = VT.LOT_DECALS
BUSTED = native('JY lot busted', 'normal_spec_decal.sps', {'DiffuseSampler': (DC['busted'][0], 'jy_lot_busted'),
                'BumpSampler': (DC['busted'][1], 'jy_lot_busted_n'), 'SpecSampler': (DC['busted'][0], 'jy_lot_busted')},
                {'bumpiness': 1.2, 'specularIntensityMult': .15})
DRIFT = native('JY lot drift', 'normal_decal.sps', {'DiffuseSampler': (DC['drift'][0], 'jy_lot_drift'),
               'BumpSampler': (DC['drift'][1], 'jy_lot_drift_n')}, {'bumpiness': 1.0, 'specularIntensityMult': .01})
SPLATS = native('JY lot splats', 'decal.sps', {'DiffuseSampler': (DC['splats'][0], 'jy_lot_splats')}, {'specularIntensityMult': .05})
STAIN = native('JY lot stain', 'decal.sps', {'DiffuseSampler': (DC['stain'][0], 'jy_lot_stain')}, {'specularIntensityMult': .05})
MATS = [LOT, LAWN, EDGE, BUSTED, DRIFT, SPLATS, STAIN]
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


# ---- the layer blend (vertex colour 2), from smooth value noise in world space ----
def vnoise(x, y, s, seed):
    gx, gy = x / s, y / s; i, j = math.floor(gx), math.floor(gy); u, v = gx - i, gy - j
    h = lambda a, b: ((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) % 1000003 / 1000003
    u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
    return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v
def fbm(x, y, s, seed): return .62 * vnoise(x, y, s, seed) + .38 * vnoise(x, y, s / 2.3, seed + 7)
def ss(a, b, t): t = min(1.0, max(0.0, (t - a) / (b - a))); return t * t * (3 - 2 * t)
def open_edge(x, y):
    """1 at the lot's outer rim (a cell with no surface next to it), .5 one cell further in, else 0."""
    i, j = int(math.floor(x / CELL)), int(math.floor(y / CELL))
    for r, w in ((1, 1.0), (2, .5)):
        if any((i + a, j + b) not in kind for a in range(-r, r + 1) for b in range(-r, r + 1)): return w
    return 0.0
def blend(x, y):
    """(green, blue) of vertex colour 2: layer 0 = (0, 0), 1 = (0, 1), 2 = (1, 0), 3 = (1, 1), blended in between."""
    w1 = ss(.54, .70, fbm(x, y, 17, 1))                                          # alligator-cracked tarmac
    w2 = ss(.56, .72, fbm(x, y, 23, 2))                                          # old grey cracked road
    w3 = max(ss(.72, .82, fbm(x, y, 8, 3)) * .6, open_edge(x, y) * (.35 + .65 * vnoise(x, y, 3, 4)))   # gravel + dirt: the open rim, rare inside
    g = min(1.0, w2 + w3); b = (1 - g) * w1 + g * (w3 / (w2 + w3 + 1e-6))
    return g, b


# ---- decals over the asphalt (Harmony's own) ----
def asphalt_at(x, y):
    k = kind.get((int(math.floor(x / CELL)), int(math.floor(y / CELL))))
    return k == 'asph' and SP.on_site(x, y) and not any(a - .5 <= x <= b + .5 and c - .5 <= y <= d_ + .5 for a, b, c, d_ in SP.NO_DECALS)
XS = [p[0] for poly in SP.PAVED for p in poly]; YS = [p[1] for poly in SP.PAVED for p in poly]
BOX = (min(XS), max(XS), min(YS), max(YS))
OIL_SPOTS = [((2404.0, 2430.0), (3053.0, 3062.0)), ((2336.0, 2344.0), (3120.0, 3127.5))]   # in front of the shop's bays, the house garage
ALPHA = []                                                                      # (world x, y, z, alpha) of every faded decal vertex
def off_of(layer): return .012 + .003 * layer


def patch(m, cx, cy, R, uvs, layer, rough=.45):
    """a soft blob of decal: 1 m cells around (cx, cy) inside a noisy rim of radius R, UVs = world / uvs metres, vertex alpha
    1 inside falling to 0 at the rim; only cells whose corners are all on the asphalt."""
    seed = int(rng.integers(1, 10 ** 6)); ox, oy = rng.uniform(0, 1, 2)
    def a_at(x, y):
        r = math.hypot(x - cx, y - cy) / R * (1 + rough * (vnoise(x, y, max(1.0, R * .5), seed) - .5) * 2)
        return ss(0.0, 1.0, (1 - r) / .45)
    n = 0
    for i in range(int(-R) - 1, int(R) + 1):
        for j in range(int(-R) - 1, int(R) + 1):
            q = [(cx + ox + i + a, cy + oy + j + b) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
            al = [a_at(x, y) for x, y in q]
            if max(al) <= 0 or not all(asphalt_at(x, y) for x, y in q): continue
            pts = [(x, y, z_at(x, y, off_of(layer))) for x, y in q]
            face(tkey(*q[0]), pts, MI[m], [(x / uvs, y / uvs) for x, y in q]); n += 1
            ALPHA.extend((x, y, z, a) for (x, y, z), a in zip(pts, al))
    return n > 0


SPLAT_UV = {'smear': (0, 0, .5, 1), 'splat': (.5, .5, 1, 1), 'patch': (.5, 0, 1, .5)}   # the splats atlas: Blender UV (v up)
def sprite(m, uv, cx, cy, L, Wd, ang, layer, seg=1.0):
    """one textured quad (its own alpha does the shape), cut into seg-sized pieces so it follows the ground."""
    u0, v0, u1, v1 = uv; ca, sa = math.cos(ang), math.sin(ang)
    corners = [(cx + ca * sx * L / 2 - sa * sy * Wd / 2, cy + sa * sx * L / 2 + ca * sy * Wd / 2) for sx in (-1, 1) for sy in (-1, 1)]
    if not all(asphalt_at(x, y) for x, y in corners + [(cx, cy)]): return False
    nu, nv = max(1, int(math.ceil(L / seg))), max(1, int(math.ceil(Wd / seg)))
    def P(s, t): return (cx + ca * (s - .5) * L - sa * (t - .5) * Wd, cy + sa * (s - .5) * L + ca * (t - .5) * Wd)
    for a in range(nu):
        for b in range(nv):
            q = [(a / nu, b / nv), ((a + 1) / nu, b / nv), ((a + 1) / nu, (b + 1) / nv), (a / nu, (b + 1) / nv)]
            pts = [P(s, t) for s, t in q]
            face(tkey(cx, cy), [(x, y, z_at(x, y, off_of(layer))) for x, y in pts], MI[m], [(u0 + s * (u1 - u0), v0 + t * (v1 - v0)) for s, t in q])
    return True


def spot(oil_bias):
    if oil_bias and rng.random() < .5:
        (xa, xb), (ya, yb) = OIL_SPOTS[rng.integers(len(OIL_SPOTS))]; return rng.uniform(xa, xb), rng.uniform(ya, yb)
    return rng.uniform(BOX[0], BOX[1]), rng.uniform(BOX[2], BOX[3])


placed = {}
def scatter(label, count, make):
    ok = tries = 0
    while ok < count and tries < count * 80:
        tries += 1; ok += bool(make())
    placed[label] = ok


def drift():                                                                    # centred on the open rim
    x, y = spot(False)
    return open_edge(x, y) >= 1 and patch(DRIFT, x, y, rng.uniform(2.5, 4.5), 4.0, 1)
scatter('busted', 18, lambda: patch(BUSTED, *spot(False), rng.uniform(2, 4.5), 2.5, 0))
scatter('drift', 10, drift)
scatter('stain', 14, lambda: (lambda L: sprite(STAIN, (0, 0, 1, 1), *spot(False), L, L * rng.uniform(.8, 1), rng.uniform(0, math.pi), 2))(rng.uniform(2.5, 5)))
scatter('oil', 60, lambda: (lambda L: sprite(SPLATS, SPLAT_UV['splat'], *spot(True), L, L * rng.uniform(.8, 1), rng.uniform(0, math.pi), 3))(rng.uniform(1, 2.2)))
scatter('smear', 16, lambda: sprite(SPLATS, SPLAT_UV['smear'], *spot(True), rng.uniform(1.4, 2), rng.uniform(2.8, 4), rng.uniform(0, math.pi), 3))
scatter('sealed', 14, lambda: (lambda L: sprite(SPLATS, SPLAT_UV['patch'], *spot(False), L, L * rng.uniform(.7, 1), rng.uniform(0, math.pi), 3))(rng.uniform(1.5, 2.5)))
kd = kdtree.KDTree(len(ALPHA))
for k, (x, y, z, a) in enumerate(ALPHA): kd.insert((x, y, z), k)
kd.balance()

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
            hit = kd.find(w) if len(ALPHA) else None
            if hit and hit[2] < 2e-3: c1[k, 3] = ALPHA[hit[1]][3]
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
assert placed['busted'] and placed['drift'] and placed['oil'], placed
print('PAVE_PASS', len(info), 'tiles', sum(v['faces'] for v in info.values()), 'faces;', sum(1 for k in kind.values() if k == 'lawn'), 'lawn cells;',
      nedge, 'edging runs; lot layers 0..3 share', [round(float(s), 2) for s in share / max(1, share.sum())], '; decals', placed,
      len(ALPHA), 'faded verts', flush=True)
