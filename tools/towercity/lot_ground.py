"""Tower City level 0: the lot slab's EDGE, dense and on the ground it meets (Antonio 2026-10-24, item 6: a tan strip round the
building bases hovering over the sidewalk in places). The old slab took its edge heights at the lot polygon's corners only - up to
99 m apart - so between them the edge was a straight line over a sidewalk that is not straight: it floated or sank.
Now every lot edge is walked at <= 0.5 m and each point takes the height of what lies 0.25 m outside it:
  * our own exterior paving where it is there (ext_plan.py: the Power St drives / the PARKING block's footprint)
  * else Rockstar's unedited collision (survey/coll_tris.bin): the LOWEST up-facing surface from 2.0 m under to 0.8 m over the old
    corner-height line (a freeway deck over the edge, a planter wall or a hedge top never lifts it; a car-park pit never drops it).
    On Alta St the old line ran 65 m straight from 28.29 to 30.72 over a sidewalk at 28.3 - 29.1: the slab stood up to 1 m proud.
  * a point with nothing found keeps the old line's height (reported)
Pure Python + numpy. `py -3 lot_ground.py` writes plan/lot_edge_dense.json {lot: [[x, y, z], ...]} (read by l0_slab.py) and
prints LOT_GROUND with the per-lot counts. The slab's inside is draped from these points (l0_slab.py)."""
import json, math, sys
import numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); sys.path.insert(0, str(T / 'work'))
import ext_plan as EP
STEP, OUTSIDE, BAND_UP, BAND_DOWN = 0.5, 0.25, 0.8, 2.0
def smooth(pts):                                    # the old corner heights, outliers on a raised road replaced (l0_slab's rule)
    z = np.array([p[2] for p in pts], np.float64); n_ = len(z)
    while True:
        dev = np.array([z[i] - np.median([z[(i + k) % n_] for k in (-3, -2, -1, 1, 2, 3)]) for i in range(n_)])
        i = int(np.argmax(np.abs(dev)))
        if abs(dev[i]) <= 1.2: break
        z[i] -= dev[i]
    return [(p[0], p[1], float(q)) for p, q in zip(pts, z)]
def area(poly): return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
class Ground:
    def __init__(self):
        t = np.fromfile(T / 'survey/coll_tris.bin', dtype=np.float32).reshape(-1, 3, 3).astype(np.float64)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); up = n[:, 2] > 0.3 * np.linalg.norm(n, axis=1)
        t = t[up]; self.t = t
        self.lo = t[:, :, :2].min(axis=1); self.hi = t[:, :, :2].max(axis=1)
        self.cell = {}
        for i, (a, b) in enumerate(zip(self.lo, self.hi)):
            for gx in range(int(math.floor(a[0] / 4)), int(math.floor(b[0] / 4)) + 1):
                for gy in range(int(math.floor(a[1] / 4)), int(math.floor(b[1] / 4)) + 1): self.cell.setdefault((gx, gy), []).append(i)
    def hits(self, x, y):
        out = []
        for i in self.cell.get((int(math.floor(x / 4)), int(math.floor(y / 4))), []):
            (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = self.t[i]
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12: continue
            a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d; b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d; c = 1 - a - b
            if min(a, b, c) >= -1e-9: out.append(a * z1 + b * z2 + c * z3)
        return out
def ours(x, y):
    """our exterior paving's top at a world point (ext_build.py: the B plaza / notch, the branch pit patch), None where it is not ours."""
    u, v = EP.L(x, y)
    z = EP.b_ground_z(u, v)
    if z is None and EP.inside(EP.A_PATCH, u, v): z = EP.patch_z(u, v) - 0.004
    return z
def dense(raw, G):
    ref = smooth(raw); n = len(ref); out = []; kinds = {'ours': 0, 'vanilla': 0, 'kept': 0}
    ccw = area(ref) > 0
    for i in range(n):
        a, b = ref[i], ref[(i + 1) % n]; L = math.dist(a[:2], b[:2]); k = max(1, int(math.ceil(L / STEP)))
        dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = (dy, -dx) if ccw else (-dy, dx)      # the outward normal
        for j in range(k):
            t = j / k; x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]); zr = a[2] + t * (b[2] - a[2])
            ox, oy = x + nx * OUTSIDE, y + ny * OUTSIDE
            z = ours(ox, oy)
            if z is not None: kinds['ours'] += 1
            else:
                c = [h for h in G.hits(ox, oy) if -BAND_DOWN <= h - zr <= BAND_UP]
                if c: z = min(c) + 0.01; kinds['vanilla'] += 1
                else: z = zr + 0.01; kinds['kept'] += 1
            out.append([round(x, 4), round(y, 4), round(z, 4)])
    return out, kinds
if __name__ == '__main__':
    EDGE = json.load(open(T / 'plan/lot_edge_z.json')); G = Ground(); res = {}; rep = {}
    for lot, raw in EDGE.items():
        res[lot], rep[lot] = dense(raw, G)
        zs = [p[2] for p in res[lot]]
        rep[lot]['points'] = len(zs); rep[lot]['z'] = [round(min(zs), 2), round(max(zs), 2)]
    json.dump(res, open(T / 'plan/lot_edge_dense.json', 'w'))
    print('LOT_GROUND', json.dumps(rep))
