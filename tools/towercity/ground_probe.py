"""Tower City: every drawn and walked face straight down through given lot-frame points (ground_check.py's data; the ORIGINAL vanilla
collision from src/ground_ref beside the shipped one). Run: py -3 tools/ground_probe.py u,v [u,v ...]"""
import sys, json, numpy as np, xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
import ground_check as G, ext_plan as EP
def hits(Tr, x, y):
    out = []
    for k, t in enumerate(Tr):
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
        if max(ax, bx, cx) < x or min(ax, bx, cx) > x or max(ay, by, cy) < y or min(ay, by, cy) > y: continue
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12: continue
        l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / d; l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / d; l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -1e-6: continue
        up = np.cross(t[1] - t[0], t[2] - t[0])[2] > 0
        out.append((round(l1 * az + l2 * bz + l3 * cz, 3), k, 'up' if up else 'down'))
    return sorted(out, reverse=True)
Cw, Cs, files = G.walked(); Dw, Dm, dn, nv = G.drawn(False)
orig = sorted((G.T / 'src/ground_ref').glob('*.ybn')); OT, OS = [], []
for k, f in enumerate(orig):
    x = ET.parse(G.XD / (f.name + '.xml')).getroot() if (G.XD / (f.name + '.xml')).exists() else None
    if x is None: continue
    b = x if x.tag == 'Bounds' else x.find('.//Bounds'); t = G.tris_of(b); OT.append(t); OS += [f.name] * len(t)
OT = np.concatenate(OT)
for a in sys.argv[1:]:
    u, v = map(float, a.split(',')); x, y = EP.W(u, v)
    print(f'== u {u} v {v}  (world {x:.2f}, {y:.2f})')
    for z, k, s in hits(Dw, x, y)[:8]: print('   DRAWN ', z, s, dn[Dm[k]])
    for z, k, s in hits(Cw, x, y)[:8]: print('   WALKED', z, s, files[Cs[k]])
    for z, k, s in hits(OT, x, y)[:8]: print('   ORIG  ', z, s, OS[k])
