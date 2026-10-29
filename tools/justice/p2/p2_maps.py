"""Justice Center phase 2: the map metadata of the new complex (called by work/p1_maps.py, the one writer of every ymap it ships).
The complex plugs into Rockstar's own LOD tree of the block (every prefix: lr_ live, hei_ / base the same), so it hands over between
levels exactly as the vanilla buildings did:
   SLOD3 sc1_lod_slod4 (15000, model rebuilt)  ->  SLOD2 sc1_lod_19 (1500 / child 750, model rebuilt, lr_sc1_lod untouched)
     ->  SLOD1 entity 'sc1_19_slod1' of <p>sc1_19 = jc_slod1 (lodDist 750, child 500)
       ->  the block's own LOD slots under it = jc_<b>_lod (500, child = the HD's)  ->  HD jc_<b> appended to <p>sc1_19 itself
           (tower 350, others 300): an HD in the child _strm_0 ymap never swapped with its LOD on the rig (both drew).
   night:  sc1_lod_emissive (SLOD2)  ->  entity 'sc1_19_sc1_emissive_slod' = jc_emi_slod (8000, child 750)
             ->  its own LOD slot = jc_emi_lod (750, child 350)  ->  HD jc_<b>_emi (as their building)
   orphans in jc_site.ymap: jc_site (podium, lawn, steps, Portal: 750, the same as the slab), jc_core (300), the site's props.
   The lot slab (jc_lot.ymap, p1_maps) takes lodDist SLAB_LOD = 750: from there on the rebuilt SLOD2 draws the ground plates.
jc_ext.ytyp holds every archetype (plain drawables, DLC_ITYP_REQUEST in the fxmanifest)."""
import json, math, copy
import xml.etree.ElementTree as E
from pathlib import Path
P2 = Path(__file__).resolve().parent; J = P2.parent.parent
HD_LOD = {'jc_tower': 350, 'jc_tower_emi': 350}                     # others 300
LOD_LOD, SLOD1_LOD, EMI_LOD = 500, 750, 750
SLAB_LOD = 750; SITE_LOD = 750; CORE_LOD = 300
BLD = ['tower', 'police', 'jail1', 'jail2', 'atrium']
def _load():
    L = json.load(open(P2 / 'out/p2_layout.json')); LL = json.load(open(P2 / 'out_lod/p2_lod_layout.json'))
    return L, LL
def world(L, c):
    """lot-frame centre -> world position (the lot frame of jc_frame: origin + heading)."""
    h = math.radians(L['heading']); x0, y0, _ = L['origin']
    return (x0 + c[0] * math.cos(h) - c[1] * math.sin(h), y0 + c[0] * math.sin(h) + c[1] * math.cos(h), c[2])
def _rot(L):
    h = math.radians(L['heading']); return (0.0, 0.0, -math.sin(h / 2), math.cos(h / 2))     # a plain entity: the conjugate (doc 09)
def arch_items(L, LL):
    out = []
    def arch(name, lo, hi, lod):
        cx, cy, cz = [(a + b) / 2 for a, b in zip(lo, hi)]; r = math.dist(lo, hi) / 2
        out.append(f'''  <Item type="CBaseArchetypeDef">
   <lodDist value="{lod}" />
   <flags value="0" />
   <specialAttribute value="0" />
   <bbMin x="{lo[0]:.4f}" y="{lo[1]:.4f}" z="{lo[2]:.4f}" />
   <bbMax x="{hi[0]:.4f}" y="{hi[1]:.4f}" z="{hi[2]:.4f}" />
   <bsCentre x="{cx:.4f}" y="{cy:.4f}" z="{cz:.4f}" />
   <bsRadius value="{r:.4f}" />
   <hdTextureDist value="{min(lod, 300)}" />
   <name>{name}</name>
   <textureDictionary>{'sc1_rd_road' if name == 'jc_site' else ''}</textureDictionary>
   <clipDictionary />
   <drawableDictionary />
   <physicsDictionary />
   <assetType>ASSET_TYPE_DRAWABLE</assetType>
   <assetName>{name}</assetName>
   <extensions />
  </Item>''')
    for n, d in L['drawables'].items(): arch(n, d['bb_lo'], d['bb_hi'], lod_of(n))
    for n, d in LL.items(): arch(n, d['bb_lo'], d['bb_hi'], lod_of(n))
    return out
def lod_of(n):
    if n in HD_LOD: return HD_LOD[n]
    if n == 'jc_site': return SITE_LOD
    if n == 'jc_core': return CORE_LOD
    if n == 'jc_slod1': return SLOD1_LOD
    if n == 'jc_emi_slod': return 8000
    if n == 'jc_emi_lod': return EMI_LOD
    if n.endswith('_lod'): return LOD_LOD
    return 300
def write_ytyp(out):
    L, LL = _load()
    (out / 'jc_ext.ytyp.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<CMapTypes>\n <extensions />\n <archetypes>\n' + '\n'.join(arch_items(L, LL)) +
        '\n </archetypes>\n <name>jc_ext</name>\n <dependencies />\n <compositeEntityTypes />\n</CMapTypes>\n', encoding='utf-8')
def _ent(proto, arch, pos, rot, lod, child, level, parent, flags, nchild=0):
    e = copy.deepcopy(proto)
    e.find('archetypeName').text = arch; e.find('flags').set('value', str(flags))
    e.find('position').attrib.update(x=f'{pos[0]:.4f}', y=f'{pos[1]:.4f}', z=f'{pos[2]:.4f}')
    e.find('rotation').attrib.update(x=f'{rot[0]:.7f}', y=f'{rot[1]:.7f}', z=f'{rot[2]:.7f}', w=f'{rot[3]:.7f}')
    e.find('scaleXY').set('value', '1'); e.find('scaleZ').set('value', '1')
    e.find('parentIndex').set('value', str(parent)); e.find('lodDist').set('value', str(lod)); e.find('childLodDist').set('value', str(child))
    e.find('lodLevel').text = level; e.find('numChildren').set('value', str(nchild)); e.find('priorityLevel').text = 'PRI_REQUIRED'
    import hashlib; e.find('guid').set('value', str(int(hashlib.md5(repr((arch, level, pos)).encode()).hexdigest()[:8], 16))); return e
def _grow(root, pts, pad):
    for tag, f in (('entitiesExtentsMin', min), ('entitiesExtentsMax', max), ('streamingExtentsMin', min), ('streamingExtentsMax', max)):
        el = root.find(tag); a = [float(el.get(k)) for k in 'xyz']; p_ = -pad if 'Min' in tag else pad
        pp = pad if 'streaming' in tag else 0.0; p_ = -pp if 'Min' in tag else pp
        for q in pts: a = [f(a[i], q[i] + p_) for i in range(3)]
        el.attrib.update(x=f'{a[0]:.3f}', y=f'{a[1]:.3f}', z=f'{a[2]:.3f}')
def hook(TREES, src_names):
    """TREES: p1_maps' {ymap name: (tree, report)}; src_names(ymap) -> the vanilla archetype names by index (before the swaps).
    Every prefix's sc1_19 parent + strm_0 get the chain. Returns {ymap: entities added}."""
    L, LL = _load(); rot = _rot(L); done = {}
    for p in ('lr_', 'hei_', ''):
        pn, sn = p + 'sc1_19', p + 'sc1_19_strm_0'
        if pn not in TREES or sn not in TREES: continue
        proot = TREES[pn][0].getroot(); pents = proot.find('entities'); pl = list(pents); orig = src_names(pn)
        i_slod = orig.index('sc1_19_slod1'); i_emi = orig.index('sc1_19_sc1_emissive_slod'); proto = pl[i_slod]
        s = pl[i_slod]; c = LL['jc_slod1']['centre']
        s.find('archetypeName').text = 'jc_slod1'; s.find('position').attrib.update(**dict(zip('xyz', [f'{v:.4f}' for v in world(L, c)])))
        s.find('rotation').attrib.update(x=f'{rot[0]:.7f}', y=f'{rot[1]:.7f}', z=f'{rot[2]:.7f}', w=f'{rot[3]:.7f}')
        s.find('lodDist').set('value', str(SLOD1_LOD)); s.find('childLodDist').set('value', str(LOD_LOD))
        s.find('numChildren').set('value', str(len(BLD)))
        m = pl[i_emi]; c = LL['jc_emi_slod']['centre']
        m.find('archetypeName').text = 'jc_emi_slod'; m.find('position').attrib.update(**dict(zip('xyz', [f'{v:.4f}' for v in world(L, c)])))
        m.find('rotation').attrib.update(x=f'{rot[0]:.7f}', y=f'{rot[1]:.7f}', z=f'{rot[2]:.7f}', w=f'{rot[3]:.7f}')
        m.find('childLodDist').set('value', str(EMI_LOD)); m.find('numChildren').set('value', '1')
        # OUR LODs take the block's own LOD SLOTS (indices the game already knows): HD -> LOD links into entities APPENDED past the
        # vanilla count never formed on the rig (the LOD kept drawing over its HD: z-fighting walls, a flat roof - 2026-10-28). Every
        # other (empty) LOD under the two slots is cut loose, and every old (empty) child of a re-used slot is made an orphan: a parent
        # swaps to its children only when ALL of them are in range.
        lods = [i for i, e in enumerate(pl) if e.findtext('lodLevel') == 'LODTYPES_DEPTH_LOD' and int(e.find('parentIndex').get('value')) == i_slod]
        elods = [i for i, e in enumerate(pl) if e.findtext('lodLevel') == 'LODTYPES_DEPTH_LOD' and int(e.find('parentIndex').get('value')) == i_emi]
        assert len(lods) >= len(BLD) and elods, ('not enough LOD slots in', pn, len(lods), len(elods))
        idx = {k: lods[n] for n, k in enumerate(BLD)}; idx['emi'] = elods[0]; used = set(idx.values())
        for i, e in enumerate(pl):
            if int(e.find('parentIndex').get('value')) in (i_slod, i_emi) and i not in used: e.find('parentIndex').set('value', '-1')
        for cn, (ct, _) in TREES.items():
            if (ct.getroot().findtext('parent') or '').lower() != pn: continue
            for e in ct.getroot().find('entities'):
                if int(e.find('parentIndex').get('value')) in used and e.findtext('archetypeName') == 'jc_empty':
                    e.find('parentIndex').set('value', '-1'); e.find('lodLevel').text = 'LODTYPES_DEPTH_ORPHANHD'
        pts = []
        hd = {k: [n for n in (f'jc_{k}',) + (('jc_bridges',) if k == 'jail2' else ()) if n in L['drawables']] for k in BLD}
        emis = [n for n in L['drawables'] if n.endswith('_emi')]
        def slot(i, n, child, par, nch, flags):
            e = pl[i]; c = world(L, LL[n]['centre']); pts.append(c)
            e.find('archetypeName').text = n; e.find('position').attrib.update(**dict(zip('xyz', [f'{v:.4f}' for v in c])))
            e.find('rotation').attrib.update(x=f'{rot[0]:.7f}', y=f'{rot[1]:.7f}', z=f'{rot[2]:.7f}', w=f'{rot[3]:.7f}')
            e.find('lodDist').set('value', str(lod_of(n))); e.find('childLodDist').set('value', str(child)); e.find('parentIndex').set('value', str(par))
            e.find('numChildren').set('value', str(nch)); e.find('flags').set('value', str(flags))
        for k in BLD: slot(idx[k], f'jc_{k}_lod', max(lod_of(x) for x in hd[k]), i_slod, len(hd[k]), 1572864)
        slot(idx['emi'], 'jc_emi_lod', max(lod_of(x) for x in emis), i_emi, len(emis), 0)
        _grow(proot, pts, 1000.0)
        # the HDs go into the SAME ymap as their LODs: an HD in the child _strm_0 ymap never swapped with its LOD on the rig (both drew:
        # z-fighting walls, the LOD's flat roof over the HD's) while SLOD1 -> LOD inside one ymap swapped fine (2026-10-28)
        spts = []
        for k in BLD:
            for n in hd[k]:
                c = world(L, L['drawables'][n]['centre']); spts.append(c)
                pents.append(_ent(proto, n, c, rot, lod_of(n), 0, 'LODTYPES_DEPTH_HD', idx[k], 1572864))
        for n in emis:
            c = world(L, L['drawables'][n]['centre']); spts.append(c)
            pents.append(_ent(proto, n, c, rot, lod_of(n), 0, 'LODTYPES_DEPTH_HD', idx['emi'], 8))
        done[pn] = 'slots %s + %d HD' % (sorted(used), len(spts))
    return done
def site_ymap(template, out):
    """jc_site.ymap: the orphans (jc_site, jc_core) + the site's vanilla props (bollards, benches, flag poles, trees)."""
    L, LL = _load(); rot = _rot(L)
    t = E.parse(template); r = t.getroot(); r.find('name').text = 'jc_site'; r.find('parent').text = ''
    ents = r.find('entities'); proto = copy.deepcopy(ents[0]); [ents.remove(e) for e in list(ents)]
    for k in ('carGenerators', 'timeCycleModifiers', 'occludeModels', 'boxOccluders', 'physicsDictionaries', 'LODLightsSOA', 'DistantLODLightsSOA', 'instancedData'):
        el = r.find(k)
        if el is not None:
            for c in list(el): el.remove(c)
    pts = []
    for n in ('jc_site', 'jc_core'):
        if n not in L['drawables']: continue
        c = world(L, L['drawables'][n]['centre']); pts.append(c)
        ents.append(_ent(proto, n, c, rot, lod_of(n), 0, 'LODTYPES_DEPTH_ORPHANHD', -1, 1572864))
    for p in L['props']:
        h = math.radians(p['heading']); q = (0.0, 0.0, -math.sin(h / 2), math.cos(h / 2)); pts.append(p['pos'])
        ents.append(_ent(proto, p['model'], p['pos'], q, 150, 0, 'LODTYPES_DEPTH_ORPHANHD', -1, 1572864))
    for tag, f, pad in (('entitiesExtentsMin', min, -100.0), ('entitiesExtentsMax', max, 100.0), ('streamingExtentsMin', min, -SITE_LOD), ('streamingExtentsMax', max, SITE_LOD)):
        a = [f(q[i] for q in pts) + pad for i in range(3)]; r.find(tag).attrib.update(x=f'{a[0]:.3f}', y=f'{a[1]:.3f}', z=f'{a[2]:.3f}')
    r.find('contentFlags').set('value', '1'); r.find('flags').set('value', '0')
    E.indent(t); t.write(out / 'jc_site.ymap.xml', encoding='utf-8', xml_declaration=True)
    return len(pts)
