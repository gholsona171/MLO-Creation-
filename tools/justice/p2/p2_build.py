"""Justice Center phase 2: every exterior HD model, their night emissive models and the site's collision, rebuilt from p2_plan /
p2_site every run (work/p2/out is wiped). Tower City's tc_kit is the shared kit (imported, never edited).
Outputs (work/p2/out): jc_tower / jc_police / jc_jail1 / jc_jail2 / jc_atrium / jc_bridges / jc_site / jc_core .ydr, their *_emi
models, jc_ext_col.ybn (all exterior collision, world space), tris_*.npy (world triangles for the gates), zfight.json (the sweep),
p2_layout.json (origin, drawables + bounds, props for the site ymap).
Run: blender -b --python p2_build.py"""
import sys, json, math, shutil, time
from pathlib import Path
P2 = Path(__file__).resolve().parent; WK = P2.parent; J = WK.parent
sys.path[:0] = [r'C:\Users\anton\Documents\Codex\TowerCity\work', str(P2), str(WK)]
import tc_kit as TK
import jc_frame as F
TK.set_origin(F.OX, F.OY, F.HDEG)
import p2_plan as PL, p2_site_plan as SP
OUT = P2 / 'out'; shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
BLD = ['tower', 'police', 'jail1', 'jail2', 'atrium']
KEYS = BLD + ['bridges', 'site'] + (['core'] if not PL.MLO_BUILT['atrium'] else []) + ['emi_' + k for k in BLD + ['bridges']]
t0 = time.time()
TK.init(OUT, {}, ext_keys=KEYS)
import p2_mats as PM
SW = PM.build()
import p2_kit as PK, p2_facade as FA, p2_sitebuild as SB
for k in BLD: FA.building(k, 'emi_' + k); print('P2_BUILT', k, round(time.time() - t0, 1), flush=True)
FA.bridges('bridges', 'emi_bridges')
SB.podium('site'); SB.steps('site'); SB.lawn('site'); SB.walls('site'); SB.portal('site')
if 'core' in KEYS: SB.core('core')
# the tower's roof: the antenna mast (real tower: a lattice mast with dishes at one corner) and its aviation light
def mast(u, v, z, h=9.0):
    legs = [(u + a, v + b) for a, b in ((-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7))]; top = [(u + a * 0.45, v + b * 0.45) for a, b in ((-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7))]
    for (a, b), (c, d) in zip(legs, top): TK.beam('tower', (a, b, z), (c, d, z + h), 0.12, 'metal')
    for i in range(6):                                          # ring braces: each side at its own height, ends short of the legs
        zz = z + 0.5 + i * (h - 1.0) / 5; t = (zz - z) / h
        P = [(a + (c - a) * t, b + (d - b) * t) for (a, b), (c, d) in zip(legs, top)]
        for j, (p, q) in enumerate(zip(P, P[1:] + P[:1])):
            L = math.dist(p, q); e = 0.09 / L; zj = zz + 0.06 * j
            TK.beam('tower', (p[0] + (q[0] - p[0]) * e, p[1] + (q[1] - p[1]) * e, zj), (q[0] - (q[0] - p[0]) * e, q[1] - (q[1] - p[1]) * e, zj), 0.07, 'metal')
    TK.box('tower', (u + 0.35, v - 0.6, z + h * 0.62), (u + 0.5, v + 0.6, z + h * 0.62 + 1.2), 'metal', col=False)        # dish panel
    TK.box('tower', (u - 0.12, v - 0.12, z + h), (u + 0.12, v + 0.12, z + h + 0.25), 'aviation', col=False)
    PK.col_box((u - 0.8, v - 0.8, z), (u + 0.8, v + 0.8, z + h), 'metal')
tb = PL.B['tower']; mast(tb['box'][1] - 4.5, tb['box'][3] - 4.5, tb['roof'])
TK.box('tower', (27.0, 31.0, tb['roof']), (37.0, 41.0, tb['roof'] + 3.6), 'granite', col=False)                             # lift overrun / plant room
PK.col_box((27.0, 31.0, tb['roof']), (37.0, 41.0, tb['roof'] + 3.6), 'stone')
# UVs per material at Rockstar's own texel density, his sidewalk's UVs + colours on the paving
import numpy as np
def ext_pass(o, L2W):
    me = o.data; uv = me.uv_layers[0]; names = [m.name if m else '' for m in me.materials]
    for p in me.polygons:
        n = names[p.material_index][3:] if names[p.material_index].startswith('JC ') else ''
        mpu = PM.M_PER_UV.get(n)
        if not mpu: continue
        ax = max(range(3), key=lambda i: abs(p.normal[i])); axes = [i for i in range(3) if i != ax]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[axes[0]] / mpu, co[axes[1]] / mpu)
    if not o.parent.name.endswith('_emi'):                     # his vertex colours (p2_mats.EXT_VCOL): never full artificial ambient
        for a in me.color_attributes:
            for d in a.data: d.color_srgb = PM.EXT_VCOL                     # color_srgb: what Sollumz stores (.color is linearised, doc 02)
    SW.paint(o, L2W @ o.matrix_world)
    # centre the model on its own bounds: the entity stands at that centre (lodDist is measured from the entity, as Rockstar's)
    import numpy as np
    from mathutils import Matrix, Vector
    P_ = np.array([v.co[:] for v in me.vertices]); c = (P_.min(0) + P_.max(0)) / 2
    me.transform(Matrix.Translation(-Vector(c))); CENTRE[o.parent.name] = [float(x) for x in c]
CENTRE = {}
TK.POST_EXT.append(ext_pass)
NAMES = {k: 'jc_' + k for k in BLD + ['bridges', 'site', 'core'] if k in KEYS}
NAMES.update({'emi_' + k: 'jc_' + k + '_emi' for k in BLD + ['bridges']})
NAMES = {k: n for k, n in NAMES.items() if TK.PARTS[k]}                                   # (the atrium has no lit bays: no _emi model)
info = TK.export_all({}, NAMES, 'jc_unused', 'jc_unused_col')
counts, nchild = PK.export_collision('jc_ext_col', OUT, TK.L2W)
props = []
def prop(model, u, v, z, h): x, y = F.W(u, v); props.append({'model': model, 'pos': [round(x, 3), round(y, 3), round(z, 3)], 'heading': round((h + F.HDEG) % 360, 2)})
for u, v in SP.S['bollards']: x, y = F.W(u, v); prop('prop_bollard_04', u, v, F.slab_z(x, y), 0.0)
for u, v, h in SP.S['benches']: prop('prop_bench_01a', u, v, PL.G, h)
for u, v in SP.S['flags']: prop('prop_flagpole_1a', u, v, PL.G, 0.0)
for u, v in SP.S['trees']: prop('prop_tree_birch_03b', u, v, SP.lawn_z(u, v) - 0.05, 0.0)
for n, d in info.items():                                         # bounds relative to the centred model
    c = CENTRE[n]; d['centre'] = c; d['bb_lo'] = [a - b for a, b in zip(d['bb_lo'], c)]; d['bb_hi'] = [a - b for a, b in zip(d['bb_hi'], c)]
lay = {'origin': [F.OX, F.OY, 0.0], 'heading': F.HDEG, 'drawables': info, 'names': NAMES, 'props': props, 'collision': {'name': 'jc_ext_col', 'faces': counts, 'children': nchild},
       'lit_bays': FA.STATS.get('lit', 0), 'buildings': {k: {'roof': PL.B[k]['roof'], 'top': PL.B[k]['top'], 'levels': PL.B[k]['levels']} for k in BLD}}
json.dump(lay, open(OUT / 'p2_layout.json', 'w'), indent=1)
print('P2_BUILD_PASS', json.dumps({'drawables': len(info), 'collision': counts, 'children': nchild, 'lit': lay['lit_bays'], 'props': len(props), 's': round(time.time() - t0)}), flush=True)
