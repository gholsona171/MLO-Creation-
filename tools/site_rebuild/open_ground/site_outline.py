"""How site_plan.SITE was measured (run once; its output is pasted into site_plan.py as data, which then checks itself against the
collision). The site is the flat strip between the shore road (Marina Dr, north) and the road to the south, kept ROAD_CLEAR m off
every road's collision edge (the cross road at the east end too), from WEST_X to where the cross road closes it.
  * distance to the road edge = Euclidean distance from each 0.25 m sample to the nearest road sample of ground_scan.py's mask
    (0.25 m), minus half a sample, so the 3 m is kept from the outer edge of the road's collision;
  * the outline is the ROAD_CLEAR + MARGIN contour of that distance, the strip's part east of WEST_X, simplified (Douglas-Peucker,
    SIMPLIFY m, and then pulled inward by SIMPLIFY so the simplified line never comes nearer than ROAD_CLEAR).
WEST_X: west of x ~1003 stands a compound (a hut with a radio tower, corrugated fences, a liquor sign, lr_cs4_03_strm_4 / long_2),
then a hardware store, a garage and a fast-food stand; the roads also start to converge west of x ~840 (survey 2026-11-27). The
open strip ends at the compound's fence (x 1000.6): the site stops 9 m short of it.
EAST_X: at the east end the cross road (Meringue Ln) and the south road's ENE branch enclose a small triangle of ground (x > 1306,
y 3562..3586) that runs on past the junction: the site stops at x 1306, where the cross road's 3 m line meets the branch's.
Run: py -3 site_outline.py      prints SITE = [...] (world x, y)"""
import numpy as np
from pathlib import Path
from scipy import ndimage
import shapely
from shapely.geometry import Polygon, Point
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
M = Path(__file__).resolve().parents[1]
ROAD_CLEAR, MARGIN, SIMPLIFY, WEST_X, EAST_X = 3.0, 0.35, 0.6, 1010.0, 1306.0
SEED = (1222.0, 3590.0)                                     # a point on the strip (the building)


def main():
    G = np.load(M / 'site' / 'ground_raw.npz'); R = G['road']; x0, y0 = G['box'][:2]; rs = float(G['road_step'])
    D = ndimage.distance_transform_edt(~R) * rs - rs / 2
    xs = x0 + (np.arange(R.shape[1]) + .5) * rs; ys = y0 + (np.arange(R.shape[0]) + .5) * rs
    Dm = np.where((xs[None, :] < WEST_X) | (xs[None, :] > EAST_X), -1.0, D)   # the two straight ends
    cs = plt.contour(xs, ys, Dm, levels=[ROAD_CLEAR + MARGIN])
    best = None
    for path in cs.allsegs[0]:
        if len(path) < 4: continue
        P = Polygon(path).buffer(0)
        if P.geom_type == 'Polygon' and P.contains(Point(SEED)): best = P
    assert best is not None, 'no closed outline round the seed'
    S = best.simplify(SIMPLIFY, preserve_topology=True).buffer(-SIMPLIFY, join_style='mitre').simplify(0.05)
    S = shapely.geometry.polygon.orient(S, 1.0)
    pts = [(round(x, 2), round(y, 2)) for x, y in list(S.exterior.coords)[:-1]]
    print('SITE = [' + ', '.join(f'({x}, {y})' for x, y in pts) + ']')
    print('# vertices', len(pts), 'area %.0f m2' % S.area, 'bounds', [round(v, 1) for v in S.bounds])


if __name__ == '__main__': main()
