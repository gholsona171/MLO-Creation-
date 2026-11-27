"""Block Boyz site survey: the numbers for each proposed placement -> ../placements.json (+ a printed summary).
A placement = the building origin (concept_v3 local (0, 0), site.json convention), heading (meta.py: local -> world by +heading
about z) and the site rectangle in the local frame. Ground = the lowest walkable collision surface (heightmap.py 'low')."""
import sys, os, math, json, csv, re, collections; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from matplotlib.path import Path
import common as C
YB = 46.0
PLACEMENTS = [
    dict(id='P1', name="Client's strip, trimmed to what fits", origin=(1222.0, 3573.0), heading=10.0, lx=(-28.0, 92.0), ly=(YB - 69.0, YB),
         note='Between Marina Dr (north, the lake side) and the road to the south. The deepest clear site there is 69 m, not 100.'),
    dict(id='P2', name="Client's strip at full size, over the south road", origin=(1222.0, 3573.0), heading=10.0, lx=(-28.0, 92.0), ly=(YB - 100.0, YB),
         note='Same building spot as P1; the lot runs 31 m further south across the road (that road section would have to close).'),
    dict(id='P3', name='Full size on the slope south of the south road', origin=(1160.0, 3482.0), heading=0.0, lx=(-28.0, 92.0), ly=(YB - 100.0, YB),
         note='The only clear 120 x 100 m sites in the box are on the rising ground south of the south road.'),
]
low, top, (gx0, gx1, gy0, gy1, cell) = C.heights(); M = np.load(os.path.join(C.D, 'masks.npz'))
GX, GY = np.meshgrid(np.arange(gx0 + .5, gx1), np.arange(gy0 + .5, gy1))
ENTS = C.entities(); NODES, SEGS = C.nodes()
GRASS = list(csv.DictReader(open(os.path.join(C.D, 'grass.tsv')), delimiter='\t'))
SCEN = list(csv.DictReader(open(os.path.join(C.D, 'scenarios.tsv')), delimiter='\t'))
CARGENS = {}
for l in open(os.path.join(C.D, 'site_scan.txt')):
    if l.startswith('CARGEN'):
        f = l.rstrip('\n').split('\t'); v = [float(t) for t in re.findall(r'[XYZ]:(-?[\d.]+)', f[2])]
        CARGENS[(round(v[0], 1), round(v[1], 1))] = (f[1], v, re.search(r'model=(\S+)', f[2]).group(1))
GROUND_RX = re.compile(r'(land|decal|beach|lkbed|lkd_|dec_|_trail|roads_|roadsb|_weed$|_rks_|clutter|_glue|armco|detail)')


def W(p, o, h):
    c, s = math.cos(h), math.sin(h); return (o[0] + c * p[0] - s * p[1], o[1] + s * p[0] + c * p[1])


def L(p, o, h):
    c, s = math.cos(h), math.sin(h); dx, dy = p[0] - o[0], p[1] - o[1]; return (c * dx + s * dy, -s * dx + c * dy)


def rect_dist(q, lx, ly):
    dx = max(lx[0] - q[0], 0, q[0] - lx[1]); dy = max(ly[0] - q[1], 0, q[1] - ly[1]); return math.hypot(dx, dy)


def seg_rect_dist(a, b, lx, ly, n=40):
    return min(rect_dist((a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n), lx, ly) for t in range(n + 1))


def kind(e):
    a = e['arch']; w = max(e['bb'][3] - e['bb'][0], e['bb'][4] - e['bb'][1])
    if 'xwire' in a: return 'wire span'
    if a.startswith('prop_telegraph') or a.startswith('prop_telegwall'): return 'power pole'
    if C.is_house(a): return 'building'
    if GROUND_RX.search(a) or w > 40: return 'ground / decal mesh'
    if 'fnc' in a or 'fence' in a: return 'fence'
    if any(t in a for t in ('bush', 'tree', 'palm', 'weed', 'grass', 'agave', 'aloe', 'plant')): return 'plant'
    if 'rock' in a or '_roks' in a: return 'rock'
    if any(t in a for t in ('rub_', 'litter', 'byard', 'tyre')): return 'junk / wreck'
    return 'prop'


def corners_of(o, h, lx, ly):
    return [W(p, o, h) for p in ((lx[0], ly[0]), (lx[1], ly[0]), (lx[1], ly[1]), (lx[0], ly[1]))]


def evaluate(P):
    o, h = P['origin'], math.radians(P['heading']); lx, ly = P['lx'], P['ly']
    corners = corners_of(o, h, lx, ly)
    cen = W(((lx[0] + lx[1]) / 2, (ly[0] + ly[1]) / 2), o, h)
    pts = np.c_[GX.ravel(), GY.ravel()]
    inside = Path(corners).contains_points(pts).reshape(GX.shape)
    g = low[inside]; g = g[~np.isnan(g)]
    zs = np.arange(np.floor(g.min()), np.ceil(g.max()) + .01, .05)
    cut = np.array([np.clip(g - z, 0, None).sum() for z in zs]) * cell * cell
    fill = np.array([np.clip(z - g, 0, None).sum() for z in zs]) * cell * cell
    zb = float(zs[np.argmin(np.abs(cut - fill))])                       # cut = fill
    zw = float(zs[np.argmin(cut + fill)])                               # least earth moved (the median)

    def earth(z):
        return dict(pad_z=round(z, 2), cut_m3=round(float(np.clip(g - z, 0, None).sum() * cell * cell)),
                    fill_m3=round(float(np.clip(z - g, 0, None).sum() * cell * cell)),
                    max_cut_m=round(float(max(g.max() - z, 0)), 2), max_fill_m=round(float(max(z - g.min(), 0)), 2),
                    share_within_0_5m=round(float((np.abs(g - z) <= .5).mean()), 3))
    bld = Path(corners_of(o, h, (-2.5, 66.5), (-10.0, 32.0))).contains_points(pts).reshape(GX.shape)
    gb = low[bld]
    wy, wx = np.nonzero(M['water'])
    wd = min(rect_dist(L((gx0 + i + .5, gy0 + j + .5), o, h), lx, ly) for i, j in zip(wx[::2], wy[::2]))
    ents = []
    rc = [(lx[0], ly[0]), (lx[1], ly[0]), (lx[1], ly[1]), (lx[0], ly[1])]
    for e in ENTS:
        q = [L(p, o, h) for p in C.corners(e)] + [L((e['x'], e['y']), o, h)]
        poly_in = any(Path(q[:4]).contains_point(p) for p in rc)
        d = 0.0 if poly_in else min(rect_dist(p, lx, ly) for p in q)
        if d <= 10.0:
            ents.append(dict(archetype=e['arch'], kind=kind(e), ymap=e['ymap'], x=round(e['x'], 2), y=round(e['y'], 2), z=round(e['z'], 2),
                             inside=d == 0.0, dist_m=round(d, 1), lod=e['lod'].replace('LODTYPES_DEPTH_', '')))
    ents.sort(key=lambda r: (r['kind'], r['archetype'], r['x']))
    segs = []
    for a, b, ped, f0, st in SEGS:
        d = seg_rect_dist(L(a, o, h), L(b, o, h), lx, ly)
        if d <= 10.0: segs.append(dict(a=[round(v, 1) for v in a], b=[round(v, 1) for v in b], ped=ped, crosses=d == 0.0, dist_m=round(d, 1)))
    gr = collections.Counter(r['archetype'] for r in GRASS if rect_dist(L((float(r['x']), float(r['y'])), o, h), lx, ly) == 0)
    sc = collections.Counter(r['type'] or r['kind'] for r in SCEN if rect_dist(L((float(r['x']), float(r['y'])), o, h), lx, ly) <= 10)
    cg = [dict(ymap=v[0], x=v[1][0], y=v[1][1], model=v[2]) for v in CARGENS.values() if rect_dist(L((v[1][0], v[1][1]), o, h), lx, ly) <= 10]
    k = collections.Counter(r['kind'] for r in ents)
    removals = [r for r in ents if r['kind'] not in ('ground / decal mesh', 'wire span')]   # wire bundles: cut / re-hung, not removed whole
    return dict(id=P['id'], name=P['name'], note=P['note'],
                site_json=dict(x=o[0], y=o[1], z=round(zb, 2), heading=P['heading']),
                site_local=dict(x=list(lx), y=list(ly)), size_m=[lx[1] - lx[0], ly[1] - ly[0]],
                centre=[round(cen[0], 1), round(cen[1], 1)], corners=[[round(a, 1), round(b, 1)] for a, b in corners],
                ground=dict(min=round(float(g.min()), 2), max=round(float(g.max()), 2), mean=round(float(g.mean()), 2), std=round(float(g.std()), 2),
                            building_min=round(float(np.nanmin(gb)), 2), building_max=round(float(np.nanmax(gb)), 2)),
                earthwork_cut_equals_fill=earth(zb), earthwork_least=earth(zw),
                road_cells_inside_m2=int((M['road'] & inside).sum()), structure_cells_inside_m2=int((M['struct'] & inside).sum()),
                water_cells_inside_m2=int((M['water'] & inside).sum()), nearest_water_m=round(wd, 1),
                vehicle_segments_crossing=sum(1 for s in segs if s['crosses'] and not s['ped']),
                ped_segments_crossing=sum(1 for s in segs if s['crosses'] and s['ped']), path_segments=segs,
                entities_by_kind=dict(k), removal_count=len(removals), removals_inside=sum(1 for r in removals if r['inside']),
                grass_instances_inside=dict(gr), grass_total=sum(gr.values()), scenario_points=dict(sc), car_generators=cg, entities=ents)


if __name__ == '__main__':
    out = [evaluate(P) for P in PLACEMENTS]
    json.dump(dict(frame='building local frame of tools/concept_v3.py (x east along the building, front = -y); site_json = the building origin '
                         'and heading as tools/meta.py reads site.json, z = the cut = fill pad height. Ground = lowest walkable collision surface.',
                   water_z=C.WATER_Z, placements=out), open(os.path.join(C.D, 'placements.json'), 'w'), indent=1)
    for r in out:
        print(r['id'], r['name'], r['size_m'], 'centre', r['centre'], 'site.json', r['site_json'])
        print('  ground', r['ground'])
        print('  cut=fill', r['earthwork_cut_equals_fill'])
        print('  least', r['earthwork_least'])
        print('  road m2', r['road_cells_inside_m2'], 'struct m2', r['structure_cells_inside_m2'], 'water m2', r['water_cells_inside_m2'], 'nearest water', r['nearest_water_m'])
        print('  veh segs crossing', r['vehicle_segments_crossing'], 'ped', r['ped_segments_crossing'], 'kinds', r['entities_by_kind'], 'removals', r['removal_count'])
        print('  grass', r['grass_total'], 'scen', r['scenario_points'], 'cargens', r['car_generators'])
