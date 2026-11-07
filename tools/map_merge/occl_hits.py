# Which box occluders / occlude-model triangles of each occluder XML overlap the packs' oriented footprints (2D SAT + z overlap).
# Usage: occl_hits.py <footprints.json> <out.json> <occl.ymap.xml>... ; prints per file counts by pack (buildings vs ground/road models apart)
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from occl_lib import load_occl, box_poly, box_desc, tri_desc, hits
F = json.load(open(sys.argv[1])); OUT = sys.argv[2]
FLAT = {'sc1_21_ground01', 'sc1_21_ground02', 'sc1_rd_r3_04', 'sc1_rd_wireset_14', 'sc1_props_flyers15'}   # ground / road / wires: not buildings
def grp(ids):
    g = set()
    for i in ids:
        f = F[i]; g.add(f['pack'] + ('_ground' if f['label'] in FLAT else ''))
    return sorted(g)
res = {}
for p in sys.argv[3:]:
    d = load_occl(p); nm = os.path.basename(p)[:-9]; R = dict(boxes=[], tris=[])
    for k, b in enumerate(d['boxes']):
        poly, z0, z1 = box_poly(b); h = hits(poly, z0, z1, F)
        if h: R['boxes'].append(dict(k=k, desc=box_desc(b), packs=grp(h), labels=sorted({F[i]['label'] for i in h})[:6]))
    for mi, m in enumerate(d['models']):
        for t in m['tris']:
            h = hits([(q[0], q[1]) for q in t], min(q[2] for q in t), max(q[2] for q in t), F)
            if h: R['tris'].append(dict(model=mi, desc=tri_desc(t), packs=grp(h)))
    res[nm] = R
    from collections import Counter
    cb = Counter(x for b in R['boxes'] for x in b['packs']); ct = Counter(x for t in R['tris'] for x in t['packs'])
    print(f"{nm:55s} boxes {dict(sorted(cb.items()))}  tris {dict(sorted(ct.items()))}")
json.dump(res, open(OUT, 'w'), indent=1)
