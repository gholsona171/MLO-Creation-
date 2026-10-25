"""Tower City level 0: map files.
 - tc_lot.ytyp: archetypes tc_empty (shared empty stand-in), tc_lot_east, tc_lot_west (temporary ground slabs)
 - tc_lot.ymap: the two slab entities
 - edited copies of every vanilla ymap with something inside a lot (src/ymap, the copies the game loads):
     * entity inside a lot whose model we CUT (work/l0_cut_result.json 'cut')  -> kept (our cut .ydr replaces the model)
     * interior (MLO) entity inside a lot                                        -> removed (car park, Online offices);
       its name goes to work/l0_mlo_gone.json and l0_col.py ships its collision file (same name) empty
     * any other entity inside a lot (buildings, props, decals, block LODs)     -> archetype swapped to tc_empty
       (indices, parents and child counts stay intact, so the LOD tree is not broken)
     * an entity outside the lots inside an exterior clean-up zone (plan/ext_cuts.json 'ents', ext_plan.py) -> tc_empty
     * car generators inside a lot                                                -> removed
     * car generators a buyer's resource removes from a file we also ship        -> removed (plan/buyer_ymap_edits.json)
     * a LOD / SLOD1 entity (any ymap, the road ymaps included) whose every descendant was removed above   -> tc_empty
       (2026-10-24, Antonio: dark props floating in the sky from far away - the road ymaps' prop-combo LODs of the removed roofs'
       AC units / masts / dishes kept drawing: their HD children were gone, the LOD itself was never swapped). A LOD with only
       SOME descendants removed keeps its entity; its model is cut by the lot outline instead (l0_cut_lod.py, run by build_l0.sh;
       the list is printed as L0_MAPS_PARTIAL and written to work/l0_lod_partial.json).
   District-wide LOD ymaps (dt1_lod, hei_dt1_lod) are NOT touched at this level (their models are cut by l0_cut_lod.py).
Writes work/maps/*.xml, then compiles them with TequiBuild into work/maps/bin."""
import xml.etree.ElementTree as E, json, glob, os, copy, subprocess
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); OUT = T / 'work/maps'; OUT.mkdir(parents=True, exist_ok=True); (OUT / 'bin').mkdir(exist_ok=True)
TB = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work\bin\Release\net48\TequiBuild.exe'
POLYS = list(json.load(open(T / 'plan/lot_polys.json')).values())
CUT = set(json.load(open(T / 'work/l0_cut_result.json'))['cut'])
SLAB = json.load(open(T / 'work/slab/slab_info.json'))
SKIP = {'dt1_lod', 'hei_dt1_lod'}
import sys; sys.path.insert(0, str(T / 'work')); import ext_rules as ER    # (pure json + geometry here: bmesh is only used inside its Blender calls)
EXT_ENTS = ER.R.get('ents', [])
BUYER_CG = [q for v in json.load(open(T / 'plan/buyer_ymap_edits.json'))['cargen_remove'].values() for q in v]
def inside(x, y):
    for poly in POLYS:
        c = False; n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
        if c: return True
    return False
report = {}; mlo_gone = set()   # removed interiors of OUR blocks (dt1_11 / dt1_12) only: their collision is emptied too (l0_col.py).
                                 # Shared ones (the CEO offices, import garages) stand in other buildings too and keep theirs.
TREES = {}                       # every edited-or-not source ymap: name -> (tree, report); written after the LOD pass
for f in sorted(glob.glob(str(T / 'src/ymap/*.ymap.xml'))):
    name = os.path.basename(f)[:-9]
    if name in SKIP: continue
    tree = E.parse(f); root = tree.getroot(); ents = root.find('entities'); rep = {'swap': 0, 'remove': 0, 'keep_cut': 0, 'cargen': 0, 'lod_gone': 0, 'ext': 0}
    if ents is not None:
        for e in list(ents):
            p = e.find('position'); x, y, z = float(p.get('x')), float(p.get('y')), float(p.get('z'))
            if not inside(x, y):
                if e.get('type') != 'CMloInstanceDef' and any(r['z'][0] <= z <= r['z'][1] and ER.inside(r['poly'], x, y) for r in EXT_ENTS):
                    e.find('archetypeName').text = 'tc_empty'; rep['ext'] += 1          # plan/ext_cuts.json 'ents' (ext_plan.py)
                continue
            a = (e.findtext('archetypeName') or '').lower()
            if e.get('type') == 'CMloInstanceDef': e.set('tc_removed', '1'); rep['remove'] += 1; mlo_gone.add(a) if ('dt1_11' in a or 'dt1_12' in a) else None; continue
            if 'dt1_rd1' in name and e.findtext('lodLevel') in ('LODTYPES_DEPTH_LOD', 'LODTYPES_DEPTH_SLOD1', 'LODTYPES_DEPTH_SLOD2'): continue   # by the LOD pass below
            if a in CUT: rep['keep_cut'] += 1; continue
            e.find('archetypeName').text = 'tc_empty'; rep['swap'] += 1
    cg = root.find('carGenerators')
    if cg is not None:
        for c in list(cg):
            q = c.find('position')
            x, y = float(q.get('x')), float(q.get('y'))
            if inside(x, y) or any(abs(x - b[0]) < 0.5 and abs(y - b[1]) < 0.5 for b in BUYER_CG): cg.remove(c); rep['cargen'] += 1
    TREES[name] = (tree, rep)
# ---- the LOD pass: a LOD / SLOD1 whose every descendant is gone draws nothing of ours - it goes too ----
# parentIndex of an entity points into its ymap's <parent> ymap; a LOD's parent SLOD1 sits in the same (parent) ymap.
GONE = lambda e: e.get('tc_removed') == '1' or e.findtext('archetypeName') == 'tc_empty'
PARTIAL = []
for pname, (ptree, prep) in TREES.items():
    pents = ptree.getroot().find('entities')
    if pents is None: continue
    pl = list(pents); kids = {}                                  # parent index -> [child elements]
    for cname, (ctree, _) in TREES.items():
        if (ctree.getroot().findtext('parent') or '').lower() != pname: continue
        for e in ctree.getroot().find('entities') if ctree.getroot().find('entities') is not None else []:
            pi = int(e.find('parentIndex').get('value'))
            if pi >= 0: kids.setdefault(pi, []).append(e)
    for e in pl:                                                 # LODs whose parent is an SLOD1 of the same ymap
        pi = int(e.find('parentIndex').get('value'))
        if pi >= 0 and e.findtext('lodLevel') == 'LODTYPES_DEPTH_LOD' and pl[pi].findtext('lodLevel') == 'LODTYPES_DEPTH_SLOD1': kids.setdefault(pi, []).append(e)
    def leaves(i, seen=()):
        out = []
        for c in kids.get(i, []):
            j = pl.index(c) if c in pl else None
            if j is not None and j not in seen and kids.get(j): out += leaves(j, seen + (i,))
            else: out.append(c)
        return out
    for i, e in enumerate(pl):
        if e.findtext('lodLevel') not in ('LODTYPES_DEPTH_LOD', 'LODTYPES_DEPTH_SLOD1') or GONE(e): continue
        lv = leaves(i)
        if not lv: continue
        g = sum(1 for c in lv if GONE(c))
        if g == len(lv): e.find('archetypeName').text = 'tc_empty'; prep['lod_gone'] += 1
        elif g: PARTIAL.append({'ymap': pname, 'index': i, 'archetype': (e.findtext('archetypeName') or '').lower(), 'lodLevel': e.findtext('lodLevel'), 'gone': g, 'of': len(lv)})
for name, (tree, rep) in TREES.items():
    ents = tree.getroot().find('entities')
    if ents is not None:
        for e in list(ents):
            if e.get('tc_removed') == '1': ents.remove(e)
    if any(rep.values()):
        E.indent(tree); tree.write(OUT / f'{name}.ymap.xml', encoding='utf-8', xml_declaration=True); report[name] = rep
    else:
        for old in (OUT / f'{name}.ymap.xml', OUT / 'bin' / f'{name}.ymap'):
            if old.exists(): old.unlink()
json.dump(PARTIAL, open(T / 'work/l0_lod_partial.json', 'w'), indent=1)
# ---- tc_lot.ytyp ----
def arch(name, lo, hi, lod, hd, txd=''):
    cx, cy, cz = [(a + b) / 2 for a, b in zip(lo, hi)]; r = sum((b - a) ** 2 for a, b in zip(lo, hi)) ** .5 / 2
    return f'''  <Item type="CBaseArchetypeDef">
   <lodDist value="{lod}" />
   <flags value="0" />
   <specialAttribute value="0" />
   <bbMin x="{lo[0]:.4f}" y="{lo[1]:.4f}" z="{lo[2]:.4f}" />
   <bbMax x="{hi[0]:.4f}" y="{hi[1]:.4f}" z="{hi[2]:.4f}" />
   <bsCentre x="{cx:.4f}" y="{cy:.4f}" z="{cz:.4f}" />
   <bsRadius value="{r:.4f}" />
   <hdTextureDist value="{hd}" />
   <name>{name}</name>
   <textureDictionary>{txd}</textureDictionary>
   <clipDictionary />
   <drawableDictionary />
   <physicsDictionary />
   <assetType>ASSET_TYPE_DRAWABLE</assetType>
   <assetName>{name}</assetName>
   <extensions />
  </Item>'''
items = [arch('tc_empty', SLAB['tc_empty']['bb_lo'], SLAB['tc_empty']['bb_hi'], 3000, 5)]
import sidewalk_mat as SW                                # the slabs are Rockstar's sidewalk: his textures, bound from his road txd
for lot in ('east', 'west'): items.append(arch(f'tc_lot_{lot}', SLAB[lot]['bb_lo'], SLAB[lot]['bb_hi'], 1500, 150, SW.TXD))
(OUT / 'tc_lot.ytyp.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<CMapTypes>\n <extensions />\n <archetypes>\n' + '\n'.join(items) +
    '\n </archetypes>\n <name>tc_lot</name>\n <dependencies />\n <compositeEntityTypes />\n</CMapTypes>\n', encoding='utf-8')
# ---- tc_lot.ymap: template = an edited vanilla ymap, entities replaced ----
tmpl = E.parse(T / 'src/ymap/dt1_12_long_0.ymap.xml'); r = tmpl.getroot(); r.find('name').text = 'tc_lot'; r.find('parent').text = ''
ents = r.find('entities'); proto = copy.deepcopy(ents[0]); [ents.remove(e) for e in list(ents)]
for k in ('carGenerators', 'timeCycleModifiers', 'occludeModels', 'boxOccluders', 'physicsDictionaries', 'LODLightsSOA', 'DistantLODLightsSOA', 'instancedData'):
    el = r.find(k)
    if el is not None:
        for c in list(el): el.remove(c)
lo = [1e9] * 3; hi = [-1e9] * 3
for lot in ('east', 'west'):
    e = copy.deepcopy(proto); o = SLAB[lot]['origin']
    e.find('archetypeName').text = f'tc_lot_{lot}'; e.find('flags').set('value', '32'); e.find('guid').set('value', str(0x7C000000 + (1 if lot == 'east' else 2)))
    e.find('position').attrib.update(x=f'{o[0]:.4f}', y=f'{o[1]:.4f}', z=f'{o[2]:.4f}')
    e.find('rotation').attrib.update(x='0', y='0', z='0', w='1')
    e.find('scaleXY').set('value', '1'); e.find('scaleZ').set('value', '1'); e.find('parentIndex').set('value', '-1')
    e.find('lodDist').set('value', '1500'); e.find('childLodDist').set('value', '0'); e.find('lodLevel').text = 'LODTYPES_DEPTH_ORPHANHD'
    e.find('numChildren').set('value', '0'); e.find('priorityLevel').text = 'PRI_REQUIRED'
    ents.append(e)
    for i in range(3): lo[i] = min(lo[i], o[i] + SLAB[lot]['bb_lo'][i]); hi[i] = max(hi[i], o[i] + SLAB[lot]['bb_hi'][i])
for tag, a, b in (('streamingExtentsMin', lo, None), ('streamingExtentsMax', hi, None), ('entitiesExtentsMin', lo, None), ('entitiesExtentsMax', hi, None)):
    pad = -1500 if 'Min' in tag and 'streaming' in tag else (1500 if 'streaming' in tag else 0)
    r.find(tag).attrib.update(x=f'{a[0] + pad:.3f}', y=f'{a[1] + pad:.3f}', z=f'{a[2] + (pad if pad else 0):.3f}')
r.find('contentFlags').set('value', '1'); r.find('flags').set('value', '0')
E.indent(tmpl); tmpl.write(OUT / 'tc_lot.ymap.xml', encoding='utf-8', xml_declaration=True)
# ---- compile ----
bad = []
for x in sorted(OUT.glob('*.xml')):
    ext = '.ytyp' if x.name.endswith('.ytyp.xml') else '.ymap'
    dst = OUT / 'bin' / (x.name[:-len(ext + '.xml')] + ext)
    res = subprocess.run([TB, 'compile', str(x), str(dst)], capture_output=True, text=True)
    if not dst.exists(): bad.append((x.name, res.stdout[-300:] + res.stderr[-300:]))
json.dump(report, open(T / 'work/l0_maps_report.json', 'w'), indent=1)
json.dump(sorted(mlo_gone), open(T / 'work/l0_mlo_gone.json', 'w'), indent=1)
tot = {k: sum(v[k] for v in report.values()) for k in ('swap', 'remove', 'keep_cut', 'cargen', 'lod_gone', 'ext')}
print('L0_MAPS', len(report), 'ymaps edited', tot, 'compile failures', bad)
print('L0_MAPS_PARTIAL', sorted(set((p['archetype'], p['gone'], p['of']) for p in PARTIAL)))
