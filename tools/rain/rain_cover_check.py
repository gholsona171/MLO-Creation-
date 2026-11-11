"""Gate: no rain inside Tower City (Antonio 2026-11-10: "if it rained outside, it rained in the building").
GTA keeps rain out with a top-down height map of OPAQUE, UP-FACING exterior faces (rig probes 2026-11-10: clear glass, interior room
drawables, script props and down-facing faces do not stop it; one up-facing opaque exterior face does). So every walkable floor of
every MLO room needs such a face straight above it.
For each up-facing floor face of every room drawable (work/*/tris_*.npy + mats_*.npy, world space) a 1 m grid of points looks
straight up through every exterior drawable (each layout's 'ext' + the lot slabs + the exterior clean-up) and is classed:
  covered     an up-facing opaque exterior face above it                                   ok
  glass_only  only exterior glass above it (the glass vault before its rain caps)          FAIL
  int_only    only room geometry above it (underground: the street and vanilla ground above are not in these files;
  open        nothing in these files above it                    both were dry on the rig 2026-11-10)  advisory
Usage: py -3 tools/rain_cover_check.py [--ignore name,name]   (--ignore leaves exterior drawables out: the planted-defect test,
e.g. --ignore tc_mall_raincap must FAIL). Writes logs/rain_cover.json; last line RAIN_COVER_PASS / RAIN_COVER_FAIL."""
import sys, json, collections
from pathlib import Path
import numpy as np
W = Path(r'C:\Users\anton\Documents\Codex\TowerCity\work')
A = sys.argv[1:]; IGNORE = set(A[A.index('--ignore') + 1].split(',')) if '--ignore' in A else set()
EXT = {'tc_ext_fix', 'tc_lot_east', 'tc_lot_west'}
for f in ('l1/l1_layout.json', 'l2/l2_layout.json', 'l3/l3_layout.json', 'gar/gar_layout.json'):
    EXT |= set(json.load(open(W / f)).get('ext', {}))
EXT -= IGNORE
D = {}
for f in sorted(W.glob('*/tris_*.npy')):
    n = f.stem[5:]; t = np.load(f).astype(np.float64); m = f.with_name('mats_' + n + '.npy')
    D[n] = (t, np.load(m) if m.exists() else np.zeros(len(t), np.int8))
ROOMS = [n for n in D if n not in EXT and n not in IGNORE and not n.startswith('tc_lot_')]
CELL = 2.0
def grid(names, up_only):
    T = np.concatenate([D[n][0] for n in names]); K = np.concatenate([D[n][1] for n in names])
    nz = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2]
    keep = nz > 1e-9 if up_only else np.ones(len(T), bool)      # the rain map sees an exterior face only from above (one-sided)
    T, K = T[keep], K[keep]
    lo = np.floor(T[..., :2].min(1) / CELL).astype(int); hi = np.floor(T[..., :2].max(1) / CELL).astype(int)
    G = collections.defaultdict(list)
    for i in range(len(T)):
        if hi[i, 0] - lo[i, 0] > 200 or hi[i, 1] - lo[i, 1] > 200: continue
        for x in range(lo[i, 0], hi[i, 0] + 1):
            for y in range(lo[i, 1], hi[i, 1] + 1): G[(x, y)].append(i)
    return T, K, G
def above(T, K, G, p, z0):
    """{kind: top z} of the faces straight above p higher than z0 + 0.5"""
    idx = G.get((int(np.floor(p[0] / CELL)), int(np.floor(p[1] / CELL))), [])
    if not idx: return {}
    t = T[idx]; a, b, c = t[:, 0], t[:, 1], t[:, 2]
    v0 = c[:, :2] - a[:, :2]; v1 = b[:, :2] - a[:, :2]; v2 = p[None, :2] - a[:, :2]
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01; ok = np.abs(den) > 1e-12; den = np.where(ok, den, 1.0)
    u = (d11 * d20 - d01 * d21) / den; v = (d00 * d21 - d01 * d20) / den
    ins = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
    z = a[:, 2] + u * (c[:, 2] - a[:, 2]) + v * (b[:, 2] - a[:, 2]); out = {}
    for j in np.nonzero(ins & (z > z0 + 0.5))[0]: out[int(K[idx[j]])] = max(out.get(int(K[idx[j]]), -1e9), float(z[j]))
    return out
def inside(p, a, b, c):
    s = lambda p1, p2, p3: (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
TE, KE, GE = grid(sorted(EXT & set(D)), True); TI, KI, GI = grid(ROOMS, False)
res = collections.defaultdict(collections.Counter); bad = collections.defaultdict(list)
for n in ROOMS:
    t, k = D[n]; nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ln = np.linalg.norm(nr, axis=1)
    seen = set()
    for tri in t[(nr[:, 2] / np.maximum(ln, 1e-9) > 0.95) & (k == 0)]:       # opaque up-facing floor faces
        lo, hi = tri.min(0), tri.max(0)
        for x in np.arange(np.ceil(lo[0]), hi[0], 1.0):
            for y in np.arange(np.ceil(lo[1]), hi[1], 1.0):
                p = np.array([x, y]); zf = float(tri[0, 2]); key = (x, y, round(zf, 1))
                if key in seen or not inside(p, *tri): continue
                seen.add(key); e = above(TE, KE, GE, p, zf)
                if 0 in e: cls = 'covered'
                elif 1 in e: cls = 'glass_only'
                else: cls = 'int_only' if 0 in above(TI, KI, GI, p, zf) else 'open'
                res[n][cls] += 1
                if cls == 'glass_only': bad[n].append([round(x, 1), round(y, 1), round(zf, 2)])
(W / 'logs').mkdir(exist_ok=True)
json.dump({'ignored': sorted(IGNORE), 'exterior': sorted(EXT & set(D)), 'rooms': {n: dict(c) for n, c in res.items()}, 'glass_only': bad}, open(W / 'logs/rain_cover.json', 'w'), indent=1)
for n in sorted(res):
    c = res[n]
    if c['glass_only'] or c['int_only'] or c['open']: print(f'  {n}: ' + ', '.join(f'{k} {v}' for k, v in sorted(c.items())))
nb = sum(len(v) for v in bad.values()); tot = sum(sum(c.values()) for c in res.values())
print(f"RAIN_COVER {'PASS' if nb == 0 else 'FAIL'} points {tot} glass_only {nb} rooms {len(res)} exterior {len(EXT & set(D))}")
print('RAIN_COVER_PASS' if nb == 0 else 'RAIN_COVER_FAIL'); sys.exit(1 if nb else 0)
