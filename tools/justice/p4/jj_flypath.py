"""The fly-through camera track, built ONCE here and used by both the recorder (jj_fly.sh) and the offline check (jj_flycheck.py), so the
check sees exactly the frames the camera flies (rig 2026-10-30 review: the old per-leg smoothstep eased the camera to a near stop at
every waypoint - stop-start, static moments - and both paths ended on deliberate holds plus a recording margin: long static ends).
Path file: one waypoint per line, lot frame, "u v z speed [look_u look_v look_z]". speed = how fast the camera passes THIS point (m/s);
between points the speed blends smoothly (cosine), so slow at doors, faster in halls, never a stop. A look target fixes the aim for the
leg that ends at that point; otherwise the camera looks 4 m ahead along the path. The aim is smoothed over time (0.7 s). The camera
eases in over the first 2 m and out over the last 2 m only, and the clip ends when the motion ends.
Track: Catmull-Rom spline through the points, sampled every 5 cm, timed by the speed profile, then resampled every DT seconds; the
Lua plays those samples back with a Catmull-Rom in time (world coordinates).
Run: py -3 jj_flypath.py lua|dur|frames <pathfile>"""
import math, sys
from pathlib import Path
import numpy as np
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
import jc_frame as F
DT, RAMP, TAU, AHEAD, VMIN = 0.4, 1.5, 0.7, 4.0, 0.3
def read(path):
    rows = [list(map(float, l.split())) for l in open(path) if l.strip() and not l.startswith('#')]
    return [np.array(r[:3]) for r in rows], [r[3] for r in rows], [np.array(r[4:7]) if len(r) >= 7 else None for r in rows]
def _cr(p0, p1, p2, p3, t):
    t2 = t * t; t3 = t2 * t
    return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (p3 - p0 + 3 * (p1 - p2)) * t3)
def track(P, SP, LK):
    """the timed camera track: (times, positions, looks) at DT, lot frame."""
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
    return T, ip(pos), ip(look)
def playback(T, A, fps=25.0):
    """the frames the Lua shows: a Catmull-Rom in time through the DT samples (same formula as the Lua)."""
    out = []; n = len(A)
    for x in np.arange(0.0, (n - 1) + 1e-9, 1.0 / (fps * DT)):
        i = int(math.floor(x)); f = x - i
        out.append(_cr(A[max(0, i - 1)], A[min(n - 1, i)], A[min(n - 1, i + 1)], A[min(n - 1, i + 2)], f))
    return np.array(out)
def world(A):
    c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([F.OX + A[:, 0] * c - A[:, 1] * s, F.OY + A[:, 0] * s + A[:, 1] * c, A[:, 2]], 1)
if __name__ == '__main__':
    mode, pf = sys.argv[1], sys.argv[2]; T, Pp, Lk = track(*read(pf))
    if mode == 'dur': print(int(math.ceil(T[-1] + 1.0)))                                # the clip = the motion + 1 s
    elif mode == 'lua':
        f = lambda A: ','.join('{%.2f,%.2f,%.2f}' % tuple(p) for p in world(A))
        print('local S={%s} local K={%s} local DT=%.2f' % (f(Pp), f(Lk), DT))
    elif mode == 'frames': print(len(playback(T, Pp)), round(T[-1], 1))
