"""Area 4 (Jail I) light-gap audit, portal-aware (jc-interiors' jc3_gap_check.py, copied and pointed at jc_jail; playbook 07): what the
game DRAWS from inside each room. A ray from a point in room R sees a face only if it belongs to R's own drawable, faces the ray (one-
sided) and is opaque (glass, kind 1, is passed). A ray crossing one of R's portals before any face leaves through it - fine. A ray that
meets nothing is a GAP.
  pass 1: every room zone, points on a 1.5 m grid at floor + 0.4 / 1.7 and 0.4 m under the ceiling (and under the tier soffit in the
          block), 300 directions each; points inside a solid or not over the room's own floor are skipped
  pass 2: the seam scan - 0.15 m in front of every lining of every room, every 0.5 m along it and 0.6 m up, rays straight at the wall and
          +-30 deg (corner slits, a wall stopping short, the cells' partitions against the front wall)
Proof: --plant deletes the booking hall's ceiling tile faces; the check must report gaps from the booking hall, or it fails itself.
Run: py -3 jj_gap_check.py [--plant]   (pass line JJ_GAP_PASS / JJ_GAP_PLANT_FOUND)"""
import json, math, sys
from pathlib import Path
import numpy as np
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
import jj_plan as J, jj_fit as JF, jc_frame as F
OUT = JL / OD; L = json.load(open(OUT / 'jj_layout.json')); PLANT = '--plant' in sys.argv
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def setup(room):
    global OPQ, E1, E2, NRM, PORT
    n = ('jc_jail_' + room).lower(); T = lot(np.load(OUT / f'tris_{n}.npy').astype(np.float64)); K = np.load(OUT / f'mats_{n}.npy')
    if PLANT and room == 'book':
        nz = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2]; c = T.mean(1)
        keep = ~((nz < 0) & (np.abs(c[:, 2] - JF.BOOK_CEIL) < 0.02)); print('PLANT removes', int((~keep).sum()), 'triangles (the booking ceiling)'); T, K = T[keep], K[keep]
    OPQ = T[K != 1]; E1 = OPQ[:, 1] - OPQ[:, 0]; E2 = OPQ[:, 2] - OPQ[:, 0]; NRM = np.cross(E1, E2)
    PORT = [np.array(p['corners'], np.float64) for p in L['portals'] if room in (p['from'], p['to'])]
def hit_tris(o, D):
    best = np.full(len(D), np.inf)
    for i in range(0, len(OPQ), 4000):
        e1, e2, v0, nr = E1[i:i + 4000], E2[i:i + 4000], OPQ[i:i + 4000, 0], NRM[i:i + 4000]
        pv = np.cross(D[:, None, :], e2[None]); det = (e1[None] * pv).sum(-1); front = (D[:, None, :] * nr[None]).sum(-1) < 0
        ok = (np.abs(det) > 1e-12) & front; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = o[None, None, :] - v0[None]; u = (tv * pv).sum(-1) * inv
        qv = np.cross(tv, e1[None]); v = (D[:, None, :] * qv).sum(-1) * inv; t = (e2[None] * qv).sum(-1) * inv
        ok &= (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 1e-4)
        best = np.minimum(best, np.where(ok, t, np.inf).min(1))
    return best
def hit_portals(o, D):
    best = np.full(len(D), np.inf)
    for C in PORT:
        n = np.cross(C[1] - C[0], C[2] - C[0]); n /= np.linalg.norm(n); den = D @ n
        with np.errstate(divide='ignore', invalid='ignore'): t = ((C[0] - o) @ n) / den
        P = o[None] + t[:, None] * D; lo = C.min(0) - 1e-3; hi = C.max(0) + 1e-3
        ok = (t > 1e-4) & np.all((P >= lo) & (P <= hi), 1); best = np.minimum(best, np.where(ok, t, np.inf))
    return best
SOL = np.load(OUT / 'solids.npy')
def inside_solid(o): return bool(np.any(np.all(SOL[:, :3] < o - 1e-3, 1) & np.all(SOL[:, 3:] > o + 1e-3, 1)))
def dirs(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], -1)
GAPS = []
def probe(o, D, tag):
    tt = hit_tris(o, D); tp = hit_portals(o, D); bad = np.isinf(tt) & np.isinf(tp)
    for d in D[bad]: GAPS.append({'pass': tag, 'from': [round(x, 2) for x in o], 'dir': [round(x, 3) for x in d]})
    return int(bad.sum())
D1 = dirs(300); down = np.array([[0, 0, -1.0]]); kept = 0; per = {}; seam = 0
for room, zs in L['zones'].items():
    setup(room); n0 = len(GAPS)
    for (u0, u1, v0, v1, z0, z1), (cu0, cu1, cv0, cv1) in zip(zs, JF.clear(room)):
        zl = [z0 + 0.4, z0 + 1.7, z1 - 0.4] + ([J.TIER2 + 0.4, J.TIER2 + 1.7, J.TIER2 - J.TIER_T - 0.4] if room == 'block' else [])
        for u in np.arange(cu0 + 0.35, cu1 - 0.2, 1.5):
            for v in np.arange(cv0 + 0.35, cv1 - 0.2, 1.5):
                for z in zl:
                    o = np.array((u, v, z))
                    if inside_solid(o) or not (hit_tris(o, down)[0] < 3.2): continue
                    kept += 1; probe(o, D1, room)
        # pass 2: the seam scan along this rect's linings
        for side in ('u0', 'u1', 'v0', 'v1'):
            at = {'u0': cu0 + 0.15, 'u1': cu1 - 0.15, 'v0': cv0 + 0.15, 'v1': cv1 - 0.15}[side]; out = -1 if side[1] == '0' else 1
            a0, a1 = (cv0, cv1) if side[0] == 'u' else (cu0, cu1)
            for a in np.arange(a0 + 0.1, a1 - 0.05, 0.5):
                for z in np.arange(z0 + 0.3, z1 - 0.1, 0.6):
                    o = np.array([at, a, z]) if side[0] == 'u' else np.array([a, at, z])
                    if inside_solid(o): continue
                    ds = []
                    for ang in (0.0, -30.0, 30.0):
                        r = math.radians(ang); ds.append([out * math.cos(r), math.sin(r), 0.0] if side[0] == 'u' else [math.sin(r), out * math.cos(r), 0.0])
                    seam += probe(o, np.array(ds), room + ' seam')
    per[room] = len(GAPS) - n0
res = {'grid_points': kept, 'rays': kept * len(D1), 'gaps': len(GAPS), 'seam_gaps': seam, 'per_room': per}
json.dump({'summary': res, 'gaps': GAPS[:500]}, open(OUT / ('gap_check_plant.json' if PLANT else 'gap_check.json'), 'w'), indent=1)
if PLANT:
    assert per.get('book', 0) > 0, 'PLANTED HOLE NOT FOUND (booking ceiling): the gap check is broken'
    print('JJ_GAP_PLANT_FOUND', json.dumps(res)); sys.exit(0)
print(('JJ_GAP_PASS ' if not GAPS else 'JJ_GAP_FAIL ') + json.dumps(res))
for g in GAPS[:20]: print(' ', g)
sys.exit(1 if GAPS else 0)
