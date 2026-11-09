# LOD-light pair merge rebuilt from VANILLA (no author file as base): vanilla vw_lodlights_X + vw_distlodlights_X XML, minus every
# author's removed lights, plus every author's changed fields (keyed by light hash). Header, name, parent kept from vanilla
# (removing lights only shrinks the extents, so vanilla's extents still cover everything).
#   lod_merge_vanilla.py <xml dir> <X> <out dir> --author TAG [--remove h1,h2,...]   (repeat --author)
# Each author's pair must be index-aligned (the lod file's hash i and the dist file's position i are the same light). An author
# whose pair is NOT aligned STOPS the merge unless --remove gives its removals explicitly (then nothing else is taken from it).
# Stops on added lights or on a light touched by two authors.
import sys, os, argparse, xml.etree.ElementTree as ET
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'lodlights.py')).read())
ap = argparse.ArgumentParser(); ap.add_argument('d'); ap.add_argument('X'); ap.add_argument('out')
ap.add_argument('--author', action='append', required=True); ap.add_argument('--remove', action='append', default=[])
a = ap.parse_args()
f = lambda who, kind: f'{a.d}/{who}__vw_{kind}lodlights_{a.X}.ymap.xml'
def aligned(who):
    vh = ET.parse(f('vanilla', '')).getroot().find('LODLightsSOA').find('hash').text.split()
    vp = [tuple(it.find(c).get('value') for c in 'xyz') for it in ET.parse(f('vanilla', 'dist')).getroot().find('DistantLODLightsSOA').find('position')]
    h = ET.parse(f(who, '')).getroot().find('LODLightsSOA').find('hash').text.split()
    p = [tuple(it.find(c).get('value') for c in 'xyz') for it in ET.parse(f(who, 'dist')).getroot().find('DistantLODLightsSOA').find('position')]
    hs = set(h); kh = [i for i, x in enumerate(vh) if x in hs]
    rp = lambda t: tuple(round(float(v), 2) for v in t); ps = set(rp(x) for x in p); kp = [i for i, x in enumerate(vp) if rp(x) in ps]
    return kh == kp
V, vns, vcat = load(f('vanilla', ''), f('vanilla', 'dist'))
recs = {r['hash']: dict(r) for r in V}; order = [r['hash'] for r in V]
removed, touched = set(), {}
explicit = {}
for s in a.remove: tag, hs = s.split('=', 1) if '=' in s else (a.author[len(explicit)], s); explicit[tag] = hs.split(',')
for who in a.author:
    if who in explicit:
        for h in explicit[who]:
            if h not in recs: sys.exit(f'STOP: {who} explicit removal {h} not in vanilla')
            if h in touched: sys.exit(f'STOP: light {h} touched by {touched[h]} and {who}')
            touched[h] = who; removed.add(h); print(f'{who}: removed light {h} at {recs[h]["position"]} (explicit list)')
        continue
    if not aligned(who): sys.exit(f'STOP: {who} pair is not index-aligned; give its removals with --remove {who}=h1,h2,...')
    A, ns, cat = load(f(who, ''), f(who, 'dist')); rem, add, chg = diff(V, A)
    if add: sys.exit(f'STOP: {who} adds lights (not handled)')
    for r in rem:
        if r['hash'] in touched: sys.exit(f'STOP: light {r["hash"]} touched by {touched[r["hash"]]} and {who}')
        touched[r['hash']] = who; removed.add(r['hash']); print(f'{who}: removed light {r["hash"]} at {r["position"]}')
    for x, y in chg:
        h = x['hash']
        if h in touched: sys.exit(f'STOP: light {h} touched by {touched[h]} and {who}')
        touched[h] = who
        for k in x:
            if k != 'street' and not same({k: x[k]}, {k: y[k]}): recs[h][k] = y[k]; print(f'{who}: light {h} {k} {x[k]} -> {y[k]}')
keep = [h for h in order if h not in removed]
ns = sum(1 for h in keep if recs[h]['street'])
TL, TD = ET.parse(f('vanilla', '')), ET.parse(f('vanilla', 'dist'))
L, D = TL.getroot().find('LODLightsSOA'), TD.getroot().find('DistantLODLightsSOA')
def setxyz(parent, tag, vals):
    el = parent.find(tag); items = list(el); tmpl = items[0]
    for it in items: el.remove(it)
    for v in vals:
        it = ET.SubElement(el, 'Item'); it.text = tmpl.text; it.tail = tmpl.tail
        for c, s in zip('xyz', v): e = ET.SubElement(it, c); e.set('value', s); e.tail = tmpl.find(c).tail
    if len(el): el[-1].tail = items[-1].tail
def setlist(parent, tag, vals):
    el = parent.find(tag); old = el.text or ''
    # keep CodeWalker's layout: values on lines, same count per line as the source
    lines = [l for l in old.split('\n') if l.strip()]; per = len(lines[0].split()) if lines else 10; ind = (lines[0][:len(lines[0]) - len(lines[0].lstrip())]) if lines else '   '
    el.text = '\n' + '\n'.join(ind + ' '.join(vals[i:i + per]) for i in range(0, len(vals), per)) + '\n' + ind[:-1]
setxyz(L, 'direction', [recs[h]['direction'] for h in keep])
for k in LOD_LISTS: setlist(L, k, [recs[h][k] for h in keep])
setxyz(D, 'position', [recs[h]['position'] for h in keep])
setlist(D, 'RGBI', [recs[h]['RGBI'] for h in keep])
D.find('numStreetLights').set('value', str(ns))
os.makedirs(a.out, exist_ok=True)
TL.write(f'{a.out}/vw_lodlights_{a.X}.ymap.xml', encoding='UTF-8', xml_declaration=True)
TD.write(f'{a.out}/vw_distlodlights_{a.X}.ymap.xml', encoding='UTF-8', xml_declaration=True)
print(f'merged: {len(V)} -> {len(keep)} lights, street {vns} -> {ns}; removed {len(removed)}, touched {len(touched)}')
