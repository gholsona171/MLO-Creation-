"""Phase 3 light-gap audit (portal-aware, playbook 07): what the game DRAWS from inside each room. A ray from a point in a room sees
a face only if the face is turned towards it (faces are one-sided in game) and is opaque (see-through glass, kind 1 in mats_*.npy,
is passed through). A ray that crosses one of the room's exit portals before meeting a face leaves through it (the exterior is drawn
there) - fine. A ray that meets nothing is a GAP (sky / void at that angle).
  pass 1: points on a 2.5 m grid over each room at 0.4 / 1.7 m and 1 m under the roof portal, 400 directions each
  pass 2: the seam scan - points 0.2 m in front of every lining, every 0.5 m along it and 1 m up, rays straight at the wall and
          +-30 deg either way (corner slits, a wall stopping short)
Proof (playbook 07: a probe proves it ran): --plant deletes the floor band's top along the north glass (a 0.6 m slit the length of
the lawn wall: the 'light strip' kind of defect); the check must report gaps there, or the check itself fails.
Run: py -3 jc3_gap_check.py [--plant]   (pass line JC3_GAP_PASS / JC3_GAP_PLANT_FOUND)"""
import json, math, sys
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_plan as JP
sys.path.insert(0, str(P3.parent)); import jc_frame as F
OUT = P3 / 'out'
L = json.load(open(OUT / 'jc3_layout.json'))
PLANT = '--plant' in sys.argv
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
T = []; K = []
for n in L['drawables']:
    T.append(lot(np.load(OUT / f'tris_{n}.npy').astype(np.float64))); K.append(np.load(OUT / f'mats_{n}.npy'))
T = np.concatenate(T); K = np.concatenate(K)
if PLANT:
    c = T.mean(1); keep = ~((c[:, 1] > JP.VB1 - JP.BAND) & (c[:, 1] < JP.VB1) & (np.abs(c[:, 2] - JP.G) < 0.01) & (c[:, 0] > JP.UB0) & (c[:, 0] < JP.UB1))
    print('PLANT removes', int((~keep).sum()), 'triangles'); T, K = T[keep], K[keep]
OPQ = T[K != 1]
E1 = OPQ[:, 1] - OPQ[:, 0]; E2 = OPQ[:, 2] - OPQ[:, 0]; NRM = np.cross(E1, E2)
PORT = []
for p in L['portals']:
    C = np.array(p['corners'], np.float64); PORT.append(C)
def hit_tris(o, D):
    """nearest front-facing opaque hit per ray (inf if none). o (3,), D (n, 3)."""
    best = np.full(len(D), np.inf)
    for i in range(0, len(OPQ), 4000):
        e1, e2, v0, nr = E1[i:i + 4000], E2[i:i + 4000], OPQ[i:i + 4000, 0], NRM[i:i + 4000]
        pv = np.cross(D[:, None, :], e2[None]); det = (e1[None] * pv).sum(-1)
        front = (D[:, None, :] * nr[None]).sum(-1) < 0
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
def dirs(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], -1)
GAPS = []
def probe(o, D, tag):
    tt = hit_tris(o, D); tp = hit_portals(o, D); bad = np.isinf(tt) & np.isinf(tp)
    for d in D[bad]: GAPS.append({'pass': tag, 'from': [round(x, 2) for x in o], 'dir': [round(x, 3) for x in d]})
    return int(bad.sum())
def in_room(u, v):
    return (JP.UA0 < u < JP.UA1 and JP.VA0 < v < JP.VA1) or (JP.UB0 < u < JP.UB1 and JP.VB0 < v < JP.VB1)
# pass 1
pts = []
for u in np.arange(JP.UA0 + 1.0, JP.UA1 - 0.5, 2.5):
    for v in np.arange(JP.VA0 + 1.0, JP.VB1 - 0.5, 2.5):
        if in_room(u, v):
            for z in (JP.G + 0.4, JP.G + 1.7, JP.PORTAL_Z - 1.0): pts.append((u, v, z))
D1 = dirs(400); kept = 0; down = np.array([[0, 0, -1.0]]); up = np.array([[0, 0, 1.0]])
for p in pts:
    o = np.array(p)
    if not (hit_tris(o, down)[0] < (o[2] - JP.G) + 0.05): continue           # inside a solid (a desk, a fin): not in the room
    kept += 1; probe(o, D1, 'grid')
# pass 2: the seam scan along every lining
n2 = 0
for w, (axis, (lo, hi), a0, a1, b) in JP.WALLS.items():
    face = hi if (axis == 'u' and lo < 0) or w == 'police' else lo; inward = 1 if face == hi else -1
    for a in np.arange(a0 + 0.1, a1 - 0.05, 0.5):
        for z in np.arange(JP.G + 0.3, JP.PORTAL_Z - 0.2, 1.0):
            off = face + inward * (JP.FIN_P + 0.05)
            o = np.array([off, a, z]) if axis == 'u' else np.array([a, off, z])
            if not in_room(o[0], o[1]): continue
            ds = []
            for ang in (0.0, -30.0, 30.0):
                r = math.radians(ang); out = -inward
                ds.append([out * math.cos(r), math.sin(r), 0.0] if axis == 'u' else [math.sin(r), out * math.cos(r), 0.0])
            n2 += probe(o, np.array(ds), 'seam')
res = {'grid_points': kept, 'rays': kept * len(D1), 'gaps': len(GAPS), 'seam_gaps': n2}
json.dump({'summary': res, 'gaps': GAPS[:500]}, open(OUT / ('gap_check_plant.json' if PLANT else 'gap_check.json'), 'w'), indent=1)
if PLANT:
    near = [g for g in GAPS if g['from'][1] > JP.VB1 - 6.0]
    assert near, 'PLANTED HOLE NOT FOUND: the gap check is broken'
    print('JC3_GAP_PLANT_FOUND', json.dumps(res))
else:
    print(('JC3_GAP_PASS ' if not GAPS else 'JC3_GAP_FAIL ') + json.dumps(res))
    for g in GAPS[:20]: print(' ', g)
