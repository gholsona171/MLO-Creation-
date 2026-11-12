"""Phase 3 area 2 (Blender, called by jc3_build.py after the galleria): the tower lobby, the stair, the public and secure lifts and the
two courtroom floors, from jc3_tower. tc_kit (TK) draws; every room's walls are the LINING of its own floor region (a strip inside its
boundary: 0.1 m against another room, so two rooms make a 0.2 m partition back to back; 0.2 m on an outer wall; 0.3 in the lobby),
cut by its door openings and window bays (p2_plan.box_minus, exact), so partitions touch and never overlap."""
import math
import tc_kit as TK
import p2_plan as PL
import jc3_tower as JT
import jc5_court as C5
from p2_plan import box_minus
OPS = {'portals': [], 'doors': [], 'props': [], 'seats': [], 'lifts': [], 'signs': 0}
def _grid_lining(region, others, ext_t, int_t):
    """region: [(u0, u1, v0, v1)] of one room; others: [(rect, thickness)] of the rooms around it. The lining = every boundary stretch
    of the region extruded inward by the thickness of what lies beyond it (another room: its value; nothing: ext_t), as non-overlapping
    rects (a grid on every edge, merged along u)."""
    def inreg(x, y): return any(r[0] < x < r[1] and r[2] < y < r[3] for r in region)
    def beyond(x, y):
        for r, t in others:
            if r[0] <= x <= r[1] and r[2] <= y <= r[3]: return t
        return ext_t
    cut_x = sorted({c for r in region for c in (r[0], r[1])} | {c for r, _ in others for c in (r[0], r[1])})
    cut_y = sorted({c for r in region for c in (r[2], r[3])} | {c for r, _ in others for c in (r[2], r[3])})
    strips = []
    for r in region:
        for side in ('u0', 'u1', 'v0', 'v1'):
            if side[0] == 'u':
                x = r[0] if side == 'u0' else r[1]; o = -1 if side == 'u0' else 1
                ys = [y for y in cut_y if r[2] <= y <= r[3]]; ys = sorted(set(ys + [r[2], r[3]]))
                for y0, y1 in zip(ys, ys[1:]):
                    ym = (y0 + y1) / 2
                    if inreg(x + o * 1e-3, ym): continue
                    t = beyond(x + o * 1e-3, ym); strips.append((x - t, x, y0, y1) if o > 0 else (x, x + t, y0, y1))
            else:
                y = r[2] if side == 'v0' else r[3]; o = -1 if side == 'v0' else 1
                xs = [x for x in cut_x if r[0] <= x <= r[1]]; xs = sorted(set(xs + [r[0], r[1]]))
                for x0, x1 in zip(xs, xs[1:]):
                    xm = (x0 + x1) / 2
                    if inreg(xm, y + o * 1e-3): continue
                    t = beyond(xm, y + o * 1e-3); strips.append((x0, x1, y - t, y) if o > 0 else (x0, x1, y, y + t))
    gx = sorted({c for st in strips for c in (st[0], st[1])} | {c for r in region for c in (r[0], r[1])})
    gy = sorted({c for st in strips for c in (st[2], st[3])} | {c for r in region for c in (r[2], r[3])})
    cells = []
    for y0, y1 in zip(gy, gy[1:]):
        run = None
        for x0, x1 in zip(gx, gx[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            on = inreg(cx, cy) and any(st[0] < cx < st[1] and st[2] < cy < st[3] for st in strips)
            if on and run and abs(run[1] - x0) < 1e-9: run = (run[0], x1, y0, y1)
            elif on:
                if run: cells.append(run)
                run = (x0, x1, y0, y1)
            else:
                if run: cells.append(run)
                run = None
        if run: cells.append(run)
    return cells
def lining(room, region, others, z0, z1, mat, holes3d, ext_t=0.2, int_t=0.1, col=True):
    for u0, u1, v0, v1 in _grid_lining(region, others, ext_t, int_t):
        for c in box_minus((u0, u1, v0, v1, z0, z1), holes3d):
            TK.box(room, (c[0], c[2], c[4]), (c[1], c[3], c[5]), mat, col)
def slab(room, region, z0, z1, mat, col=True):
    for u0, u1, v0, v1 in region: TK.box(room, (u0, v0, z0), (u1, v1, z1), mat, col)
def opening_boxes(z_lo=None):
    """3D boxes of every door opening (through any partition, 0.4 m deep) + lift door openings."""
    out = []
    for o in JT.OPENINGS:
        if o['axis'] == 'u': out.append((o['plane'] - 0.4, o['plane'] + 0.4, o['a0'], o['a1'], o['z0'], o['z1']))
        else: out.append((o['a0'], o['a1'], o['plane'] - 0.4, o['plane'] + 0.4, o['z0'], o['z1']))
    return out
def bay_boxes(F):
    """the window bays of the floor at F as 3D boxes through the outer lining (0.2 m) + 1 cm either side."""
    out = []
    for fid, (ax, plane, o) in JT.FACE_LINE.items():
        lo, hi = sorted((plane, plane + o * JT.OL))
        for a0, a1, z0, z1 in JT.bays(fid, F):
            out.append((lo - 0.01, hi + 0.01, a0, a1, z0, z1) if ax == 'u' else (a0, a1, lo - 0.01, hi + 0.01, z0, z1))
    return out
def window_portals(room, F, region):
    """one limbo portal per face run of bays inside the room's region (on the lining's room face, the bays' height)."""
    out = []
    for fid, (ax, plane, o) in JT.FACE_LINE.items():
        bs = JT.bays(fid, F)
        for r in region:
            lo, hi = (r[2], r[3]) if ax == 'u' else (r[0], r[1])
            touch = (abs((r[1] if ax == 'u' and o > 0 else r[0] if ax == 'u' else r[3] if o > 0 else r[2]) - (plane + o * JT.OL)) < 0.02)
            if not touch: continue
            ins = [(max(a0, lo), min(a1, hi), z0, z1) for a0, a1, z0, z1 in bs if min(a1, hi) - max(a0, lo) > 0.05]
            if not ins: continue
            a0 = min(i[0] for i in ins); a1 = max(i[1] for i in ins)
            out.append({'from': room, 'to': 'limbo', 'kind': f'{room} {fid} windows', 'P': (ax, plane, a0, a1, ins[0][2], ins[0][3], o)})
    return out
def court_floor(f):
    """one courtroom floor (area 2's rooms and doors) in area 5's BrunX finish: walls + their shell (jc5_dress.walls), the courtroom's
    tray ceiling, pilasters, the bench backdrop with the court seal, flags, chandeliers, framed documents; mahogany fittings with marble caps."""
    F = JT.FLOORS[f]; crt, pub, rst, sec = f'crt{f}', f'pub{f}', f'rst{f}', f'sec{f}'
    IN = (JT.IU0, JT.IU1, JT.IV0, JT.IV1); CB = JT.CB; CO = JT.CORE
    R = {crt: [CB], sec: [(CB[1], CO[0], CB[2], CB[3])],
         rst: [(JT.IU0, CB[0], JT.W_RING_V, CB[3]), (JT.IU0, JT.RST_E, CB[3], JT.IV1)],
         'stair': [(CO[0], CO[1], JT.LIFT_BODY, CO[3])], 'lift': [(CO[0], CO[1], CO[2], JT.LIFT_BODY)]}
    taken = R[crt] + R[sec] + R[rst] + R['stair'] + R['lift']
    R[pub] = [(a, b, c, d) for a, b, c, d in TK.rects_minus(*IN, taken)]
    holes = opening_boxes() + D5.deep_bays(F)
    lift_holes = [(c - 0.65, c + 0.65, CO[2] - 0.4, CO[2] + 0.4, F, F + 2.6) for c in ((CO[0] + CO[1]) / 2 - 1.7, (CO[0] + CO[1]) / 2 + 1.7)]
    def others(me): return [(r, 0.1) for k, rs in R.items() if k != me for r in rs]
    top = {crt: F + JT.CEIL_T - 0.2, pub: F + JT.ROOM_H, rst: F + JT.ROOM_H, sec: F + JT.ROOM_H}
    # floors: the courtroom carpeted, the well (bar .. dais) in floorboards; public marble, restricted carpet, secure vinyl
    well = (CB[0], CB[1], C5.CT['well_v'][0], C5.CT['well_v'][1])                    # (within the courtroom's own slab)
    slab(crt, TK.rects_minus(*CB, [well]), F - 0.4, F, 'bx_carpet'); slab(crt, [well], F - 0.4, F, 'bx_plank')
    slab(pub, R[pub], F - 0.4, F, 'bx_carrara'); slab(rst, R[rst], F - 0.4, F, 'bx_carpet'); slab(sec, R[sec], F - 0.4, F, 'speckle')
    # ceilings
    D5.tray_ceiling(crt, CB, top[crt], C5.CT['tray'], C5.CT['tray_drop'], walls=(JT.CW,) * 4)
    slab(pub, R[pub], top[pub], top[pub] + 0.2, 'bx_offceil', col=False); slab(rst, R[rst], top[rst], top[rst] + 0.2, 'bx_offceil', col=False)
    slab(sec, R[sec], top[sec], top[sec] + 0.2, 'ceiltile', col=False)
    # walls
    D5.walls(crt, R[crt], [], F, top[crt] - C5.CT['tray_drop'], holes, C5.WAINSCOT['crt'], upper='plaster', cap='bx_nero', ext_t=JT.CW)
    lining(crt, R[crt], [], top[crt] - C5.CT['tray_drop'], top[crt], 'plaster', holes, ext_t=JT.CW, int_t=JT.CW)        # over the cornice: plain to the slab
    D5.walls(pub, R[pub], others(pub), F, top[pub], holes + lift_holes, C5.WAINSCOT['office'], upper='bx_wallmarble', cap='bx_mahog', ext_t=JT.OL)
    D5.walls(rst, R[rst], others(rst), F, top[rst], holes, C5.WAINSCOT['office'], upper='plaster', cap='bx_mahog', ext_t=JT.OL)
    lining(sec, R[sec], others(sec), F, top[sec], 'block', holes, ext_t=JT.OL, int_t=0.1)
    for room in (crt, pub, rst, sec): OPS['portals'] += window_portals(room, F, R[room])
    for room in (pub, rst, sec): lights_grid(room, R[room], top[room], 3.2)
    # the interior partitions inside rst and pub (one room each: walls with doors, no portal): mahogany wainscot band, plaster above
    inner = [(rst, 'v', JT.CORR_N, JT.IU0 + JT.OL, JT.RST_E - 0.1), (rst, 'u', JT.JURY_E, JT.CORR_N, JT.IV1 - JT.OL),
             (rst, 'u', JT.CHAMB_E, JT.CORR_N, JT.IV1 - JT.OL), (rst, 'v', JT.WIT_N, JT.IU0 + JT.OL, JT.CB[0] - 0.1),
             (pub, 'v', JT.CONF_S, JT.RST_E + 0.1, JT.IU1 - JT.OL)]
    for room, ax, at, a0, a1 in inner: D5.partition(room, ax, at, a0, a1, F, F + JT.ROOM_H, holes, 'plaster' if room == rst else 'bx_wallmarble')
    # the courtroom: pilasters + sconces on the side walls, the bench backdrop, the seal, flags, chandeliers, documents, the clock
    ct = C5.CT; ztop = top[crt] - C5.CT['tray_drop'] - C5.CORNICE[0]
    for v in ct['pil_v']:
        for plane, s in ((JT.CU0, 1), (JT.CU1, -1)):
            if any(o['axis'] == 'u' and abs(o['plane'] - (JT.CB[1] if s < 0 else JT.CB[0])) < 0.4 and o['a0'] - 0.4 < v < o['a1'] + 0.4 for o in JT.OPENINGS): continue
            D5.pilaster(crt, 'u', plane, v, s, F, ztop, ct['pilaster_w'], ct['pilaster_p']); D5.sconce(crt, 'u', plane + s * ct['pilaster_p'], v, s, F + 3.1)
    backdrop(crt, F)
    for m, u, v in ct['flags']: OPS['props'].append((crt, m, u, v, F, 0.0 if u < 25 else 180.0))
    for u, v in ct['chandeliers']: D5.chandelier(crt, u, v, top[crt], 1.15)
    for key, lines, wall, v in ct['documents']:                                              # framed historic documents (our own art)
        D5.placard(crt, key, list(lines), (JT.CU0 if wall == 'u0' else JT.CU1, v, F + 2.75), '+u' if wall == 'u0' else '-u', 0.75, 1.5)
    m, u, z = ct['clock']; OPS['props'].append((crt, m, u, JT.CV1 - 0.025, F + z, 0.0))
    for vv in (25.0, 37.0):                                                                     # air grilles high on the side walls
        for plane, s in ((JT.CU0, 1), (JT.CU1, -1)):
            TK.box(crt, (min(plane, plane + s * 0.02), vv - 0.6, F + 4.7), (max(plane, plane + s * 0.02), vv + 0.6, F + 5.0), 'bx_vent', col=False)
    # fittings
    fit = JT.court_fittings(f)
    for u0, u1, v0, v1, z0, z1, mat, col in fit['boxes']: TK.box(crt, (u0, v0, F + z0), (u1, v1, F + z1), mat, col)
    for u0, u1, v0, v1, z0, z1 in fit['cols']: TK.colbox(crt, (u0, v0, F + z0), (u1, v1, F + z1))
    st = TK.stair(crt, 'u', 28.57, -1, F, F + JT.DAIS, (38.6, 39.9), 'bx_plank', None)        # the dais steps (east)
    for m, u, v, z, h in fit['props']: OPS['props'].append((crt, m, u, v, F + z, h))
    for u, v, z, h, what in fit['seats']: OPS['seats'].append((u, v, F + z, h, what, crt, 'PROP_HUMAN_SEAT_BENCH'))
    sf = JT.sec_fittings(f)
    for u0, u1, v0, v1, z0, z1, mat, col in sf['boxes']: TK.box(sec, (u0, v0, F + z0), (u1, v1, F + z1), mat, col)
    for m, u, v, z, h in sf['props']: OPS['props'].append((sec, m, u, v, F + z, h))
    for u, v, z, h, what in sf['seats']: OPS['seats'].append((u, v, F + z, h, what, sec, 'PROP_HUMAN_SEAT_BENCH'))
    # cell partitions (block) between corridor and cells, and between cells
    ce = JT.CELL_V0[-1] + JT.CELL_D                                     # the cell block's north end (its last partition's far face)
    for c in box_minus((32.6, 32.75, JT.CELL_S, ce, F, F + JT.ROOM_H), holes): TK.box(sec, (c[0], c[2], c[4]), (c[1], c[3], c[5]), 'block')
    for v0 in JT.CELL_V0: TK.box(sec, (32.75, v0 + JT.CELL_D - 0.15, F), (JT.CORE[0] - 0.1, v0 + JT.CELL_D, F + JT.ROOM_H), 'block')
    TK.box(sec, (32.75, JT.CELL_S, F), (JT.CORE[0] - 0.1, JT.CELL_S + 0.15, F + JT.ROOM_H), 'block')     # the landing / cell 1 wall
    chambers(f, F)
    # placards (the BrunX style): the courtroom door, the lift lobby, the chambers door
    n = f'{"3" if f == "A" else "5"}{f}'
    D5.placard(pub, f'court{f}', C5.COURT_PLACARD[f], (29.45, JT.CB[2] - 0.1, F + 2.62), '-v', 1.5, 0.42)
    D5.placard(pub, f'lvl{f}', [f'LEVEL {n[0]}', f'COURTROOM {n}'], (JT.CORE[0] + 3.8, JT.CORE[2] - 0.1, F + 2.45), '-v', 1.6, 0.50)
    D5.placard(rst, f'chambers{f}', list(C5.CHAMBERS[f]), (26.9, JT.CORR_N - 0.1, F + 1.75), '-v', 0.9, 0.42)
    return R
def backdrop(crt, F):
    """the tall arch-topped mahogany panel behind the bench (north wall), 8 cm proud, with the court seal at its centre."""
    u0, u1, zt = C5.CT['backdrop']; zb = F + JT.DAIS; w = u1 - u0; r = w / 2; cu = (u0 + u1) / 2; zs = zb + zt - r
    face = JT.CV1; d = 0.08; n = 24
    prof = [(u0, zb), (u1, zb)] + [(cu + r * math.cos(math.pi * k / n), zs + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
    V = [(u, face - d, z) for u, z in prof] + [(u, face, z) for u, z in prof]; m = len(prof)
    front = tuple(range(m)); back = tuple(range(m, 2 * m))[::-1]
    sides = [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
    TK.mesh(crt, V, [front, back] + [s_[::-1] for s_ in sides], 'bx_mahog', col=True, name='backdrop')   # front CCW seen from -v (faces the room)
    TK.box(crt, (u0 - 0.12, face - d - 0.03, zb), (u1 + 0.12, face, zb + 0.10), 'bx_mahog')        # its plinth moulding
    D5.SH.keep_clear(crt, (u0, face - d, zb), (u1, face, zb + zt))                                   # the shell stops on its sides
    OPS['props'].append((crt, 'jc_courts_seal_court', cu, face - d, F + C5.CT['seal_z'], 0.0, C5.CT['seal_size']))
def chambers(f, F):
    """the judge's chambers in rst: mahogany bookcases on both side walls round the seal and flags (the BrunX office)."""
    rst = f'rst{f}'; west = JT.JURY_E + 0.1; east = JT.CHAMB_E - 0.1; v0, v1 = JT.CORR_N + 0.1, JT.IV1 - JT.OL
    D5.bookcase(rst, 'u', west, v0 + 1.3, 47.9, 1, F); D5.bookcase(rst, 'u', west, 50.1, v1 - 0.3, 1, F)
    D5.bookcase(rst, 'u', east, v0 + 1.3, v1 - 1.3, -1, F)
    OPS['props'].append((rst, 'jc_courts_seal_court', west + 0.002, 49.0, F + 1.5, 90.0, 0.9))       # on the wall over the wainscot
    OPS['props'] += [(rst, 'jc_courts_flag_us', west + 0.45, 48.3, F, 270.0), (rst, 'jc_courts_flag_ohio', west + 0.45, 49.7, F, 90.0)]
def lights_grid(room, region, z, pitch):
    for u0, u1, v0, v1 in region:
        nu = max(1, int((u1 - u0) // pitch)); nv = max(1, int((v1 - v0) // pitch))
        if (u1 - u0) < 1.4 or (v1 - v0) < 1.4: continue
        for i in range(nu):
            for j in range(nv):
                TK.lamp(room, u0 + (u1 - u0) * (i + 0.5) / nu, v0 + (v1 - v0) * (j + 0.5) / nv, z, energy=0.7, falloff=8.0, size=(1.2, 0.3))
def glass_runs(room, region, curtained, ztop=None):
    """the colonnade glass (lobby_runs) along this room's outer edges: holes cut through its lining; a window portal per stretch, or
    (curtained rooms) also heavy pleated curtains filling the stretch on the room side of the glass, so it reads as curtains from both sides;
    they hang from the room's ceiling (ztop) when it is lower than the glass."""
    holes = []
    for fid, a0, a1, z0, z1 in JT.lobby_runs():
        for r in region:
            if fid == 'N' and abs(r[3] - JT.LB[3]) < 1e-6: lo, hi, ax, plane, into, at = r[0], r[1], 'v', JT.LV1, 1, JT.LB[3]
            elif fid == 'S' and abs(r[2] - JT.LB[2]) < 1e-6: lo, hi, ax, plane, into, at = r[0], r[1], 'v', JT.LV0, -1, JT.LB[2]
            elif fid == 'E' and abs(r[1] - JT.LB[1]) < 1e-6: lo, hi, ax, plane, into, at = r[2], r[3], 'u', JT.LU1, 1, JT.LB[1]
            else: continue
            b0, b1 = max(a0, lo + 0.31), min(a1, hi - 0.31)
            if b1 - b0 < 0.2: continue
            dz = (at - 0.6, at + 0.1) if into > 0 else (at - 0.1, at + 0.6)
            holes.append((dz[0], dz[1], b0, b1, z0, z1) if ax == 'u' else (b0, b1, dz[0], dz[1], z0, z1))
            # every stretch is a window portal to limbo, curtained or not: a room with no way out to limbo (the auditorium had only its
            # lobby door) drew nothing of the building once the game's room tracking slipped in it (rig 2026-11-11, Antonio)
            OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': f'{room} {fid} glass', 'P': (ax, plane, b0, b1, z0, z1, into)})
            if room not in curtained: continue
            c0 = at - into * 0.30; n = int((b1 - b0) // 0.14); z1 = min(z1, ztop) if ztop else z1                                       # pleats: 14 cm, alternately 6 / 14 cm deep
            for i in range(n):
                p0 = b0 + (b1 - b0) * i / n; p1 = b0 + (b1 - b0) * (i + 1) / n; dd = 0.06 if i % 2 else 0.14
                lo_n, hi_n = sorted((c0, c0 - into * dd))
                if ax == 'u': TK.box(room, (lo_n, p0, z0), (hi_n, p1, z1), 'bx_curtain', col=False)
                else: TK.box(room, (p0, lo_n, z0), (p1, hi_n, z1), 'bx_curtain', col=False)
            lo_n, hi_n = sorted((c0, c0 - into * 0.14))
            TK.colbox(room, (lo_n, b0, z0) if ax == 'u' else (b0, lo_n, z0), (hi_n, b1, z1) if ax == 'u' else (b1, hi_n, z1))
    return holes
def lobby():
    """the grand lobby (area 5, BrunX look): chevron + white marble floor, banded walls (mahogany wainscot, cream marble, cornice),
    coffered ceiling, chandeliers, the statues, flags, the court seal, the Clerk of Courts front desk, benches, the treasury board."""
    room = 'tlobby'; CO = JT.CORE; SL = JT.SLIFT; F = JT.F1
    region = [(JT.LB[0], JT.LB[1], JT.LB[2], C5.GW), (PL.TOWER_VEST[0], PL.TOWER_VEST[1], 17.3, JT.LB[2])]
    taken = [(CO[0], CO[1], CO[2], CO[3]), SL]
    reg = []
    for r in region: reg += TK.rects_minus(*r, taken)
    wing = [(r, 0.1) for k, rs in C5.WING.items() for r in rs]
    oth = [((CO[0], CO[1], JT.LIFT_BODY, CO[3]), 0.1), ((CO[0], CO[1], CO[2], JT.LIFT_BODY), 0.1), (SL, 0.1), ((13.0, 38.0, 16.0, 17.3), 0.15)] + wing
    holes = opening_boxes() + glass_runs(room, reg, ())
    lift_holes = [(c - 0.65, c + 0.65, CO[2] - 0.4, CO[2] + 0.4, F, F + 2.6) for c in ((CO[0] + CO[1]) / 2 - 1.7, (CO[0] + CO[1]) / 2 + 1.7)]
    fl = C5.FIELD
    for r in reg:
        for a, b, c, d in TK.rects_minus(*r, [fl]): TK.box(room, (a, c, F - 0.4), (b, d, F), 'bx_carrara')
        a, b, c, d = max(r[0], fl[0]), min(r[1], fl[1]), max(r[2], fl[2]), min(r[3], fl[3])
        if b - a > 0.01 and d - c > 0.01: TK.box(room, (a, c, F - 0.4), (b, d, F), 'bx_chevron')
    top = JT.LOB_CEIL - 0.2
    slab(room, reg, top, JT.LOB_CEIL, 'bx_coffer', col=False)
    band_hole = [(CO[0] - 0.25, CO[1] + 0.25, CO[2] - 0.25, CO[3] + 0.25, JT.CORE_BAND[0], JT.CORE_BAND[1])]   # the core's lining leaves the band's course
    D5.walls(room, reg, oth, F, top, holes + lift_holes + band_hole, C5.WAINSCOT['tlobby'], upper='bx_wallmarble', cap='bx_mahog', ext_t=JT.LL)
    core_band(room)
    # pilasters: the west wall and the wing wall's lobby face, clear of the doors, the seal and the board
    for v in (23.4, 26.8, 37.8, 40.2): D5.pilaster(room, 'u', JT.LU0, v, 1, F, top - C5.CORNICE[0], 0.55, 0.10, zin=(2.6, 5.2))
    for u in (17.6, 25.6, 34.8, 44.6): D5.pilaster(room, 'v', C5.GW - 0.1, u, -1, F, top - C5.CORNICE[0], 0.55, 0.10, zin=(2.6, 5.2))
    for u, v in C5.CHANDELIERS_LOBBY: D5.chandelier(room, u, v, top, 1.35)
    lights_grid(room, reg, top, 7.0)
    # the Clerk of Courts front desk: panelled mahogany, black marble top, the staff work surface behind it; its rope queue
    u0, u1, v0, v1, hh = C5.FRONT_DESK
    TK.box(room, (u0, v0, F), (u1, v1, F + hh - 0.05), 'bx_mahog'); TK.box(room, (u0 - 0.06, v0 - 0.06, F + hh - 0.05), (u1 + 0.06, v1 + 0.02, F + hh), 'bx_nero')
    TK.box(room, (u0 + 0.1, v1, F + 0.72), (u1 - 0.1, v1 + 0.55, F + 0.76), 'bx_nero')
    for u in (u0 + 0.15, u1 - 0.15): TK.box(room, (u - 0.05, v1, F), (u + 0.05, v1 + 0.55, F + 0.72), 'bx_mahog')
    for k, u in enumerate((u0 + 1.6, (u0 + u1) / 2, u1 - 1.6)):
        OPS['props'] += [(room, 'prop_off_chair_05', u, v1 + 1.05, F, 0.0), (room, 'prop_monitor_01a', u, v1 + 0.35, F + 0.76, 180.0),
                         (room, 'prop_keyboard_01a', u, v1 + 0.15, F + 0.76, 180.0)]
    OPS['props'] += [(room, 'v_ret_gc_phone', u0 + 0.6, v1 + 0.3, F + 0.76, 180.0), (room, 'ex_mp_h_acc_vase_flowers_02', u1 - 0.5, (v0 + v1) / 2, F + hh, 0.0)]
    for u, v, h, n in C5.QUEUE:
        for i in range(n + 1): OPS['props'].append((room, 'v_corp_bk_rope', u + 1.72 * i, v, F, h if i < n else (h + 180.0) % 360.0))
    for u, v, h in C5.STATUES: OPS['props'].append((room, 'jc_courts_statue_justice', u, v, F, h))
    for m, u, v, h in C5.LOBBY_FLAGS: OPS['props'].append((room, m, u, v, F, h))
    m, plane, v, z, sz = C5.LOBBY_SEAL; OPS['props'].append((room, m, plane + 0.001, v, z, 90.0, sz))
    for u, v, h in C5.BENCHES: OPS['props'].append((room, 'v_res_fh_benchlong', u, v, F, h))
    jury_assembly(room)
    # the treasury board (Government Offices, public summary): a framed board on the wing wall's lobby face, its header placard
    cu, w, h, zc = C5.TREASURY; face = C5.GW - 0.1
    D5.placard(room, 'board', ['TREASURY BOARD'], (cu, face, F + zc), '-v', w, h - 0.5)
    D5.placard(room, 'treasury', ['TREASURY BOARD', 'AND APPOINTMENTS'], (cu, face, F + zc + h / 2 + 0.05), '-v', 2.4, 0.42)
    for key, lines, u, v, z, face_ in C5.PLACARDS_LOBBY: D5.placard(room, key, lines, (u, v, z), face_, 1.7 if len(lines) == 2 else 1.6, 0.46 if len(lines) == 2 else 0.40)
    OPS['props'] += [(room, 'apa_mp_h_acc_plant_palm_01', u, v, F, 0.0) for u, v in ((JT.LU0 + 1.0, C5.GW - 1.1), (JT.LU1 - 1.0, JT.LV0 + 1.2), (36.6, 21.9))]
    OPS['props'] += [(room, 'prop_watercooler', JT.LU0 + 0.3, 21.6, F, 90.0), (room, 'prop_bin_11b', JT.LU0 + 0.35, 22.4, F, 0.0), (room, 'prop_bin_11b', 43.6, 36.2, F, 0.0)]
    directory(room)
    return reg
def gov_wing():
    """the Government Offices' public side in the lobby's north band: the auditorium (elections, ballot booth), the reception (tax
    desk) and the Security room (locker). Returns their regions."""
    F = JT.F1; out = {}
    lob = [(JT.LB[0], JT.LB[1], JT.LB[2], C5.GW)]
    for room, reg in C5.WING.items():
        oth = [(r, 0.1) for k, rs in C5.WING.items() if k != room for r in rs] + [(r, 0.1) for r in lob]
        top = C5.WING_TOP[room]; full = JT.LOB_CEIL - 0.2
        holes = opening_boxes() + glass_runs(room, reg, C5.CURTAINED, top)
        slab(room, reg, F - 0.4, F, {'gaud': 'bx_greycarpet', 'grec': 'bx_carrara', 'gsec': 'bx_greycarpet'}[room])
        D5.walls(room, reg, oth, F, full, holes, C5.WAINSCOT[room], upper='bx_wallmarble' if room != 'gsec' else 'plaster', cap='bx_mahog', ext_t=JT.LL)
        slab(room, reg, full, full + 0.2, 'bx_coffer' if room != 'gsec' else 'plaster', col=False)
        if top < full - 0.01:                                                              # Security: its own low ceiling under the closed top,
            r = reg[0]; slab(room, [(r[0] + 0.1, r[1] - JT.LL, r[2] + 0.1, r[3] - JT.LL)], top, top + 0.2, 'bx_offceil')   # inside its walls (solid: its top is a floor to the checks)
        lights_grid(room, reg, top, 3.4 if room == 'gsec' else 5.0)
        out[room] = reg
    # the auditorium: stage, its backdrop with the city seal and flags, lectern, rows of armchairs, the ballot booth by the door
    u0, u1, v0, v1, hs = C5.STAGE
    TK.box('gaud', (u0, v0, F), (u1, v1, F + hs - 0.03), 'bx_mahog'); TK.box('gaud', (u0, v0, F + hs - 0.03), (u1, v1, F + hs), 'bx_plank')
    cu = (u0 + u1) / 2
    TK.box('gaud', (cu - 1.2, v0 - 0.30, F), (cu + 1.2, v0, F + 0.20), 'bx_plank')                                    # the step up (two 0.20 risers)
    bd = JT.LB[3] - 0.3 - 0.40                                                                                         # backdrop panel, clear in front of the pleats
    TK.box('gaud', (cu - 2.0, bd, F + hs), (cu + 2.0, bd + 0.14, F + hs + 4.6), 'bx_mahog')
    m, u, v, z, sz = C5.AUD_SEAL; OPS['props'].append(('gaud', m, u, bd, F + hs + 2.2, 0.0, sz))
    for m, u, v, h in C5.AUD_FLAGS: OPS['props'].append(('gaud', m, u, v, F + hs, h))
    lu, lv = C5.LECTERN; TK.box('gaud', (lu - 0.32, lv - 0.25, F + hs), (lu + 0.32, lv + 0.25, F + hs + 1.12), 'bx_mahog'); TK.box('gaud', (lu - 0.36, lv - 0.30, F + hs + 1.12), (lu + 0.36, lv + 0.29, F + hs + 1.16), 'bx_nero')
    for u, v in C5.AUD_ROWS: OPS['props'].append(('gaud', 'v_res_m_armchair', u, v, F, 180.0))
    u, v, h = C5.BOOTH; OPS['props'].append(('gaud', 'jc_courts_ballot_booth', u, v, F, h))
    D5.placard('gaud', 'ballot', ['BALLOT BOOTH'], (u, C5.GW + 0.1, F + 1.95), '+v', 1.1, 0.34)
    for u, v in ((16.0, 47.0), (27.4, 47.0), (16.0, 44.0), (27.4, 44.0)): D5.chandelier('gaud', u, v, C5.WING_TOP['gaud'], 1.2)
    # the reception: the tax desk counter, the clerk's station behind it, waiting chairs, the city seal and flags on the west wall
    u0, u1, v0, v1, hh = C5.TAX_DESK
    TK.box('grec', (u0, v0, F), (u1, v1, F + hh - 0.05), 'bx_mahog'); TK.box('grec', (u0 - 0.06, v0 - 0.06, F + hh - 0.05), (u1 + 0.06, v1 + 0.02, F + hh), 'bx_nero')
    TK.box('grec', (u0 + 0.1, v1, F + 0.72), (u1 - 0.1, v1 + 0.55, F + 0.76), 'bx_nero')
    for u in (u0 + 0.15, u1 - 0.15): TK.box('grec', (u - 0.05, v1, F), (u + 0.05, v1 + 0.55, F + 0.72), 'bx_mahog')
    OPS['props'] += [('grec', 'prop_monitor_01a', u0 + 1.4, v1 + 0.35, F + 0.76, 180.0), ('grec', 'prop_keyboard_01a', u0 + 1.4, v1 + 0.15, F + 0.76, 180.0),
                     ('grec', 'prop_off_chair_05', u1 - 1.2, v1 + 1.15, F, 0.0), ('grec', 'v_ret_gc_phone', u1 - 0.5, v1 + 0.3, F + 0.76, 180.0),
                     ('grec', 'p_amb_clipboard_01', (u0 + u1) / 2, (v0 + v1) / 2, F + hh, 10.0)]
    D5.placard('grec', 'taxdesk', ['TAX DESK'], ((u0 + u1) / 2, v0 - 0.061, F + 0.62), '-v', 1.3, 0.36)
    for u, v, h in C5.REC_CHAIRS: OPS['props'].append(('grec', 'v_res_m_armchair', u, v, F, h))
    OPS['props'] += [('grec', 'jc_courts_seal_city', C5.GW_U + 0.101, 48.5, F + 3.0, 90.0, 1.3), ('grec', 'jc_courts_flag_us', C5.GW_U + 0.6, 47.3, F, 90.0),
                     ('grec', 'jc_courts_flag_cle', C5.GW_U + 0.6, 49.7, F, 90.0), ('grec', 'apa_mp_h_acc_plant_palm_01', 46.6, 46.3, F, 0.0)]
    D5.placard('grec', 'security', ['SECURITY'], (C5.SEC[0] + 3.4, C5.SEC[2] - 0.1, F + 2.6), '-v', 1.2, 0.36)
    D5.placard('grec', 'govoff', ['GOVERNMENT OFFICES'], (38.7, C5.GW + 0.1, F + 2.95), '+v', 2.2, 0.40)
    # Security: the locker, a desk with a monitor and a chair
    m, u, v, h = C5.LOCKER; OPS['props'].append(('gsec', m, u, v, F, h))
    a, b, c, d = C5.SEC_DESK; TK.box('gsec', (a, c, F + 0.72), (b, d, F + 0.76), 'bx_nero')
    for x in (a + 0.06, b - 0.06):
        for y in (c + 0.06, d - 0.06): TK.box('gsec', (x - 0.03, y - 0.03, F), (x + 0.03, y + 0.03, F + 0.72), 'bx_mahog', False)
    OPS['props'] += [('gsec', 'prop_monitor_01a', (a + b) / 2, d - 0.2, F + 0.76, 0.0), ('gsec', 'prop_off_chair_05', (a + b) / 2, c - 0.55, F, 180.0),
                     ('gsec', 'prop_cs_walkie_talkie', a + 0.3, c + 0.3, F + 0.76, 0.0)]
    return out
def office_floor(k):
    """the Mayor's (L13) / the Governor's (L25) suite: reception at the lifts (east), the office (west), the BrunX office look. Each office
    has its own layout (mayor_office / governor_office); the Governor's is the corner office over the whole south side."""
    F = C5.office_F(k); room = k; title, seal, flag, short = C5.OFFICE_TITLE[k]; top = F + C5.OFF_H; OFF = C5.OFFS[k]
    reg = [OFF]; oth = [(C5.LIFT_BOX, 0.1)]; CO = JT.CORE
    holes = opening_boxes() + D5.deep_bays(F)
    lift_holes = [(c - 0.65, c + 0.65, CO[2] - 0.4, CO[2] + 0.4, F, F + 2.6) for c in ((CO[0] + CO[1]) / 2 - 1.7, (CO[0] + CO[1]) / 2 + 1.7)]
    slab(room, reg, F - 0.4, F, 'bx_carpet')
    office = (OFF[0], C5.OFF_SPLIT, OFF[2], OFF[3]); rec = (C5.OFF_SPLIT, OFF[1], OFF[2], OFF[3])
    D5.tray_ceiling(room, office, top, 1.2, 0.30, walls=(JT.OL, 0.1, JT.OL, JT.OL))
    slab(room, [rec], top, top + 0.2, 'bx_coffer', col=False)
    D5.walls(room, reg, oth, F, top - 0.30, holes + lift_holes, C5.WAINSCOT['office'], upper='bx_wallmarble', cap='bx_mahog', ext_t=JT.OL)
    lining(room, reg, oth, top - 0.30, top, 'plaster', holes + lift_holes, ext_t=JT.OL, int_t=0.1)
    D5.partition(room, 'u', C5.OFF_SPLIT, OFF[2] + JT.OL, OFF[3] - JT.OL, F, top, holes, 'bx_wallmarble')
    OPS['portals'] += window_portals(room, F, reg)
    lights_grid(room, [rec], top, 3.4)
    (governor_office if k == 'govnr' else mayor_office)(room, F, top, OFF[0] + JT.OL, OFF[3] - JT.OL, seal, flag)
    # the reception: the secretary's desk, sofas, the flags and seal on the partition, the office placard by its door
    v0 = OFF[2] + JT.OL
    OPS['props'] += [(room, 'v_corp_officedesk', 45.6, 22.4, F, 270.0), (room, 'prop_off_chair_05', 46.7, 22.4, F, 270.0),
                     (room, 'prop_monitor_01a', 45.8, 22.4, F + 0.76, 90.0), (room, 'v_ret_gc_phone', 45.6, 21.7, F + 0.76, 90.0),
                     (room, 'v_club_officesofa', 37.0, v0 + 0.55, F, 180.0), (room, 'v_club_officesofa', 37.0, v0 + 3.6, F, 0.0),
                     (room, 'v_res_fh_coftableb', 37.0, v0 + 2.1, F, 0.0), (room, 'apa_mp_h_acc_plant_palm_01', 48.9, 19.0, F, 0.0)]
    ps = C5.OFF_SPLIT + 0.1
    OPS['props'] += [(room, 'jc_courts_seal_' + seal, ps + 0.001, 27.0, F + 1.45, 90.0, 0.9), (room, 'jc_courts_flag_us', ps + 0.5, 26.0, F, 270.0),
                     (room, 'jc_courts_flag_' + flag, ps + 0.5, 28.0, F, 90.0)]
    D5.placard(room, k + '_title', [title], (ps, 20.7, F + 1.75), '+u', 1.7, 0.42)
    return {k: reg}
def _desk(room, u, v, F):
    """the executive desk at (u, v) facing south (the visitors), its chair behind it, a lamp and papers, two visitors' armchairs."""
    OPS['props'] += [(room, 'v_corp_officedesk', u, v, F, 0.0), (room, 'ex_prop_offchair_exec_01', u, v + 1.05, F, 0.0),
                     (room, 'v_corp_cd_desklamp', u - 0.6, v - 0.1, F + 0.76, 0.0), (room, 'prop_cd_folder_pile2', u + 0.5, v - 0.05, F + 0.76, 0.0),
                     (room, 'v_res_m_armchair', u - 0.7, v - 1.4, F, 180.0), (room, 'v_res_m_armchair', u + 0.7, v - 1.4, F, 180.0)]
def mayor_office(room, F, top, west, north, seal, flag):
    """the Mayor's office (7 m): the city seal on the north wall between the US and Cleveland flags, bookcases either side, the desk
    before it facing the door side; a sofa group on the west wall; one chandelier."""
    cu, cv = C5.OFFICE_DESK['mayor']
    OPS['props'].append((room, 'jc_courts_seal_' + seal, cu, north - 0.002, F + 1.75, 0.0, 1.1))
    OPS['props'] += [(room, 'jc_courts_flag_us', cu - 0.9, north - 0.45, F, 180.0), (room, 'jc_courts_flag_' + flag, cu + 0.9, north - 0.45, F, 0.0)]
    D5.bookcase(room, 'v', north, west + 0.25, cu - 1.9, -1, F, h=2.3); D5.bookcase(room, 'v', north, cu + 1.9, C5.OFF_SPLIT - 0.35, -1, F, h=2.3)
    _desk(room, cu, cv, F)
    OPS['props'] += [(room, 'v_res_m_h_sofa', west + 0.55, 21.2, F, 90.0), (room, 'v_res_fh_coftableb', west + 1.95, 21.2, F, 90.0),
                     (room, 'v_res_m_armchair', west + 3.35, 21.2, F, 270.0), (room, 'apa_mp_h_acc_plant_palm_01', west + 0.65, 18.75, F, 0.0)]
    D5.chandelier(room, cu, 23.4, top, 1.0)
def governor_office(room, F, top, west, north, seal, flag):
    """the Governor's office, the grandest room: the corner office over the whole south side (18 m, windows south and west). The state
    seal on the north wall in a set of four flags (US, Ohio each side), long bookcases, the desk before them; a conference table for
    ten by the west windows; a sofa group by the door; two chandeliers."""
    cu, cv = C5.OFFICE_DESK['govnr']
    OPS['props'].append((room, 'jc_courts_seal_' + seal, cu, north - 0.002, F + 1.75, 0.0, 1.4))
    fv = north - 0.45
    OPS['props'] += [(room, 'jc_courts_flag_' + flag, cu - 2.6, fv, F, 180.0), (room, 'jc_courts_flag_us', cu - 1.4, fv, F, 180.0),
                     (room, 'jc_courts_flag_' + flag, cu + 1.4, fv, F, 0.0), (room, 'jc_courts_flag_us', cu + 2.6, fv, F, 0.0)]
    D5.bookcase(room, 'v', north, west + 0.25, cu - 3.7, -1, F, h=2.3); D5.bookcase(room, 'v', north, cu + 3.8, cu + 7.5, -1, F, h=2.3)
    _desk(room, cu, cv, F)
    # the conference table (mahogany pedestal, black marble top) for ten by the west windows
    t0, t1, w0, w1 = west + 1.25, west + 6.05, 20.3, 21.7
    TK.box(room, (t0 + 0.4, w0 + 0.4, F), (t1 - 0.4, w1 - 0.4, F + 0.72), 'bx_mahog'); TK.box(room, (t0, w0, F + 0.72), (t1, w1, F + 0.77), 'bx_nero')
    for i in range(4):
        u = t0 + 0.6 + i * 1.2
        OPS['props'] += [(room, 'v_corp_bk_chair1', u, w0 - 0.55, F, 180.0), (room, 'v_corp_bk_chair1', u, w1 + 0.55, F, 0.0)]
    OPS['props'] += [(room, 'v_corp_bk_chair1', t0 - 0.55, (w0 + w1) / 2, F, 90.0), (room, 'v_corp_bk_chair1', t1 + 0.55, (w0 + w1) / 2, F, 270.0),
                     (room, 'prop_cd_folder_pile2', t0 + 1.2, (w0 + w1) / 2, F + 0.77, 0.0), (room, 'prop_cd_folder_pile2', t1 - 1.2, (w0 + w1) / 2, F + 0.77, 90.0)]
    # the sofa group by the door (clear of its swing), plants in the corners
    e = C5.OFF_SPLIT - 0.1
    OPS['props'] += [(room, 'v_res_m_h_sofa', e - 0.65, 20.4, F, 270.0), (room, 'v_res_fh_coftableb', e - 2.05, 20.4, F, 90.0),
                     (room, 'v_res_m_armchair', e - 3.45, 19.7, F, 90.0), (room, 'v_res_m_armchair', e - 3.45, 21.1, F, 90.0),
                     (room, 'apa_mp_h_acc_plant_palm_01', west + 0.65, 18.65, F, 0.0), (room, 'apa_mp_h_acc_plant_palm_01', e - 0.75, north - 0.75, F, 0.0)]
    D5.chandelier(room, (t0 + t1) / 2, (w0 + w1) / 2, top, 1.1); D5.chandelier(room, cu + 4.5, 23.4, top, 1.1)
def jury_assembly(room):
    """the Jury Assembly sign hung from the ceiling over the east benches: a 4 cm walnut panel, the sign on both faces, two brass rods."""
    u, v, zc, w, h = JT.JURY_ASSEMBLY; z = JT.F1 + zc; top = JT.LOB_CEIL - 0.2
    TK.box(room, (u - 0.02, v - w / 2, z - h / 2), (u + 0.02, v + w / 2, z + h / 2), 'bx_mahog', col=False)
    for face, du in (('-u', 0.015), ('+u', -0.015)):                     # TK.sign stands 5 cm off its centre: 0.035 off the axis = 1.5 cm proud of the 2 cm half-panel
        TK.sign(room, (u + du, v, z), face, w - 0.1, h - 0.1, ['JURY ASSEMBLY'], 'TC sign jury assembly', bg=(26, 22, 18), fg=(232, 214, 170), emis=False, scale=0.9)
    for dv in (-w / 2 + 0.2, w / 2 - 0.2): TK.box(room, (u - 0.01, v + dv - 0.01, z + h / 2), (u + 0.01, v + dv + 0.01, top), 'brass', col=False)
def core_band(room):
    """the walnut band (the bank's panel wood) with brass top / bottom edges round the core, in the course the lining leaves for it:
    0.1 deep like the lining, so its face is the lining's face."""
    CO = JT.CORE; z0, z1 = JT.CORE_BAND; e = JT.CORE_BAND_EDGE
    faces = [(CO[0] - 0.1, CO[1] + 0.1, CO[2] - 0.1, CO[2]), (CO[0] - 0.1, CO[1] + 0.1, CO[3], CO[3] + 0.1),
             (CO[0] - 0.1, CO[0], CO[2], CO[3]), (CO[1], CO[1] + 0.1, CO[2], CO[3])]
    for u0, u1, v0, v1 in faces:
        TK.box(room, (u0, v0, z0), (u1, v1, z0 + e), 'brass'); TK.box(room, (u0, v0, z0 + e), (u1, v1, z1 - e), 'bx_mahog')
        TK.box(room, (u0, v0, z1 - e), (u1, v1, z1), 'brass')
def directory(room):
    """the directory board between the lift doors (made from JT.DIRECTORY) in a 4 cm brass frame proud of the lining."""
    CO = JT.CORE; zc, w, h = JT.DIRECTORY_BOARD; mid = (CO[0] + CO[1]) / 2; face = CO[2] - 0.1; z = JT.F1 + zc; f = 0.04
    TK.sign(room, (mid, face, z), '-v', w, h, JT.DIRECTORY, 'TC sign tower directory', bg=(26, 22, 18), fg=(232, 214, 170), emis=False, scale=0.8)
    for a0, a1, b0, b1 in ((mid - w / 2 - f, mid + w / 2 + f, z + h / 2, z + h / 2 + f), (mid - w / 2 - f, mid + w / 2 + f, z - h / 2 - f, z - h / 2),
                           (mid - w / 2 - f, mid - w / 2, z - h / 2, z + h / 2), (mid + w / 2, mid + w / 2 + f, z - h / 2, z + h / 2)):
        TK.box(room, (a0, face - 0.06, b0), (a1, face, b1), 'brass', col=False)
    D5.SH.keep_clear(room, (mid - w / 2 - f, face - 0.06, z - h / 2 - f), (mid + w / 2 + f, face, z + h / 2 + f))   # the wall shell stops round the board
def lift_marks(room, name, z0):
    """the floor number over each lift door of the public bank, on the lining's face (tc_kit.lift_bank's own indicator stands in the
    front wall's plane, behind this room's 0.1 lining, and is never seen)."""
    CO = JT.CORE; mid = (CO[0] + CO[1]) / 2; zc, w, h = JT.LIFT_IND
    for c in (mid - 1.7, mid + 1.7):
        TK.sign(room, (c, CO[2] - 0.1, z0 + zc), '-v', w, h, [name], f'TC lift floor {name}', bg=(10, 10, 10), fg=(255, 160, 40))
def stair():
    room = 'stair'; CO = JT.CORE; SC = JT.SC; z0, z1 = JT.F1, JT.STAIR_TOP + 3.2
    reg = [(CO[0], CO[1], JT.LIFT_BODY, CO[3])]
    holes = opening_boxes()
    lining(room, reg, [], z0, z1, 'conc', holes, ext_t=0.2, int_t=0.2)
    slab(room, reg, z0 - 0.4, z0, 'speckle'); slab(room, reg, z1, z1 + 0.2, 'conc', col=False)
    for base, d, zb, zt, lane in JT.flights():
        TK.stair(room, 'u', base, d, zb, zt, lane, 'speckle', 'steel', fill_to=None, depth=0.45)
        zl = zt                                                                 # the landing the flight arrives at
        if d < 0: TK.box(room, (SC[0], SC[2], zl - 0.3), (JT.W_LAND, SC[3], zl), 'speckle')   # west landing
        elif zl > JT.F1 + 1e-6: TK.box(room, (JT.E_LAND, SC[2], zl - 0.3), (SC[1], SC[3], zl), 'speckle')   # east landing (L1's is the floor)
    TK.box(room, (JT.W_LAND, JT.MIDW[0], z0), (JT.E_LAND, JT.MIDW[1], JT.STAIR_TOP + 1.0), 'conc')                 # the wall between the lanes, one piece
    for zl in (JT.F1 + 3.6 * k for k in range(5)):
        TK.lamp(room, (JT.E_LAND + SC[1]) / 2, (SC[2] + SC[3]) / 2, zl + 3.0, energy=0.6, falloff=6.0, size=(0.9, 0.3))
        TK.lamp(room, (SC[0] + JT.W_LAND) / 2, (SC[2] + SC[3]) / 2, zl + 1.8 + 3.0, energy=0.6, falloff=6.0, size=(0.9, 0.3))
    return reg
def lifts():
    CO = JT.CORE; mid = (CO[0] + CO[1]) / 2
    for name, room, z0, z1 in JT.LIFT_STOPS:
        TK.lift_bank(room, 'courts', name, CO[0], CO[1], CO[2], JT.LIFT_BODY, z0, z1, front='granite', body='granite', panel=tuple(s[0] for s in JT.LIFT_STOPS))
        lift_marks(room, name, z0)
    for name, room, z0, z1 in JT.SEC_STOPS:
        sec_car(room, name, z0, z1)
def sec_car(room, name, z0, z1):
    """one car facing +v (into the secure corridor, or at B1 the prisoner tunnel): cab, front wall with one sliding door, the shaft
    walls, up to the room's ceiling z1."""
    cu0, cu1, cv0, cv1 = JT.SEC_CAB; SL = JT.SLIFT; c = (cu0 + cu1) / 2; ep = cv1 + 0.3   # front wall cv1 .. ep (doors at ep)
    TK.box(room, (cu0, cv0, z0), (cu1, cv1, z0 + 0.03), 'steel')
    for a, b, v0_, v1_ in ((cu0, cu0 + 0.02, cv0, cv1), (cu1 - 0.02, cu1, cv0, cv1), (cu0, cu1, cv0, cv0 + 0.02)):
        TK.box(room, (a, v0_, z0 + 0.03), (b, v1_, z0 + 2.75), 'steel', col=False)
    TK.box(room, (cu0, cv0, z0 + 2.75), (cu1, cv1, z0 + 2.8), 'steel', col=False); TK.lamp(room, c, (cv0 + cv1) / 2, z0 + 2.75, energy=0.5, falloff=4.0, size=(0.8, 0.8))
    for a0, a1, c0, c1 in TK.rects_minus(SL[0] + 0.1, SL[1] - 0.1, z0, z1, [(c - 0.65, c + 0.65, z0, z0 + 2.6)]):
        TK.box(room, (a0, cv1, c0), (a1, ep, c1), 'block')
    TK.box(room, (c - 0.65, cv1, z0), (c + 0.65, ep, z0 + 0.03), 'steel')
    for a0, a1, b0, b1 in TK.rects_minus(SL[0] + 0.1, SL[1] - 0.1, SL[2] + 0.1, cv1, [(cu0, cu1, cv0, cv1)]): TK.box(room, (a0, b0, z0), (a1, b1, z1), 'block')
    TK.door(room, TK.LIFT_DOOR, c + 0.65, ep - 0.15, z0, 180.0)       # the leaf runs +x from its origin: heading 180 lays it across the opening
                                                                           # from c + 0.65 and it slides into the wall on the core side (as tc_kit.lift_bank's left car)
    if z1 > z0 + 2.8 + 1e-6: TK.box(room, (cu0, cv0, z0 + 2.8), (cu1, cv1, z1), 'block')      # over the cab (none at B1: the tunnel's ceiling is the cab's)
    OPS['lifts'].append({'bank': 'secure', 'floor': name, 'z': z0, 'cabs': [TK.world(c, (cv0 + cv1) / 2) + [z0]], 'heading': (math.degrees(TK.HEAD)) % 360})
def prepare():
    """the doors, openings and portals of area 2 (the galleria's walls need the doorway before anything is drawn)."""
    JT.DOORS.clear(); JT.OPENINGS.clear(); JT.PORTALS.clear()
    for a0, nm in JT.GALLERIA_DOORS: JT.double_door(nm, 'galleria', 'tlobby', 'v', 17.3, a0, JT.F1, 1, models=(JT.GLASS_L, JT.GLASS_R))
    JT.single_door('L1_stair', 'tlobby', 'stair', 'u', JT.CORE[1], JT.STAIR_DOOR_V, JT.F1, -1)
    for f in JT.FLOORS: JT.floor_plan(f)
    for name, frm, to, ax, plane, a0, into, kind in C5.WING_DOORS:                    # area 5: the Government Offices wing
        (JT.double_door if kind == 'double' else JT.single_door)(name, frm, to, ax, plane, a0, JT.F1, into)
    for k in C5.OFFICE_FLOORS:                                                         # the Mayor's / the Governor's office doors (inside the suite)
        name, frm, to, ax, plane, a0, into, kind = C5.OFFICE_DOOR(k); JT.double_door(name, frm, to, ax, plane, a0, C5.office_F(k), into)
def build_rooms():
    """areas 2 + 5: returns the room regions (2D rects) for the layout / gates / probes."""
    regions = {'tlobby': lobby(), 'stair': stair()}
    regions.update(gov_wing())
    for f in JT.FLOORS: regions.update(court_floor(f))
    for k in C5.OFFICE_FLOORS: regions.update(office_floor(k))
    D5.shells()                                                           # every room's wall shell, once its built-ins stand
    for f in JT.FLOORS: OPS['props'] += [(r, m, u, v, JT.FLOORS[f] + z, h) for r, m, u, v, z, h in JT.room_props(f)]
    lifts()
    OPS['portals'] = [{'from': p['from'], 'to': p['to'], 'kind': p['kind'], 'P': p['P'], 'door': p.get('door')} for p in JT.PORTALS] + OPS['portals']
    OPS['doors'] = list(JT.DOORS)
    regions.pop('lift', None)
    return regions
import jc5_dress as D5                                                     # area 5's helpers (imports this module back: kept last)
