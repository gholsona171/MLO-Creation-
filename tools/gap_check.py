"""Light-gap audit of the junkyard garage (Antonio, round 6: "I'm checking corners and looking for gaps in walls and gaps in seams
where we've added things ... wire that into our checks"). Run after every shop_edit.py build, before anything goes to Antonio.
Takes the finished interior shell (jy_shop8.ydr) and exterior skin (jy_shop8_ext.ydr) together and fires rays out of every room
from a grid of points (three heights) in ~600 directions. A ray that leaves the building without touching any face found a hole:
its exit point (where it crosses the building's outer box) is binned to 0.25 m cells. Holes inside known openings (door holes:
props fill them; the roll-up doors) are listed apart. Everything else is a GAP to fix.
Run: bash gap_check.sh (exports the XML, then runs this in Blender)       Output ../site/shop_junkyard/gap_report.json + a summary line GAP_CHECK"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
M_ = Path(__file__).resolve().parents[1]; SRC = M_ / 'site' / 'shop_junkyard'
import re, subprocess, xml.etree.ElementTree as ET
verts, polys = [], []                                                # geometry from CodeWalker XML (gap_check.sh exports it; a Sollumz
for name in ('jy_shop8', 'jy_shop8_ext'):                            # re-import trips on the embedded sign textures' mip chains)
    r = ET.parse(SRC / f'{name}.ydr.xml').getroot()
    hi = r.find('DrawableModelsHigh')
    for g in (hi if hi is not None else r).iter('Item'):
        vb, ib = g.find('VertexBuffer'), g.find('IndexBuffer')
        if vb is None or ib is None: continue
        dat = vb.find('Data') if vb.find('Data') is not None else vb.find('Data2'); b = len(verts)
        verts += [Vector([float(q) for q in re.split(r'\s+', ln.strip())[:3]]) for ln in dat.text.strip().splitlines()]
        I = [int(q) for q in ib.find('Data').text.split()]; polys += [[b + I[k], b + I[k + 1], b + I[k + 2]] for k in range(0, len(I), 3)]
tree = BVHTree.FromPolygons(verts, polys)
def seen(o, d, dist):
    """the first face the ray SEES: faces are one-sided in game, a face turned away (its back to the ray) is invisible."""
    p = o.copy(); left = dist
    while left > 0:
        loc, nrm, _, t = tree.ray_cast(p, d, left)
        if loc is None: return None
        if nrm.dot(d) < 0: return loc
        p = loc + d * 1e-3; left -= t + 1e-3
    return None
BOX = ((-15.6, -13.0, -2.2), (10.3, 12.4, 6.2))                     # the building's outer box (model frame)
ROOMS = [((-14.9, -12.3), (9.6, 1.0), -1.0),                       # work bay: x, y ranges, a height inside it (floor / ceiling are
         ((-14.9, 2.0), (-6.5, 8.4), -1.0),                         # found from there by rays: samples at floor + 0.4, floor + 1.7
         ((-5.6, 2.0), (9.6, 8.4), -1.0),                           # and ceiling - 0.3, so no point ever sits outside the walls or
         ((-0.9, 9.2), (9.6, 11.8), -1.0),                          # in the roof void)
         ((-14.9, 2.0), (9.6, 8.4), 2.2)]                           # the deck
OPEN = {'south roll-up 1': ((-13.1, -13.0, -2.0), (-7.8, -12.5, 2.4)), 'south roll-up 2': ((-6.8, -13.0, -2.0), (-1.5, -12.5, 2.4)),
        'east roll-up': ((9.9, -9.7, -2.3), (10.3, -1.3, 2.95)),
        'bay person door (south, west end)': ((-15.0, -13.0, -2.0), (-13.7, -12.5, 0.15)), 'bay person door (south, east end)': ((8.3, -13.0, -2.0), (9.5, -12.4, 0.15)),
        'bay person door (east)': ((9.9, -0.1, -2.0), (10.3, 1.15, 0.15)), 'office back door (north)': ((7.9, 8.8, -2.0), (9.1, 12.5, 0.15)), 'front double door': ((-15.6, 1.7, -2.0), (-15.1, 3.8, 0.2)),
        'office/bay door': ((-3.3, 1.3, -2.0), (-2.1, 1.7, 0.2)), 'lobby/office door': ((-6.2, 6.5, -2.0), (-5.8, 7.7, 0.2))}
def dirs(n):
    g = math.pi * (3 - math.sqrt(5)); out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - z * z); out.append(Vector((r * math.cos(g * i), r * math.sin(g * i), z)))
    return out
D = dirs(600)
def exit_point(o, d):
    t = min(((BOX[1][k] if d[k] > 0 else BOX[0][k]) - o[k]) / d[k] for k in range(3) if abs(d[k]) > 1e-6)
    return o + d * t
def in_box(p, b, m=0.0): return all(b[0][k] - m <= p[k] <= b[1][k] + m for k in range(3))
bins = {}; n = 0
UP, DOWN = Vector((0, 0, 1)), Vector((0, 0, -1))
for (x0, y0), (x1, y1), zr in ROOMS:
    nx, ny = max(2, int((x1 - x0) / 2.0)), max(2, int((y1 - y0) / 2.0))
    for i in range(nx):
        for j in range(ny):
            c = Vector((x0 + (x1 - x0) * (i + 0.5) / nx, y0 + (y1 - y0) * (j + 0.5) / ny, zr))
            fl, ce = tree.ray_cast(c, DOWN, 6.0)[0], tree.ray_cast(c, UP, 8.0)[0]
            if fl is None or ce is None: continue                       # not inside a room here
            zs = [fl.z + 0.4, fl.z + 1.7, ce.z - 0.3]
            for z in zs:
                if not fl.z + 0.1 < z < ce.z - 0.1: continue
                o = Vector((c.x, c.y, z))
                for d in D:
                    n += 1
                    if seen(o, d, 80.0) is not None: continue
                    e = exit_point(o, d)
                    if any(in_box(e, b, 0.05) for b in OPEN.values()): continue
                    k = tuple(round(c * 4) / 4 for c in e); bins[k] = bins.get(k, 0) + 1
gaps = sorted(bins.items(), key=lambda kv: -kv[1])
# cluster neighbouring cells into gap sites
sites = []
for k, c in gaps:
    for s in sites:
        if any(max(abs(a - b) for a, b in zip(k, q)) <= 0.5 for q in s['cells']): s['cells'].append(k); s['rays'] += c; break
    else: sites.append({'cells': [k], 'rays': c})
for s in sites:
    cs = s['cells']; s['lo'] = [min(c[k] for c in cs) for k in range(3)]; s['hi'] = [max(c[k] for c in cs) for k in range(3)]; del s['cells']
sites.sort(key=lambda s: -s['rays'])
# ---- pass 2: every outer wall scanned point by point - rays straight out (and 25 deg either side) from 0.3 m inside, every 0.1 m
#      along and 0.2 m up: a thin slit can't hide between rays here. Wall: (axis, inner plane, outward sign, along range, z range)
WALLS = [('x', -15.31, -1, (-12.7, 8.85), (-1.85, 3.3)), ('x', 10.04, 1, (-12.7, 12.15), (-1.85, 3.3)),
         ('y', -12.74, -1, (-15.25, 10.0), (-1.85, 3.3)), ('y', 8.88, 1, (-15.25, -1.35), (-1.85, 3.3)),
         ('y', 12.18, 1, (-1.25, 10.0), (-1.85, 3.3)), ('x', -1.30, -1, (8.95, 12.15), (-1.85, 3.3))]
slits = []
for ax, plane, sg, (a0, a1), (z0, z1) in WALLS:
    a = a0
    while a <= a1:
        z = z0
        while z <= z1:
            o = Vector((plane - sg * 0.3, a, z)) if ax == 'x' else Vector((a, plane - sg * 0.3, z))
            fl, ce = tree.ray_cast(o, DOWN, 6.0)[0], tree.ray_cast(o, UP, 8.0)[0]
            if fl is not None and ce is not None and fl.z + 0.05 < z < ce.z - 0.05:
                for yaw in (-25, 0, 25):
                    r = math.radians(yaw)
                    d = Vector((sg * math.cos(r), math.sin(r), 0.0)) if ax == 'x' else Vector((math.sin(r), sg * math.cos(r), 0.0))
                    if seen(o, d, 3.0) is None:
                        e = o + d * 0.5
                        if not any(in_box(e, b, 0.05) for b in OPEN.values()): slits.append([round(e.x, 2), round(e.y, 2), round(z, 2)])
                        break
            z += 0.2
        a += 0.1
sl = []                                                              # group slit hits per wall position
for p in slits:
    for g in sl:
        if abs(g['x'] - p[0]) < 0.35 and abs(g['y'] - p[1]) < 0.35: g['z'] = [min(g['z'][0], p[2]), max(g['z'][1], p[2])]; g['n'] += 1; break
    else: sl.append({'x': p[0], 'y': p[1], 'z': [p[2], p[2]], 'n': 1})
json.dump({'rays': n, 'sites': sites, 'wall_slits': sl}, open(SRC / 'gap_report.json', 'w'), indent=1)
print('GAP_CHECK', json.dumps({'rays': n, 'gap_sites': len(sites), 'wall_slits': len(sl), 'top': sites[:8], 'slits': sl[:20]}), flush=True)
