import sys, os
from collections import Counter
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'ybn_flat.py')).read())
V = flat(sys.argv[1])
for p in sys.argv[2:]:
    A = flat(p); rem, add, pairs = diff(V, A)
    moved_flags = diff([V[i] for i in rem], [A[j] for j in add], use_flags=False)[2]
    print(f'===== {os.path.basename(p)}: polys {len(V)} -> {len(A)}; removed {len(rem)}, added {len(add)} (of which {len(moved_flags)} are the same polygon in a child with other flags)')
    R = [V[i] for i in rem]; Ad = [A[j] for j in add]
    for lbl, L in (('-', R), ('+', Ad)):
        for g in clusters(L):
            print(f'   {lbl} {len(g):5d} polys {span(g)}  {dict(Counter(x["tag"] for x in g))} flags {set(x["flags"][0][:30] for x in g)}')
