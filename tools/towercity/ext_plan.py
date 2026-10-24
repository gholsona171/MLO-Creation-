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
     its top stretched to the deck soffit (no cap beam there), with its own collision moved with it."""
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
A_MARK = [rect(79.65, 84.75, -52.5, -35.85), rect(85.45, 92.5, -52.5, -35.85)]   # turn dashes /
                                            # arrows on the main deck (the edge line u 79.3 and the lane line u 85.1 stay)
A_SRC = (-61.0, -53.0)                      # the clone source: the straight stretch south of the mouth (no dropped kerb, probed)
A_SHIFTS = [8.0, 16.0, 24.0]                # source length 8 m, three copies reach past the island's kerb (clipped there)
A_CLIP = rect(60.0, KERB_U + 0.001, *A_V)
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
B_DRIVE = rect(3.0, 40.5, -77.35, -61.0)    # the drives' tarmac (material rule: kerbs and planters are other materials)
B_MOUTH_V = -77.35                          # the street's kerb line the drives crossed (the paving stops here, bollards on it)
B_ROAD_MATS = r'road|marking|damage'
B_ENTS = rect(1.0, 36.0, -66.0, -58.0)      # ivy tops on the block (z 36.5)
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
        {'name': 'A branch: road, kerbs, decals', 'models': r'^dt1_rd1_r1_(14|ovly_00)$', 'poly': W_(A_ALL), 'z': [38.5, 60.0], 'col': True},
        {'name': 'A branch: structure + barrier corner', 'models': r'^dt1_rd1_(fwy02|r2_fwy_ovly_02)$', 'poly': W_(A_STRUCT), 'z': [38.5, 60.0], 'col': True},
        {'name': 'A turn dashes / arrows on the deck', 'models': r'^dt1_rd1_r1_(14|ovly_00)$', 'polys': [W_(p) for p in A_MARK], 'z': [42.5, 44.0], 'mat': 'marking', 'col': False},
        {'name': 'B PARKING block', 'models': DT1_11, 'poly': W_(B_BLOCK), 'z': [20.0, 60.0], 'col': True, 'col_files': 'dt1_11'},
        {'name': 'B drives: tarmac + markings', 'models': r'^dt1_rd1_r1_12$', 'poly': W_(B_DRIVE), 'z': [28.0, 31.6], 'mat': B_ROAD_MATS, 'col': False},
        {'name': 'B drives: arrows + decals', 'models': r'^dt1_rd1_r1_ovly_23$', 'poly': W_(B_DRIVE), 'z': [28.0, 31.6], 'over': 'B_TARMAC', 'col': False},
    ]
    clone = [
        {'name': 'A deck edge: sidewalk + kerb', 'models': r'^dt1_rd1_r1_14$', 'src': W_(rect(72.9, KERB_U, *A_SRC)), 'z': [42.5, 44.6],
         'shifts': [list(Wd(0.0, s)) for s in A_SHIFTS], 'clip': W_(A_CLIP), 'col': True},
        {'name': 'A deck edge: barrier + fascia', 'models': r'^dt1_rd1_fwy02$', 'src': W_(rect(70.0, 74.0, *A_SRC)), 'z': [38.5, 44.6],
         'shifts': [list(Wd(0.0, s)) for s in A_SHIFTS], 'clip': W_(A_CLIP), 'col': False},
    ]
    move = [{'name': 'P driveway pillar', 'models': r'^dt1_rd1_(fwy02|r2_fwy_ovly_02)$', 'centre': list(W(*PIL_C)), 'r': PIL_R, 'z': list(PIL_Z),
             'mat': 'wall_concrete32|pilar|fuckedup|glue',            # the column, its base and its decals - never the cap beam over it
             'shift': list(Wd(0.0, PIL_DV)) + [GROUND_DZ], 'top': [41.7 + GROUND_DZ, SOFFIT + 0.02],
             'col': True, 'col_z': [31.0, 40.8], 'col_nz_max': 0.5}]   # collision: the column's walls under the cap beam (40.87) only
    ents = [{'name': 'A ivy on the old walls', 'poly': W_(A_ALL), 'z': [32.0, 41.0]}, {'name': 'B ivy on the block', 'poly': W_(B_ENTS), 'z': [32.0, 41.0]}]
    occl = [W_(A_ALL), W_(B_BLOCK), W_(B_DRIVE)]
    return {'_note': 'written by work/ext_plan.py - do not edit by hand', 'cut': cut, 'clone': clone, 'move': move, 'ents': ents, 'occl': occl,
            'ext_only': ['dt1_rd1_fwy02', 'dt1_rd1_r2_fwy_ovly_02', 'dt1_rd1_r1_12', 'dt1_rd1_r1_ovly_23'],     # cut by these rules only (never by the lot)
            'b_tarmac': [[list(W(p[0], p[1])) for p in poly] for poly in b_tarmac()]}       # world (x, y): the 'over' test of the decal rule
# ---------------- the B paving ----------------
def _tris():
    return json.load(open(T / 'survey/tris_front.json'))         # Rockstar's own triangles (tools/tri_dump.py, src/native originals)
def _clip_v(tri, vmin):
    """clip a lot-frame triangle [(u, v, z)] to v >= vmin (Sutherland-Hodgman, one plane) -> polygon (maybe empty)."""
    out = []
    for i in range(len(tri)):
        a, b = tri[i], tri[(i + 1) % len(tri)]; ia, ib = a[1] >= vmin, b[1] >= vmin
        if ia: out.append(a)
        if ia != ib:
            t = (vmin - a[1]) / (b[1] - a[1]); out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
    return out
def b_tarmac():
    """the drives' surface (lot frame, z): Rockstar's BASE tarmac layer of r1_12 in B_DRIVE ('im_road_002') + the edge-strip layer
    where no base lies under it ('im_road_edge_001' along the kerbs), clipped at the mouth line. The other road layers (patches,
    damage, dirt, blends, markings) are overlays drawn on top of the base - the cut removes them all, the paving copies only the
    footprint, so it meets every kerb and planter exactly and has no overlapping layers (a coplanar clash)."""
    base, edge = [], []
    for r in _tris():
        if r[0] != 'dt1_rd1_r1_12' or r[1] not in ('im_road_002', 'im_road_edge_001'): continue
        P = [L(p[0], p[1]) + (p[2],) for p in r[2:5]]
        cu = sum(p[0] for p in P) / 3; cv = sum(p[1] for p in P) / 3; cz = sum(p[2] for p in P) / 3
        if not inside(B_DRIVE, cu, cv) or not 28.0 <= cz <= 31.6: continue
        (base if r[1] == 'im_road_002' else edge).append(P)
    keep = base + [P for P in edge if drive_z(sum(p[0] for p in P) / 3, sum(p[1] for p in P) / 3, base) is None]
    out = []
    for P in keep:
        poly = _clip_v(P, B_MOUTH_V)
        if len(poly) >= 3: out.append([[round(c, 4) for c in p] for p in poly])
    return out
def drive_z(u, v, tar=None):
    """the drives' own surface height at (u, v): the tarmac triangle under it (None outside)."""
    for poly in tar or b_tarmac():
        for i in range(1, len(poly) - 1):
            (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = poly[0], poly[i], poly[i + 1]
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12: continue
            a = ((y2 - y3) * (u - x3) + (x3 - x2) * (v - y3)) / d; b = ((y3 - y1) * (u - x3) + (x1 - x3) * (v - y3)) / d; c = 1 - a - b
            if min(a, b, c) >= -1e-6: return a * z1 + b * z2 + c * z3
    return None
NOTCH = [(1.50, NOTCH_SOUTH), (34.15, NOTCH_SOUTH), (33.24, -62.99), (26.81, -60.06), (STEP_U, -60.08), (STEP_U, STEP_FOOT + 0.10),
         (4.65, STEP_FOOT + 0.10), (4.65, -63.85), (1.97, -63.85)]   # the block's footprint outside the lot, in front of / beside the steps;
                                                                     # its outline follows the lot edge (plan/lot_polys.json west) and stops
                                                                     # 10 cm under the first riser; west of the drive it stops at the L planter
def notch_z(u, v, tar=None):
    """the notch paving: the drive's height along its north end (v -64.45), rising 1 % toward the building; in front of the
    steps it eases to the first riser's foot (29.40 + 0.02) so the bottom step keeps its full rise."""
    uu = min(max(u, 5.0), 33.5); z0 = None
    for k in range(0, 33):                                    # the nearest drive along the notch's south edge (planter tops in between)
        for du in ((0.0,) if k == 0 else (k * 0.25, -k * 0.25)):
            z0 = drive_z(uu + du, NOTCH_SOUTH - 0.3, tar)
            if z0 is not None: break
        if z0 is not None: break
    assert z0 is not None, ('no drive near the notch at u', u)
    t = (v - NOTCH_SOUTH)
    k = min(max(t / (STEP_FOOT - NOTCH_SOUTH), 0.0), 1.0); zw = z0 + (29.42 - z0) * k     # in front of the steps
    ze = z0 + 0.01 * t                                                                     # beside them (to the lot edge)
    w = min(max((u - STEP_U) / 2.0, 0.0), 1.0); return zw + (ze - zw) * w                 # blended over 2 m past the steps' end
def bollards():
    """bollards on the mouth line (0.45 m inside the street kerb line), 1.6 m apart, across each drive: [(u, v)]"""
    out = []
    for u0, u1 in ((5.2, 15.2), (25.4, 38.4)):
        n = int((u1 - u0) / 1.6) + 1; d = (u1 - u0) / (n - 1)
        out += [(round(u0 + i * d, 3), B_MOUTH_V + 0.45) for i in range(n)]
    return out
BENCHES = [(10.2, -68.5, 180.0), (28.6, -68.0, 180.0)]   # (u, v, heading in the lot frame): seat facing -v (the street)
def build_spec():
    tar = b_tarmac()
    return {'_note': 'written by work/ext_plan.py - do not edit by hand', 'origin': list(ORIGIN), 'heading': HEADING,
            'tarmac': tar, 'notch': NOTCH, 'bollards': [[u, v, round(drive_z(u, v, tar) or 0.0, 3)] for u, v in bollards()],
            'benches': [[u, v, round(drive_z(u, v, tar) or 0.0, 3), h] for u, v, h in BENCHES], 'notch_south': NOTCH_SOUTH, 'step_u': STEP_U,
            'step_foot': STEP_FOOT, 'a_patch': A_PATCH}
if __name__ == '__main__':
    R = rules(); json.dump(R, open(T / 'plan/ext_cuts.json', 'w'), indent=1)
    B = build_spec(); json.dump(B, open(T / 'plan/ext_build.json', 'w'), indent=1)
    print('EXT_PLAN', json.dumps({'cut': len(R['cut']), 'clone': len(R['clone']), 'move': len(R['move']), 'b_tarmac_tris': len(R['b_tarmac']),
                                  'bollards': len(B['bollards']), 'benches': len(B['benches'])}))
