"""Offline check of a drive line before it is used on the rig (a drive control, a route leg): every built triangle (phase 2 drawn +
collision, phase 3 rooms, the lot slab) that is near-vertical (|n.z| < 0.6), between 0.15 m over the slab and 30.0 m z, and inside a
corridor (lot u0,v0 -> u1,v1, half width) is listed by source. An open control line must list nothing; a wall line must list the wall.
Vanilla map geometry and props (bollards) are not in these files. Run: py -3 jc3_corridor.py u0,v0,u1,v1,halfwidth [...]"""
import sys, numpy as np, math
from pathlib import Path
W = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter\work'); sys.path[:0] = [str(W), str(W/'p3')]
import jc_frame as F
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
src = {'ext_col': W/'p2/out/coltris_jc_ext_col.npy'}
for f in list((W/'p2/out').glob('tris_jc_*.npy')) + list((W/'p3/out').glob('tris_jc_*.npy')):
    if '_emi' not in f.name: src[f.stem[5:]] = f
src['slab'] = W/'slab/tris_jc_lot.npy'
segs = [tuple(map(float, a.split(','))) for a in sys.argv[1:]]   # u0,v0,u1,v1,halfwidth
for name, f in src.items():
    T = lot(np.load(f).astype(np.float64))
    n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); L = np.linalg.norm(n,axis=1)+1e-12; nz = np.abs(n[:,2])/L
    for (u0,v0,u1,v1,hw) in segs:
        d = np.array([u1-u0, v1-v0]); ln = np.linalg.norm(d); d/=ln; q = np.array([-d[1], d[0]])
        P = T[...,:2] - [u0,v0]; a = P@d; b = P@q
        # triangle bbox in segment frame overlaps the corridor
        m = (a.max(1) > 0) & (a.min(1) < ln) & (b.max(1) > -hw) & (b.min(1) < hw) & (nz < 0.6) & (T[...,2].max(1) > 28.45) & (T[...,2].min(1) < 30.0)
        if m.any():
            idx = np.nonzero(m)[0]
            print(name, (u0,v0,u1,v1), m.sum(), 'e.g.', [[round(x,2) for x in T[i].mean(0)] for i in idx[:4]], 'zrange', round(T[idx][...,2].min(),2), round(T[idx][...,2].max(),2))
