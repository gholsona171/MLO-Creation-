"""Area 3 Police HQ: the wet rooms (2026-11-11 rebuild, Antonio's rig shots at postal 446: "a sink-and-toilet mash-up: a carved
dresser with a toilet stuck to its end", "the stalls are horrible", "see into the restroom from the hallway").
  * Vanities are Rockstar's commercial counter (v_73_p_ap_banosink_aa001: the FIB building's granite counter, five under-mount basins,
    wall hung, 4.9 m); the single-user public WCs get Rockstar's wall basin (prop_sink_02). The residential v_res_m_sinkunit (a carved
    dresser WITH a toilet modelled into its end) and the fast-food prep sink are gone from the building.
  * Toilets stand only inside stalls (or alone in a single-user WC behind its own solid door): stalls are kit (no Rockstar stall fits
    these rooms: v_73_p_ap_banostall_az is 7.2 x 2.9 m): 25 mm laminate partitions 0.3 m off the floor to 2.1 m, floor-mounted front
    panels, a steel headrail, and a 0.6 m door per stall standing open inward at 90 deg along the lot grid (static, with collision,
    as Rockstar's stall doors are static models; an angled leaf would be the one face off the grid).
  * Men's rooms: Rockstar's urinal row (v_73_p_ap_banourinal_aa003, four urinals with privacy screens, front = the model's -x).
  * Every restroom / locker-room door is Rockstar's solid office door (v_ilev_fib_door1, no glass: jc3_police.DOOR_MODEL).
  props() -> [(room, model, u, v, z over the floor, heading)]   kit() -> [(room, lo, hi, material, collision)]
Heading: 0 faces -v (a model's front is -y), 90 +u, 180 +v, 270 -u."""
import jc3_police as P
from jc3_police_dress import W, bb, face_of, local
P1, P2 = P.P1, P.P2
COUNTER, BASIN, URINAL = 'v_73_p_ap_banosink_aa001', 'prop_sink_02', 'v_73_p_ap_banourinal_aa003'
TOILET, DRYER, BIN = 'prop_toilet_02', 'prop_handdry_01', 'v_serv_waste_bin1'
COUNTER_BOTTOM = 0.15                    # the counter's 0.71 m depth hangs from a 0.86 m top
BASIN_BOTTOM = 0.24                      # prop_sink_02: rim at 0.86 (its pivot 0.44 over its bottom, the rim 0.18 over the pivot)
STALL_D, DOOR_W, PANEL_T = 1.55, 0.6, 0.025
PART_Z, TOP_Z = 0.3, 2.1
SHOWER1 = (11.8, 12.9, 14.0)             # men's shower partitions (u) on the south wall (G_EA), kept as approved
SHOWER2 = (18.5, 19.6, 20.7)             # women's shower partitions (u) on G_LOCK, in the strip by the stair
def centred(room, model, axis, line, side, a, bottom=0.0):
    """W() with the model's bounding-box CENTRE (not its pivot) at a along the wall."""
    r, m, u, v, z, h = W(room, model, axis, line, side, a, bottom)
    lo, hi = bb(model); cx = (lo[0] + hi[0]) / 2; du, dv = local(0.0, 0.0, h, cx, 0.0)
    return (r, m, u - du, v - dv, z, h)
def urinals(room, axis, line, side, a, floor_z):
    """the urinal row centred at a, its back (the model's +x, 0.28) on the wall face over the trim bands, facing the room."""
    lo, hi = bb(URINAL); f = face_of(room, axis, line, side, a)
    pu, pv = (f + side * 0.15, a) if axis == 'u' else (a, f + side * 0.15)
    d = f + side * (P.trim_proud(room, pu, pv, 0.0, hi[2] - lo[2], axis, side) + hi[0] + 0.01)
    if axis == 'v': h = 270.0 if side > 0 else 90.0                  # the model's -x onto +v / -v
    else: h = 0.0 if side > 0 else 180.0                             # ... onto +u / -u
    u, v = (d, a) if axis == 'u' else (a, d)
    return [(room, URINAL, u, v, 0.0, h)]
def stalls(room, axis, line, side, a0, a1, n, floor_z, ends=(True, True)):
    """n toilet stalls against the wall `line` (the room on `side`) between a0 .. a1 along it: partitions between them (and at an end
    that is not a wall: ends), front panels either side of a centred 0.6 m door, a headrail, each door ajar inward, a toilet on the
    back wall facing the door. -> (props, boxes)"""
    f = face_of(room, axis, line, side, (a0 + a1) / 2); F = f + side * STALL_D
    z = floor_z
    def bx(n0, n1, b0, b1, z0, z1, mat='panel_grey', col=True):
        lo_n, hi_n = min(n0, n1), max(n0, n1)
        lo, hi = ((lo_n, b0, z + z0), (hi_n, b1, z + z1)) if axis == 'u' else ((b0, lo_n, z + z0), (b1, hi_n, z + z1))
        return (room, lo, hi, mat, col)
    props, boxes = [], []
    w = (a1 - a0) / n; cuts = [a0 + w * i for i in range(n + 1)]
    for i, c in enumerate(cuts):
        if (i == 0 and not ends[0]) or (i == n and not ends[1]): continue
        p0 = c if i == 0 else (c - PANEL_T if i == n else c - PANEL_T / 2); p1 = p0 + PANEL_T
        boxes.append(bx(f, F, p0, p1, PART_Z, TOP_Z))                                      # partitions (off the floor)
    for i in range(n):
        s0, s1 = cuts[i], cuts[i + 1]; c = (s0 + s1) / 2; d0, d1 = c - DOOR_W / 2, c + DOOR_W / 2
        boxes += [bx(F, F + side * PANEL_T, s0, d0, 0.0, TOP_Z), bx(F, F + side * PANEL_T, d1, s1, 0.0, TOP_Z)]   # front panels (floor to rail)
        boxes.append(bx(F, F - side * DOOR_W, d1 - PANEL_T, d1, PART_Z, TOP_Z - 0.05))   # the door, open inward on its far jamb's hinge
        props.append(W(room, TOILET, axis, line, side, c))
    boxes.append(bx(F, F + side * 0.04, a0, a1, TOP_Z, TOP_Z + 0.05, 'steel', False))      # the headrail over the fronts
    return props, boxes
def l2_restrooms():
    """L2 (pstaff2): the men's and women's restrooms, 8.8 x 2.75 m each, entered from the corridor's east wall (u 24) at their west end:
    the counter along one long wall, two stalls across the east end, the men's urinal row on the other long wall."""
    S, z = 'pstaff2', P2; props, boxes = [], []
    for name, v0, v1, cw, cs in (("men's restroom", -32.75, -30.0, -30.0, -1), ("women's restroom", -35.5, -32.75, -35.5, 1)):
        props.append(centred(S, COUNTER, 'v', cw, cs, 27.85, COUNTER_BOTTOM))              # u 25.4 .. 30.3 (the door's swing: u < 25.3)
        props += [W(S, DRYER, 'v', cw, cs, 30.75, 1.05), W(S, BIN, 'v', cw, cs, 30.75)]
        a0, a1 = face_of(S, 'v', v0, 1, 31.9), face_of(S, 'v', v1, -1, 31.9)                # between the long walls' faces
        p, b = stalls(S, 'u', P.LOB_W, -1, a0, a1, 2, z, ends=(False, False)); props += p; boxes += b
        if name.startswith('men'): props += urinals(S, 'v', v0, 1, 27.1, z)                 # the south wall, u 25.4 .. 28.8
    return props, boxes
def l1_showers():
    """L1 (pstaff1): the men's showers / WC (three showers on the south wall, two stalls on the stair wall, the counter on the north
    wall west of the door, urinals); the women's: two showers in the strip by the stair, two stalls on the south wall, the counter on
    the north wall (the lockers move to the west wall: dress2). The men's door moves east (u 16.75: jc3_police.INNER_DOORS) so the
    counter fits west of it."""
    S, z = 'pstaff1', P1; props, boxes = [], []
    # men's: showers (racks) + their partitions
    props += [W(S, 'prop_shower_rack_01', 'v', P.G_EA, 1, (a + b) / 2, 1.3) for a, b in zip((P.WI + 0.2,) + SHOWER1[:-1], SHOWER1)]
    boxes += [(S, (u - 0.025, P.G_EA + 0.1, z), (u + 0.025, P.G_EA + 1.1, z + 2.0), 'tile', True) for u in SHOWER1]
    props.append(centred(S, COUNTER, 'v', P.G_MEN, -1, 13.2, COUNTER_BOTTOM))              # u 10.75 .. 15.65 (the door: u 16.75 ..)
    p, b = stalls(S, 'u', P.STAIR_B[0], -1, face_of(S, 'v', P.G_EA, 1, 17.5), -32.9, 2, z, ends=(False, True)); props += p; boxes += b
    props += [W(S, DRYER, 'v', P.G_MEN, -1, 16.2, 1.05), W(S, BIN, 'u', P.WI, 1, -31.75)]   # the dryer between the counter and the door (the west wall: windows)
    props += [(S, 'hei_heist_stn_benchshort', 14.9, -33.6, 0.0, 90.0), (S, 'v_res_fh_towelstack', 14.9, -33.2, 0.45, 0.0)]
    # women's: the strip's two showers (racks + partitions), two stalls on the south wall of the locker room, the counter on its north wall
    props += [W(S, 'prop_shower_rack_01', 'v', P.G_LOCK, 1, (a + b) / 2, 1.3) for a, b in zip(SHOWER2, SHOWER2[1:])]
    boxes += [(S, (u - 0.025, P.G_LOCK + 0.1, z), (u + 0.025, P.G_LOCK + 1.1, z + 2.0), 'tile', True) for u in SHOWER2]
    p, b = stalls(S, 'v', P.G_LOCK, 1, 15.6, P.STAIR_B[0], 2, z); props += p; boxes += b
    props.append(centred(S, COUNTER, 'v', P.G_EA, -1, 13.8, COUNTER_BOTTOM))               # u 11.35 .. 16.25 (the lockers: the west wall)
    props += [W(S, DRYER, 'v', P.G_EA, -1, 16.75, 1.05), W(S, BIN, 'v', P.G_EA, -1, 17.5)]
    return props, boxes
def l1_public():
    """L1 (plobby): the two single-user public WCs off the hall (2.25 x 3.44 m, door on the north wall): the toilet on the back
    (south) wall, the wall basin on the side wall clear of the door's swing, a hand dryer, a bin."""
    R = 'plobby'; out = []
    for u0, u1, sk in ((17.5, 19.75, 1), (19.75, 22.0, -1)):                # sk: +1 the basin on the west wall, -1 the east wall
        wall = u0 if sk > 0 else u1
        out += [W(R, TOILET, 'v', P.HALL_S, 1, (u0 + u1) / 2), W(R, BASIN, 'u', wall, sk, -12.05, BASIN_BOTTOM),
                W(R, DRYER, 'u', wall, sk, -12.95, 1.05), W(R, BIN, 'u', wall, sk, -10.75)]
    return out
def props():
    a = l2_restrooms()[0] + l1_showers()[0]
    return [(r, m, u, v, z, h) for r, m, u, v, z, h in a] + l1_public()
def kit():
    return l2_restrooms()[1] + l1_showers()[1]
