"""Justice Center phase 3 area 6: the prisoner tunnel (room 'tunnel', JC_PRISONER_TUNNEL) of the MLO jc_courts.
B1 (z 22.8): from Jail I's secure stair (its B1 landing door, u -8.55: Jail I's door, Jail I's MLO jc_jail) east under the galleria and
the tower lobby to the bottom of the courts tower's secure lift shaft, where the secure bank has its B1 stop (jc3_tower.SEC_STOPS; the
cab, front wall and door are jc3_tower_build.sec_car, as at L3 / L5). 2.4 m clear (an escort and a prisoner side by side), 2.8 m high,
painted block, concrete floor, strip lights every 4 m, signs, two cameras.
Why it is a courts room (2026-11-11): built as a room of jc_jail it stretched Jail I's MLO box east over the galleria, the tower lobby and
the auditorium (u -45 .. 35.9, z 22.4 .. 40.3): two interiors' boxes over the same rooms, and the game's room tracking put the camera in
the wrong one (the auditorium void, rig 2026-11-11). Under the courts it is the courts' own: Jail I's box now ends at its own wall.
The doorway to Jail I is a portal to limbo on both sides (each MLO its own); the door leaf is Jail I's (on its portal).
Pure numbers at the top (the gates import them); build() runs in Blender, called by jc3_build.py."""
import importlib.util as _iu
import sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; WK = P3.parent
sys.path[:0] = [str(P3), str(WK / 'p2'), str(WK)]
import p2_plan as PL
import jc3_tower as JT
_sp = _iu.spec_from_file_location('_jj_plan', str(WK / 'jail' / 'jj_plan.py')); JJ = _iu.module_from_spec(_sp); _sp.loader.exec_module(JJ)   # Jail I's door (read only)
KEY = 'tunnel'
ROOM_NAME = {KEY: 'JC_PRISONER_TUNNEL'}
TCYC = {KEY: 'mp_heist_tuner_smshop_default'}
B1 = JT.SEC_B1                                            # 22.8: the floor (30 risers under Jail I's L1: its secure stair)
assert abs(B1 - JJ.B1) < 1e-9, 'the tunnel floor and Jail I secure stair B1 landing differ'
Z1 = B1 + JT.TUN_H                                        # 25.6: the ceiling
SLAB_T, ROOF_T = 0.4, 0.2
EXT_T, INT_T = 0.3, 0.1                                   # linings: 0.3 against the ground, 0.1 at the west end (Jail I's 0.3 behind it)
SL = JT.SLIFT                                             # (31.2, 35.0, 22.8, 25.8): the secure lift shaft
BAND = (SL[3], SL[3] + 3.0)                               # 25.8 .. 28.8: the tunnel's band (2.4 m clear between its 0.3 linings)
WEST = JJ.R['dstair']['rects'][0][1]                      # -8.55: Jail I's secure stair's east edge = the tunnel's west end
RECTS = [(WEST, SL[1] + 0.8, BAND[0], BAND[1]),           # the run
         (SL[0] - 0.2, SL[1] + 0.2, SL[2] - 0.2, BAND[0])]  # the pocket round the cab: its 0.3 linings leave the shaft's 0.1 margins of sec_car
JAIL_SIDE = [(JJ.R['dstair']['rects'][0], INT_T)]          # the west end: 0.1 (Jail I's own 0.3 lining stands behind it)
DOOR = dict(plane=WEST, a0=JJ.DS_DOOR_A, a1=JJ.DS_DOOR_A + JJ.OPEN_W, z0=B1, z1=B1 + JJ.LEAF_H + 0.10)   # Jail I's door opening
CLEAR = (WEST + INT_T, RECTS[0][1] - EXT_T, BAND[0] + EXT_T, BAND[1] - EXT_T)   # the run's clear floor: -8.45 .. 35.5, 26.1 .. 28.5
CAB_C = (JT.SEC_CAB[0] + JT.SEC_CAB[1]) / 2               # 33.1
CAB_EP = JT.SEC_CAB[3] + 0.3                              # 25.5: the cab's front wall face (the landing starts here)
def portal():
    """the doorway to Jail I: this room's portal to limbo (Jail I has its own on the same opening)."""
    return {'from': KEY, 'to': 'limbo', 'kind': 'tunnel jail door', 'P': ('u', DOOR['plane'], DOOR['a0'], DOOR['a1'], DOOR['z0'], DOOR['z1'], -1)}
def hole():
    return (DOOR['plane'] - 0.4, DOOR['plane'] + 0.4, DOOR['a0'], DOOR['a1'], DOOR['z0'], DOOR['z1'])
def zone():
    return [(u0, u1, v0, v1, B1, Z1) for u0, u1, v0, v1 in RECTS]
def lights():
    """(u, v, z, energy, falloff, size): strip lights every 4 m along the run's ceiling."""
    out = []; tv = (CLEAR[2] + CLEAR[3]) / 2; u = CLEAR[0] + 1.5
    while u < CLEAR[1] - 0.5: out.append((u, tv, Z1, 0.45, 6.0, (1.5, 0.12))); u += 4.0
    return out
def signs():
    """(centre, face, w, h, lines, name, bg, fg): the lift sign over its door (in the 0.2 m of wall over the door head), the way signs."""
    return [((CAB_C, CAB_EP, B1 + 2.7), '+v', 2.2, 0.18, ['SECURE ELEVATOR  -  B1'], 'TC sign jc tunnel lift', (30, 30, 34), (232, 214, 170)),
            ((CLEAR[0] + 2.0, CLEAR[3], B1 + 2.3), '-v', 2.6, 0.3, ['COURTS TOWER  >>'], 'TC sign jc tunnel courts', (150, 20, 20), (255, 255, 255)),
            ((CLEAR[1] - 4.5, CLEAR[3], B1 + 2.3), '-v', 2.6, 0.3, ['<<  JAIL I'], 'TC sign jc tunnel jail', (150, 20, 20), (255, 255, 255))]
def props():
    """(model, u, v, base z, heading): the cameras at both ends, an extinguisher on the north wall."""
    return [('prop_cctv_cam_01a', CLEAR[0] + 0.2, CLEAR[3], B1 + 2.5, 135.0), ('prop_cctv_cam_01a', CLEAR[1] - 0.2, CLEAR[3], B1 + 2.5, 225.0),
            ('prop_fire_exting_2a', CLEAR[0] + 12.0, CLEAR[3] - 0.012, B1 + 0.4, 180.0)]
def build(TB):
    """the shell (floor slab, ceiling slab, linings cut by Jail I's doorway), lights, signs; the props and the portal go to TB.OPS
    (jc3_build places and writes them with the tower's). The cab is the secure bank's B1 stop (TB.lifts -> sec_car). -> {room: rects}"""
    import tc_kit as TK
    TB.slab(KEY, RECTS, B1 - SLAB_T, B1, 'conc')
    TB.slab(KEY, RECTS, Z1, Z1 + ROOF_T, 'conc', col=False)
    TB.lining(KEY, RECTS, JAIL_SIDE, B1, Z1, 'block', [hole()], ext_t=EXT_T, int_t=INT_T)
    for u, v, z, e, fo, size in lights(): TK.lamp(KEY, u, v, z, energy=e, falloff=fo, size=size)
    for c, face, w, h, lines, name, bg, fg in signs(): TK.sign(KEY, c, face, w, h, lines, name, bg=bg, fg=fg, emis=False, scale=0.9)
    for m, u, v, z, hd in props(): TB.OPS['props'].append((KEY, m, u, v, z, hd))
    TB.OPS['portals'].append(portal())
    TK.LCOL[KEY] = (1.0, 0.98, 0.94)
    return {KEY: list(RECTS)}
