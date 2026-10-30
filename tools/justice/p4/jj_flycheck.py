"""Offline check of a jj_fly.sh path file against the BUILT geometry (playbook: cinematic fly-throughs - never through a wall, never
hugging one): samples the camera's Catmull-Rom spline every 0.2 m exactly as jj_fly.sh's Lua does, and measures the distance from each
sample to every built triangle (our room drawables, Jail I's exterior). Clearance must be >= 0.9 m, except within 1.2 m of a door
opening (a 1.4 m doorway leaves 0.7 m each side), where >= 0.45 m. Also prints the recording time (the Lua's own leg timing) and flags
any hold longer than 3 s. Proof: --plant moves one waypoint into a wall; the check must flag it.
Run: py -3 jj_flycheck.py <pathfile> [--plant]   (JJ_FLYCHECK_PASS / JJ_FLYCHECK_PLANT_FOUND)"""
import json, math, sys
from pathlib import Path
import numpy as np
JL = Path(__file__).resolve().parent; WK = JL.parent; sys.path[:0] = [str(JL), str(WK)]
import jc_frame as F
OD = JL / __import__('os').environ.get('JJ_OUT', 'out')
L = json.load(open(OD / 'jj_layout.json'))
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
T = np.concatenate([lot(np.load(OD / f'tris_{d}.npy').astype(np.float64)) for d in L['drawables']] + [lot(np.load(WK / 'p2/out/tris_jc_jail1.npy').astype(np.float64))])
K = np.concatenate([np.load(OD / f'mats_{d}.npy') for d in L['drawables']] + [np.load(WK / 'p2/out/mats_jc_jail1.npy')])
rows = [list(map(float, l.split())) for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
if '--plant' in sys.argv: rows[len(rows) // 2][0:2] = [-26.0, 10.0]                     # into the booking hall's west wall
P = [np.array(r[:3]) for r in rows]; SP = [r[3] for r in rows]
def cr(p0, p1, p2, p3, t): t2 = t * t; t3 = t2 * t; return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (p3 - p0 + 3 * (p1 - p2)) * t3)
def pt(i, t): n = len(P); return cr(P[max(0, i - 1)], P[i], P[min(n - 1, i + 1)], P[min(n - 1, i + 2)], t)
S = []
for i in range(len(P) - 1):
    n = max(2, int(np.linalg.norm(P[i + 1] - P[i]) / 0.2))
    S += [pt(i, k / n) for k in range(n)]
S = np.array(S + [P[-1]])
def dist(p):
    """distance from p to the nearest triangle (exact point-triangle distance, vectorised, Ericson's closest-point regions)."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]; ab, ac, ap = b - a, c - a, p - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1); bp = p - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1); cp = p - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-12, 1e-12, va + vb + vc); v = vb / den; w = vc / den
    q = a + ab * v[:, None] + ac * w[:, None]
    with np.errstate(divide='ignore', invalid='ignore'):
        q = np.where(((d1 <= 0) & (d2 <= 0))[:, None], a, q)
        q = np.where(((d3 >= 0) & (d4 <= d3))[:, None], b, q)
        q = np.where(((d6 >= 0) & (d5 <= d6))[:, None], c, q)
        m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); q = np.where(m[:, None], a + ab * (d1 / np.where(d1 - d3 == 0, 1, d1 - d3))[:, None], q)
        m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); q = np.where(m[:, None], a + ac * (d2 / np.where(d2 - d6 == 0, 1, d2 - d6))[:, None], q)
        m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); t_ = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1, (d4 - d3) + (d5 - d6))
        q = np.where(m[:, None], b + (c - b) * t_[:, None], q)
    return float(np.sqrt(((q - p) ** 2).sum(1)).min())
doors = [((o['plane'], (o['a0'] + o['a1']) / 2) if o['axis'] == 'u' else ((o['a0'] + o['a1']) / 2, o['plane'])) + (o['z0'],) for o in L['openings']]
near = lambda p: any(math.hypot(p[0] - d[0], p[1] - d[1]) < 1.2 and d[2] - 0.5 < p[2] < d[2] + 3.0 for d in doors)
sel = T[:, :, :].reshape(-1, 3); lo, hi = S.min(0) - 3, S.max(0) + 3
keep = np.all((T.min(1) < hi) & (T.max(1) > lo), 1); T = T[keep]
bad = []; worst = 9.0
for p in S:
    d = dist(p); worst = min(worst, d); lim = 0.45 if near(p) else 0.9
    if d < lim: bad.append((round(d, 2), [round(x, 2) for x in p], 'door' if near(p) else 'wall'))
secs = sum(np.linalg.norm(P[i + 1] - P[i]) / SP[i + 1] for i in range(len(P) - 1))
holds = [(i + 1, round(np.linalg.norm(P[i + 1] - P[i]) / SP[i + 1], 1)) for i in range(len(P) - 1) if np.linalg.norm(P[i + 1] - P[i]) < 0.6 and np.linalg.norm(P[i + 1] - P[i]) / SP[i + 1] > 3.0]
for b in bad[:15]: print('  CLOSE', *b)
for h in holds: print('  LONG HOLD at waypoint', h)
if '--plant' in sys.argv:
    assert bad, 'PLANTED WAYPOINT IN A WALL NOT FOUND: the fly check is broken'; print('JJ_FLYCHECK_PLANT_FOUND', len(bad)); sys.exit(0)
ok = not bad and not holds
print(('JJ_FLYCHECK_PASS ' if ok else 'JJ_FLYCHECK_FAIL ') + json.dumps({'samples': len(S), 'min_clearance': round(worst, 2), 'close': len(bad), 'long_holds': len(holds), 'seconds': round(secs, 1)}))
sys.exit(0 if ok else 1)
