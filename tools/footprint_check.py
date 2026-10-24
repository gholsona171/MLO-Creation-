"""Prop footprint check (pivot-aware): props through walls, props overlapping each other, props blocking doorways.

Input JSON (props.json):
  {"rooms":   {"<room>": [[u0, u1, v0, v1], ...]},            # usable floor rectangles per room (lot frame)
   "doors":   [[axis, line, a0, a1], ...],                     # axis 'u' = wall on u = line, opening a0..a1 along v ('v' the reverse)
   "props":   [[room, model, u, v, base_dz, heading, scale], ...]}
Bounds come from arch_ytyp.json (find_arch_ytyp.ps1). Headings: a prop's front is -Y; 0 faces -v, 90 faces +u, 180 +v, 270 -u.
Usage: py -3 footprint_check.py props.json arch_ytyp.json
"""
import json, math, sys

def bounds(A, m):
    k = A.get(m.lower())
    if not k: return None
    f = lambda s: [float(x[2:]) for x in s.split()]
    return f(k['bbMin']) + f(k['bbMax'])

def footprint(b, u, v, h, sc):
    t = math.radians(h); c, s = math.cos(t), math.sin(t)
    w = [(u + sc * (x * c - y * s), v + sc * (x * s + y * c)) for x in (b[0], b[3]) for y in (b[1], b[4])]
    return (min(p[0] for p in w), max(p[0] for p in w), min(p[1] for p in w), max(p[1] for p in w), sc * (b[5] - b[2]))

def main(pj, aj):
    P = json.load(open(pj)); A = {k.lower(): v for k, v in json.load(open(aj, encoding='utf-8-sig')).items()}
    big, bad = [], 0
    for room, m, u, v, dz, h, *sc in P['props']:
        sc = sc[0] if sc and sc[0] else 1.0; b = bounds(A, m)
        if not b: print('NO BOUNDS', m); bad += 1; continue
        u0, u1, v0, v1, hz = footprint(b, u, v, h, sc); rs = P['rooms'][room]
        corners = [(x, y) for x in (u0, u1) for y in (v0, v1)]
        if hz > 0.3 and not all(any(a - .06 <= x <= bb + .06 and c - .06 <= y <= d + .06 for a, bb, c, d in rs) for x, y in corners):
            print('WALL', room, m, [round(x, 2) for x in (u0, u1, v0, v1)]); bad += 1
        if (u1 - u0) * (v1 - v0) * hz > 0.2 and dz < 0.2: big.append((room, m, (u0, u1, v0, v1)))
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            (r, m, a), (r2, m2, b) = big[i], big[j]
            if r != r2: continue
            ov, ow = min(a[1], b[1]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[2], b[2])
            if ov > .06 and ow > .06: print('OVERLAP', r, m, m2, round(ov, 2), round(ow, 2)); bad += 1
    for axis, line, a0, a1 in P.get('doors', []):
        z = (line - .8, line + .8, a0, a1) if axis == 'u' else (a0, a1, line - .8, line + .8)
        for r, m, a in big:
            if min(a[1], z[1]) - max(a[0], z[0]) > .05 and min(a[3], z[3]) - max(a[2], z[2]) > .05:
                print('DOORWAY', r, m, axis, line, a0); bad += 1
    print('checked', len(P['props']), 'props,', bad, 'findings'); return bad

if __name__ == '__main__': sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
