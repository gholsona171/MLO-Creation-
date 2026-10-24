"""Light-gap audit of the mall's upper tenant floors (playbook 07 / tools/gap_check.py's method on our build outputs): rays from points
inside every unit, the corridor, the passage and the stair lobby (a 1.5 m grid, floor + 0.4, floor + 1.7, ceiling - 0.3) in ~600
directions. Faces are one-sided in game: a face turned away from the ray is not seen. A ray that leaves without SEEING a face is a
hole, unless it leaves the building through one of its window bays (the glass is meant to be seen through). Geometry: every mall
drawable (work/l2/tris_tc_mall_*.npy, rooms + exterior shell), world space taken back to the lot frame. Points that fall inside a
solid (a counter, a bookcase) can report false gaps: check those by eye. Regions: l2_layout.json 'upper_check'.
Run: blender -b --python upper_gap_check.py   -> work/l2/upper_gap_report.json, a summary line UPPER_GAP_CHECK"""
import json, math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
WK = Path(r'C:\Users\anton\Documents\Codex\TowerCity\work')
ORG, H = (71.0, -884.0), math.radians(69.5); ch, sh = math.cos(H), math.sin(H)
T = np.concatenate([np.load(f).astype(np.float64) for f in sorted((WK / 'l2').glob('tris_tc_mall_*.npy'))])
x, y = T[..., 0] - ORG[0], T[..., 1] - ORG[1]; Lc = np.stack([x * ch + y * sh, -x * sh + y * ch, T[..., 2]], -1)
tree = BVHTree.FromPolygons([Vector(p) for p in Lc.reshape(-1, 3)], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(Lc))])
def seen(o, d, dist=250.0):
    p = o.copy(); left = dist
    while left > 0:
        loc, nrm, _, t = tree.ray_cast(p, d, left)
        if loc is None: return None
        if nrm.dot(d) < 0: return loc
        p = loc + d * 1e-3; left -= t + 1e-3
    return None
LV = {'L2': (36.4, 42.4), 'L3': (43.6, 49.6)}; BU, BV = 78.0, 54.0
WIN = []                                                    # the street walls' window bays on levels 2 and 3 (l2_build.WIN's rule)
for axis, at, a, b in (('v', -BV, -BU, -22.0), ('v', -BV, 22.0, BU), ('v', BV, -BU, BU), ('u', -BU, -BV, BV), ('u', BU, -BV, BV)):
    for c in np.arange(a + 7.5, b - 3.0, 7.5):
        if axis == 'v' and at == BV and abs(c) < 26.0 + 0.3 + 3.1: continue
        if axis == 'u' and -4.0 - 3 < c < 4.0 + 3: continue
        for z0 in (36.4, 43.6): WIN.append((axis, at, c - 2.6, c + 2.6, z0 + 1.0, z0 + 4.6))
def exit_kind(o, d):
    ts = [((math.copysign(BU, d[0]) - o[0]) / d[0], 'u') if abs(d[0]) > 1e-9 else (1e9, 'u'), ((math.copysign(BV, d[1]) - o[1]) / d[1], 'v') if abs(d[1]) > 1e-9 else (1e9, 'v')]
    t, ax = min(ts); p = o + d * t
    if p[2] > 50.6 or p[2] < 35.8: return 'gap', p
    at = math.copysign(BU if ax == 'u' else BV, d[0] if ax == 'u' else d[1]); s = p[1] if ax == 'u' else p[0]
    if any(w[0] == ax and abs(w[1] - at) < 0.1 and w[2] - 0.05 <= s <= w[3] + 0.05 and w[4] - 0.05 <= p[2] <= w[5] + 0.05 for w in WIN): return 'window', p
    return 'gap', p
def dirs(n=600):
    g = math.pi * (3 - math.sqrt(5)); return [Vector((math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.cos(g * i), math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.sin(g * i), 1 - 2 * (i + .5) / n)) for i in range(n)]
D = dirs()
def grid(a, b):
    n = max(2, math.ceil((b - a - 0.8) / 1.5) + 1); return [a + 0.4 + (b - a - 0.8) * k / (n - 1) for k in range(n)]
LAY = json.load(open(WK / 'l2/l2_layout.json')); pts = []
for name, rs in LAY['upper_check']['rooms'].items():
    zf, zc = LV[name.split()[1]]
    for a, b, c, d in rs:
        for u in grid(a, b):
            for v in grid(c, d):
                for z in (zf + 0.4, zf + 1.7, zc - 0.3): pts.append((name, Vector((u, v, z))))
gaps, wins, cells = 0, 0, {}
for name, o in pts:
    for d in D:
        if seen(o, d) is not None: continue
        k, p = exit_kind(o, d)
        if k == 'window': wins += 1; continue
        gaps += 1; key = (name, round(p[0] * 4) / 4, round(p[1] * 4) / 4, round(p[2] * 4) / 4, tuple(round(c, 1) for c in o))
        cells[key] = cells.get(key, 0) + 1
rep = sorted(([k[0], [k[1], k[2], k[3]], list(k[4]), c] for k, c in cells.items()), key=lambda r: -r[-1])
json.dump({'points': len(pts), 'rays': len(pts) * len(D), 'window_rays': wins, 'gap_rays': gaps, 'cells': rep}, open(WK / 'l2/upper_gap_report.json', 'w'), indent=1)
by = {}
for n, p, o, c in rep: by[n] = by.get(n, 0) + c
print('UPPER_GAP_CHECK', json.dumps({'points': len(pts), 'rays': len(pts) * len(D), 'window_rays': wins, 'gap_rays': gaps, 'gap_cells': len(rep)}), flush=True)
for n, c in sorted(by.items(), key=lambda x: -x[1])[:40]: print('  GAP', n, c, flush=True)
