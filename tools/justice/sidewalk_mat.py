"""Justice Center (from Tower City work/sidewalk_mat.py): the lot slab IS Rockstar's sidewalk (Antonio, 2026-10-24: "either your
sidewalk colour takes over the entire sidewalk, or you leave it to the base sidewalk colour - two different colours look crazy and
patchy"). Run inside Blender.
  * one material for the whole lot: im_sidewalk012, the sidewalk that rings most of the block's edge (256 of 560 m measured 0.3 m outside
    the lot outline; dc_road_crossing_002 143 m, im_sidewalk003 96 m), copied from his road model sc1_rd_r4_02 (shader
    normal_spec_detail.sps, its parameters and sampler names, textures NOT embedded: they bind through the archetype's txd sc1_rd_road
    and its parents - im_sidewalk012 itself lives in the global gtxd ch1struct11+hi)
  * UVs: his scale (5.98 m per UV, the median of his faces) and his direction (his u runs along the street grid = the lot frame u)
  * the texture is 2 x 2 concrete flags with a narrow flag strip on its left edge; it tiles both ways (TILE 1, no kerb band)
  * vertex colour 0: inverse-distance mean of his nearest sidewalk corners of the same material, easing to his median 1 - 5 m away
    from his sidewalk (one even tone over the lot; his corner shading spread wide reads as blotches - Tower City)."""
import json, math, numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter')
TXD = 'sc1_rd_road'
LOT_MAT = {'lot': 'im_sidewalk012'}
SRC_MODEL = 'sc1_rd_r4_02'                       # the road model that carries it (src/native)
S = json.load(open(T / 'plan/sidewalks.json'))                  # tools/sidewalk_dump.py
ORIGIN = (335.87, -1640.11); H = math.radians(50.0)            # the lot frame (jc_frame)
TILES = {'im_sidewalk012': 1.0}                 # 2 x 2 flags, tiles both ways
def lot_uv(u, v, mat, tile):
    """lot-frame (u, v) -> his UV for that material, u inside its own tile (index `tile`)."""
    m = S['mats'][mat]['m_per_uv']; return ((u - tile * TILES[mat] * m) / m, v / m)
def lot_of(x, y):
    dx, dy = x - ORIGIN[0], y - ORIGIN[1]; return (dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H))
_C = {}
def _corners(mat):
    if mat not in _C:
        a = np.array([c[1:8] for c in S['corners'] if c[0] == mat], np.float64)
        _C[mat] = (a[:, :3], a[:, 3:7], np.median(a[:, 3:7], axis=0))
    return _C[mat]
def vcol(x, y, z, mat, k=24):
    """his vertex colour 0 near a point: the inverse-distance mean of his nearest sidewalk corners AT THIS LEVEL (|dz| < 1.5 m: the deck's
    sidewalk never takes the dark, shaded colours of the street under it), easing to his median colour 1 - 5 m away from his sidewalk
    (our wide paving keeps one even tone - his corner-to-corner shading spread over a plaza read as dark blotches)."""
    P, Cc, med = _corners(mat)
    lvl = np.abs(P[:, 2] - z) < 1.5
    if lvl.sum() < k: return tuple(med)
    P2, C2 = P[lvl], Cc[lvl]; d = np.sqrt(((P2[:, :2] - (x, y)) ** 2).sum(1)) + 0.05
    i = np.argpartition(d, k)[:k]; w = d[i] ** -2; near = (C2[i] * w[:, None]).sum(0) / w.sum()
    t = min(max((d.min() - 1.0) / 4.0, 0.0), 1.0)
    return tuple(near * (1 - t) + med * t)
def load():
    """Rockstar's sidewalk materials, copied into this Blender session: {name: material}. The imported road model is removed."""
    import bpy
    before = set(bpy.data.objects)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(T / 'src/native'), files=[{'name': SRC_MODEL + '.ydr'}])
    out = {}
    for m in list(bpy.data.materials):
        if m.name in S['mats'] and m.name not in out:
            c = m.copy(); c.name = 'JC ' + m.name; c['preserve_authored_uv'] = 1; c['tc_sidewalk'] = m.name
            for n in c.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image is not None: n.texture_properties.embedded = False
            out[m.name] = c
    for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
    assert set(out) == set(S['mats']), ('sidewalk materials missing from', SRC_MODEL, set(S['mats']) - set(out))
    return out
def paint(o, M):
    """o: a drawable model (mesh) placed by M (its local -> world matrix). Every face of one of our sidewalk materials is cut on the
    tile seams (constant lot u, every TILE x metres-per-UV) and gets his UVs (inside its tile) and his vertex colour 0 (sRGB, as
    stored) from his nearest sidewalk corners. Returns the face count painted."""
    import bpy, bmesh
    from mathutils import Vector, Matrix
    me = o.data; Mi = M.inverted(); R3 = Mi.to_3x3()
    mats = [(m.get('tc_sidewalk') if m else None) for m in me.materials]
    if not any(mats): return 0
    bm = bmesh.new(); bm.from_mesh(me)
    ux = Vector((math.cos(H), math.sin(H), 0.0))                     # the lot's u axis in the world
    for mat in set(m for m in mats if m):
        W_ = TILES[mat] * S['mats'][mat]['m_per_uv']
        fs = [f for f in bm.faces if mats[f.material_index] == mat]
        us = [lot_of(*(M @ v.co).xy)[0] for f in fs for v in f.verts]
        if not us: continue
        for k in range(int(math.floor(min(us) / W_)), int(math.ceil(max(us) / W_)) + 1):
            g = [x for f in fs if f.is_valid for x in [f] + list(f.edges) + list(f.verts)]
            p0 = Vector((ORIGIN[0], ORIGIN[1], 0.0)) + ux * (k * W_)
            res = bmesh.ops.bisect_plane(bm, geom=list(set(g)), plane_co=Mi @ p0, plane_no=(R3 @ ux).normalized())
            fs = [f for f in set(fs) | {x for x in res['geom'] if isinstance(x, bmesh.types.BMFace)} if f.is_valid and mats[f.material_index] == mat]
    bm.to_mesh(me); bm.free()
    uvl = me.uv_layers[0]; col = me.color_attributes[0] if me.color_attributes else None; n = 0
    for f in me.polygons:
        mat = mats[f.material_index] if f.material_index < len(mats) else None
        if not mat: continue
        c = M @ f.center; tile = math.floor(lot_of(c.x, c.y)[0] / (TILES[mat] * S['mats'][mat]['m_per_uv']))
        for li in f.loop_indices:
            w = M @ me.vertices[me.loops[li].vertex_index].co; u, v = lot_of(w.x, w.y)
            uvl.data[li].uv = lot_uv(u, v, mat, tile)
            if col is not None and col.domain == 'CORNER': col.data[li].color_srgb = vcol(w.x, w.y, w.z, mat)
        n += 1
    return n
