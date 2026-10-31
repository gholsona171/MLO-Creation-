"""Area 3 build (Blender, called by jc3_build.py): the Police HQ's underground garage from jc3_pgarage's numbers - the B1 deck (pdeck),
the IN and OUT ramp rooms (pramp_in, pramp_out: each lane's trench from its street door down to B1, under L2's slab), the columns
with their numbers, the bay markings, the workshop / fuel / wash fit-out. Rockstar's carpark recipe (hei_dt1_11_garage, playbook 03):
concrete everywhere (Mission Row's conc / speckle here), painted markings, prop_wall_light_05a fittings; timecycle carpark_dt1_03.
Portals: deck <-> each ramp at its foot (the lane's full width and height), each ramp -> limbo at its street door (the roll-up door,
a native door on that portal)."""
import tc_kit as TK
import jc3_tower as JT, jc3_police as P, jc3_pgarage as G, jc3_pgarage_dress as GD
import jc3_tower_build as TB
OPS = TB.OPS
CEIL_PLATE = 0.02                                                         # the B1 ceiling plate under L1's slab (2.78 m clear)
RAMP_CEIL = P.P2 - 0.4                                                    # 31.6: the ramps' ceiling = the underside of L2's slab
def deck_region():
    return TK.rects_minus(*G.B1, [(G.U_FOOT, G.B1[1], G.B1[2], G.TRENCH[1]), P.STAIR_B])
def _px_arrow(n=128):
    """a white arrow pointing up the texture (+v), transparent round it (rows top-first, flipped for Blender)."""
    import numpy as np
    px = np.zeros((n, n, 4), np.float32); y, x = np.mgrid[0:n, 0:n] / (n - 1)
    head = (y < 0.45) & (np.abs(x - 0.5) < (0.45 - y) * 1.0); shaft = (y >= 0.45) & (y < 0.95) & (np.abs(x - 0.5) < 0.14)
    m = head | shaft; px[m] = (0.92, 0.92, 0.88, 1.0); return px[::-1].copy()
def _px_blob(seed, n=64):
    """an oil stain: a dark irregular blob, soft edged."""
    import numpy as np
    rng = np.random.default_rng(seed); y, x = np.mgrid[0:n, 0:n] / (n - 1) - 0.5; r = np.hypot(x, y)
    a = np.arctan2(y, x); edge = 0.38 + 0.06 * np.sin(3 * a + rng.random() * 6) + 0.04 * np.sin(7 * a + rng.random() * 6)
    alpha = np.clip((edge - r) / 0.08, 0, 1) * (0.55 + 0.25 * rng.random((n, n)))
    px = np.zeros((n, n, 4), np.float32); px[..., :3] = 0.07; px[..., 3] = alpha; return px
def _px_drain(n=64):
    import numpy as np
    px = np.zeros((n, n, 4), np.float32); px[...] = (0.25, 0.25, 0.25, 1.0); px[4:-4, 4:-4] = (0.05, 0.05, 0.05, 1.0)
    for k in range(8, n - 6, 7): px[6:-6, k:k + 3] = (0.32, 0.32, 0.32, 1.0)
    return px
def floor_decal(room, u, v, along_up, across, up_deg, px, name, z):
    """a painted floor marking: a quad on the floor (decal shader: drawn over it, never fights it), its texture's top toward `up_deg`."""
    import bpy, math
    from mathutils import Vector
    key = name + '_d'                                                     # '_d': decals may overlay (the sweep)
    if key not in TK.MAT:
        m = TK.tex_mat(key, px, shader='decal.sps'); m['preserve_authored_uv'] = True; TK.KEEP.add(m.name); TK.MAT[key] = m
    t = math.radians(up_deg); d = (math.cos(t), math.sin(t)); r = (d[1], -d[0])
    c = lambda a, b: Vector((u + r[0] * a + d[0] * b, v + r[1] * a + d[1] * b, z))
    pts = [c(-across / 2, -along_up / 2), c(across / 2, -along_up / 2), c(across / 2, along_up / 2), c(-across / 2, along_up / 2)]
    me = bpy.data.meshes.new(key); me.from_pydata(pts, [], [(0, 1, 2, 3)]); me.materials.append(TK.MAT[key])
    uv = me.uv_layers.new(name='UVMap 0')
    for li, q in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[li].uv = q
    me.update(); assert me.polygons[0].normal.z > 0.99, f'decal {name} faces down'
    o = bpy.data.objects.new(key, me); TK.coll().objects.link(o); TK.PARTS[room].append(o)
def dressing(room):
    """the garage's dressing (jc3_pgarage_dress): props, signs, floor markings, hazard bands / pipes / duct / panels, warm task lights."""
    for x in GD.dress(): OPS['props'].append((room, x[1], x[2], x[3], x[4], x[5]))
    for r, c, face, w, h, lines, name, bg, fg, hang in GD.signs():
        if hang: TK.hanging_sign(r, c, face, w, h, lines, name, hang, bg=bg, fg=fg, emis=False, scale=1.0)
        else: TK.sign(r, c, face, w, h, lines, name, bg=bg, fg=fg, emis=False, scale=1.0)
    zd = G.ZB + 0.004
    for i, (kind, u, v, a, b, up, text) in enumerate(GD.decals()):
        if kind == 'number': floor_decal(room, u, v, b, a, up, TK.sign_px([text], a, b, (232, 190, 30), (20, 20, 20), 1.0), f'JC gar bay {text}', zd)
        elif kind == 'arrow': floor_decal(room, u, v, a, b, up, _px_arrow(), 'JC gar arrow', zd)
        elif kind == 'oil': floor_decal(room, u, v, b, a, up, _px_blob(i), f'JC gar oil {i}', zd - 0.001)
        elif kind == 'drain': floor_decal(room, u, v, b, a, up, _px_drain(), 'JC gar drain', zd)
    for lo, hi, mat, col in GD.boxes(): TK.box(room, lo, hi, mat, col=col)
    for u, v, z, e, fo, size, col in GD.lamps(): TK.lamp(room, u, v, z, energy=e, falloff=fo, size=size, color=col)
def ramp_collision(room, us, c0, c1):
    """a ramp's collision: one open, welded surface strip (shared vertices at every section, up-facing), no faces under it. Prisms
    with their own collision left a vertical end face under every 0.5 m seam, flush with the surface: a car climbing the OUT ramp
    caught three of them (rig 2026-10-30; jc3_ramp_seams.py reads the compiled bound and fails on any such riser)."""
    import bpy
    from mathutils import Vector
    V = [Vector((u, v, G.ramp_z(u))) for u in us for v in (c0, c1)]
    F = [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(len(us) - 1)]   # (u, c0) -> (u+, c0) -> (u+, c1) -> (u, c1): normal +z
    me = bpy.data.meshes.new('col'); me.from_pydata(V, [], F); me.update()
    assert all(p.normal.z > 0.9 for p in me.polygons), 'the ramp collision surface must face up'
    me.materials.append(TK.colmat(room)); o = bpy.data.objects.new('col', me); TK.coll().objects.link(o); TK._sink(room, o)
def build():
    R = {}; holes = TB.opening_boxes()
    # ---------------- the B1 deck ----------------
    room = 'pdeck'; reg = deck_region(); R[room] = reg
    feet = [(G.U_FOOT - 0.15, G.U_FOOT + 0.05, l0, l1, G.ZB, G.CEIL_B - CEIL_PLATE) for l0, l1 in G.LANES.values()]   # the deck's lining, the full lane
    ramps = [((G.U_FOOT, G.B1[1], G.TRENCH[0], G.TRENCH[1]), 0.1), (P.STAIR_B, 0.15)]
    TB.slab(room, reg, G.ZB - 0.4, G.ZB, 'conc')
    TB.slab(room, reg, G.CEIL_B - CEIL_PLATE, G.CEIL_B, 'conc', col=False)
    TB.lining(room, reg, ramps, G.ZB, G.CEIL_B - CEIL_PLATE, 'conc', holes + feet, ext_t=G.RW, int_t=0.1)
    for i, (u, v) in enumerate(G.COLUMNS):
        TK.box(room, (u - 0.25, v - 0.25, G.ZB), (u + 0.25, v + 0.25, G.CEIL_B - CEIL_PLATE), 'conc')
        for face, du, dv in (('-u', -0.25, 0.0), ('+u', 0.25, 0.0)):
            TK.sign(room, (u + du, v + dv, G.ZB + 1.8), face, 0.4, 0.4, [f'P{i + 1}'],                     # (TK.sign stands 5 cm off the face)
                    f'TC sign column P{i + 1}', bg=(230, 190, 30), fg=(20, 20, 20), emis=False, scale=1.0)
    for u, v, h, row in G.bays():                                         # the bay lines (Rockstar's decal shader: drawn over the floor)
        if row < 0: continue
        r = G.ROWS[row]
        if r[4] in ('u-', 'u+'): TK.box(room, (r[0], v - G.BAY_W / 2 - 0.05, G.ZB), (r[1], v - G.BAY_W / 2 + 0.05, G.ZB + 0.003), 'paint_d', col=False)
        else: TK.box(room, (u - G.BAY_W / 2 - 0.05, r[2], G.ZB), (u - G.BAY_W / 2 + 0.05, r[3], G.ZB + 0.003), 'paint_d', col=False)
    TB.lights_grid(room, reg, G.CEIL_B - CEIL_PLATE, 6.0)
    TK.box(room, (G.ISLAND[0], G.ISLAND[2], G.ZB), (G.ISLAND[1], G.ISLAND[3], G.ZB + G.ISLAND[4]), 'conc')         # the fuel island's kerb
    for m, u, v, z, h in G.fitout(): OPS['props'].append((room, m, u, v, z, h))
    dressing(room)
    for l0, l1 in G.LANES.values():                                       # the ramp feet: deck <-> ramp
        k = 'pramp_in' if (l0 + l1) / 2 == G.IN_C else 'pramp_out'
        # the foot's portal on the plane where the ramp room starts, the full lane: the deck's reveal in front of it is the deck's own
        # geometry, the ramp's side walls end on it (a portal on the deck's face left the reveal's plate visible from the ramp unportalled)
        OPS['portals'].append({'from': room, 'to': k, 'kind': f'{k} foot', 'P': ('u', G.U_FOOT, l0, l1, G.ZB, G.CEIL_B - CEIL_PLATE, 1)})
    # ---------------- the ramp rooms ----------------
    for k, (l0, l1) in (('pramp_in', G.LANES['in']), ('pramp_out', G.LANES['out'])):
        lane = (G.U_FOOT, P.EI, l0, l1); R[k] = [lane]
        c0, c1 = l0 + 0.2, l1 - 0.2                                       # the clear lane, inside its 0.2 linings (the lanes do not touch)
        us = [G.U_FOOT + i * 0.5 for i in range(int((G.U_TOP - G.U_FOOT) / 0.5))] + [G.U_TOP]
        for a, b in zip(us, us[1:]):                                      # the ramp: a solid under its surface (drawn only) ...
            TK.prism(k, a, b, c0, c1, lambda u: G.ZB - 0.4, G.ramp_z, 'conc', col=False)
        ramp_collision(k, us, c0, c1)                                     # ... and ONE welded collision surface over its whole length
        TK.box(k, (G.U_FOOT, l0, RAMP_CEIL - CEIL_PLATE), (P.EI, l1, RAMP_CEIL), 'conc', col=False)
        door = [(P.EI - 0.5, P.EI + 0.5, *G.DOORS['in' if k == 'pramp_in' else 'out'], G.ZD - 0.1, G.ZD + G.ROLLUP[2] + 0.1)]
        foot = [(G.U_FOOT - 0.05, G.U_FOOT + 0.3, l0 + 0.2, l1 - 0.2, G.ZB, G.CEIL_B - CEIL_PLATE)]   # through the west wall only, the clear lane
        TB.lining(k, [lane], [((G.U_FOOT, P.EI, *G.LANES['out' if k == 'pramp_in' else 'in']), 0.1)], G.ZB - 0.4, RAMP_CEIL - CEIL_PLATE,
                  'conc', holes + door + foot, ext_t=0.2, int_t=0.1)
        TB.lights_grid(k, [lane], RAMP_CEIL - CEIL_PLATE, 5.0)
        d0, d1 = G.DOORS['in' if k == 'pramp_in' else 'out']
        OPS['portals'].append({'from': k, 'to': 'limbo', 'kind': f'{k} street door', 'P': ('u', P.EI - 0.2, d0, d1, G.ZD, G.ZD + G.ROLLUP[2], 1),
                               'door': f'{k}_rollup'})
        OPS['doors'].append({'name': f'{k}_rollup', 'model': G.ROLLUP[0], 'room': k, 'pos': [P.EI + 0.2, (d0 + d1) / 2, G.ZD + G.ROLLUP[2] / 2],
                             'heading': 90.0, 'portal': (k, 'limbo')})
    return R
