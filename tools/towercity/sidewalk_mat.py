"""Tower City: our ground outside the buildings IS Rockstar's sidewalk (Antonio, 2026-10-24: "either your sidewalk colour takes over the
entire sidewalk, or you leave it to the base sidewalk colour - two different colours look crazy and patchy"). Replaces paving_mat.py
(our own grey flags). Run inside Blender.
  * the material is Rockstar's own, copied from his road model (shader normal_spec_detail.sps, its parameters, its sampler texture
    names - dc_sidewalk001 / 004 + _n / _s + the detail map), textures NOT embedded: the game binds his own textures through the
    archetype's textureDictionary TXD (the road models' txd, dt1_rd1_1 - l0_maps.py / ext_meta.py set it)
  * per lot the sidewalk that rings it: west (tower) dc_sidewalk001 (741 + 294 m2 of the 5 m band round the lot), east (mall)
    dc_sidewalk004 (1049 m2; dc_sidewalk001 252 m2 on one street) - survey/sidewalks.json (tools/sidewalk_dump.py)
  * UVs: his scale (metres per UV, median of his faces) and his direction (aligned with the street grid = the lot frame)
  * vertex colour 0 (his baked light / dirt): inverse-distance mean of his nearest sidewalk corners of the same material, so the
    paving continues the sidewalk it meets instead of starting a new tone at the lot edge."""
import json, math, numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
TXD = 'dt1_rd1_1'
LOT_MAT = {'west': 'dc_sidewalk001', 'east': 'dc_sidewalk004'}
SRC_MODEL = 'dt1_rd1_r1_08'                       # a road model that carries both materials (src/native)
S = json.load(open(T / 'survey/sidewalks.json'))
ORIGIN = (-78.897, -827.328); H = math.radians(69.5)
TILES = {'dc_sidewalk001': 0.9, 'dc_sidewalk004': 1.0}   # dc_sidewalk001 (dt1_rd1_1.ytd): 4 x 4 flags over u 0 .. 0.9 and a cobble / drain band
                                                  # at u 0.9 .. 1 (the band he lays along the kerb). Our wide paving uses the flags only: its
                                                  # faces are cut every TILE x his metres-per-UV across u, and each face's u runs 0 .. TILE inside
                                                  # its tile (the seam falls on a flag joint). dc_sidewalk004 (globalroads.ytd, the parent txd):
                                                  # 2 x 2 plain flags, tiles both ways (TILE 1).
def lot_uv(u, v, mat, tile):
    """lot-frame (u, v) -> his UV for that material, u inside its own tile (index `tile`)."""
    m = S['mats'][mat]['m_per_uv']; return ((u - tile * TILES[mat] * m) / m, v / m)
def lot_of(x, y):
    dx, dy = x - ORIGIN[0], y - ORIGIN[1]; return (dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H))
_C = {}
def _corners(mat):
    if mat not in _C:
        a = np.array([c[1:8] for c in S['corners'] if c[0] == mat], np.float64); _C[mat] = (a[:, :2], a[:, 3:7])
    return _C[mat]
def vcol(x, y, mat, k=8):
    P, Cc = _corners(mat); d = np.sqrt(((P - (x, y)) ** 2).sum(1)) + 0.05
    i = np.argpartition(d, k)[:k]; w = d[i] ** -2
    return tuple((Cc[i] * w[:, None]).sum(0) / w.sum())
def load():
    """Rockstar's sidewalk materials, copied into this Blender session: {name: material}. The imported road model is removed."""
    import bpy
    before = set(bpy.data.objects)
    assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(T / 'src/native'), files=[{'name': SRC_MODEL + '.ydr'}])
    out = {}
    for m in list(bpy.data.materials):
        if m.name in S['mats'] and m.name not in out:
            c = m.copy(); c.name = 'TC ' + m.name; c['preserve_authored_uv'] = 1; c['tc_sidewalk'] = m.name
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
            if col is not None and col.domain == 'CORNER': col.data[li].color_srgb = vcol(w.x, w.y, mat)
        n += 1
    return n
