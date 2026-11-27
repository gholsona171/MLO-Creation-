"""The vanilla drawables the site steps edit, listed from the extracted maps (../vanilla/*.ymap.xml, vanilla_extract.ps1 -Box):
  * the drawn ground (site_plan.TERRAIN_RX: land / beach / trail ... models) placed as HD / orphan HD within REACH of the site:
    terrain.py lowers them under the new grade (a model with nothing on the site comes out unchanged and is not shipped);
  * every merged wire mesh (site_plan.WIRE_RX) within REACH: wires.py cuts / re-hangs them.
Archetypes the maps name only by hash are skipped (none of the ground or wire models here are). Road models (cs4_roads_*) are left
alone: the site keeps 3 m off every road, and editing them would clash with every road mod.
Run: py -3 vanilla_models.py     Output ../vanilla/models.txt (one comma list for vanilla_extract.ps1 -Ydr) + models.tsv (name, kind,
x, y, z of its placement; every placement must be identity-rotated, the steps assume it)"""
import glob, os, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T)); import site_plan as SP
M = T.parent; VAN = M / 'vanilla'
REACH = 200.0
HD = ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD')
ROAD = re.compile(r'road', re.I)


def main():
    seen = {}
    for f in sorted(VAN.glob('*.ymap.xml')):
        es = ET.parse(f).getroot().find('entities')
        for e in (es if es is not None else []):
            a = (e.findtext('archetypeName') or '').lower()
            if e.findtext('lodLevel') not in HD or a.startswith('hash_'): continue
            kind = 'wire' if SP.WIRE_RX.search(a) else 'terrain' if SP.TERRAIN_RX.search(a) and not ROAD.search(a) else None
            if not kind: continue
            p = e.find('position'); x, y, z = (float(p.get(k)) for k in 'xyz')
            if not SP.near_site(x, y, REACH): continue
            q = e.find('rotation'); assert abs(float(q.get('z'))) < 1e-4 and abs(float(q.get('w'))) > 0.9999, f'{a}: not identity-rotated'
            rec = (kind, round(x, 4), round(y, 4), round(z, 4))
            assert seen.get(a, rec) == rec, f'{a}: placed twice at different spots'
            seen[a] = rec
    (VAN / 'models.txt').write_text(','.join(sorted(seen)), encoding='utf-8')
    (VAN / 'models.tsv').write_text(''.join(f'{a}\t{k}\t{x}\t{y}\t{z}\n' for a, (k, x, y, z) in sorted(seen.items())), encoding='utf-8')
    print('VANILLA_MODELS_PASS', sum(1 for v in seen.values() if v[0] == 'terrain'), 'terrain', sum(1 for v in seen.values() if v[0] == 'wire'), 'wire')


if __name__ == '__main__': main()
