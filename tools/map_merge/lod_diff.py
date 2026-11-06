import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'lodlights.py')).read())
d = sys.argv[1]; V, vns, vc = load(f'{d}/vanilla__vw_lodlights_medium012.ymap.xml', f'{d}/vanilla__vw_distlodlights_medium012.ymap.xml')
from collections import Counter
print('vanilla lights', len(V), 'street', vns, 'cat', vc, 'dup hashes', sum(c - 1 for c in Counter(r['hash'] for r in V).values() if c > 1))
for s in sys.argv[2:]:
    A, ns, c = load(f'{d}/src_{s}__vw_lodlights_medium012.ymap.xml', f'{d}/src_{s}__vw_distlodlights_medium012.ymap.xml')
    rem, add, chg = diff(V, A); print(f'== {s}: lights {len(A)} street {ns} cat {c}; removed {len(rem)} added {len(add)} changed {len(chg)}')
    P = lambda r: '(' + ', '.join(f'{float(x):.1f}' for x in r['position']) + ')'
    for r in rem: print('   - hash', r['hash'], P(r), 'street' if r['street'] else '')
    for r in add: print('   + hash', r['hash'], P(r), 'street' if r['street'] else '')
    for a, b in chg: print('   ~ hash', a['hash'], P(a), '->', {k: b[k] for k in a if a[k] != b[k] and not (isinstance(a[k], tuple) and same({k: a[k]}, {k: b[k]}))})
