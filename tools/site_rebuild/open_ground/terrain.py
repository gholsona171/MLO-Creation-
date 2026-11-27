"""Rockstar's drawn ground at the Block Boyz site put under our lot surface (ground.py): every land / beach / trail model on the site
(vanilla_models.py) - its sand, its overlays and its decals. Every LOD mesh is first cut along the site's outline (site_plan.SITE)
and on a GRID m world grid inside it (so no long triangle can bridge over a hump of the new grade), then each vertex on the
outline is set to the new grade (grade.grade_z) and each one inside the site DEPTH m under it (or left where it is if it is
already lower: the old basins); outside nothing moves. Textures stay in Rockstar's dictionaries (not embedded). Our copies replace
the vanilla models by name.
Run: blender -b --python terrain.py -- <ydr name>      (terrain_all.sh runs every listed model)
Input ../vanilla/models/<name>.ydr + its placement from ../vanilla/models.tsv.  Output ../site/terrain/<name>.ydr"""
import bpy, bmesh, sys, math
from pathlib import Path
from mathutils import Vector
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T)); import site_plan as SP, grade as GR
M_ = T.parent; SRC = M_ / 'vanilla' / 'models'; OUT = M_ / 'site' / 'terrain'; OUT.mkdir(parents=True, exist_ok=True)
from bl_ext.user_default.sollumz.sollumz_properties import LODLevel
name = sys.argv[sys.argv.index('--') + 1]
DEPTH, EDGE, GRID = 0.25, 0.05, 4.0
pos = None
for r in (M_ / 'vanilla' / 'models.tsv').read_text().splitlines():
    a, kind, x, y, z = r.split('\t')
    if a == name: pos = Vector((float(x), float(y), float(z)))
assert pos is not None, f'{name}: not in models.tsv'
(OUT / f'{name}.ydr').unlink(missing_ok=True)
S = SP.SITE; xs = [p[0] for p in S]; ys = [p[1] for p in S]
BOX = (min(xs), max(xs), min(ys), max(ys))
# every cut: (a point on the plane, its normal, the plan box a face must reach to be cut): the outline's edges, then the grid lines
CUTS = []
for i in range(len(S)):
    (ax, ay), (bx, by) = S[i], S[(i + 1) % len(S)]
    CUTS.append((Vector((ax, ay, 0.0)), Vector((by - ay, -(bx - ax), 0.0)).normalized(), (min(ax, bx) - 1, max(ax, bx) + 1, min(ay, by) - 1, max(ay, by) + 1)))
for k in range(int(BOX[0] // GRID) + 1, int(BOX[1] // GRID) + 1):
    CUTS.append((Vector((k * GRID, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), (k * GRID - .01, k * GRID + .01, BOX[2], BOX[3])))
for k in range(int(BOX[2] // GRID) + 1, int(BOX[3] // GRID) + 1):
    CUTS.append((Vector((0.0, k * GRID, 0.0)), Vector((0.0, 1.0, 0.0)), (BOX[0], BOX[1], k * GRID - .01, k * GRID + .01)))


def reaches(P_, box):
    """the face's plan extent meets the box (by extent, not by corner: a long thin triangle spans a line with no corner near it)."""
    return min(q.x for q in P_) <= box[1] and max(q.x for q in P_) >= box[0] and min(q.y for q in P_) <= box[3] and max(q.y for q in P_) >= box[2]


bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ydr'}])
root = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable' and o.parent is None); root.name = name
for m in bpy.data.materials:
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and hasattr(nd, 'texture_properties'): nd.texture_properties.embedded = False
moved = 0
for ob in [o for o in root.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_drawable_model']:
    mw = ob.matrix_world; inv = mw.inverted(); inv3 = inv.to_3x3()
    W = lambda co: mw @ co + pos
    for level in LODLevel:
        lod = ob.sz_lods.get_lod(level); me = lod.mesh if lod else None
        if me is None or not me.vertices: continue
        bm = bmesh.new(); bm.from_mesh(me)
        if not any(SP.on_site(*W(v.co).xy) for v in me.vertices) and not any(
                reaches([W(me.vertices[i].co) for i in p.vertices], BOX) for p in me.polygons): bm.free(); continue
        for co, no, box in CUTS:
            faces = [f for f in bm.faces if reaches([W(v.co) for v in f.verts], box)]
            if not faces: continue
            geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=inv @ (co - pos), plane_no=(inv3 @ no).normalized())
        for v in bm.verts:
            w = W(v.co)
            if SP.seg_dist(w.x, w.y, S) <= EDGE: z = GR.grade_z(w.x, w.y)
            elif SP.on_site(w.x, w.y): z = min(w.z, GR.grade_z(w.x, w.y) - DEPTH)
            else: continue
            if abs(z - w.z) > 1e-4: w.z = z; v.co = inv @ (w - pos); moved += 1
        bm.to_mesh(me); bm.free()
print('TERRAIN_STATS', name, moved, flush=True)
if not moved: print('TERRAIN_UNCHANGED', name, flush=True); sys.exit(0)
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('TERRAIN_PASS', name, moved, flush=True)
