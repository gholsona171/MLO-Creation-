import sys
from collections import defaultdict
def load(p):
    d = defaultdict(list)
    for ln in open(p):
        ln = ln.strip()
        if not ln: continue
        i, *pts = ln.split(';'); d[int(i)].append(tuple(tuple(float(c) for c in q.split(',')) for q in pts))
    return d
def key(t): return frozenset(t)
V = load(sys.argv[1])
res = {}
for p in sys.argv[2:]:
    D = load(p); print('=====', p)
    for i in sorted(set(V) | set(D)):
        vs = {key(t): t for t in V[i]}; ds = {key(t): t for t in D[i]}
        rem = [vs[k] for k in vs if k not in ds]; add = [ds[k] for k in ds if k not in vs]
        if rem or add:
            print(f' model {i}: vanilla {len(V[i])} tris, now {len(D[i])}; removed {len(rem)}, added {len(add)}')
            for lbl, L in (('-', rem), ('+', add)):
                for t in L:
                    xs=[q[0] for q in t]; ys=[q[1] for q in t]; zs=[q[2] for q in t]
                    print(f'   {lbl} x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f} z {min(zs):.1f}..{max(zs):.1f}')
            res.setdefault(p, {})[i] = (set(k for k in vs if k not in ds), set(k for k in ds if k not in vs))
ps = sys.argv[2:]
if len(ps) == 2:
    a, b = res.get(ps[0], {}), res.get(ps[1], {})
    for i in set(a) & set(b):
        print(f'model {i} touched by both: removed-overlap {len(a[i][0] & b[i][0])}, either added: {len(a[i][1])}/{len(b[i][1])}')
