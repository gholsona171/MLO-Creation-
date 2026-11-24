"""campath.py <route.json> <out dir> [--solids solids.json] : compiles a cinematic camera route into a timed track for campath.sh.
Antonio (2026-11-24): "smooth movements and transitions, very cinematic, not robotic and stiff; no points inside walls".

route.json: {"name": "...", "hour": 17, "fov": 52, "shake": 0.12, "clearance": 0.35,
             "shots": [{"hour"?: .., "keys": [{"p": [x,y,z], "speed": m/s, "look"?: [x,y,z], "fov"?: deg}, ...]}, ...]}
  * the camera path runs a CENTRIPETAL Catmull-Rom through the keys (no loops or overshoot at tight corners) and is re-sampled by
    arc length, so speed is what you set, not the spacing of your points;
  * speed blends smoothly from key to key (cosine) and is acceleration-limited both ways (ACC m/s^2). A shot starts already
    moving at START_FRAC of its first speed and never stops: shots dip to black between them (campath.sh), never halt;
  * look: a key with "look" aims at that point (consecutive look keys = the aim glides between them while the camera moves:
    parallax); a key without looks along the path. Aim = yaw / pitch, unwrapped, then smoothed over time (Gaussian, LOOK_SIGMA s)
    so turns ease in and out instead of snapping;
  * fov per key (default route fov), smoothed the same way.
Output <out>/<name>.track.json: per shot {hour, dt, x, y, z, pitch, yaw, fov} sampled every 1 / RATE s (the Lua side interpolates
between samples with Catmull-Rom), and <name>.report.txt.
--solids: [{"name", "lo": [x,y,z], "hi": [x,y,z]}] axis-aligned boxes (walls, slabs, furniture, poles...). Every 5 cm of every shot
must stay `clearance` m clear of all of them; the swept path is also tested for crossing one (a wall between two samples). Any
violation fails the build (CAMPATH_FAIL) with the shot, time, point and the box it hits. campath.sh's probe run checks the same in
game with shape tests."""
import json, math, sys
from pathlib import Path

RATE, ACC, START_FRAC, LOOK_SIGMA, FOV_SIGMA, SUB = 10, 0.55, 0.45, 0.55, 0.8, 300


def v3(a, b, t): return [a[i] + (b[i] - a[i]) * t for i in range(3)]
def dist(a, b): return math.dist(a, b)


def centripetal(P, sub=SUB, alpha=0.5):
    """dense polyline through P (centripetal Catmull-Rom); ends extended by mirroring the neighbouring point."""
    if len(P) == 1: return [P[0]]
    Q = [v3(P[0], P[1], -1.0)] + P + [v3(P[-1], P[-2], -1.0)]
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        def tj(ti, a, b): return ti + max(dist(a, b), 1e-4) ** alpha
        t0 = 0.0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for k in range(sub + (1 if i == len(Q) - 3 else 0)):
            t = t1 + (t2 - t1) * k / sub
            A1 = [((t1 - t) * p0[j] + (t - t0) * p1[j]) / (t1 - t0) for j in range(3)]
            A2 = [((t2 - t) * p1[j] + (t - t1) * p2[j]) / (t2 - t1) for j in range(3)]
            A3 = [((t3 - t) * p2[j] + (t - t2) * p3[j]) / (t3 - t2) for j in range(3)]
            B1 = [((t2 - t) * A1[j] + (t - t0) * A2[j]) / (t2 - t0) for j in range(3)]
            B2 = [((t3 - t) * A2[j] + (t - t1) * A3[j]) / (t3 - t1) for j in range(3)]
            out.append([((t2 - t) * B1[j] + (t - t1) * B2[j]) / (t2 - t1) for j in range(3)])
    return out


def arclen(L):
    s = [0.0]
    for a, b in zip(L, L[1:]): s.append(s[-1] + dist(a, b))
    return s


def at_s(L, S, s):
    """point on polyline L (cumulative lengths S) at arc length s."""
    s = max(0.0, min(S[-1], s)); lo, hi = 0, len(S) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if S[m] <= s: lo = m
        else: hi = m
    seg = S[hi] - S[lo]; return v3(L[lo], L[hi], 0.0 if seg < 1e-9 else (s - S[lo]) / seg)


def key_arcs(keys, L, S):
    """arc length of each key on the dense path (the nearest dense point, searched forward so a path crossing itself stays right)."""
    out, j = [], 0
    for k in keys:
        best = min(range(j, len(L)), key=lambda i: dist(L[i], k['p'])); out.append(S[best]); j = best
    return out


def blend(vals, arcs, s):
    """cosine blend of per-key values along arc length."""
    if s <= arcs[0]: return vals[0]
    for i in range(len(arcs) - 1):
        if s <= arcs[i + 1]:
            u = (s - arcs[i]) / max(arcs[i + 1] - arcs[i], 1e-6); w = (1 - math.cos(math.pi * u)) / 2
            return vals[i] + (vals[i + 1] - vals[i]) * w
    return vals[-1]


def gauss(xs, sigma_samples):
    if sigma_samples <= 0: return xs[:]
    r = int(3 * sigma_samples); w = [math.exp(-0.5 * (k / sigma_samples) ** 2) for k in range(-r, r + 1)]; out = []
    for i in range(len(xs)):
        acc = tot = 0.0
        for k, wk in zip(range(-r, r + 1), w):
            j = min(len(xs) - 1, max(0, i + k)); acc += xs[j] * wk; tot += wk
        out.append(acc / tot)
    return out


def yaw_pitch(d):
    h = math.hypot(d[0], d[1]); return math.degrees(math.atan2(-d[0], d[1])), math.degrees(math.atan2(d[2], max(h, 1e-6)))


def unwrap(a):
    out = [a[0]]
    for x in a[1:]:
        p = out[-1]; x = x + 360 * round((p - x) / 360); out.append(x)
    return out


def compile_shot(shot, route):
    keys = shot['keys']; P = [k['p'] for k in keys]
    L = centripetal(P); S = arclen(L); arcs = key_arcs(keys, L, S); total = S[-1]
    sp = [k['speed'] for k in keys]; fovs = [k.get('fov', route.get('fov', 52.0)) for k in keys]
    ds = 0.05; n = max(2, int(total / ds) + 1); grid = [total * i / (n - 1) for i in range(n)]
    v = [blend(sp, arcs, s) for s in grid]; v[0] = min(v[0], sp[0] * START_FRAC)
    for i in range(1, n): v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * ACC * (grid[i] - grid[i - 1])))
    for i in range(n - 2, -1, -1): v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * ACC * (grid[i + 1] - grid[i])))
    T = [0.0]
    for i in range(1, n): T.append(T[-1] + (grid[i] - grid[i - 1]) * 2 / (v[i] + v[i - 1]))
    dur = T[-1]; m = int(dur * RATE) + 1
    look_keys = [(a, k['look']) for a, k in zip(arcs, keys) if 'look' in k]
    LA = [a for a, _ in look_keys]
    xs, ys, zs, yaws, pitches, fv = [], [], [], [], [], []
    j = 0
    for q in range(m):
        t = min(dur, q / RATE)
        while j < n - 2 and T[j + 1] < t: j += 1
        u = 0.0 if T[j + 1] == T[j] else (t - T[j]) / (T[j + 1] - T[j]); s = grid[j] + (grid[j + 1] - grid[j]) * u
        p = at_s(L, S, s); xs.append(p[0]); ys.append(p[1]); zs.append(p[2])
        ahead = at_s(L, S, min(total, s + 3.0)); back = at_s(L, S, max(0.0, s - 0.5))
        fwd = [ahead[i] - back[i] for i in range(3)]
        d = fwd
        if look_keys:
            # weight of "aim at the look track" vs "look along the path": 1 between two look keys, eased out to 0 towards keys without one
            wts = [1.0 if 'look' in k else 0.0 for k in keys]; w = blend(wts, arcs, s)
            if w > 1e-3:
                tgt = [blend([lp[i] for _, lp in look_keys], LA, s) for i in range(3)]    # the aim point glides key to key
                aim = [tgt[i] - p[i] for i in range(3)]
                na = math.dist(aim, [0, 0, 0]) or 1; nf = math.dist(fwd, [0, 0, 0]) or 1
                d = [fwd[i] / nf * (1 - w) + aim[i] / na * w for i in range(3)]
        yw, pt = yaw_pitch(d); yaws.append(yw); pitches.append(max(-65.0, min(65.0, pt)))
        fv.append(blend(fovs, arcs, s))
    yaws = gauss(unwrap(yaws), LOOK_SIGMA * RATE); pitches = gauss(pitches, LOOK_SIGMA * RATE); fv = gauss(fv, FOV_SIGMA * RATE)
    r = lambda a, k=3: [round(x, k) for x in a]
    return {'hour': shot.get('hour', route.get('hour', 13)), 'dt': 1.0 / RATE, 'dur': round(dur, 2), 'len': round(total, 1),
            'x': r(xs), 'y': r(ys), 'z': r(zs), 'pitch': r(pitches, 2), 'yaw': r(yaws, 2), 'fov': r(fv, 2), 'name': shot.get('name', '')}


def box_dist(p, lo, hi):
    return math.sqrt(sum(max(lo[i] - p[i], 0.0, p[i] - hi[i]) ** 2 for i in range(3)))


def check(track, solids, clear):
    """every 5 cm along each shot (dense from the samples): clearance to every box. Returns violations."""
    bad = []
    for si, sh in enumerate(track):
        pts = list(zip(sh['x'], sh['y'], sh['z']))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]; k = max(1, int(math.dist(a, b) / 0.05))
            for q in range(k):
                p = v3(list(a), list(b), q / k)
                for bx in solids:
                    if box_dist(p, bx['lo'], bx['hi']) < clear:
                        bad.append((si + 1, sh['name'], round(i / RATE, 1), [round(c, 2) for c in p], bx['name'])); break
                else: continue
                break
    return bad


def main():
    route = json.load(open(sys.argv[1])); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    solids = json.load(open(sys.argv[sys.argv.index('--solids') + 1])) if '--solids' in sys.argv else []
    track = [compile_shot(s, route) for s in route['shots']]
    name = route['name']
    json.dump({'name': name, 'shake': route.get('shake', 0.12), 'shots': track}, open(out / f'{name}.track.json', 'w'))
    lines = [f"shot {i + 1} {s['name']}: {s['len']} m in {s['dur']} s" for i, s in enumerate(track)]
    total = sum(s['dur'] for s in track); lines.append(f'total {total:.1f} s of motion, {len(track)} shots')
    bad = check(track, solids, route.get('clearance', 0.35)) if solids else []
    seen = set()
    for b in bad:
        if (b[0], b[4]) in seen: continue
        seen.add((b[0], b[4])); lines.append(f'TOO CLOSE: shot {b[0]} {b[1]} t={b[2]} s at {b[3]}: {b[4]}')
    (out / f'{name}.report.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(('CAMPATH_FAIL ' + str(len(seen)) + ' clearance problems') if bad else f'CAMPATH_PASS {name} {total:.1f} s, {len(solids)} solids checked')
    sys.exit(1 if bad else 0)


if __name__ == '__main__': main()
