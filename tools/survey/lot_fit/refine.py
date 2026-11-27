"""Block Boyz site survey: refine a placement family. For headings h0..h1 (1 deg) and anchors in a box (1 m) keep the full-depth
sites (clear of roads, water, structures; masks.npz from search.py) and rank them by the ground range inside the site.
Usage: py -3 refine.py h0 h1 ax0 ax1 ay0 ay1 [depth]"""
import sys, os, math; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import common as C
low, top, (x0, x1, y0, y1, c) = C.heights(); bad = np.load(os.path.join(C.D, 'masks.npz'))['bad']
h0, h1, ax0, ax1, ay0, ay1 = (float(v) for v in sys.argv[1:7]); DEP = float(sys.argv[7]) if len(sys.argv) > 7 else 100.0
us = np.arange(-59.5, 60, 1.0); vs = np.arange(.5, DEP, 1.0); U, V = np.meshgrid(us, vs); U = U.ravel(); V = V.ravel()
res = []
for hd in np.arange(h0, h1 + .1, 1.0):
    h = math.radians(hd); dx = math.cos(h) * U + math.sin(h) * V; dy = math.sin(h) * U - math.cos(h) * V
    for ax in np.arange(ax0, ax1 + .1, 2.0):
        for ay in np.arange(ay0, ay1 + .1, 2.0):
            ii = np.floor(ax + dx - x0).astype(int); jj = np.floor(ay + dy - y0).astype(int)
            if ii.min() < 0 or jj.min() < 0 or ii.max() >= bad.shape[1] or jj.max() >= bad.shape[0]: continue
            if bad[jj, ii].any(): continue
            g = low[jj, ii]; res.append((float(np.ptp(g)), float(g.std()), hd % 360, ax, ay, float(g.mean())))
res.sort()
for r in res[:12]: print('range %.2f std %.2f h=%d anchor=(%.0f,%.0f) mean %.2f' % r)
print(len(res), 'clear sites')
