# Build merged sc1_28_0 XML: base = KQ's file (full re-export); apply Malmqvist's child-3 edit (polygons it removed / added vs vanilla).
import sys, itertools, xml.etree.ElementTree as ET
van, base, other, out, CH = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
TOL = 0.03
def child(tree, i): return list(tree.getroot().find('Bounds').find('Children'))[i]
def world(ch):
    gc = ch.find('GeometryCenter'); c = [float(gc.get(a)) for a in 'xyz']
    return c, [[float(x) + c[i] for i, x in enumerate(l.split(','))] for l in ch.find('Vertices').text.strip().splitlines()]
def polys(ch):
    c, V = world(ch); mats = [ET.tostring(m).decode().split() for m in ch.find('Materials')]
    res = []
    for p in ch.find('Polygons'):
        vk = sorted(k for k in p.attrib if k.startswith('v'))
        res.append(dict(el=p, tag=p.tag, mat=mats[int(p.get('m'))], pts=[V[int(p.get(k))] for k in vk], extra={k: v for k, v in p.attrib.items() if not k.startswith('v') and k != 'm'}))
    return res
def same(a, b):
    if a['tag'] != b['tag'] or a['mat'] != b['mat'] or len(a['pts']) != len(b['pts']): return False
    perms = itertools.permutations(b['pts'])
    return any(all(max(abs(x - y) for x, y in zip(u, v)) <= TOL for u, v in zip(a['pts'], q)) for q in perms)
tv, tb, to = ET.parse(van), ET.parse(base), ET.parse(other)
PV, PO = polys(child(tv, CH)), polys(child(to, CH))
removed = [p for p in PV if not any(same(p, q) for q in PO)]
added = [q for q in PO if not any(same(q, p) for p in PV)]
print(f'other author, child {CH}: removed {len(removed)}, added {len(added)}')
cb = child(tb, CH); PB = polys(cb)
c, V = world(cb)
mats_b = [ET.tostring(m).decode().split() for m in cb.find('Materials')]
polyel = cb.find('Polygons')
for r in removed:
    hit = [p for p in PB if same(r, p)]
    if len(hit) != 1: sys.exit(f'removed polygon not found exactly once in base ({len(hit)}) -> stop')
    polyel.remove(hit[0]['el']); print(f'  removed {r["tag"]} from base')
vt = cb.find('Vertices'); lines = vt.text.strip().splitlines(); n0 = len(lines); newv = {}
for a in added:
    mi = mats_b.index(a['mat'])   # same material item in base's list
    idx = []
    for pt in a['pts']:
        k = tuple(round(x, 4) for x in pt)
        if k not in newv:   # vertices shared by the added polygons are stored once
            lines.append(', '.join(f'{pt[i] - c[i]:.6f}' for i in range(3))); newv[k] = len(lines) - 1
        idx.append(newv[k])
    attrs = {'m': str(mi)}; attrs.update({f'v{i+1}': str(v) for i, v in enumerate(idx)}); attrs.update(a['extra'])
    e = ET.SubElement(polyel, a['tag'], attrs); e.tail = polyel[-2].tail if len(polyel) > 1 else '\n'
    print(f'  added {a["tag"]} m={mi} verts {idx}')
# vertices no longer referenced by any polygon (the removed box's 4) are dropped and indices compacted
used = sorted({int(v) for p in polyel for k, v in p.attrib.items() if k.startswith('v')})
remap = {old: new for new, old in enumerate(used)}
for p in polyel:
    for k in [k for k in p.attrib if k.startswith('v')]: p.set(k, str(remap[int(p.get(k))]))
lines = [lines[i] for i in used]
ind = vt.text[:len(vt.text) - len(vt.text.lstrip())]; tail = vt.text[len(vt.text.rstrip()):]
vt.text = ind + ind.join(lines) + tail
print(f'  vertices {n0} -> {len(lines)} ({len(newv)} new, unused dropped)')
tb.write(out, encoding='UTF-8', xml_declaration=True)
