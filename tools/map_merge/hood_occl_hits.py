# Occluder boxes / occlude-model triangles that overlap any hood exterior footprint (oriented, 2D SAT + z overlap)
import sys, os, math, glob, json, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from hood_fp import footprints
F = footprints(sys.argv[1], sys.argv[2], -1)
def axes(poly):
    out = []
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]; out.append((-(y2 - y1), x2 - x1))
    return out
def sep(a, b):
    for ax in axes(a) + axes(b):
        pa = [ax[0] * x + ax[1] * y for x, y in a]; pb = [ax[0] * x + ax[1] * y for x, y in b]
        if max(pa) < min(pb) or max(pb) < min(pa): return True
    return False
def hits(poly, z0, z1):
    return [f['i'] for f in F if z1 >= f['z'][0] and z0 <= f['z'][1] and not sep(poly, f['poly'])]
res = {}
for f in sorted(glob.glob(os.path.join(sys.argv[3], '*.ymap.xml'))):
    nm = os.path.basename(f)[:-9]; r = ET.parse(f).getroot(); boxes = []; tris = []
    for k, it in enumerate(r.find('boxOccluders')):
        g = {c.tag: int(c.get('value')) for c in it}
        cx, cy, cz = g['iCenterX'] / 4, g['iCenterY'] / 4, g['iCenterZ'] / 4; L, W, H = g['iLength'] / 4, g['iWidth'] / 4, g['iHeight'] / 4
        a = math.atan2(g['iSinZ'], g['iCosZ']); c, s = math.cos(a), math.sin(a)
        poly = [(cx + c * x - s * y, cy + s * x + c * y) for x, y in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2))]
        h = hits(poly, cz - H / 2, cz + H / 2)
        if h: boxes.append(dict(k=k, key=[g['iCenterX'], g['iCenterY'], g['iCenterZ'], g['iLength'], g['iWidth'], g['iHeight']], centre=[round(cx, 1), round(cy, 1), round(cz, 1)], size=[L, W, H], rot=round(math.degrees(a)), bld=h))
    tp = f[:-4] + '.tris'
    if os.path.exists(tp):
        n = {}
        for ln in open(tp):
            ln = ln.strip()
            if not ln: continue
            mi, *pts = ln.split(';'); P = [[float(x) for x in q.split(',')] for q in pts]
            h = hits([(p[0], p[1]) for p in P], min(p[2] for p in P), max(p[2] for p in P))
            if h: tris.append(dict(model=int(mi), pts=[[round(v, 3) for v in p] for p in P], bld=h))
    res[nm] = dict(boxes=boxes, tris=tris)
    from collections import Counter
    print(f'== {nm}: {len(boxes)} boxes, {len(tris)} triangles over hood buildings; tris by model {dict(Counter(t["model"] for t in tris))}')
    for b in boxes: print(f'     box #{b["k"]} centre {b["centre"]} L{b["size"][0]:.1f} W{b["size"][1]:.1f} H{b["size"][2]:.1f} rot {b["rot"]} -> bld {b["bld"]}')
json.dump(res, open(sys.argv[4], 'w'))
print('footprints:', [(f['i'], [round(v, 1) for v in f['pos']], round(f['yaw'])) for f in F])
