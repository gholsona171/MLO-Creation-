# LOD-light pair diff vs vanilla for any pair name: lod_diff2.py <xml dir> <X e.g. medium012> <tag> [<tag>...]  (files <tag>__vw_[dist]lodlights_X.ymap.xml)
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'lodlights.py')).read())
from collections import Counter
d, X = sys.argv[1], sys.argv[2]
f = lambda who, kind: f'{d}/{who}__vw_{kind}lodlights_{X}.ymap.xml'
V, vns, vc = load(f('vanilla', ''), f('vanilla', 'dist'))
print('vanilla lights', len(V), 'street', vns, 'cat', vc, 'dup hashes', sum(c - 1 for c in Counter(r['hash'] for r in V).values() if c > 1))
P = lambda r: '(' + ', '.join(f'{float(x):.1f}' for x in r['position']) + ')'
for s in sys.argv[3:]:
    A, ns, c = load(f(s, ''), f(s, 'dist'))
    rem, add, chg = diff(V, A); print(f'== {s}: lights {len(A)} street {ns} cat {c}; removed {len(rem)} added {len(add)} changed {len(chg)}')
    for r in rem: print('   - hash', r['hash'], P(r), 'street' if r['street'] else '')
    for r in add: print('   + hash', r['hash'], P(r), 'street' if r['street'] else '')
    for a, b in chg: print('   ~ hash', a['hash'], P(a), '->', {k: b[k] for k in a if a[k] != b[k] and not (isinstance(a[k], tuple) and same({k: a[k]}, {k: b[k]}))})
