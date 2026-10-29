"""Area 4 (Jail I) offline gates on the BUILT files (playbook 07: every gate is run on a planted defect first and must find it).
  roomids   every collision triangle of jc_jail.ybn (CodeWalker XML of the built file) carries a room id >= 1, every room id is present,
            and a triangle whose centre lies in exactly one room's zone carries THAT room's id. Plant: one BVH child's id swapped.
  ground    drawn vs walked, per room on a 0.25 m grid from two heights (the floor + 2.0, the upper tier + 2.0): the top up-facing drawn
            face (tris_*.npy, opaque) against the top up-facing collision face. MISMATCH > 5 cm (stairs: > one riser), NOCOL (drawn,
            nothing to stand on), HOLE (nothing drawn under a point of the room). Plant: a 1 x 1 m patch of the booking floor's collision cut.
  drive     the sally port drive (jj_plan.DRIVE_PATH, VEHICLES): each vehicle's swept box (+0.3 m each side, floor + 0.15 .. roof + 0.2,
            from the street to its stop) against every built triangle - ours (drawn + collision) and Jail I's exterior (work/p2/out,
            drawn + collision). Plant: a 0.5 m pillar box in the bay must be hit.
Run: py -3 jj_gates.py roomids|ground|drive [--plant]   (pass lines JJ_<GATE>_PASS / JJ_<GATE>_PLANT_FOUND)"""
import json, math, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
JL = Path(__file__).resolve().parent; WK = JL.parent; sys.path[:0] = [str(JL), str(WK)]
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
import jj_plan as J, jj_fit as JF, jc_frame as F
OUT = JL / OD; PLANT = '--plant' in sys.argv; GATE = sys.argv[1]
L = json.load(open(OUT / 'jj_layout.json'))
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def ybn(path):
    """(tris (n,3,3) MLO-local = lot frame, room id per tri, child index per tri) from a CodeWalker ybn XML."""
    r = ET.parse(path).getroot(); T, R_, C = [], [], []
    for ci, ch in enumerate(r.iter('Item')):
        if ch.get('type') not in ('GeometryBVH', 'Geometry'): continue
        gc = ch.find('GeometryCenter'); off = np.array([float(gc.get(k)) for k in 'xyz'])
        V = np.array([[float(x) for x in l.split(',')] for l in ch.find('Vertices').text.strip().split('\n')]) + off
        rooms = [int(m.find('RoomID').get('value')) for m in ch.find('Materials')]
        for t in ch.find('Polygons'):
            if t.tag != 'Triangle': continue
            T.append(V[[int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))]]); R_.append(rooms[int(t.get('m'))]); C.append(ci)
    return np.array(T), np.array(R_), np.array(C)
def drawn():
    T, K = [], []
    for d in L['drawables']:
        T.append(lot(np.load(OUT / f'tris_{d}.npy').astype(np.float64))); K.append(np.load(OUT / f'mats_{d}.npy'))
    return np.concatenate(T), np.concatenate(K)
def zone_of(p, e=0.02):
    """the rooms whose zone holds p STRICTLY (e inside its region: a face on a shared boundary belongs to neither test)."""
    hits = [k for k, zs in L['zones'].items() for z in zs if z[0] + e < p[0] < z[1] - e and z[2] + e < p[1] < z[3] - e and z[4] - J.SLAB_T + e < p[2] < z[5] + J.ROOF_T - e]
    return hits
def down(T, pts, up_only=True):
    """the top hit z (below each point) of a ray straight down onto up-facing faces of T (nan if none)."""
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); keep = n[:, 2] > 1e-9 if up_only else np.abs(n[:, 2]) > 1e-9
    T = T[keep]; out = np.full(len(pts), np.nan)
    a, b, c = T[:, 0, :2], T[:, 1, :2], T[:, 2, :2]
    lo = np.minimum(np.minimum(a, b), c); hi = np.maximum(np.maximum(a, b), c)
    for i, p in enumerate(pts):
        m = np.all(lo <= p[:2] + 1e-9, 1) & np.all(hi >= p[:2] - 1e-9, 1)
        if not m.any(): continue
        t = T[m]; v0, v1, v2 = t[:, 0], t[:, 1], t[:, 2]
        d = (v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1])
        w0 = ((v1[:, 1] - v2[:, 1]) * (p[0] - v2[:, 0]) + (v2[:, 0] - v1[:, 0]) * (p[1] - v2[:, 1])) / d
        w1 = ((v2[:, 1] - v0[:, 1]) * (p[0] - v2[:, 0]) + (v0[:, 0] - v2[:, 0]) * (p[1] - v2[:, 1])) / d
        w2 = 1 - w0 - w1; ok = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        z = w0 * v0[:, 2] + w1 * v1[:, 2] + w2 * v2[:, 2]; ok &= z <= p[2] + 1e-6
        if ok.any(): out[i] = z[ok].max()
    return out
def roomids():
    T, R_, C = ybn(OUT / 'xml/jc_jail.ybn.xml')
    if PLANT:
        c0 = C[0]; R_ = R_.copy(); R_[C == c0] = (R_[C == c0] % len(J.ROOMS)) + 1; print('PLANT: child', c0, 'room id swapped')
    bad = []
    if (R_ < 1).any(): bad.append(('room id 0', int((R_ < 1).sum())))
    miss = set(J.ROOMS.values()) - set(R_.tolist())
    if miss: bad.append(('room ids missing', sorted(miss)))
    wrong = 0
    for t, rid in zip(T, R_):
        z = zone_of(t.mean(0))
        if len(z) == 1 and J.ROOMS[z[0]] != rid: wrong += 1
    if wrong: bad.append(('triangles in another room\'s zone', wrong))
    return bad, {'triangles': len(T), 'ids': sorted(set(R_.tolist()))}
STAIRS = []
SOL = np.load(OUT / 'solids.npy') if (OUT / 'solids.npy').exists() else np.zeros((0, 6))
def ground():
    TD, K = drawn(); TD = TD[K == 0]
    TC, R_, C = ybn(OUT / 'xml/jc_jail.ybn.xml')
    if PLANT:
        c = TC.mean(1); cut = (np.abs(c[:, 0] + 22.0) < 0.5) & (np.abs(c[:, 1] - 4.0) < 0.5) & (np.abs(c[:, 2] - J.G) < 0.3)
        # cut the floor's collision triangles under a 1 x 1 m patch: retriangulating is not needed - every collision triangle touching it goes
        lo, hi = TC.min(1), TC.max(1); cut = (lo[:, 0] < -21.5) & (hi[:, 0] > -22.5) & (lo[:, 1] < 4.5) & (hi[:, 1] > 3.5) & (np.abs(c[:, 2] - J.G) < 0.05)
        print('PLANT: removes', int(cut.sum()), 'booking floor collision triangles'); TC = TC[~cut]
    stair_zones = [(si[0] - 0.4, si[1], si[2], si[3]) for si in [J.ST_IN]] + [(J.TSTAIR_W[0], J.TSTAIR_W[1], J.TSTAIR_BASE - 0.6, J.BRIDGE[2] + 0.3)] + [(J.RAMP[0], J.RAMP[1], J.RAMP[2] - 0.3, J.RAMP[3] + 0.3)] + [(J.DS_IN[0], J.DS_IN[1], J.DS_IN[2], J.DS_LAND_N + 0.6)]
    found = []; n = 0
    for k, zs in L['zones'].items():
        for u0, u1, v0, v1, z0, z1 in zs:
            levels = [z1 - 0.05] + ([J.TIER2 - J.TIER_T - 0.05] if k == 'block' else [])      # rays from under the ceiling (and the tier's soffit)
            us = np.arange(u0 + 0.137, u1, 0.25); vs = np.arange(v0 + 0.171, v1, 0.25)
            for zl in levels:
                P = np.array([(u, v, zl) for u in us for v in vs])
                P = P[~np.array([bool(len(SOL)) and bool(np.any(np.all(SOL[:, :3] < p - 1e-3, 1) & np.all(SOL[:, 3:] > p + 1e-3, 1))) for p in P])]   # not inside a wall
                dz = down(TD, P); cz = down(TC, P); n += len(P)
                for p, a, b in zip(P, dz, cz):
                    if zl < z1 - 1.0 and any(s[0] <= p[0] <= s[1] and s[2] <= p[1] <= s[3] for s in stair_zones): continue   # under-soffit level: not on a stair
                    if np.isnan(a) and np.isnan(b): found.append(('HOLE', k, *np.round(p, 2))); continue
                    if np.isnan(b): found.append(('NOCOL', k, *np.round(p, 2), round(a, 3))); continue
                    if np.isnan(a): continue                                   # collision with nothing drawn over it: an invisible blocker (checked by the walks)
                    tol = 0.21 if any(s[0] <= p[0] <= s[1] and s[2] <= p[1] <= s[3] for s in stair_zones) else 0.05
                    if a - b > 2.2: continue                                   # drawn > 2.2 m over the walked floor: a fitting you walk under (doc 02)
                    if abs(a - b) > tol and min(a, b) > z0 - 0.5: found.append(('MISMATCH', k, *np.round(p, 2), round(a, 3), round(b, 3)))
    if PLANT:
        hit = [f for f in found if f[0] in ('NOCOL', 'MISMATCH') and abs(f[2] + 22.0) < 0.6 and abs(f[3] - 4.0) < 0.6]
        return hit, {'cells': n}
    return found, {'cells': n}
def _tri_box(T, lo, hi):
    """triangles (n,3,3) overlapping the axis box lo..hi (separating axis test, Akenine-Moller)."""
    c = (lo + hi) / 2; h = (hi - lo) / 2; V = T - c; ok = np.ones(len(T), bool)
    for a in range(3): ok &= ~((V[:, :, a].min(1) > h[a]) | (V[:, :, a].max(1) < -h[a]))
    E = [V[:, 1] - V[:, 0], V[:, 2] - V[:, 1], V[:, 0] - V[:, 2]]
    n = np.cross(E[0], E[1]); d = (n * V[:, 0]).sum(1); r = (np.abs(n) * h).sum(1); ok &= np.abs(d) <= r
    for e in E:
        for a in range(3):
            ax = np.zeros((len(T), 3)); ax[:, a] = 1.0; axv = np.cross(ax, e)
            p = (V * axv[:, None, :]).sum(2); r = (np.abs(axv) * h).sum(1)
            ok &= ~((p.min(1) > r) | (p.max(1) < -r))
    return ok
def drive():
    TD, _ = drawn(); TC, _, _ = ybn(OUT / 'xml/jc_jail.ybn.xml')
    P2 = WK / 'p2/out'; ext = [lot(np.load(P2 / 'tris_jc_jail1.npy').astype(np.float64)), lot(np.load(P2 / 'coltris_jc_ext_col.npy').astype(np.float64))]
    ALL = np.concatenate([TD, TC] + ext)
    if PLANT:
        s = J.DRIVE_STOP - 3.0; pil = np.array([[s, J.DRIVE_V - 0.25, J.SALLY_Z], [s + 0.5, J.DRIVE_V + 0.25, J.SALLY_Z + 3.0]])
        q = [[pil[0][0], pil[0][1], pil[0][2]], [pil[1][0], pil[0][1], pil[0][2]], [pil[1][0], pil[1][1], pil[1][2]]]
        ALL = np.concatenate([ALL, np.array([q])]); print('PLANT: a pillar triangle in the bay at u', s)
    out = []
    for name, (w, h, l) in J.VEHICLES.items():
        lo = np.array([J.JBOX[0] - 6.0, J.DRIVE_V - w / 2 - 0.3, J.SALLY_Z + 0.15]); hi = np.array([J.DRIVE_STOP, J.DRIVE_V + w / 2 + 0.3, J.SALLY_Z + h + 0.2])
        m = _tri_box(ALL, lo, hi)
        if m.any(): out.append((name, int(m.sum()), np.round(ALL[m][0].mean(0), 2).tolist()))
    return out, {'triangles': len(ALL), 'vehicles': list(J.VEHICLES)}
bad, info = {'roomids': roomids, 'ground': ground, 'drive': drive}[GATE]()
tag = 'JJ_' + GATE.upper()
for b in bad[:25]: print(' ', b)
if PLANT:
    assert bad, f'PLANTED DEFECT NOT FOUND: the {GATE} gate is broken'
    print(tag + '_PLANT_FOUND', len(bad), json.dumps(info)); sys.exit(0)
print((tag + '_PASS ' if not bad else tag + '_FAIL ') + json.dumps({**info, 'findings': len(bad)})); sys.exit(1 if bad else 0)
