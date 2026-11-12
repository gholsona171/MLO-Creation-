"""Justice Center phase 3, AREA 3: the Police HQ's L1 + L2 as numbers - the 2026-10-31 REDESIGN Antonio approved ("too much open space",
"not enough going on"; plans/area3_redesign/PLAN.md, jc3_redesign_plan.py): dense rooms off narrow corridors, the public side and the
secure side apart. Pure Python: jc3_police_build.py draws them, jc3_police_dress.py furnishes them; the gates, probes and mlo-data read
them. The rooms are rooms of MLO jc_courts; inside an MLO room the named spaces are walled with doors and no portals.
  plobby   public: the lobby (double height) + its NE pocket, the public corridor south to the victim rooms and the press room, the hall
           to the galleria link, the public restrooms (all but the lobby L1 height, L2 offices over the south block)
  pdesk    front of house: the front desk behind the counter (and the property / records windows onto the hall), dispatch, the watch
           commander, copy & supply
  pstaff1  L1 staff side: break room, briefing, fitness, locker rooms (showers inside), evidence (intake, cage, shelving), armory, the
           staff corridor, report writing, patrol equipment, the roll-call corridor
  pstair   the staff stair B1 - L1 - L2
  pstaff2  L2: command (commander, assistant, conference), detectives, IT, training, internal affairs, crime analysis, restrooms,
           records, the L2 east wing over the public south block, quartermaster; the interview suites are rooms of their own
Every partition that meets the west face lands in a gap between its window bays (tests/test_jc3_police.py)."""
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
LOB_W = 32.8                                                              # the lobby's west wall / the front desk's counter wall
GAR_N = -44.4                                                             # the public south block | the roll-call corridor (behind the east colonnade's
                                                                          # closed end, -44.39 .. -43.89)
HALL_S = -13.44                                                           # the restrooms / windows row | the staff side (= a W face gap)
HALL_N = -10.0                                                            # the hall to the galleria (v -10.0 .. -7.2) | the restrooms / windows row
DESK_S = -30.0                                                            # front of house | staff side (south)
DESK_W = 24.0                                                             # front of house | staff corridor (the corridor's east wall)
LOBBY_S = -31.0                                                           # the lobby | the public south block
PUB_E = 34.4                                                              # the public corridor (LOB_W .. 34.4) | victim rooms + press room
NE = (LOB_W, 43.2, -9.1, NI_FACE)                                         # the lobby's NE pocket behind the north face's window bay (39.2 .. 42.9)
TRENCH_N = -47.6                                                          # the garage ramps' trench (L1 storey): v SG .. -48.0, u >= U_FOOT
U_FOOT = 21.47                                                            # (= jc3_pgarage.U_FOOT: the ramps reach B1 there; checked by the tests)
LOBBY = (LOB_W, EG, LOBBY_S, -9.1)                                        # double height
SOUTH = (LOB_W, EG, GAR_N, LOBBY_S)                                       # the public south block (L1), the L2 east wing over it
HALL = (17.5, LOB_W, HALL_N, NI_LINK)
REST = (17.5, 22.0, HALL_S, HALL_N)
REGIONS = {
    'plobby': [LOBBY, NE, SOUTH, HALL, REST],                             # [0] / [1]: double height; the rest L1 height
    'pdesk': [(DESK_W, LOB_W, DESK_S, HALL_N)],
}
TALL = ['lobby']                                                          # plobby's double-height space (walls to CEIL - 0.2)
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
STAFF1 = [(WI, 17.5, HALL_S, NI_LINK), (WI, LOB_W, TRENCH_N, HALL_S), (WI, U_FOOT, SG, TRENCH_N), (LOB_W, EI, TRENCH_N, GAR_N),
          (22.0, DESK_W, HALL_S, HALL_N)]                               # (+ the staff corridor's north end to the hall)
STAFF2 = [(WI, LOB_W, SG, NI_LINK), (LOB_W, EI, SG, GAR_N), SOUTH]          # (+ the L2 east wing over the public south block)
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
# ---------------- named spaces (walls between them, doors without portals: one MLO room each side) ----------------
COR = (22.0, 24.0)                                                        # the staff corridor (u), L1 and L2
G_BRIEF, G_LOCK, G_EVID, G_CAPT = -26.75, -40.05, -48.93, -17.87          # cross walls: west face gap centres
G_BREAK, G_FIT, G_MEN = -13.44, -22.31, -31.18
G_AG = -50.4                                                              # the armory's cage line (issue vestibule | cage)
G_EA, G_EB = -35.62, -40.05                                                # east cross walls: the colonnade's pier gaps (never on its glass)
SB = STAIR_B
SPACES_LOBBY = {   # plobby
    'lobby': [LOBBY, NE], 'public corridor': [(LOB_W, PUB_E, GAR_N, LOBBY_S)],
    'victim room A': [(PUB_E, EG, G_EA, LOBBY_S)], 'victim room B': [(PUB_E, EG, G_EB, G_EA)], 'press room': [(PUB_E, EG, GAR_N, G_EB)],
    'hall': [HALL], "men's restroom": [(17.5, 19.75, HALL_S, HALL_N)], "women's restroom": [(19.75, 22.0, HALL_S, HALL_N)]}
OPEN_LOBBY = {('lobby', 'public corridor'), ('lobby', 'hall')}
SPACES_DESK = {    # pdesk
    'front desk': [(28.0, LOB_W, -26.0, -17.9)], 'dispatch': [(DESK_W, 28.0, -26.0, -17.9)], 'watch commander': [(DESK_W, LOB_W, DESK_S, -26.0)],
    'copy and supply': [(DESK_W, LOB_W, -17.9, HALL_S)], 'property window': [(DESK_W, 28.4, HALL_S, HALL_N)], 'records window': [(28.4, LOB_W, HALL_S, HALL_N)]}
OPEN_DESK = set()
SPACES1 = {   # L1 staff side (pstaff1)
    'break room': [(WI, 17.5, G_BREAK, NI_LINK)], 'briefing room': [(WI, COR[0], G_FIT, G_BREAK)], 'fitness room': [(WI, COR[0], G_BRIEF, G_FIT)],
    "men's locker room": [(WI, SB[0], G_MEN, G_BRIEF), (SB[0], COR[0], SB[3], G_BRIEF)], "men's showers": [(WI, SB[0], -35.62, G_MEN)],
    "women's locker room": [(WI, SB[0], G_LOCK, -35.62), (SB[0], COR[0], G_LOCK, SB[2])],
    'evidence intake': [(16.0, COR[0], -44.49, G_LOCK)], 'evidence cage': [(16.0, U_FOOT, G_EVID, -44.49), (U_FOOT, COR[0], TRENCH_N, -44.49)],
    'evidence shelving': [(WI, 16.0, G_EVID, G_LOCK)], 'armory issue': [(WI, U_FOOT, G_AG, G_EVID)], 'armory': [(WI, U_FOOT, SG, G_AG)],
    'corridor': [(COR[0], COR[1], TRENCH_N, HALL_N)], 'report room': [(COR[1], LOB_W, -41.3, DESK_S)],
    'patrol equipment': [(COR[1], LOB_W, TRENCH_N, -41.3)], 'roll call corridor': [(LOB_W, EI, TRENCH_N, GAR_N)]}
OPEN1 = set()
# the evidence cage's walls are steel mesh (Rockstar's Mission Row armoury mesh, normal_cutout), not block: the cage reads as a cage from
# the intake counter, the store and the armory (2026-11-01, Antonio via the rig shots); doors in them hang in short block frames
MESH1 = {('evidence intake', 'evidence cage'), ('evidence cage', 'evidence shelving'), ('armory issue', 'evidence cage'), ('armory issue', 'armory')}
# (2026-11-01, Antonio: secure rooms read windowless; weapons behind mesh) the armory is a mesh cage behind a 1.4 m issue vestibule,
# entered through a Mission Row cell gate; the secure rooms' west window bays stay glazed outside but are lined solid inside (their
# limbo portal kept: from outside the glazing shows the lining, not a void)
WINDOWLESS = {'pstaff1': ('armory', 'armory issue', 'evidence shelving'), 'pint1': None}   # None: the whole room
DOOR_MODEL = {('pstaff1', 'armory gate'): 'v_ilev_ph_cellgate'}         # inner doors that are not the office door
# restrooms and locker rooms: Rockstar's solid office door, no glass (2026-11-11, Antonio: "you can see into the restroom from the
# hallway": Mission Row's office doors all carry an env-mapped pane that shows a reflection, not the room)
DOOR_MODEL.update({k: 'v_ilev_fib_door1' for k in (('plobby', 'men wc'), ('plobby', 'women wc'), ('pstaff2', 'men wc'), ('pstaff2', 'women wc'),
                                                   ('pstaff1', 'men'), ('pstaff1', 'women'), ('pstaff1', 'men showers'))})

SPACES2 = {   # L2 (pstaff2; the interview suites are rooms of their own)
    "commander's office": [(WI, 17.5, G_CAPT, NI_LINK)], 'executive assistant': [(17.5, COR[0], G_CAPT, NI_LINK)],
    'command conference': [(WI, COR[0], G_BRIEF, G_CAPT)], 'detective lieutenant': [(WI, SB[0], G_MEN, G_BRIEF)],
    'interview prep': [(SB[0], COR[0], SB[3], G_BRIEF)], 'detectives': [(WI, SB[0], G_EVID, G_MEN), (SB[0], COR[0], G_EVID, SB[2])],
    'corridor': [(COR[0], COR[1], SG, NI_LINK)], 'IT room': [(COR[1], LOB_W, -13.0, NI_LINK)], 'training room': [(COR[1], LOB_W, -24.0, -13.0)],
    'internal affairs': [(COR[1], 28.4, DESK_S, -24.0)], 'crime analysis': [(28.4, LOB_W, DESK_S, -24.0)],
    "men's restroom": [(COR[1], LOB_W, -32.75, DESK_S)], "women's restroom": [(COR[1], LOB_W, -35.5, -32.75)],
    'detectives east': [(COR[1], LOB_W, -41.3, -35.5)], 'records': [(COR[1], LOB_W, SG, -41.3)],
    'east corridor': [(LOB_W, PUB_E, GAR_N, LOBBY_S)], 'patrol lieutenant': [(PUB_E, EG, G_EB, LOBBY_S)], "sergeants' office": [(PUB_E, EG, GAR_N, G_EB)],
    'quartermaster': [(LOB_W, EI, SG, GAR_N)]}
OPEN2 = set()
# doors inside a room (no portal): (room, name, floor z, axis, plane, a0) - single GEN leaves, 1.4 m from a0
INNER_DOORS = [
    ('pstaff1', 'break', P1, 'v', G_BREAK, 13.0), ('pstaff1', 'brief', P1, 'u', COR[0], -16.6), ('pstaff1', 'fitness', P1, 'u', COR[0], -25.4),
    ('pstaff1', 'men', P1, 'u', COR[0], -29.6), ('pstaff1', 'men showers', P1, 'v', G_MEN, 16.75), ('pstaff1', 'women', P1, 'u', COR[0], -39.6),
    ('pstaff1', 'evid', P1, 'u', COR[0], -43.0), ('pstaff1', 'cage', P1, 'v', -44.49, 18.6), ('pstaff1', 'shelving', P1, 'u', 16.0, -43.6),
    ('pstaff1', 'arm', P1, 'v', G_EVID, 17.6), ('pstaff1', 'armory gate', P1, 'v', G_AG, 17.9), ('pstaff1', 'report', P1, 'u', COR[1], -35.0), ('pstaff1', 'equip', P1, 'u', COR[1], -46.0),
    ('pstaff1', 'rollcall', P1, 'u', LOB_W, -46.6),
    ('pdesk', 'front', P1, 'u', 28.0, -25.6), ('pdesk', 'watch', P1, 'v', -26.0, 26.3), ('pdesk', 'copy', P1, 'v', -17.9, 25.0),
    ('pdesk', 'property', P1, 'v', HALL_S, 25.0), ('pdesk', 'records', P1, 'v', HALL_S, 30.6),
    ('plobby', 'victim a', P1, 'u', PUB_E, -33.4), ('plobby', 'victim b', P1, 'u', PUB_E, -37.4), ('plobby', 'press', P1, 'u', PUB_E, -42.6),
    ('plobby', 'men wc', P1, 'v', HALL_N, 18.1), ('plobby', 'women wc', P1, 'v', HALL_N, 20.3),
    ('pstaff2', 'commander', P2, 'u', 17.5, -12.6), ('pstaff2', 'assistant', P2, 'u', COR[0], -14.0), ('pstaff2', 'conf', P2, 'u', COR[0], -24.0),
    ('pstaff2', 'prep', P2, 'u', COR[0], -28.4), ('pstaff2', 'lieutenant', P2, 'u', SB[0], -28.9), ('pstaff2', 'detectives', P2, 'u', COR[0], -40.0),
    ('pstaff2', 'it', P2, 'u', COR[1], -10.4), ('pstaff2', 'training', P2, 'u', COR[1], -19.0), ('pstaff2', 'ia', P2, 'u', COR[1], -26.4),
    ('pstaff2', 'analysis', P2, 'v', -24.0, 31.2), ('pstaff2', 'men wc', P2, 'u', COR[1], -32.2), ('pstaff2', 'women wc', P2, 'u', COR[1], -34.9),
    ('pstaff2', 'detectives e', P2, 'u', COR[1], -39.4), ('pstaff2', 'records', P2, 'u', COR[1], -50.0), ('pstaff2', 'east wing', P2, 'u', LOB_W, -39.4),
    ('pstaff2', 'patrol lt', P2, 'u', PUB_E, -33.4), ('pstaff2', 'sergeants', P2, 'u', PUB_E, -42.6), ('pstaff2', 'quartermaster', P2, 'u', LOB_W, -46.6)]
# doors with portals between rooms: (name, from, to, z, axis, plane, a0, kind)
PORTAL_DOORS = [
    ('P_front', 'plobby', None, P1, 'u', FRONT[1], FRONT[0], 'glass pair'),          # to the plaza (an exit portal)
    ('P_link', 'plobby', 'galleria', P1, 'v', LINK[1], LINK[0], 'glass pair'),        # the galleria link
    ('P_desk', 'pdesk', 'pstaff1', P1, 'u', DESK_W, -20.0, 'single'),                 # dispatch -> staff corridor
    ('P_staff', 'plobby', 'pstaff1', P1, 'v', HALL_N, COR[0] + 0.3, 'single'),          # the public hall -> the staff corridor (lockable)
    ('P_stairL1', 'pstair', 'pstaff1', P1, 'u', SB[1], SB_SLAND[0], 'single'),         # stair (L1 south landing) -> the staff corridor
    ('P_stairL2', 'pstair', 'pstaff2', P2, 'u', SB[1], SB_SLAND[0], 'single'),         # stair (L2 south landing) -> the L2 corridor
    ('P_stairB1', 'pstair', 'pdeck', 25.6, 'v', SB[2], SB_LANES[0][0], 'single'),       # stair (B1 south landing) -> the garage
    ('P_int1', 'pint1', 'pstaff2', P2, 'v', -48.93, 11.6, 'single'), ('P_obs1', 'pobs1', 'pstaff2', P2, 'v', -48.93, 14.35, 'single'),
    ('P_obs2', 'pobs2', 'pstaff2', P2, 'v', -48.93, 16.45, 'single'), ('P_int2', 'pint2', 'pstaff2', P2, 'v', -48.93, 19.5, 'single'),
]
# the counters: (name, axis, plane, a0, a1): the front desk's window in the lobby's west wall, and the property / records windows from the
# hall (bullet-resistant glazing, a ledge on each side, a portal between the two rooms through the glass)
COUNTER = (-24.6, -19.4)                                                  # along v in the wall u = LOB_W
COUNTERS = [('front desk', 'u', LOB_W, -24.6, -19.4), ('property', 'v', HALL_N, 24.6, 27.8), ('records', 'v', HALL_N, 29.2, 32.4)]
# ---------------- finishes (the approved board: navy / gold / grey, wood at the front desk and in command) ----------------
# every space's finish (jc3_redesign_plan.FINISH): the build lays its trim bands on each wall face by the space in front of it, the
# dressing sets wall items off the band they hang on. Walls themselves: the lobby granite, plaster in offices, Mission Row block on L1 staff.
FINISH_OF = {
    'plobby': {'lobby': 'lobby', 'public corridor': 'public', 'hall': 'public', 'victim room A': 'office', 'victim room B': 'office',
               'press room': 'command', "men's restroom": 'wet', "women's restroom": 'wet'},
    'pdesk': {'front desk': 'command', 'dispatch': 'office', 'watch commander': 'office', 'copy and supply': 'office',
              'property window': 'public', 'records window': 'public'},
    'pstaff1': {"men's showers": 'wet', 'evidence intake': 'secure', 'evidence cage': 'secure', 'evidence shelving': 'secure',
                'armory': 'secure', 'armory issue': 'secure', 'report room': 'office'},                                  # (the rest: staff)
    'pstaff2': {"commander's office": 'command', 'executive assistant': 'command', 'command conference': 'command', 'IT room': 'secure',
                'corridor': 'staff', 'east corridor': 'staff', 'quartermaster': 'staff', "men's restroom": 'wet', "women's restroom": 'wet'},   # (the rest: office)
}
FINISH_DEFAULT = {'plobby': 'public', 'pdesk': 'office', 'pstaff1': 'staff', 'pstaff2': 'office', 'pint1': 'plain', 'pobs1': 'plain',
                  'pobs2': 'plain', 'pint2': 'plain', 'pstair': None}
# trim bands per finish: (material, bottom, top over the floor (None: up to the ceiling), how deep the shell stands off the wall; built by
# jc3_police_finish). Depth steps of >= 1.3 cm (the sweep reads same-facing faces within 1.2 cm as fighting); bands of one finish never
# overlap in height.
SKIRT = ('skirt', 0.0, 0.1, 0.02)
TRIMS = {
    'lobby':   [SKIRT, ('panel', 0.10, 1.20, 0.035), ('gold', 1.20, 1.23, 0.048), ('navy', 1.23, None, 0.035)],   # wood under navy, gold rail
    'public':  [SKIRT, ('navy', 0.10, 1.10, 0.035), ('gold', 1.10, 1.13, 0.048)],
    'staff':   [SKIRT, ('navy', 0.10, 1.10, 0.035), ('gold', 1.10, 1.13, 0.048)],
    'office':  [SKIRT, ('navy', 0.90, 0.98, 0.035)],
    'command': [SKIRT, ('panel', 0.10, 1.20, 0.035), ('gold', 1.20, 1.23, 0.048), ('navy', 1.23, None, 0.035)],
    'secure':  [('hazard', 0.0, 0.15, 0.02)],
    'wet':     [SKIRT, ('tile', 0.10, 1.80, 0.035), ('navy', 1.80, 1.85, 0.048)],
    'plain':   [SKIRT],
    'accent':  [SKIRT, ('brick', 0.10, None, 0.035)],                  # a brick feature wall (the board's warm accent)
}
# brick feature walls: (room, axis, wall line, the room's side, a0, a1 along the wall)
ACCENTS = [('pstaff1', 'v', G_BREAK, -1, WI, COR[0]), ('pdesk', 'v', DESK_S + 4.0, 1, DESK_W, 28.0), ('pstaff2', 'v', G_MEN, -1, WI, STAIR_B[0]),
           ('pstaff2', 'u', LOB_W, -1, -24.0, -13.0), ('plobby', 'v', GAR_N, 1, PUB_E, EG)]
def face_finish(room, u, v, axis=None, side=0):
    """the finish of the wall face in front of (u, v) facing `side` along `axis`: an accent wall's, else its space's."""
    for r, ax, line, sd, a0, a1 in ACCENTS:
        if r == room and ax == axis and sd == side:
            n, a = (u, v) if ax == 'u' else (v, u)
            if 0.0 <= (n - line) * sd <= 0.6 and a0 - 1e-6 <= a <= a1 + 1e-6: return 'accent'
    return finish_at(room, u, v)
def space_at(room, u, v):
    """the named space of `room` holding (u, v) (None outside every space)."""
    sp = {'plobby': SPACES_LOBBY, 'pdesk': SPACES_DESK, 'pstaff1': SPACES1, 'pstaff2': SPACES2}.get(room, {})
    for k, rs in sp.items():
        if any(r[0] - 1e-6 <= u <= r[1] + 1e-6 and r[2] - 1e-6 <= v <= r[3] + 1e-6 for r in rs): return k
    return None
def finish_at(room, u, v):
    k = space_at(room, u, v)
    return FINISH_OF.get(room, {}).get(k, FINISH_DEFAULT.get(room)) if k else FINISH_DEFAULT.get(room)
def shell_bands(room, u, v, axis, side, F, H):
    """the wall shell's bands (jc_shell) on the wall at (u, v) facing `side` along `axis`: [(material, z0, z1, depth)], z absolute."""
    return [(m, F + z0, F + (z1 if z1 is not None else H), pr) for m, z0, z1, pr in TRIMS.get(face_finish(room, u, v, axis, side), [])]
SHELL_DEPTHS = sorted({pr for f in TRIMS.values() for *_, pr in f})
def trim_proud(room, u, v, z0, z1, axis=None, side=0):
    """how far the trim bands stand off the wall face at (u, v) between z0 .. z1 over the floor (wall items stand off that much more)."""
    f = face_finish(room, u, v, axis, side)
    return max([p for m, a, b, p in TRIMS.get(f, []) if a < z1 and (b is None or b > z0)] or [0.0])
# ---------------- furnishing and dressing: jc3_police_dress.py (Rockstar's police-station props, signs) ----------------
