# ymap entity diff vs vanilla: key = guid (falls back to archetype+position); reports removed / added / changed (field by field), plus non-entity sections
import sys, xml.etree.ElementTree as ET
def ents(r):
    out = []
    for it in r.find('entities'):
        d = {c.tag: (c.text.strip() if c.text and c.text.strip() else tuple(sorted(c.attrib.items()))) for c in it}
        d['_type'] = it.get('type'); out.append(d)
    return out
def pos(d): a = dict(d['position']); return tuple(float(a[k]) for k in 'xyz')
def rot(d): a = dict(d['rotation']); return tuple(float(a[k]) for k in 'xyzw')
def key(d): return dict(d['guid'])['value']
def numeq(a, b, t=1e-4):
    try: return all(abs(float(x[1]) - float(y[1])) <= t for x, y in zip(a, b)) and [x[0] for x in a] == [y[0] for y in b]
    except Exception: return a == b
def changed(a, b):
    ch = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x == y: continue
        if isinstance(x, tuple) and isinstance(y, tuple) and numeq(x, y): continue
        ch.append((k, x, y))
    return ch
def desc(d): p = pos(d); return f"{d['archetypeName']} guid {key(d)} at ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"
V = ET.parse(sys.argv[1]).getroot(); VE = ents(V)
vk = {}
for d in VE: vk.setdefault(key(d), []).append(d)
print(f'vanilla entities {len(VE)}, unique guids {len(vk)}')
for p in sys.argv[2:]:
    R = ET.parse(p).getroot(); E = ents(R); print('=====', p, f'entities {len(E)}')
    ek = {}
    for d in E: ek.setdefault(key(d), []).append(d)
    for k in vk:
        if k not in ek: print('  REMOVED', desc(vk[k][0]))
    for k in ek:
        if k not in vk: print('  ADDED  ', desc(ek[k][0]))
        else:
            c = changed(vk[k][0], ek[k][0])
            if c: print('  CHANGED', desc(vk[k][0]), '->', [(f, y) for f, x, y in c])
    order = [key(d) for d in E if key(d) in vk] == [key(d) for d in VE if key(d) in ek]
    print('  order of kept entities same:', order)
    for c in V:
        if c.tag == 'entities': continue
        a = ' '.join(ET.tostring(c).decode().split()); b = R.find(c.tag); b = ' '.join(ET.tostring(b).decode().split()) if b is not None else None
        if a != b: print(f'  section <{c.tag}> differs: {a[:160]} || {(b or "MISSING")[:160]}')
