"""Justice Center phase 3, AREA 3: the Police HQ's L1 + L2 (fit_v1: public lobby + bullet-resistant front desk + waiting + desk office
on L1; offices on L2; the garage with its plaza driveway), as numbers. Pure Python: jc3_police_build.py draws them; the gates, the probes
and mlo-data read them. The rooms are rooms of MLO jc_courts (one MLO: the galleria's police link is then an ordinary portal).
Lot frame, z absolute. Police levels are 3.2 m: 16 risers of 0.20 per storey, Rockstar's 0.20 / 0.27 stair.
Rooms:
  plobby   the public lobby inside the east colonnade glass (double height, to 34.8), the front doors (a glazed pair in the glass),
           waiting benches, the front desk's counter window; the public hall west to the galleria link (L1 height).
  pdesk    the desk office behind the bullet-resistant counter (sergeant's desk, dispatch).
  pstaff1  L1 staff side: the staff corridor, the locker room, the briefing room, evidence + armory (walls and doors inside the room).
  pgarage  the vehicle garage behind the east-face roll-up door (double height), 4 bays on the west wall, a staff door.
  pstair   the staff stair L1 -> L2.
  pstaff2  L2: the open office, the captain's office, the conference room, two interview rooms, the corridor.
Every partition that meets the west face lands in a gap between its window bays (checked by tests/test_jc3_police.py)."""
import math, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3.parent / 'p2'), str(P3.parent)]
import p2_plan as PL
import jc3_tower as JT
LV = PL.B['police']['levels']; P1, P2, P3L = LV[0], LV[1], LV[2]          # 28.8 32.0 35.2
SLAB_T = 0.4; CEIL = P3L - SLAB_T                                         # 34.8: the underside of L3's floor
L1_CEIL = P2 - SLAB_T                                                     # 31.6: L1 rooms' ceiling (L2's floor slab 31.6 .. 32.0)
D = PL.B['police']['depth']                                               # 0.45: the facade
WI = PL.B['police']['box'][0] + D                                         # 10.55: the west face's inner plane
NI_LINK = -7.2                                                            # the galleria's wall (v -7.2 .. -6.9): back to back with it
NI_FACE = PL.B['police']['box'][3] - D                                    # -7.65: the north face's inner plane (u > 37.9, not covered)
EG = PL.B['police']['box'][1] - PL.ARC_BACK                               # 42.1: the east colonnade's glass
SG = PL.B['police']['box'][2] + PL.ARC_BACK                               # -56.6: the south colonnade's glass
EI = PL.B['police']['box'][1] - D                                         # 44.65: the east face's inner plane (the garage)
OL = 0.2                                                                  # outer linings
# ---------------- the plan lines ----------------
LOB_W = 32.8                                                              # the lobby's west wall / the desk office's counter wall
GAR_N = -44.4                                                             # lobby | patrol room: behind the east colonnade's closed end (-44.39 .. -43.89; the
                                                                          # colonnade grew a bay south when the garage doors moved - 2026-10-29)
HALL_S = -13.44                                                           # the public hall (to the galleria link) | staff side (= the W face gap)
DESK_S = -30.0                                                            # desk office | staff side (south)
DESK_W = 24.0                                                             # desk office | staff corridor (the corridor's east wall)
NE = (LOB_W, 43.2, -9.1, NI_FACE)                                         # the lobby's NE pocket behind the north face's window bay (39.2 .. 42.9)
TRENCH_N = -47.6                                                          # the garage ramps' trench (L1 storey): v SG .. -48.0, u >= U_FOOT
U_FOOT = 21.47                                                            # (= jc3_pgarage.U_FOOT: the ramps reach B1 there; checked by the tests)
REGIONS = {
    'plobby': [(LOB_W, EG, GAR_N, -9.1), NE, (17.5, LOB_W, HALL_S, NI_LINK)],
    'pdesk': [(DESK_W, LOB_W, DESK_S, HALL_S)],
}
# the police stair B1 - L1 - L2: lanes along v (west lane flights go north, east lane flights go south), landings at both ends; every
# floor's landing is the south one (doors: L1 / L2 east wall into the staff corridor, B1 south wall onto the garage's return aisle)
RISE, GO, RISERS = 0.20, 0.27, 8
STAIR_B = (18.4, 22.0, -35.75, -30.0)
SB_LANES = ((18.55, 20.1), (20.3, 21.85))                                 # west lane, east lane (u); the 0.2 wall between them
SB_MIDW = (20.1, 20.3)
SB_SLAND = (STAIR_B[2] + 0.15, STAIR_B[2] + 1.7)                          # the south landing (v), 1.55 deep
SB_NLAND = (STAIR_B[3] - 0.15 - 1.3, STAIR_B[3] - 0.15)                   # the north half landing (v)
def flights(zb0):
    """the flights from the floor at zb0 to the next (+3.2): up the west lane northward to the north half landing, then up the east lane
    southward to the next floor's south landing. [(v_start, direction, z_bottom, z_top, lane)]"""
    return [(SB_SLAND[1], 1, zb0, zb0 + RISERS * RISE, SB_LANES[0]), (SB_NLAND[0], -1, zb0 + RISERS * RISE, zb0 + 2 * RISERS * RISE, SB_LANES[1])]
def voids():
    """the volumes phase 2's hull hands over above B1 (p2_plan.police_voids imports this and jc3_pgarage.voids): (u0, u1, v0, v1, z0, z1)."""
    return [(WI, LOB_W, SG, NI_LINK, P1, CEIL), (LOB_W, EG, GAR_N, -9.1, P1, CEIL), (NE[0], NE[1], NE[2], NE[3], P1, CEIL),
            (LOB_W, EI, SG, GAR_N, P1, CEIL)]
STAFF1 = [(WI, 17.5, HALL_S, NI_LINK), (WI, LOB_W, TRENCH_N, HALL_S), (WI, U_FOOT, SG, TRENCH_N), (LOB_W, EI, TRENCH_N, GAR_N)]
STAFF2 = [(WI, LOB_W, SG, NI_LINK), (LOB_W, EI, SG, GAR_N)]
# ---------------- doors ----------------
FRONT = (PL.POLICE_FRONT, PL.B['police']['box'][1] - PL.ARC_BACK)        # the front pair: a0 along v in the east glass (p2_plan's number)
LINK = (18.65, NI_LINK)                                                   # the galleria link pair: a0 along u (the reserved 18 .. 22)
# ---------------- the L2 interview suites (Antonio 2026-10-29: one-way mirrors) ----------------
# interview | observation | observation | interview, the mirror walls at u MIR (the interview room sees a mirror, the observation room
# sees the interview room through dark glass: a room-to-room portal); each a room of its own (portals need rooms)
MIR = (14.2, 18.4)
SUITES = {'pint1': (WI, MIR[0], SG, -48.93), 'pobs1': (MIR[0], 16.3, SG, -48.93), 'pobs2': (16.3, MIR[1], SG, -48.93), 'pint2': (MIR[1], 22.0, SG, -48.93)}
MIRROR = [('pint1', 'pobs1', 'u', MIR[0], -1), ('pint2', 'pobs2', 'u', MIR[1], 1)]   # (interview, observation, axis, plane, interview side: -1 = u < plane)
def mirror_heading(side):
    """the mirror panel's heading (lot frame): the panel faces -Y, so heading 90 faces +u, 270 faces -u - into the interview room."""
    return 90.0 if side > 0 else 270.0
def facing(heading, normal=(0.0, -1.0)):
    """a model-space horizontal normal turned by an entity heading (degrees, counter-clockwise): its lot-frame (u, v)."""
    h = math.radians(heading); return (normal[0] * math.cos(h) - normal[1] * math.sin(h), normal[0] * math.sin(h) + normal[1] * math.cos(h))
MIRROR_SPAN = (-55.6, -50.0, P2 + 0.9, P2 + 2.2)                          # the mirror / dark glass: v0, v1, z0, z1
MIRROR_PROP = ('jc_courts_mirror', 1.0, 1.0)                              # our own 1 x 1 m mirror_default panel facing -Y (Tower City's
# tc_prop_mirror recipe, jc3_police_build.export_mirror), its own entity scaled to the span. NOT Rockstar's vw_vwint02_pent_mbt_mirror:
# that model is TWO panels (y +-0.30..0.94, a 0.6 m gap between) facing -x - scaled up it left a see-through strip and, turned with
# +x into the room, showed its back to the interview room (rig 2026-10-30: the interview side read as clear glass into observation)
# ---------------- rooms in the MLO ----------------
KEYS = ['plobby', 'pdesk', 'pstaff1', 'pstair', 'pstaff2', 'pint1', 'pobs1', 'pobs2', 'pint2']
ROOM_NAME = {'plobby': 'JC_POLICE_LOBBY', 'pdesk': 'JC_POLICE_DESK', 'pstaff1': 'JC_POLICE_STAFF_L1', 'pstair': 'JC_POLICE_STAIR',
             'pstaff2': 'JC_POLICE_STAFF_L2', 'pint1': 'JC_POLICE_INTERVIEW_1', 'pobs1': 'JC_POLICE_OBSERVE_1', 'pobs2': 'JC_POLICE_OBSERVE_2',
             'pint2': 'JC_POLICE_INTERVIEW_2'}
TCYC = {k: 'mp_heist_tuner_smshop_default' for k in KEYS}
def west_gaps():
    """the gaps between the west face's window bays (a partition meeting the west face must land in one)."""
    face = next(f for f in PL.face_list('police') if f[0] == 'W')
    bs = sorted({(o[1], o[2]) for o in PL.openings('police', face) if o[0] == 'win'})
    return [(a[1], b[0]) for a, b in zip(bs, bs[1:])]
def west_bays(F):
    face = next(f for f in PL.face_list('police') if f[0] == 'W')
    return [(o[1], o[2], o[3], o[4]) for o in PL.openings('police', face) if o[0] == 'win' and F <= o[3] < F + 3.2]
def north_bays(F):
    face = next(f for f in PL.face_list('police') if f[0] == 'N')
    return [(o[1], o[2], o[3], o[4]) for o in PL.openings('police', face) if o[0] == 'win' and F <= o[3] < F + 3.2]
# ---------------- the staff sides: named spaces (walls between them, doors without portals: one MLO room per side) ----------------
COR = (22.0, 24.0)                                                        # the staff corridor (u), L1 and L2, full length
G_BRIEF, G_LOCK, G_EVID, G_CAPT = -26.75, -40.05, -48.93, -17.87          # cross walls: west face gap centres
G_BREAK = -13.44
SB = STAIR_B
SPACES1 = {   # L1 (pstaff1): name: [(u0, u1, v0, v1)]
    'break room': [(WI, 17.5, G_BREAK, NI_LINK)], 'briefing room': [(WI, COR[0], G_BRIEF, G_BREAK)],
    'locker room': [(WI, SB[0], G_LOCK, G_BRIEF), (SB[0], COR[0], G_LOCK, SB[2]), (SB[0], COR[0], SB[3], G_BRIEF)],
    'evidence': [(WI, U_FOOT, G_EVID, G_LOCK), (U_FOOT, COR[0], TRENCH_N, G_LOCK)], 'armory': [(WI, U_FOOT, SG, G_EVID)],
    'corridor': [(COR[0], COR[1], TRENCH_N, HALL_S)], 'report room': [(COR[1], LOB_W, -41.3, DESK_S)],
    'kit store': [(COR[1], LOB_W, TRENCH_N, -41.3)], 'patrol room': [(LOB_W, EI, TRENCH_N, GAR_N)]}
OPEN1 = set()
SPACES2 = {   # L2 (pstaff2; the interview suites are rooms of their own)
    'captain office': [(WI, COR[0], G_CAPT, NI_LINK)], 'conference room': [(WI, COR[0], G_BRIEF, G_CAPT)],
    'open office': [(WI, SB[0], G_EVID, G_BRIEF), (SB[0], COR[0], G_EVID, SB[2]), (SB[0], COR[0], SB[3], G_BRIEF)],
    'corridor': [(COR[0], COR[1], SG, NI_LINK)], 'open office east': [(COR[1], LOB_W, -41.3, NI_LINK)],
    'records': [(COR[1], LOB_W, SG, -41.3)], 'L2 store': [(LOB_W, EI, SG, GAR_N)]}
OPEN2 = {('corridor', 'open office east')}
# doors inside the staff sides (no portal): (name, floor z, axis, plane, a0) - single GEN leaves
INNER_DOORS = [
    ('brief', P1, 'u', COR[0], -21.0), ('lock', P1, 'u', COR[0], -38.6), ('evid', P1, 'u', COR[0], -46.0), ('arm', P1, 'v', G_EVID, 15.0),
    ('break', P1, 'v', G_BREAK, 13.0), ('report', P1, 'u', COR[1], -35.0), ('kit', P1, 'u', COR[1], -46.0), ('patrol', P1, 'u', LOB_W, -46.6),
    ('capt', P2, 'u', COR[0], -14.0), ('conf', P2, 'u', COR[0], -24.0), ('office', P2, 'u', COR[0], -40.0),
    ('records', P2, 'u', COR[1], -50.0), ('office e', P2, 'u', COR[1], -30.0), ('l2store', P2, 'u', LOB_W, -46.6)]
# doors with portals between rooms: (name, from, to, z, axis, plane, a0, kind)
PORTAL_DOORS = [
    ('P_front', 'plobby', None, P1, 'u', FRONT[1], FRONT[0], 'glass pair'),          # to the plaza (an exit portal)
    ('P_link', 'plobby', 'galleria', P1, 'v', LINK[1], LINK[0], 'glass pair'),        # the galleria link
    ('P_desk', 'pdesk', 'pstaff1', P1, 'u', DESK_W, -20.0, 'single'),                 # desk office -> staff corridor
    ('P_staff', 'plobby', 'pstaff1', P1, 'v', HALL_S, COR[0] + 0.3, 'single'),          # the public hall -> the staff corridor (lockable)
    ('P_stairL1', 'pstair', 'pstaff1', P1, 'u', SB[1], SB_SLAND[0], 'single'),         # stair (L1 south landing) -> the staff corridor
    ('P_stairL2', 'pstair', 'pstaff2', P2, 'u', SB[1], SB_SLAND[0], 'single'),         # stair (L2 south landing) -> the L2 corridor
    ('P_stairB1', 'pstair', 'pdeck', 25.6, 'v', SB[2], SB_LANES[0][0], 'single'),       # stair (B1 south landing) -> the garage
    ('P_int1', 'pint1', 'pstaff2', P2, 'v', -48.93, 11.6, 'single'), ('P_obs1', 'pobs1', 'pstaff2', P2, 'v', -48.93, 14.35, 'single'),
    ('P_obs2', 'pobs2', 'pstaff2', P2, 'v', -48.93, 16.45, 'single'), ('P_int2', 'pint2', 'pstaff2', P2, 'v', -48.93, 19.5, 'single'),
]
# the front desk: the counter in the lobby's west wall (bullet-resistant glazing over it), a pass-through tray
COUNTER = (-24.6, -19.4)                                                  # along v in the wall u = LOB_W
# ---------------- furnishing: Rockstar props (survey/arch_ytyp.json), (room, model, u, v, z above the floor, heading) ----------------
# heading: a prop's back (+y) points to (-sin h, cos h); chairs face -y. Desks: v_corp_officedesk's user side is +y (chair 1.2 m behind).
BENCH, DESK, OCH, BKC, LCH, EXC = 'v_ilev_ph_bench', 'v_corp_officedesk', 'prop_off_chair_05', 'v_corp_bk_chair1', 'v_ilev_leath_chr', 'ex_prop_offchair_exec_01'
SHELF, FCAB, LOCK, SIDE = 'v_corp_offshelfdark', 'v_corp_filecabtall', 'v_ind_rc_locker', 'v_corp_sidetable'
def _desk(room, u, v, h=0.0, monitor=True):
    import math
    t = math.radians(h); bx, by = -math.sin(t), math.cos(t)                # the desk's +y (its user side)
    out = [(room, DESK, u, v, 0.0, h), (room, OCH, u + bx * 1.2, v + by * 1.2, 0.0, h)]
    if monitor: out += [(room, 'prop_monitor_01a', u - bx * 0.1, v - by * 0.1, 0.76, (h + 180.0) % 360), (room, 'prop_keyboard_01a', u + bx * 0.25, v + by * 0.25, 0.76, (h + 180.0) % 360)]
    return out
def furniture():
    L = []
    # L1 public lobby + hall
    L += [('plobby', BENCH, 33.4, v, 0.0, 90.0) for v in (-36.0, -32.0, -15.0)]
    for cu, cv in ((38.0, -34.5), (38.0, -14.5)):
        L += [('plobby', BENCH, cu, cv - 0.5, 0.0, 0.0), ('plobby', BENCH, cu, cv + 0.5, 0.0, 180.0)]
        L += [('plobby', 'ch_prop_ch_planter_01', cu + du, cv, 0.0, 0.0) for du in (-2.35, 2.35)]
    L += [('plobby', m, 33.3, v, 0.0, 90.0) for m, v in (('v_20_flag01', -18.6), ('v_20_flag02', -18.0), ('v_20_flag03', -17.4))]
    L += [('plobby', 'prop_bin_11b', 41.4, -38.0, 0.0, 0.0), ('plobby', 'prop_bin_11b', 41.4, -11.0, 0.0, 0.0)]
    L += [('plobby', 'ch_prop_ch_planter_01', 17.95, -8.1, 0.0, 0.0), ('plobby', 'ch_prop_ch_planter_01', 22.05, -8.1, 0.0, 0.0),
          ('plobby', BENCH, 27.5, -12.85, 0.0, 180.0)]
    # desk office
    L += _desk('pdesk', 28.5, -27.0, 0.0) + _desk('pdesk', 28.5, -16.6, 180.0)
    L += [('pdesk', OCH, 31.3, -22.0, 0.0, 90.0), ('pdesk', 'prop_police_radio_main', 32.35, -20.2, 1.05, 270.0)]
    L += [('pdesk', FCAB, 24.45, v, 0.0, 90.0) for v in (-29.3, -28.7, -28.1)]
    # L1 staff side: briefing, lockers (against the stair's west wall), evidence, armory (behind evidence), break room, report, kit, patrol
    L += [('pstaff1', BKC, u, v, 0.0, 180.0) for v in (-22.0, -20.6, -19.2) for u in (12.6, 13.8, 15.0, 16.2, 17.4, 18.6, 19.8)]
    L += [('pstaff1', 'v_corp_conftable2', 16.2, -15.0, 0.0, 0.0)]
    L += [('pstaff1', LOCK, 17.86, -35.4 + 0.8 * i, 0.0, 270.0) for i in range(7)] + [('pstaff1', BENCH, 14.0, -33.0, 0.0, 90.0)]
    L += [('pstaff1', SHELF, 21.63, -42.6, 0.0, 270.0), ('pstaff1', SHELF, 16.0, -44.5, 0.0, 90.0)]
    L += [('pstaff1', FCAB, u, -40.47, 0.0, 0.0) for u in (12.0, 12.6, 13.2)]
    L += [('pstaff1', LOCK, 20.98, v, 0.0, 270.0) for v in (-55.8, -55.0, -54.2, -53.4, -52.6, -51.8)]
    L += [('pstaff1', 'prop_cabinet_01', u, -56.1, 0.0, 180.0) for u in (12.0, 12.6, 13.2, 13.8)]
    L += [('pstaff1', 'v_res_tt_fridge', 16.95, -8.0, 0.0, 270.0), ('pstaff1', SIDE, 16.95, -9.6, 0.0, 270.0),
          ('pstaff1', 'prop_coffee_mac_01', 17.0, -9.6, 0.88, 270.0), ('pstaff1', 'prop_vend_soda_02', 16.9, -11.4, 0.0, 270.0),
          ('pstaff1', SIDE, 12.6, -9.2, 0.0, 0.0), ('pstaff1', OCH, 12.6, -10.25, 0.0, 180.0), ('pstaff1', OCH, 12.6, -8.15, 0.0, 0.0)]
    L += _desk('pstaff1', 26.5, -38.0) + _desk('pstaff1', 30.5, -38.0)
    L += [('pstaff1', 'prop_watercooler', 24.4, -42.4, 0.0, 90.0)] + [('pstaff1', SHELF, 28.4, v, 0.0, 0.0) for v in (-46.9, -44.0)]
    L += [('pstaff1', LOCK, u, -40.5, 0.0, 0.0) for u in [34.2 + 0.8 * i for i in range(11)]]
    L += [('pstaff1', 'v_corp_conftable2', 38.7, -45.0, 0.0, 0.0)] + [('pstaff1', BKC, u, v, 0.0, h) for u in (37.4, 38.7, 40.0) for v, h in ((-46.0, 180.0), (-44.0, 0.0))]
    # L2: captain, conference, open office (desks clear of the stair), the interview suites, records, open office east, L2 store
    L += [('pstaff2', DESK, 16.0, -12.0, 0.0, 90.0), ('pstaff2', EXC, 14.8, -12.0, 0.0, 90.0),
          ('pstaff2', 'v_corp_lazychair', 17.7, -12.8, 0.0, 270.0), ('pstaff2', 'v_corp_lazychair', 17.7, -11.2, 0.0, 270.0),
          ('pstaff2', SHELF, 16.0, -7.67, 0.0, 0.0), ('pstaff2', 'v_20_flag01', 11.6, -8.2, 0.0, 0.0), ('pstaff2', 'v_20_flag02', 12.2, -8.2, 0.0, 0.0)]
    L += [('pstaff2', 'v_corp_conftable2', 16.3, -22.3, 0.0, 0.0)]
    L += [('pstaff2', LCH, u, v, 0.0, h) for u in (14.8, 16.3, 17.8) for v, h in ((-23.3, 180.0), (-21.3, 0.0))]
    L += [('pstaff2', LCH, 13.95, -22.3, 0.0, 90.0), ('pstaff2', LCH, 18.65, -22.3, 0.0, 270.0)]
    for v in (-46.0, -40.5, -35.0, -29.5): L += _desk('pstaff2', 14.0, v)
    for v in (-46.0, -40.5): L += _desk('pstaff2', 19.0, v)
    for room, u in (('pint1', 12.4), ('pint2', 20.2)):
        L += [(room, SIDE, u, -52.8, 0.0, 0.0), (room, OCH, u, -53.8, 0.0, 180.0), (room, OCH, u, -51.8, 0.0, 0.0)]
    L += [('pobs1', OCH, 15.6, -52.8, 0.0, 270.0), ('pobs2', OCH, 17.1, -52.8, 0.0, 90.0)]
    L += [('pstaff2', SHELF, 28.4, v, 0.0, 0.0) for v in (-44.5, -48.0, -51.5, -55.0)]
    for u in (26.5, 30.5):
        for v in (-34.0, -27.0, -20.0, -13.0): L += _desk('pstaff2', u, v)
    L += [('pstaff2', SHELF, u, -55.8, 0.0, 180.0) for u in (35.5, 38.5, 41.5)]
    return [(r, m, u, v, (P1 if r in ('plobby', 'pdesk', 'pstaff1') else P2) + z, h) for r, m, u, v, z, h in L]
