# Entity ymap merge rebuilt from VANILLA: vanilla XML + every author's edits vs vanilla.
#   merge_ymap_vanilla.py <vanilla.xml> <out.xml> <author.xml> [<author.xml> ...]   (author tag = file name before '__')
# Entities (matched by guid): an author's changed entity replaces the vanilla Item verbatim (in place, order kept), a removed one is
# removed, an added one is appended. Car generators (matched field by field, numbers 1e-3): removed / added / changed by position.
# Header: streaming + entities extents = union of vanilla and every author. Name and parent stay vanilla's.
# STOPS when two authors touch the same entity or car generator, or when an author changed any other section (physicsDictionaries
# are compared as joaat hashes; block is ignored).
import sys, os, re, xml.etree.ElementTree as ET
H = os.path.dirname(os.path.abspath(sys.argv[0]))
exec(open(os.path.join(H, 'joaat.py')).read())
van, out, authors = sys.argv[1], sys.argv[2], sys.argv[3:]
NUM = r'-?\d+\.?\d*(?:E[-+]?\d+)?'
def norm(it):
    s = ' '.join(ET.tostring(it).decode().split())
    return re.sub(r'<(archetypeName|carModel|popGroup)>([^<]*)</', lambda m: f'<{m.group(1)}>{hname(m.group(2)) if m.group(2) else ""}</', s)
def near(a, b):
    na, nb = norm(a), norm(b)
    strip = lambda t: re.sub(r'hash_[0-9A-F]{8}', 'H', t)
    fa, fb = re.findall(NUM, strip(na)), re.findall(NUM, strip(nb))
    return re.sub(NUM, '#', strip(na)) == re.sub(NUM, '#', strip(nb)) and re.findall(r'hash_[0-9A-F]{8}', na) == re.findall(r'hash_[0-9A-F]{8}', nb) \
        and len(fa) == len(fb) and all(abs(float(x) - float(y)) <= 1e-3 * max(1.0, abs(float(x))) for x, y in zip(fa, fb))
def ents(r): return {it.find('guid').get('value'): it for it in r.find('entities')}
def gens(r): cg = r.find('carGenerators'); return list(cg) if cg is not None else []
def gpos(it): p = it.find('position'); return tuple(float(p.get(c)) for c in 'xyz')
def phys(r): p = r.find('physicsDictionaries'); return sorted(hname(i.text) for i in p) if p is not None else []
SKIP = {'name', 'parent', 'entities', 'carGenerators', 'block', 'physicsDictionaries', 'streamingExtentsMin', 'streamingExtentsMax', 'entitiesExtentsMin', 'entitiesExtentsMax'}
tv = ET.parse(van); V = tv.getroot(); VE = ents(V); EL = V.find('entities'); CG = V.find('carGenerators'); VG = gens(V)
touched, gtouched, log = {}, {}, []
for ap in authors:
    tag = os.path.basename(ap).split('__')[0]; A = ET.parse(ap).getroot(); AE = ents(A)
    for c in V:
        if c.tag in SKIP: continue
        o = A.find(c.tag)
        if o is None or not near(c, o): sys.exit(f'STOP: {tag} changed section <{c.tag}> (not handled)')
    if phys(A) != phys(V): sys.exit(f'STOP: {tag} changed physicsDictionaries')
    for g, it in VE.items():
        if g in AE and near(it, AE[g]): continue
        if g in touched: sys.exit(f'STOP: entity guid {g} touched by {touched[g]} and {tag}')
        touched[g] = tag
        cur = [x for x in EL if x.find('guid').get('value') == g][0]
        if g not in AE: EL.remove(cur); log.append(f'{tag}: removed entity guid {g} ({hname(it.findtext("archetypeName"))})')
        else:
            i = list(EL).index(cur); new = AE[g]; new.tail = cur.tail; EL.remove(cur); EL.insert(i, new)
            log.append(f'{tag}: changed entity guid {g} ({hname(it.findtext("archetypeName"))})')
    for g, it in AE.items():
        if g in VE: continue
        if g in touched: sys.exit(f'STOP: added guid {g} from {touched[g]} and {tag}')
        touched[g] = tag; it.tail = EL[-1].tail if len(EL) else '\n '; EL.append(it); log.append(f'{tag}: added entity guid {g} ({hname(it.findtext("archetypeName"))})')
    AG = gens(A); left = list(AG)
    for it in VG:
        m = next((x for x in left if near(it, x)), None)
        if m is not None: left.remove(m); continue
        k = gpos(it)
        if k in gtouched: sys.exit(f'STOP: car generator at {k} touched by {gtouched[k]} and {tag}')
        gtouched[k] = tag
        n = next((x for x in left if max(abs(p - q) for p, q in zip(gpos(x), k)) < 0.05), None)
        cur = [x for x in CG if x is it or near(x, it)][0]
        if n is None: CG.remove(cur); log.append(f'{tag}: removed car generator {it.findtext("carModel") or "-"} at ({k[0]:.2f}, {k[1]:.2f}, {k[2]:.2f})')
        else:
            left.remove(n); i = list(CG).index(cur); n.tail = cur.tail; CG.remove(cur); CG.insert(i, n); log.append(f'{tag}: changed car generator at {k}')
    for x in left:
        k = gpos(x)
        if k in gtouched: sys.exit(f'STOP: car generator at {k} touched twice')
        gtouched[k] = tag; x.tail = CG[-1].tail if len(CG) else '\n '; CG.append(x); log.append(f'{tag}: added car generator at {k}')
    for t, fn in (('streamingExtentsMin', min), ('entitiesExtentsMin', min), ('streamingExtentsMax', max), ('entitiesExtentsMax', max)):
        e, o = V.find(t), A.find(t)
        for c in 'xyz':
            if fn(float(e.get(c)), float(o.get(c))) != float(e.get(c)): log.append(f'  header {t}.{c}: {e.get(c)} -> {o.get(c)} (from {tag})'); e.set(c, o.get(c))
print('\n'.join(log)); tv.write(out, encoding='UTF-8', xml_declaration=True)
print(f'saved {out}: {len(EL)} entities, {len(CG) if CG is not None else 0} car generators; {len(touched)} entities and {len(gtouched)} car gens from authors')
