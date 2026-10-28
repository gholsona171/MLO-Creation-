"""Justice Center phase 1: the removed block's night lights (from Tower City work/l0_lodlights.py). GTA draws every building's far-view
lights from the distant-LOD-light maps (distlodlights_*.ymap, one copy per game update / DLC: base, apa_, hei_, vw_, m25_2_; the rig runs
the vw_ set) - with the block gone they would float in the empty sky over the lot.
Each light inside the lot outline is moved to z -1000: its index is kept, because the near-view LOD lights (lodlights_*.ymap) read their
positions from these lists by index - so both go dark and nothing else shifts. Kept: a light within LAMP_R m of a street lamp that still
stands outside the lot (its head can overhang the outline) - checked, and counted.
Sources: src/lodlights/*.ymap.xml (tools/lodlights_find.ps1: every distlodlights name with lights in the lot, the copy the game loads).
Out: work/lodlights/bin/*.ymap (only files with lights moved)."""
import json, glob, os, subprocess, shutil, csv, re, sys, math
import xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import jc_frame as F
from shapely.geometry import Polygon, Point
J = F.J; OUT = J / 'work/lodlights'; shutil.rmtree(OUT, ignore_errors=True); (OUT / 'bin').mkdir(parents=True)
TB = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work\bin\Release\net48\TequiBuild.exe'
LOT = Polygon([p[:2] for p in F.lot_w()]); LAMP_R = 3.0
rows = list(csv.DictReader(open(J / 'plan/near_entities_wide.tsv'), delimiter='\t')); YM = {r['ymap'] for r in rows}
LAMPS = [(float(r['x']), float(r['y'])) for r in rows if F.live_ymap(r['ymap'], YM) and re.search(r'streetlight|lamp|traffic', r['archetype'])
         and 'sc1_19' not in r['ymap'] and not LOT.contains(Point(float(r['x']), float(r['y'])))]
rep, bad, kept = {}, [], 0
for f in sorted(glob.glob(str(J / 'src/lodlights/*.ymap.xml'))):
    name = os.path.basename(f)[:-9]; tree = E.parse(f); n = 0
    for it in tree.getroot().find('DistantLODLightsSOA').find('position'):
        x, y, z = (float(it.find(k).get('value')) for k in 'xyz')
        if not LOT.contains(Point(x, y)): continue
        if any(math.hypot(x - a, y - b) <= LAMP_R for a, b in LAMPS): kept += 1; continue
        it.find('z').set('value', '-1000.0'); n += 1
    rep[name] = n
    if not n: continue
    E.indent(tree, space=' '); tree.write(OUT / f'{name}.ymap.xml', encoding='UTF-8', xml_declaration=True)
    r = subprocess.run([TB, 'compile', str(OUT / f'{name}.ymap.xml'), str(OUT / 'bin' / f'{name}.ymap')], capture_output=True, text=True)
    if not (OUT / 'bin' / f'{name}.ymap').exists(): bad.append((name, (r.stdout + r.stderr)[-300:]))
json.dump({'moved': rep, 'kept_by_street_lamps': kept}, open(J / 'work/p1_lodlights_report.json', 'w'), indent=1)
print('P1_LODLIGHTS moved', sum(rep.values()), 'in', sum(1 for v in rep.values() if v), 'maps', rep, '| kept by a street lamp:', kept, '| compile failures:', bad)
if bad: raise SystemExit(1)
