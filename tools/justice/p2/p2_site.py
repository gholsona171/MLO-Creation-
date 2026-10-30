"""Justice Center phase 2: the site around the buildings, as numbers (py -3 with shapely; writes plan/p2_site.json, which the Blender
build, the LOD baker, p1_maps (prop seating) and the gates read through p2_site_plan.py). Lot frame (jc_frame). Every surface here
sits ABOVE the lot slab by 0.15 m or more (never near-coplanar with it: a flicker and a cross-check hit):
  * PODIUM: the plaza on Innocence Blvd + the aprons round the tower and the atrium, one granite-edged deck at the ground floors'
    height (G 28.8), Rockstar's sidewalk flags (im_sidewalk012, the slab's own material) with the old plaza's red-brick bands
  * STEPS: 3 risers of ~0.17 m (going 0.33) from the slab up to the podium and to every colonnade not on it (Rockstar's outdoor
    steps: one smooth collision ramp along the nosings, doc 09 stairs)
  * LAWN + SLOPED WALK (Lakeside -> Davis Ave): grass from the podium's / Jail I's edge (28.8) down to 0.15 m over the slab at a
    granite kerb 2.5 m in from the lot edge; the walk is a 4 m paved strip across it on the same height function
  * BOLLARDS on Rockstar's dropped kerbs that lead nowhere now (doc 02: bollards on the mouth line make it plaza); the drops at
    Macdonald v 13..19 (sally port) and Innocence v -51..-45 (police garage) are re-used as driveways
  * the secure yard walls, the plaza's police wall + letters, benches, flag poles, trees, the Portal sculpture's centre line
Run: py -3 p2_site.py"""
import json, math, sys
from pathlib import Path
from shapely.geometry import Polygon, LineString, box, Point
from shapely.ops import unary_union
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W)); sys.path.insert(0, str(W.parent))
import jc_frame as F, p2_plan as PL
G = PL.G
LOT = Polygon([F.L(*p[:2]) for p in F.lot_w()])
INSET = 2.5
IN = LOT.buffer(-INSET, join_style=2)
EAST = 63.1                                                   # the podium's street edge (= the lawn's inset line on Innocence)
PODIUM = [(45.1, EAST, -44.0, -7.2), (37.9, EAST, -7.2, 17.3), (50.6, EAST, 17.3, 56.3), (-8.5, EAST, 56.3, 60.3), (-8.5, 13.7, 49.6, 56.3)]
BANDS_V = [-36.0, -26.0, -16.0, -3.0, 8.0, 24.0, 36.0, 48.0]   # red-brick bands across the plaza (1 m), every ~10 m
BAND_W = 1.0
PU = unary_union([box(a, c, b, d) for a, b, c, d in PODIUM])
STEP_H, STEP_N, STEP_GO = (G - PL.SLAB) / 3, 3, 0.33
def steps():
    """[(axis, at, s0, s1, out, z_low, z_top)]: a flight along a straight edge; `at` is the edge's plane (the top riser), the
    flight runs `out` (+1 / -1) away from it on axis u or v."""
    out = [('u', EAST, -42.0, 58.3, 1, PL.SLAB, G),             # the plaza's street front on Innocence Blvd
           ('v', -44.0, 46.0, EAST - 0.8, -1, PL.SLAB, G)]          # the plaza's south edge (the police drive / Roy Lowenstein side)
    for k in ('tower', 'police', 'jail1'):                       # every colonnade run that is not on the podium
        for face in PL.face_list(k):
            runs = []
            for a0, a1 in PL.arcade_bays(k, face):
                p = PL.P(face, (a0 + a1) / 2, 0.6, 0)
                if PU.buffer(0.05).contains(Point(p[0], p[1])) or LAWN_RAW.buffer(0.05).contains(Point(p[0], p[1])): continue
                if runs and a0 - runs[-1][1] < 2.0: runs[-1][1] = a1
                else: runs.append([a0, a1])
            for a0, a1 in runs:
                _, at, ax, *_ , o = face
                out.append((ax, at, a0 - 0.3, a1 + 0.3, o, PL.SLAB, G))
    return out
# the sloped walk: from the podium's north edge to Davis Ave (the real one runs from the entrance to Lakeside Ave)
WALK_LINE = [(31.0, 60.3), (26.0, 75.0), (17.5, 99.0)]
WALK_W = 4.0
LAWN_RAW = IN.intersection(box(-60, 60.3, 80, 140)).difference(box(-60, 40, -8.5, 63.6))
WALK = LineString(WALK_LINE).buffer(WALK_W / 2, cap_style=2).intersection(LAWN_RAW)
LAWN = LAWN_RAW.difference(WALK)
INNER = LineString([(EAST + 1, 60.3), (-8.5, 60.3), (-8.5, 63.6), (-50.0, 63.6)])      # the building side of the lawn (28.8)
# kept road-ymap props in the lawn: planted round (p1_maps seats them on the lawn: p2_site_plan.ground_z)
BOLLARDS = []
for (u, v0, v1) in ((EAST + 2.15, -34.5, -26.5), (EAST + 2.15, 16.5, 27.5), (-48.0, -53.5, -46.5)):
    n = int((v1 - v0) / 1.6); BOLLARDS += [(u, v0 + (v1 - v0) * i / n) for i in range(n + 1)]
YARD_WALLS = [(-44.6, -44.0, -24.5, -7.0, 3.6), (-4.8, -4.2, -24.5, -7.2, 3.6)]            # (u0, u1, v0, v1, height) granite
# area 3 (Antonio 2026-10-29): a driveway from each police garage door to Innocence Blvd - Rockstar's concrete at the doors' threshold
# height (slab + 5 cm), a dipped kerb (the strip runs on 0.8 m past the lot edge, down to the road), prop_bollard_04 along both sides
KERB_OUT, KERB_DROP = 0.4, 0.012                                         # the last 0.4 m eases from +5 to +3.8 cm: over the cross check s 3 cm, never
                                                                          # its plane (the road kerb's own dip: from its measured line, OUTSTANDING)
DRIVEWAYS = []
for gk in ('police_in', 'police_out'):
    d0, d1 = PL.GARAGES[gk]['s']; strip = box(PL.B['police']['box'][1], d0 - 0.3, 90.0, d1 + 0.3).intersection(LOT)
    edge = strip.bounds[2]                                                # the lot edge (Innocence Blvd's back of kerb) at this strip
    DRIVEWAYS.append({'door': gk, 'v': (d0 - 0.3, d1 + 0.3), 'u0': PL.B['police']['box'][1], 'edge': edge})
_bl = sorted({round(DRIVEWAYS[0]['v'][0] - 0.3, 2), round((DRIVEWAYS[0]['v'][1] + DRIVEWAYS[1]['v'][0]) / 2, 2), round(DRIVEWAYS[1]['v'][1] + 0.3, 2)})
for v_ in _bl:                                                            # three lines: south, the pier's middle, north
    u_ = PL.B['police']['box'][1] + 0.9
    while u_ < DRIVEWAYS[0]['edge'] - 0.5: BOLLARDS.append((round(u_, 3), v_)); u_ += 1.7
for _w in YARD_WALLS:                                                                      # a wall meeting the atrium's glass meets a stone bay
    if abs(_w[3] - PL.rects('atrium')[0][2]) < 1e-6 and PL.rects('atrium')[0][0] <= _w[0] <= PL.rects('atrium')[0][1]:
        assert any(c0 <= _w[0] and _w[1] <= c1 for c0, c1 in PL.ATRIUM_SOLID['S0']), 'a yard wall ends on the atrium glass: add it to p2_plan.ATRIUM_SOLID'
YARD_GATE = ('W', -16.5, 1.4)                                                              # pedestrian gate in the west wall: centre v, width
POLICE_WALL = (55.0, 55.6, -31.0, -21.0, 0.95)                                            # the low pink granite wall with the bronze letters
PORTAL = dict(u=47.0, v0=1.0, h=8.0, r=0.42)                                               # our own bent dark tube on the plaza's NW end
BENCHES = [(52.5, -12.0, 90.0), (52.5, -4.0, 90.0), (57.5, 30.0, 270.0), (57.5, 40.0, 270.0), (5.0, 53.0, 180.0)]
FLAGS = [(60.5, -20.0), (60.5, -17.0), (60.5, -14.0)]
TREES = [(-35.0, 80.0), (-20.0, 88.0), (-5.0, 76.0), (5.0, 92.0), (40.0, 70.0), (46.0, 76.0), (-30.0, 100.0)]
def main():
    poly = lambda g: [[round(x, 4), round(y, 4)] for x, y in g.exterior.coords[:-1]]
    parts = lambda g: [poly(p) for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.area > 0.5]
    out = {'G': G, 'slab': PL.SLAB, 'inset': INSET, 'east': EAST, 'podium': PODIUM, 'bands_v': BANDS_V, 'band_w': BAND_W,
           'steps': steps(), 'step': [STEP_N, STEP_GO], 'lawn': parts(LAWN), 'walk': parts(WALK), 'inner': list(INNER.coords),
           'outer': [list(c) for c in IN.exterior.coords], 'bollards': BOLLARDS, 'driveways': DRIVEWAYS, 'kerb_out': KERB_OUT, 'kerb_drop': KERB_DROP, 'yard_walls': YARD_WALLS, 'yard_gate': YARD_GATE,
           'police_wall': POLICE_WALL, 'portal': PORTAL, 'benches': BENCHES, 'flags': FLAGS, 'trees': [t for t in TREES if LAWN.contains(Point(t))],
           'walk_line': WALK_LINE}
    json.dump(out, open(F.J / 'plan/p2_site.json', 'w'), indent=1)
    print('P2_SITE podium %.0f m2 lawn %.0f m2 (%d parts) walk %.0f m2 steps %d bollards %d trees %d' % (PU.area, LAWN.area, len(out['lawn']), WALK.area, len(out['steps']), len(BOLLARDS), len(out['trees'])))
if __name__ == '__main__': main()
