"""The distance models (LOD / SLOD) that still draw cleared things over the site. site_clear.py swaps a LOD to jy_empty only when ALL
its children were cleared, and never touches the SLODs above the LODs, so a combined LOD or SLOD that also covers off-site props
kept drawing the cleared bushes, junk and the old hangar from ~100 m out (seen from the road and the air, 2026-11-23). This lists
every LOD / SLOD placement in the area's parent ymaps (cs4_02, hei_cs4_02, lr_cs4_02) that site_clear.py left in place, within
REACH of the site, minus the drawn ground (terrain names: land / road / barrier ..., handled by terrain.py or left alone).
lod_extract.ps1 pulls their models from the game and lod_cut.py cuts the site out of them.
Run: py -3 lod_list.py     Output ../site/lod_targets.tsv (archetype, x, y, z, qx, qy, qz, qw)"""
import math, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T)); import site_plan as SP
M = T.parent; VAN = M / 'vanilla'; CLR = M / 'site' / 'xml'
REACH = 200.0
TERRAIN = re.compile(r'land|dtrack|retain|erotub|brrier|rumble|_rd|road|rocks?g?$', re.I)
LODS = ('LODTYPES_DEPTH_LOD', 'LODTYPES_DEPTH_SLOD1', 'LODTYPES_DEPTH_SLOD2', 'LODTYPES_DEPTH_SLOD3', 'LODTYPES_DEPTH_SLOD4')
PTS = [p for poly in SP.PAVED for p in poly]


def near_site(x, y): return SP.on_site(x, y) or min(math.hypot(x - px, y - py) for px, py in PTS) <= REACH


def main():
    seen = {}
    for parent in ('cs4_02', 'hei_cs4_02', 'lr_cs4_02'):
        van = list(ET.parse(VAN / f'{parent}.ymap.xml').getroot().find('entities'))
        out = list(ET.parse(CLR / f'{parent}.ymap.xml').getroot().find('entities'))
        assert len(van) == len(out), parent
        for v, o in zip(van, out):
            a = v.findtext('archetypeName'); p = v.find('position'); q = v.find('rotation')
            if v.findtext('lodLevel') not in LODS or o.findtext('archetypeName') == 'jy_empty' or TERRAIN.search(a): continue
            x, y, z = (float(p.get(k)) for k in 'xyz')
            if not near_site(x, y): continue
            rec = (round(x, 3), round(y, 3), round(z, 3)) + tuple(round(float(q.get(k)), 6) for k in ('x', 'y', 'z', 'w'))
            assert seen.get(a.lower(), rec) == rec, f'{a}: placed twice at different spots (a cut would show at both)'
            seen[a.lower()] = rec
    (M / 'site' / 'lod_targets.tsv').write_text(''.join('\t'.join([a] + [str(c) for c in r]) + '\n' for a, r in sorted(seen.items())), encoding='utf-8')
    print('LOD_LIST_PASS', len(seen), 'distance models')


if __name__ == '__main__': main()
