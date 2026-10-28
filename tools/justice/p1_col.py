"""Justice Center phase 1: vanilla collision inside the lot, from Tower City work/l0_col.py. One file per Blender process:
  blender -b --python p1_col.py -- <name without .ybn>        Input src/game/<name>.ybn  Output work/col/<name>.ybn
 - the block's own collision files (sc1_19_0, hi@sc1_19_0..5, ma@sc1_19_0): EVERYTHING goes, also the old block's pieces that
   reach past the outline (the low block's canopy, wall feet; their drawables are gone too). The file is shipped holding only a
   keeper (one of its own triangles at 1 % size, 80 m under the ground) so the game still loads a valid bound.
 - the street files that hold old-block collision inside the lot (Rockstar packs collision by area: sc1_rd_4 / 14 and the vehicle
   files hi@sc1_rd_0 / 1 / 7 / 8, every prefix): triangles split along the lot outline, every face / primitive inside it and under ZCUT
   goes (the car-park ramps, the sunken beds, hedges, walls). Above ZCUT only the street poles' crossarms reach in (z 41-42) and stay.
   Spheres / capsules / cylinders inside the lot go at ANY height: they are the removed trees' trunks and crowns (the huge palms'
   crown capsules stood at z 48 - the first build left them floating over the lot; caught by tools/ground_check.py).
   Kept: the collision of the road-ymap props kept in the band (palm / birch trunks: their capsules live in these files) - any
   primitive or triangle within KEEP_R of a kept band prop (work/p1_maps_report.json 'kept_band_lr').
   A box primitive is sampled over its footprint: all inside -> deleted; partly inside -> turned into triangles and cut like them.
 - ground triangles left touching the lot lose their procedural id (no weeds poking through the slab - Cloud 9 lesson)."""
import bpy, bmesh, sys, json, re
from pathlib import Path
from mathutils import Vector
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter'); SRC = J / 'src/game'; OUT = J / 'work/col'; OUT.mkdir(parents=True, exist_ok=True)
POLY = [Vector((p[0], p[1], 0)) for p in json.load(open(J / 'plan/lot_poly.json'))['world']]
ZCUT = 37.0
KEEP_R = 1.0
KEPT = [Vector((k[1], k[2], k[3])) for k in json.load(open(J / 'work/p1_maps_report.json'))['kept_band_lr']]
name = sys.argv[sys.argv.index('--') + 1]
GONE = re.match(r'^(hi@|ma@)?sc1_19_\d+$', name) is not None
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x: c = not c
    return c
def kept(p): return any((p.xy - k.xy).length <= KEEP_R for k in KEPT)
def in_any(p): return True if GONE else (p.z < ZCUT and inside(POLY, p.x, p.y) and not kept(p))
def near_any(p, d=0.6): return any(inside(POLY, p.x + dx, p.y + dy) for dx in (-d, 0, d) for dy in (-d, 0, d))
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ybn'}])
ybn = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_bound_composite' and o.parent is None)
prim = tri = deproc = 0; boxcut = 0; keptn = 0
src = next((o for o in ybn.children_recursive if o.type == 'MESH' and o.sollum_type.startswith('sollumz_bound_poly_') and o.data.vertices), None)
keeper = src.copy(); keeper.data = src.data.copy(); bpy.context.scene.collection.objects.link(keeper); keeper.parent = src.parent
keeper.matrix_world = src.matrix_world.copy(); keeper.name = 'JC_KEEPER'
for v in keeper.data.vertices: v.co = v.co * 0.01
keeper.location.z -= 80
def footprint_samples(vs, n=12):
    out = []
    a, b, c, d = sorted(vs, key=lambda v: v.z)[:4] if len(vs) >= 8 else (vs + vs)[:4]
    base = [a, b, c, d]; cen = sum(base, Vector()) / 4
    for p in base:
        for k in range(n + 1): out.append(p.lerp(cen, 0.02 + 0.98 * k / n))
    for i in range(4):
        for j in range(i + 1, 4):
            for k in range(1, n): out.append(base[i].lerp(base[j], k / n).lerp(cen, 0.02))
    return out
for nm in [o.name for o in ybn.children_recursive if o.name != 'JC_KEEPER']:
    ob = bpy.data.objects.get(nm)
    if ob is None or ob.type != 'MESH' or ob.sollum_type != 'sollumz_bound_poly_box' or not ob.data.vertices: continue
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]; hit = [in_any(p) for p in footprint_samples(vs)]
    if all(hit): bpy.data.objects.remove(ob, do_unlink=True); prim += 1
    elif any(hit):
        bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
        ob.data.transform(ob.matrix_basis); ob.matrix_basis.identity()
        ob.sollum_type = 'sollumz_bound_poly_triangle'; boxcut += 1
bpy.context.view_layer.update()
for nm in [o.name for o in ybn.children_recursive if o.name != 'JC_KEEPER']:
    ob = bpy.data.objects.get(nm)
    if ob is None or ob.type != 'MESH' or not ob.data.vertices: continue
    mw = ob.matrix_world
    if ob.sollum_type.startswith('sollumz_bound_poly_') and ob.sollum_type != 'sollumz_bound_poly_triangle':
        vs = [mw @ v.co for v in ob.data.vertices]; c = sum(vs, Vector()) / len(vs)
        if in_any(c) or (not GONE and inside(POLY, c.x, c.y) and not kept(c)): bpy.data.objects.remove(ob, do_unlink=True); prim += 1   # (a primitive is a trunk / crown / post: no z rule)
        elif not GONE and inside(POLY, c.x, c.y): keptn += 1
    elif ob.sollum_type == 'sollumz_bound_poly_triangle':
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if not GONE:
            vs = [mw @ v.co for v in bm.verts]
            lo = Vector((min(v.x for v in vs), min(v.y for v in vs), 0)); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), 0))
            inv = mw.inverted(); inv3 = inv.to_3x3()
            for i in range(len(POLY)):
                a, b = POLY[i], POLY[(i + 1) % len(POLY)]
                if max(a.x, b.x) < lo.x - 1 or min(a.x, b.x) > hi.x + 1 or max(a.y, b.y) < lo.y - 1 or min(a.y, b.y) > hi.y + 1: continue
                d = (b - a).normalized(); nrm = Vector((-d.y, d.x, 0))
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=inv @ a, plane_no=(inv3 @ nrm).normalized())
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
        dead = [f for f in bm.faces if in_any(mw @ f.calc_center_median())]
        tri += len(dead); bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(ob.data); bm.free()
        if GONE: continue
        me = ob.data; clean = {}
        for f in me.polygons:
            m = me.materials[f.material_index]
            if m is None or m.collision_properties.procedural_id == 0: continue
            if near_any(mw @ f.center):
                if m.name not in clean:
                    c2 = m.copy(); c2.collision_properties.procedural_id = 0; me.materials.append(c2); clean[m.name] = len(me.materials) - 1
                f.material_index = clean[m.name]; deproc += 1
alive = any(o.type == 'MESH' and o.name != 'JC_KEEPER' and o.data.polygons for o in ybn.children_recursive)
if alive: bpy.data.objects.remove(keeper, do_unlink=True)
for ob in [o for o in ybn.children_recursive if o.type == 'MESH' and o.sollum_type == 'sollumz_bound_poly_triangle' and not o.data.polygons and o.name != 'JC_KEEPER']:
    bpy.data.objects.remove(ob, do_unlink=True)
for ob in [o for o in ybn.children_recursive if o.sollum_type in ('sollumz_bound_geometrybvh', 'sollumz_bound_geometry')]:
    if not any(c.type == 'MESH' and c.data.vertices for c in ob.children_recursive) and not (ob.type == 'MESH' and ob.data.vertices):
        for c in list(ob.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(ob, do_unlink=True)
ybn.name = name
bpy.ops.object.select_all(action='DESELECT'); ybn.select_set(True); bpy.context.view_layer.objects.active = ybn
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('P1_COL_PASS', json.dumps({name: {'prims': prim, 'tris': tri, 'deproc': deproc, 'boxes_cut': boxcut, 'kept_band_prims': keptn,
                                        'result': 'kept' if alive else 'EMPTY->keeper', 'rule': 'all' if GONE else 'lot z<%.0f' % ZCUT}}), flush=True)
