"""Justice Center phase 3: the interiors, as numbers (pure Python: the Blender build, the metadata writer, the render, the gates and
the mlo-data writer all import this one module). Lot frame of work/jc_frame.py (u towards Innocence Blvd, v towards Davis Ave,
z = world z); the MLO 'jc_courts' sits at the lot origin with the lot heading, so MLO-local = lot frame (as the phase 2 exteriors).
Phase 2 is imported read-only (work/p2/p2_plan.py): every face, level and opening comes from there. What phase 3 needs changed in
phase 2 is listed in work/p3/p2_changes.md and is applied only through p2_plan's own hooks (SEE_OUT, MLO_BUILT, openings()).

AREA 1 (this file so far): the atrium galleria = the public entrance, the security checkpoint and the lobby.
  * One room, 'galleria' (the whole L-shaped atrium, 28.8 to the glass roof at 43.1). Exit portals: the three curtain walls (on the
    stone / mullion back plane, the ROOM side of the glass: playbook 02) and the glass roof (under its beams). The neighbours' walls
    (Jail I west, the tower north / east, the police HQ south) are the room's own granite linings, 0.3 m, the depth the exterior's
    roof glass is inset by (p2_facade.atrium_pieces).
  * Main entrance: two pairs of native doors (v_ilev_ph_door01 / 002, Mission Row's glazed front doors) in the east curtain wall,
    each pair in two curtain bays: ENTRY (south pair) and EXIT (north pair). Doors are attached to the east exit portal.
  * Checkpoint: two screening lanes (casino security's X-ray belt ch_prop_baggage_scanner_01a + walk-through detector
    ch_prop_ch_metal_detector_01a), a 2.4 m glass screen line across the hall, a queue of Pacific Standard's rope stanchions
    (v_corp_bk_rope), an exit lane with a guard podium, the security desk (kit counter, Rockstar's props on it).
  * Lobby: granite floor field (Pacific Standard's polished floor marble) with dark bands, the buildings' granite on every wall with
    fins at the tower's bay rhythm, seating islands round planters, flags and the dedication inscription on the Jail I wall.
Doors of the other buildings (tower lift lobby, police HQ link) come with their areas; their spots on the walls are reserved here
(RESERVED) so nothing is placed there now."""
import math, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; WK = P3.parent
sys.path[:0] = [str(WK / 'p2'), str(WK)]
import p2_plan as PL
G = PL.G                                         # 28.8: the galleria floor = the podium / plaza outside the doors
MLO = 'jc_courts'                                # the courts MLO (atrium + tower interiors as they are built)
ROOMS = {'galleria': 1}                          # collision room ids (1..31, 0 = limbo)
ROOM_NAME = {'galleria': 'JC_GALLERIA'}
TCYC = {'galleria': 'mp_heist_tuner_smshop_default'}   # pins exposure (-1 .. 0.1), bloom .25, no sky light (TC LIT_TC, lower case)
# ---------------- the atrium box (phase 2) ----------------
AB = PL.B['atrium']; D = AB['depth']             # 0.3: the atrium's stone depth = our linings' thickness
RA, RB = PL.rects('atrium')                      # (-8.5, 37.9, -7.2, 17.3), (-8.5, 13.7, 17.3, 49.6)
ROOF = AB['roof']                                # 43.1: the glass roof (exterior jc_atrium); beams hang to 42.6
PORTAL_Z = ROOF - 0.55                           # 42.55: the roof portal lies under the beams (they are exterior: drawn through it)
LIN = D
# the room (clear of linings / the stone back plane): A' and B'
UA0, UA1, VA0, VA1 = RA[0] + LIN, RA[1] - D, RA[2] + D, RA[3] - LIN        # -8.2, 37.6, -6.9, 17.0
UB0, UB1, VB0, VB1 = RB[0] + LIN, RB[1] - LIN, VA1, RB[3] - D              # -8.2, 13.4, 17.0, 49.3
SLAB_T = 0.5                                     # floor slab 28.3 .. 28.8
# ---------------- the faces (exterior curtain walls) ----------------
def _face(fid):
    return next(f for f in PL.face_list('atrium') if f[0] == fid)
FACE_E, FACE_S, FACE_N = _face('E0'), _face('S0'), _face('N1')
def curtain(face): return [(o[1], o[2]) for o in PL.openings('atrium', face) if o[0] == 'curtain']
E_BAYS = curtain(FACE_E)                         # 16 bays of 1.456 m, s (= v) -6.6 .. 16.7
# ---------------- the main entrance ----------------
DOOR_L, DOOR_R = 'v_ilev_ph_door01', 'v_ilev_ph_door002'     # leaf 1.30 x 2.30, pivot at the hinge, mid-height (z -1.15 .. 1.15)
LEAF_W, LEAF_H = 1.30, 2.30
DOOR_TOP = G + LEAF_H + 0.10                     # the opening: the door's own top + 10 cm (playbook 07)
ENTRANCES = {'entry': (5, 6), 'exit': (9, 10)}   # curtain bay pairs (index into E_BAYS) that become door openings
def entrance_span(k):
    a, b = ENTRANCES[k]; return (E_BAYS[a][0], E_BAYS[b][1])
DOOR_U = RA[1] - D / 2                           # 37.75: the leaves in the curtain's glass plane
def doors():
    """[(name, model, u, v, z, heading)]: per pair the left leaf hinged at the south jamb (leaf runs +v: heading 90 turns the
    model's +x to +v) and the right leaf at the north jamb (door002's leaf runs -x -> -v)."""
    out = []
    for k in ENTRANCES:
        s0, s1 = entrance_span(k); jamb = ((s1 - s0) - 2 * LEAF_W) / 2
        out.append((f'{k}_l', DOOR_L, DOOR_U, s0 + jamb, G + LEAF_H / 2, 90.0))
        out.append((f'{k}_r', DOOR_R, DOOR_U, s1 - jamb, G + LEAF_H / 2, 90.0))
    return out
def door_openings():
    """the openings phase 2 cuts in the atrium's east curtain (p2_changes.md): (face, kind, s0, s1, z0, z1)."""
    return [('E0', 'door', *entrance_span(k), G, DOOR_TOP) for k in ENTRANCES]
# ---------------- linings (the neighbours' walls, inside the atrium) ----------------
WALLS = {   # name: (axis of the plane, (lo, hi) across, a0, a1 along, the building behind)
    'jail':    ('u', (RA[0], UA0), VA0, VB1, 'jail1'),
    'tower_s': ('v', (VA1, RA[3]), UB1, UA1, 'tower'),          # owns the corner square (13.4 .. 13.7, 17.0 .. 17.3)
    'tower_w': ('u', (UB1, RB[1]), RA[3], VB1, 'tower'),
    'police':  ('v', (RA[2], VA0), PL.B['police']['box'][0], UA1, 'police'),
}
FIN_W, FIN_P = 0.35, 0.20                        # granite fins on the walls (the tower's exterior rib, 0.35 wide), 0.20 proud
SKIRT_H, SKIRT_P = 0.15, 0.02                    # dark granite skirting
RESERVED = {   # wall stretches kept free for the next areas' doors: (wall, a0, a1, z0, z1, what)
    'tower_lobby': ('tower_s', 22.5, 31.5, G, G + 4.2, 'tower lift lobby (area 2)'),
    'police_link': ('police', 18.0, 22.0, G, G + 3.0, 'police HQ public lobby link (area 3)'),
}
def fins(wall):
    """fin centres along a wall: the tower's bay rhythm (7.2 m bays, 0.7 m fins) on the tower walls; 6 m elsewhere; never inside a
    reserved stretch or within 0.6 m of an end."""
    axis, (lo, hi), a0, a1, b = WALLS[wall]
    pitch = 7.9 if b == 'tower' else 6.0
    n = int((a1 - a0 - 1.2) // pitch); x0 = (a0 + a1) / 2 - n * pitch / 2
    out = []
    for i in range(n + 1):
        c = x0 + i * pitch
        if c - FIN_W / 2 < a0 + 0.6 or c + FIN_W / 2 > a1 - 0.6: continue
        if any(r[0] == wall and r[1] - 0.3 < c < r[2] + 0.3 for r in RESERVED.values()): continue
        out.append(c)
    return out
# ---------------- floor ----------------
BAND = 0.6                                       # dark granite band round the room and across the L's joint
def floor_rects():
    """[(u0, u1, v0, v1, kind)] - field (polished marble) and band (dark granite), edge to edge (never overlapping)."""
    out = []
    for (u0, u1, v0, v1) in ((UA0, UA1, VA0, VA1), (UB0, UB1, VB0, VB1)):
        out.append((u0 + BAND, u1 - BAND, v0 + BAND, v1 - BAND, 'field'))
        out += [(u0, u1, v0, v0 + BAND, 'band'), (u0, u1, v1 - BAND, v1, 'band'), (u0, u0 + BAND, v0 + BAND, v1 - BAND, 'band'), (u1 - BAND, u1, v0 + BAND, v1 - BAND, 'band')]
    return out
# ---------------- portals (winding normal INTO roomTo) ----------------
def portals():
    """[(from, to, kind, (axis, plane, a0, a1, z0, z1, into))] - z portals use (axis 'z', plane z, (u0, u1), (v0, v1), into)."""
    return [('galleria', 'limbo', 'east curtain + entrances', ('u', UA1, VA0, VA1, G, PORTAL_Z, 1)),
            ('galleria', 'limbo', 'south curtain', ('v', VA0, UA0, PL.B['police']['box'][0], G, PORTAL_Z, -1)),
            ('galleria', 'limbo', 'north curtain', ('v', VB1, UB0, UB1, G, PORTAL_Z, 1)),
            ('galleria', 'limbo', 'roof A', ('z', PORTAL_Z, (UA0, UA1), (VA0, VA1), 1)),
            ('galleria', 'limbo', 'roof B', ('z', PORTAL_Z, (UB0, UB1), (VB0, VB1), 1))]
DOOR_PORTAL = 0                                  # the doors are attached to portal 0 (drawn from both sides)
# ---------------- the perimeter's collision (the hull band goes to the MLO: p2_plan.mlo_voids) ----------------
def perimeter_col():
    """collision boxes (lo, hi) replacing the atrium's hull in its MLO band (28.8 .. 43.1): each curtain wall's full stone depth
    (doors cut out: the leaves are the collision there), the roof over the whole L."""
    out = []; z0, z1 = G, ROOF
    holes = [(s0, s1) for _, _, s0, s1, _, _ in door_openings()]
    vs = sorted({RA[2], RA[3]} | {x for h in holes for x in h})
    for a, b in zip(vs, vs[1:]):
        mid = (a + b) / 2; inside = any(h0 < mid < h1 for h0, h1 in holes)
        out.append(((UA1, a, DOOR_TOP if inside else z0), (RA[1], b, z1)))
    out.append(((RA[0], RA[2], z0), (PL.B['police']['box'][0], VA0, z1)))                     # south: Jail corner to the police
    out.append(((RB[0], VB1, z0), (RB[1], RB[3], z1)))                                          # north (lawn)
    out.append(((RA[0], RA[2], ROOF - 0.08), (RA[1], RA[3], ROOF)))                             # roof glass (walkable, as the hull's)
    out.append(((RB[0], RA[3], ROOF - 0.08), (RB[1], RB[3], ROOF)))
    return out
# ---------------- the checkpoint ----------------
XRAY, WTMD = 'ch_prop_baggage_scanner_01a', 'ch_prop_ch_metal_detector_01a'    # 1.02 x 3.01 x 1.52 / 1.24 x 1.03 x 2.58, pivots centred on the floor
SCREEN_U = 29.0                                  # the screen line (glass, 2.4 m) across the hall: public side east of it
SCREEN_T, SCREEN_H = 0.10, 2.40
LANES = [(-1.4, 0.35), (2.2, 3.95)]              # (belt centre v, detector centre v) per lane
EXIT_LANE = (6.6, 8.2)                           # the exit lane's gap in the screen (v), the guard podium beside it
EXIT_SPLIT_V = 5.6                               # glass screen along u from the screen line towards the doors: queue | exit
EXIT_SPLIT_U = (SCREEN_U, 34.6)
def screen_gaps():
    """gaps in the screen line (v0, v1): every belt (its tunnel is the barrier) and detector, and the exit lane."""
    g = []
    for bv, dv in LANES: g += [(bv - 0.52, bv + 0.52), (dv - 0.63, dv + 0.63)]
    g.append(EXIT_LANE); return sorted(g)
def screen_runs():
    """the screen line's glass runs (v0, v1) between the gaps (a run under 0.15 m is a mullion only)."""
    out = []; a = VA0
    for g0, g1 in screen_gaps():
        if g0 - a > 0.02: out.append((a, g0))
        a = g1
    out.append((a, VA1)); return out
DESK = dict(u=(23.4, 24.2), v=(-2.6, 2.6), top=1.05, front_u=24.2)      # the security desk: a kit counter (collision), staff on its west
PODIUM = dict(u=(27.2, 27.9), v=(8.5, 9.4))                              # the exit lane's guard podium
# rope queue: chains of v_corp_bk_rope (post at origin, a 1.72 m rope along +x to the next post); (u, v, heading, count)
ROPE = 'v_corp_bk_rope'; ROPE_L = 1.72
QUEUE = [(36.2, 4.9, 180.0, 3),                  # along -u at v 4.9: the entry queue | the exit flow
         (36.2, -3.0, 180.0, 3)]                 # the queue's south side (the lanes' belts load from inside it)
# ---------------- the lobby (secure side) ----------------
BENCH = 'v_ilev_ph_bench'                        # 3.29 m row seat (Mission Row lobby), pivot centred, seats face -y
PLANTER = 'ch_prop_ch_planter_01'                # 0.77 x 0.80 x 2.26 tree in a planter (casino)
PALM = 'apa_mp_h_acc_plant_palm_01'
FLAGS = ['v_20_flag01', 'v_20_flag02', 'v_20_flag03']     # Mission Row's lobby flags on stands (interior-only: v_int_20 ytyp)
ISLANDS = [(4.0, 4.0), (-1.5, 31.0)]             # seating islands: a planter box (kit) with benches on its four sides
ISL_BOX = (2.2, 2.2, 0.55)                       # planter box (u, v, height)
def island_benches(c):
    """four benches round an island, facing out (front -y; heading so the seats face away from the planter)."""
    u, v = c; w, d, _ = ISL_BOX; off = 0.9
    return [(u, v - d / 2 - off, 0.0), (u, v + d / 2 + off, 180.0), (u - w / 2 - off - 0.6, v, 270.0), (u + w / 2 + off + 0.6, v, 90.0)]
WALL_BENCHES = [(UA0 + 0.70, 9.2, 90.0), (UA0 + 0.70, 33.2, 90.0), (UA0 + 0.70, 39.2, 90.0),  # backs to the Jail I wall (clear of its fins), facing +u
                (5.0, VB1 - 0.75, 180.0), (-3.0, VB1 - 0.75, 180.0)]                       # facing the lawn through the north glass
WALL_PLANTERS = [(UA0 + 1.17, 4.5), (UA0 + 1.17, 15.0), (UA0 + 1.17, 28.0), (UA0 + 1.17, 46.5),        # palm bounds 1.52 x 1.79: centres
                 (UB1 - 1.17, 46.5), (UB1 - 1.17, 24.0), (11.2, VA1 - 1.4)]                               # 0.96 m + the fin depth off the wall
INSCRIPTION = dict(wall='jail', a=(14.0, 26.0), z=(36.0, 37.6), lines=['CLEVELAND JUSTICE CENTER'])
FLAG_SPOT = (-7.4, 17.4, 21.6)                   # (u, v0, v1): three flags in front of the inscription
# ---------------- lights ----------------
def wall_lights():
    """(u, v, z, mount) wall washers on every lining (between the fins), two tiers."""
    out = []
    for w, (axis, (lo, hi), a0, a1, b) in WALLS.items():
        F = fins(w); xs = [(p + q) / 2 for p, q in zip(F, F[1:])] if len(F) > 1 else [(a0 + a1) / 2]
        face = hi if (axis == 'u' and lo < 0) or (axis == 'v' and w == 'police') else lo
        sign = {'jail': '-u', 'tower_s': '+v', 'tower_w': '+u', 'police': '-v'}[w]
        for x in xs:
            if any(r[0] == w and r[1] - 0.5 < x < r[2] + 0.5 for r in RESERVED.values()): continue   # the next area lights its own door
            for z in (G + 5.2, G + 10.4):
                out.append((face, x, z, sign) if axis == 'u' else (x, face, z, sign))
    return out
# ---------------- seats (sit points: tested on the rig before shipping) ----------------
def seat_points(model, u, v, z, heading):
    """the sit points of a placed seat (lot frame), heading = the way the sitter faces. v_ilev_ph_bench (measured from the model,
    tools/seat_probe.py): seat pans at z 0.42-0.435 between armrests at x -1.27 / -0.65 / 0 / 0.62 / 1.25 -> 4 seats at
    x -0.96 / -0.32 / 0.31 / 0.94; the backrest's front at y +0.30, seats face -y; sit point 0.22 m in front of it (y +0.08).
    UNTESTED until the rig sit test (feedback-mlo-seating)."""
    if model != BENCH: return []
    h = math.radians(heading); c, s = math.cos(h), math.sin(h); out = []
    for x in (-0.96, -0.32, 0.31, 0.94):
        y = 0.08; out.append((u + x * c - y * s, v + x * s + y * c, z + 0.43, (heading + 180.0) % 360.0))   # facing the prop's -y
    return out
