"""Cinematic fly-through track in WORLD coordinates, for any build (generalised from justice/p4/jj_flypath.py + jj_flycheck.py, 2026-11-27).
Path file: one waypoint per line, "x y z speed [look_x look_y look_z]" (# comments; a line "@ label" names the next section in reports).
speed = how fast the camera passes THIS point (m/s), blended smoothly (cosine) between points, never a stop; a look target fixes the aim
for the leg ending at that point, else the camera looks AHEAD m ahead along the path. Aim smoothed over TAU s; eased in/out over RAMP m
at the very ends only. Track = Catmull-Rom through the points (5 cm), timed by the speed profile, resampled every DT s; fly_rec.sh plays
those samples back with a Catmull-Rom in time, so this check sees the frames the camera shows.
Modes:
  lua <path>    the track as a Lua chunk (S, K, DT)            dur <path>   the clip length (s, motion + 1)
  times <path>  when the camera passes each waypoint (s)       check <path> --tris a.npy [b.npy ...] [--doors doors.json] [--plant|--plant-static]
check: CLOSE (camera >= 0.9 m from every triangle, 0.45 m within 1.2 m of a door; --door-clear X for a door under 1 m wide, where
its own centre line is nearer: say so in the route), STATIC (slower than 0.25 m/s and turning < 5 deg/s
for > 2 s). --tris: (n,3,3) world-coordinate triangle arrays (the kit's tris_*.npy). --doors: [{"pos": [x,y,z]}, ...] (mlo-data/doors.json).
Proof: --plant moves the middle waypoint 0.3 m off the nearest triangle (CLOSE must flag it); --plant-static splices 3 s of frozen frames.
Run: python fly_path.py check route.txt --tris site/bb/tris_*.npy --doors doors.json   ->  FLYCHECK_PASS {...} | FLYCHECK_FAIL | FLYCHECK_PLANT_FOUND"""
import glob, json, math, sys
import numpy as np
DT, RAMP, TAU, AHEAD, VMIN = 0.4, 1.5, 0.7, 4.0, 0.3


def read(path):
    rows, labels = [], {}
    for l in open(path):
        l = l.strip()
        if not l or l.startswith('#'): continue
        if l.startswith('@'): labels[len(rows)] = l[1:].strip(); continue
        rows.append(list(map(float, l.split())))
    return [np.array(r[:3]) for r in rows], [r[3] for r in rows], [np.array(r[4:7]) if len(r) >= 7 else None for r in rows], labels


def _cr(p0, p1, p2, p3, t):
    t2 = t * t; t3 = t2 * t
    return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (p3 - p0 + 3 * (p1 - p2)) * t3)


def track(P, SP, LK):
    """(sample times, positions, looks) every DT, plus the time the camera passes each waypoint."""
    n = len(P); pos, leg, frac = [], [], []
    for i in range(n - 1):
        k = max(8, int(np.linalg.norm(P[i + 1] - P[i]) / 0.05))
        for j in range(k):
            t = j / k; pos.append(_cr(P[max(0, i - 1)], P[i], P[min(n - 1, i + 1)], P[min(n - 1, i + 2)], t)); leg.append(i); frac.append(t)
    pos.append(P[-1]); leg.append(n - 2); frac.append(1.0); pos = np.array(pos)
    ds = np.r_[0.0, np.linalg.norm(np.diff(pos, axis=0), axis=1)]; s = np.cumsum(ds); L = s[-1]
    v = np.array([SP[i] + (SP[i + 1] - SP[i]) * (1 - math.cos(math.pi * f)) / 2 for i, f in zip(leg, frac)])
    ramp = np.minimum(1.0, np.minimum(s / RAMP, (L - s) / RAMP)).clip(0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
    v = np.maximum(VMIN, v * ramp)
    t = np.r_[0.0, np.cumsum(ds[1:] / ((v[1:] + v[:-1]) / 2))]
    wp = [0.0] + [float(t[j]) for j in range(1, len(pos)) if frac[j] == 0.0] + [float(t[-1])]
    raw = []
    for j in range(len(pos)):
        lk = LK[leg[j] + 1]
        if lk is not None: raw.append(lk); continue
        a = np.searchsorted(s, min(L, s[j] + AHEAD)); q = pos[min(a, len(pos) - 1)]
        if np.linalg.norm(q - pos[j]) < 0.5: q = pos[j] + (P[-1] - P[-2])
        raw.append(np.array([q[0], q[1], pos[j][2] - 0.25 * (np.linalg.norm(q[:2] - pos[j][:2]) / AHEAD)]))
    look = [raw[0]]
    for j in range(1, len(raw)):
        a = 1 - math.exp(-(t[j] - t[j - 1]) / TAU); look.append(look[-1] + (raw[j] - look[-1]) * a)
    look = np.array(look); T = np.arange(0.0, t[-1] + 1e-9, DT)
    if T[-1] < t[-1]: T = np.r_[T, t[-1]]
    ip = lambda A: np.stack([np.interp(T, t, A[:, k]) for k in range(3)], 1)
    return T, ip(pos), ip(look), wp


def playback(A, fps=25.0):
    out = []; n = len(A)
    for x in np.arange(0.0, (n - 1) + 1e-9, 1.0 / (fps * DT)):
        i = int(math.floor(x)); f = x - i
        out.append(_cr(A[max(0, i - 1)], A[min(n - 1, i)], A[min(n - 1, i + 1)], A[min(n - 1, i + 2)], f))
    return np.array(out)


def _dist(T, p):
    """distance from p to the nearest triangle (exact point-triangle distance, vectorised)."""
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
    d = np.sqrt(((q - p) ** 2).sum(1)); k = int(d.argmin())
    return float(d[k]), q[k]


def check(pf, args):
    P, SP, LK, labels = read(pf)
    tris = [f for a in args[args.index('--tris') + 1:] if not a.startswith('--') for f in glob.glob(a)]
    if '--doors' in args: tris = [f for f in tris if f != args[args.index('--doors') + 1]]
    T = np.concatenate([np.load(f).astype(np.float64).reshape(-1, 3, 3) for f in tris if f.endswith('.npy')])
    doors = [np.array(d['pos']) for d in json.load(open(args[args.index('--doors') + 1]))] if '--doors' in args else []
    if '--plant' in args:                                         # the middle waypoint 0.3 m off its nearest face: CLOSE must flag it
        m = len(P) // 2; d, q = _dist(T, P[m]); P[m] = q + (P[m] - q) / max(d, 1e-6) * 0.3
    TT, PP, LL, wp = track(P, SP, LK); S = playback(PP); A = playback(LL)
    if '--plant-static' in args:
        k = len(S) // 2; S = np.concatenate([S[:k], np.repeat(S[k:k + 1], 75, 0), S[k:]]); A = np.concatenate([A[:k], np.repeat(A[k:k + 1], 75, 0), A[k:]])
    lo, hi = S.min(0) - 3, S.max(0) + 3; T = T[np.all((T.min(1) < hi) & (T.max(1) > lo), 1)]
    near = lambda p: any(math.hypot(p[0] - d[0], p[1] - d[1]) < 1.2 and d[2] - 3.0 < p[2] < d[2] + 3.0 for d in doors)
    DOOR_CLEAR = float(args[args.index('--door-clear') + 1]) if '--door-clear' in args else 0.45
    bad, worst = [], 9.0
    for k in range(0, len(S), 5):                                                   # every 0.2 s
        p = S[k]; d, _ = _dist(T, p); worst = min(worst, d); lim = DOOR_CLEAR if near(p) else 0.9
        if d < lim: bad.append((round(k / 25.0, 1), round(d, 2), [round(x, 2) for x in p]))
    fr = 25.0; spd = np.linalg.norm(np.diff(S, axis=0), axis=1) * fr
    aim = A - S; aim = aim / np.maximum(1e-9, np.linalg.norm(aim, axis=1))[:, None]
    turn = np.degrees(np.arccos(np.clip((aim[1:] * aim[:-1]).sum(1), -1, 1))) * fr
    still = (spd < 0.25) & (turn < 5.0); holds, run = [], 0
    for k, st in enumerate(np.r_[still, False]):
        if st: run += 1
        else:
            if run / fr > 2.0: holds.append((round((k - run) / fr, 1), round(run / fr, 1)))
            run = 0
    for b in bad[:int(__import__('os').environ.get('FLY_SHOW', 20))]: print('  CLOSE at %.1f s: %.2f m at %s' % b)
    for h in holds: print('  STATIC at %.1f s for %.1f s' % h)
    if '--plant' in args: assert bad, 'PLANTED CLOSE WAYPOINT NOT FOUND: the check is broken'; print('FLYCHECK_PLANT_FOUND close', len(bad)); return 0
    if '--plant-static' in args: assert holds, 'PLANTED HOLD NOT FOUND: the check is broken'; print('FLYCHECK_PLANT_FOUND static', holds); return 0
    ok = not bad and not holds
    sec = {labels[i]: round(wp[i], 1) for i in sorted(labels) if i < len(wp)}
    print(('FLYCHECK_PASS ' if ok else 'FLYCHECK_FAIL ') + json.dumps({'triangles': len(T), 'frames': len(S), 'min_clearance': round(worst, 2),
                                                                     'close': len(bad), 'static': len(holds), 'seconds': round(float(TT[-1]), 1), 'sections': sec}))
    return 0 if ok else 1


if __name__ == '__main__':
    mode, pf = sys.argv[1], sys.argv[2]
    if mode == 'check': sys.exit(check(pf, sys.argv[3:]))
    P, SP, LK, labels = read(pf); T, Pp, Lk, wp = track(P, SP, LK)
    if mode == 'dur': print(int(math.ceil(T[-1] + 1.0)))
    elif mode == 'times': print(json.dumps([round(x, 1) for x in wp]))
    elif mode == 'lua':
        f = lambda A: ','.join('{%.2f,%.2f,%.2f}' % tuple(p) for p in A)
        print('local S={%s} local K={%s} local DT=%.2f' % (f(Pp), f(Lk), DT))
