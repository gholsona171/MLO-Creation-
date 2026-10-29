"""Justice Center phase 2 gates on the BUILT exterior (offline; build_p1.sh stops on any failure - nothing deploys):
  sweep  tc_kit's level sweep (work/p2/out/zfight.json, written by p2_build.py for every drawable and across drawables): two faces
         facing the same way within 1.2 cm and overlapping = a flicker. Outside, every face can be seen (from the street, the tower,
         a helicopter), so unlike an interior nothing is excused - every clash fails.
  cross  Tower City's cross_check rule over every exported drawable of the complex AND the lot slab (work/slab/tris_jc_lot.npy):
         two horizontal triangles of different drawables facing the same way, within 3 cm in height, sharing floor area.
  --plant (with cross): the proof run - a copy of the podium's top is put 1 cm over itself as a planted 'other drawable'; the run must
         report it, or the gate is broken (doc 07: prove a check on a known defect first).
Run: py -3 p2_gates.py sweep cross [--plant]"""
import sys, json, collections, numpy as np
from pathlib import Path
P2 = Path(__file__).resolve().parent; J = P2.parent.parent
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\TowerCity\work')
def sweep():
    Z = json.load(open(P2 / 'out/zfight.json')); bad = [(d, h) for d, hs in Z.items() for h in hs]
    c = collections.Counter((d, h.get('kind', 'clash'), tuple(sorted(h['mats']))) for d, h in bad)
    print(f'P2_SWEEP {len(bad)} visible problem(s)')
    for (d, k, m), n in c.most_common(20):
        ex = next(h['at'] for dd, h in bad if dd == d and tuple(sorted(h['mats'])) == m); print(f'  {n:4d}  {d:30s} {k:5s} {"/".join(m):40s} e.g. {ex}')
    return 1 if bad else 0
def cross(plant=False):
    import cross_check as CC
    D = {}
    files = sorted((P2 / 'out').glob('tris_*.npy')) + [J / 'work/slab/tris_jc_lot.npy']
    for f in files:
        T = np.load(f).astype(np.float64)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); L = np.linalg.norm(n, axis=1); ok = L > 1e-6
        T, n = T[ok], n[ok] / L[ok][:, None]; flat = np.abs(n[:, 2]) > 0.95
        D[f.stem[5:]] = (T[flat], np.sign(n[flat][:, 2]))
    if plant:
        T, s = D['jc_site']; up = (s > 0) & (np.abs(T[:, :, 2].mean(1) - 28.8) < 0.01); P_ = T[up][:40].copy(); P_[:, :, 2] += 0.01
        D['planted'] = (P_, np.ones(len(P_))); print('P2_CROSS --plant:', len(P_), 'podium triangles copied 1 cm up as drawable "planted"')
    names = list(D); hits = []
    for i, a in enumerate(names):
        Ta, sa = D[a]
        if not len(Ta): continue
        alo, ahi = Ta.min(1), Ta.max(1)
        for b in names[i + 1:]:
            Tb, sb = D[b]
            if not len(Tb): continue
            blo, bhi = Tb.min(1), Tb.max(1)
            if (ahi.max(0)[:2] < blo.min(0)[:2]).any() or (bhi.max(0)[:2] < alo.min(0)[:2]).any(): continue
            zb = Tb[:, :, 2].mean(1)
            for j in range(len(Ta)):
                za = Ta[j][:, 2].mean()
                m = (np.abs(zb - za) < CC.DZ) & (sb == sa[j]) & (blo[:, 0] < ahi[j][0]) & (bhi[:, 0] > alo[j][0]) & (blo[:, 1] < ahi[j][1]) & (bhi[:, 1] > alo[j][1])
                for k in np.nonzero(m)[0]:
                    if CC.overlap_area(Ta[j], Tb[k]) > 0.0: hits.append((a, b, [round(float(x), 2) for x in (alo[j] + ahi[j]) / 2]))
    seen = {}
    for a, b, at in hits: seen.setdefault((a, b), [0, at]); seen[(a, b)][0] += 1
    print(f'P2_CROSS {len(hits)} coplanar overlap(s) between drawables ({len(files)} drawables + slab)')
    for (a, b), (n, at) in sorted(seen.items(), key=lambda x: -x[1][0]): print(f'  {n:4d}  {a:22s} x {b:22s} e.g. {at}')
    if plant: return 0 if any('planted' in k for k in seen) else 1
    return 1 if hits else 0
if __name__ == '__main__':
    rc = 0
    if 'sweep' in sys.argv: rc |= sweep()
    if 'cross' in sys.argv:
        if '--plant' in sys.argv:
            if cross(plant=True): print('P2_CROSS NOT PROVEN: the planted overlap was not found'); sys.exit(1)
            print('P2_CROSS proven on the planted overlap')
        rc |= cross()
    print('P2_GATES_PASS' if rc == 0 else 'P2_GATES_FAIL'); sys.exit(rc)
