"""Tower City: metadata of the exterior clean-up's pieces, from work/extfix/ext_layout.json (ext_build.py):
  tc_ext_fix.ytyp / tc_ext_fix.ymap   the Power St plaza paving (tc_ext_fix, placed at the tower lot origin like every tower exterior)
                                      + the plaza's vanilla street props as plain map entities: bollards on the old drives' mouths
                                      (prop_bollard_04, as at the parking doors) and benches (prop_bench_05, Rockstar's downtown bench)
Its collision tc_ext_fix_col.ybn is a world-space static bound (streamed like the lot slab's). Compiled into work/extfix/bin."""
import json, math, copy
import xml.etree.ElementTree as ET
import mlo_meta as MM
OUT = MM.T / 'work/extfix'
L = json.load(open(OUT / 'ext_layout.json'))
ORG = (*L['origin'], 0.0); HEAD = L['heading']; D = L['drawables']; EXT = L['ext']
MM.plain_ytyp('tc_ext_fix', EXT, D, 600, 300, OUT)
MM.ymap('tc_ext_fix', 'ent', [(n, D[n]['bb_lo'], D[n]['bb_hi']) for n in EXT], ORG, HEAD, OUT, 2702000000, 600, 600)
h = math.radians(HEAD)
p = OUT / 'tc_ext_fix.ymap.xml'; ym = ET.parse(p); root = ym.getroot(); es = root.find('entities'); proto = es[0]
PROPS = [('prop_bollard_04', u, v, z, 0.0) for u, v, z in L['bollards']] + [('prop_bench_05', u, v, z, hd) for u, v, z, hd in L['benches']]
for i, (model, u, v, z, hd) in enumerate(PROPS):
    wh = math.radians((hd + HEAD) % 360)
    e = copy.deepcopy(proto); e.find('archetypeName').text = model; e.find('guid').set('value', str(2702000100 + i))
    MM.setvec(e.find('position'), (ORG[0] + u * math.cos(h) - v * math.sin(h), ORG[1] + u * math.sin(h) + v * math.cos(h), z))
    for k, val in zip('xyzw', (0.0, 0.0, -math.sin(wh / 2), math.cos(wh / 2))): e.find('rotation').set(k, f'{val:.7f}')   # plain entity: the conjugate
    e.find('lodDist').set('value', '120')
    es.append(e)
MM.write(root, p)
bad = MM.compile_all(OUT, ('tc_ext_fix.ytyp', 'tc_ext_fix.ymap'))
print('EXT_META', 'entities', len(es), 'props', len(PROPS), 'compile failures:', bad)
