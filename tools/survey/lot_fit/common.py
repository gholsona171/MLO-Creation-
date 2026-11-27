"""Block Boyz site survey: shared loaders (height map, live entities, path nodes, water) for the plot and the placement search."""
import csv, re, math, os
import numpy as np
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER_Z = 30.0                                   # the Alamo Sea quads (common.rpf water.xml)
# water.xml quads over the box: (x0, x1, y0, y1, type). type 0 = full rectangle, 2 = a triangle (see water_quads())
WATER_QUADS = [(848, 1304, 3636, 4224, 0), (1304, 1540, 3676, 3796, 2), (1304, 1540, 3796, 4380, 0), (1540, 1612, 3828, 3860, 0)]


def heights():
    z = np.load(os.path.join(D, 'heightmap_1m.npz')); x0, x1, y0, y1, c = z['box']
    return z['low'], z['top'], (x0, x1, y0, y1, c)


def var(n): return 2 if n.startswith('lr_') else 1 if n.startswith('hei_') else 0


def entities(hd_only=True):
    """the live copy of every ymap (lr_ > hei_ > base; the game's IPL state was not asked, see site_survey.md)."""
    R = list(csv.DictReader(open(os.path.join(D, 'near_entities.tsv')), delimiter='\t')); best = {}
    for r in R:
        b = re.sub(r'^(lr_|hei_)', '', r['ymap'])
        if b not in best or var(r['ymap']) > var(best[b]): best[b] = r['ymap']
    live = set(best.values()); out = []
    for r in R:
        if r['ymap'] not in live: continue
        if hd_only and r['lodLevel'] not in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD'): continue
        q = [float(r[k]) for k in ('qx', 'qy', 'qz', 'qw')]
        # ymap rotations are stored conjugated: the world heading is -2*atan2(qz, qw)
        hd = -2 * math.atan2(q[2], q[3])
        bb = [float(r[k]) if r[k] else 0.0 for k in ('bbMinX', 'bbMinY', 'bbMinZ', 'bbMaxX', 'bbMaxY', 'bbMaxZ')]
        out.append(dict(ymap=r['ymap'], arch=r['archetype'], ytyp=r['ytyp'], x=float(r['x']), y=float(r['y']), z=float(r['z']),
                        h=hd, bb=bb, lod=r['lodLevel'], lodDist=float(r['lodDist'])))
    return out


def corners(e):
    """the entity's archetype bounding box in world plan (4 corners)."""
    b = e['bb']; c, s = math.cos(e['h']), math.sin(e['h'])
    return [(e['x'] + c * x - s * y, e['y'] + s * x + c * y) for x, y in ((b[0], b[1]), (b[3], b[1]), (b[3], b[4]), (b[0], b[4]))]


def nodes():
    R = list(csv.DictReader(open(os.path.join(D, 'nodes.tsv')), delimiter='\t')); N = {}
    for r in R: N[(int(r['area']), int(r['node']))] = r
    segs = []
    for r in R:
        for l in r['links'].split():
            a, n = (int(v) for v in l.split(':')); o = N.get((a, n))
            if o is None: continue
            segs.append(((float(r['x']), float(r['y'])), (float(o['x']), float(o['y'])), r['ped'] == 'True', int(r['flags0']), int(r['street'])))
    return R, segs


def in_water_quad(x, y):
    for x0, x1, y0, y1, t in WATER_QUADS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            if t == 0: return True
            return True          # the triangle quad (1304..1540, 3676..3796): treated as covered; the terrain test decides
    return False


HOUSE_RX = re.compile(r'(_build_|bighouse|smallhouse|meth01|methlbovly|_house|_shed|_hut)')


def is_house(arch): return bool(HOUSE_RX.search(arch)) and not arch.endswith(('_decal', '_rails', '_rails1', '_rails2'))
