"""Justice Center phase 1: map files (from Tower City work/l0_maps.py). Rebuilds work/maps from the game's own ymaps every run.
 - jc_lot.ytyp: jc_empty (the shared empty stand-in) and jc_lot (the lot slab: Rockstar's sidewalk, his road txd sc1_rd_road)
 - jc_lot.ymap: the slab entity
 - edited copies of every vanilla ymap with something of the block in it (src/ymap = the copy the game loads, every prefix: lr_ is live
   on the rig, hei_ and base are edited the same way so the block stays gone whatever a server's IPL state):
     * every entity of the block's own ymaps (sc1_19*: the courts tower, the low block, the library, the sheriff station, the car park,
       the plaza, the monument, their props, LODs and SLOD1s)            -> archetype swapped to jc_empty (indices / parents intact)
     * a road-ymap HD entity whose origin is inside the lot (plan/lot_poly.json) and more than BAND m in from its edge -> jc_empty,
       except the street wiring KEEP_WIRES (its bounds centre is inside, its spans hang between the kept poles along Davis Ave and
       Macdonald St: traced with work/tools/wire_spans.py, every span ends on a standing street pole)
     * a road-ymap entity in the BAND (the 4 m strip inside the edge): kept (brief), except posters (sc1_props_flyers*: they hung on
       the old walls); one that stood on the old raised beds and would float over the slab is set down onto it (jc_frame.slab_z)
     * car generators inside the lot                                      -> removed (area_clear.lua switches them off too)
     * a LOD / SLOD1 entity (any ymap) whose every descendant is gone      -> jc_empty; one with only some gone keeps its entity and
       its model is cut by the lot (p1_cut_lod.py; listed in work/p1_lod_partial.json)
   SLOD2 / SLOD3 entities (sc1_lod*) are never swapped: their models are cut by the lot (p1_cut_lod.py).
PHASE 2 (when work/p2/out/p2_layout.json exists - the complex is built): p2/p2_maps.py hooks the new buildings into the block's own LOD
tree in every prefix's sc1_19 + sc1_19_strm_0 (SLOD1 / emissive SLOD re-used, LODs + HDs appended), writes jc_ext.ytyp and jc_site.ymap,
and the slab's lodDist comes from that chain (p2_maps.SLAB_LOD); kept band props are seated on OUR ground (the lawn), not the slab.
Writes work/maps/*.xml, compiles them with TequiBuild into work/maps/bin, report work/p1_maps_report.json."""
import xml.etree.ElementTree as E, json, glob, os, copy, subprocess, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import jc_frame as F
P2_ON = (Path(__file__).parent / 'p2/out/p2_layout.json').exists()
if P2_ON:
    sys.path.insert(0, str(Path(__file__).parent / 'p2')); import p2_maps as P2M, p2_site_plan as SP
def ground_z(x, y):
    """where a kept prop stands: our own ground (phase 2: the lawn / podium) where there is one, else the slab."""
    zs = F.slab_z(x, y)
    if not P2_ON: return zs
    u, v = F.L(x, y); return SP.ground_uv(u, v, zs)
J = F.J; OUT = J / 'work/maps'
shutil.rmtree(OUT, ignore_errors=True); (OUT / 'bin').mkdir(parents=True)
TB = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work\bin\Release\net48\TequiBuild.exe'
from shapely.geometry import Polygon, Point
LOT = Polygon([p[:2] for p in F.lot_w()])
BAND = 4.0
KEEP_WIRES = {'sc1_rd_wireset_21', 'sc1_rd_cablemesh760288_thvy001'}
POSTER = ('sc1_props_flyers',)
SEAT_TOL = 0.05
SLAB = json.load(open(J / 'work/slab/slab_info.json'))
def block_ymap(name): return 'sc1_19' in name
report = {}; TREES = {}; seated = []; removed = {'block': 0, 'road': 0, 'poster': 0, 'cargen': 0, 'lod_gone': 0}; kept_band = []
for f in sorted(glob.glob(str(J / 'src/ymap/*.ymap.xml'))):
    name = os.path.basename(f)[:-9]
    tree = E.parse(f); root = tree.getroot(); ents = root.find('entities')
    rep = {'swap_block': 0, 'swap_road': 0, 'poster': 0, 'seated': 0, 'cargen': 0, 'lod_gone': 0}
    if ents is not None:
        for e in list(ents):
            a = (e.findtext('archetypeName') or '').lower(); lod = e.findtext('lodLevel')
            if block_ymap(name):
                e.find('archetypeName').text = 'jc_empty'; rep['swap_block'] += 1; continue
            p = e.find('position'); x, y, z = float(p.get('x')), float(p.get('y')), float(p.get('z'))
            if lod not in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD') or not LOT.contains(Point(x, y)): continue
            if a.startswith(POSTER): e.find('archetypeName').text = 'jc_empty'; rep['poster'] += 1; continue
            if LOT.exterior.distance(Point(x, y)) > BAND:
                if a in KEEP_WIRES: continue
                e.find('archetypeName').text = 'jc_empty'; rep['swap_road'] += 1; continue
            zs = ground_z(x, y)                                     # in the band: kept; set down onto the ground if it would float
            if name.startswith('lr_'): kept_band.append([a, round(x, 2), round(y, 2), round(z, 2), round(zs, 2)])
            if abs(z - zs) > SEAT_TOL:
                p.set('z', '%.5f' % zs); rep['seated'] += 1
                if name.startswith('lr_'): seated.append([a, round(z, 2), round(zs, 2)])
    cg = root.find('carGenerators')
    if cg is not None:
        for c in list(cg):
            q = c.find('position')
            if LOT.contains(Point(float(q.get('x')), float(q.get('y')))): cg.remove(c); rep['cargen'] += 1
    TREES[name] = (tree, rep)
# ---- the LOD pass (Tower City): a LOD / SLOD1 whose every descendant is gone draws nothing of ours - it goes too ----
GONE = lambda e: e.findtext('archetypeName') == 'jc_empty'
PARTIAL = []
for pname, (ptree, prep) in TREES.items():
    pents = ptree.getroot().find('entities')
    if pents is None: continue
    pl = list(pents); kids = {}
    for cname, (ctree, _) in TREES.items():
        if (ctree.getroot().findtext('parent') or '').lower() != pname: continue
        ce = ctree.getroot().find('entities')
        for e in (ce if ce is not None else []):
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
        if g == len(lv): e.find('archetypeName').text = 'jc_empty'; prep['lod_gone'] += 1
        elif g: PARTIAL.append({'ymap': pname, 'index': i, 'archetype': (e.findtext('archetypeName') or '').lower(), 'lodLevel': e.findtext('lodLevel'), 'gone': g, 'of': len(lv)})
P2_ADDED = {}
if P2_ON:                                                      # phase 2: the new complex in the block's LOD tree (p2/p2_maps.py)
    def src_names(ym): return [(e.findtext('archetypeName') or '').lower() for e in E.parse(J / f'src/ymap/{ym}.ymap.xml').getroot().find('entities')]
    P2_ADDED = P2M.hook(TREES, src_names)
    for k, n in P2_ADDED.items(): TREES[k][1]['p2_added'] = n
    P2M.write_ytyp(OUT)
for name, (tree, rep) in TREES.items():
    if any(rep.values()):
        E.indent(tree); tree.write(OUT / f'{name}.ymap.xml', encoding='utf-8', xml_declaration=True); report[name] = rep
json.dump(PARTIAL, open(J / 'work/p1_lod_partial.json', 'w'), indent=1)
# ---- jc_lot.ytyp ----
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
LOT_LOD = P2M.SLAB_LOD if P2_ON else 15000       # phase 1: the cut SLOD2 (1500 m) / SLOD3 (15000 m) no longer drew the block: the slab must
items = [arch('jc_empty', SLAB['jc_empty']['bb_lo'], SLAB['jc_empty']['bb_hi'], 3000, 5),   # (or the lot is a hole from far away)
         arch('jc_lot', SLAB['lot']['bb_lo'], SLAB['lot']['bb_hi'], LOT_LOD, 150, 'sc1_rd_road')]
(OUT / 'jc_lot.ytyp.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<CMapTypes>\n <extensions />\n <archetypes>\n' + '\n'.join(items) +
    '\n </archetypes>\n <name>jc_lot</name>\n <dependencies />\n <compositeEntityTypes />\n</CMapTypes>\n', encoding='utf-8')
# ---- jc_lot.ymap: template = a vanilla block ymap, entities replaced ----
tmpl = E.parse(J / 'src/ymap/lr_sc1_19_long_0.ymap.xml'); r = tmpl.getroot(); r.find('name').text = 'jc_lot'; r.find('parent').text = ''
ents = r.find('entities'); proto = copy.deepcopy(ents[0]); [ents.remove(e) for e in list(ents)]
for k in ('carGenerators', 'timeCycleModifiers', 'occludeModels', 'boxOccluders', 'physicsDictionaries', 'LODLightsSOA', 'DistantLODLightsSOA', 'instancedData'):
    el = r.find(k)
    if el is not None:
        for c in list(el): el.remove(c)
e = copy.deepcopy(proto); o = SLAB['lot']['origin']
e.find('archetypeName').text = 'jc_lot'; e.find('flags').set('value', '32'); e.find('guid').set('value', str(0x6A430001))
e.find('position').attrib.update(x=f'{o[0]:.4f}', y=f'{o[1]:.4f}', z=f'{o[2]:.4f}')
e.find('rotation').attrib.update(x='0', y='0', z='0', w='1')
e.find('scaleXY').set('value', '1'); e.find('scaleZ').set('value', '1'); e.find('parentIndex').set('value', '-1')
e.find('lodDist').set('value', str(LOT_LOD)); e.find('childLodDist').set('value', '0'); e.find('lodLevel').text = 'LODTYPES_DEPTH_ORPHANHD'
e.find('numChildren').set('value', '0'); e.find('priorityLevel').text = 'PRI_REQUIRED'
ents.append(e)
lo = [o[i] + SLAB['lot']['bb_lo'][i] for i in range(3)]; hi = [o[i] + SLAB['lot']['bb_hi'][i] for i in range(3)]
for tag, a in (('streamingExtentsMin', lo), ('streamingExtentsMax', hi), ('entitiesExtentsMin', lo), ('entitiesExtentsMax', hi)):
    pad = (-LOT_LOD if 'Min' in tag else LOT_LOD) if 'streaming' in tag else 0
    r.find(tag).attrib.update(x=f'{a[0] + pad:.3f}', y=f'{a[1] + pad:.3f}', z=f'{a[2] + pad:.3f}')
r.find('contentFlags').set('value', '1'); r.find('flags').set('value', '0')
E.indent(tmpl); tmpl.write(OUT / 'jc_lot.ymap.xml', encoding='utf-8', xml_declaration=True)
if P2_ON: print('P2_SITE_YMAP', P2M.site_ymap(J / 'src/ymap/lr_sc1_19_long_0.ymap.xml', OUT), 'entities', '| hooked', P2_ADDED)
# ---- compile ----
bad = []
for x in sorted(OUT.glob('*.xml')):
    ext = '.ytyp' if x.name.endswith('.ytyp.xml') else '.ymap'
    dst = OUT / 'bin' / (x.name[:-len(ext + '.xml')] + ext)
    res = subprocess.run([TB, 'compile', str(x), str(dst)], capture_output=True, text=True)
    if not dst.exists(): bad.append((x.name, res.stdout[-300:] + res.stderr[-300:]))
tot = {k: sum(v.get(k, 0) for v in report.values()) for k in ('swap_block', 'swap_road', 'poster', 'seated', 'cargen', 'lod_gone')}
live = {k: v for k, v in report.items() if k.startswith('lr_')}
json.dump({'per_ymap': report, 'total': tot, 'live_lr': {k: sum(v.get(k, 0) for v in live.values()) for k in tot}, 'p2_added': P2_ADDED, 'seated_lr': seated, 'kept_band_lr': kept_band,
           'partial': PARTIAL}, open(J / 'work/p1_maps_report.json', 'w'), indent=1)
print('P1_MAPS', len(report), 'ymaps edited, all prefixes', tot, '| live lr_ copies', {k: sum(v.get(k, 0) for v in live.values()) for k in tot}, '| compile failures', bad)
print('P1_MAPS_PARTIAL', sorted(set((p['archetype'], p['gone'], p['of']) for p in PARTIAL)))
if bad: raise SystemExit(1)
