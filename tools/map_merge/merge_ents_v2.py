# Merged ymap XML: base author's XML; every entity another author changed vs vanilla (matched by guid) is replaced with that author's Item verbatim,
# entities another author removed are removed, entities another author added are appended. Names are compared as joaat hashes.
# Stops if two authors touched the same entity, or if a non-entity section of another author differs from vanilla (other than header/extents/block).
import sys, os, re, xml.etree.ElementTree as ET
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'joaat.py')).read())
van, base, out, others = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
def items(r): return {it.find('guid').get('value'): it for it in r.find('entities')}
def norm(it):
    s = ' '.join(ET.tostring(it).decode().split())
    return re.sub(r'<archetypeName>([^<]*)</', lambda m: f'<archetypeName>{hname(m.group(1))}</', s)
NUM = r'-?\d+\.?\d*(?:E-?\d+)?'
def near(a, b):
    na, nb = norm(a), norm(b)
    fa, fb = re.findall(NUM, re.sub(r'hash_[0-9A-F]{8}', '', na)), re.findall(NUM, re.sub(r'hash_[0-9A-F]{8}', '', nb))
    shape = lambda t: re.sub(NUM, '#', re.sub(r'hash_[0-9A-F]{8}', 'H', t))   # structure with every number blanked; numbers compared below
    return shape(na) == shape(nb) and re.findall(r'hash_[0-9A-F]{8}', na) == re.findall(r'hash_[0-9A-F]{8}', nb) and len(fa) == len(fb) and all(abs(float(x) - float(y)) <= 1e-3 for x, y in zip(fa, fb))   # 1 mm: re-saved files carry float noise
tv, tb = ET.parse(van), ET.parse(base); V, B = items(tv.getroot()), items(tb.getroot())
touched = {g: 'base' for g in V if g not in B or not near(V[g], B[g])}
touched.update({g: 'base' for g in B if g not in V})
ents = tb.getroot().find('entities')
for op in others:
    to = ET.parse(op); O = items(to.getroot()); tag = os.path.basename(op).split('__')[0]
    for g in V:
        if g in O and near(V[g], O[g]): continue
        if g in touched: sys.exit(f'STOP: entity guid {g} ({V[g].findtext("archetypeName")}) changed by {touched[g]} and {tag}')
        touched[g] = tag
        if g not in O:
            ents.remove(B[g]); print(f'{tag}: removed entity guid {g}')
        else:
            lst = list(ents); i = lst.index(B[g]); new = O[g]; new.tail = B[g].tail
            ents.remove(B[g]); ents.insert(i, new); B[g] = new; print(f'{tag}: took changed entity guid {g} ({hname(new.findtext("archetypeName"))}) at index {i}')
    for g in O:
        if g not in V:
            if g in B: sys.exit(f'STOP: added guid {g} exists in base too')
            new = O[g]; new.tail = list(ents)[-1].tail; ents.append(new); touched[g] = tag; print(f'{tag}: added entity guid {g}')
# header extents = union of every author's extents (each author's own file covers its own entities)
for op in others:
    ro = ET.parse(op).getroot()
    for t, f in (('streamingExtentsMin', min), ('entitiesExtentsMin', min), ('streamingExtentsMax', max), ('entitiesExtentsMax', max)):
        e, o = tb.getroot().find(t), ro.find(t)
        for a in 'xyz':
            v = f(float(e.get(a)), float(o.get(a)))
            if v != float(e.get(a)): print(f'  header {t}.{a}: {e.get(a)} -> {o.get(a)} (from {os.path.basename(op).split("__")[0]})'); e.set(a, o.get(a))
tb.write(out, encoding='UTF-8', xml_declaration=True); print('base changed', sum(1 for v in touched.values() if v == 'base'))
