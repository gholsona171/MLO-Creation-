"""Area 3, the Police HQ's UNDERGROUND GARAGE (Antonio 2026-10-29), as numbers: two street doors in the east face (IN = south, OUT =
north), each with its own straight ramp westward down to B1 (Rockstar / Tower City parking profile: 4 m parabolic vertical curves at both
ends, 1:7 between, playbook 02), and a one-way loop on B1 with no crossing and no head-on meeting:
  IN ramp foot (heading west, v IN_C) -> turn north up the west aisle (east half... the IN lane, x = IN_X) -> north aisle eastbound ->
  east aisle southbound -> return aisle westbound (v RET_V) -> a left U-turn (radius UT_R, centre at the OUT foot's u) -> OUT ramp foot
  (heading east, v OUT_C) -> up and out. The U-turn stays east of the IN lane: the two paths never meet.
Rooms (MLO jc_courts, timecycle carpark_dt1_03): pramp_in, pramp_out (each lane's trench from the door down to B1, open over its length
where the headroom under L1's slab is short), pdeck (B1: parking, the fleet workshop, fuel island, wash bay). Staff: the police stair
runs on down to B1. Separate from jc-jail's prisoner tunnel (u -8.55..35.8, v 25.8..28.8, z 22.4..25.8): no link."""
import sys, math
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3.parent / 'p2'), str(P3.parent)]
import p2_plan as PL
import jc3_police as P
ZB = 25.6                                                                 # B1 floor (slab 25.2 .. 25.6)
CEIL_B = P.P1 - 0.4                                                       # 28.4: B1's ceiling = the underside of L1's slab (2.8 m clear: the van)
RW = 0.3                                                                  # retaining walls (inside the box)
B1 = (P.WI + RW, P.EI - RW, PL.B['police']['box'][2] + PL.B['police']['depth'] + RW, P.NI_FACE - RW)   # 10.85 44.35 -58.85 -7.95
CLEAR = (B1[0] + RW, B1[1] - RW, B1[2] + RW, B1[3] - RW)                  # the deck's clear faces (inside the linings)
ZD = PL.PGARAGE['z0']                                                     # 28.34: the street (+5 cm) at the doors
# ---------------- the two doors and lanes (east face, v) ----------------
LANE_W = 3.6                                                              # clear lane between kerbs / walls
ROLLUP = PL.POLICE_ROLLUP                                                 # the doors are phase 2's facade numbers (p2_plan): the 4 m roll-up rose over L2's floor
DOOR_W = ROLLUP[1] + 0.1                                                  # the opening: the door + 10 cm (doc 06)
IN_C, OUT_C = PL.POLICE_DOOR_C['in'], PL.POLICE_DOOR_C['out']             # lane / door centres (IN south, OUT north)
LANES = {'in': (IN_C - LANE_W / 2, IN_C + LANE_W / 2), 'out': (OUT_C - LANE_W / 2, OUT_C + LANE_W / 2)}
DIV = (LANES['in'][1], LANES['out'][0])                                   # the dividing wall between the lanes (1.3 m)
TRENCH = (-56.6, -47.6)                                                   # the two lanes + their walls, v (south wall behind the south colonnade glass)
DOORS = {'in': (IN_C - DOOR_W / 2, IN_C + DOOR_W / 2), 'out': (OUT_C - DOOR_W / 2, OUT_C + DOOR_W / 2)}
# ---------------- the ramp profile (along u, from the door westward) ----------------
VC = 4.0; SLOPE = 1 / 7                                                   # vertical curves, steepest grade
U_TOP = P.EI                                                              # 44.65: the curve starts at the door line
DROP = ZD - ZB                                                            # 2.74
RUN = 2 * VC + (DROP - VC * SLOPE) / SLOPE                                # 8 + 15.18 = 23.18
U_FOOT = U_TOP - RUN                                                      # 21.47: the ramp meets B1 here
def ramp_z(u):
    """the ramp's surface height at u (U_FOOT <= u <= U_TOP): parabolic curve at both ends, straight 1:7 between."""
    s = U_TOP - u                                                         # distance down the ramp from the door
    if s <= 0: return ZD
    if s >= RUN: return ZB
    if s < VC: return ZD - SLOPE * s * s / (2 * VC)
    if s > RUN - VC: t = RUN - s; return ZB + SLOPE * t * t / (2 * VC)
    return ZD - SLOPE * VC / 2 - SLOPE * (s - VC)
def headroom(u): return P.P1 - 0.4 - ramp_z(u)                            # under L1's slab, if it were there
OPEN_U = (U_FOOT, U_TOP)                                                  # L1's floor is open over the whole ramp (headroom < 2.8 m everywhere but the foot)
# ---------------- the loop on B1 ----------------
UT_R = 5.5                                                                # the U-turn / IN turn radius (path centre line); 6.0 put the
                                                                          # U-turn 2.5 m off the IN lane once the lane cleared the lining
# the test vehicles (jj_plan.VEHICLES sizes): width, length
VEHICLES = {'police3': (2.05, 5.05), 'policet': (2.30, 6.20)}
DRIVE_VEHICLES = ('police3',)          # the loop is gated for the patrol car; the van (policet) does not fit the loop (2026-10-30 sweep):
                                       # Antonio decides (main asked) - jc3_drive_sweep.py prints its result as information
MARG = 0.15                                                               # clearance kept round the body (the swept-path gate's margin)
def swing(r, veh='policet'):
    """how far a vehicle's corners reach past its path line on a turn of radius r: the drive probe turns the body about its centre
    (heading set, jj_probe's heading hold), so the outer corners sweep a circle of hypot(r + w/2, l/2) (+ the margin)."""
    w, l = VEHICLES[veh]; return math.hypot(r + w / 2 + MARG, l / 2 + MARG) - r
IN_R = 6.0                                                                # the IN turn (W -> N) at the ramp foot
IN_X = CLEAR[0] + swing(IN_R)                                             # 13.14: the IN lane's line up the west aisle - the turn's swing off the
                                                                          # LINING's face (11.95 from the wall line: the van pressed the lining)
IN_S = max(IN_C, CLEAR[2] + swing(IN_R))                                  # the deck approach to the IN turn: the lane, unless the swing needs more
WEST_AISLE = (B1[0], 17.35)                                               # IN northbound (west half) + the U-turn's west edge
RET_V = OUT_C + 2 * UT_R                                                  # -38.0: the return aisle's centre line
UT_C = (U_FOOT, OUT_C + UT_R)                                             # the U-turn's centre (21.47, -44.0): it ends heading east at the OUT foot
NORTH_AISLE = (-14.2, B1[3])                                              # v
EAST_AISLE = (38.4, B1[1])                                                # u
RET_AISLE = (RET_V - 3.0, RET_V + 3.0)                                    # v
# parking rows (perpendicular bays 2.6 x 5.0), between the aisles
BAY_W, BAY_D = 2.6, 5.0
ROWS = [  # (u0, u1, v0, v1, facing): the bay's open end faces 'u-' / 'u+'
    (WEST_AISLE[1], WEST_AISLE[1] + BAY_D, RET_AISLE[1], NORTH_AISLE[0], 'u-'),
    (WEST_AISLE[1] + BAY_D + 6.0, WEST_AISLE[1] + 2 * BAY_D + 6.0, RET_AISLE[1], NORTH_AISLE[0], 'u-'),
    (EAST_AISLE[0] - BAY_D, EAST_AISLE[0], RET_AISLE[1], NORTH_AISLE[0], 'u+'),
    (UT_C[0] + UT_R + 1.2, EAST_AISLE[0], TRENCH[1] + 0.2, RET_AISLE[0], 'v+'),            # south of the return aisle, past the U-turn
]
MID_AISLE = (WEST_AISLE[1] + BAY_D, WEST_AISLE[1] + BAY_D + 6.0)            # one-way southbound (north aisle -> return aisle)
def bays():
    """[(u, v, heading, row)] bay centres; heading = the direction a car parked nose-in faces (row -1 = the east wall's parallel bays).
    Bays under the workshop or the stair are left out."""
    out = []
    for k in range(int((PARALLEL[3] - PARALLEL[2]) // 6.0)): out.append(((PARALLEL[0] + PARALLEL[1]) / 2, PARALLEL[2] + (k + 0.5) * 6.0, 180.0, -1))
    for i, (u0, u1, v0, v1, f) in enumerate(ROWS):
        if f in ('u-', 'u+'):
            n = int((v1 - v0) // BAY_W)
            for k in range(n): out.append(((u0 + u1) / 2, v0 + (k + 0.5) * BAY_W, 90.0 if f == 'u-' else 270.0, i))
        else:
            n = int((u1 - u0) // BAY_W)
            for k in range(n): out.append((u0 + (k + 0.5) * BAY_W, (v0 + v1) / 2, 180.0, i))
    def free(b):
        u, v = b[0], b[1]
        return not any(r[0] - 0.01 < u < r[1] + 0.01 and r[2] - 1.0 < v < r[3] + 1.0 for r in (WORKSHOP, P.STAIR_B))
    return [b for b in out if free(b)]
# ---------------- the fleet workshop, fuel, wash (north end of B1) ----------------
WORKSHOP = (MID_AISLE[1], EAST_AISLE[0], -22.4, NORTH_AISLE[0])           # service bays with car lifts, benches, tool chests (rows 2 / 3 there)
FUEL = (WEST_AISLE[1] + 1.0, MID_AISLE[1] - 1.0, NORTH_AISLE[0] + 1.2, NORTH_AISLE[0] + 2.4)   # the fuelling island in the north aisle
WASH = (EAST_AISLE[0] - BAY_D, EAST_AISLE[0], NORTH_AISLE[0] - 4.0, NORTH_AISLE[0])   # the wash bay (the workshop's NE corner, off the east aisle)
PARALLEL = (B1[1] - 2.2, B1[1], -36.0, NORTH_AISLE[0] - 1.0)          # parallel bays along the east wall (6 m each), the east aisle 3.75 m beside them
COLUMNS = [(u, v) for u in (WEST_AISLE[1] + BAY_D, MID_AISLE[1], EAST_AISLE[0] - BAY_D) for v in (-35.0, -27.2, -19.4)]
# ---------------- the drive loop (one definition: the plan test, the plan drawing, the rig drive and the swept-path gate) ----------------
RC = 6.0                                                                  # the loop's corner radius (path centre line)
NORTH_V = CLEAR[3] - swing(RC)                                            # -10.24: the north aisle's line, the corners' swing off the north wall
EAST_U = (EAST_AISLE[0] + PARALLEL[0]) / 2                                # 40.3: the east aisle's lane, beside the parallel bays
def _arc(c, r, a0, a1, n, spd):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n), spd) for k in range(1, n + 1)]
def drive_bay():
    """the row-4 bay the drive test parks in: the easternmost one the van can turn into (radius >= 4 m) straight off the loop's SE
    corner, which ends heading west at u = EAST_U - RC."""
    return max((b for b in bays() if b[3] == 3 and (EAST_U - RC) - b[0] >= 4.0), key=lambda b: b[0])
def bay_r():
    return (EAST_U - RC) - drive_bay()[0]                                  # the turn into / out of the test bay
def loop_route():
    """the drive through the garage as waypoints (lot u, v, speed m/s; negative = reverse), from the street to the street: the IN lane down
    the ramp, the IN turn north (radius UT_R), the west aisle, the NW / NE / SE corners (radius RC), the return aisle west, a left turn
    nose-in into the test bay (radius BAY_R) and back out along the same arc, on west to the U-turn (radius UT_R, centre UT_C), the OUT
    lane up the ramp and out. The points are the body centre's path (the probe turns the body about its centre)."""
    h = math.pi / 2; pts = [(60.0, IN_C, 4.0), (U_TOP + 0.8, IN_C, 3.0), (U_FOOT, IN_C, 3.0), (IN_X + IN_R, IN_S, 3.0)]
    pts += _arc((IN_X + IN_R, IN_S + IN_R), IN_R, -h, -2 * h, 8, 2.5)                       # west -> north (right turn)
    pts += [(IN_X, NORTH_V - RC, 3.0)]
    pts += _arc((IN_X + RC, NORTH_V - RC), RC, 2 * h, h, 6, 2.5)                            # north -> east
    pts += [(EAST_U - RC, NORTH_V, 3.0)]
    pts += _arc((EAST_U - RC, NORTH_V - RC), RC, h, 0.0, 6, 2.5)                            # east -> south
    pts += [(EAST_U, RET_V + RC, 3.0)]
    pts += _arc((EAST_U - RC, RET_V + RC), RC, 0.0, -h, 6, 2.5)                             # south -> west
    bu = drive_bay()[0]; BAY_R = bay_r(); c = (bu + BAY_R, RET_V - BAY_R); v_stop = TRENCH[1] + 0.2 + 0.3 + 3.1   # nose 0.3 m off the bay's end (van 6.2 m)
    pts += _arc(c, BAY_R, h, 2 * h, 6, 1.5) + [(bu, v_stop, 1.0)]                          # west -> south, into the bay (off the SE corner's end)
    pts += [(bu, RET_V - BAY_R, -1.2)] + _arc(c, BAY_R, 2 * h, h, 6, -1.2)                  # back out along the same arc: facing west
    pts += [(UT_C[0], RET_V, 3.0)]
    pts += _arc(UT_C, UT_R, h, 3 * h, 10, 2.5)                                              # the U-turn: west -> south -> east
    pts += [(U_FOOT + 2.0, OUT_C, 3.0), (U_TOP - 0.8, OUT_C, 3.0), (U_TOP + 2.4, OUT_C, 3.0), (60.0, OUT_C, 4.0)]
    return pts
# ---------------- the fit-out: Rockstar props (survey/arch_ytyp.json), (model, u, v, z above B1, heading); all under 2.78 m ----------------
SERVICE_BAYS = [(WORKSHOP[0] + BAY_D / 2, v) for v in (-21.1, -18.5, -15.9)]   # row 2's north bays: a pair of lift platforms each
ISLAND = (FUEL[0], FUEL[1], FUEL[2], FUEL[3], 0.15)                       # the fuel island's kerb (kit concrete, 15 cm)
def fitout():
    L = []
    L += [('m25_2_int_02_post_lift', u, v, 0.0, 0.0) for u, v in SERVICE_BAYS]          # one lift platform per service bay, along the car
    L += [('prop_toolchest_05', 34.4, -21.95, 0.0, 180.0), ('prop_toolchest_04', 35.8, -21.95, 0.0, 180.0), ('prop_compressor_02', 38.0, -21.95, 0.0, 180.0),
          ('prop_tyre_rack_01', 36.6, -22.1, 0.0, 180.0), ('prop_tyre_rack_01', 37.3, -22.1, 0.0, 180.0),
          ('prop_tool_bench02', 33.95, -20.2, 0.0, 0.0), ('prop_car_engine_01', 35.2, -20.1, 0.0, 0.0), ('imp_prop_impexp_parts_rack_01a', 37.3, -19.9, 0.0, 0.0),
          ('prop_carjack', 33.0, -17.2, 0.0, 90.0)]                                  # between service bays 2 and 3
    L += [('v_ind_cs_jerrycan01', u, -18.45, 0.0, 0.0) for u in (33.6, 34.0, 34.4)] + [('prop_barrel_02a', u, -18.6, 0.0, 0.0) for u in (34.95, 35.55)]
    L += [('prop_gas_pump_1a', u, (FUEL[2] + FUEL[3]) / 2, ISLAND[4], 0.0) for u in (FUEL[0] + 2.0, FUEL[1] - 2.0)]
    L += [('prop_bollard_04', u, (FUEL[2] + FUEL[3]) / 2, ISLAND[4], 0.0) for u in (FUEL[0] + 0.3, FUEL[1] - 0.3)]
    L += [('prop_compressor_03', FUEL[1] - 0.6, (FUEL[2] + FUEL[3]) / 2 + 0.1, ISLAND[4], 0.0)]                     # the air pump
    L += [('prop_hose_1', WASH[0] + 0.5, WASH[3] - 0.6, 0.0, 0.0), ('prop_bucket_02a', WASH[0] + 1.2, WASH[3] - 0.5, 0.0, 0.0),
          ('prop_fire_hosereel', WASH[1] - 0.2, WASH[3] - 0.8, 0.0, 270.0)]
    L += [('prop_bollard_04', U_FOOT - 0.4, (DIV[0] + DIV[1]) / 2, 0.0, 0.0), ('prop_cctv_cam_01a', U_FOOT - 0.3, DIV[1], CEIL_B - 0.5 - ZB, 270.0)]
    return [(m, u, v, ZB + z, h) for m, u, v, z, h in L]
# ---------------- rooms in the MLO ----------------
KEYS = ['pdeck', 'pramp_in', 'pramp_out']
ROOM_NAME = {'pdeck': 'JC_POLICE_GARAGE_B1', 'pramp_in': 'JC_POLICE_RAMP_IN', 'pramp_out': 'JC_POLICE_RAMP_OUT'}
TCYC = {k: 'carpark_dt1_03' for k in KEYS}                                # Rockstar's car park timecycle (playbook 02)
def voids():
    """the volume under L1 phase 2's hull hands over: B1 and its retaining walls, from below the hull's bottom (27.8) up to L1."""
    return [(P.WI, P.EI, B1[2] - RW, P.NI_FACE, ZB - 0.4, P.P1)]
def under_ceiling():
    """B1 and its walls up to its ceiling (lot rect + z): phase 2 builds nothing in here - the colonnades' 0.5 m floor slabs (28.3 ..
    28.8) hung 8 cm under B1's ceiling (28.38) into the garage (drawn + collision: the van's roof is 28.30; sweep 2026-10-30)."""
    return [(P.WI, P.EI, B1[2] - RW, P.NI_FACE, ZB - 0.4, CEIL_B)]
