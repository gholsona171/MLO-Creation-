# Oriented footprints (2D polygon + z range) of every building / MLO room / exterior entity the Grove-area packs place.
# CEntityDef yaw is stored inverted (world yaw = -stored); a CMloInstanceDef is not inverted (checked: kq_pharmacy's rooms rotated
# with +yaw reproduce its ymap entitiesExtents; -yaw is 13 m off). Usage: footprints_grove.py <xml dir> <vanilla_bounds.json> <out.json>
import sys, os, math, json, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from occl_lib import quat_yaw, oriented
from joaat import hname
X, VB, OUT = sys.argv[1], json.load(open(sys.argv[2], encoding='utf-8-sig')), sys.argv[3]
def P(f): return ET.parse(os.path.join(X, f)).getroot()
def v3(el): return [float(el.get(k)) for k in 'xyz']
def q4(el): return {k: float(v) for k, v in el.attrib.items()}
def arch_map(*ytyps):
    m = {}
    for y in ytyps:
        for a in P(y).find('archetypes'): m[hname(a.find('name').text)] = a
    return m
def bounds(h, A):
    if h in A: a = A[h]; return v3(a.find('bbMin')), v3(a.find('bbMax')), A[h].find('name').text
    if h in VB: return VB[h]['bbMin'], VB[h]['bbMax'], VB[h]['name']
    return None
F = []
def add(pack, kind, label, pos, yaw, lo, hi):
    poly, z = oriented(pos, yaw, lo, hi); F.append(dict(id=len(F), pack=pack, kind=kind, label=label, pos=[round(v, 2) for v in pos], poly=poly, z=z))
def entities(pack, ymap, A, kind='ext', only=None):
    for e in P(ymap).find('entities'):
        if e.get('type') != 'CEntityDef': continue
        h = hname(e.find('archetypeName').text)
        if only and h not in only: continue
        b = bounds(h, A)
        if not b: print('no bounds', pack, h); continue
        add(pack, kind, only[h] if only else b[2], v3(e.find('position')), quat_yaw(q4(e.find('rotation')), -1), b[0], b[1])
def mlo(pack, ymap, A, rooms=True):
    for e in P(ymap).find('entities'):
        if e.get('type') != 'CMloInstanceDef': continue
        a = A[hname(e.find('archetypeName').text)]; p = v3(e.find('position')); yaw = quat_yaw(q4(e.find('rotation')), +1)
        if rooms:
            for r in a.find('rooms'):
                if r.find('name').text == 'limbo': continue
                lo, hi = v3(r.find('bbMin')), v3(r.find('bbMax')); lo, hi = [min(x, y) for x, y in zip(lo, hi)], [max(x, y) for x, y in zip(lo, hi)]
                add(pack, 'mlo_room', r.find('name').text, p, yaw, lo, hi)
        else:   # rooms are bogus (+-360 m): use the interior's own entities
            c, s = math.cos(yaw), math.sin(yaw)
            for me in a.find('entities'):
                b = bounds(hname(me.find('archetypeName').text), A)
                if not b or max(b[1][0] - b[0][0], b[1][1] - b[0][1]) > 200: continue
                lp = v3(me.find('position')); wp = [p[0] + c * lp[0] - s * lp[1], p[1] + s * lp[0] + c * lp[1], p[2] + lp[2]]
                add(pack, 'mlo_entity', b[2], wp, yaw + quat_yaw(q4(me.find('rotation')), -1), b[0], b[1])
# hood (Malmqvist Vagos hood): exterior shells
A = arch_map('hood__hood_exterior_f_va_metadata2.ytyp.xml'); entities('hood', 'hood__hood_exterior_f_va_placement.ymap.xml', A)
# Grimzy compound: own exterior entities, MLO rooms, and the vanilla building models it replaces (placed by its lr_ ymaps)
A = arch_map('grimzy__grimzygrv_yt.ytyp.xml'); entities('grimzy', 'grimzy__grimzygrv_ym.ymap.xml', A); mlo('grimzy', 'grimzy__grimzygrv_ym.ymap.xml', A)
REPL = ['sc1_21_roundred', 'sc1_21_details_00', 'sc1_21_details_06', 'sc1_21_emc', 'sc1_21_res02', 'sc1_21_res_det02', 'sc1_21_ground01', 'sc1_21_ground02', 'sc1_props_flyers15', 'sc1_rd_r3_04', 'sc1_rd_wireset_14']
only = {hname(n): n for n in REPL}
for y in ['grimzy__lr_sc1_21_strm_0.ymap.xml', 'grimzy__lr_sc1_21_strm_1.ymap.xml', 'grimzy__lr_sc1_rd_long_1.ymap.xml', 'grimzy__lr_sc1_rd_strm_0.ymap.xml']:
    entities('grimzy', y, {}, 'replaced_vanilla', only)
# gcom Groove Street: exterior entities + the three interiors (rooms are +-360 m, so their entities)
A = arch_map('gcom__gcom_groove_int.ytyp.xml', 'gcom__gcom_groove_gar_int.ytyp.xml', 'gcom__gcom_groove_mine_int.ytyp.xml')
entities('gcom', 'gcom__gcom_groove_ext.ymap.xml', A)
for y in ['gcom__gcom_groove_int_milo.ymap.xml', 'gcom__gcom_groove_gar_int_milo.ymap.xml', 'gcom__gcom_groove_mine_int_milo.ymap.xml']: mlo('gcom', y, A, rooms=False)
# kq Davis pharmacy: MLO rooms (its MLO archetype bbox is all zero)
A = arch_map('kq__kq_pharmacy.ytyp.xml'); mlo('kq', 'kq__kq_pharmacy.ymap.xml', A)
json.dump(F, open(OUT, 'w'))
from collections import Counter
print(Counter((f['pack'], f['kind']) for f in F))
for pk in ['hood', 'grimzy', 'gcom', 'kq']:
    xs = [x for f in F if f['pack'] == pk for x, y in f['poly']]; ys = [y for f in F if f['pack'] == pk for x, y in f['poly']]
    print(pk, 'x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
