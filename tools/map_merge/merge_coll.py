# N-way collision merge (CodeWalker ybn XML).
# Base author's file + every other author's geometry changes vs vanilla:
#   polygons removed (matched in world space, any child), polygons added (into the base child that holds the same vanilla
#   polygons as that author's child, or into a new child copied from the author's), child flag changes.
# Every child is then written again from world-space polygons: GeometryCenter = centre of its vertices (so CodeWalker's
# int16 quantisation cannot clamp), vertices shared, unused ones dropped, material + material-colour lists remapped.
# Stops when two authors change the same polygon, or the same child's flags differently.
# usage: python -I merge_coll.py vanilla.xml base.xml out.xml other1.xml [other2.xml ...]
import sys, os, copy, xml.etree.ElementTree as ET
from collections import Counter
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'ybn_flat.py')).read())
van, base, out, others = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
V = flat(van)
TB = ET.parse(base); B = flat(base); kidsB = list(TB.getroot().find('Bounds').find('Children'))
EMPTY = {'tag': None, 'mat': None, 'pts': [], 'flags': None, 'extra': ()}

def kid_list(p): return list(ET.parse(p).getroot().find('Bounds').find('Children'))
def kflags(ch): return ((ch.findtext('CompositeFlags1') or '').strip(), (ch.findtext('CompositeFlags2') or '').strip())
def child_map(A, pairs):   # author child index -> vanilla child index (majority of kept polygons)
    c = {}
    for i, j in pairs: c.setdefault(A[j]['ci'], Counter())[V[i]['ci']] += 1
    return {k: v.most_common(1)[0][0] for k, v in c.items()}

rb, ab, pb = diff(V, B, use_flags=False)
b_of_v = {}
for i, j in pb: b_of_v.setdefault(V[i]['ci'], Counter())[B[j]['ci']] += 1
base_child_for_vchild = {k: v.most_common(1)[0][0] for k, v in b_of_v.items()}
vflags = {p['ci']: p['flags'] for p in V}
changed_by = {i: 'base' for i in rb}
alive = [True] * len(B); extra = []; new_kids = []; flag_set = {}

for op in others:
    tag = os.path.basename(op).split('__')[0]; A = flat(op); kidsA = kid_list(op)
    ra, aa, pa = diff(V, A, use_flags=False); cmap = child_map(A, pa)
    for ca in range(len(kidsA)):   # a child whose polygons all moved (e.g. re-quantised): same index + same flags1 as vanilla = same child
        if ca not in cmap and ca in vflags and kflags(kidsA[ca])[0] == vflags[ca][0] and ca not in cmap.values():
            cmap[ca] = ca; print(f'{tag}: child {ca} has no unchanged polygons; mapped to vanilla child {ca} by index and flags')
    for ca, cv in cmap.items():
        fa = kflags(kidsA[ca]); vf = vflags[cv]
        if fa != vf:
            cb = base_child_for_vchild.get(cv)
            fb = kflags(kidsB[cb])
            if fb != vf and fb != fa: sys.exit(f'STOP: flags of vanilla child {cv} changed differently by base and {tag}')
            if fb != fa: flag_set[cb] = fa; print(f'{tag}: base child {cb} takes the flags of {tag} child {ca}')
    mine = []
    for i in ra:
        if changed_by.get(i) not in (None, 'base'): sys.exit(f'STOP: vanilla polygon {span([V[i]])} removed by {changed_by[i]} and {tag}')
        if changed_by.get(i) == 'base': continue      # both removed it: agree
        changed_by[i] = tag; mine.append(i)
    hits = diff([V[i] for i in mine], [B[j] if alive[j] else EMPTY for j in range(len(B))], use_flags=False)[2]
    if len(hits) != len(mine): sys.exit(f'STOP: {tag} removes {len(mine)} polygons but only {len(hits)} found in base')
    for _, j in hits: alive[j] = False
    newmap = {}
    for j in aa:
        p = A[j]; ca = p['ci']; cv = cmap.get(ca)
        if cv is not None and cv in base_child_for_vchild:
            extra.append((base_child_for_vchild[cv], p, kidsA[ca]))
        else:
            if ca not in newmap:
                e = copy.deepcopy(kidsA[ca]); newmap[ca] = len(kidsB) + len(new_kids); new_kids.append(e)
                print(f'{tag}: new child from {tag} child {ca} ({kflags(e)[0][:40]})')
            extra.append((newmap[ca], p, kidsA[ca]))
    print(f'{tag}: removed {len(hits)} polygons from base, added {len(aa)}')

children_el = TB.getroot().find('Bounds').find('Children')
for e in new_kids: e.tail = kidsB[-1].tail; children_el.append(e)
kids = list(children_el)
per = {i: [] for i in range(len(kids))}
for j, p in enumerate(B):
    if alive[j]: per[p['ci']].append((p, kidsB[p['ci']]))
for ci, p, src in extra: per[ci].append((p, src))

def matitem_key(m): return tuple((c.tag, c.get('value') if c.get('value') is not None else (c.text or '').strip()) for c in m if c.tag != 'MaterialColourIndex')
def colour_of(m, cols):   # some exporters write a colour index past the end of the list
    i = int(m.find('MaterialColourIndex').get('value')); return cols[i] if 0 <= i < len(cols) else None
def colours(ch, t):
    x = ch.findtext(t); return [l.strip() for l in x.strip().splitlines()] if x and x.strip() else []
touched = set(ci for ci, _, _ in extra) | set(B[j]['ci'] for j in range(len(B)) if not alive[j]) | set(flag_set)
IND, END = '\n' + ' ' * 5, '\n' + ' ' * 4
for ci, ch in enumerate(kids):
    polys = per[ci]
    if ci >= len(kidsB):   # new child: start from empty lists
        for t in ('Materials',): ch.find(t).clear()
    mats_el = ch.find('Materials'); mats = list(mats_el)
    mcols = colours(ch, 'MaterialColours') if ci < len(kidsB) else []
    has_mc = ch.find('MaterialColours') is not None and (ci >= len(kidsB) and bool(colours(polys[0][1], 'MaterialColours')) if polys and ci >= len(kidsB) else bool(mcols))
    has_vc = bool(colours(ch, 'VertexColours'))
    keys = {}
    for k, m in enumerate(mats):
        keys.setdefault((matitem_key(m), colour_of(m, mcols) if mcols else None), k)
    verts, vcols, vidx, newpolys = [], [], {}, []
    for p, src in polys:
        sm = list(src.find('Materials')); smc = colours(src, 'MaterialColours')
        el = p['el']; mi = sm[int(el.get('m'))]
        colour = colour_of(mi, smc) if smc else None
        k = (matitem_key(mi), colour if has_mc else None)
        if k not in keys:
            m2 = copy.deepcopy(mi)
            if has_mc:
                if colour is None: colour = mcols[0] if mcols else '255, 255, 255, 255'
                if colour not in mcols: mcols.append(colour)
                m2.find('MaterialColourIndex').set('value', str(mcols.index(colour)))
            else:
                m2.find('MaterialColourIndex').set('value', '0')
            m2.tail = IND; mats_el.append(m2); mats.append(m2); keys[k] = len(mats) - 1
        attrs = dict(el.attrib); attrs['m'] = str(keys[k])
        for n, a in enumerate(sorted(x for x in el.attrib if x.startswith('v'))):
            pt = p['pts'][n]
            vc = ((p['vcol'][n] if p.get('vcol') else '255, 255, 255, 255') if has_vc else None)
            key = (round(pt[0], 4), round(pt[1], 4), round(pt[2], 4), vc)
            if key not in vidx: vidx[key] = len(verts); verts.append(pt); vcols.append(vc)
            attrs[a] = str(vidx[key])
        newpolys.append((el.tag, attrs))
    if not verts: sys.exit(f'STOP: child {ci} would be empty - not handled')
    if mats_el is not None and len(mats_el): mats_el.text = IND; mats_el[-1].tail = END
    lo = [min(v[i] for v in verts) for i in range(3)]; hi = [max(v[i] for v in verts) for i in range(3)]
    gc = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ch.find('GeometryCenter').attrib.update({a: f'{gc[i]:.6f}' for i, a in enumerate('xyz')})
    ch.find('Vertices').text = IND + IND.join(', '.join(f'{v[i] - gc[i]:.6f}' for i in range(3)) for v in verts) + END
    if has_vc: ch.find('VertexColours').text = IND + IND.join(vcols) + END
    if has_mc: ch.find('MaterialColours').text = IND + IND.join(mcols) + END
    pe = ch.find('Polygons'); pe.clear(); pe.text = IND
    for t, a in newpolys:
        e = ET.SubElement(pe, t, a); e.tail = IND
    pe[-1].tail = END
    if ci in flag_set: ch.find('CompositeFlags1').text, ch.find('CompositeFlags2').text = flag_set[ci]
    if ci in touched or ci >= len(kidsB):   # bounds = union of the old box and the new geometry (+ radius of round shapes)
        r = max([float(a['radius']) for t, a in newpolys if 'radius' in a] + [0.0])
        old = ci < len(kidsB)
        bmin = [min(float(ch.find('BoxMin').get(a)), lo[i] - r) if old else lo[i] - r for i, a in enumerate('xyz')]
        bmax = [max(float(ch.find('BoxMax').get(a)), hi[i] + r) if old else hi[i] + r for i, a in enumerate('xyz')]
        mid = [(bmin[i] + bmax[i]) / 2 for i in range(3)]
        for tg, vals in (('BoxMin', bmin), ('BoxMax', bmax), ('BoxCenter', mid), ('SphereCenter', mid)):
            ch.find(tg).attrib.update({a: f'{vals[i]:.6f}' for i, a in enumerate('xyz')})
        ch.find('SphereRadius').set('value', f'{sum((bmax[i] - bmin[i]) ** 2 for i in range(3)) ** 0.5 / 2:.6f}')
root = TB.getroot().find('Bounds')
for i, a in enumerate('xyz'):
    root.find('BoxMin').set(a, f'{min([float(k.find("BoxMin").get(a)) for k in kids] + [float(root.find("BoxMin").get(a))]):.6f}')
    root.find('BoxMax').set(a, f'{max([float(k.find("BoxMax").get(a)) for k in kids] + [float(root.find("BoxMax").get(a))]):.6f}')
TB.write(out, encoding='UTF-8', xml_declaration=True)
print('children', len(kids), 'polygons', sum(len(per[i]) for i in per))
