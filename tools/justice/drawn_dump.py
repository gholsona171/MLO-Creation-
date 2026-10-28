"""Justice Center (Blender, read-only on the game files): every DRAWN vanilla surface round the block, placed like the game places it.
Adapted from Tower City work/tools/drawn_dump.py.
Entities: plan/near_entities_wide.tsv (tools/near_ents.ps1), the LIVE copy of each ymap (jc_frame.live_ymap: lr_ when it exists, else
the base name, hei_ only when neither exists), HD / orphan HD, no props, deduplicated.
Models: the first dir of --dirs that holds <name>.ydr (pass the cut dir first to see a build: work/cut, then src/native).
--skip <json list file>: model names to leave out (a build's removed models: they are swapped to the empty model).
Plain entity rotation in a ymap = the conjugate of the real one (playbook 02).
Run: blender -b --python drawn_dump.py -- <out.npz> --dirs d1,d2 [--skip f.json] [--margin 25]
  -> tris (n, 3, 3) world, mid (model index per triangle), mat (material index per triangle), names, mats."""
import bpy, sys, json, csv, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter'); sys.path.insert(0, str(J / 'work'))
import jc_frame as F
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; dirs = [Path(d) for d in a[a.index('--dirs') + 1].split(',')]
skip = set(json.load(open(a[a.index('--skip') + 1]))) if '--skip' in a else set()
margin = float(a[a.index('--margin') + 1]) if '--margin' in a else 25.0
xs = [p[0] for p in F.KERB_W]; ys = [p[1] for p in F.KERB_W]
BOX = (min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin)
ents = {}; seen = set()
ROWS = list(csv.DictReader(open(J / 'plan/near_entities_wide.tsv'), delimiter='\t')); YM = {r['ymap'] for r in ROWS}
for r in ROWS:
    if not F.live_ymap(r['ymap'], YM) or r['bbMinX'] == '': continue
    nm = r['archetype'].lower(); lod = r['lodLevel']
    if lod not in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD') or nm.startswith(('prop_', 'p_')) or nm in skip: continue
    x, y, z, qx, qy, qz, qw = (float(r[k]) for k in ('x', 'y', 'z', 'qx', 'qy', 'qz', 'qw'))
    lo = [float(r[k]) for k in ('bbMinX', 'bbMinY', 'bbMinZ')]; hi = [float(r[k]) for k in ('bbMaxX', 'bbMaxY', 'bbMaxZ')]
    rad = math.dist(lo, hi) / 2 + math.hypot((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)   # bounds need not be centred on the origin
    if x + rad < BOX[0] or x - rad > BOX[1] or y + rad < BOX[2] or y - rad > BOX[3]: continue
    key = (nm, round(x, 1), round(y, 1))
    if key in seen: continue
    seen.add(key)
    src = next((d for d in dirs if (d / f'{nm}.ydr').exists()), None)
    if src is None: continue
    ents.setdefault((nm, str(src)), []).append((Vector((x, y, z)), Quaternion((qw, -qx, -qy, -qz))))
tris = []; mid = []; mat = []; names = []; mats = []
for (nm, src), places in sorted(ents.items()):
    bpy.ops.wm.read_homefile(use_empty=True)
    try:
        if 'FINISHED' not in bpy.ops.sollumz.import_assets(directory=src, files=[{'name': nm + '.ydr'}]): continue
    except Exception: print('DRAWN_DUMP skip', nm, flush=True); continue
    root = bpy.data.objects.get(nm) or next((o for o in bpy.data.objects if o.parent is None and o.sollum_type == 'sollumz_drawable'), None)
    if root is None: continue
    V = []; M = []
    for m in [c for c in root.children_recursive if c.type == 'MESH' and c.sollum_type == 'sollumz_drawable_model']:
        l = m.sz_lods.get_lod(LODLevel.HIGH)
        if l is None or l.mesh is None: continue
        me = l.mesh; me.calc_loop_triangles(); mw = m.matrix_world
        P = np.array([tuple(mw @ v.co) for v in me.vertices]); I = np.array([t.vertices[:] for t in me.loop_triangles], np.int64)
        if not len(I): continue
        V.append(P[I])
        for t in me.loop_triangles:
            mn = nm + '|' + (me.materials[t.material_index].name.split('.')[0] if me.materials and me.materials[t.material_index] else '')
            if mn not in mats: mats.append(mn)
            M.append(mats.index(mn))
    if not V: continue
    V = np.concatenate(V); names.append(nm); M = np.array(M, np.int32)
    for pos, q in places:
        R = np.array(q.to_matrix()); W_ = V @ R.T + np.array(pos)
        tris.append(W_.astype(np.float32)); mid.append(np.full(len(W_), len(names) - 1, np.int32)); mat.append(M)
np.savez_compressed(out, tris=np.concatenate(tris), mid=np.concatenate(mid), mat=np.concatenate(mat), names=np.array(names), mats=np.array(mats))
print('DRAWN_DUMP', len(names), 'models', sum(len(t) for t in tris), 'triangles', flush=True)
