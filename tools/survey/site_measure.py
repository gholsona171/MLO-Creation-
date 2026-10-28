"""Justice Center survey: measure the lot from heightmap.npz (vanilla collision tops).
Min-area rectangles (heading, size, centre) of: the whole sc1_19 block, the courts tower (by height bands), the low city-hall block,
the library, and the plaza disc. Prints JSON-ish lines; site.json is written by site_json.py from these numbers."""
import numpy as np, json, sys
from scipy.spatial import ConvexHull
from scipy import ndimage
d = np.load(r'C:\Users\anton\Documents\Codex\JusticeCenter\survey\heightmap.npz')
top, x0, y0, cell = d['top'], float(d['x0']), float(d['y0']), float(d['cell'])
ny, nx = top.shape
X = x0 + (np.arange(nx) + .5) * cell; Y = y0 + (np.arange(ny) + .5) * cell
GX, GY = np.meshgrid(X, Y)

def mar(mask):
    P = np.c_[GX[mask], GY[mask]]
    H = P[ConvexHull(P).vertices]; best = None
    for i in range(len(H)):
        e = H[(i + 1) % len(H)] - H[i]; a = np.arctan2(e[1], e[0])
        R = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]]); Q = H @ R.T
        lo, hi = Q.min(0), Q.max(0); A = np.prod(hi - lo)
        if best is None or A < best[0]:
            c = ((lo + hi) / 2) @ R; best = (A, np.degrees(a) % 90, hi - lo, c)
    A, h, s, c = best
    return dict(heading_deg=round(h, 2), size_m=[round(s[0], 1), round(s[1], 1)], centre=[round(c[0], 2), round(c[1], 2)], cells=int(mask.sum()), hull=[[round(p[0], 1), round(p[1], 1)] for p in H])

def comp(mask, x, y):
    lab, n = ndimage.label(mask); j = int((y - y0) / cell); i = int((x - x0) / cell)
    return lab == lab[j, i]
out = {}
has = top > -1e8
out['block'] = mar(has)
for zb in (35, 45, 60, 80, 95):
    m = comp(top > zb, 335.9, -1640.1) if top[int((-1640.1 - y0) / cell), int((335.9 - x0) / cell)] > zb else None
    if m is not None: out[f'tower_above_{zb}'] = {k: v for k, v in mar(m).items() if k != 'hull'}
out['tower_roof_z_max'] = round(float(top[comp(top > 45, 335.9, -1640.1)].max()), 2)
for name, (x, y) in {'cityhall_low': (326.6, -1568.5), 'library': (243.4, -1601.0), 'sheriff': (379.1, -1609.9), 'carpark': (369.9, -1676.6)}.items():
    z = top[int((y - y0) / cell), int((x - x0) / cell)]
    m = comp(top > z - 1.5, x, y) if False else None
    out[name + '_z_at_origin'] = round(float(z), 2)
# ground levels along the block's edge: lowest 10 % of block cells, and per quadrant
z = top[has]
out['block_z_p05_p50_p95'] = [round(float(np.percentile(z, p)), 2) for p in (5, 50, 95)]
json.dump(out, open(r'C:\Users\anton\Documents\Codex\JusticeCenter\survey\measure.json', 'w'), indent=1)
for k, v in out.items():
    if isinstance(v, dict): print(k, {kk: vv for kk, vv in v.items() if kk != 'hull'})
    else: print(k, v)
