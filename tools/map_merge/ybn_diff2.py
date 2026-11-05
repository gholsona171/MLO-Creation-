# tolerant polygon diff: world-space verts, match by tag+material, every vertex within TOL (triangles: any vertex order)
import sys, itertools
from collections import defaultdict, Counter
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0] if '/' in sys.argv[0] else '.')
TOL = 0.03
exec(open(sys.argv[0].replace('ybn_diff2.py','ybn_load.py')).read())
def close(p, q):
    if p[0] != q[0] or p[1] != q[1] or len(p[2]) != len(q[2]) or any(abs(float(x[1]) - float(y[1])) > 1e-4 for x, y in zip(p[3], q[3])): return False
    perms = itertools.permutations(q[2])
    for qq in perms:
        if all(max(abs(a - b) for a, b in zip(u, v)) <= TOL for u, v in zip(p[2], qq)): return True
    return False
def cell(p):
    c = [sum(v[i] for v in p[2]) / len(p[2]) for i in range(3)]; return tuple(int(x // 1.0) for x in c)
def diff(A, B):
    grid = defaultdict(list)
    for j, q in enumerate(B): grid[cell(q)].append(j)
    used = set(); rem = []
    for p in A:
        cx, cy, cz = cell(p); hit = None
        for d in itertools.product((-1, 0, 1), repeat=3):
            for j in grid.get((cx + d[0], cy + d[1], cz + d[2]), []):
                if j not in used and close(p, B[j]): hit = j; break
            if hit is not None: break
        if hit is None: rem.append(p)
        else: used.add(hit)
    add = [q for j, q in enumerate(B) if j not in used]
    return rem, add
def span(ps):
    xs = [v[0] for p in ps for v in p[2]]; ys = [v[1] for p in ps for v in p[2]]; zs = [v[2] for p in ps for v in p[2]]
    return f'x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f} z {min(zs):.1f}..{max(zs):.1f}' if xs else '-'
if __name__ == '__main__':
    paths = sys.argv[1:]; V = load(paths[0]); verbose = True
    for p in paths[1:]:
        D = load(p); print('=====', p)
        for i, (a, b) in enumerate(zip(V, D)):
            rem, add = diff(a['polys'], b['polys'])
            print(f' child {i}: polys {len(a["polys"])} -> {len(b["polys"])}, verts {a["nv"]} -> {b["nv"]}, mats {a["nmat"]} -> {b["nmat"]}; removed {len(rem)}, added {len(add)}')
            for lbl, L in (('-', rem), ('+', add)):
                if not L: continue
                print(f'   {lbl} span {span(L)} types {dict(Counter(x[0] for x in L))} mats {dict(Counter(x[1] for x in L))}')
                for x in L[:400]: print(f'      {lbl} {x[0]} m{x[1]} {span([x])} {x[3] if x[3] else ""}')
