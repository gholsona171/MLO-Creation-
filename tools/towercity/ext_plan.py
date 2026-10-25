"""Tower City EXTERIOR clean-up (Antonio's exterior review, 2026-10-24): the rules that clear the old Maze Bank block's leftovers
around the tower lot and what we build in their place. Pure Python (no Blender): `py -3 ext_plan.py` writes
  plan/ext_cuts.json   the vanilla-model rules level 0 applies (world coordinates):
     cut    - faces of the named models (regex) inside a polygon and a height band (and, if given, of a material) are deleted:
              l0_cut.py (drawables) and l0_col.py (collision, the 'col' rules)
     clone  - faces of a model inside a source box are copied, shifted, clipped to a target box: Rockstar's own sidewalk, kerb and
              deck-edge barrier continue across the closed branch mouth (drawable + collision, identical shifts)
     move   - faces inside a box are moved (and their top stretched to the deck soffit): the freeway pillar in the parking drive
     ents   - map entities (l0_maps.py) inside a polygon / height band are swapped to tc_empty (ivy on the old car-park walls)
     occl   - extra polygons over which every vanilla occluder goes (l0_occl.ps1)
  plan/ext_build.json  what ext_build.py builds: the plaza paving over the old car-park drives, its bollards / benches.
Lot frame = the tower lot (tower_plan.ORIGIN, HEADING): u along the podium front, -v toward Power St / the freeway off-ramp.

The zones (each found in game + in Rockstar's own geometry, survey/tris_front.json / tris_east.json, tools/tri_dump.py):
  A  SAN ANDREAS AVE BRANCH (items 3 + 7): the old Maze Bank car park's upper entrance - a 10 m road off the San Andreas Ave deck
     (z 43.2) between its west kerb (u 79.0) and the old building (u 66), v -46.2 .. -35.9, with turn arrows on the main deck and
     the old building's walls under it. Removed whole (road, kerb returns, barrier corner, structure west of the deck edge, Maze
     Bank walls); the deck's west edge is closed with the sidewalk + kerb + barrier of the straight stretch south of it
     (v -61 .. -53), cloned north to the planter island at v -35.85 - the deck now ends the same way all along.
  B  POWER ST CAR-PARK ENTRANCE (items 4 + 5): the PARKING block (louvred vent wall, PARKING letters, two mesh roll gates) in
     front of the portico steps and the two kerbed drives between the planters under the off-ramp. The block goes (it is the
     Maze Bank plaza model's part outside the lot), the drives' tarmac / arrows / markings go; the planters, the hedges and the
     off-ramp's pillar stay. Our paving covers the drives (draped on their own surface) and the block's footprint.
  P  THE DRIVEWAY PILLAR (item 8): the west column of the San Andreas deck's pier at v -21.3 stood in front of the parking's IN
     door with its collision cut by the lot. It moves 12.3 m north along the deck edge (clear of both doors and their turns),
     its top stretched to the deck soffit (no cap beam there), with its own collision moved with it, and in its LOD + SLOD1 models
     (the move rule's 'lod' entries, applied by l0_cut_lod.py).
  Final review (2026-10-24): the planter island cut at the deck-edge barrier + the barrier run on beside it; the asphalt wedge at the
  new kerb's north end filled with the cloned sidewalk; the PARKING block's ledge overhanging its south face (B_OVER)."""
import json, math, re
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
ORIGIN = (-78.897, -827.328); HEADING = 69.5
_h = math.radians(HEADING); C, S = math.cos(_h), math.sin(_h)
def W(u, v): return (ORIGIN[0] + u * C - v * S, ORIGIN[1] + u * S + v * C)
def L(x, y): dx, dy = x - ORIGIN[0], y - ORIGIN[1]; return (dx * C + dy * S, -dx * S + dy * C)
def Wd(du, dv): return (du * C - dv * S, du * S + dv * C)          # a lot-frame shift as a world vector
def rect(u0, u1, v0, v1): return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
def inside(poly, u, v):
    c = False; n = len(poly)
    for i in range(n):
        (a0, a1), (b0, b1) = poly[i], poly[(i + 1) % n]
        if (a1 > v) != (b1 > v) and u < (b0 - a0) * (v - a1) / (b1 - a1) + a0: c = not c
    return c
DT1_11 = r'^(hei_)?dt1_11_'                 # every Maze Bank block model (the cut list's dt1_11_* / hei_dt1_11_*)
# ---------------- A: the branch ----------------
KERB_U = 79.05                              # the San Andreas deck's west kerb face (straight north and south of the mouth)
A_V = (-53.0, -35.85)                       # from the straight sidewalk stretch's north end to the planter island's kerb face
A_ALL = rect(66.0, KERB_U, *A_V)            # everything of the branch west of the kerb line
A_STRUCT = rect(66.0, 74.0, *A_V)           # the deck structure west of the deck edge (the barrier line u 73.0)
A_UNDER = rect(66.0, 74.0, -36.0, -30.0)     # the old building's wall corner under the planter island north of the branch (u 72.3 .. 73.1,
                                             # z 31.3 .. 42.9): with the branch gone it hung in the air as a thin slab and a 'pole'
A_MARK = [rect(79.65, 84.75, -52.5, -35.85), rect(85.45, 92.5, -52.5, -35.85)]   # turn dashes /
                                            # arrows on the main deck (the edge line u 79.3 and the lane line u 85.1 stay)
A_SRC = (-61.0, -53.0)                      # the clone source: the straight stretch south of the mouth (no dropped kerb, probed)
A_SHIFTS = [8.0, 16.0, 24.0]                # source length 8 m, three copies reach past the island's kerb (clipped there)
A_CLIP = rect(60.0, KERB_U + 0.001, *A_V)
# ---------------- C: the deck's west side north of the branch (Antonio's shots 71 / 72 / 75, 2026-10-24) ----------------
# North of the branch mouth the San Andreas deck's west side was the old Maze Bank's: a planter island on its edge (cut by the lot,
# hanging past the deck), the Maze Bank plaza on the deck's wide part (lot-cut: the deck's open top showed as dark jagged shapes
# and a red kerb piece floating over our paving), and a second branch - a ramp lane from the Alta St end of the deck down into the
# old building (the 'arrow slab' overhanging the sidewalk), its gore hatching and its own deck. All of it goes; the deck gets the
# same edge as everywhere else on it:
#   * KERB: Rockstar's own kerb, BENT along the main road's west gutter line (K_LINE: the inner edge of his gutter strip, his own
#     vertices, survey/tris_deck.json) - clone kind 'bend' (ext_rules.py) - from the mouth's straight clone (v -35.85) to where the
#     lane's west kerb (BK_LINE) meets the road (v 70): the lane between them becomes sidewalk, tapering out as the lane did
#   * SIDEWALK: our paving (ext_build.py, Rockstar's sidewalk material: sidewalk_mat.py) from the barrier / the lane's west kerb to
#     the bent kerb's back edge, at the kerb's top height
#   * BARRIER: Rockstar's barrier + fascia + soffit, the straight stretch south of the mouth cloned north to V_SPLIT, where the
#     lane's west kerb and its parapet cross the barrier line and carry the deck edge on; the deck west of u 74 goes up to there
def _road_lines():
    """K_LINE (the main road's west gutter, inner edge = the kerb face) and BK_LINE (the lane's west kerb face) from Rockstar's own
    r1_14 triangles: [(u, v, z)]. z = the gutter height at the kerb foot."""
    R = json.load(open(T / 'survey/tris_deck.json')); G, K = [], []
    for r in R:
        if r[1] not in ('im_road_edge_001', 'im_kerbs03'): continue
        P = [L(p[0], p[1]) + (p[2],) for p in r[2:5]]
        if min(p[2] for p in P) >= 40: (G if r[1] == 'im_road_edge_001' else K).append(P)
    def cuts(v, segs):
        out = []
        for P in segs:
            for i in range(3):
                a, b = P[i], P[(i + 1) % 3]
                if (a[1] - v) * (b[1] - v) <= 0 and a[1] != b[1]:
                    t = (v - a[1]) / (b[1] - a[1]); out.append((a[0] + t * (b[0] - a[0]), a[2] + t * (b[2] - a[2])))
        return out
    k, bk = [], []
    for i in range(int((70.0 - A_V[1]) / 1.0) + 1):
        v = min(A_V[1] + i * 1.0, 70.0)
        if -12.0 < v < 20.0 and not (-12.0 < v <= 10.0): continue          # v 10..20: a crossing interrupts the gutter: interpolated
        pred = 79.33 if v < 20 else 79.11 + 0.165 * (v - 20.0)              # the main gutter's run (kerb face), to pick it out
        c = [g for g in cuts(v, G) if abs(g[0] - pred) < 1.2]
        if v <= A_V[1] + 3.5: c = [(KERB_U - 0.02 + (v - A_V[1]) / 3.85 * (79.33 - KERB_U + 0.02), 43.07 + (v - A_V[1]) / 3.85 * 0.12)]
        if c: k.append((round(min(c)[0], 3), round(v, 3), round(min(c)[1], 3)))
        if v >= 47.0:
            b = [x for x in cuts(v, K) if 68.0 < x[0] < pred - 1.0]
            if b: bk.append((round(max(b)[0], 3), round(v, 3), round(max(b)[1] - 0.15, 3)))   # its face foot (road side)
    return k, bk
K_LINE, BK_LINE = _road_lines()
BK_END = 70.0                                # the lane has tapered to the kerb (0.7 m; Rockstar's next road model): our kerb ends on his
BARRIER_IN = 73.44                           # the deck-edge barrier's inner face (im_freeway_barrier001 u 73.05 .. 73.44)
def _bk_at(u):
    for a, b in zip(BK_LINE, BK_LINE[1:]):
        if a[0] <= u <= b[0]: return a[1] + (u - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    raise ValueError(u)
V_SPLIT = round(_bk_at(BARRIER_IN), 3)       # the lane's west kerb crosses the barrier line here (v ~49)
def _k_end():
    """the kerb line, its north end bent onto the lane kerb: from v 54 it runs straight to BK_LINE's end (the lane's taper)."""
    k = [p for p in K_LINE if p[1] <= 54.0]; e = BK_LINE[-1]
    return k + [(e[0], e[1], e[2])]
K_PATH = _k_end()
C_CUT = ([(60.0, A_V[1])] + [(u, v) for u, v, z in K_PATH] + [(u, v) for u, v, z in reversed(BK_LINE) if v >= V_SPLIT - 0.5]
         + [(BARRIER_IN, V_SPLIT), (60.0, V_SPLIT)])                  # road / island / plaza / lane: west of the kerb line (and east of the
                                                                       # lane's kerb north of V_SPLIT) - the kept kerb lies outside it
C_STRUCT = rect(60.0, 74.0, A_V[1], V_SPLIT)  # the deck structure west of u 74 (the clone puts his own edge back: soffit, fascia, barrier)
C_SHIFTS = [8.0 * k for k in range(1, 14)]   # the barrier source (8 m) tiled from the mouth to V_SPLIT
BR_CLIP = rect(60.0, 74.001, A_V[0], V_SPLIT)
BR_COL_CLIP = rect(60.0, BARRIER_IN + 0.001, A_V[1], V_SPLIT)              # the barrier's collision north of the mouth (the mouth's own
                                                                       # comes with the sidewalk clone, whose source reaches the barrier)
KERB_SRC = rect(78.4, KERB_U + 0.001, *A_SRC)  # the kerb strip of the straight stretch: kerb top + face, 0.65 m behind the face line
KERB_W = KERB_U - 78.4
KERB_FOOT_Z = 43.07                            # its foot (the gutter) along the source stretch (survey/tris_deck.json)
def c_kerb_back():
    """the bent kerb's back edge (lot frame): K_PATH moved KERB_W to its left (west), with the kerb TOP height (foot + 0.15)."""
    out = []
    for i, (u, v, z) in enumerate(K_PATH):
        a = K_PATH[max(i - 1, 0)]; b = K_PATH[min(i + 1, len(K_PATH) - 1)]
        du, dv = b[0] - a[0], b[1] - a[1]; L_ = math.hypot(du, dv); nu, nv = -dv / L_, du / L_          # left of the path = west
        out.append((round(u + nu * KERB_W, 3), round(v + nv * KERB_W, 3), round(z + 0.15, 3)))
    return out
def c_paving():
    """our paving (ext_build.py) between the deck edge and the bent kerb's back: [(u, v, z)] outline, z = the kerb top beside it.
    West side: the barrier's inner face to V_SPLIT, then the lane's west kerb (BK_LINE, its top) to the taper's end."""
    kb = c_kerb_back(); bk = [(u, v, z + 0.15) for u, v, z in BK_LINE if v >= V_SPLIT]
    zw = lambda v: min(kb, key=lambda p: abs(p[1] - v))[2]
    west = [(BARRIER_IN, A_V[1], zw(A_V[1])), (BARRIER_IN, V_SPLIT, zw(V_SPLIT))] + bk
    return kb + list(reversed(west))
# under the branch: the old car park's down-ramp pit (to z 15.9, outside the lot, drawn by the removed car-park interior only) between
# the lot edge and Low Power St's sidewalk (its west edge u 72.6 under the deck): our ground closes it at the sidewalk's height
A_PATCH = [(71.55, -32.66), (72.58, -32.43), (72.58, -48.3), (72.15, -49.30), (69.07, -47.46), (68.79, -39.56)]
A_PATCH_Z = [(-32.4, 31.40), (-36.0, 31.30), (-40.0, 31.20), (-45.0, 31.10), (-49.3, 30.95)]     # the sidewalk's edge (probed, collision)
def patch_z(u, v):
    t = A_PATCH_Z
    if v >= t[0][0]: return t[0][1]
    for (v0, z0), (v1, z1) in zip(t, t[1:]):
        if v1 <= v <= v0: return z0 + (v - v0) * (z1 - z0) / (v1 - v0)
    return t[-1][1]
# ---------------- B: the Power St entrance ----------------
NOTCH_SOUTH = -64.45                        # the PARKING block's south face is v -64.4; the planters start at v -64.5
STEP_FOOT = -62.82; STEP_U = 22.9           # our portico steps (l3_build: LAND - 6 GO; PORT + PIER_W + 0.6): first riser line, east end
B_BLOCK = [(1.0, -58.0), (36.0, -58.0), (36.0, NOTCH_SOUTH), (1.0, NOTCH_SOUTH)]          # the block + its walls / gates / letters
B_ENTS = rect(1.0, 36.0, -66.0, -58.0)      # ivy tops on the block (z 36.5)
B_OVER = rect(1.0, 36.0, -65.6, NOTCH_SOUTH)  # the block's louvre wall ledge + its roof-planter lip overhang its south face by up to 0.95 m
                                              # (dt1_11 'window_wall' z 34.95 .. 36.52, 'ground_stones02' z 36.2): left by B_BLOCK, they
                                              # showed as dark wedges in front of the podium east of the portico (final review, 2026-10-24).
                                              # Above z 33 only: the planters (z 28.6 .. 30.9) and hedges (to 31.8) under it stay.
# ---------------- F: the Alta St footbridge (Antonio's shot 74, 2026-10-24) ----------------
# Rockstar's footbridge from the bank's upper terrace across Alta St (dt1_10_build1: deck, side panels, low walls; its rails
# dt1_10_build1_rail2; collision dt1_10_0) landed on the old Maze Bank's deck plaza at v 58 (z 43.2). That plaza is gone; the bridge
# ended in mid-air 3 m off our podium's north wall. Connecting it would need a door + landing into the podium 3.6 m under its roof
# (no room there to take it), so the SPAN goes (v 54 .. 98.65, the bank terrace's planter row): the bank keeps its own upper
# terrace, its planter row along the street and its landing (v 102.9 .. 109). Its LOD (dt1_10_build1_lod = hash_1977f283 in
# dt1_10_slod_children.ydd) and SLOD (dt1_10_slod = hash_0c19b59c in dt1_lod_01_02_09_10_children.ydd) lose the same faces
# (l0_cut_lod.py 'lodcut'). The Maze Bank plaza's landing remnant goes too.
F_SPAN = rect(26.5, 33.5, 54.0, 98.65)
F_MATS = r'rsn_ground_0001|walls_01\.001|windows_03|mc_wall|logo'      # the bridge's own materials (never the terrace's yk_wall / ground_0002)
F_LAND = rect(25.0, 35.0, 55.0, 70.0)
# ---------------- P: the pillar ----------------
PIL_C = (75.91, -21.31); PIL_R = 1.6        # its faces: u 74.6 .. 77.2, v -22.6 .. -20.0, z 31.59 .. 41.8 (fwy02 + its decal model)
PIL_DV = 12.3                               # to v -9.0: 8.5 m north of the IN door's jamb (v -17.5), on the same deck edge line
PIL_Z = (31.0, 41.85)
SOFFIT = 42.43                              # the deck's underside there (fwy02 'mh_bridge_base01_striped'); the pier cap beam ends at v -19.0
GROUND_DZ = 0.25                            # the street at the new spot is 0.25 m higher (31.84 vs 31.59, probed)
def rules():
    W_ = lambda poly: [[round(c, 4) for c in W(u, v)] for u, v in poly]
    cut = [
        {'name': 'A branch: Maze Bank leftovers', 'models': DT1_11, 'poly': W_(A_ALL), 'z': [10.0, 60.0], 'col': True, 'col_files': 'dt1_11'},   # + the pit's walls
        # (collision: the Maze Bank block's files only - the street's sidewalk under the deck is in the road files and stays)
        {'name': 'A island: old walls under it', 'models': DT1_11, 'poly': W_(A_UNDER), 'z': [10.0, 43.05], 'col': True, 'col_files': 'dt1_11'},
        {'name': 'A branch: road, kerbs, decals', 'models': r'^dt1_rd1_r1_(14|ovly_00)$', 'poly': W_(A_ALL), 'z': [38.5, 60.0], 'col': True},
        {'name': 'A branch: structure + barrier corner', 'models': r'^dt1_rd1_(fwy02|r2_fwy_ovly_02)$', 'poly': W_(A_STRUCT), 'z': [38.5, 60.0], 'col': True},
        {'name': 'A turn dashes / arrows on the deck', 'models': r'^dt1_rd1_r1_(14|ovly_00)$', 'polys': [W_(p) for p in A_MARK], 'z': [42.5, 44.0], 'mat': 'marking', 'col': False},
        {'name': 'C deck west side: island, plaza, lane, gore', 'models': DT1_11 + r'|^dt1_rd1_r1_(14|ovly_00)$', 'poly': W_(C_CUT), 'z': [40.5, 47.0], 'col': True},
        {'name': 'C deck structure west of the new edge', 'models': r'^dt1_rd1_(fwy02|r2_fwy_ovly_02)$', 'poly': W_(C_STRUCT), 'z': [38.5, 60.0], 'col': True},
        # L (2026-10-24, Antonio's shots 71 / 77 / 81): inside the lots our slab is the only ground. Rockstar's street models that are cut
        # by their own rules only (footprint / ext_only) kept their faces under the slab: his old driveway kerb and darker sidewalk poked
        # through it (dark jagged patches, a red kerb piece floating). Their street-level faces inside the lots go; decks above stay.
        {'name': 'L lot ground: street models under the slab', 'models': r'^dt1_rd1_r1_(12|14|ovly_00|ovly_23)$',
         'polys': [[[round(c, 4) for c in p_] for p_ in q] for q in json.load(open(T / 'plan/lot_polys.json')).values()], 'z': [20.0, 38.5], 'col': False},
        {'name': 'F footbridge: deck, panels, walls', 'models': r'^dt1_10_build1$', 'poly': W_(F_SPAN), 'z': [41.95, 48.0], 'mat': F_MATS, 'col': False},
        {'name': 'F footbridge: its collision', 'models': r'(?!)', 'poly': W_(F_SPAN), 'z': [41.0, 48.0], 'col': True, 'col_files': 'dt1_10'},   # (collision materials are not drawable ones)
        {'name': 'F footbridge: its walk-on over the planter row', 'models': r'(?!)', 'poly': W_(rect(26.5, 33.5, 98.65, 102.85)), 'z': [43.0, 48.0],
         'col': True, 'col_files': 'dt1_10'},          # (an invisible deck at 43.2 over the bank's planters, 0.3 m over their tops: it led onto the span)
        {'name': 'F footbridge: rails', 'models': r'^dt1_10_build1_rail2$', 'poly': W_(F_SPAN), 'z': [41.0, 48.0], 'col': False},
        {'name': 'F footbridge: the old plaza landing', 'models': DT1_11, 'poly': W_(F_LAND), 'z': [40.0, 48.0], 'col': True, 'col_files': 'dt1_11'},
        {'name': 'B PARKING block', 'models': DT1_11, 'poly': W_(B_BLOCK), 'z': [20.0, 60.0], 'col': True, 'col_files': 'dt1_11'},
        {'name': 'B PARKING block: overhang', 'models': DT1_11, 'poly': W_(B_OVER), 'z': [33.0, 60.0], 'col': True, 'col_files': 'dt1_11'},
        {'name': 'B drives: all of them (tarmac, kerbs, strips, drains, dropped kerbs, paint)', 'models': r'^dt1_rd1_r1_(12|ovly_23)$', 'poly': W_(B_CUT), 'z': [28.0, 31.6], 'col': False},
    ]
    clone = [
        {'name': 'A deck edge: sidewalk + kerb', 'models': r'^dt1_rd1_r1_14$', 'src': W_(rect(72.9, KERB_U, *A_SRC)), 'z': [42.5, 44.6],
         'shifts': [list(Wd(0.0, s)) for s in A_SHIFTS], 'clip': W_(A_CLIP), 'col': True},
        {'name': 'A deck edge: barrier + fascia', 'models': r'^dt1_rd1_fwy02$', 'src': W_(rect(70.0, 74.0, *A_SRC)), 'z': [38.5, 44.6],
         'shifts': [list(Wd(0.0, s)) for s in C_SHIFTS], 'clip': W_(BR_CLIP), 'col': False},      # the mouth + north to the lane's kerb
        {'name': 'C deck edge: barrier collision', 'models': r'(?!)', 'src': W_(rect(72.9, BARRIER_IN + 0.2, *A_SRC)), 'z': [42.5, 44.6],
         'shifts': [list(Wd(0.0, s)) for s in C_SHIFTS], 'clip': W_(BR_COL_CLIP), 'col': True},   # collision only (no drawable matches)
        {'name': 'C kerb along the road (bent)', 'models': r'^dt1_rd1_r1_14$', 'src': W_(KERB_SRC), 'z': [42.5, 44.6], 'col': True,
         'bend': {'a': list(W(KERB_U, A_SRC[0])), 'b': list(W(KERB_U, A_SRC[1])), 'z0': KERB_FOOT_Z,
                  'path': [list(W(u, v)) + [z] for u, v, z in K_PATH], 'step': 0.5}},     # his kerb, bent along the road's gutter line
    ]
    clone.append({'name': 'B the street kerb across the old mouths (bent onto the kerb line)', 'models': r'^dt1_rd1_r1_12$', 'src': W_(B_KERB_SRC), 'z': [28.0, 31.6], 'col': True,
                  'bend': {'a': list(W(44.0, KV(44.0))) + [KZ(44.0)], 'b': list(W(52.0, KV(52.0))) + [KZ(52.0)], 'z0': None,
                           'path': [list(W(u, KV(u))) + [KZ(u)] for u in (B_U[0], B_U[1])], 'step': 0.5}})
    move = [{'name': 'P driveway pillar', 'models': r'^dt1_rd1_(fwy02|r2_fwy_ovly_02)$', 'centre': list(W(*PIL_C)), 'r': PIL_R, 'z': list(PIL_Z),
             'mat': 'wall_concrete32|pilar|fuckedup|glue',            # the column, its base and its decals - never the cap beam over it
             'shift': list(Wd(0.0, PIL_DV)) + [GROUND_DZ], 'top': [41.7 + GROUND_DZ, SOFFIT + 0.02],
             'col': True, 'col_z': [31.0, 40.8], 'col_nz_max': 1.0,    # collision: the column + its base under the cap beam (40.87) only
             # its LOD models move with it (final review 2026-10-24: from a distance the deck's LOD still drew the column at its old spot).
             # fwy02's LOD (dt1_rd1 'hash_d50b466a', lodDist 400, in dt1_rd1_r1f_slod1_children.ydd: column 'im_wall_concrete32_lod' +
             # base 'dt1_05_rsn_dc_pilar_0002_lod', top 41.59) and the SLOD1 over it ('dt1_rd1_r1f_slod1', lodDist 1000, in
             # dt1_lod_rd_children.ydd: 12 side triangles, one material, z 31.33 .. 41.59) - l0_cut_lod.py applies these.
             'lod': [{'names': ['hash_d50b466a'], 'mat': 'wall_concrete32|pilar', 'nz_max': 1.0, 'top': [41.5 + GROUND_DZ, SOFFIT + 0.02]},
                     {'names': ['dt1_rd1_r1f_slod1'], 'mat': None, 'nz_max': 0.5, 'top': [41.5 + GROUND_DZ, SOFFIT + 0.02]}]}]
    ents = [{'name': 'A ivy on the old walls', 'poly': W_(A_ALL), 'z': [32.0, 41.0]}, {'name': 'B ivy on the block', 'poly': W_(B_ENTS), 'z': [32.0, 41.0]}]
    occl = [W_(A_ALL), W_(A_UNDER), W_(C_CUT), W_(C_STRUCT), W_(B_BLOCK), W_(B_OVER), W_(B_CUT), W_(F_SPAN)]
    lodcut = [{'name': 'F footbridge (LOD + SLOD)', 'names': ['hash_1977f283', 'hash_0c19b59c'], 'poly': W_(F_SPAN), 'z': [41.0, 48.0]},
              {'name': 'C deck past its new edge (LOD + SLOD1)', 'names': ['hash_d50b466a', 'dt1_rd1_r1f_slod1'], 'poly': W_(rect(60.0, 73.0, A_V[1], V_SPLIT)), 'z': [38.5, 47.0]}]
    FOOTW = [q for v in json.load(open(T / 'plan/footprint_cuts.json')).values() for q in v]     # our own outlines (podium wing, apron, bridge mouth)
    keep_col = [{'name': n, 'tris': t, 'except': FOOTW} for n, t in json.load(open(T / 'survey/kept_features.json')).items()]   # tools/kept_features.py
    return {'_note': 'written by work/ext_plan.py - do not edit by hand', 'cut': cut, 'clone': clone, 'move': move, 'ents': ents, 'occl': occl, 'keep_col': keep_col, 'lodcut': lodcut,
            'ext_only': ['dt1_10_build1', 'dt1_10_build1_rail2', 'dt1_rd1_fwy02', 'dt1_rd1_r2_fwy_ovly_02', 'dt1_rd1_r1_12', 'dt1_rd1_r1_ovly_23'],     # cut by these rules only (never by the lot)
            }
# ---------------- the B plaza (rebuilt 2026-10-24, Antonio's shots 77 - 80) ----------------
# The first pass paved only the drives' own tarmac at road level and kept everything else of them: the drives' kerbs (red-painted
# slivers out of the planter bases), their drain trenches, the sidewalk strips between them, the dropped kerbs at the mouths - and our
# paving lay over the lot slab where the two met (seams), a different grey from Rockstar's. Now the old drives are ONE plaza: every
# face of the drive model inside B_CUT goes; one paving (Rockstar's own sidewalk material, sidewalk_mat.py) covers it at the street's
# sidewalk height; the street keeps its kerb across the old mouths (his kerb, cloned from the straight stretch east of them and laid
# on the kerb line); the lot slab has a hole where the plaza is (one surface, never two). The planters stay whole (their collision
# too: survey/kept_features.json).
def KV(u): return -77.60 + (u + 2.9) * 0.0154          # Power St's kerb face line (lot frame v), fitted on his kerb's foot vertices
def KZ(u): return 29.20 + (u + 2.9) * 0.01495          # its foot (gutter) height                 (u -16.6 .. 64: survey/tris_front.json)
KERB_TOP = 0.15; KERB_BACK = 0.28                      # his kerb: 15 cm high, 28 cm from face to back (Power St, u 44 .. 52)
B_U = (3.0, 40.5)                                      # the old drives' mouths, between Rockstar's sidewalk either side
def plaza_z(u, v): return KZ(u) + KERB_TOP              # the plaza: the kerb's top, level across (the street rises 1.5 % east)
B_PLAZA = [(B_U[0], KV(B_U[0]) + KERB_BACK), (B_U[1], KV(B_U[1]) + KERB_BACK), (B_U[1], NOTCH_SOUTH), (B_U[0], NOTCH_SOUTH)]
B_CUT = [(B_U[0], KV(B_U[0]) + 0.02), (B_U[1], KV(B_U[1]) + 0.02), (B_U[1], -61.0), (B_U[0], -61.0)]   # (his kerb face south of it stays)
B_KERB_SRC = rect(44.0, 52.0, KV(48.0) - 0.15, KV(48.0) + KERB_BACK + 0.05)
B_MOUTH_V = KV(20.0) + KERB_BACK                        # (the bollards stand 0.45 m behind the kerb's back)
def _lot_edge_u(v, a=(0.5, -66.7), b=(3.4, -60.3)):              # the west lot's edge here (plan/lot_polys.json, lot frame)
    return round(a[0] + (v - a[1]) / (b[1] - a[1]) * (b[0] - a[0]), 3)
NOTCH = [(1.50, NOTCH_SOUTH), (34.15, NOTCH_SOUTH), (33.24, -62.99), (26.81, -60.06), (STEP_U, -60.08), (STEP_U, STEP_FOOT + 0.10),
         (_lot_edge_u(STEP_FOOT + 0.10), STEP_FOOT + 0.10), (_lot_edge_u(-63.85), -63.85), (1.97, -63.85)]
# (2026-10-24, Antonio's shot 80: the notch stopped at the L planter's corner (u 4.65) - between the planter and the first riser a
# 2.7 x 1 m strip had nothing drawn and no floor: a hole down to the void. It now runs along the lot edge to the steps' foot.)   # the block's footprint outside the lot, in front of / beside the steps;
                                                                     # its outline follows the lot edge (plan/lot_polys.json west) and stops
                                                                     # 10 cm under the first riser; west of the drive it stops at the L planter
def notch_z(u, v):
    """the notch paving: the plaza's height along its south edge; in front of the steps it eases to the first riser's foot
    (29.40 + 0.02) so the bottom step keeps its full rise; beside them it rises 1 % toward the building."""
    z0 = plaza_z(min(max(u, B_U[0]), B_U[1]), NOTCH_SOUTH); t = (v - NOTCH_SOUTH)
    k = min(max(t / (STEP_FOOT - NOTCH_SOUTH), 0.0), 1.0); zw = z0 + (29.42 - z0) * k
    ze = z0 + 0.01 * t
    w = min(max((u - STEP_U) / 2.0, 0.0), 1.0); return zw + (ze - zw) * w
def b_ground_z(u, v):
    """our paving's top in the B area (lot frame), None outside it - for lot_ground.py's edge samples."""
    if inside(NOTCH, u, v): return notch_z(u, v)
    if inside(B_PLAZA, u, v): return plaza_z(u, v)
    return None
def bollards():
    """bollards 0.45 m behind the kerb's back, 1.6 m apart, across each old mouth: [(u, v)]"""
    out = []
    for u0, u1 in ((5.2, 15.2), (25.4, 38.4)):
        n = int((u1 - u0) / 1.6) + 1; d = (u1 - u0) / (n - 1)
        out += [(round(u0 + i * d, 3), round(KV(u0 + i * d) + KERB_BACK + 0.45, 3)) for i in range(n)]
    return out
BENCHES = [(10.2, -68.5, 180.0), (28.6, -68.0, 180.0)]   # (u, v, heading in the lot frame): seat facing -v (the street)
def build_spec():
    return {'_note': 'written by work/ext_plan.py - do not edit by hand', 'origin': list(ORIGIN), 'heading': HEADING,
            'plaza': B_PLAZA, 'notch': NOTCH, 'bollards': [[u, v, round(plaza_z(u, v), 3)] for u, v in bollards()],
            'benches': [[u, v, round(plaza_z(u, v), 3), h] for u, v, h in BENCHES], 'notch_south': NOTCH_SOUTH, 'step_u': STEP_U,
            'slab_holes': [[list(W(u, v)) for u, v in q] for q in (B_PLAZA, NOTCH)],
            'step_foot': STEP_FOOT, 'a_patch': A_PATCH, 'c_paving': c_paving(), 'c_kerb_back': c_kerb_back()}
if __name__ == '__main__':
    R = rules(); json.dump(R, open(T / 'plan/ext_cuts.json', 'w'), indent=1)
    B = build_spec(); json.dump(B, open(T / 'plan/ext_build.json', 'w'), indent=1)
    print('EXT_PLAN', json.dumps({'cut': len(R['cut']), 'clone': len(R['clone']), 'move': len(R['move']),
                                  'bollards': len(B['bollards']), 'benches': len(B['benches'])}))
