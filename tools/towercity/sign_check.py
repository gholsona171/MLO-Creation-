"""Tower City signage audit (Antonio 2026-10-24: "CLEVELAND WIRELESS" through the gallery soffit, "TERMINAL TAILORS" cut off by the
shopfront frame, "LIFTS - STAIRS - SUITES" cut off, "HIGBEE GALLERY" partly hidden). Every sign panel the builds made
(work/l1, work/l2 signs.json - tc_kit.sign records each one, lot frame) is checked against every exported triangle of every
drawable (tris_*.npy + mats_*.npy kinds) and every placed prop (layout props, boxes from survey/arch_ytyp.json):
  CLIP   something crosses the sign: a triangle or prop box inside the panel's slab (rect inset 1 cm, +-3 cm off its plane)
  FRONT  something stands in front of the panel within 1.5 m along its normal (frames, soffits, glass, posts, another sign)
  VIEW   (signs 1 m wide or more) seen from 2.5 m straight on more than a third of it is hidden, or from all the viewer's directions (straight, +-30 deg
         aside, 25 deg from below) more than two thirds
  WALL   nothing behind it within 0.25 m (a sign must hang on something: a wall, a fascia, a beam)
  TEXT   (signs 1.5 m wide or more) its letters come out smaller than 12 cm (sign_tex.py shrinks a long name to the width: wrap it or give it room)
Glass counts for CLIP and FRONT (a sign behind or through glass is cut off by its frame / reads as behind glass), not for VIEW.
Usage: py -3 sign_check.py [--list]  -> work/l2/sign_report.json; exit 1 on any CLIP / FRONT / VIEW / WALL / TEXT."""
import json, math, sys
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; T0 = W.parent
ORG, H = (71.0, -884.0), math.radians(69.5); ch, sh = math.cos(H), math.sin(H)
DEBUG = sys.argv[sys.argv.index('--debug') + 1] if '--debug' in sys.argv else ''
SLAB, INSET, FRONT_D, VIEW_D, WALL_D, MIN_TEXT = 0.025, 0.01, 1.5, 2.5, 0.25, 0.12
def lot(t):
    x, y = t[..., 0] - ORG[0], t[..., 1] - ORG[1]; return np.stack([x * ch + y * sh, -x * sh + y * ch, t[..., 2]], -1)
TR, KD = [], []
for lotd in ('l1', 'l2'):
    for f in sorted((W / lotd).glob('tris_*.npy')):
        TR.append(lot(np.load(f).astype(np.float64)))
        mf = f.with_name('mats_' + f.stem[5:] + '.npy'); KD.append(np.load(mf) if mf.exists() else np.zeros(len(TR[-1]), np.int8))
TR, KD = np.concatenate(TR), np.concatenate(KD)
TLO, THI = TR.min(1), TR.max(1)
BB = {k.lower(): v for k, v in json.load(open(T0 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
def pbox(p):
    """a placed prop as an oriented box: centre, axes (3x3, rows), half sizes."""
    v = BB.get(p['model'].lower())
    if not v: return None
    f = lambda s: np.array([float(x[2:]) for x in s.split()]); lo, hi = f(v['bbMin']), f(v['bbMax'])
    sc = p.get('scale'); kx, kz = (sc[0], sc[1]) if isinstance(sc, list) else ((sc, sc) if sc else (1.0, 1.0))
    lo, hi = lo * [kx, kx, kz], hi * [kx, kx, kz]; t = math.radians(p['heading'])
    R = np.array([[math.cos(t), math.sin(t), 0], [-math.sin(t), math.cos(t), 0], [0, 0, 1]])
    c = np.array(p['pos']) + R.T @ ((lo + hi) / 2); return c, R, (hi - lo) / 2, p['model']
PROPS = [b for L in ('l1', 'l2') for p in json.load(open(W / L / f'{L}_layout.json'))['props'] for b in [pbox(p)] if b and p['model'] != 'tc_prop_mirror']
SIGNS = [dict(s, lot=L) for L in ('l1', 'l2') if (W / L / 'signs.json').exists() for s in json.load(open(W / L / 'signs.json'))]
def frame(s):
    P = np.array(s['pts'], float); o = P[0]; ex = P[1] - P[0]; ey = P[3] - P[0]; w, h = np.linalg.norm(ex), np.linalg.norm(ey)
    ex, ey = ex / w, ey / h; n = np.cross(ex, ey); return o, ex, ey, n / np.linalg.norm(n), w, h
def clip_poly(poly, n, d):
    """keep the part of a convex polygon where n.x <= d."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; da, db = n @ a - d, n @ b - d
        if da <= 0: out.append(a)
        if (da < 0) != (db < 0) and abs(da - db) > 1e-12: out.append(a + (b - a) * (da / (da - db)))
    return out
def in_slab(tri, o, ex, ey, n, w, h, z0=-SLAB, z1=SLAB):
    poly = list(tri)
    for nn, dd in ((-ex, -(ex @ o) - INSET), (ex, ex @ o + w - INSET), (-ey, -(ey @ o) - INSET), (ey, ey @ o + h - INSET), (-n, -(n @ o) - z0), (n, n @ o + z1)):
        poly = clip_poly(poly, nn, dd)
        if not poly: return False
    return True
def ray_tris(o, d, L, idx):
    """distances along the ray to the triangles idx it crosses (two-sided, Moller-Trumbore)."""
    if not len(idx): return np.zeros(0)
    A, B, C = TR[idx, 0], TR[idx, 1], TR[idx, 2]; e1, e2 = B - A, C - A; p = np.cross(d, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); s = o - A; u = (s * p).sum(1) * inv
    q = np.cross(s, e1); v = (q * d).sum(1) * inv; t = (e2 * q).sum(1) * inv
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < L); return t[m]
def ray_box(o, d, L, b):
    c, R, hs, _ = b; lo_, ld = R @ (o - c), R @ d; t0, t1 = 0.0, L
    for k in range(3):
        if abs(ld[k]) < 1e-12:
            if abs(lo_[k]) > hs[k]: return False
            continue
        a, bb = (-hs[k] - lo_[k]) / ld[k], (hs[k] - lo_[k]) / ld[k]; t0, t1 = max(t0, min(a, bb)), min(t1, max(a, bb))
        if t0 > t1: return False
    return True
def box_in_slab(b, o, ex, ey, n, w, h):
    c, R, hs, _ = b; pts = [c + R.T @ (hs * np.array(sg)) for sg in [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]]
    loc = np.array([[(p - o) @ ex, (p - o) @ ey, (p - o) @ n] for p in pts])
    return loc[:, 0].max() > INSET and loc[:, 0].min() < w - INSET and loc[:, 1].max() > INSET and loc[:, 1].min() < h - INSET and loc[:, 2].max() > -SLAB and loc[:, 2].min() < SLAB
def text_height(s):
    """sign_tex.py's font size (metres) for this sign's lines (Arial Bold advance ~0.66 em per char, caps)."""
    lines = s['lines']; fs = s['h'] / len(lines) * 0.62; longest = max(len(t) for t in lines)
    return min(fs, s['w'] * 0.92 / max(1, longest * 0.66)) * 0.72        # cap height ~0.72 em
rep = []
for s in SIGNS:
    o, ex, ey, n, w, h = frame(s); P = np.array(s['pts'])
    lo = P.min(0) - FRONT_D - VIEW_D; hi = P.max(0) + FRONT_D + VIEW_D
    near = np.nonzero((THI >= lo).all(1) & (TLO <= hi).all(1))[0]
    own = near[(np.abs((TR[near] - o) @ n) < 0.003).all(1)]                 # the panel's own triangles (and anything on its plane: checked as CLIP below)
    ownset = set(own[[((TR[i] - o) @ ex).min() > -0.01 and ((TR[i] - o) @ ex).max() < w + 0.01 and ((TR[i] - o) @ ey).min() > -0.01 and ((TR[i] - o) @ ey).max() < h + 0.01 for i in own]].tolist())
    cand = np.array([i for i in near if i not in ownset], np.int64)
    issues = []
    clip = [i for i in cand if KD[i] != 2 and in_slab(TR[i], o, ex, ey, n, w, h)]
    pb = [b for b in PROPS if np.all(np.abs(b[0] - (P.min(0) + P.max(0)) / 2) < (P.max(0) - P.min(0)) / 2 + 3.0)]
    clipp = [b[3] for b in pb if box_in_slab(b, o, ex, ey, n, w, h)]
    if clip or clipp: issues.append(('CLIP', len(clip), sorted(set(clipp)), [round(float(x), 2) for x in TR[clip[0]].mean(0)] if clip else None))
    if DEBUG and DEBUG in s['name']:
        for i in clip: print('   clip tri', np.round(TR[i], 2).tolist(), 'kind', KD[i])
    samp = [o + ex * w * (i + 0.5) / 8 + ey * h * (j + 0.5) / 3 for i in range(8) for j in range(3)]
    fr = 0; vb = 0; vs = 0; wl = 0; nv = 0
    up = np.array((0, 0, 1.0)); side = np.cross(up, n); side = side / (np.linalg.norm(side) + 1e-12) if np.linalg.norm(side) > 1e-6 else ex
    views = [n] + [x / np.linalg.norm(x) for x in [n * math.cos(a) + side * math.sin(a) for a in (0.52, -0.52)] + [n * math.cos(0.44) - up * math.sin(0.44)]]
    opq = cand[KD[cand] == 0] if len(cand) else cand; nong = cand[KD[cand] != 2] if len(cand) else cand
    for p in samp:
        q = p + n * 0.004
        if len(ray_tris(q, n, FRONT_D, nong)) or any(ray_box(q, n, FRONT_D, b) for b in pb): fr += 1
        for d in views:
            nv += 1
            if len(ray_tris(q, d, VIEW_D, opq)) or any(ray_box(q, d, VIEW_D, b) for b in pb):
                vb += 1; vs += d is views[0]
        if not len(ray_tris(p - n * 0.004, -n, WALL_D, opq)): wl += 1
    if fr: issues.append(('FRONT', fr, 24))
    if s['w'] >= 1.0 and (vs > len(samp) / 3 or vb > 2 * nv / 3): issues.append(('VIEW', vs, len(samp), vb, nv))   # (signage; a lift's button panel faces the cab's far wall 2.3 m away)
    if wl > 4 and s['room'] not in ('limbo',): issues.append(('WALL', wl, 24))
    th = text_height(s)
    if th < MIN_TEXT and s['w'] >= 1.5: issues.append(('TEXT', round(th, 3)))      # (small fixtures - lift buttons, door numbers - are not signage)
    rep.append({'name': s['name'], 'room': s['room'], 'lot': s['lot'], 'lines': s['lines'], 'w': s['w'], 'h': s['h'],
                'centre': [round(float(x), 2) for x in (P.min(0) + P.max(0)) / 2], 'normal': [round(float(x), 2) for x in n], 'issues': issues})
bad = [r for r in rep if r['issues']]
json.dump(rep, open(W / 'l2/sign_report.json', 'w'), indent=1)
print(f'SIGN_CHECK {len(rep)} signs, {len(bad)} with problems', 'PASS' if not bad else 'FAIL')
for r in bad[: (999 if '--list' in sys.argv else 60)]: print(f"  {r['name'][:38]:38s} {' / '.join(r['lines'])[:34]:34s} {r['centre']} {r['issues']}")
sys.exit(1 if bad else 0)
