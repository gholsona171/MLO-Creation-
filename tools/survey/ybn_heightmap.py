"""Justice Center survey: top-surface height map of vanilla collision (CodeWalker ybn XML) on a world grid.
Reads every src/xml/*.ybn.xml, turns triangles + box primitives into triangles in world space and keeps, per 0.5 m cell,
the highest up-facing surface below ZMAX (and its file). Writes survey/heightmap.npz + heightmap.png (north up).
Usage: py -3 ybn_heightmap.py [zmax]"""
import re, sys, glob, os
import numpy as np
from scipy.spatial import ConvexHull
ROOT = r'C:\Users\anton\Documents\Codex\JusticeCenter'
X0, X1, Y0, Y1, CELL = 220.0, 430.0, -1725.0, -1530.0, 0.5
ZMAX = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
nx, ny = int((X1 - X0) / CELL), int((Y1 - Y0) / CELL)
top = np.full((ny, nx), -1e9); src = np.full((ny, nx), -1, int)
num = r'(-?[\d.]+(?:E[-+]?\d+)?)'

def tris_of(xml):
    out = []
    for ch in re.finditer(r'<Item type="Geometry(?:BVH)?">(.*?)</Polygons>', xml, re.S):
        b = ch.group(1)
        m = re.search(r'<CompositeTransform>(.*?)</CompositeTransform>', b, re.S)
        T = np.array([float(v) for v in m.group(1).split()]).reshape(4, 4) if m else np.eye(4)
        g = re.search(r'<GeometryCenter x="%s" y="%s" z="%s"' % (num, num, num), b)
        gc = np.array([float(g.group(i)) for i in (1, 2, 3)])
        vt = re.search(r'<Vertices>(.*?)</Vertices>', b, re.S).group(1)
        V = np.array([[float(c) for c in l.split(',')] for l in vt.strip().splitlines()]) + gc
        V = V @ T[:3, :3] + T[3, :3]     # row-vector convention (identity here)
        for t in re.finditer(r'<Triangle m="\d+" v1="(\d+)" v2="(\d+)" v3="(\d+)"', b):
            out.append(V[[int(t.group(1)), int(t.group(2)), int(t.group(3))]])
        for t in re.finditer(r'<Box m="\d+" v1="(\d+)" v2="(\d+)" v3="(\d+)" v4="(\d+)"', b):
            P = V[[int(t.group(i)) for i in (1, 2, 3, 4)]]; c = P.mean(0)
            C = np.vstack([P, 2 * c - P])          # 4 alternate corners + their reflections = the 8 corners
            try:
                h = ConvexHull(C)
                for s in h.simplices: out.append(C[s])
            except Exception:
                pass
    return out

files = sorted(glob.glob(os.path.join(ROOT, 'src', 'xml', '*.ybn.xml')))
xs = X0 + (np.arange(nx) + 0.5) * CELL; ys = Y0 + (np.arange(ny) + 0.5) * CELL
for fi, f in enumerate(files):
    tris = tris_of(open(f, encoding='utf-8').read()); n = 0
    for T in tris:
        a, b, c = T
        nrm = np.cross(b - a, c - a); L = np.linalg.norm(nrm)
        if L < 1e-9 or abs(nrm[2]) / L < 0.3: continue          # walls don't make a top surface
        i0 = max(0, int((min(T[:, 0]) - X0) / CELL)); i1 = min(nx - 1, int((max(T[:, 0]) - X0) / CELL))
        j0 = max(0, int((min(T[:, 1]) - Y0) / CELL)); j1 = min(ny - 1, int((max(T[:, 1]) - Y0) / CELL))
        if i1 < i0 or j1 < j0: continue
        gx, gy = np.meshgrid(xs[i0:i1 + 1], ys[j0:j1 + 1])
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        sub = top[j0:j1 + 1, i0:i1 + 1]; ss = src[j0:j1 + 1, i0:i1 + 1]
        upd = ins & (z > sub) & (z < ZMAX)
        sub[upd] = z[upd]; ss[upd] = fi; n += 1
    print(os.path.basename(f), len(tris), 'tris', n, 'used')
names = [os.path.basename(f) for f in files]
np.savez_compressed(os.path.join(ROOT, 'survey', 'heightmap.npz'), top=top, src=src, x0=X0, y0=Y0, cell=CELL, names=np.array(names))
from PIL import Image
z = top.copy(); z[z < -1e8] = np.nan
lo, hi = 20.0, 100.0
g = np.clip((z - lo) / (hi - lo), 0, 1); g = np.nan_to_num(g, nan=0)
img = (np.stack([g, g, g], -1) * 255).astype(np.uint8)[::-1]   # north up
Image.fromarray(img).save(os.path.join(ROOT, 'survey', 'heightmap.png'))
print('done', np.nanmin(z), np.nanmax(z))
