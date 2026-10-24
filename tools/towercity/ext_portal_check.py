"""Exterior-model faces seen from inside without a portal (Antonio 2026-10-23: the mall's clock-window gable was built in the exterior
drawable; from the mezzanine its stone round the glass drew as void). An exterior model is drawn from inside an MLO only through a
portal to limbo, so any exterior face that looks INTO a room (its centre nudged 0.3 m along its normal lands inside a room's box)
must be seen through one of that MLO's limbo portals (the line from the face along its normal crosses a portal's outline),
unless an interior surface stands in front of it within 4 m - otherwise it is invisible from inside and the room shows void there. Input: work/<lot>/tris_<ext>.npy + <lot>_layout.json (rooms' drawable boxes, portals).
Run: py -3 ext_portal_check.py   (exit 1 on any hit; lists them per room)"""
import json, math, sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent
H = math.radians(69.5)
LOTS = [('l1', 'tc_ug_ext', (71.0, -884.0)), ('l2', 'tc_mall_ext', (71.0, -884.0)), ('l3', 'tc_tower_ext', (-78.897, -827.328))]


def to_local(P, o):
    dx, dy = P[..., 0] - o[0], P[..., 1] - o[1]
    return np.stack([dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H), P[..., 2]], -1)


def limbo_portals(L):
    keys = {r['key'] for r in L['rooms']}
    out = []
    for p in L['portals']:
        if 'limbo' in (p['from'], p['to']) and (p['from'] in keys or p['to'] in keys):
            c = np.array(p['corners'], float); n = np.cross(c[1] - c[0], c[2] - c[0]); n /= np.linalg.norm(n)
            out.append((c, n))
    return out


def seen_through_portal(pt, nrm, portals, reach=40.0):
    """does the line from the face into the room (along its normal) cross one of the limbo portals?"""
    for c, n in portals:
        den = float(np.dot(nrm, n))
        if abs(den) < 1e-6: continue
        t = float(np.dot(c[0] - pt, n)) / den
        if not (-0.05 <= t <= reach): continue
        q = pt + nrm * t; ok = True
        for i in range(len(c)):
            e = c[(i + 1) % len(c)] - c[i]
            if np.dot(np.cross(e, q - c[i]), n) < -1e-3: ok = False; break
        if ok: return True
    return False


def ray_blocked(pt, d, A, E1, E2, reach=4.0):
    """Moller-Trumbore against the interior triangles (A, E1 = B - A, E2 = C - A): something interior within `reach` along d?"""
    if len(A) == 0: return False
    P = np.cross(d, E2); det = (E1 * P).sum(1); m = np.abs(det) > 1e-9
    inv = np.zeros_like(det); inv[m] = 1.0 / det[m]; S = pt - A
    u = (S * P).sum(1) * inv; Q = np.cross(S, E1); v = (Q * d).sum(1) * inv; t = (E2 * Q).sum(1) * inv
    return bool(np.any(m & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.02) & (t < reach)))


def main():
    hits = {}
    for lot, ext, o in LOTS:
        L = json.load(open(W / lot / f'{lot}_layout.json'))
        f = W / lot / f'tris_{ext}.npy'
        if not f.exists(): continue
        T = to_local(np.load(f).astype(np.float64), o)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1); ok = a > 1e-6; n[ok] /= a[ok, None]
        c = T.mean(1); probe = c + n * 0.3
        boxes = [(r, np.array(L['drawables'][r['drawable']]['bb_lo']) + 0.05, np.array(L['drawables'][r['drawable']]['bb_hi']) - 0.05)
                 for r in L['rooms'] if r['drawable'] in L['drawables']]
        ports = limbo_portals(L)
        I = np.concatenate([to_local(np.load(g).astype(np.float64), o) for g in sorted((W / lot).glob('tris_*.npy')) if g.stem != f'tris_{ext}'])
        IA, IE1, IE2 = I[:, 0], I[:, 1] - I[:, 0], I[:, 2] - I[:, 0]; Ilo, Ihi = I.min(1), I.max(1)
        for i in np.where(ok & (a / 2 > 0.05))[0]:
            room = next((r['key'] for r, lo, hi in boxes if np.all(probe[i] > lo) and np.all(probe[i] < hi)), None)
            if not room: continue
            near = np.all(Ilo < np.maximum(c[i], c[i] + n[i] * 4.0) + 0.01, 1) & np.all(Ihi > np.minimum(c[i], c[i] + n[i] * 4.0) - 0.01, 1)
            if ray_blocked(c[i], n[i], IA[near], IE1[near], IE2[near]): continue        # an interior surface stands in front of it
            if not seen_through_portal(c[i], n[i], ports):
                h = hits.setdefault((lot, room), [0, 0.0, c[i]]); h[0] += 1; h[1] += a[i] / 2
    tot = sum(v[1] for v in hits.values())
    print(f'EXT_PORTAL {len(hits)} room(s), {tot:.1f} m2 of exterior faces seen from inside without a portal')
    for (lot, room), (k, area, at) in sorted(hits.items(), key=lambda kv: -kv[1][1]):
        print(f'  {lot} {room:14s} {k:5d} faces {area:8.1f} m2  e.g. local {np.round(at, 2).tolist()}')
    sys.exit(1 if hits else 0)


if __name__ == '__main__': main()
