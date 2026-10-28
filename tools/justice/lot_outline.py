"""Justice Center phase 1: the clearing outline = Rockstar's own back-of-sidewalk line round block sc1_19.
The sidewalks, kerbs and streets round the block are the road models (sc1_rd_r*); the block's own ground (sc1_19_ground) starts where
their surface ends. So the outline is taken from the road models' own geometry, not drawn by hand:
  1. every up-facing triangle of the base road models (not the _o / _d overlays) within 25 m of the survey kerb, in plan
  2. their union (shapely), closed by +-1 cm to shut sub-centimetre cracks between Rockstar's pieces (edges do not move)
  3. the union's inner ring that holds the block centre = the inner sidewalk edge (exact, T-junctions included)
  5. 'inner_world': the outline shrunk by the 4 m band (the prop-combo LOD cut, p1_cut_lod.py --inner)
  4. each vertex's z from the road surface under it (Rockstar's own edge height); a vertex is dropped only where the edge runs straight
     through it in plan AND height (< 2 mm / 3 mm), so the slab's edge has every vertex of his sidewalk edge (no T-junction cracks)
Writes plan/lot_poly.json: 'world' [[x, y, z]...] (z = Rockstar's sidewalk edge height at the vertex), 'uv', 'gaps', 'source'.
Input: work/xml_ground/drawn_before.npz (tools/drawn_dump.py on the untouched game models).
Run: py -3 lot_outline.py"""
import sys, json, math, numpy as np
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
sys.path.insert(0, str(Path(__file__).parent)); import jc_frame as F
J = F.J
Z = np.load(J / 'work/xml_ground/drawn_before.npz'); T = Z['tris'].astype(np.float64); mid = Z['mid']; names = Z['names']
road = np.array([n.startswith('sc1_rd_r') and not n.endswith(('_o', '_ov', '_d')) for n in names])
up = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2] > 1e-9
c = T.mean(1)
near = np.array([F.edge_dist(F.KERB_W, x, y) < 25 for x, y in c[:, :2]])
sel = np.nonzero(road[mid] & up & (T.max(1)[:, 2] < 35) & near)[0]
polys = [Polygon(T[k, :, :2]) for k in sel]
U = unary_union([p for p in polys if p.is_valid and p.area > 1e-8]).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
cx, cy = F.W(0, 40)
rings = [r for g in getattr(U, 'geoms', [U]) for r in g.interiors if Polygon(r).contains(Point(cx, cy))]
if len(rings) != 1: raise SystemExit('LOT_OUTLINE FAILED: %d inner rings round the block centre (the road ring is not closed)' % len(rings))
ring = list(rings[0].coords)[:-1]
def zat(x, y):
    """Rockstar's road surface height at (x, y): the top road triangle containing it, else the nearest road vertex"""
    best = None
    for k in sel[(np.abs(c[sel, 0] - x) < 12) & (np.abs(c[sel, 1] - y) < 12)]:
        (ax, ay, az), (bx, by, bz), (qx, qy, qz) = T[k]
        d = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
        if abs(d) < 1e-12: continue
        l1 = ((by - qy) * (x - qx) + (qx - bx) * (y - qy)) / d; l2 = ((qy - ay) * (x - qx) + (ax - qx) * (y - qy)) / d; l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -0.002: continue
        z = l1 * az + l2 * bz + l3 * qz
        if best is None or z > best: best = z
    if best is None:
        V = T[sel].reshape(-1, 3); i = np.argmin((V[:, 0] - x) ** 2 + (V[:, 1] - y) ** 2); best = V[i, 2]
    return float(best)
Z3 = [(x, y, zat(x, y)) for x, y in ring]
P = []
for i, (x, y, z) in enumerate(Z3):
    a = Z3[i - 1]; b = Z3[(i + 1) % len(Z3)]
    ex, ey = b[0] - a[0], b[1] - a[1]; L = math.hypot(ex, ey)
    if L > 0 and abs((x - a[0]) * ey - (y - a[1]) * ex) / L < 0.002 and math.dist(a[:2], (x, y)) < L:
        t = math.dist(a[:2], (x, y)) / L
        if abs(a[2] + (b[2] - a[2]) * t - z) < 0.003: continue          # collinear in plan AND in height: the road edge is straight there
    P.append((x, y, z))
area = sum(P[i - 1][0] * P[i][1] - P[i][0] * P[i - 1][1] for i in range(len(P))) / 2
if area < 0: P = P[::-1]
uv = [[round(t, 3) for t in F.L(p[0], p[1])] for p in P]
BAND = 4.0                                    # p1_maps.BAND: the strip inside the edge whose road-ymap props are kept
inner = Polygon([p[:2] for p in P]).buffer(-BAND, join_style=2)
assert inner.geom_type == 'Polygon'
json.dump({'source': 'road models back-of-sidewalk edge (lot_outline.py)', 'world': [[round(p[0], 4), round(p[1], 4), round(p[2], 4)] for p in P],
           'uv': uv, 'area_m2': round(abs(area), 1), 'band_m': BAND,
           'inner_world': [[round(x, 4), round(y, 4)] for x, y in list(inner.exterior.coords)[:-1]]}, open(J / 'plan/lot_poly.json', 'w'), indent=0)
zs = [p[2] for p in P]
print('LOT_OUTLINE %d vertices, area %.0f m2, edge z %.2f..%.2f, longest edge %.1f m' % (len(P), abs(area), min(zs), max(zs),
      max(math.dist(P[i - 1][:2], P[i][:2]) for i in range(len(P)))))
