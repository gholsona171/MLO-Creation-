# Merge a LOD-light pair: base author's two XMLs + each other author's per-light changes vs vanilla (keyed by light hash).
# Handles: light changed (any field), light removed. Stops on added lights or on a light touched by two authors.
# Header extents = union over authors. Writes merged__vw_lodlights_X / merged__vw_distlodlights_X XML.
import sys, os, xml.etree.ElementTree as ET
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'lodlights.py')).read())
d, X, base, others = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
f = lambda who, kind: f'{d}/{who}__vw_{kind}lodlights_{X}.ymap.xml'
V, _, _ = load(f('vanilla', ''), f('vanilla', 'dist'))
B, bns, _ = load(f(f'src_{base}', ''), f(f'src_{base}', 'dist'))
touched = {}
rem, add, chg = diff(V, B)
for r in rem: touched[r['hash']] = base
for a, b in chg: touched[a['hash']] = base
if add: sys.exit('STOP: base adds lights (not handled)')
TL, TD = ET.parse(f(f'src_{base}', '')), ET.parse(f(f'src_{base}', 'dist'))
L, D = TL.getroot().find('LODLightsSOA'), TD.getroot().find('DistantLODLightsSOA')
def cols():
    return {'hash': L.find('hash').text.split()}
for o in others:
    A, ns, _ = load(f(f'src_{o}', ''), f(f'src_{o}', 'dist')); rem, add, chg = diff(V, A)
    if add: sys.exit(f'STOP: {o} adds lights (not handled)')
    for r in rem + [a for a, b in chg]:
        if r['hash'] in touched: sys.exit(f'STOP: light hash {r["hash"]} at {r["position"]} changed by {touched[r["hash"]]} and {o}')
        touched[r['hash']] = o
    hashes = L.find('hash').text.split()
    for a, b in chg:
        i = hashes.index(a['hash'])
        for k in LOD_LISTS:
            if a[k] != b[k]:
                el = L.find(k); vals = el.text.split(); vals[i] = b[k]; el.text = ' '.join(vals); print(f'{o}: light {a["hash"]} {k} {a[k]} -> {b[k]}')
        for k, el, sub in (('direction', L, 'direction'), ('position', D, 'position')):
            if not same({k: a[k]}, {k: b[k]}):
                it = list(el.find(sub))[i]
                for ax, v in zip('xyz', b[k]): it.find(ax).set('value', v)
                print(f'{o}: light {a["hash"]} {k} -> {b[k]}')
        if a['RGBI'] != b['RGBI']:
            el = D.find('RGBI'); vals = el.text.split(); vals[i] = b['RGBI']; el.text = ' '.join(vals); print(f'{o}: light {a["hash"]} RGBI -> {b["RGBI"]}')
    if rem: sys.exit(f'STOP: {o} removes lights; removal merge not written yet')  # (base removes here; others only change)
    for t, fn in (('streamingExtentsMin', min), ('entitiesExtentsMin', min), ('streamingExtentsMax', max), ('entitiesExtentsMax', max)):
        for T, kind in ((TL, ''), (TD, 'dist')):
            e, oe = T.getroot().find(t), ET.parse(f(f'src_{o}', kind)).getroot().find(t)
            for ax in 'xyz':
                if fn(float(e.get(ax)), float(oe.get(ax))) != float(e.get(ax)): print(f'  {kind}lodlights header {t}.{ax}: {e.get(ax)} -> {oe.get(ax)} (from {o})'); e.set(ax, oe.get(ax))
TL.write(f('merged', ''), encoding='UTF-8', xml_declaration=True); TD.write(f('merged', 'dist'), encoding='UTF-8', xml_declaration=True)
print('touched', len(touched), 'lights;', sum(1 for v in touched.values() if v == base), 'by', base)
