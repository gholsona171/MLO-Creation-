"""Tower City survey tool (Blender): every DRAWN vanilla surface round the lots, placed like the game places it - for ground_check.py.
Entities: survey/near_entities.tsv (HD / orphan HD, no props, deduplicated base / hei_ copies), minus what level 0 takes away:
an entity whose origin is inside a lot is swapped to tc_empty (l0_maps.py) unless its model is shipped cut (work/cut: then the CUT
model is used), plus the exterior 'ents' swaps. Models come from work/cut, src/native, src/ground_ref_ydr (extract_by_name.ps1).
Plain entity rotation in a ymap = the conjugate of the real one (playbook 02).
Run: blender -b --python drawn_dump.py -- <out.npz>   -> tris (n, 3, 3) world + model index per triangle + names."""
import bpy, sys, json, csv, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); sys.path.insert(0, str(T / 'work'))
import ext_rules as ER
out = sys.argv[sys.argv.index('--') + 1]
LOTS = list(json.load(open(T / 'plan/lot_polys.json')).values())
CUT = json.load(open(T / 'work/l0_cut_result.json'))['cut']
xs = [p[0] for q in LOTS for p in q]; ys = [p[1] for q in LOTS for p in q]
BOX = (min(xs) - 25, max(xs) + 25, min(ys) - 25, max(ys) + 25)
def inlot(x, y): return any(ER.inside(q, x, y) for q in LOTS)
ents = {}; seen = set()
for r in csv.reader(open(T / 'survey/near_entities.tsv'), delimiter='\t'):
    try: a = r[1].lower(); x, y, z, qx, qy, qz, qw = map(float, r[2:9]); lod = r[9]; lo = list(map(float, r[10:13])); hi = list(map(float, r[13:16]))
    except Exception: continue
    if lod not in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD') or a.startswith(('prop_', 'p_')) or hi[2] - lo[2] > 60: continue
    rad = math.dist(lo, hi) / 2
    if x + rad < BOX[0] or x - rad > BOX[1] or y + rad < BOX[2] or y - rad > BOX[3]: continue
    key = (a.replace('hei_', ''), round(x, 1), round(y, 1))
    if key in seen: continue
    seen.add(key)
    if a in CUT: src = T / 'work/cut'
    elif inlot(x, y): continue                                                     # swapped to tc_empty
    elif any(r_['z'][0] <= z <= r_['z'][1] and ER.inside(r_['poly'], x, y) for r_ in ER.R.get('ents', [])): continue
    else: src = next((d for d in (T / 'src/native', T / 'src/ground_ref_ydr') if (d / f'{a}.ydr').exists()), None)
    if src is None: continue
    ents.setdefault((a, str(src)), []).append((Vector((x, y, z)), Quaternion((qw, -qx, -qy, -qz))))
tris = []; mid = []; names = []
for (a, src), places in sorted(ents.items()):
    bpy.ops.wm.read_homefile(use_empty=True)
    try:
        if 'FINISHED' not in bpy.ops.sollumz.import_assets(directory=src, files=[{'name': a + '.ydr'}]): continue
    except Exception: print('DRAWN_DUMP skip', a, flush=True); continue
    root = bpy.data.objects.get(a) or next((o for o in bpy.data.objects if o.parent is None and o.sollum_type == 'sollumz_drawable'), None)
    if root is None: continue
    V = []
    for m in [c for c in root.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        l = m.sz_lods.get_lod(LODLevel.HIGH)
        if l is None or l.mesh is None: continue
        me = l.mesh; me.calc_loop_triangles(); mw = m.matrix_world
        P = np.array([tuple(mw @ v.co) for v in me.vertices]); I = np.array([t.vertices[:] for t in me.loop_triangles], np.int64)
        if len(I): V.append(P[I])
    if not V: continue
    V = np.concatenate(V); names.append(a)
    for pos, q in places:
        R = np.array(q.to_matrix()); W_ = V @ R.T + np.array(pos)
        tris.append(W_.astype(np.float32)); mid.append(np.full(len(W_), len(names) - 1, np.int32))
np.savez_compressed(out, tris=np.concatenate(tris), mid=np.concatenate(mid), names=np.array(names))
print('DRAWN_DUMP', len(names), 'models', sum(len(t) for t in tris), 'triangles', flush=True)
