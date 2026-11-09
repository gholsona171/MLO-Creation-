# Car generator + physicsDictionaries diff of ymap XMLs vs vanilla. Car gens compared field by field with 1e-3 tolerance on numbers
# (matched by position within 5 cm), names as joaat hashes.
import sys, os, xml.etree.ElementTree as ET
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'joaat.py')).read())
def rec(it):
    d = {}
    for c in it:
        if c.tag == 'position': d['pos'] = tuple(float(c.get(a)) for a in 'xyz')
        elif c.get('value') is not None: d[c.tag] = float(c.get('value'))
        else: d[c.tag] = hname(c.text or '')
    return d
def gens(r):
    cg = r.find('carGenerators'); return [rec(it) for it in (cg if cg is not None else [])]
def same(a, b):
    if set(a) != set(b): return False
    for k in a:
        x, y = a[k], b[k]
        if k == 'pos':
            if max(abs(p - q) for p, q in zip(x, y)) > 1e-3: return False
        elif isinstance(x, float):
            if abs(x - y) > 1e-3 * max(1, abs(x)): return False
        elif x != y: return False
    return True
def phys(r):
    p = r.find('physicsDictionaries'); return sorted(hname(i.text) for i in p) if p is not None else []
def desc(g): return f"{g.get('carModel')} at ({g['pos'][0]:.2f}, {g['pos'][1]:.2f}, {g['pos'][2]:.2f})"
V = ET.parse(sys.argv[1]).getroot(); vg = gens(V); vp = phys(V)
print('vanilla cargens', len(vg), 'physdicts', len(vp))
for p in sys.argv[2:]:
    R = ET.parse(p).getroot(); g = gens(R); ph = phys(R); left = list(g)
    print('=====', os.path.basename(p), 'cargens', len(g))
    for x in vg:
        m = next((y for y in left if same(x, y)), None)
        if m is not None: left.remove(m); continue
        near = next((y for y in left if max(abs(a - b) for a, b in zip(x['pos'], y['pos'])) < 0.05), None)
        if near is not None: left.remove(near); print('  ~ cargen', desc(x), {k: near[k] for k in x if not same({k: x[k]}, {k: near.get(k)})})
        else: print('  - cargen', desc(x))
    for y in left: print('  + cargen', desc(y))
    if ph != vp: print('  physdicts: removed', sorted(set(vp) - set(ph)), 'added', sorted(set(ph) - set(vp)))
