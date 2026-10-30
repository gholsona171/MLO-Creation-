"""Justice Center phase 3, AREA 2: the courts tower's lobby (L1-L2), the stair + lifts, and the two courtroom floors (A on L3-L4,
B on L5-L6), as numbers (pure Python; jc3_build.py draws them, jc3_meta / the gates / the probes / mlo-data read them).
Lot frame, z absolute. The tower's interior volumes are phase 2's (p2_plan.tower_voids: the hull keeps the rest); levels L1..L7 are
3.6 m (18 risers of 0.20) so the stair is Rockstar's 0.20 / 0.27.
Per courtroom floor (identical plans, f = 'A' / 'B'):
  crt  the courtroom, INNER (p2_plan.TOWER_COURT, no window), double height: bench on a 0.40 dais (north), witness stand west of it,
       jury box (two tiers, 12) on the west wall, clerk desk, two counsel tables + lectern in the well, the bar with its gate, 66 seats
       of gallery pews (south). Doors: public (south, from pub), judge + jury (north, from rst), defendant (east, from sec).
  pub  public: the south corridor, the lift lobby, the east waiting hall along the windows, an attorney conference room (NE).
  rst  restricted: the corridor behind the courtroom, the jury room (NW), the judge's chambers and robing room (N), a witness room.
  sec  secure: the secure lift (one car), the corridor, three holding cells, the officers' post at the defendant door.
Lobby (L1-L2, room tlobby): inside the colonnade glass (3.0 m back), the vestibule + two pairs of doors from the galleria, the public
lift bank (stops L1 / L3 / L5), the stair door, an information desk. Stair (room stair): one room from L1 to L5 (doors on L1 / L3 / L5).
Every partition that meets an outer wall lands in a gap between window bays (a granite fin): checked by tests/test_jc3_tower.py."""
import math, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3.parent / 'p2'), str(P3.parent)]
import p2_plan as PL
LV = PL.B['tower']['levels']; F1, F2, F3, F4, F5, F6, F7 = LV[:7]
FLOORS = {'A': F3, 'B': F5}
IU0, IU1, IV0, IV1 = PL.TOWER_IN['u0'], PL.TOWER_IN['u1'], PL.TOWER_IN['v0'], PL.TOWER_IN['v1']   # 14.15 50.15 17.75 55.85
OL = 0.2                                                                # outer lining (behind the window glass)
RU0, RU1, RV0, RV1 = IU0 + OL, IU1 - OL, IV0 + OL, IV1 - OL            # 14.35 49.95 17.95 55.65: rooms' faces on the outer walls
CB = PL.TOWER_COURT; CORE = PL.TOWER_CORE; SLIFT = PL.TOWER_SECLIFT
CW = 0.15                                                               # courtroom wall (inside its box); neighbours add a 0.1 skin
CU0, CU1, CV0, CV1 = CB[0] + CW, CB[1] - CW, CB[2] + CW, CB[3] - CW     # 19.35 31.05 22.95 41.05: the courtroom's clear
DAIS = 0.40; CEIL_T = 6.8                                               # dais 2 risers; courtroom ceiling at F + 6.8 (next floor's slab over)
ROOM_H = 3.4                                                            # pub / rst / sec ceilings at F + 3.4
# room lines (each a wall's centre line, 0.2 thick split 0.1 / 0.1 between the rooms)
W_RING_V = 21.0                                                         # west ring rst / south corridor pub: on the W face's solid corner (< 21.3)
RST_E = 39.55                                                           # rst / pub, north side: in the N face's fin gap 39.2 .. 39.9
CORR_N = 43.0                                                           # restricted corridor / rooms
JURY_E = 24.75; CHAMB_E = 32.15                                         # jury room | chambers | robing: N face fin gaps 24.4..25.1 / 31.8..32.5
WIT_N = 28.88                                                           # witness room (west ring): W face fin gap 28.52 .. 29.23
CONF_S = 44.73                                                          # NE conference room: E face fin gap 44.38 .. 45.08
# ---------------- rooms ----------------
def rooms():
    out = {'galleria': 1, 'tlobby': 2, 'stair': 3}
    for i, f in enumerate(FLOORS): out.update({f'crt{f}': 4 + 4 * i, f'pub{f}': 5 + 4 * i, f'rst{f}': 6 + 4 * i, f'sec{f}': 7 + 4 * i})
    return out
ROOM_NAME = {'tlobby': 'JC_TOWER_LOBBY', 'stair': 'JC_TOWER_STAIR', **{f'{k}{f}': f'JC_{n}_{f}' for f in FLOORS for k, n in
             (('crt', 'COURTROOM'), ('pub', 'COURT_PUBLIC'), ('rst', 'COURT_RESTRICTED'), ('sec', 'COURT_SECURE'))}}
TCYC = {k: 'mp_heist_tuner_smshop_default' for k in ROOM_NAME}
# ---------------- doors (native) ----------------
GEN = 'v_ilev_ph_gendoor005'                                            # Mission Row's solid office door: leaf along -x (1.30), hinge at 0, mid-height
GLASS_L, GLASS_R = 'v_ilev_ph_door01', 'v_ilev_ph_door002'              # the glazed pair (as the galleria's street doors)
CELL = 'v_ilev_ph_cellgate'                                             # Mission Row cell gate: leaf along -x (1.30)
LEAF = 1.30; LEAF_H = 2.30; JAMB = 0.05
def door_on(axis, plane, a0, z, model=GEN, sense=1):
    """one leaf in an opening starting at a0 along the wall (the opening is a0 .. a0 + LEAF + 2 JAMB). axis 'u' = wall plane u = plane
    (leaf along v), 'v' = plane v = plane (leaf along u). The model's leaf runs along its -x from the hinge: the hinge goes at the
    opening's far end and the heading points +x along the wall, so the leaf lies back across the opening (rig 2026-10-29: the first
    headings turned the leaves into the wall beside the opening - every area 2 door walk failed)."""
    h0 = a0 + JAMB + LEAF
    if axis == 'u': return (plane, h0, z + LEAF_H / 2, 90.0)           # heading 90: +x -> +v, so the leaf (-x) runs -v from the hinge
    return (h0, plane, z + LEAF_H / 2, 0.0)                             # heading 0: the leaf (-x) runs -u from the hinge
DOORS = []                                                              # {name, model, room, pos, heading, portal: (from, to) or None}
OPENINGS = []                                                           # {wall key, axis, plane, a0, a1, z0, z1}: holes the walls leave
PORTALS = []                                                            # {from, to, kind, P: (axis, plane, a0, a1, z0, z1, into)}
def single_door(name, frm, to, axis, plane, a0, z, into, model=GEN, wall=None):
    a1 = a0 + LEAF + 2 * JAMB; u, v, zz, h = door_on(axis, plane, a0, z)
    DOORS.append({'name': name, 'model': model, 'room': frm, 'pos': [u, v, zz], 'heading': h, 'portal': (frm, to) if to else None})
    OPENINGS.append({'axis': axis, 'plane': plane, 'a0': a0, 'a1': a1, 'z0': z, 'z1': z + LEAF_H + 0.10, 'name': name})
    if to: PORTALS.append({'from': frm, 'to': to, 'kind': name, 'P': (axis, plane, a0, a1, z, z + LEAF_H + 0.10, into), 'door': name})
def double_door(name, frm, to, axis, plane, a0, z, into, models=(GEN, GEN)):
    """a pair in one opening a0 .. a0 + 2 LEAF + 2 JAMB: leaf 1 hinged at a0's side, leaf 2 at the far side, meeting in the middle.
    (Same model twice: the second turned 180 deg so its leaf runs the other way.)"""
    a1 = a0 + 2 * LEAF + 2 * JAMB
    for k, (hinge, hd) in enumerate(((a0 + JAMB, 0.0), (a1 - JAMB, 180.0))):
        m = models[k]
        if m == GLASS_L or m == GLASS_R:                                    # the Mission Row pair: door01 leaf +x, door002 leaf -x
            h = 90.0 if axis == 'u' else 0.0
        else:
            h = (90.0 if axis == 'u' else 0.0) + (180.0 if k == 0 else 0.0)   # leaf 2 runs -a from its hinge; leaf 1 (turned 180) runs +a
        u, v = (plane, hinge) if axis == 'u' else (hinge, plane)
        DOORS.append({'name': f'{name}_{k}', 'model': m, 'room': frm, 'pos': [u, v, z + LEAF_H / 2], 'heading': h % 360.0, 'portal': (frm, to) if to else None})
    OPENINGS.append({'axis': axis, 'plane': plane, 'a0': a0, 'a1': a1, 'z0': z, 'z1': z + LEAF_H + 0.10, 'name': name})
    if to: PORTALS.append({'from': frm, 'to': to, 'kind': name, 'P': (axis, plane, a0, a1, z, z + LEAF_H + 0.10, into), 'door': name})
def holes_on(axis, plane, tol=0.35):
    return [(o['a0'], o['a1'], o['z0'], o['z1']) for o in OPENINGS if o['axis'] == axis and abs(o['plane'] - plane) < tol]
# ---------------- window bays (phase 2's openings) on the courtroom floors ----------------
def bays(face_id, F):
    face = next(f for f in PL.face_list('tower') if f[0] == face_id)
    return [(o[1], o[2], o[3], o[4]) for o in PL.openings('tower', face) if o[0] == 'win' and abs(o[3] - (F + 0.95)) < 0.01]
FACE_LINE = {'N': ('v', RV1, 1), 'S': ('v', RV0, -1), 'E': ('u', RU1, 1), 'W': ('u', RU0, -1)}   # the room-side plane of each outer lining
# ---------------- the lobby (L1-L2) ----------------
A = PL.TOWER_IN['arc']                                                 # 3.0: the colonnade glass line
LB = (IU0, 50.6 - A, 17.3 + A, 56.3 - A)                               # the lobby's void box (u0, u1, v0, v1)
LL = 0.3                                                               # lobby linings
LU0, LU1, LV0, LV1 = LB[0] + LL, LB[1] - LL, LB[2] + LL, LB[3] - LL    # 14.45 47.3 20.6 53.0
VEST = (PL.TOWER_VEST[0] + LL, PL.TOWER_VEST[1] - LL)                  # 22.8 .. 31.2: the vestibule's clear width
LOB_CEIL = F3 - 0.4                                                    # 35.6: the lobby's ceiling = the underside of L3's floor slab
def lobby_runs():
    """the colonnade glass runs the lobby looks out through: (face, a0, a1, z0, z1)."""
    out = []
    for face in PL.face_list('tower'):
        for run in PL.arcade_runs('tower', face): out.append((face[0], run[0][0], run[-1][1], run[0][2], run[0][3]))
    return out
GALLERIA_DOORS = [(23.9, 'lobby_a'), (27.2, 'lobby_b')]                # a0 of each glazed pair (2 x 1.30 + jambs = 2.70)
# ---------------- the stair (0.20 / 0.27, switchback per 1.8 m half storey) ----------------
SC = (CORE[0] + 0.2, CORE[1] - 0.2, CORE[2] + 3.35, CORE[3] - 0.2)     # stair clear u 35.2 .. 42.4, v 32.35 .. 35.45
LIFT_BODY = CORE[2] + 3.15                                             # 32.15: the lift bank's back (stair's south wall from here)
LANE_S = (SC[2], SC[2] + 1.30); LANE_N = (SC[3] - 1.30, SC[3]); MIDW = (LANE_S[1] + 0.15, LANE_N[0] - 0.15)
E_LAND = 39.8                                                          # the east landing from u 39.8 (doors on its east wall)
RISERS = 9; GO = 0.27
W_LAND = E_LAND - (RISERS - 1) * GO                                    # 37.64: the west landing's edge
STAIR_TOP = F5                                                         # last landing (L5)
STAIR_DOOR_V = 33.35                                                   # the doors on the core's east wall (a0 along v)
def flights():
    """[(base u, direction, bottom z, top z, lane)]: from L1 to L5, two flights of 9 risers per storey."""
    out = []; z = F1
    while z < STAIR_TOP - 1e-6:
        out.append((E_LAND, -1, z, z + 1.8, LANE_S)); out.append((W_LAND, 1, z + 1.8, z + 3.6, LANE_N)); z += 3.6
    return out
# ---------------- lifts ----------------
LIFT_STOPS = [('L1', 'tlobby', F1, LOB_CEIL), ('L3', 'pubA', F3, F3 + ROOM_H), ('L5', 'pubB', F5, F5 + ROOM_H)]
# the lobby's core dressing (Antonio 2026-10-29): a walnut band with brass edges round the core above the doors, a floor number over
# every lift door (every stop), a brass-framed directory board between the two lift doors
CORE_BAND = (F1 + 3.0, F1 + 3.4)                                       # z: above the lift doors (2.6) and their floor numbers (2.64 .. 2.86)
CORE_BAND_EDGE = 0.03                                                  # the brass edge strips (top and bottom of the band)
LIFT_IND = (2.75, 0.9, 0.22)                                           # floor number over a lift door: centre z above the floor, w, h
DIRECTORY = ['DIRECTORY', 'L5    COURTROOM 5B', 'L3    COURTROOM 3A', 'L1    CLERK OF COURTS', 'L1    JURY ASSEMBLY',
             'L1    LOBBY']                                              # what the tower holds (the board is made from this)
# Antonio 2026-10-29: the L1 information desk is the Clerk of Courts counter; the seating by the east glass (north) is Jury Assembly
CLERK_DESK = (24.6, 29.4, 22.6, 23.4, 1.05)                             # the counter (u0, u1, v0, v1, height); its sign is its public (south) face
JURY_ASSEMBLY = (45.4, 43.0, 3.1, 2.6, 0.5)                             # the hanging sign over the east benches: u, v, centre z above the floor, w, h
DIRECTORY_BOARD = (1.6, 1.3, 1.5)                                      # centre z above the floor, w, h (between the lift doors)
LOBBY_FLAGS = [('v_20_flag01', 34.45, 30.3), ('v_20_flag02', 34.45, 31.0), ('v_20_flag03', 34.45, 31.7)]   # against the core's west face, clear of the lift doors
SEC_STOPS = [('L3', 'secA', F3), ('L5', 'secB', F5)]
SEC_B1 = 22.8                                                          # the secure bank's B1 stop: jc-jail's prisoner tunnel (work/jail/jj_plan.B1)
SEC_CAB = (SLIFT[0] + 0.7, SLIFT[1] - 0.7, SLIFT[2] + 0.2, SLIFT[3] - 0.6)   # one car: u 31.9 .. 34.3, v 23.0 .. 25.2; front wall to 25.5, doors face +v
SEC_LAND = 1.8                                                         # the secure lift's landing: front wall face (25.5) .. the cells' south wall
CELL_S = SEC_CAB[3] + 0.3 + SEC_LAND                                   # the cells' south wall (27.3) (rig 2026-10-29: at 25.8 the lift opened onto a 0.3 m slot)
CELL_D = 2.75                                                          # each cell's pitch along v (a 0.15 block partition at its north end)
CELL_V0 = tuple(CELL_S + 0.2 + k * CELL_D for k in range(3))           # the cells' south edges (27.5, 30.25, 33.0)
# ---------------- one courtroom floor ----------------
def floor_plan(f):
    """the courtroom floor's doors, openings and portals (appended to DOORS / OPENINGS / PORTALS) and its fittings."""
    F = FLOORS[f]; crt, pub, rst, sec = f'crt{f}', f'pub{f}', f'rst{f}', f'sec{f}'
    double_door(f'{f}_public', pub, crt, 'v', CB[2], 28.05, F, 1)                          # south wall: the gallery doors
    single_door(f'{f}_judge', rst, crt, 'v', CB[3], 28.65, F, -1)                          # north wall, east of the dais
    single_door(f'{f}_jury', rst, crt, 'v', CB[3], 19.45, F, -1)                           # north wall, west: the jurors' aisle
    single_door(f'{f}_defendant', sec, crt, 'u', CB[1], 35.55, F, -1)                      # east wall: holding -> the well
    single_door(f'{f}_staff', pub, rst, 'u', RST_E, CORR_N - 1.55, F, -1)                  # pub -> the restricted corridor (lockable)
    single_door(f'{f}_stair', pub, 'stair', 'u', CORE[1], STAIR_DOOR_V, F, -1)             # pub <-> stair landing
    for nm, a0 in (('jury_room', 20.4), ('chambers', 28.0), ('robing', 35.2)): single_door(f'{f}_{nm}', rst, None, 'v', CORR_N, a0, F, 1)
    single_door(f'{f}_witness', rst, None, 'v', WIT_N, 16.2, F, -1)
    single_door(f'{f}_conference', pub, None, 'v', CONF_S, 41.0, F, 1)
    for k, v0 in enumerate(CELL_V0): single_door(f'{f}_cell{k + 1}', sec, None, 'u', 32.675, v0 + 0.6, F, 1, model=CELL)
WALL_MAT = {'crt': 'slat', 'pub': 'plaster', 'rst': 'plaster', 'sec': 'block'}
def court_fittings(f):
    """[(kind, args)] the courtroom's built fittings (kit) and its props / seats; z is relative to the floor."""
    out = {'boxes': [], 'props': [], 'seats': []}
    B = out['boxes']; P = out['props']; S = out['seats']
    def box(u0, u1, v0, v1, z0, z1, mat, col=True): B.append((u0, u1, v0, v1, z0, z1, mat, col))
    # dais (+0.40) and its steps (east, going -u), the bench
    box(22.3, 28.3, 37.7, CV1, -0.4, DAIS, 'plank')
    box(22.6, 28.0, 37.65, 38.3, 0.0, 1.30, 'panel'); box(22.6, 28.0, 38.3, 39.0, 1.14, 1.18, 'plank')           # bench front (5 cm proud of the dais) + desk top
    for u in (22.75, 27.85): box(u - 0.06, u + 0.06, 38.3, 39.0, DAIS, 1.14, 'panel')                            # desk ends
    P.append(('ex_prop_offchair_exec_01', 25.3, 39.6, DAIS, 0.0))
    for u in (22.7, 23.3, 27.6): P.append(('v_20_flag01' if u < 23 else 'v_20_flag02' if u < 27 else 'v_20_flag03', u, 40.5, DAIS, 0.0))
    # witness stand (+0.20) west of the dais: front + a side panel, entered from the west aisle
    box(20.6, 22.3, 38.0, 39.6, -0.4, 0.20, 'plank')
    box(20.6, 22.3, 38.0, 38.12, 0.20, 1.10, 'panel'); box(20.6, 20.72, 38.12, 38.9, 0.20, 1.10, 'panel')
    P.append(('v_corp_bk_chair1', 21.5, 39.0, 0.20, 0.0))
    # jury box: two tiers (back +0.40, front +0.20), a rail, open at its north end
    box(CU0, 20.6, 30.5, 35.8, -0.4, 0.40, 'plank'); box(20.6, 21.85, 30.5, 35.8, -0.4, 0.20, 'plank')
    box(21.85, 22.0, 30.5, 35.2, 0.0, 1.0, 'panel'); box(CU0, 22.0, 30.38, 30.5, 0.0, 1.0, 'panel')
    for k in range(6):
        v = 31.0 + k * 0.85
        P.append(('v_ilev_leath_chr', 20.0, v, 0.40, 90.0)); P.append(('v_ilev_leath_chr', 21.2, v, 0.20, 90.0))
    # clerk desk (front panel to the well) and two chairs facing south
    box(23.0, 27.6, 36.1, 36.75, 0.72, 0.76, 'plank'); box(23.0, 27.6, 36.0, 36.1, 0.0, 1.05, 'panel')     # top behind the front panel
    for u in (23.1, 27.5): box(u - 0.05, u + 0.05, 36.1, 36.75, 0.0, 0.72, 'panel')
    for u in (24.2, 26.4):
        P.append(('prop_off_chair_05', u, 37.25, 0.0, 0.0))
        P.append(('prop_monitor_01a', u, 36.5, 0.76, 180.0)); P.append(('prop_keyboard_01a', u, 36.25, 0.76, 180.0))
    # counsel tables (kit: top + legs: legroom) + chairs facing the bench; the lectern
    for u0, u1 in ((22.8, 25.0), (26.3, 28.5)):
        box(u0, u1, 32.0, 32.9, 0.72, 0.76, 'plank')
        for uu in (u0 + 0.08, u1 - 0.08):
            for vv in (32.08, 32.82): box(uu - 0.04, uu + 0.04, vv - 0.04, vv + 0.04, 0.0, 0.72, 'panel', False)
        for uu in (u0 + 0.55, u1 - 0.55):
            P.append(('v_corp_bk_chair1', uu, 31.45, 0.0, 180.0))
        P.append(('prop_cd_folder_pile2', (u0 + u1) / 2, 32.5, 0.76, 0.0))
    box(25.35, 25.95, 34.2, 34.6, 0.0, 1.15, 'panel')
    # the bar (0.95) across the room, a gap for its gate in the aisle
    for u0, u1 in ((CU0, 25.2), (26.1, CU1)): box(u0, u1, 29.9, 30.0, 0.0, 0.95, 'panel')
    # gallery pews: 6 rows facing north, a west block (8 seats) and an east block (3), centre + east aisles. The east aisle lines up with
    # the public double door: both leaves' walking lanes clear of the pew ends (rig 2026-10-29: a 4-seat east block put its ends in
    # leaf 0's lane, the walker stuck on them)
    for k in range(6):
        vb = 23.25 + k * 0.95
        for u0, n in ((19.6, 8), (26.2, 3)):
            u1 = u0 + n * 0.62
            box(u0 + 0.05, u1 - 0.05, vb + 0.08, vb + 0.55, 0.40, 0.45, 'plank')                                   # seat (between the ends)
            box(u0 + 0.05, u1 - 0.05, vb, vb + 0.08, 0.0, 0.95, 'plank')                                           # back
            for uu in (u0, u1 - 0.05): box(uu, uu + 0.05, vb, vb + 0.55, 0.0, 0.70, 'panel')                     # ends
            box(u0 + 0.05, u1 - 0.05, vb + 0.30, vb + 0.36, 0.0, 0.40, 'panel', False)                              # the seat's apron
            for j in range(n): S.append((u0 + 0.31 + j * 0.62, vb + 0.30, 0.45, 180.0, 'gallery pew'))   # (u, v, seat z, facing as a prop heading, what)
    return out
def sec_fittings(f):
    out = {'boxes': [], 'props': [], 'seats': []}
    B = out['boxes']
    for k, v0 in enumerate(CELL_V0):
        B.append((34.35, 34.9, v0 + 0.1, v0 + 1.75, 0.0, 0.45, 'block', True))                    # the cell's concrete bench (east wall)
        for vv in (v0 + 0.55, v0 + 1.3): out['seats'].append((34.55, vv, 0.45, 270.0, f'holding cell {k + 1}'))
        out['props'].append(('prop_toilet_01', 34.5, v0 + 2.15, 0.0, 270.0))                    # back to the east wall, clear of the gate's swing
    B.append((31.4, 32.2, 37.5, 39.0, 0.72, 0.76, 'plank', True)); B.append((31.4, 32.2, 37.5, 37.6, 0.0, 0.72, 'block', True))
    out['props'] += [('prop_off_chair_05', 32.55, 38.25, 0.0, 270.0), ('prop_cs_walkie_talkie', 31.8, 38.0, 0.76, 0.0),
                     ('prop_cctv_mon_02', 31.7, 38.6, 0.76, 90.0)]
    return out
# chairs: sit point from the prop (seat height, sit point y in the prop's frame; facing = the prop's front, -y). Checked on the rig.
CHAIR_SEAT = {'v_corp_bk_chair1': (0.48, 0.02), 'v_ilev_leath_chr': (0.50, 0.04), 'ex_prop_offchair_exec_01': (0.52, 0.05),
              'prop_off_chair_05': (0.50, 0.02), 'v_ilev_ph_bench': None,
              'v_corp_lazychair': (0.44, 0.03)}                                # (2026-10-29: had none - never sit-tested; rig sit + clone photos verify)
def room_props(f):
    """[(room, model, u, v, z_rel, heading)] for rst and pub (the jury room, the chambers, the robing room, the witness room, the NE
    conference room, the waiting benches and plants)."""
    rst, pub = f'rst{f}', f'pub{f}'; out = []
    tc = (19.5, 49.0)                                                     # jury room table (long axis along v)
    out.append((rst, 'v_corp_conftable2', *tc, 0.0, 90.0))
    for k in range(5):
        v = 47.55 + k * 0.725
        out += [(rst, 'v_ilev_leath_chr', tc[0] - 1.15, v, 0.0, 90.0), (rst, 'v_ilev_leath_chr', tc[0] + 1.15, v, 0.0, 270.0)]
    out += [(rst, 'v_ilev_leath_chr', tc[0], 46.6, 0.0, 180.0), (rst, 'v_ilev_leath_chr', tc[0], 51.4, 0.0, 0.0)]
    out += [(rst, 'prop_watercooler', 15.0, 44.0, 0.0, 90.0), (rst, 'v_corp_offshelfdark', JURY_E - 0.1 - 0.27, 52.5, 0.0, 270.0),
            (rst, 'v_corp_potplant1', RU0 + 0.75, RV1 - 0.8, 0.0, 0.0)]
    out += [(rst, 'v_corp_officedesk', 28.45, 51.8, 0.0, 0.0), (rst, 'ex_prop_offchair_exec_01', 28.45, 53.0, 0.0, 0.0),
            (rst, 'v_corp_lazychair', 27.5, 50.0, 0.0, 180.0), (rst, 'v_corp_lazychair', 29.4, 50.0, 0.0, 180.0),
            (rst, 'v_corp_offshelfdark', JURY_E + 0.1 + 0.27, 46.0, 0.0, 90.0), (rst, 'v_corp_offshelfdark', JURY_E + 0.1 + 0.27, 48.6, 0.0, 90.0),
            (rst, 'v_corp_potplant1', CHAMB_E - 0.85, RV1 - 0.8, 0.0, 0.0)]
    out += [(rst, 'v_corp_offshelfdark', RST_E - 0.1 - 0.27, 47.0, 0.0, 270.0), (rst, 'v_corp_lazychair', 35.0, 52.0, 0.0, 180.0),
            (rst, 'v_corp_lazychair', 36.6, 52.0, 0.0, 180.0), (rst, 'v_corp_sidetable', 35.8, 53.0, 0.0, 0.0)]
    out += [(rst, 'v_corp_lazychair', RU0 + 0.45, v, 0.0, 90.0) for v in (23.0, 24.3, 25.6)] + [(rst, 'prop_watercooler', 18.6, 27.9, 0.0, 270.0)]
    ct = (44.8, 50.2)
    out.append((pub, 'v_corp_conftable2', *ct, 0.0, 0.0))
    for u in (43.4, 44.8, 46.2): out += [(pub, 'v_ilev_leath_chr', u, ct[1] - 1.0, 0.0, 180.0), (pub, 'v_ilev_leath_chr', u, ct[1] + 1.0, 0.0, 0.0)]
    for u in (22.0, 26.0, 34.0, 38.0): out.append((pub, 'v_ilev_ph_bench', u, RV0 + 0.5, 0.0, 180.0))
    for v in (27.0, 33.0, 39.0): out.append((pub, 'v_ilev_ph_bench', RU1 - 0.5, v, 0.0, 270.0))
    out += [(pub, 'v_corp_potplant1', u, v, 0.0, 0.0) for u, v in ((RU0 + 0.75, RV0 + 0.8), (RU1 - 0.75, RV0 + 0.8), (RU1 - 0.75, 43.9))]
    out += [(pub, 'prop_watercooler', 42.95, 30.0, 0.0, 90.0), (pub, 'prop_bin_11b', 43.3, 28.5, 0.0, 0.0)]
    return out
