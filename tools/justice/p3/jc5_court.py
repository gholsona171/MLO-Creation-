"""Justice Center phase 3, AREA 5 (2026-11-11): the courthouse and Government Offices in the BrunX look (plans/area5_courthouse/PLAN.md),
as numbers (pure Python; jc3_tower_build / jc5_dress draw them). Lot frame, z absolute. Replaces area 2's lobby layout and courtroom
dressing (rebuilt from here, nothing layered over the old ones).
  tlobby  the grand lobby (L1-L2): chevron field + white marble, mahogany wainscot, cream marble, cornice, coffered ceiling, chandeliers,
          two Lady Justice statues with flags, the court seal, the Clerk of Courts front desk + rope queue, benches, the treasury board.
  gaud    the auditorium (Government Offices, elections): double height, curtains behind the north glass, a stage, rows of armchairs,
          the ballot booth on the back wall beside the door.
  grec    Government Offices reception: the tax desk counter, waiting chairs, windows north + east.
  gsec    the Security room: the locker, a desk; windowless (curtained glass), its own 3.4 m ceiling.
  mayor   L13: Office of the Mayor (reception at the lifts, the office west of it).   govnr  L25: Office of the Governor (same plan).
Courtrooms (crtA / crtB) and the chambers in rstA / rstB keep their rooms and doors (jc3_tower.floor_plan); only their finish and fittings
come from here."""
import math
import jc3_tower as JT
import p2_plan as PL
LV = PL.B['tower']['levels']
F1 = JT.F1; LOB_CEIL = JT.LOB_CEIL
# ---------------- the Government Offices wing in the lobby's north band ----------------
GW = 41.2                                                              # wall line between the lobby and the wing (0.2 thick, 0.1 each side)
GW_U = 29.2                                                            # auditorium | reception
SEC = (41.6, JT.LB[1], 47.2, JT.LB[3])                                 # the Security room (NE corner, off the reception)
WING = {'gaud': [(JT.LB[0], GW_U, GW, JT.LB[3])],
        'grec': [(GW_U, JT.LB[1], GW, SEC[2]), (GW_U, SEC[0], SEC[2], JT.LB[3])],
        'gsec': [SEC]}
WING_TOP = {'gaud': LOB_CEIL - 0.2, 'grec': LOB_CEIL - 0.2, 'gsec': F1 + 3.4}       # ceiling slab undersides
CURTAINED = {'gaud', 'gsec'}                                           # rooms whose colonnade glass is lined (curtains); the glass is still their window portal
ROOM_NAME = {'gaud': 'JC_GOV_AUDITORIUM', 'grec': 'JC_GOV_RECEPTION', 'gsec': 'JC_GOV_SECURITY', 'mayor': 'JC_MAYOR', 'govnr': 'JC_GOVERNOR'}
WING_DOORS = [('gaud_door', 'tlobby', 'gaud', 'v', GW, 20.3, 1, 'double'), ('grec_door', 'tlobby', 'grec', 'v', GW, 37.4, 1, 'double'),
              ('gsec_door', 'grec', 'gsec', 'v', SEC[2], 43.4, 1, 'single')]           # (name, from, to, axis, plane, a0, into, kind)
# into = the side of the plane the 'to' room is on (+1: +v), as every other door of the MLO: it sets the portal's winding, whose normal
# must point INTO 'to'. (2026-11-11: these three had -1; the game then counted walking in as nothing and walking out as walking in:
# inside the auditorium the camera stayed in the lobby, outside it was 'in' the auditorium - the building vanished. jc6_portal_gate.)
# ---------------- the upper office floors (Mayor L13, Governor L25) ----------------
OFFICE_FLOORS = {'mayor': 13, 'govnr': 25}                             # level numbers (1-based: L13 = LV[12])
def office_F(k): return LV[OFFICE_FLOORS[k] - 1]
OFFS = {'mayor': (24.75, JT.IU1, JT.IV0, JT.CORE[2]),                 # the Mayor's suite: south side of the plate, west edge in the S fin gap 24.4..25.1
        'govnr': (JT.IU0, JT.IU1, JT.IV0, JT.CORE[2])}                 # the Governor's: the whole south side, the corner office (S + W windows)
OFFICE_DESK = {'mayor': (28.5, 26.4), 'govnr': (22.0, 26.3)}           # the desks' centres (the c9_government office points sit on them)
OFF_SPLIT = 32.15                                                      # office | reception: S face fin gap 31.8 .. 32.5
OFF_H = 3.15                                                           # clear height (3.59 floor to floor, 0.4 slab, a little plenum)
LIFT_BOX = (JT.CORE[0], JT.CORE[1], JT.CORE[2], JT.LIFT_BODY)           # the lift bank's body behind the reception's north wall
def office_voids():
    """the volumes phase 2 cuts out of the tower hull for the two suites (p2_plan.tower_voids appends them)."""
    out = []
    for k in OFFICE_FLOORS:
        F = office_F(k); out += [(*OFFS[k], F - 0.0, F + OFF_H + 0.25), (*LIFT_BOX, F, F + OFF_H + 0.25)]
    return out
SEE_OUT_PART = {OFFICE_FLOORS[k]: [OFFS[k]] for k in OFFICE_FLOORS}      # only the suite's bays are see-out on those levels
OFFICE_DOOR = lambda k: (f'{k}_office', k, None, 'u', OFF_SPLIT, 22.6, 1, 'double')
OFFICE_TITLE = {'mayor': ('OFFICE OF THE MAYOR', 'city', 'cle', 'MAYOR'), 'govnr': ('OFFICE OF THE GOVERNOR', 'state', 'ohio', 'GOVERNOR')}
# ---------------- finishes (bands on every lining, z above the floor) ----------------
WAINSCOT = {'tlobby': 1.40, 'gaud': 1.10, 'grec': 1.40, 'gsec': 1.10, 'crt': 2.20, 'chambers': 1.10, 'office': 1.10}
CAP_H = 0.07; PANEL_P = 0.03; CAP_P = 0.055; SKIRT_H = 0.14; SKIRT_P = 0.045
CORNICE = (0.45, 0.10, 0.16)                                           # band height under the ceiling, proud, crown proud
# ---------------- the lobby ----------------
FIELD = (16.6, 33.2, 23.2, 39.4)                                      # chevron field (the hall west of the core); white marble round it
FRONT_DESK = (21.0, 29.0, 25.6, 26.5, 1.08)                            # Clerk of Courts counter (u0, u1, v0, v1, top): public face south (v0)
QUEUE = [(21.5, 24.3, 0.0, 4)]                                         # v_corp_bk_rope chains: (u, v, heading, posts-1)
STATUES = [(15.95, 32.3, 90.0), (34.10, 32.3, 270.0)]                  # (u, v, heading: the figure faces +u / -u) west wall | core west face
LOBBY_FLAGS = [(m, u, v, 90.0 if u < 25 else 270.0) for m, u, v in JT.LOBBY_FLAGS]   # the cloth faces the hall (front -y), hangs along the wall
LOBBY_SEAL = ('jc_courts_seal_court', JT.LU0, 32.3, F1 + 3.6, 1.6)      # (model, wall plane u, v, z of the base, size m) over statue 1
BENCHES = [(19.5, 38.4, 0.0), (26.5, 38.4, 0.0), (44.0, 38.6, 0.0), (45.2, 24.0, 270.0)]   # v_res_fh_benchlong (u, v, heading; front -y)
TREASURY = (30.6, 4.0, 2.2, 1.55)                                      # the treasury board on the wing wall's lobby face: centre u, w, h, centre z rel
LOCKER_SPOT = (46.35, 50.6)                                            # the Security locker point (script): in front of the locker
CHANDELIERS_LOBBY = [(20.5, 27.0), (29.0, 27.0), (20.5, 35.5), (29.0, 35.5), (44.0, 30.0)]
PLACARDS_LOBBY = [('auditorium', ['AUDITORIUM'], 21.6, GW - 0.1, F1 + 2.95, '-v'), ('gov', ['GOVERNMENT', 'OFFICES'], 38.7, GW - 0.1, F1 + 2.95, '-v'),
                  ('clerk', ['CLERK OF COURTS'], 25.0, FRONT_DESK[2], F1 + 0.62, '-v'),
                  ('courts', ['COURTROOMS', 'LEVELS 3 AND 5'], 38.8, JT.CORE[2] - 0.1, F1 + 4.3, '-v')]
# ---------------- the auditorium ----------------
STAGE = (15.0, 28.6, 49.6, JT.LB[3] - 0.5, 0.40)                        # (clear of the curtain pleats)                        # the stage platform (north), height
AUD_ROWS = [(16.3 + 0.95 * j, 43.8 + 1.2 * i) for i in range(4) for j in range(13) if not (5 <= j <= 6)]   # armchairs: 4 rows x 11, centre aisle; 2 m clear inside the door
LECTERN = (21.8, 50.6)
BOOTH = (17.4, 41.62, 180.0)                                           # the ballot booth on the back (south) wall west of the door: its back panel (+y) to the wall, open to the room (+v)
AUD_FLAGS = [('jc_courts_flag_us', 18.2, 51.9, 180.0), ('jc_courts_flag_cle', 25.4, 51.9, 180.0)]
AUD_SEAL = ('jc_courts_seal_city', 21.8, JT.LB[3] - 0.3, F1 + 0.4 + 2.4, 1.4)
CLERK_SPOT = (25.6, 48.6, 180.0)                                      # where the elections clerk stands (script NPC): by the stage, facing the rows
# ---------------- the reception (tax desk) and Security ----------------
TAX_DESK = (33.0, 38.6, 46.2, 47.0, 1.08)                              # counter: public face south (v0), the clerk behind it (north)
TAX_CLERK = (35.8, 47.75, 180.0)                                      # the NPC tax clerk behind the counter, facing the public (-v)
REC_CHAIRS = [(31.0 + 1.0 * k, 42.3, 180.0) for k in range(3)] + [(46.6, 42.6 + 1.0 * k, 270.0) for k in range(3)]   # facing the desk (+v) | the room (-u)
LOCKER = ('ch_prop_ch_service_locker_02a', 46.95, 50.6, 270.0)          # Security: the locker on the east wall
SEC_DESK = (42.3, 44.1, 51.4, 52.3)
# ---------------- the courtroom (relative z; lot u / v) ----------------
CT = dict(well_v=(30.0, 37.7), pilaster_w=0.5, pilaster_p=0.10, pil_v=[25.0, 28.6, 32.2, 35.8, 39.4], tray=1.6, tray_drop=0.45,
          backdrop=(22.3, 28.3, 4.4), seal_z=2.9, seal_size=1.3, flags=[('jc_courts_flag_us', 22.85, 40.55), ('jc_courts_flag_ohio', 27.75, 40.55)],
          chandeliers=[(25.2, 27.0), (25.2, 34.5)], documents=[('doc_us', ('THE CONSTITUTION', 'OF THE UNITED STATES'), 'u0', 27.0),
          ('doc_ohio', ('CONSTITUTION OF THE', 'STATE OF OHIO'), 'u1', 30.4), ('doc_rights', ('THE BILL', 'OF RIGHTS'), 'u0', 37.6)], clock=('v_ret_gc_clock', 30.0, 4.6))
COURT_PLACARD = {'A': ['COURTROOM 3A'], 'B': ['COURTROOM 5B']}
CHAMBERS = {'A': ("JUDGE'S", 'CHAMBERS'), 'B': ('CHIEF JUDGE', 'CHAMBERS')}
