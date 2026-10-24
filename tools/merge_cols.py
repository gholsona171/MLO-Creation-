"""Merge an MLO's collision objects into ONE mesh per room before the Sollumz composite (playbook 02, Collision):
Sollumz convert_objs_to_single_composite makes one BoundGeometryBVH child per object, and each child appears to cost a
phInstGta physics instance. One child per room keeps room detection (RoomID lives in the polygon materials) and the
STAIRS flag (one material per flag set), with a tiny child count.

Use inside a headless Blender + Sollumz build, after all collision objects exist and before the composite:
    from merge_cols import merge_cols
    cols = merge_cols(cols, make_material)        # make_material(): a fresh Sollumz collision material
    comp = convert_objs_to_single_composite(cols, SollumType.BOUND_GEOMETRYBVH, 'General (Default)')
Every object's materials must carry collision_properties.room_id; flags other than stairs are not kept (extend `key`).
From Tower City work/res_build.py (residence floors: 3,446 boxes -> 22 children)."""
from collections import defaultdict
import bpy


def merge_cols(objs, make_material, link_to=None):
    groups = defaultdict(list)
    for o in objs: groups[o.data.materials[0].collision_properties.room_id].append(o)
    merged = []
    for rid, members in sorted(groups.items()):
        verts, faces, flags = [], [], []
        for o in members:
            mw = o.matrix_world; base = len(verts); st = [m.collision_flags.stairs for m in o.data.materials]
            verts += [tuple(mw @ v.co) for v in o.data.vertices]
            for p in o.data.polygons: faces.append([base + i for i in p.vertices]); flags.append(int(st[p.material_index]))
        me = bpy.data.meshes.new(f'col_room{rid}'); me.from_pydata(verts, [], faces)
        keys = sorted(set(flags))
        for stairs in keys:
            m = make_material(); m.collision_properties.room_id = rid; m.collision_flags.stairs = bool(stairs)
            m.update_tag()                       # else the exported (evaluated) material keeps RoomID 0
            me.materials.append(m)
        idx = {k: i for i, k in enumerate(keys)}; me.polygons.foreach_set('material_index', [idx[f] for f in flags]); me.update()
        ob = bpy.data.objects.new(f'col_room{rid}', me)
        (link_to or bpy.context.scene.collection).objects.link(ob); merged.append(ob)
        for o in members: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    return merged
