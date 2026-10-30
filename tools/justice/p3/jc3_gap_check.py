"""Phase 3 light-gap audit (portal-aware, playbook 07): what the game DRAWS from inside each room. A ray from a point in room R sees
a face only if the face belongs to R's own drawable, is turned towards it (faces are one-sided in game) and is opaque (see-through
glass, kind 1 in mats_*.npy, is passed through). A ray that crosses one of R's portals (to limbo or another room) before meeting a
face leaves through it - fine: what lies beyond is drawn through that portal. A ray that meets nothing is a GAP (void at that angle).
  pass 1: every room (out/jc3_layout.json zones), points on a grid (galleria 2.5 m, the tower's rooms 2.0 m) at 0.4 / 1.7 m and
          0.6 m under the top, 300 directions each
  pass 2: the galleria's seam scan - points 0.2 m in front of every lining, every 0.5 m along it and 1 m up, rays straight at the
          wall and +-30 deg either way (corner slits, a wall stopping short)
Proof (playbook 07: a probe proves it ran): --plant galleria deletes the floor band's top along the north glass (a 0.6 m slit);
--plant tower deletes courtroom A's ceiling. Each must be reported, or the check itself fails.
Run: py -3 jc3_gap_check.py [--plant galleria|tower]   (pass line JC3_GAP_PASS / JC3_GAP_PLANT_FOUND)"""
import json, math, sys
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_plan as JP
sys.path.insert(0, str(P3.parent)); import jc_frame as F
OUT = P3 / 'out'
L = json.load(open(OUT / 'jc3_layout.json'))
PLANT = sys.argv[sys.argv.index('--plant') + 1] if '--plant' in sys.argv else None
ONLY = set(sys.argv[sys.argv.index('--rooms') + 1].split(',')) if '--rooms' in sys.argv else None   # (debugging: just these rooms)
import jc3_tower as JT
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def load(names):
    T = []; K = []
    for n in names:
        T.append(lot(np.load(OUT / f'tris_{n}.npy').astype(np.float64))); K.append(np.load(OUT / f'mats_{n}.npy'))
    return np.concatenate(T), np.concatenate(K)
def setup(room, plant=None):
    """this room's own opaque faces (one-sided) + its portals: a face of another room is drawn only through a portal."""
    global OPQ, E1, E2, NRM, PORT
    T, K = load([('jc_courts_' + room).lower()])
    if plant == 'galleria' and room == 'galleria':
        c = T.mean(1); keep = ~((c[:, 1] > JP.VB1 - JP.BAND) & (c[:, 1] < JP.VB1) & (np.abs(c[:, 2] - JP.G) < 0.01) & (c[:, 0] > JP.UB0) & (c[:, 0] < JP.UB1))
        print('PLANT removes', int((~keep).sum()), 'triangles (the floor band along the north glass)'); T, K = T[keep], K[keep]
    if plant == 'tower' and room == 'crtA':
        nz = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2]; c = T.mean(1)
        keep = ~((nz < 0) & (np.abs(c[:, 2] - (JT.F3 + JT.CEIL_T - 0.2)) < 0.05))
        print('PLANT removes', int((~keep).sum()), 'triangles (courtroom A ceiling)'); T, K = T[keep], K[keep]
    OPQ = T[K != 1]; E1 = OPQ[:, 1] - OPQ[:, 0]; E2 = OPQ[:, 2] - OPQ[:, 0]; NRM = np.cross(E1, E2)
    PORT = [np.array(p['corners'], np.float64) for p in L['portals'] if room in (p['from'], p['to'])]
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
SOL = np.load(OUT / 'solids.npy') if (OUT / 'solids.npy').exists() else np.zeros((0, 6))
def inside_solid(o):
    if len(SOL) and np.any(np.all(SOL[:, :3] < o - 1e-3, 1) & np.all(SOL[:, 3:] > o + 1e-3, 1)): return True    # inside a solid box of the build
    return _inside_by_faces(o)
def _inside_by_faces(o):
    """True if the nearest face along any axis ray from o is turned AWAY from o (o is inside a closed solid: a wall, a shaft, a desk)."""
    D = np.array([[1.0, 0, 0], [-1.0, 0, 0], [0, 1.0, 0], [0, -1.0, 0], [0, 0, 1.0], [0, 0, -1.0]])
    for d in D:
        best, back = np.inf, False
        for i in range(0, len(OPQ), 4000):
            e1, e2, v0, nr = E1[i:i + 4000], E2[i:i + 4000], OPQ[i:i + 4000, 0], NRM[i:i + 4000]
            pv = np.cross(d, e2); det = (e1 * pv).sum(-1); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
            tv = o - v0; u = (tv * pv).sum(-1) * inv; qv = np.cross(tv, e1); v = (d * qv).sum(-1) * inv; t = (e2 * qv).sum(-1) * inv
            ok &= (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 1e-4)
            if ok.any():
                j = np.argmin(np.where(ok, t, np.inf))
                if t[j] < best: best, back = t[j], (nr[j] @ d) > 0
        if back: return True
    return False
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
def in_room(u, v):
    return (JP.UA0 < u < JP.UA1 and JP.VA0 < v < JP.VA1) or (JP.UB0 < u < JP.UB1 and JP.VB0 < v < JP.VB1)
D1 = dirs(300); down = np.array([[0, 0, -1.0]]); kept = 0; per = {}
SAMPLE = {}
for room, zs in L['zones'].items():
    if ONLY and room not in ONLY: continue
    setup(room, PLANT); n0 = len(GAPS)
    for u0, u1, v0, v1, z0, z1 in zs:
        for u in np.arange(u0 + 0.5, u1 - 0.3, 2.0 if room != 'galleria' else 2.5):
            for v in np.arange(v0 + 0.5, v1 - 0.3, 2.0 if room != 'galleria' else 2.5):
                for z in (z0 + 0.4, z0 + 1.7, z1 - 0.6):
                    o = np.array((u, v, z))
                    if not (hit_tris(o, down)[0] < (o[2] - z0) + 0.05) or inside_solid(o): continue   # not over the floor / inside a solid
                    kept += 1; probe(o, D1, room)
    per[room] = len(GAPS) - n0; SAMPLE[room] = GAPS[n0:n0 + 40]
# pass 2: the galleria's seam scan along every lining
n2 = 0
if not ONLY: setup('galleria', PLANT)
for w, (axis, (lo, hi), a0, a1, b) in (JP.WALLS.items() if not ONLY else []):
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
res = {'grid_points': kept, 'rays': kept * len(D1), 'gaps': len(GAPS), 'seam_gaps': n2, 'per_room': per}
json.dump({'summary': res, 'gaps': GAPS[:500], 'per_room_samples': SAMPLE}, open(OUT / (f'gap_check_plant_{PLANT}.json' if PLANT else 'gap_check_rooms.json' if ONLY else 'gap_check.json'), 'w'), indent=1)
if PLANT == 'galleria':
    near = [g for g in GAPS if g['pass'] == 'galleria' and g['from'][1] > JP.VB1 - 6.0]
    assert near, 'PLANTED HOLE NOT FOUND: the gap check is broken'
    print('JC3_GAP_PLANT_FOUND', json.dumps(res))
elif PLANT == 'tower':
    near = [g for g in GAPS if g['pass'] == 'crtA']
    assert near, 'PLANTED HOLE NOT FOUND (courtroom A ceiling): the gap check is broken'
    print('JC3_GAP_PLANT_FOUND', json.dumps(res))
else:
    print(('JC3_GAP_PASS ' if not GAPS else 'JC3_GAP_FAIL ') + json.dumps(res))
    for g in GAPS[:20]: print(' ', g)
