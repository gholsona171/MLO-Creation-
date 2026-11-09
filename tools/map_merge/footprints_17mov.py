# Oriented footprints of the 17mov car washes (sector sc1): every entity of 17mov_carwash_ymap / _3_ymap whose archetype is in
# 17mov_carwash_ytyp, its bbox rotated to its placement (CEntityDef yaw inverted). Writes footprints JSON for occl_hits.py.
import sys, os, json, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from occl_lib import quat_yaw, oriented
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'joaat.py')).read())
d, out = sys.argv[1], sys.argv[2]
A = {}
for a in ET.parse(os.path.join(d, 'cw__17mov_carwash_ytyp.ytyp.xml')).getroot().find('archetypes'):
    A[hname(a.findtext('name'))] = ([float(a.find('bbMin').get(c)) for c in 'xyz'], [float(a.find('bbMax').get(c)) for c in 'xyz'], a.findtext('name'))
F = []
for f, site in (('cw__17mov_carwash_ymap.ymap.xml', 'davis'), ('cw__17mov_carwash_3_ymap.ymap.xml', 'strawberry')):
    for it in ET.parse(os.path.join(d, f)).getroot().find('entities'):
        n = hname(it.findtext('archetypeName'))
        if n not in A: continue
        lo, hi, name = A[n]
        if max(h - l for h, l in zip(hi, lo)) < 2: continue          # skip small props
        p = [float(it.find('position').get(c)) for c in 'xyz']; q = {c: float(it.find('rotation').get(c)) for c in 'xyzw'}
        s = float(it.find('scaleXY').get('value')), float(it.find('scaleXY').get('value')), float(it.find('scaleZ').get('value'))
        poly, z = oriented(p, quat_yaw(q), lo, hi, s)
        F.append(dict(id=len(F), pack='17mov_' + site, label=name, poly=poly, z=list(z)))
json.dump(F, open(out, 'w'), indent=1); print(len(F), 'footprints', sorted({(f['pack'], f['label']) for f in F})[:20])
