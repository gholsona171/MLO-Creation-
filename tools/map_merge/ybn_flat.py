# Flatten a CodeWalker ybn XML into world-space polygons: (child index, child flags, tag, material item, points, extra attrs)
import xml.etree.ElementTree as ET, itertools
from collections import defaultdict
def mat_key(m, mcols):
    # MaterialColourIndex points into the child's MaterialColours list, whose order differs per exporter: compare the colour itself
    out = []
    for c in m:
        v = c.get('value') if c.get('value') is not None else (c.text or '').strip()
        if c.tag == 'MaterialColourIndex': continue   # exporters rebuild the colour palette (values differ), so it is not part of identity
        out.append((c.tag, v))
    return tuple(out)
def flat(p):
    root = ET.parse(p).getroot().find('Bounds'); out = []; kids = list(root.find('Children'))
    for ci, ch in enumerate(kids):
        gc = ch.find('GeometryCenter'); c = [float(gc.get(a)) for a in 'xyz']
        tr = ch.findtext('CompositeTransform').split()
        assert [float(x) for x in tr[:3]] == [1, 0, 0] and [float(x) for x in tr[4:7]] == [0, 1, 0] and [float(x) for x in tr[12:15]] == [0, 0, 0], f'{p} child {ci}: non-identity transform'
        V = [[float(x) + c[i] for i, x in enumerate(l.split(','))] for l in ch.find('Vertices').text.strip().splitlines()]
        mc = ch.find('MaterialColours'); mcols = [l.strip() for l in mc.text.strip().splitlines()] if mc is not None and mc.text and mc.text.strip() else []
        vc = ch.find('VertexColours'); vcols = [l.strip() for l in vc.text.strip().splitlines()] if vc is not None and vc.text and vc.text.strip() else None
        mats = [mat_key(m, mcols) for m in ch.find('Materials')]
        fl = ((ch.findtext('CompositeFlags1') or '').strip(), (ch.findtext('CompositeFlags2') or '').strip())
        for p_ in ch.find('Polygons'):
            vk = sorted(k for k in p_.attrib if k.startswith('v'))
            out.append(dict(ci=ci, flags=fl, tag=p_.tag, mat=mats[int(p_.get('m'))], pts=[V[int(p_.get(k))] for k in vk], vcol=[vcols[int(p_.get(k))] for k in vk] if vcols else None,
                            extra=tuple(sorted((k, v) for k, v in p_.attrib.items() if not k.startswith('v') and k not in ('m', 'f1', 'f2', 'f3'))), el=p_))
    return out
TOL = 0.05   # exporters with GeometryCenter 0,0,0 quantise world coords to ~2.5 cm
def close(p, q, use_flags=True):
    if p['tag'] != q['tag'] or p['mat'] != q['mat'] or len(p['pts']) != len(q['pts']): return False
    if use_flags and p['flags'] != q['flags']: return False
    if len(p['extra']) != len(q['extra']) or any(a[0] != b[0] or abs(float(a[1]) - float(b[1])) > 1e-3 for a, b in zip(p['extra'], q['extra'])): return False
    if p['tag'] == 'Box':   # a box is stored as 4 of its 8 corners, and exporters pick different ones: compare centre + edge lengths
        return box_sig_close(p['pts'], q['pts'])
    return any(all(max(abs(a - b) for a, b in zip(u, v)) <= TOL for u, v in zip(p['pts'], qq)) for qq in itertools.permutations(q['pts']))
def box_sig(pts):
    c = [sum(v[i] for v in pts) / 4 for i in range(3)]
    d = sorted(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for a, b in itertools.combinations(pts, 2))
    return c, d
def box_sig_close(a, b):
    (ca, da), (cb, db) = box_sig(a), box_sig(b)
    return max(abs(x - y) for x, y in zip(ca, cb)) <= TOL and max(abs(x - y) for x, y in zip(da, db)) <= 2 * TOL
def cell(p): return tuple(int(sum(v[i] for v in p['pts']) / len(p['pts']) // 1.0) for i in range(3))
def diff(A, B, use_flags=True):
    grid = defaultdict(list)
    for j, q in enumerate(B): grid[cell(q)].append(j)
    used = set(); rem = []; pairs = []
    for i, p in enumerate(A):
        cx, cy, cz = cell(p); hit = None
        for d in itertools.product((-1, 0, 1), repeat=3):
            for j in grid.get((cx + d[0], cy + d[1], cz + d[2]), []):
                if j not in used and close(p, B[j], use_flags): hit = j; break
            if hit is not None: break
        if hit is None: rem.append(i)
        else: used.add(hit); pairs.append((i, hit))
    add = [j for j in range(len(B)) if j not in used]
    return rem, add, pairs
def span(ps):
    xs = [v[0] for p in ps for v in p['pts']]; ys = [v[1] for p in ps for v in p['pts']]; zs = [v[2] for p in ps for v in p['pts']]
    return f'x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f} z {min(zs):.1f}..{max(zs):.1f}' if xs else '-'
def clusters(ps, gap=3.0):
    # group polygons whose bounding boxes come within `gap` m of each other
    boxes = []
    for p in ps:
        xs = [v[0] for v in p['pts']]; ys = [v[1] for v in p['pts']]; zs = [v[2] for v in p['pts']]
        boxes.append([min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)])
    par = list(range(len(ps)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    order = sorted(range(len(ps)), key=lambda i: boxes[i][0])
    for a_i, a in enumerate(order):
        for b in order[a_i + 1:]:
            if boxes[b][0] > boxes[a][3] + gap: break
            A, B = boxes[a], boxes[b]
            if all(A[k] - gap <= B[k + 3] and B[k] - gap <= A[k + 3] for k in range(3)): par[f(a)] = f(b)
    groups = defaultdict(list)
    for i in range(len(ps)): groups[f(i)].append(ps[i])
    return sorted(groups.values(), key=lambda g: -len(g))
