"""Portal-aware light-gap audit of the whole east-lot MLO tc_under (mall levels 1-3, the promenade, the RTA lobby): playbook 07's
gap_check method, plus what the game really draws. Built 2026-10-24 for Antonio's report (promenade ceiling open to the sky, a
slit between the side corridors' floor and the window wall).
A ray from a point in room R SEES a face only if
  * the face is turned toward the ray (faces are one-sided in game),
  * it is not see-through glass (mats_*.npy kind 1) or a decal (kind 2),
  * its drawable is drawn from where the ray is: R's own drawable, or the drawable of a room the ray has entered through a portal
    (a portal to limbo makes the exterior models - tc_mall_ext / tc_ug_ext - drawn).
Faces of other drawables are not drawn from R unless the line of sight, carried on, passes through a portal into their room (the game
draws a room through its portal's screen rectangle): otherwise the ray passes them (that is the "sky strip" seam).
A ray that ends without seeing anything is a GAP unless it went out through a portal to limbo (a window / door: the street).
Pass 1's 'undrawn' rays (another room's face seen from inside a room, mostly storefront jambs / head rails just outside a portal's
rectangle) are ADVISORY: the game draws a neighbour through its portal's screen rectangle, which is larger than the portal seen
obliquely, so most are drawn in game. Hard failures: gap, slit, mirror, and pass 2's undrawn (the outer walls' seams).
Passes: 1) a grid over every room region (l1/l2 layouts 'gap_regions'; 3 m, 3 heights) in 150 directions; 2) the perimeter seam scan:
every region edge on an outer wall, 0.2 m along x 0.2 m up from floor+0.02 to the ceiling, straight out, +-30 deg, and out-and-down
(slab edge to window wall), plus the floor's edge looking down.
Points inside a solid (most axis rays meet back faces) are skipped. Mirror portals (flags 4) are not view openings.
Run: blender -b --python mall_gap_check.py [-- only=prom,avenue]   -> work/l2/mall_gap_report.json, a line MALL_GAP_CHECK {...}
Exit status: the line ends PASS when there are no gap cells."""
import json, math, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
WK = Path(r'C:\Users\anton\Documents\Codex\TowerCity\work')
ORG, H = (71.0, -884.0), math.radians(69.5); ch, sh = math.cos(H), math.sin(H)
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
ONLY = set(ARGS['only'].split(',')) if 'only' in ARGS else None
LAYS = [json.load(open(WK / 'l1/l1_layout.json')), json.load(open(WK / 'l2/l2_layout.json'))]
DRAW = {r['key']: r['drawable'] for L in LAYS for r in L['rooms']}
EXTD = [d for L in LAYS for d in L['ext']]
# ---- every drawable's triangles (lot frame), kinds, one BVH
names, T, K, DI = [], [], [], []
for lot in ('l1', 'l2'):
    for f in sorted((WK / lot).glob('tris_*.npy')):
        nm = f.stem[5:]; t = np.load(f).astype(np.float64); mf = f.with_name('mats_' + nm + '.npy')
        k = np.load(mf) if mf.exists() else np.zeros(len(t), np.int8)
        assert len(k) == len(t), f'{mf.name}: rebuild (kinds and triangles differ)'
        x, y = t[..., 0] - ORG[0], t[..., 1] - ORG[1]; t = np.stack([x * ch + y * sh, -x * sh + y * ch, t[..., 2]], -1)
        names.append(nm); T.append(t); K.append(k); DI.append(np.full(len(t), len(names) - 1, np.int32))
T, K, DI = np.concatenate(T), np.concatenate(K), np.concatenate(DI)
NRM = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); NRM /= np.maximum(np.linalg.norm(NRM, axis=1), 1e-12)[:, None]
tree = BVHTree.FromPolygons([Vector(p) for p in T.reshape(-1, 3)], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(T))], epsilon=0.0)
DID = {n: i for i, n in enumerate(names)}
EXT_IDS = {DID[d] for d in EXTD if d in DID}
# ---- portals: per room, plane + polygon (both directions)
PORT = {}
for L in LAYS:
    for p in L['portals']:
        if p.get('flags', 0) & 4: continue
        C = np.array(p['corners'], float); n = np.cross(C[1] - C[0], C[2] - C[0]); n /= np.linalg.norm(n)
        for a, b in ((p['from'], p['to']), (p['to'], p['from'])): PORT.setdefault(a, []).append((C, n, float(n @ C[0]), b))
PARR = {r: (np.array([q[1] for q in ps]), np.array([q[2] for q in ps])) for r, ps in PORT.items()}
def portal_hit(room, o, d, tmax):
    """nearest portal of `room` crossed by the ray within tmax: (t, other room) or None (planes in one numpy step, then the
    polygon test on the few candidates, nearest first)."""
    if room not in PARR: return None
    N, Kk = PARR[room]; den = N @ d
    with np.errstate(divide='ignore', invalid='ignore'): t = (Kk - N @ o) / den
    cand = np.nonzero((np.abs(den) > 1e-9) & (t > 1e-4) & (t < tmax + 2e-3))[0]          # (a portal on a face's plane is crossed first)
    for i in cand[np.argsort(t[cand])]:
        C, n, k, other = PORT[room][i]; q = o + d * t[i]; ok = True; s0 = None
        for j in range(len(C)):
            c = np.cross(C[(j + 1) % len(C)] - C[j], q - C[j]) @ n
            if abs(c) < 1e-12: continue
            if s0 is None: s0 = c > 0
            elif (c > 0) != s0: ok = False; break
        if ok: return (float(t[i]), other)
    return None
def behind_portal(room, p, d, di, reach=3.0):
    """a face of another room's (or the exterior's) drawable that stands on THIS side of the portal into it: the game draws that
    room through the portal's screen rectangle, so the face is drawn where the line of sight, carried on, passes through the portal
    (a shopfront's jambs, glass and sill sit between the shop and its portal plane)."""
    ph = portal_hit(room, p, d, reach)
    if not ph: return False
    return (ph[1] == 'limbo' and di in EXT_IDS) or DID.get(DRAW.get(ph[1]), -2) == di
def trace(room, o, d, dist=300.0, mirror=False):
    """'seen' | 'window' | 'gap' | 'undrawn' (passed a face of a drawable that is not drawn from here). mirror=True: a reflected ray -
    the reflection draws only the mirror's own room, so crossing any portal is 'black'."""
    o = np.array(o, float); d = np.array(d, float); vis = {DID.get(DRAW.get(room), -1)}; out = False; undrawn = False; left = dist
    for _ in range(60):
        loc, nrm, idx, t = tree.ray_cast(Vector(o), Vector(d), left)
        th = t if loc is not None else left
        ph = portal_hit(room, o, d, th)
        if ph and loc is not None and abs(ph[0] - t) < 2e-3 and NRM[idx] @ d < 0 and K[idx] == 0 and DI[idx] in vis: return 'seen'   # a wall on the portal's plane (round its opening) stays a wall
        if ph:
            if mirror: return 'black'
            t, room = ph; o = o + d * (t + 1e-4); left -= t
            if room == 'limbo': out = True; vis |= EXT_IDS
            else: vis.add(DID.get(DRAW.get(room), -1))
            continue
        if loc is None: return 'window' if out else ('undrawn' if undrawn else 'gap')
        i = idx; front = NRM[i] @ d < 0
        if front and K[i] == 0:
            if DI[i] in vis or out or behind_portal(room, np.array(loc), d, DI[i]): return 'seen'
            if any(DI[j] in vis and NRM[j] @ d < 0 and K[j] == 0 for _, _, j, _ in tree.find_nearest_range(loc, 2e-3)): return 'seen'   # coincident faces: the drawn one wins
            undrawn = True
        o = np.array(loc) + d * 1e-3; left -= t + 1e-3
    return 'seen'
def probe(room, o, d):
    """debug one ray: every event on its way (probe=room,x,y,z,dx,dy,dz)."""
    o = np.array(o, float); d = np.array(d, float); d /= np.linalg.norm(d); left = 300.0
    for _ in range(40):
        loc, nrm, idx, t = tree.ray_cast(Vector(o), Vector(d), left)
        th = t if loc is not None else left; ph = portal_hit(room, o, d, th)
        if ph: print('   portal', room, '->', ph[1], 'at', np.round(o + d * ph[0], 2)); t, room = ph; o = o + d * (t + 1e-4); left -= t; continue
        if loc is None: print('   escapes'); return
        print('   hit', names[DI[idx]], 'kind', K[idx], 'front' if NRM[idx] @ d < 0 else 'back', np.round(np.array(loc), 3), 'tri', np.round(T[idx], 2).tolist())
        o = np.array(loc) + d * 1e-3; left -= t + 1e-3
if 'probe' in ARGS:
    q = ARGS['probe'].split(','); dd = np.array([float(x) for x in q[4:7]]); dd /= np.linalg.norm(dd)
    g = math.pi * (3 - math.sqrt(5)); n = int(ARGS.get('dirs', 150))
    S = [np.array((math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.cos(g * i), math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.sin(g * i), 1 - 2 * (i + .5) / n)) for i in range(n)]
    dd = max(S, key=lambda x: x @ dd)                     # (the report rounds directions: snap to the check's own)
    print('   DIR', np.round(dd, 4)); [print('   GAPDIR', np.round(x, 4), trace(q[0], np.array([float(v) for v in q[1:4]]), x)) for x in S if trace(q[0], np.array([float(v) for v in q[1:4]]), x) not in ('seen', 'window')]
    probe(q[0], [float(x) for x in q[1:4]], dd); print('   TRACE', trace(q[0], np.array([float(x) for x in q[1:4]]), dd)); raise SystemExit
ROOM_OF = [None]
def first_face(room, o, d, dist=60.0):
    """what the ray meets first that faces it (glass included, decals not): 'drawn' (a face drawn from here - own drawable or
    reached through a portal), 'foreign' (another drawable's face, not drawn here) or 'none'."""
    o = np.array(o, float); d = np.array(d, float); vis = {DID.get(DRAW.get(room), -1)}; left = dist
    for _ in range(60):
        loc, nrm, idx, t = tree.ray_cast(Vector(o), Vector(d), left)
        th = t if loc is not None else left
        ph = portal_hit(room, o, d, th)
        if ph:
            t, room = ph; o = o + d * (t + 1e-4); left -= t
            if room == 'limbo': return 'drawn'
            vis.add(DID.get(DRAW.get(room), -1)); continue
        if loc is None: return 'none'
        if NRM[idx] @ d < 0 and K[idx] != 2: return 'drawn' if DI[idx] in vis else 'foreign'
        o = np.array(loc) + d * 1e-3; left -= t + 1e-3
    return 'none'
def inside_solid(o):
    """True for a point that is not in open room space: inside a closed solid (most axis rays meet back faces first), or with
    nothing over / under it that faces it (above a vault's soffit, under a floor)."""
    for d in ((0, 0, 1), (0, 0, -1)):
        if first_face(ROOM_OF[0], o, d) != 'drawn': return True
    n = 0
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        loc, nrm, idx, t = tree.ray_cast(Vector(o), Vector(d), 50.0)
        if loc is not None and NRM[idx] @ np.array(d) > 0 and K[idx] == 0: n += 1
    return n >= 2                                       # (2: the cullers drop a box face that meets another, e.g. a soffit's top)
def sphere(n):
    g = math.pi * (3 - math.sqrt(5)); return [np.array((math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.cos(g * i), math.sqrt(1 - (1 - 2 * (i + .5) / n) ** 2) * math.sin(g * i), 1 - 2 * (i + .5) / n)) for i in range(n)]
REG = [r for L in LAYS for r in L.get('gap_regions', []) if ONLY is None or r[0] in ONLY]
OUTER = (77.6, 53.6)                                    # the mall's outer walls' inner faces (|u|, |v|)
cells = {}; stats = {'points': 0, 'skipped_solid': 0, 'rays': 0, 'window': 0}
def log(kind, room, o, d):
    if kind == 'undrawn' and PASS[0] == '1': kind = 'undrawn-advisory'
    key = (kind, room, round(o[0] * 2) / 2, round(o[1] * 2) / 2, round(o[2] * 2) / 2)
    c = cells.setdefault(key, {'kind': kind, 'room': room, 'at': [round(float(x), 2) for x in o], 'dir': [round(float(x), 2) for x in d], 'n': 0}); c['n'] += 1
def shoot(room, o, dirs):
    o = np.array(o, float); ROOM_OF[0] = room
    if 'pass' in ARGS and ARGS['pass'] != PASS[0]: return
    if inside_solid(o): stats['skipped_solid'] += 1; return
    stats['points'] += 1
    for d in dirs:
        stats['rays'] += 1; r = trace(room, o, d)
        if r == 'window': stats['window'] += 1
        elif r in ('gap', 'undrawn'): log(r, room, o, d)
PASS = ['1']
D1 = sphere(int(ARGS.get('dirs', 150)))
for room, u0, u1, v0, v1, zf, zc in REG:                # pass 1: the rooms
    step = float(ARGS.get('step', 3.0))
    gu = np.linspace(u0 + 0.3, u1 - 0.3, max(2, int(math.ceil((u1 - u0) / step)) + 1)); gv = np.linspace(v0 + 0.3, v1 - 0.3, max(2, int(math.ceil((v1 - v0) / step)) + 1))
    for u in gu:
        for v in gv:
            for z in (zf + 0.4, zf + 1.7, zc - 0.3): shoot(room, (u, v, z), D1)
def seam_dirs(n):                                       # out of the wall (n = outward unit in plan): straight, +-30 deg, down-out, along the floor
    n = np.array((n[0], n[1], 0.0), float); t = np.array((-n[1], n[0], 0.0)); out = []
    for a in (0.0, 0.5236, -0.5236):
        h = n * math.cos(a) + t * math.sin(a)
        for e in (0.0, -0.35, -0.8, 0.35): out.append(np.array((h[0] * math.cos(e), h[1] * math.cos(e), math.sin(e))))
    return out
PASS[0] = '2'
for room, u0, u1, v0, v1, zf, zc in REG:                # pass 2: the seam scan on every outer wall
    edges = [((u0, v0), (u0, v1), (-1, 0)), ((u1, v0), (u1, v1), (1, 0)), ((u0, v0), (u1, v0), (0, -1)), ((u0, v1), (u1, v1), (0, 1))]
    for (a0, b0), (a1, b1), n in edges:
        at = a0 if n[0] else b0
        if abs(abs(at) - (OUTER[0] if n[0] else OUTER[1])) > 0.05 and room != 'prom': continue
        L = math.hypot(a1 - a0, b1 - b0); dirs = seam_dirs(n)
        for s in np.arange(0.1, L - 0.05, 0.25):
            x, y = a0 + (a1 - a0) * s / L - n[0] * 0.15 + 0.0137, b0 + (b1 - b0) * s / L - n[1] * 0.15 + 0.0171   # (off the mesh lines: a ray on a shared edge slips through)
            for z in sorted({zf + 0.02, zf + 0.1, zf + 0.25, zf + 0.5, zf + 0.8, zf + 1.1, zf + 1.6, zf + 2.6, zf + 3.6, zc - 0.3, zc - 0.05}): shoot(room, (x, y, z), dirs)
SLITS = []                                              # pass 0: no inner wall meets a street wall inside a window (wall end behind the glass)
for ax, at, st, lines in LAYS[1].get('street_partitions', []):
    for w in LAYS[1].get('windows', []):
        if w[0] == ax and abs(w[1] - at) < 1e-6 and (w[5] < 36.0) == (st == 'L1'):
            for x in lines:
                if w[3] - 0.2 < x < w[4] + 0.2: SLITS.append([ax, at, st, x, w[3], w[4], w[5]]); log('slit', st, np.array((at, x, w[5]) if ax == 'u' else (x, at, w[5]), float), np.zeros(3))
print('  SLITS', len(SLITS), SLITS[:6], flush=True)
MIR = []                                                # pass 3: every mirror, looked into from its own floor: no black in the reflection
def mirrors_of(L):
    """the layout's mirrors (l2_build 'mirrors'), or - for an older layout - read off its mirror portals (flags 4)."""
    if 'mirrors' in L: return L['mirrors']
    out = []
    for p in L['portals']:
        if not p.get('flags', 0) & 4: continue
        C = np.array(p['corners']); n = np.cross(C[1] - C[0], C[2] - C[0])
        out.append({'unit': f"{p['from']} {C[0][0]:.1f} {C[:, 2].min():.1f}", 'room': p['from'], 'u': float(C[0][0]), 'v': [float(C[:, 1].min()), float(C[:, 1].max())],
                    'z': [float(C[:, 2].min()), float(C[:, 2].max())], 'faces': -int(np.sign(n[0]))})
    return out
for m in ([] if ONLY and not ({'up_s', 'up_n'} & ONLY) else mirrors_of(LAYS[1])):
    nrm = np.array((m['faces'], 0.0, 0.0)); room = m['room']; black = 0; total = 0
    reg = next(r for r in LAYS[1]['gap_regions'] if r[0] == room and r[5] < m['z'][0] < r[6] and r[3] <= m['v'][0] and m['v'][1] <= r[4]
               and min(r[1], r[2]) <= m['u'] + m['faces'] * 0.5 <= max(r[1], r[2]))
    us = [x for x in np.linspace(reg[1] + 0.4, reg[2] - 0.4, 8) if (x - m['u']) * m['faces'] > 1.0]
    eyes = [np.array((u, v, reg[5] + z)) for u in us for v in np.linspace(reg[3] + 0.6, reg[4] - 0.6, 6) for z in (1.2, 1.7)]
    pts = [np.array((m['u'], v, z)) for v in np.linspace(m['v'][0] + 0.1, m['v'][1] - 0.1, 12) for z in np.linspace(m['z'][0] + 0.1, m['z'][1] - 0.1, 4)]
    ROOM_OF[0] = room
    for e in eyes:
        if inside_solid(e): continue
        for p in pts:
            d = p - e; L = np.linalg.norm(d); d /= L
            loc, _, _, t = tree.ray_cast(Vector(e), Vector(d), L - 0.05)
            if loc is not None: continue                    # this eye does not see that part of the mirror
            r = d - 2 * (d @ nrm) * nrm; total += 1
            if trace(room, p + r * 0.01, r, mirror=True) != 'seen':
                black += 1; log('mirror', room, p, r)
    MIR.append({'unit': m['unit'], 'reflected_rays': total, 'black': black}); print('  MIRROR', m['unit'], total, 'rays', black, 'black', flush=True)
rep = sorted(cells.values(), key=lambda c: -c['n'])
by = {}
for c in rep: by[(c['room'], c['kind'])] = by.get((c['room'], c['kind']), 0) + c['n']
json.dump({'stats': stats, 'mirrors': MIR, 'by_room': {f'{a} {b}': n for (a, b), n in by.items()}, 'cells': rep}, open(WK / 'l2/mall_gap_report.json', 'w'), indent=1)
hard = [c for c in rep if c['kind'] != 'undrawn-advisory']
print('MALL_GAP_CHECK', json.dumps({**stats, 'gap_cells': len(hard), 'advisory_cells': len(rep) - len(hard)}), 'PASS' if not hard else 'FAIL', flush=True)
for (a, b), n in sorted(by.items(), key=lambda x: -x[1])[:40]: print('  GAP', a, b, n, flush=True)
for c in hard[:30]: print('   ', c, flush=True)
