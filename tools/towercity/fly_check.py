"""Tower City fly-through check (Antonio 2026-10-20: "I don't want you running into any walls or going through walls").
The camera path of a C:\\C9Test\\routes\\fly_<name>.lua, sampled exactly as tc_flythrough.sh flies it (Catmull-Rom through the
points), is tested against EVERY visible surface of the map (the triangles each build exports: work/<lot>/tris_*.npy - walls,
glass, ceilings, pendants, signs, chandeliers, railings) and every prop's box (tables, slots, trees, doors - doors are listed
apart: the fly opens them). A sample closer than CLEAR (the camera's near plane + margin) to any of them is a hit.
Usage: py -3 fly_check.py full   -> lists the hits per path segment; exit 1 if any."""
import re, sys, json, math, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; T = W.parent
CLEAR = 0.45
FRAMES = ('hei_obankbsafeframe',)            # props that are a frame round an opening (their box would wrongly fill the doorway; the
                                             # wall behind them is in the surface check)
FR = {'m': (71.0, -884.0), 't': (-78.897, -827.328)}; H = math.radians(69.5)
def world(f, u, v): o = FR[f]; return o[0] + u * math.cos(H) - v * math.sin(H), o[1] + u * math.sin(H) + v * math.cos(H)
def path(name):
    src = open(rf'C:\C9Test\routes\fly_{name}.lua', encoding='utf-8').read()
    ev = {}; names = re.findall(r'local\s+([\w,\s]+)=\s*([^\n]+)', src)
    for lhs, rhs in names:                                                                                # "local M, P1, ... = a + 1.9, b + 1.9"
        ks = [k.strip() for k in lhs.split(',')]; vs = [x.strip() for x in rhs.split('--')[0].split(',')]
        if len(ks) == len(vs) and all(re.fullmatch(r'[\d.]+\s*\+\s*[\d.]+', x) for x in vs):
            for k, x in zip(ks, vs): a, b = x.split('+'); ev[k] = float(a) + float(b)
    pts = []
    for f, u, v, z, s in re.findall(r"\{'([mt])',\s*([-\d.]+),\s*([-\d.]+),\s*([\w.]+),\s*([\d.]+)\}", src):
        x, y = world(f, float(u), float(v)); pts.append((np.array([x, y, ev[z] if z in ev else float(z)]), float(s), f'{f} {u} {v} {z}'))
    return pts
def samples(pts, step=0.25):
    P = [p[0] for p in pts]; out = []
    for seg in range(len(P) - 1):                                                                          # straight legs, as flown
        b, c = P[seg], P[seg + 1]; n = max(2, int(np.linalg.norm(c - b) / step))
        for k in range(n): out.append((seg, b + (c - b) * k / n))
    return out
def prop_tris():
    """every prop as its bounding box (12 triangles), world space; doors tagged."""
    S = json.load(open(T / 'survey/arch_ytyp.json', encoding='utf-8-sig'))
    def bb(m):
        if m not in S: return None
        f = lambda s: [float(t.split(':')[1]) for t in s.split()]; return f(S[m]['bbMin']), f(S[m]['bbMax'])
    tris, tags = [], []
    for lay, f in (('l1/l1_layout.json', 'm'), ('l2/l2_layout.json', 'm'), ('l3/l3_layout.json', 't'), ('res/res_layout.json', 't')):
        L = json.load(open(W / lay))
        for p in L.get('props', []):
            m = p['model'].lower(); b = bb(m)
            if not b or m in FRAMES: continue
            (x0, y0, z0), (x1, y1, z1) = b; s = p.get('scale') or 1.0; s, sz = (s if isinstance(s, (list, tuple)) else (s, s)); h = math.radians(p.get('heading', 0.0)); u, v, z = p['pos']
            C = []
            for X in (x0, x1):
                for Y in (y0, y1):
                    for Z in (z0, z1):
                        lu, lv = u + s * (X * math.cos(h) - Y * math.sin(h)), v + s * (X * math.sin(h) + Y * math.cos(h))
                        wx, wy = world(f, lu, lv); C.append((wx, wy, z + sz * Z))
            C = np.array(C)
            for q in ((0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)):
                tris += [C[[q[0], q[1], q[2]]], C[[q[0], q[2], q[3]]]]; tags += [('door ' if any(k in m for k in ('door', 'gate', 'vaul')) else 'prop ') + m] * 2
    return np.array(tris, np.float32), tags
def closest(p, A, B, C):
    """distance from point p to triangles (A, B, C) (Ericson, vectorised)."""
    ab, ac, ap = B - A, C - A, p - A
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - B; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - C; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den[den == 0] = 1e-12
    v = vb / den; w = vc / den; Q = A + ab * v[:, None] + ac * w[:, None]
    m = (d1 <= 0) & (d2 <= 0); Q[m] = A[m]
    m = (d3 >= 0) & (d4 <= d3); Q[m] = B[m]
    m = (d6 >= 0) & (d5 <= d6); Q[m] = C[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0) & ~((d1 <= 0) & (d2 <= 0)) & ~((d3 >= 0) & (d4 <= d3))
    t = d1 / np.where(d1 - d3 == 0, 1e-12, d1 - d3); Q[m] = (A + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0) & ~((d1 <= 0) & (d2 <= 0)) & ~((d6 >= 0) & (d5 <= d6))
    t = d2 / np.where(d2 - d6 == 0, 1e-12, d2 - d6); Q[m] = (A + ac * t[:, None])[m]
    m = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0) & ~((d3 >= 0) & (d4 <= d3)) & ~((d6 >= 0) & (d5 <= d6))
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-12, (d4 - d3) + (d5 - d6)); Q[m] = (B + (C - B) * t[:, None])[m]
    return np.linalg.norm(p - Q, axis=1)
def main(name):
    tris, tags = [], []
    for f in sorted(W.glob('*/tris_*.npy')):
        t = np.load(f); tris.append(t); tags += [f.stem[5:]] * len(t)
    pt, ptag = prop_tris(); tris.append(pt); tags += ptag
    tris = np.concatenate(tris).astype(np.float64); tags = np.array(tags)
    lo, hi = tris.min(1) - CLEAR, tris.max(1) + CLEAR; CS = 4.0
    grid = {}
    for i in range(len(tris)):
        a, b = np.floor(lo[i] / CS).astype(int), np.floor(hi[i] / CS).astype(int)
        for x in range(a[0], b[0] + 1):
            for y in range(a[1], b[1] + 1):
                for z in range(a[2], b[2] + 1): grid.setdefault((x, y, z), []).append(i)
    grid = {k: np.array(v) for k, v in grid.items()}
    pts = path(name); hits = {}; doors = set()
    for seg, p in samples(pts):
        c = tuple(np.floor(p / CS).astype(int)); idx = grid.get(c)
        if idx is None: continue
        d = closest(p, tris[idx, 0], tris[idx, 1], tris[idx, 2]); k = int(d.argmin())
        near = idx[d < CLEAR]
        if len(near) and all(str(tags[i]).startswith('door ') for i in near): doors.add(str(tags[near[0]])); continue   # a door: the fly opens it
        if d[k] < CLEAR:
            h = hits.setdefault(seg, {'n': 0, 'min': 9.0, 'what': set(), 'at': None})
            h['n'] += 1; h['what'].add(str(tags[idx[k]]))
            if d[k] < h['min']: h['min'] = float(d[k]); h['at'] = [round(float(x), 2) for x in p]
    print(f'FLY_CHECK {name}: {len(pts)} points, {len(samples(pts))} samples, {len(tris)} triangles | segments touching something: {len(hits)}')
    print('  doors the fly opens:', sorted(doors))
    for seg, h in sorted(hits.items()):
        f = pts[seg][2][0]; o = FR[f]; dx, dy = h['at'][0] - o[0], h['at'][1] - o[1]
        lu, lv = dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H)                  # the hit in the segment's own frame
        print(f'  seg {seg:3d} {pts[seg][2]:>22s} -> {pts[seg + 1][2]:<22s} {h["n"]:4d} samples, nearest {h["min"]:.2f} m at {f} ({lu:.1f}, {lv:.1f}, {h["at"][2]:.1f}): {sorted(h["what"])[:4]}')
    return 1 if hits else 0
if __name__ == '__main__': sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'full'))
