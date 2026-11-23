"""Power lines over the Graveyard tow yard. The poles all stay (Antonio), but some vanilla wire spans ended on buildings that are gone
(the old hangar, the mobile home, the junk sheds): those ends hang in mid-air. For each wire drawable, every span (a connected piece
of the mesh) is checked inside REGION (the site + 15 m):
  * both ends on standing poles (POLES, ../site/poles.tsv from site_scan.ps1, within HELD m in plan: the crossarm) -> untouched;
  * one end on a pole, the other free -> its line from the pole, carried on past the free end, meets the house's upper storey
    (HOUSE_WALL): it is re-hung onto an insulator there (prop_telegwall_01b, placed by site_place.py from ../site/wires/*.json), its
    cross-section kept and its sag scaled with the new length; otherwise it is taken out;
  * both ends free -> taken out.
Run:  blender -b --python wires.py -- <ydr name> <x> <y> <z>     (x y z: the wire entity's position; identity rotation)
      (wires_all.sh runs every wire model over the site)
Input ../vanilla/<name>.ydr   Output ../site/wires/<name>.ydr + <name>.json (the new anchors); nothing written when nothing changes"""
import bpy, bmesh, sys, json
from pathlib import Path
from mathutils import Vector
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T)); import site_plan as SP, house_plan as H
M_ = T.parent; SRC = M_ / 'vanilla'; OUT = M_ / 'site' / 'wires'; OUT.mkdir(parents=True, exist_ok=True)
xs = [p[0] for poly in SP.PAVED for p in poly]; ys = [p[1] for poly in SP.PAVED for p in poly]
REGION = (min(xs) - 15, max(xs) + 15, min(ys) - 15, max(ys) + 15)
POLES = [(float(r.split('\t')[1]), float(r.split('\t')[2])) for r in (M_ / 'site' / 'poles.tsv').read_text().splitlines() if r.strip()]
HELD = 2.5                                                       # a span ends on a crossarm, up to ~2 m off the pole
HOUSE_WALL = (H.X0 + 8.0, H.X0 + H.W, H.Y0, H.Y0 + H.D)          # the main block (two storeys); the garage wing is too low
ANCHOR_Z = H.ROOF - 0.8                                          # insulator height on the upper storey, under the parapet
args = sys.argv[sys.argv.index('--') + 1:]; name = args[0]; P = Vector((float(args[1]), float(args[2]), float(args[3])))
def held(v): return min(((v.x - x) ** 2 + (v.y - y) ** 2) ** 0.5 for x, y in POLES) <= HELD
def in_region(v): a, b, c, d = REGION; return a <= v.x <= b and c <= v.y <= d
def wall_point(free_end, pole_end):
    """the span's line from its pole, carried on past the free end (up to 3x), meets the house's upper storey: there, 3 cm off the
    wall, at ANCHOR_Z, with the insulator's heading. (None, None) if it never reaches it."""
    a, b, c, d = HOUSE_WALL
    for i in range(1201):
        p = pole_end.lerp(free_end, i / 400)
        if a <= p.x <= b and c <= p.y <= d: break
    else: return None, None
    q = p.copy(); dx = min(abs(q.x - a), abs(q.x - b)); dy = min(abs(q.y - c), abs(q.y - d))
    if dx < dy:
        if abs(q.x - a) < abs(q.x - b): q.x, hd = a - 0.03, 270.0
        else: q.x, hd = b + 0.03, 90.0
    else:
        if abs(q.y - c) < abs(q.y - d): q.y, hd = c - 0.03, 0.0
        else: q.y, hd = d + 0.03, 180.0
    return Vector((q.x, q.y, ANCHOR_Z)), hd
bpy.ops.wm.read_homefile(use_empty=True)
assert 'FINISHED' in bpy.ops.sollumz.import_assets(directory=str(SRC), files=[{'name': name + '.ydr'}])
for f in (OUT / f'{name}.ydr', OUT / f'{name}.json'): f.unlink(missing_ok=True)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.vertices]
report = []; anchors = []; changed = 0
for ob in meshes:
    mw = ob.matrix_world
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; comp = []
        while stack:
            u = stack.pop()
            if u.index in seen: continue
            seen.add(u.index); comp.append(u); stack += [e.other_vert(u) for e in u.link_edges]
        comps.append(comp)
    dead = []
    for comp in comps:
        W = [(mw @ u.co) + P for u in comp]
        step = max(1, len(W) // 40)
        i0, i1 = max(((i, j) for i in range(0, len(W), step) for j in range(0, len(W), step)), key=lambda ij: (W[ij[0]] - W[ij[1]]).length)
        e0, e1 = W[i0], W[i1]
        f0, f1 = (in_region(e) and not held(e) for e in (e0, e1))
        if not (f0 or f1): continue
        changed += 1
        free_e, pole_e = (e0, e1) if f0 else (e1, e0)
        new_end, hd = (None, None) if (f0 and f1) or not held(pole_e) else wall_point(free_e, pole_e)
        report.append({'ends': [[round(c, 1) for c in e0], [round(c, 1) for c in e1]], 'rehung': new_end is not None})
        if new_end is None: dead.extend(comp); continue
        anchors.append([round(c, 3) for c in new_end] + [hd])
        chord = free_e - pole_e; L = chord.length; nchord = new_end - pole_e; L2 = nchord.length; dirn = chord.normalized()
        for u, w in zip(comp, W):
            t = max(0.0, min(1.0, (w - pole_e).dot(dirn) / L)); dev = w - (pole_e + chord * t)
            nw = pole_e + nchord * t + Vector((dev.x, dev.y, dev.z * (L2 / L)))
            u.co = mw.inverted() @ (nw - P)
    if dead: bmesh.ops.delete(bm, geom=list({u for u in dead}), context='VERTS')
    bm.to_mesh(ob.data); bm.free()
print('WIRES_SPANS', name, json.dumps(report), flush=True)
if not changed: print('WIRES_UNCHANGED', name, flush=True); sys.exit(0)
json.dump(anchors, open(OUT / f'{name}.json', 'w'), indent=1)
root = next(o for o in bpy.data.objects if o.sollum_type == 'sollumz_drawable' and o.parent is None)
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True); bpy.context.view_layer.objects.active = root
assert 'FINISHED' in bpy.ops.sollumz.export_assets(directory=str(OUT), use_custom_settings=True, target_formats={'NATIVE'}, target_versions={'GEN8'}, limit_to_selected=True)
print('WIRES_PASS', name, len(anchors), 're-hung', len([r for r in report if not r['rehung']]), 'taken out', flush=True)
