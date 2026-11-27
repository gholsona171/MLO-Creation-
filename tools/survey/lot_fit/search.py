"""Block Boyz site survey: where does the site rectangle fit? For every heading and every anchor (the world point of the site's back
edge middle, local (32, 46)) it finds the deepest site (120 m wide along local x, up to 100 m deep toward local -y) that stays clear
of road collision (+3 m), water (ground under 30.0 inside a water quad, +5 m) and the houses (+5 m).
Writes search.npz (best depth per anchor/heading) and prints the best anchors."""
import sys, os, math; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from scipy import ndimage
import common as C
low, top, (x0, x1, y0, y1, c) = C.heights()
z = np.load(os.path.join(C.D, 'heightmap_1m.npz')); src = z['src']; files = list(z['files'])
road = np.isin(src, [i for i, f in enumerate(files) if 'roads' in f])
X, Y = np.meshgrid(np.arange(x0 + .5, x1), np.arange(y0 + .5, y1))
quad = np.vectorize(C.in_water_quad)(X, Y)
water = quad & ((low < C.WATER_Z) | np.isnan(low))
lab, n = ndimage.label(water); size = ndimage.sum(water, lab, range(1, n + 1))
water = np.isin(lab, [i + 1 for i, v in enumerate(size) if v >= 200])   # single cells are holes in the collision, not water
struct = (top - low) > 2.0                       # anything standing on the ground: reported as a removal, it does not block
house = np.zeros_like(road)                      # the houses / sheds (their footprints) block: we keep the neighbours
from matplotlib.path import Path
for e in C.entities():
    if C.is_house(e['arch']): house |= Path(C.corners(e)).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
ROAD_BUF, WATER_BUF, HOUSE_BUF = 3, 5, 5
dil = lambda m, r: ndimage.binary_dilation(m, iterations=r)
bad = dil(road, ROAD_BUF) | dil(water, WATER_BUF) | dil(house, HOUSE_BUF) | np.isnan(low)
np.savez_compressed(os.path.join(C.D, 'masks.npz'), road=road, water=water, struct=struct, house=house, bad=bad)
W, DMAX, S = 120.0, 100.0, 2.0
us = np.arange(-W / 2 + S / 2, W / 2, S); vs = np.arange(S / 2, DMAX, S)     # u across, v forward from the back edge
U, V = np.meshgrid(us, vs); U = U.ravel(); V = V.ravel()
AX = np.arange(1040, 1480, 4.0); AY = np.arange(3420, 3800, 4.0)
HEADS = list(range(0, 360, 5))
best = np.zeros((len(HEADS), len(AY), len(AX)))
for hi, hd in enumerate(HEADS):
    h = math.radians(hd); ch, sh = math.cos(h), math.sin(h)
    # local offset from the anchor: (u, -v) -> world
    dx = ch * U + sh * V; dy = sh * U - ch * V
    for j, ay in enumerate(AY):
        px = AX[:, None] + dx[None, :]; py = np.broadcast_to(ay + dy[None, :], px.shape)
        ii = np.floor(px - x0).astype(int); jj = np.floor(py - y0).astype(int)
        ok = (ii >= 0) & (ii < bad.shape[1]) & (jj >= 0) & (jj < bad.shape[0])
        b = np.ones_like(ok); b[ok] = bad[jj[ok], ii[ok]]
        vb = np.where(b, V[None, :], 1e9).min(1)
        best[hi, j] = np.minimum(vb - S / 2, DMAX)
np.savez_compressed(os.path.join(C.D, 'search.npz'), best=best, heads=HEADS, ax=AX, ay=AY)
flat = [(best[hi, j, i], HEADS[hi], AX[i], AY[j]) for hi in range(len(HEADS)) for j in range(len(AY)) for i in range(len(AX))]
flat.sort(reverse=True)
print('deepest sites (depth, heading, anchor x, y):'); seen = []
for d, hd, ax, ay in flat:
    if any(abs(ax - a) < 40 and abs(ay - b) < 40 for a, b in seen): continue
    seen.append((ax, ay)); print(f'  {d:5.1f} m  h={hd:3d}  anchor=({ax:.0f}, {ay:.0f})')
    if len(seen) >= 15: break
