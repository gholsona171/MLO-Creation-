"""Block Boyz site survey: ground height map from vanilla collision (CodeWalker ybn XML), the same rasteriser as the playbook's
tools/survey/ybn_heightmap.py, with the box and folders as arguments and two surfaces per cell:
  top = the highest up-facing surface (roofs, decks, the ground where nothing stands on it)
  low = the lowest up-facing surface (the floor under a roof, the terrain under a pier: the ground proxy)
Usage: py -3 heightmap.py <xml dir> <out.npz> [x0 x1 y0 y1 cell]"""
import re, sys, glob, os
import numpy as np
from scipy.spatial import ConvexHull
XD, OUT = sys.argv[1], sys.argv[2]
X0, X1, Y0, Y1, CELL = (float(v) for v in (sys.argv[3:8] if len(sys.argv) > 7 else (1000, 1500, 3400, 3900, 1.0)))
nx, ny = int((X1 - X0) / CELL), int((Y1 - Y0) / CELL)
top = np.full((ny, nx), -1e9); low = np.full((ny, nx), 1e9); src = np.full((ny, nx), -1, int)
num = r'(-?[\d.]+(?:E[-+]?\d+)?)'


def tris_of(xml):
    out = []
    for ch in re.finditer(r'<Item type="Geometry(?:BVH)?">(.*?)</Polygons>', xml, re.S):
        b = ch.group(1)
        m = re.search(r'<CompositeTransform>(.*?)</CompositeTransform>', b, re.S)
        T = np.array([float(v) for v in m.group(1).split()]).reshape(4, 4) if m else np.eye(4)
        g = re.search(r'<GeometryCenter x="%s" y="%s" z="%s"' % (num, num, num), b)
        gc = np.array([float(g.group(i)) for i in (1, 2, 3)])
        vt = re.search(r'<Vertices>(.*?)</Vertices>', b, re.S)
        if not vt: continue
        V = np.array([[float(c) for c in l.split(',')] for l in vt.group(1).strip().splitlines()]) + gc
        V = V @ T[:3, :3] + T[3, :3]
        for t in re.finditer(r'<Triangle m="\d+" v1="(\d+)" v2="(\d+)" v3="(\d+)"', b):
            out.append(V[[int(t.group(1)), int(t.group(2)), int(t.group(3))]])
        for t in re.finditer(r'<Box m="\d+" v1="(\d+)" v2="(\d+)" v3="(\d+)" v4="(\d+)"', b):
            P = V[[int(t.group(i)) for i in (1, 2, 3, 4)]]; c = P.mean(0); C = np.vstack([P, 2 * c - P])
            try:
                for s in ConvexHull(C).simplices: out.append(C[s])
            except Exception:
                pass
    return out


files = sorted(glob.glob(os.path.join(XD, '*.ybn.xml')))
xs = X0 + (np.arange(nx) + 0.5) * CELL; ys = Y0 + (np.arange(ny) + 0.5) * CELL
for fi, f in enumerate(files):
    tris = tris_of(open(f, encoding='utf-8').read()); n = 0
    for T in tris:
        a, b, c = T
        nrm = np.cross(b - a, c - a); L = np.linalg.norm(nrm)
        if L < 1e-9 or nrm[2] / L < 0.3: continue            # walls and down-facing faces don't make a walkable surface
        i0 = max(0, int((T[:, 0].min() - X0) / CELL)); i1 = min(nx - 1, int((T[:, 0].max() - X0) / CELL))
        j0 = max(0, int((T[:, 1].min() - Y0) / CELL)); j1 = min(ny - 1, int((T[:, 1].max() - Y0) / CELL))
        if i1 < i0 or j1 < j0: continue
        gx, gy = np.meshgrid(xs[i0:i1 + 1], ys[j0:j1 + 1])
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not ins.any(): continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        st = top[j0:j1 + 1, i0:i1 + 1]; sl = low[j0:j1 + 1, i0:i1 + 1]; ss = src[j0:j1 + 1, i0:i1 + 1]
        u = ins & (z > st); st[u] = z[u]; ss[u] = fi
        u = ins & (z < sl); sl[u] = z[u]; n += 1
    print(os.path.basename(f), len(tris), 'tris', n, 'used', flush=True)
top[top < -1e8] = np.nan; low[low > 1e8] = np.nan
np.savez_compressed(OUT, top=top, low=low, src=src, files=np.array([os.path.basename(f) for f in files]),
                    box=np.array([X0, X1, Y0, Y1, CELL]))
print('cells', nx, ny, 'empty', int(np.isnan(low).sum()))
