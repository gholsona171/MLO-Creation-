"""Area 3 build (Blender, called by jc3_build.py): the Police HQ's underground garage from jc3_pgarage's numbers - the B1 deck (pdeck),
the IN and OUT ramp rooms (pramp_in, pramp_out: each lane's trench from its street door down to B1, under L2's slab), the columns
with their numbers, the bay markings, the workshop / fuel / wash fit-out. Rockstar's carpark recipe (hei_dt1_11_garage, playbook 03):
concrete everywhere (Mission Row's conc / speckle here), painted markings, prop_wall_light_05a fittings; timecycle carpark_dt1_03.
Portals: deck <-> each ramp at its foot (the lane's full width and height), each ramp -> limbo at its street door (the roll-up door,
a native door on that portal)."""
import tc_kit as TK
import jc3_tower as JT, jc3_police as P, jc3_pgarage as G
import jc3_tower_build as TB
OPS = TB.OPS
CEIL_PLATE = 0.02                                                         # the B1 ceiling plate under L1's slab (2.78 m clear)
RAMP_CEIL = P.P2 - 0.4                                                    # 31.6: the ramps' ceiling = the underside of L2's slab
def deck_region():
    return TK.rects_minus(*G.B1, [(G.U_FOOT, G.B1[1], G.B1[2], G.TRENCH[1]), P.STAIR_B])
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
        for a, b in zip(us, us[1:]):                                      # the ramp: a solid under its surface, smooth collision
            TK.prism(k, a, b, c0, c1, lambda u: G.ZB - 0.4, G.ramp_z, 'conc')
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
