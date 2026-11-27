"""The site's new ground (the grade): one height field every ground step reads (site_col.py sets the collision to it, terrain.py puts
Rockstar's drawn ground under it, ground.py drapes our ground surface on it), so what you see and what you stand on are one.
  * the PAD (site_plan: the building's roof + deck outline + 2 m apron), grown by PAD_GROW (one 2 m grid cell's diagonal, so every
    collision / ground cell that touches the pad is wholly flat): exactly PAD_Z = the club's floor top minus site_plan.FLOOR_GAP.
    Natural ground can never come through the floor.
  * the arch's two feet: the ground in a LEG_R disc round each foot lies within site_plan.LEG_Z (the blade always buried, never
    floating), and round the disc within a cone of LEG_SLOPE (15 %) of that band: the back foot
    lands 4.6 m from the site's north edge, 0.6 m over the old ground there, so it stands on a low mound.
  * the rest of the lot: a smooth membrane (least squared slope) held to the untouched ground just outside the site (every node
    outside the outline keeps Rockstar's ground: the lot meets it, and both road verges, without a step), to the pad, and to the
    ground under the two power poles the site keeps (site_plan: the south line), pulled lightly (LAMBDA) toward the natural
    ground's broad trend (a TREND_M m median), so the long lot keeps the strip's gentle fall instead of a dead-flat plate.
Rockstar's ground = the lowest up-facing collision per 1 m cell (ground_scan.py, ../site/ground_raw.npz), as it is (a smoothed
copy at the outline left 0.2 m steps against the untouched collision just outside).
Run: py -3 grade.py      Output ../site/grade.npy + grade.json (+ grade.png). grade_z(x, y) reads it (bilinear), Blender too."""
import json, math
import numpy as np
from pathlib import Path
T = Path(__file__).resolve().parent; M = T.parent
PAD_GROW, LAMBDA, TREND_M, POLE_HOLD, LEG_SLOPE = 2.9, 5e-4, 41, 1.5, 0.15


def build():
    import sys; sys.path.insert(0, str(T)); import site_plan as SP
    from scipy import ndimage
    from shapely.geometry import Polygon, Point
    import shapely as V
    G = np.load(M / 'site' / 'ground_raw.npz'); low = G['low']; gx0, gy0, st = G['box'][:3]
    raw = low.copy()
    if np.isnan(raw).any():                                                         # (9 cells with no collision: nearest ground)
        idx = ndimage.distance_transform_edt(np.isnan(raw), return_distances=False, return_indices=True); raw = raw[tuple(idx)]
    trend = ndimage.median_filter(raw, TREND_M, mode='nearest')     # (the outside nodes keep the collision's own heights: no step)
    # nodes = the raw cells' centres (world x0 + 0.5 + i): a 1 m lattice offset by half a metre
    nyy, nxx = raw.shape; xs = gx0 + st * (np.arange(nxx) + .5); ys = gy0 + st * (np.arange(nyy) + .5)
    X, Y = np.meshgrid(xs, ys)
    S = Polygon(SP.SITE); d = SP.derived()
    inside = V.contains_xy(S, X, Y)
    pad = np.zeros_like(inside)
    for p in d['pad']: pad |= V.contains_xy(Polygon(p).buffer(PAD_GROW), X, Y)
    kept_poles = [(x, y) for x, y in SP.kept_poles_on_site()]
    pole = np.zeros_like(inside)
    for x, y in kept_poles: pole |= (X - x) ** 2 + (Y - y) ** 2 <= POLE_HOLD ** 2
    Z = raw.copy(); Z[pad] = SP.PAD_Z
    Z = solve(Z, inside & ~pad & ~pole, trend)
    # the arch feet: ground in [LEG_Z] on the LEG_R disc, and round it a cone of LEG_SLOPE out to where the lot already lies
    # inside that band (iterated: nodes outside the cone are held on it and the rest solved again, until none is)
    dl = np.min([np.hypot(X - x, Y - y) for x, y in SP.LEGS], axis=0)
    lo_b = SP.LEG_Z[0] - LEG_SLOPE * np.maximum(dl - SP.LEG_R, 0); hi_b = SP.LEG_Z[1] + LEG_SLOPE * np.maximum(dl - SP.LEG_R, 0)
    held = np.zeros_like(inside)
    for _ in range(40):
        out = inside & ~pad & ~pole & ~held & ((Z < lo_b - 1e-4) | (Z > hi_b + 1e-4))
        if not out.any(): break
        held |= out; Z[held] = np.clip(Z[held], lo_b[held], hi_b[held])
        Z = solve(Z, inside & ~pad & ~pole & ~held, trend)
    assert not (inside & ~pad & ~pole & ~held & ((Z < lo_b - 1e-3) | (Z > hi_b + 1e-3))).any(), 'arch feet: the cone did not settle'
    np.save(M / 'site' / 'grade.npy', Z); np.save(M / 'site' / 'grade_raw.npy', raw)
    info = {'origin': [float(xs[0]), float(ys[0])], 'step': float(st), 'shape': list(Z.shape), 'pad_z': SP.PAD_Z,
            'pad_grow': PAD_GROW, 'lambda': LAMBDA, 'trend_m': TREND_M, 'kept_poles': kept_poles, 'leg_z': SP.LEG_Z}
    json.dump(info, open(M / 'site' / 'grade.json', 'w'), indent=1)
    return Z, raw, inside, pad, xs, ys


def solve(Z, free, trend):
    """the membrane: every free node's height from its 4 neighbours (fixed ones as given) and the trend (LAMBDA)."""
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    Z = Z.copy(); nyy, nxx = Z.shape
    k = -np.ones(Z.shape, int); k[free] = np.arange(int(free.sum())); n = int(free.sum())
    rows, cols, vals = [], [], []; b = LAMBDA * trend[free].astype(float)
    fj, fi = np.nonzero(free)
    diag = np.full(n, LAMBDA)
    for dj, di in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        j2, i2 = fj + dj, fi + di; ok = (j2 >= 0) & (j2 < nyy) & (i2 >= 0) & (i2 < nxx)
        diag[ok] += 1.0
        nb = np.where(ok, k[np.clip(j2, 0, nyy - 1), np.clip(i2, 0, nxx - 1)], -1)
        f = ok & (nb >= 0)
        rows += list(k[fj[f], fi[f]]); cols += list(nb[f]); vals += [-1.0] * int(f.sum())
        fx = ok & (nb < 0)
        b[k[fj[fx], fi[fx]]] += Z[j2[fx], i2[fx]]                                    # a fixed neighbour (outside / pad / pole)
    A = sparse.csr_matrix((np.r_[diag, vals], (np.r_[np.arange(n), rows], np.r_[np.arange(n), cols])), shape=(n, n))
    Z[free] = spsolve(A, b)
    return Z


_L = {}
def _lattice(name):
    if name not in _L:
        info = json.load(open(M / 'site' / 'grade.json')); _L[name] = (np.load(M / 'site' / f'{name}.npy'), info['origin'], info['step'])
    return _L[name]


def _bilinear(name, x, y):
    Z, (ox, oy), st = _lattice(name)
    fx, fy = (x - ox) / st, (y - oy) / st
    i, j = int(math.floor(fx)), int(math.floor(fy)); i = min(max(i, 0), Z.shape[1] - 2); j = min(max(j, 0), Z.shape[0] - 2)
    tx, ty = min(max(fx - i, 0.0), 1.0), min(max(fy - j, 0.0), 1.0)
    return float(Z[j, i] * (1 - tx) * (1 - ty) + Z[j, i + 1] * tx * (1 - ty) + Z[j + 1, i] * (1 - tx) * ty + Z[j + 1, i + 1] * tx * ty)


def grade_z(x, y):
    """the new ground's height at world (x, y): bilinear on the 1 m lattice (Blender-safe: numpy only)."""
    return _bilinear('grade', x, y)


def raw_z(x, y):
    """Rockstar's ground (before the grade) at world (x, y), same lattice and interpolation."""
    return _bilinear('grade_raw', x, y)


def report(Z, raw, inside, pad, xs, ys):
    import sys; sys.path.insert(0, str(T)); import site_plan as SP
    from scipy import ndimage
    from shapely.geometry import Polygon
    import shapely as V
    gy, gx = np.gradient(Z); slope = np.hypot(gx, gy) * 100                         # percent
    X, Y = np.meshgrid(xs, ys)
    edge_d = ndimage.distance_transform_edt(inside)                                 # metres to the outline (inside)
    S = Polygon(SP.SITE)
    pad_in = np.zeros_like(inside)
    for p in SP.derived()['pad']: pad_in |= V.contains_xy(Polygon(p), X, Y)
    padg_d = ndimage.distance_transform_edt(~pad)                                    # metres to the grown pad
    lot = inside & ~pad
    open_lot = lot & (edge_d > 6) & (padg_d > 6)
    dz = (Z - raw)[inside]
    under = raw[pad_in]
    return {'pad_z': SP.PAD_Z, 'floor_top': SP.FLOOR_TOP, 'pad_flat_max_dev': float(np.abs(Z[pad] - SP.PAD_Z).max()),
            'lot_z': [round(float(Z[lot].min()), 2), round(float(Z[lot].max()), 2)],
            'slope_open_lot_pct': {'p50': round(float(np.percentile(slope[open_lot], 50)), 2), 'p95': round(float(np.percentile(slope[open_lot], 95)), 2),
                                   'max': round(float(slope[open_lot].max()), 2)},
            'slope_edge_band_pct': {'p95': round(float(np.percentile(slope[lot & (edge_d <= 6)], 95)), 2), 'max': round(float(slope[lot & (edge_d <= 6)].max()), 2)},
            'slope_round_pad_pct': {'p95': round(float(np.percentile(slope[lot & (padg_d <= 6)], 95)), 2), 'max': round(float(slope[lot & (padg_d <= 6)].max()), 2)},
            'cut_m3': round(float(np.clip(-dz, 0, None).sum())), 'fill_m3': round(float(np.clip(dz, 0, None).sum())),
            'max_cut_m': round(float(-dz.min()), 2), 'max_fill_m': round(float(dz.max()), 2),
            'old_ground_under_pad': [round(float(under.min()), 2), round(float(under.max()), 2)]}


def picture(Z, raw, inside, xs, ys):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    import sys; sys.path.insert(0, str(T)); import site_plan as SP
    fig, ax = plt.subplots(2, 1, figsize=(16, 11))
    ext = [xs[0] - .5, xs[-1] + .5, ys[0] - .5, ys[-1] + .5]
    for a, img, title, cm, lim in ((ax[0], np.where(inside, Z, np.nan), 'new ground z (grade)', 'terrain', (30, 35)),
                                   (ax[1], np.where(inside, Z - raw, np.nan), 'fill (+) / cut (-) m', 'RdBu_r', (-2.5, 2.5))):
        im = a.imshow(img, origin='lower', extent=ext, cmap=cm, vmin=lim[0], vmax=lim[1]); fig.colorbar(im, ax=a, shrink=.8)
        a.plot(*zip(*(SP.SITE + [SP.SITE[0]])), 'k-', lw=1)
        for p in SP.derived()['pad']: a.plot(*zip(*(p + [p[0]])), 'm-', lw=1)
        bl = SP.derived()['building']; a.plot(*zip(*(bl + [bl[0]])), 'k--', lw=1)
        a.contour(xs, ys, np.where(inside, Z, np.nan), levels=np.arange(30, 36, .25), colors='k', linewidths=.3)
        a.set_title(title); a.set_aspect('equal'); a.set_xlim(1000, 1312); a.set_ylim(3538, 3646)
    plt.tight_layout(); plt.savefig(M / 'site' / 'grade.png', dpi=80); plt.close()


if __name__ == '__main__':
    Z, raw, inside, pad, xs, ys = build()
    picture(Z, raw, inside, xs, ys)
    print('GRADE_PASS', json.dumps(report(Z, raw, inside, pad, xs, ys)))
