"""Block Boyz site survey: the deepest clear site for a given local width, searched over building origins and headings.
The site in the building's local frame (concept_v3: x east along the building, front = -y): x lx0..lx1, y from YB (behind the
arch's back leg) forward to YB - depth. Clear = no road collision (+3 m), water (+5 m), structure (+3 m) cell (masks.npz).
Usage: py -3 fit.py lx0 lx1 h0 h1 hstep x0 x1 y0 y1 step [dmax]"""
import sys, os, math; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import common as C
YB = 46.0
low, top, (gx0, gx1, gy0, gy1, c) = C.heights(); bad = np.load(os.path.join(C.D, 'masks.npz'))['bad']
a = [float(v) for v in sys.argv[1:11]]; lx0, lx1, h0, h1, hs, X0, X1, Y0, Y1, st = a
DMAX = float(sys.argv[11]) if len(sys.argv) > 11 else 220.0
LX = np.arange(lx0 + .5, lx1, 1.0); LY = YB - np.arange(.5, DMAX, 1.0)
U, V = np.meshgrid(LX, LY); U = U.ravel(); V = V.ravel()
res = []
for hd in np.arange(h0, h1 + 1e-6, hs):
    h = math.radians(hd); dx = math.cos(h) * U - math.sin(h) * V; dy = math.sin(h) * U + math.cos(h) * V
    for ox in np.arange(X0, X1 + 1e-6, st):
        for oy in np.arange(Y0, Y1 + 1e-6, st):
            ii = np.floor(ox + dx - gx0).astype(int); jj = np.floor(oy + dy - gy0).astype(int)
            ok = (ii >= 0) & (ii < bad.shape[1]) & (jj >= 0) & (jj < bad.shape[0])
            b = np.ones(len(U), bool); b[ok] = bad[jj[ok], ii[ok]]
            dep = (YB - V[b]).min() - .5 if b.any() else DMAX
            if dep < 60: continue
            g = low[jj[ok & (YB - V < dep)], ii[ok & (YB - V < dep)]]
            res.append((round(dep), -float(np.nanstd(g)), hd % 360, ox, oy, float(np.nanmin(g)), float(np.nanmax(g))))
res.sort(reverse=True)
seen = []
for r in res:
    if any(abs(r[3] - p) < 20 and abs(r[4] - q) < 20 and r[2] == hh for p, q, hh in seen): continue
    seen.append((r[3], r[4], r[2])); print('depth %d std %.2f h=%d origin=(%.0f,%.0f) ground %.1f..%.1f' % (r[0], -r[1], r[2], r[3], r[4], r[5], r[6]))
    if len(seen) >= 12: break
