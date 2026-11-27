"""The lot's drawn ground: the whole site (site_plan.SITE) draped LIFT m over the new grade (grade.grade_z) on a 1 m world grid (every
line of site_col.py's 2 m collision grid is one of its lines), each grid cell clipped exactly to the site's outline. Rockstar's own ground under it is lowered
out of sight by terrain.py.
Surface (not decided yet; a plain compacted dirt / gravel lot for now): the game's 4-layer ground shader
(terrain_cb_w_4lyr_pxm_spm, as Rockstar's ground) on Rockstar's own Sandy Shores ground textures (LAYERS: the desert gravel-stones-dirt
of this strip's land model as the base, soft patches of packed dirt and desert sand), which layer shows painted into vertex colour 2
from smooth noise in world space so nothing repeats. Height maps flat (no parallax). Vertex colour 1 = Rockstar's ground values
(R 1, G 0, B 1: G is the artificial night ambient, 0 on all his land: a 1 there glows at night). To change the surface later, change
LAYERS (and site_plan.LOT_MATERIAL for the collision) and rebuild.
No collision of its own (the vanilla ground under it is graded by site_col.py). Nothing is drawn under the club's walls (its floor
covers that). Drawables: one per 40 m tile (bb_ground_<i>_<j>); their textures in one dictionary, bb_ground.ytd (ytd_build.ps1),
named by every tile as its textureDictionary (site_meta.py). Rockstar's DDS files are copied byte for byte under our names.
Run: blender -b --python ground.py     Output ../site/ground/*.ydr + ground_info.json + tex/compressed/*.dds (for ytd_build.ps1)"""
import bpy, bmesh, sys, json, math, shutil, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP, grade as GR, concept_v3 as C
M_ = T.parent; OUT = M_ / 'site' / 'ground'; VTEX = M_ / 'tex' / 'vanilla'
W = Path(r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work'); sys.path.insert(0, str(W))
bpy.ops.wm.read_homefile(use_empty=True)
coll = bpy.data.collections.new('Collection'); bpy.context.scene.collection.children.link(coll)
import v13_kit as K
from mlo_surface import dds
from bl_ext.user_default.sollumz.ydr.shader_materials import create_shader
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True); TEX = OUT / 'tex'; (TEX / 'compressed').mkdir(parents=True)
CELL, TILE, LIFT, UVS = 1.0, 40.0, 0.02, 5.0       # (1 m cells: inside each 2 m collision cell, so the drawn ground follows it)
LAYERS = [('cs_rsn_sl_desgravelstonesdirt_01', 'cs_rsn_sl_desgravelstonesdirt_01_n'),     # 0 base: compacted gravel-dirt
          ('im_ground_dirt001', 'im_ground_dirt001_n'),                                     # 1 soft patches: packed dirt
          ('cs_rsn_sl_dessand_01', 'cs_rsn_sl_dessand_01_n'),                               # 2 soft patches: desert sand
          ('cs_rsn_sl_desgravelstonesdirt_01', 'cs_rsn_sl_desgravelstonesdirt_01_n')]     # 3 (unused corner)
TILE0 = (25, 88)                                                                           # (x 1000 = tile 25, y 3520 = tile 88)


def lot_material():
    m = create_shader('terrain_cb_w_4lyr_pxm_spm.sps'); m.name = 'BB lot'; m['preserve_authored_uv'] = True
    for k, (dif, nrm) in enumerate(LAYERS):
        for sampler, src, stem in ((f'TextureSampler_layer{k}', dif, f'bb_gnd_l{k}'), (f'BumpSampler_layer{k}', nrm, f'bb_gnd_l{k}_n')):
            dst = TEX / 'compressed' / f'{stem}.dds'; shutil.copyfile(VTEX / f'{src}.dds', dst)
            im = bpy.data.images.load(str(dst), check_existing=False)
            im.colorspace_settings.name = 'sRGB' if sampler.startswith('Texture') else 'Non-Color'; im.pack()
            nd = m.node_tree.nodes[sampler]; nd.image = im; nd.texture_properties.embedded = False
    flat_h = np.full((8, 8, 4), .5, np.float32); flat_h[..., 3] = 1
    for k in range(4):
        nd = m.node_tree.nodes[f'heightMapSamplerLayer{k}']; nd.image = dds('bb_gnd_flat_h', flat_h, TEX, True, 'BC3_UNORM'); nd.texture_properties.embedded = False
    for p, v in {**{f'heightScale{k}': 0.0 for k in range(4)}, **{f'heightBias{k}': 0.0 for k in range(4)}, 'bumpiness': 1.0,
                 'parallaxSelfShadowAmount': 0.0, 'bumpSelfShadowAmount': .3, 'specularIntensityMult': .02, 'specularFalloffMultSpecMap': 30}.items():
        q = m.node_tree.nodes.get(p); assert q, p; q.set_float(v)
    return m


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman: the polygon clipped to the axis-aligned cell."""
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


def vnoise(x, y, s, seed):
    gx, gy = x / s, y / s; i, j = math.floor(gx), math.floor(gy); u, v = gx - i, gy - j
    h = lambda a, b: ((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) % 1000003 / 1000003
    u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
    return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v
def fbm(x, y, s, seed): return .62 * vnoise(x, y, s, seed) + .38 * vnoise(x, y, s / 2.3, seed + 7)
def ss(a, b, t): t = min(1.0, max(0.0, (t - a) / (b - a))); return t * t * (3 - 2 * t)
def blend(x, y):
    """(green, blue) of vertex colour 2: layer 0 = (0, 0), 1 = (0, 1), 2 = (1, 0). Mostly the gravel-dirt, soft broad patches of
    packed dirt and sand at most 60 % strength."""
    w1 = .6 * ss(.48, .78, fbm(x, y, 23, 1)); w2 = .5 * ss(.52, .80, fbm(x, y, 37, 2))
    return w2, (1 - w2) * w1


LOT = lot_material()
WALL = [SP.W(p)[:2] for p in C.outline(192)]                       # the club's outer wall line (its floor covers what is inside)
def under_walls(pts): return all(SP.inpoly(x, y, WALL) and SP.seg_dist(x, y, WALL) > 0.6 for x, y in pts)
tiles = {}
def bm_of(key):
    if key not in tiles:
        bm = bmesh.new(); tiles[key] = (bm, bm.loops.layers.uv.new('UVMap'))
    return tiles[key]


S = SP.SITE; xs = [p[0] for p in S]; ys = [p[1] for p in S]; cells = skipped = 0
for i in range(int(math.floor(min(xs) / CELL)), int(math.ceil(max(xs) / CELL))):
    for j in range(int(math.floor(min(ys) / CELL)), int(math.ceil(max(ys) / CELL))):
        x0, y0 = i * CELL, j * CELL
        vs = []
        for (x, y) in clip(S, x0, y0, x0 + CELL, y0 + CELL):
            if not vs or abs(vs[-1][0] - x) > 1e-5 or abs(vs[-1][1] - y) > 1e-5: vs.append((x, y))
        if len(vs) >= 3 and abs(vs[0][0] - vs[-1][0]) < 1e-5 and abs(vs[0][1] - vs[-1][1]) < 1e-5: vs.pop()
        if len(vs) < 3: continue
        area = 0.5 * sum(vs[k - 1][0] * vs[k][1] - vs[k][0] * vs[k - 1][1] for k in range(len(vs)))
        if abs(area) < 1e-4: continue
        if area < 0: vs = vs[::-1]
        if under_walls(vs): skipped += 1; continue
        key = (int(math.floor(x0 / TILE)), int(math.floor(y0 / TILE)))
        bm, uvl = bm_of(key)
        f = bm.faces.new([bm.verts.new(Vector((x, y, GR.grade_z(x, y) + LIFT))) for x, y in vs])
        f.smooth = True
        for lp, (x, y) in zip(f.loops, vs): lp[uvl].uv = (x / UVS, y / UVS)
        cells += 1

info = {}
for (ti, tj), (bm, uvl) in sorted(tiles.items()):
    name = f'bb_ground_{ti - TILE0[0]}_{tj - TILE0[1]}'
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name + '_mesh'); bm.to_mesh(me); bm.free(); me.materials.append(LOT)
    o = bpy.data.objects.new(name + '_mesh', me); coll.objects.link(o)
    vs = [v.co for v in me.vertices]
    origin = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, 33.0))
    me.transform(Matrix.Translation(-origin))
    root, lo, hi = K.new_drawable(name, [o], cols=[], uv=1.0, keep_uv={LOT.name})
    for ob in root.children_recursive:
        if ob.type != 'MESH' or ob.sollum_type != 'sollumz_drawable_model': continue
        md = ob.data
        for nm in ('Color 1', 'Color 2'):
            if nm not in md.color_attributes: md.color_attributes.new(nm, 'BYTE_COLOR', 'CORNER')
        world = [ob.matrix_world @ v.co + origin for v in md.vertices]
        c1 = np.tile(np.array([1.0, 0.0, 1.0, 1.0], np.float32), (len(md.vertices), 1))
        c2 = np.zeros((len(md.vertices), 4), np.float32); c2[:, 3] = 1
        for k, w in enumerate(world):
            g, b = blend(w.x, w.y); c2[k, 1], c2[k, 2] = g, b
        for nm, c in (('Color 1', c1), ('Color 2', c2)):
            at = md.color_attributes[nm]
            vals = c if at.domain == 'POINT' else c[[lp.vertex_index for lp in md.loops]]
            at.data.foreach_set('color', np.ascontiguousarray(vals, np.float32).ravel())
        for p in md.polygons: p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
    assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
    info[name] = {'origin': list(origin), 'bb_lo': list(lo), 'bb_hi': list(hi), 'faces': len(me.polygons)}
json.dump(info, open(OUT / 'ground_info.json', 'w'), indent=1)
print('GROUND_PASS', len(info), 'tiles', cells, 'cells', skipped, 'cells under the club left out', sum(v['faces'] for v in info.values()), 'triangles', flush=True)
