"""Clear the Block Boyz site (site_plan.SITE): every vanilla HD entity standing on the site or within site_plan.CLEAR_MARGIN of it
goes - bushes, trees, rocks, junk, fences, props, the hobo camp at the junction, the fruit stand if it is inside - except
  * the drawn ground (site_plan.TERRAIN_RX: land / beach / trail ... models): terrain.py lowers it under the new grade;
  * the merged wire meshes (site_plan.WIRE_RX): wires.py cuts them;
  * road models (anything named ...road...): the site keeps 3 m off every road;
  * utility poles (site_plan.POLE_RX) that stay: only site_plan.POLES_GONE (and anything within POLE_GONE_R of one: its insulators,
    its lamp) go.
Method (Tower City l0_maps.py, Graveyard site_clear.py): a cleared entity's archetype is swapped to our empty model bb_empty, so
indices, parents and child counts stay intact and the LOD tree is not broken. A distance model (LOD) is swapped only when ALL its
children (in every child map of that LOD map) are cleared; the rest is lod_cut.py's job. Car generators on the site go. Every
variant of a touched map is edited (base / patchday, hei_ heist, lr_ lowrider: which one the game runs depends on the server's IPL
state); each keeps its vanilla name so it replaces the game's copy.
Inputs ../vanilla/*.ymap.xml (vanilla_extract.ps1). Outputs ../site/xml/*.ymap.xml (wiped first) compiled to ../site/clear/*.ymap,
../site/clear/bb_empty.ydr, ../site/site_clear_report.json.
Run: py -3 site_clear.py"""
import json, re, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import site_plan as SP

M = T.parent; VAN = M / 'vanilla'; XO = M / 'site' / 'xml_clear'; OUT = M / 'site' / 'clear'
TB = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work\bin\Release\net48\TequiBuild.exe'
EMPTY_YDR = Path(r'C:\Users\anton\Documents\Codex\TowerCity\resource\tower_city\stream\tc_empty.ydr')   # a drawable with nothing in it
EMPTY = 'bb_empty'
HD = ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD')
ROAD = re.compile(r'road', re.I)
VARIANT = re.compile(r'^(lr_|hei_)')


def pos(e): p = e.find('position'); return float(p.get('x')), float(p.get('y'))
def base(name): return VARIANT.sub('', name)


def keep_reason(a, x, y):
    """why an entity on the site stays (None: it goes)."""
    if SP.TERRAIN_RX.search(a): return 'terrain'
    if SP.WIRE_RX.search(a): return 'wire'
    if ROAD.search(a): return 'road'
    if SP.POLE_RX.search(a) and not SP.pole_gone(x, y): return 'pole'
    return None


def clears(e):
    a = e.findtext('archetypeName') or ''
    if e.findtext('lodLevel') not in HD: return False
    x, y = pos(e)
    if SP.pole_gone(x, y) and a != EMPTY: return True                        # a removed pole and everything on it
    return SP.near_site(x, y) and keep_reason(a, x, y) is None


def entity_maps():
    """every extracted map with entities, by base name -> its variants present."""
    groups = {}
    for f in sorted(VAN.glob('*.ymap.xml')):
        r = ET.parse(f).getroot(); es = r.find('entities')
        if es is None or not len(es): continue
        groups.setdefault(base(f.name[:-9]), []).append(f.name[:-9])
    return groups


def main():
    shutil.rmtree(XO, ignore_errors=True); XO.mkdir(parents=True); shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
    groups = entity_maps(); rep = {}; trees = {}
    touched = sorted(b for b, vs in groups.items() if any(touches(VAN / f'{v}.ymap.xml') for v in vs))
    cleared_children = {}                                                     # (parent map, parent index) -> children cleared
    for b in touched:
        for v in groups[b]:
            t = ET.parse(VAN / f'{v}.ymap.xml'); r = t.getroot(); parent = r.findtext('parent') or ''
            n = 0; kinds = {}
            for e in r.find('entities'):
                if not clears(e): continue
                a = e.findtext('archetypeName'); pi = int(e.find('parentIndex').get('value'))
                if pi >= 0: cleared_children[(parent, pi)] = cleared_children.get((parent, pi), 0) + 1
                kinds[a] = kinds.get(a, 0) + 1
                e.find('archetypeName').text = EMPTY; n += 1
            cg = r.find('carGenerators'); ncg = 0
            for g in list(cg if cg is not None else []):
                p = g.find('position')
                if p is not None and SP.near_site(float(p.get('x')), float(p.get('y'))): cg.remove(g); ncg += 1
            trees[v] = t; rep[v] = {'swapped': n, 'cargens_removed': ncg, 'archetypes': kinds}
    # the distance models: a LOD whose children are ALL cleared is swapped too (every variant's own LOD map)
    for (parent, pi), k in sorted(cleared_children.items()):
        if not parent: continue
        if parent not in trees:
            if not (VAN / f'{parent}.ymap.xml').exists(): raise SystemExit(f'LOD map {parent} not extracted')
            trees[parent] = ET.parse(VAN / f'{parent}.ymap.xml'); rep.setdefault(parent, {'lods_swapped': 0, 'lods_partly_cleared_kept': 0, 'lods': []})
        pe = list(trees[parent].getroot().find('entities'))[pi]
        if int(pe.find('numChildren').get('value')) == k:
            rep[parent].setdefault('lods', []).append(pe.findtext('archetypeName'))
            pe.find('archetypeName').text = EMPTY; rep[parent]['lods_swapped'] = rep[parent].get('lods_swapped', 0) + 1
        else: rep[parent]['lods_partly_cleared_kept'] = rep[parent].get('lods_partly_cleared_kept', 0) + 1
    unchanged = [v for v, rr in rep.items() if not rr.get('swapped') and not rr.get('cargens_removed') and not rr.get('lods_swapped')]
    for v in unchanged: trees.pop(v); rep.pop(v)                             # (a LOD map with nothing swapped is not shipped)
    bad = []
    for v, t in sorted(trees.items()):
        x = XO / f'{v}.ymap.xml'; t.write(x, encoding='UTF-8', xml_declaration=True)
        out = OUT / f'{v}.ymap'; rr = subprocess.run([TB, 'compile', str(x), str(out)], capture_output=True, text=True)
        if not out.exists(): bad.append((v, (rr.stdout + rr.stderr)[-300:]))
    assert not bad, bad
    shutil.copy2(EMPTY_YDR, OUT / f'{EMPTY}.ydr')
    json.dump(rep, open(M / 'site' / 'site_clear_report.json', 'w'), indent=1)
    tot = sum(r.get('swapped', 0) for r in rep.values())
    print('SITE_CLEAR_PASS maps', len(trees), 'entities swapped', tot, 'lods swapped', sum(r.get('lods_swapped', 0) for r in rep.values()),
          'cargens removed', sum(r.get('cargens_removed', 0) for r in rep.values()))


def touches(f):
    """the map has something to clear: an entity, or a car generator on the site."""
    r = ET.parse(f).getroot(); cg = r.find('carGenerators')
    return (any(clears(e) for e in r.find('entities')) or
            any(g.find('position') is not None and SP.near_site(float(g.find('position').get('x')), float(g.find('position').get('y')))
                for g in (cg if cg is not None else [])))


if __name__ == '__main__': main()
