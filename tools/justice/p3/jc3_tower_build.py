"""Phase 3 area 2 (Blender, called by jc3_build.py after the galleria): the tower lobby, the stair, the public and secure lifts and the
two courtroom floors, from jc3_tower. tc_kit (TK) draws; every room's walls are the LINING of its own floor region (a strip inside its
boundary: 0.1 m against another room, so two rooms make a 0.2 m partition back to back; 0.2 m on an outer wall; 0.3 in the lobby),
cut by its door openings and window bays (p2_plan.box_minus, exact), so partitions touch and never overlap."""
import math
import tc_kit as TK
import p2_plan as PL
import jc3_tower as JT
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
    F = JT.FLOORS[f]; crt, pub, rst, sec = f'crt{f}', f'pub{f}', f'rst{f}', f'sec{f}'
    IN = (JT.IU0, JT.IU1, JT.IV0, JT.IV1); CB = JT.CB; CO = JT.CORE
    R = {crt: [CB], sec: [(CB[1], CO[0], CB[2], CB[3])],
         rst: [(JT.IU0, CB[0], JT.W_RING_V, CB[3]), (JT.IU0, JT.RST_E, CB[3], JT.IV1)],
         'stair': [(CO[0], CO[1], JT.LIFT_BODY, CO[3])], 'lift': [(CO[0], CO[1], CO[2], JT.LIFT_BODY)]}
    taken = R[crt] + R[sec] + R[rst] + R['stair'] + R['lift']
    R[pub] = [(a, b, c, d) for a, b, c, d in TK.rects_minus(*IN, taken)]
    holes = opening_boxes() + bay_boxes(F)
    lift_holes = [(c - 0.65, c + 0.65, CO[2] - 0.4, CO[2] + 0.4, F, F + 2.6) for c in ((CO[0] + CO[1]) / 2 - 1.7, (CO[0] + CO[1]) / 2 + 1.7)]
    def others(me): return [(r, 0.1) for k, rs in R.items() if k != me for r in rs]
    top = {crt: F + JT.CEIL_T - 0.2, pub: F + JT.ROOM_H, rst: F + JT.ROOM_H, sec: F + JT.ROOM_H}
    flo = {crt: 'carpet', pub: 'marble', rst: 'carpet', sec: 'speckle'}
    wal = {crt: 'slat', pub: 'plaster', rst: 'plaster', sec: 'block'}
    for room in (crt, pub, rst, sec):
        reg = R[room]
        slab(room, reg, F - 0.4, F, flo[room])
        slab(room, reg, top[room], top[room] + 0.2, 'ceiltile' if room != crt else 'plaster', col=False)
        oth = others(room) if room != crt else []
        lining(room, reg, oth, F, top[room], wal[room], holes + (lift_holes if room == pub else []),
               ext_t=JT.OL if room != crt else JT.CW, int_t=0.1 if room != crt else JT.CW)
        OPS['portals'] += window_portals(room, F, reg)
        lights_grid(room, reg, top[room], 4.0 if room == crt else 3.2)
    # the interior partitions inside rst and pub (one room each: walls with doors, no portal)
    inner = [(rst, 'v', JT.CORR_N, JT.IU0 + JT.OL, JT.RST_E - 0.1), (rst, 'u', JT.JURY_E, JT.CORR_N, JT.IV1 - JT.OL),
             (rst, 'u', JT.CHAMB_E, JT.CORR_N, JT.IV1 - JT.OL), (rst, 'v', JT.WIT_N, JT.IU0 + JT.OL, JT.CB[0] - 0.1),
             (pub, 'v', JT.CONF_S, JT.RST_E + 0.1, JT.IU1 - JT.OL)]
    for room, ax, at, a0, a1 in inner:
        box3 = (at - 0.1, at + 0.1, a0, a1, F, F + JT.ROOM_H) if ax == 'u' else (a0, a1, at - 0.1, at + 0.1, F, F + JT.ROOM_H)
        for c in box_minus(box3, holes): TK.box(room, (c[0], c[2], c[4]), (c[1], c[3], c[5]), 'plaster')
    # fittings
    fit = JT.court_fittings(f)
    for u0, u1, v0, v1, z0, z1, mat, col in fit['boxes']: TK.box(crt, (u0, v0, F + z0), (u1, v1, F + z1), mat, col)
    st = TK.stair(crt, 'u', 28.57, -1, F, F + JT.DAIS, (38.6, 39.9), 'plank', None)        # the dais steps (east)
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
    # signs
    TK.sign(pub, (29.45, JT.CB[2] - 0.1, F + 2.75), '-v', 2.4, 0.5, [f'COURTROOM {"3" if f == "A" else "5"}{f}'], f'TC sign courtroom {f}', bg=(30, 30, 34), fg=(232, 214, 170))
    TK.sign(crt, (25.3, JT.CV1, F + 3.6), '-v', 3.4, 1.0, ['COURT OF COMMON PLEAS', 'CUYAHOGA COUNTY, OHIO'], f'TC sign bench {f}', bg=(40, 28, 18), fg=(214, 178, 110), emis=False)
    TK.sign(pub, (JT.CORE[0] + 3.8, JT.CORE[2] - 0.0, F + 2.95), '-v', 3.0, 0.35, [f'LEVEL {3 if f == "A" else 5}  -  COURTROOM {"3" if f == "A" else "5"}{f}'], f'TC sign lifts {f}', bg=(30, 30, 34), fg=(232, 214, 170))
    return R
def lights_grid(room, region, z, pitch):
    for u0, u1, v0, v1 in region:
        nu = max(1, int((u1 - u0) // pitch)); nv = max(1, int((v1 - v0) // pitch))
        if (u1 - u0) < 1.4 or (v1 - v0) < 1.4: continue
        for i in range(nu):
            for j in range(nv):
                TK.lamp(room, u0 + (u1 - u0) * (i + 0.5) / nu, v0 + (v1 - v0) * (j + 0.5) / nv, z, energy=0.7, falloff=8.0, size=(1.2, 0.3))
def lobby():
    room = 'tlobby'; CO = JT.CORE; SL = JT.SLIFT
    region = [JT.LB, (PL.TOWER_VEST[0], PL.TOWER_VEST[1], 17.3, JT.LB[2])]
    taken = [(CO[0], CO[1], CO[2], CO[3]), SL]
    reg = []
    for r in region: reg += TK.rects_minus(*r, taken)
    oth = [((CO[0], CO[1], JT.LIFT_BODY, CO[3]), 0.1), ((CO[0], CO[1], CO[2], JT.LIFT_BODY), 0.1), (SL, 0.1), ((13.0, 38.0, 16.0, 17.3), 0.15)]
    runs = JT.lobby_runs(); holes = opening_boxes()
    for fid, a0, a1, z0, z1 in runs:
        if fid == 'N': holes.append((a0, a1, JT.LB[3] - 0.5, JT.LB[3] + 0.1, z0, z1)); OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': 'lobby N glass', 'P': ('v', JT.LV1, a0, a1, z0, z1, 1)})
        if fid == 'S': holes.append((a0, a1, JT.LB[2] - 0.1, JT.LB[2] + 0.5, z0, z1)); OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': 'lobby S glass', 'P': ('v', JT.LV0, a0, a1, z0, z1, -1)})
        if fid == 'E': holes.append((JT.LB[1] - 0.5, JT.LB[1] + 0.1, a0, a1, z0, z1)); OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': 'lobby E glass', 'P': ('u', JT.LU1, a0, a1, z0, z1, 1)})
    lift_holes = [(c - 0.65, c + 0.65, CO[2] - 0.4, CO[2] + 0.4, JT.F1, JT.F1 + 2.6) for c in ((CO[0] + CO[1]) / 2 - 1.7, (CO[0] + CO[1]) / 2 + 1.7)]
    slab(room, reg, JT.F1 - 0.4, JT.F1, 'marble')
    slab(room, reg, JT.LOB_CEIL - 0.2, JT.LOB_CEIL, 'plaster', col=False)
    band_hole = [(CO[0] - 0.15, CO[1] + 0.15, CO[2] - 0.15, CO[3] + 0.15, JT.CORE_BAND[0], JT.CORE_BAND[1])]   # the core's lining leaves the band's course
    lining(room, reg, oth, JT.F1, JT.LOB_CEIL - 0.2, 'granite', holes + lift_holes + band_hole, ext_t=JT.LL, int_t=0.1)
    core_band(room)
    lights_grid(room, reg, JT.LOB_CEIL - 0.2, 6.0)
    # the information desk (kit counter) by the vestibule, benches
    u0, u1, v0, v1, hh = JT.CLERK_DESK                                    # the Clerk of Courts counter, its name on its public face
    TK.box(room, (u0, v0, JT.F1), (u1, v1, JT.F1 + hh), 'granite'); TK.box(room, (u0 - 0.1, v0 - 0.1, JT.F1 + hh), (u1 + 0.1, v1 + 0.1, JT.F1 + hh + 0.04), 'band')
    TK.sign(room, ((u0 + u1) / 2, v0 + 0.035, JT.F1 + 0.62), '-v', 3.2, 0.36, ['CLERK OF COURTS'], 'TC sign clerk of courts', bg=(26, 22, 18), fg=(232, 214, 170), emis=False, scale=0.9)
    jury_assembly(room)
    for u in (25.6, 28.4): OPS['props'].append((room, 'prop_off_chair_05', u, 24.2, JT.F1, 0.0))
    for u, v, h in ((JT.LU1 - 0.5, 40.0, 270.0), (JT.LU1 - 0.5, 46.0, 270.0)): OPS['props'].append((room, JT_BENCH, u, v, JT.F1, h))   # east wall, facing in
    for cu, cv in ((22.5, 33.0), (22.5, 44.0), (30.5, 47.5)):                       # seating islands: benches back to back, planters at the ends
        OPS['props'] += [(room, JT_BENCH, cu, cv - 0.5, JT.F1, 0.0), (room, JT_BENCH, cu, cv + 0.5, JT.F1, 180.0)]
        OPS['props'] += [(room, 'ch_prop_ch_planter_01', cu + du, cv, JT.F1, 0.0) for du in (-2.35, 2.35)]
    OPS['props'] += [(room, m, u, v, JT.F1, 0.0) for m, u, v in JT.LOBBY_FLAGS]
    OPS['props'] += [(room, 'apa_mp_h_acc_plant_palm_01', u, v, JT.F1, 0.0) for u, v in ((JT.LU0 + 1.0, JT.LV1 - 1.0), (JT.LU1 - 1.0, JT.LV1 - 1.0), (JT.LU1 - 1.0, JT.LV0 + 1.2))]
    OPS['props'] += [(room, 'ch_prop_ch_planter_01', u, 27.9, JT.F1, 0.0) for u in (34.2, 43.4)]
    OPS['props'] += [(room, 'prop_watercooler', JT.LU0 + 0.3, 27.0, JT.F1, 90.0), (room, 'prop_bin_11b', JT.LU0 + 0.35, 28.0, JT.F1, 0.0), (room, 'prop_bin_11b', 43.6, 36.2, JT.F1, 0.0)]
    directory(room)
    return reg
def jury_assembly(room):
    """the Jury Assembly sign hung from the ceiling over the east benches: a 4 cm walnut panel, the sign on both faces, two brass rods."""
    u, v, zc, w, h = JT.JURY_ASSEMBLY; z = JT.F1 + zc; top = JT.LOB_CEIL - 0.2
    TK.box(room, (u - 0.02, v - w / 2, z - h / 2), (u + 0.02, v + w / 2, z + h / 2), 'panel', col=False)
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
        TK.box(room, (u0, v0, z0), (u1, v1, z0 + e), 'brass'); TK.box(room, (u0, v0, z0 + e), (u1, v1, z1 - e), 'panel')
        TK.box(room, (u0, v0, z1 - e), (u1, v1, z1), 'brass')
def directory(room):
    """the directory board between the lift doors (made from JT.DIRECTORY) in a 4 cm brass frame proud of the lining."""
    CO = JT.CORE; zc, w, h = JT.DIRECTORY_BOARD; mid = (CO[0] + CO[1]) / 2; face = CO[2] - 0.1; z = JT.F1 + zc; f = 0.04
    TK.sign(room, (mid, face, z), '-v', w, h, JT.DIRECTORY, 'TC sign tower directory', bg=(26, 22, 18), fg=(232, 214, 170), emis=False, scale=0.8)
    for a0, a1, b0, b1 in ((mid - w / 2 - f, mid + w / 2 + f, z + h / 2, z + h / 2 + f), (mid - w / 2 - f, mid + w / 2 + f, z - h / 2 - f, z - h / 2),
                           (mid - w / 2 - f, mid - w / 2, z - h / 2, z + h / 2), (mid + w / 2, mid + w / 2 + f, z - h / 2, z + h / 2)):
        TK.box(room, (a0, face - 0.06, b0), (a1, face, b1), 'brass', col=False)
def lift_marks(room, name, z0):
    """the floor number over each lift door of the public bank, on the lining's face (tc_kit.lift_bank's own indicator stands in the
    front wall's plane, behind this room's 0.1 lining, and is never seen)."""
    CO = JT.CORE; mid = (CO[0] + CO[1]) / 2; zc, w, h = JT.LIFT_IND
    for c in (mid - 1.7, mid + 1.7):
        TK.sign(room, (c, CO[2] - 0.1, z0 + zc), '-v', w, h, [name], f'TC lift floor {name}', bg=(10, 10, 10), fg=(255, 160, 40))
JT_BENCH = 'v_ilev_ph_bench'
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
    for name, room, z0 in JT.SEC_STOPS:
        sec_car(room, name, z0)
    cu0, cu1, cv0, cv1 = JT.SEC_CAB                                       # B1: jc-jail's tunnel stop (its MLO draws the cab, front wall and door;
    OPS['lifts'].append({'bank': 'secure', 'floor': 'B1', 'z': JT.SEC_B1, 'cabs': [TK.world((cu0 + cu1) / 2, (cv0 + cv1) / 2) + [JT.SEC_B1]],   # here only its stop)
                         'heading': (math.degrees(TK.HEAD)) % 360})
def sec_car(room, name, z0):
    """one car facing +v (into the secure corridor): cab, front wall with one sliding door, the shaft walls."""
    cu0, cu1, cv0, cv1 = JT.SEC_CAB; SL = JT.SLIFT; z1 = z0 + JT.ROOM_H; c = (cu0 + cu1) / 2; ep = cv1 + 0.3   # front wall cv1 .. ep (doors at ep)
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
    TK.box(room, (cu0, cv0, z0 + 2.8), (cu1, cv1, z1), 'block')
    OPS['lifts'].append({'bank': 'secure', 'floor': name, 'z': z0, 'cabs': [TK.world(c, (cv0 + cv1) / 2) + [z0]], 'heading': (math.degrees(TK.HEAD)) % 360})
def prepare():
    """the doors, openings and portals of area 2 (the galleria's walls need the doorway before anything is drawn)."""
    JT.DOORS.clear(); JT.OPENINGS.clear(); JT.PORTALS.clear()
    for a0, nm in JT.GALLERIA_DOORS: JT.double_door(nm, 'galleria', 'tlobby', 'v', 17.3, a0, JT.F1, 1, models=(JT.GLASS_L, JT.GLASS_R))
    JT.single_door('L1_stair', 'tlobby', 'stair', 'u', JT.CORE[1], JT.STAIR_DOOR_V, JT.F1, -1)
    for f in JT.FLOORS: JT.floor_plan(f)
def build_rooms():
    """the whole of area 2: returns the room regions (2D rects) for the layout / gates / probes."""
    regions = {'tlobby': lobby(), 'stair': stair()}
    for f in JT.FLOORS: regions.update(court_floor(f))
    for f in JT.FLOORS: OPS['props'] += [(r, m, u, v, JT.FLOORS[f] + z, h) for r, m, u, v, z, h in JT.room_props(f)]
    lifts()
    OPS['portals'] = [{'from': p['from'], 'to': p['to'], 'kind': p['kind'], 'P': p['P'], 'door': p.get('door')} for p in JT.PORTALS] + OPS['portals']
    OPS['doors'] = list(JT.DOORS)
    regions.pop('lift', None)
    return regions
