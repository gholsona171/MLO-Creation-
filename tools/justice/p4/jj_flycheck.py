"""Offline check of a jj_fly.sh path file against the BUILT geometry (playbook: cinematic fly-throughs - never through a wall, never
hugging one, never standing still). It checks the frames the camera actually shows: jj_flypath.py builds the track (the same one
jj_fly.sh plays) and its 25 fps playback is sampled here.
- CLOSE: the camera's distance to every built triangle (our room drawables, Jail I's exterior) >= 0.9 m, and >= 0.45 m within 1.2 m of
  a door opening (a 1.4 m doorway leaves 0.7 m each side).
- HUG (rig 2026-10-30 review: the camera hugged walls): rays to both sides of the motion, level, at the camera and 0.8 m lower (the
  narrower space across counts: a stair rail under the camera); the nearer side must be >= 1.2 m away
  or the camera must sit in the middle 30 % of the space across (narrow stairs, the tunnel: centred is right); doorways (1.2 m) exempt.
- STATIC: the camera slower than 0.25 m/s with its aim turning under 5 deg/s for more than 2 s (a hold), the end included.
Proof: --plant moves one waypoint into a wall (CLOSE must flag it); --plant-hug moves one 1.0 m from the booking hall's west wall
(HUG must flag it); --plant-static splices 3 s of frozen frames into the playback (STATIC must flag it).
Run: py -3 jj_flycheck.py <pathfile> [--plant|--plant-hug|--plant-static]   (JJ_FLYCHECK_PASS / JJ_FLYCHECK_PLANT_FOUND)"""
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
import jj_flypath as FP
P, SP, LK = FP.read(sys.argv[1]); mid = len(P) // 2
if '--plant' in sys.argv: P[mid][0:2] = [-26.0, 10.0]                                      # into the booking hall's west wall
if '--plant-hug' in sys.argv:                                                               # a short pass 1.0 m off the booking hall's west wall
    P[mid:mid] = [np.array([-24.9, 6.0, 30.3]), np.array([-24.9, 10.0, 30.3]), np.array([-24.9, 14.0, 30.3])]; SP[mid:mid] = [1.0, 1.0, 1.0]; LK[mid:mid] = [None] * 3
TT, PP, LL = FP.track(P, SP, LK); S = FP.playback(TT, PP); A = FP.playback(TT, LL)
if '--plant-static' in sys.argv:          # a 3 s frozen camera spliced into the frames (the track itself never drops under 0.3 m/s)
    k = len(S) // 2; S = np.concatenate([S[:k], np.repeat(S[k:k + 1], 75, 0), S[k:]]); A = np.concatenate([A[:k], np.repeat(A[k:k + 1], 75, 0), A[k:]])
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
def ray(o, d):
    """the distance along the level ray o + t d to the nearest triangle (Moller-Trumbore, vectorised), capped at 8 m."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]; e1, e2 = b - a, c - a; h = np.cross(d, e2); det = (e1 * h).sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        f = 1.0 / det; sv = o - a; u = f * (sv * h).sum(1); q = np.cross(sv, e1); v = f * (q * d).sum(1); t = f * (e2 * q).sum(1)
        ok = (np.abs(det) > 1e-9) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < 8.0)
    return float(t[ok].min()) if ok.any() else 8.0
bad = []; hug = []; worst = 9.0
for k in range(0, len(S), 5):                                                                # every 0.2 s
    p = S[k]; d = dist(p); worst = min(worst, d); lim = 0.45 if near(p) else 0.9
    if d < lim: bad.append((round(d, 2), [round(x, 2) for x in p], 'door' if near(p) else 'wall'))
    m = S[min(len(S) - 1, k + 5)] - S[max(0, k - 5)]; m[2] = 0.0
    if np.linalg.norm(m) < 0.05: m = A[k] - p; m[2] = 0.0
    if np.linalg.norm(m) < 1e-6: continue
    m = m / np.linalg.norm(m); n_ = np.array([-m[1], m[0], 0.0]); dl, dr = ray(p, n_), ray(p, -n_)
    lo_ = p - np.array([0.0, 0.0, 0.8]); across = min(dl + dr, ray(lo_, n_) + ray(lo_, -n_))     # the space across at camera AND body height (a rail under the camera narrows it)
    if not near(p) and min(dl, dr) < 1.2 and min(dl, dr) < 0.35 * across: hug.append((round(min(dl, dr), 2), round(across, 2), [round(x, 2) for x in p]))
fr = 25.0; spd = np.linalg.norm(np.diff(S, axis=0), axis=1) * fr
aim = A - S; aim = aim / np.maximum(1e-9, np.linalg.norm(aim, axis=1))[:, None]
turn = np.degrees(np.arccos(np.clip((aim[1:] * aim[:-1]).sum(1), -1, 1))) * fr
still = (spd < 0.25) & (turn < 5.0); holds = []; run = 0
for k, st in enumerate(np.r_[still, False]):
    if st: run += 1
    else:
        if run / fr > 2.0: holds.append((round((k - run) / fr, 1), round(run / fr, 1)))
        run = 0
secs = float(TT[-1])
for b in bad[:15]: print('  CLOSE', *b)
for h in hug[:15]: print('  HUG (nearer side, across, at)', *h)
for h in holds: print('  STATIC at %.1f s for %.1f s' % h)
if '--plant' in sys.argv:
    assert bad, 'PLANTED WAYPOINT IN A WALL NOT FOUND: the fly check is broken'; print('JJ_FLYCHECK_PLANT_FOUND close', len(bad)); sys.exit(0)
if '--plant-hug' in sys.argv:
    assert hug, 'PLANTED WALL-HUGGING PASS NOT FOUND: the fly check is broken'; print('JJ_FLYCHECK_PLANT_FOUND hug', len(hug)); sys.exit(0)
if '--plant-static' in sys.argv:
    assert holds, 'PLANTED HOLD NOT FOUND: the fly check is broken'; print('JJ_FLYCHECK_PLANT_FOUND static', holds); sys.exit(0)
ok = not bad and not hug and not holds
print(('JJ_FLYCHECK_PASS ' if ok else 'JJ_FLYCHECK_FAIL ') + json.dumps({'frames': len(S), 'min_clearance': round(worst, 2), 'close': len(bad), 'hug': len(hug), 'static': len(holds), 'seconds': round(secs, 1)}))
sys.exit(0 if ok else 1)
