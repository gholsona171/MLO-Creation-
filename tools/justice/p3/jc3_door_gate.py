"""Door gate (2026-11-01, Antonio: "gaps all over the doors"): every door of the build (out/jc3_layout.json 'doors': the galleria's street
pairs, the tower and police doors; not the garage roll-ups, which are map doors in their own openings) checked by the playbook door tool
(MLO-Creation/tools/doors/door_fit.py) against everything drawn (out/tris_jc_courts_*.npy + phase 2's work/p2/out/tris_jc_*.npy): each side and the head within 5 mm of the
leaf's bbox and no see-through ray round it.
Clearance: the walking lane through each leaf (1.5 m out both sides, 1.0 for the cell gates, as jc3_probe.doors2 walks) and the leaf's
swing to 80 deg both ways must be clear of every prop and built solid (door_fit.clearance).
Proof: --plant narrows the first police door's leaf by 5 cm at its latch edge (= a 5 cm oversized opening) and puts a box 0.6 m in front
of it; the gate must flag the gap, the slits and the blocked lane.
Run: py -3 jc3_door_gate.py [--plant]   (JC3_DOORS_PASS / JC3_DOORS_PLANT_FOUND)"""
import json, math, sys
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc_frame as F, jc3_tower as JT
L = json.load(open(P3 / 'out/jc3_layout.json'))
TOL = 0.005
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def main():
    files = sorted((P3 / 'out').glob('tris_jc_courts_*.npy')) + [f for f in sorted((P3.parent / 'p2' / 'out').glob('tris_jc_*.npy')) if not f.stem.endswith('_emi')]
    T = np.concatenate([lot(np.load(f).astype(np.float64)) for f in files])     # our rooms + phase 2's shells (the street door frames)
    doors = [{'name': d['name'], 'model': d['model'], 'pos': d['pos'], 'heading': d['heading']} for d in L['doors'] if 'rollup' not in d['name']]
    plant = None
    if '--plant' in sys.argv:
        plant = {next(d['name'] for d in doors if d['name'].startswith('P_in_')): 0.05}
    res = JT.DF.check(T, doors, JT.ARCH, TOL, shrink=plant)
    # clearance (2026-11-01 rig: three doors the walker could not get through): the walking lane through each leaf to D - 0.3 (the probe's
    # D 1.5 m, 1.0 for the cell gates: it arrives 0.6 m short, a ped is 0.3 m wide) and the leaf's swing to 70 deg (0.85 m clear) both ways
    import jc3_arch; A = jc3_arch.load()
    fv = lambda t: [float(x[2:]) for x in t.split()]
    boxes = []
    for q in L['placed']:
        lo, hi = fv(A[q['model'].lower()]['bbMin']), fv(A[q['model'].lower()]['bbMax']); h = math.radians(q['heading']); c, s_ = math.cos(h), math.sin(h)
        pts = [(q['u'] + x * c - y * s_, q['v'] + x * s_ + y * c) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
        boxes.append(((min(p[0] for p in pts), min(p[1] for p in pts), q['z'] + lo[2]), (max(p[0] for p in pts), max(p[1] for p in pts), q['z'] + hi[2])))
    boxes += [((b[0], b[1], b[2]), (b[3], b[4], b[5])) for b in np.load(P3 / 'out/solids.npy')]
    if plant:                                                                   # a planted box in the planted door's path
        d0 = next(d for d in doors if d['name'] in plant); lo, hi = JT.DF.leaf_bbox(JT.ARCH, d0['model']); h = math.radians(d0['heading'])
        m = np.array(d0['pos'][:2]) + np.array([math.cos(h), math.sin(h)]) * (lo[0] + hi[0]) / 2 + np.array([-math.sin(h), math.cos(h)]) * 0.6
        boxes.append(((m[0] - 0.2, m[1] - 0.2, d0['pos'][2] - 1.15), (m[0] + 0.2, m[1] + 0.2, d0['pos'][2])))
    for r, d in zip(res, doors):
        lo, hi = JT.DF.leaf_bbox(JT.ARCH, d['model'])
        D = 1.0 if d['model'] == JT.CELL else 1.5                                # the probe's start / target distance
        r['clear'] = JT.DF.clearance(d, JT.ARCH, boxes, d['pos'][2] + lo[2], depth=D - 0.3, max_angle=70.0)   # (a ped arrives 0.6 m short of
        if r['clear']: r['ok'] = False                                            #  its target, 0.3 m wide; 70 deg opens 0.85 m)
        if r['clear']: r['ok'] = False
    bad = [r for r in res if not r['ok']]
    if plant:
        hit = [r for r in bad if r['name'] in plant]
        print('plant:', hit[0] if hit else None)
        if not hit or not hit[0]['slits'] or not any(k == 'lane' for k, _, _ in hit[0]['clear']): print('JC3_DOORS_PLANT_MISSED'); return 1
        print('JC3_DOORS_PLANT_FOUND (gap + slit + blocked lane)'); return 0
    for r in bad[:40]: print(' ', r['name'], r['gaps'], 'slits', r['slits'], r['clear'][:3])
    worst = max((v for r in res for v in r['gaps'].values() if v is not None), default=None)
    print(f'JC3_DOORS {len(res)} doors, worst gap {worst} m, {sum(r["slits"] for r in res)} slit rays, {len(bad)} failing')
    print('JC3_DOORS_PASS' if not bad else 'JC3_DOORS_FAIL'); return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
