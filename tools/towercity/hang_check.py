"""Tower City 'nothing floats' check (Antonio 2026-10-24: the court's chandeliers hung on rods that went up to nothing). Every hung or
mounted fitting the builds record (tc_kit.ANCHORS -> work/l1, work/l2 anchors.json: lamps, pendants, chandeliers, hanging signs'
rods, the flag's wires) names the point where it is held and the direction of its support. From that point a ray must meet a face
turned toward it (a ceiling's underside, a wall, a rib's soffit) within 8 cm, on any exported drawable (tris_*.npy, lot frame).
Usage: py -3 hang_check.py [--list]   exit 1 if any fitting is held by nothing."""
import json, math, sys
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent
ORG, H = (71.0, -884.0), math.radians(69.5); ch, sh = math.cos(H), math.sin(H)
REACH = 0.08
TR = []
for lot in ('l1', 'l2'):
    for f in sorted((W / lot).glob('tris_*.npy')):
        t = np.load(f).astype(np.float64); x, y = t[..., 0] - ORG[0], t[..., 1] - ORG[1]; TR.append(np.stack([x * ch + y * sh, -x * sh + y * ch, t[..., 2]], -1))
TR = np.concatenate(TR); LO, HI = TR.min(1), TR.max(1)
NRM = np.cross(TR[:, 1] - TR[:, 0], TR[:, 2] - TR[:, 0])
def held(p, d):
    p = np.array(p, float); d = np.array(d, float); m = np.nonzero((HI >= p - REACH - 1e-3).all(1) & (LO <= p + REACH + 1e-3).all(1))[0]
    m = m[NRM[m] @ d < 0]                                                     # faces turned toward the fitting
    if not len(m): return False
    A, B, C = TR[m, 0], TR[m, 1], TR[m, 2]; e1, e2 = B - A, C - A; q = np.cross(d, e2); det = (e1 * q).sum(1)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); s = p - A; u = (s * q).sum(1) * inv
    r = np.cross(s, e1); v = (r * d).sum(1) * inv; t = (e2 * r).sum(1) * inv
    return bool((ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 0) & (t <= REACH)).any())
A = [dict(a, lot=lot) for lot in ('l1', 'l2') if (W / lot / 'anchors.json').exists() for a in json.load(open(W / lot / 'anchors.json'))]
bad = [a for a in A if not held(a['p'], a['d'])]
by = {}
for a in A: by[a['name'].split(' rod')[0] if ' rod' in a['name'] else a['name']] = by.get(a['name'], 0) + 1
print(f'HANG_CHECK {len(A)} fittings, {len(bad)} held by nothing', 'PASS' if not bad else 'FAIL')
for a in bad[: (999 if '--list' in sys.argv else 40)]: print('  FLOATS', a['lot'], a['room'], a['name'], a['p'], 'support dir', a['d'])
sys.exit(1 if bad else 0)
