"""Foreign geometry inside jc_jail's rooms (2026-10-29: the walker in the secure stair stopped on an INVISIBLE floor at 28.29 - phase 1's
lot slab, drawn and colliding across the whole lot, crosses the stair shaft that goes 6 m down; the old walk check had no z test and
called it 'arrived'). Every other build's surface that can reach our rooms - the lot slab (work/slab: drawn tris + its collision via
CodeWalker XML), phase 2's exteriors (drawn) and their collision (coltris) - is tested against every room's clear volume (its region
inside the linings, floor + 0.05 to ceiling - 0.05): any triangle overlapping one (separating-axis test) is an intrusion.
Proof: --plant adds a slab triangle across the booking hall at 30.0; it must be found. Run: py -3 jj_intrusion.py [--plant]"""
import json, math, sys, subprocess
from pathlib import Path
import numpy as np
JL = Path(__file__).resolve().parent; WK = JL.parent; sys.path[:0] = [str(JL), str(WK)]
import jj_plan as J, jj_fit as JF, jc_frame as F
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
SRC = {'lot slab (drawn)': WK / 'slab/tris_jc_lot.npy', 'phase 2 Jail I (drawn)': WK / 'p2/out/tris_jc_jail1.npy',
       'phase 2 atrium (drawn)': WK / 'p2/out/tris_jc_atrium.npy', 'phase 2 tower (drawn)': WK / 'p2/out/tris_jc_tower.npy',
       'phase 2 site (drawn)': WK / 'p2/out/tris_jc_site.npy', 'phase 2 collision': WK / 'p2/out/coltris_jc_ext_col.npy'}
def slab_col():
    """the lot slab's COLLISION, from its built ybn (CodeWalker XML; MLO-free world space)."""
    x = JL / 'out/xml/jc_lot_col.ybn.xml'; x.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(JL / 'tools/local_xml.ps1'), '-In', str(WK / 'slab/jc_lot_col.ybn'), '-Out', str(x)], capture_output=True)
    if not x.exists(): raise SystemExit('INTRUSION: could not read the slab collision - nothing was tested')
    g = {'__file__': str(JL / 'jj_gates.py'), '__name__': 'x'}; sys.argv_ = sys.argv; sys.argv = ['x', 'none']
    exec(open(JL / 'jj_gates.py', encoding='utf-8').read().split('bad, info =')[0], g); sys.argv = sys.argv_
    T, _, _ = g['ybn'](x); return T                                                   # (a world-space bound: no frame change needed)
def tri_box(T, lo, hi):
    c = (lo + hi) / 2; h = (hi - lo) / 2; V = T - c; ok = np.ones(len(T), bool)
    for a in range(3): ok &= ~((V[:, :, a].min(1) > h[a]) | (V[:, :, a].max(1) < -h[a]))
    E = [V[:, 1] - V[:, 0], V[:, 2] - V[:, 1], V[:, 0] - V[:, 2]]
    n = np.cross(E[0], E[1]); ok &= np.abs((n * V[:, 0]).sum(1)) <= (np.abs(n) * h).sum(1)
    for e in E:
        for a in range(3):
            ax = np.zeros((len(T), 3)); ax[:, a] = 1.0; axv = np.cross(ax, e); p = (V * axv[:, None, :]).sum(2); r = (np.abs(axv) * h).sum(1)
            ok &= ~((p.min(1) > r) | (p.max(1) < -r))
    return ok
sets = {k: lot(np.load(p).astype(np.float64)) for k, p in SRC.items() if p.exists()}
missing = [k for k, p in SRC.items() if not p.exists()]
if missing: raise SystemExit(f'INTRUSION: missing inputs {missing} - nothing was tested')
Tc = slab_col(); sets['lot slab (collision)'] = lot(Tc) if np.abs(Tc[..., 0]).max() > 200 else Tc
if '--plant' in sys.argv: sets['PLANT'] = np.array([[[-25.0, 1.0, 30.0], [-15.0, 1.0, 30.0], [-20.0, 17.0, 30.0]]])
bad = []
for k, r in J.R.items():
    for (u0, u1, v0, v1) in JF.clear(k):
        lo = np.array([u0 + 0.02, v0 + 0.02, r['z0'] + 0.05]); hi = np.array([u1 - 0.02, v1 - 0.02, r['z1'] - 0.05])
        for name, T in sets.items():
            m = tri_box(T, lo, hi)
            if m.any(): bad.append((k, name, int(m.sum()), [round(x, 2) for x in T[m][0].mean(0)]))
for b in bad: print(' ', *b)
if '--plant' in sys.argv:
    assert any(b[1] == 'PLANT' for b in bad), 'PLANTED SLAB NOT FOUND: the intrusion check is broken'; print('JJ_INTRUSION_PLANT_FOUND'); sys.exit(0)
print(('JJ_INTRUSION_PASS' if not bad else 'JJ_INTRUSION_FAIL') + f' {len(bad)} room / source overlaps'); sys.exit(1 if bad else 0)
