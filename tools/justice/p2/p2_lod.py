"""Justice Center phase 2: the LOD chain's own models (run in Blender after p2_build.py), all from p2_plan (the same openings, the
same lit bays as the HD models, so nothing changes between levels but the detail):
  jc_<b>_lod   one per building (Jail II carries the skybridges): the massing boxes with a BAKED facade - every opening of the HD
               facade rasterised into one atlas per building (stone = the mean of Rockstar's own stone texture, dark glass, louvres...)
  jc_slod1     the whole complex in one model (the same boxes, the atlases at half size)
  jc_emi_lod   the lit bays as quads 0.15 m in front of the massing (emissivenight), jc_emi_slod the same 0.4 m out (the night SLOD)
  slod_add.npz the massing + the cleared lot's ground plates (lot / podium / lawn / walk) as world triangles with UVs into one
               combined atlas (slod_atlas.png): p1_cut_lod.py --add puts them into Rockstar's SLOD2 sc1_lod_19 and SLOD3 sc1_lod_slod4
Every model is centred on its own bounds (the entity sits at its centre, as Rockstar places LODs: lodDist is measured from there).
Outputs work/p2/out_lod/. Run: blender -b --python p2_lod.py"""
import sys, json, math, shutil
from pathlib import Path
P2 = Path(__file__).resolve().parent; WK = P2.parent; J = WK.parent
sys.path[:0] = [r'C:\Users\anton\Documents\Codex\TowerCity\work', str(P2), str(WK)]
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
import tc_kit as TK
import jc_frame as F
TK.set_origin(F.OX, F.OY, F.HDEG)
import p2_plan as PL, p2_site_plan as SP
OUT = P2 / 'out_lod'; shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
TK.init(OUT, {}, ext_keys=())
import p2_mats as PM
SW = PM.build()
BLD = ['tower', 'police', 'jail1', 'jail2', 'atrium']
def srgb_mean(name):
    im = bpy.data.images.load(str(PM.TEX / (name + '.dds'))); px = np.array(im.pixels[:], np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    return tuple(float(c) for c in px.mean(0))       # Blender hands a DDS's pixels back as stored (sRGB): no conversion (a linear->sRGB pass
                                                       # lifted the dark roof to light grey and the stone to near white on the rig)
STONE = {'granite': srgb_mean('ko_gv_wall'), 'cream': srgb_mean('mc_wall_0001')}
GRASS = srgb_mean('im_grass10deepb'); ROOF = srgb_mean('im_roof04_big')
SIDEWALK = (0.62, 0.60, 0.57)
COL = {'win': (0.11, 0.13, 0.15), 'ribbon': (0.13, 0.11, 0.09), 'punch': (0.11, 0.13, 0.15), 'arcade': (0.10, 0.09, 0.08), 'slot': (0.16, 0.15, 0.14),
       'vent': (0.07, 0.07, 0.075), 'curtain': (0.30, 0.36, 0.40), 'garage': (0.12, 0.12, 0.12), 'door': (0.12, 0.14, 0.15)}   # door: the atrium entrances (dark glass leaves)
PPM = 6.0                                                         # atlas pixels per metre
def face_img(k, face):
    """one face of building k rasterised: (image HxWx3, s0, z0) - s along the face over its full extent (corners included)."""
    b = PL.B[k]; f, at, ax, s0, s1, o = face
    s0f, s1f = (s0 - b['depth'], s1 + b['depth']) if ax == 'u' else (s0, s1); z0, z1 = PL.SLAB - 0.3, b['top']
    w = max(2, int(math.ceil((s1f - s0f) * PPM))); h = max(2, int(math.ceil((z1 - z0) * PPM)))
    img = np.ones((h, w, 3), np.float32) * np.array(STONE['cream' if k == 'jail2' else 'granite'])
    def rect(a0, a1, c0, c1, col):
        x0, x1 = int((a0 - s0f) * PPM), int(math.ceil((a1 - s0f) * PPM)); y0, y1 = int((z1 - c1) * PPM), int(math.ceil((z1 - c0) * PPM))
        img[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = col
    for kind, a0, a1, c0, c1 in PL.openings(k, face): rect(a0, a1, c0, c1, COL[kind])
    for a0, a1, c0, c1, pr in PL.fins(k, face): rect(a0, a1, c0, c1, tuple(min(1.0, c * 1.06) for c in STONE['cream' if k == 'jail2' else 'granite']))
    return img, s0f, s1f, z0, z1
def atlas(k):
    """every face of building k side by side + a roof patch: (pixels, {face id: (u0, u1, v0, v1) in the atlas, the face's s / z range})."""
    faces = [(fc, face_img(k, fc)) for fc in PL.face_list(k)]
    W_ = sum(im.shape[1] for _, (im, *_r) in faces) + 16; H_ = max(im.shape[0] for _, (im, *_r) in faces)
    A = np.zeros((H_, W_, 3), np.float32); x = 0; reg = {}
    for fc, (im, s0f, s1f, z0, z1) in faces:
        A[:im.shape[0], x:x + im.shape[1]] = im; reg[fc[0]] = (x, x + im.shape[1], 0, im.shape[0], s0f, s1f, z0, z1); x += im.shape[1]
    A[:, x:] = (0.30, 0.36, 0.40) if k == 'atrium' else ROOF; reg['roof'] = (x + 4, W_ - 4, 4, 12)
    return A, reg
def pot(A, maxw=1024, maxh=1024):
    """resize to power-of-two dims (box / nearest), returns (pixels, sx, sy) with the scale applied."""
    h, w = A.shape[:2]; W2 = min(maxw, 1 << int(math.ceil(math.log2(w)))); H2 = min(maxh, 1 << int(math.ceil(math.log2(h))))
    yi = (np.arange(H2) * h / H2).astype(int); xi = (np.arange(W2) * w / W2).astype(int)
    return A[yi][:, xi], W2 / w, H2 / h
import os
DEBUG = os.environ.get('JC_LOD_DEBUG') == '1'                   # diagnostic: every level in its own colour (LOD red, SLOD1 blue, SLOD2/3 green)
def tex(name, A, shader='default.sps'):
    px = np.ones(A.shape[:2] + (4,), np.float32); px[:, :, :3] = A
    if DEBUG: px[:, :, :3] = (1.0, 0.1, 0.1) if name.endswith('_lod_atlas') else (0.1, 0.2, 1.0) if name.startswith('jc_slod1') else (0.1, 1.0, 0.1)
    m = TK.create_shader(shader); m.name = name; nd = m.node_tree.nodes['DiffuseSampler']
    nd.image = TK.dds(name, px[::-1].copy(), OUT / 'tex', False, 'BC3_UNORM'); nd.texture_properties.embedded = True
    m['preserve_authored_uv'] = 1; return m
def box_faces(k, bx, reg, sz, roof=True):
    """the 4 sides (+ top) of a massing box with UVs into the atlas: [(4 verts, 4 uvs)]."""
    u0, u1, v0, v1, z0, z1 = bx; H_, W_ = sz; out = []
    def uv(fid, s, z):
        x0, x1, y0, y1, s0f, s1f, fz0, fz1 = reg[fid]
        X = x0 + (s - s0f) / max(1e-6, (s1f - s0f)) * (x1 - x0); Y = y0 + (fz1 - z) / max(1e-6, (fz1 - fz0)) * (y1 - y0)
        return (X / W_, 1.0 - Y / H_)
    fids = {f[0][0]: f[0] for f in PL.face_list(k) for _ in [0]}
    sides = [('N', [(u1, v1), (u0, v1)], 'u'), ('S', [(u0, v0), (u1, v0)], 'u'), ('E', [(u1, v0), (u1, v1)], 'v'), ('W', [(u0, v1), (u0, v0)], 'v')]
    for f, (p, q), axis in sides:
        fid = next((x for x in reg if x != 'roof' and x[0] == f and _owns(k, x, bx)), None)
        if fid is None: fid = next(x for x in reg if x != 'roof' and x[0] == f)
        sa, sb = (p[0], q[0]) if axis == 'u' else (p[1], q[1])
        V = [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)]
        out.append((V, [uv(fid, sa, z0), uv(fid, sb, z0), uv(fid, sb, z1), uv(fid, sa, z1)]))
    if roof:
        x0, x1, y0, y1 = reg['roof']; ru = [(x0 / W_, 1 - y1 / H_), (x1 / W_, 1 - y1 / H_), (x1 / W_, 1 - y0 / H_), (x0 / W_, 1 - y0 / H_)]
        out.append(([(u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1)], ru))
    return out
def _owns(k, fid, bx):
    """the atrium's faces are per rect (N0, E1 ...): the one on this box's side."""
    if len(fid) == 1: return True
    r = PL.rects(k)[int(fid[1:])]; return tuple(r) == tuple(bx[:4])
def mesh_from(quads, mat, name):
    me = bpy.data.meshes.new(name); V, Fc, U = [], [], []
    for vs, uvs in quads:
        b = len(V); V += vs; Fc.append(tuple(range(b, b + len(vs)))); U += uvs
    me.from_pydata([Vector(v) for v in V], [], Fc); me.materials.append(mat); me.update()
    for p in me.polygons:                                         # wind every face outward (normal away from the box centre)
        pass
    uvl = me.uv_layers.new(name='UVMap 0')
    for li, l in enumerate(me.loops): uvl.data[li].uv = U[l.vertex_index]
    o = bpy.data.objects.new(name, me); bpy.data.collections['Collection'].objects.link(o); return o
INFO = {}
def drawable(name, objs):
    """centre the parts on their own bounds, make the drawable, export; INFO[name] = centre (lot frame) + bounds."""
    P_ = np.array([v.co[:] for o in objs for v in o.data.vertices]); c = (P_.min(0) + P_.max(0)) / 2
    for o in objs: o.data.transform(Matrix.Translation(-Vector(c)))
    root, lo, hi = TK.K.new_drawable(name, objs, uv=0.25, keep_uv={m.name for o in objs for m in o.data.materials})
    for o in root.children_recursive:
        if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model':
            vc = (1.0, 1.0, 1.0, 1.0) if name.startswith('jc_emi') else PM.EXT_VCOL       # his values (p2_mats.EXT_VCOL); the night lights 1.0
            for a in o.data.color_attributes:
                for d in a.data: d.color_srgb = vc
    TK._export(root, OUT); INFO[name] = {'centre': [float(x) for x in c], 'bb_lo': list(lo), 'bb_hi': list(hi)}
ATL = {}
for k in BLD:
    A, reg = atlas(k)
    if k == 'jail2':                                               # the skybridges' faces: stone bands + the dark ribbon, at the atlas's end
        bw = int(8 * PPM); bh = int(4.0 * PPM); B_ = np.ones((bh, bw, 3), np.float32) * np.array(STONE['granite'])
        B_[int(0.95 * PPM):int(3.05 * PPM)] = COL['ribbon']; A2 = np.zeros((max(A.shape[0], bh), A.shape[1] + bw, 3), np.float32); A2[:A.shape[0], :A.shape[1]] = A; A2[:bh, A.shape[1]:] = B_
        reg['bridge'] = (A.shape[1], A.shape[1] + bw, 0, bh); A = A2
    ATL[k] = (A, reg)
SLODQ = []                                                         # (world tri verts, uvs, atlas key)
for k in BLD:
    A, reg = ATL[k]; Ap, sx, sy = pot(A); H_, W_ = A.shape[:2]
    quads = [q for bx in PL.massing(k) for q in box_faces(k, bx, reg, (H_, W_))]
    if k == 'jail2':
        x0, x1, y0, y1 = reg['bridge']
        for (u0, u1, v0, v1, z0, z1) in PL.bridge_massing():
            bq = [((u0, v1, z0), (u1, v1, z0), (u1, v0, z0), (u0, v0, z0)), ((u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1))]
            sides = [((u0, v0), (u1, v0)), ((u1, v0), (u1, v1)), ((u1, v1), (u0, v1)), ((u0, v1), (u0, v0))]
            for p, q in sides:
                quads.append(([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)], [(x0 / W_, 1 - y1 / H_), (x1 / W_, 1 - y1 / H_), (x1 / W_, 1 - y0 / H_), (x0 / W_, 1 - y0 / H_)]))
            for vs in bq: quads.append((list(vs), [(x0 / W_, 1 - y0 / H_)] * 4))
    m = tex(f'jc_{k}_lod_atlas', Ap); o = mesh_from(quads, m, f'jc_{k}_lod_m'); drawable(f'jc_{k}_lod', [o])
    ATL[k] = (A, reg, quads)
objs = []
for k in BLD:
    A, reg, quads = ATL[k]; Ap, _, _ = pot(A, 512, 512)
    objs.append(mesh_from(quads, tex(f'jc_slod1_{k}', Ap), f'jc_slod1_{k}'))
drawable('jc_slod1', objs)
def emi_quads(off):
    out = []
    for k in BLD:
        for face, a0, a1, z0, z1 in PL.lit_bays(k):
            f, at, ax, s0, s1, o = face
            if ax == 'u': V = [(at + o * off, a0, z0), (at + o * off, a1, z0), (at + o * off, a1, z1), (at + o * off, a0, z1)]
            else: V = [(a0, at + o * off, z0), (a1, at + o * off, z0), (a1, at + o * off, z1), (a0, at + o * off, z1)]
            n = (o, 0, 0) if ax == 'u' else (0, o, 0)
            e1 = Vector(V[1]) - Vector(V[0]); e2 = Vector(V[2]) - Vector(V[0])
            if e1.cross(e2).dot(Vector(n)) < 0: V = V[::-1]
            out.append((V, [(0, 0), (1, 0), (1, 1), (0, 1)] if e1.cross(e2).dot(Vector(n)) >= 0 else [(0, 1), (1, 1), (1, 0), (0, 0)]))
    for n, (u0, u1, v0, v1, z0, z1) in PL.BRIDGES.items():          # the skybridges' ribbons (p2_facade.bridges: lit by (name, face))
        along_v = (v1 - v0) > (u1 - u0)
        for f, at, ax, a0, a1, o in ([('E', u1, 'u', v0, v1, 1), ('W', u0, 'u', v0, v1, -1)] if along_v else [('N', v1, 'v', u0, u1, 1), ('S', v0, 'v', u0, u1, -1)]):
            if not PL.lit(n, f): continue
            zb, zt = z0 + 0.95, z1 - 0.95
            V = [(at + o * off, a0, zb), (at + o * off, a1, zb), (at + o * off, a1, zt), (at + o * off, a0, zt)] if ax == 'u' else [(a0, at + o * off, zb), (a1, at + o * off, zb), (a1, at + o * off, zt), (a0, at + o * off, zt)]
            nn = (o, 0, 0) if ax == 'u' else (0, o, 0); e1 = Vector(V[1]) - Vector(V[0]); e2 = Vector(V[2]) - Vector(V[0])
            out.append((V if e1.cross(e2).dot(Vector(nn)) >= 0 else V[::-1], [(0, 0), (1, 0), (1, 1), (0, 1)]))
    return out
drawable('jc_emi_lod', [mesh_from(emi_quads(0.15), TK.MAT['win_emis'], 'jc_emi_lod_m')])
drawable('jc_emi_slod', [mesh_from(emi_quads(0.4), TK.MAT['win_emis'], 'jc_emi_slod_m')])
# ---- the SLOD2 / SLOD3 additions: massing + ground plates, world triangles, UVs into one combined atlas ----
CELLS = {}; tiles = []
for k in BLD:
    Ap, _, _ = pot(ATL[k][0], 256, 256); tiles.append((k, Ap))
for nm, col in (('lot', SIDEWALK), ('podium', SIDEWALK), ('lawn', GRASS), ('walk', SIDEWALK)):
    t = np.ones((32, 32, 3), np.float32) * np.array(col); tiles.append((nm, t))
SA = np.zeros((1024, 1024, 3), np.float32); x = y = rowh = 0
for nm, t in tiles:
    h, w = t.shape[:2]
    if x + w > 1024: x = 0; y += rowh; rowh = 0
    SA[y:y + h, x:x + w] = t; CELLS[nm] = (x, y, w, h); x += w; rowh = max(rowh, h)
def remap(nm, uv):
    x0, y0, w, h = CELLS[nm]; u, v = uv; return ((x0 + u * w) / 1024, 1 - (y0 + (1 - v) * h) / 1024)
TRI, TUV = [], []
def tri_add(V, U, nm):
    for i in range(1, len(V) - 1):
        TRI.append([F.W(*V[j][:2]) + (V[j][2],) for j in (0, i, i + 1)]); TUV.append([remap(nm, U[j]) for j in (0, i, i + 1)])
for k in BLD:
    for V, U in ATL[k][2]: tri_add(V, U, k)
def plate(poly, zf, nm, grid=4.0):
    bm = bmesh.new(); vs = [bm.verts.new(Vector((u, v, 0))) for u, v in poly]; f = bm.faces.new(vs); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    for f in bm.faces:
        V = [(v.co.x, v.co.y, zf(v.co.x, v.co.y)) for v in f.verts]
        if Vector(V[1]).cross(Vector(V[2])) is None: pass
        a, b, c = (Vector(p) for p in V)
        if (b - a).cross(c - a).z < 0: V = V[::-1]
        tri_add(V, [(0.5, 0.5)] * 3, nm)
    bm.free()
lot = [F.L(*p[:2]) for p in F.lot_w()]
plate(lot, lambda u, v: F.slab_z(*F.W(u, v)), 'lot')
for u0, u1, v0, v1 in SP.S['podium']: plate([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], lambda u, v: PL.G + 0.02, 'podium')
for p in SP.S['lawn']: plate(p, lambda u, v: SP.lawn_z(u, v) + 0.02, 'lawn')
for p in SP.S['walk']: plate(p, lambda u, v: SP.lawn_z(u, v) + 0.02, 'walk')
px = np.ones((1024, 1024, 4), np.float32); px[:, :, :3] = SA
if DEBUG: px[:, :, :3] = (0.1, 1.0, 0.1)
TK.dds('jc_slod_atlas', px[::-1].copy(), OUT / 'tex', False, 'BC3_UNORM')
shutil.copy(OUT / 'tex' / 'compressed' / 'jc_slod_atlas.dds', OUT / 'jc_slod_atlas.dds')
np.savez(OUT / 'slod_add.npz', tris=np.array(TRI, np.float64), uvs=np.array(TUV, np.float32))
json.dump(INFO, open(OUT / 'p2_lod_layout.json', 'w'), indent=1)
print('P2_LOD_PASS', json.dumps({k: [round(x, 1) for x in v['centre']] for k, v in INFO.items()}), 'slod tris', len(TRI), flush=True)
