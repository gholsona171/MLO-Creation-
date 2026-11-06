# geometry-only diff (child flags ignored) + duplicate count + child flag changes, clustered
import sys, os
from collections import Counter
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'ybn_flat.py')).read())
V = flat(sys.argv[1]); out = {}
for p in sys.argv[2:]:
    A = flat(p); rem, add, pairs = diff(V, A, use_flags=False)
    R = [V[i] for i in rem]; Ad = [A[j] for j in add]
    dup = diff(Ad, V, use_flags=False)[2]   # added polygons that equal a vanilla polygon = extra copies
    flagmoves = Counter((V[i]['flags'][1][:25], A[j]['flags'][1][:25]) for i, j in pairs if V[i]['flags'] != A[j]['flags'])
    print(f'===== {os.path.basename(p)}: removed {len(R)}, added {len(Ad)} (of these {len(dup)} are extra copies of vanilla polygons); polygons kept but in a child with other flags: {sum(flagmoves.values())}')
    for (a, b), n in flagmoves.items(): print(f'     flags2 {a}... -> {b}...: {n} polys')
    dupset = set(id(Ad[i]) for i, j in dup)
    for lbl, L in (('-', R), ('+', [x for x in Ad if id(x) not in dupset]), ('+dup', [x for x in Ad if id(x) in dupset])):
        for g in clusters(L):
            print(f'   {lbl:4s} {len(g):5d} {span(g)}  {dict(Counter(x["tag"] for x in g))}')
