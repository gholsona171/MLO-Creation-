"""Justice Center: trace the street wire sets that cross / touch the lot - every span (connected piece of a wire / cable mesh, from its
CodeWalker XML: tools/cw_xml.ps1 on the .ydr) with its two ends, the nearest pole to each end, and whether the end lies in the lot.
A wire set whose bounds centre is inside the lot is NOT necessarily the block's: here both (sc1_rd_wireset_21, sc1_rd_cablemesh760288)
run along Davis Ave and Macdonald St between street poles and every span ends on a standing pole -> kept (p1_maps.KEEP_WIRES).
Run (from work/): py -3 tools/wire_spans.py   (needs scratch/wires/<name>.ydr.xml)"""
import re, sys, csv, math, numpy as np, collections
sys.path.insert(0, '.'); import jc_frame as F                   # run from work/
from shapely.geometry import Polygon, Point
LOT = Polygon([p[:2] for p in F.lot_w()])
rows = list(csv.DictReader(open('../plan/near_entities_wide.tsv'), delimiter='\t')); YM = {r['ymap'] for r in rows}
poles = [(r['archetype'], np.array([float(r['x']), float(r['y']), float(r['z'])])) for r in rows if F.live_ymap(r['ymap'], YM) and re.search(r'telegraph|elecbox|pole', r['archetype'])]
def geoms(fn):
    x = open(fn).read(); out = []
    for g in re.findall(r'<VertexBuffer>.*?<Data>(.*?)</Data>.*?<IndexBuffer>\s*<Data>(.*?)</Data>', x, re.S):
        V = np.array([[float(t) for t in l.split()[:3]] for l in g[0].strip().splitlines()])
        I = np.array([int(t) for t in g[1].split()]).reshape(-1, 3)
        out.append((V, I))
    return out
for nm in ('sc1_rd_wireset_21', 'sc1_rd_cablemesh760288_thvy001'):
    r = next(r for r in rows if r['archetype'] == nm and F.live_ymap(r['ymap'], YM)); o = np.array([float(r['x']), float(r['y']), float(r['z'])])
    for V, I in geoms('scratch/wires/%s.ydr.xml' % nm):
        V = V + o
        # components by shared vertex positions
        par = list(range(len(V)))
        def f(a):
            while par[a] != a: par[a] = par[par[a]]; a = par[a]
            return a
        key = {}
        for i, v in enumerate(V):
            k = tuple(np.round(v, 2)); 
            if k in key: par[f(i)] = f(key[k])
            else: key[k] = i
        for t in I:
            par[f(t[1])] = f(t[0]); par[f(t[2])] = f(t[0])
        comp = collections.defaultdict(list)
        for i in range(len(V)): comp[f(i)].append(i)
        print(nm, len(comp), 'spans')
        for c in comp.values():
            P = V[c]; d = P[:, :2]; 
            # endpoints: the two points farthest apart
            i = np.argmax(((d - d[0]) ** 2).sum(1)); j = np.argmax(((d - d[i]) ** 2).sum(1))
            ends = []
            for e in (P[i], P[j]):
                best = min(poles, key=lambda p: np.linalg.norm(p[1][:2] - e[:2]))
                ends.append('%s %.1fm z%.1f %s' % (best[0].replace('prop_', ''), np.linalg.norm(best[1][:2] - e[:2]), e[2], 'IN' if LOT.contains(Point(*e[:2])) else 'out'))
            sag = P[:, 2].min()
            print('   %4d pts len %.1f  lowest z %.1f  |' % (len(c), np.linalg.norm(P[i][:2] - P[j][:2]), sag), ' / '.join(ends), ' mid', [round(t, 1) for t in F.L(*((P[i][:2] + P[j][:2]) / 2))])
