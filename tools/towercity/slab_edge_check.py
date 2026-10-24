"""Tower City check (offline, built files): the lot slab's drawn edge against the ground just outside it, all round both lots.
For every dense edge sample: the slab's top 0.10 m inside the edge vs the ground 0.25 m outside (lot_ground.py: our paving or
Rockstar's collision). Prints SLAB_EDGE with the worst steps and the count over 6 cm; fails (exit 1) on any step over 15 cm (a lone kerb crossing
lands between the two).
Run on the OLD slab first (a known defect: Alta St stood up to 1 m proud) to prove it catches it."""
import sys, json, math, numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); sys.path.insert(0, str(T / 'work'))
import lot_ground as LG, ext_plan as EP
slab = Path(sys.argv[1]) if len(sys.argv) > 1 else T / 'work/slab'
G = LG.Ground(); EDGE = json.load(open(T / 'plan/lot_edge_z.json')); bad = 0; rep = {}
def top(tri, x, y):
    best = None
    for (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) in tri:
        d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(d) < 1e-12: continue
        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d; b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d; c = 1 - a - b
        if min(a, b, c) >= -1e-9:
            z = a * z1 + b * z2 + c * z3; best = z if best is None else max(best, z)
    return best
for lot, raw in EDGE.items():
    t = np.load(slab / f'tris_tc_lot_{lot}.npy').astype(np.float64)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); t = t[np.abs(n[:, 2]) > 0.3 * np.linalg.norm(n, axis=1)]
    ref = LG.smooth(raw); ccw = LG.area(ref) > 0; steps = []
    for i in range(len(ref)):
        a, b = ref[i], ref[(i + 1) % len(ref)]; L = math.dist(a[:2], b[:2]); k = max(1, int(L / 1.0))
        dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = (dy, -dx) if ccw else (-dy, dx)
        for j in range(k):
            s = (j + 0.5) / k; x, y = a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1]); zr = a[2] + s * (b[2] - a[2])
            sel = t[(np.abs(t[:, :, 0].mean(1) - x) < 6) & (np.abs(t[:, :, 1].mean(1) - y) < 6)]
            zin = top(sel, x - nx * 0.10, y - ny * 0.10)
            ox, oy = x + nx * 0.25, y + ny * 0.25
            zo = LG.ours(ox, oy)
            if zo is None:
                c = [h for h in G.hits(ox, oy) if -LG.BAND_DOWN <= h - zr <= LG.BAND_UP]; zo = min(c) + 0.01 if c else None
            if zin is None or zo is None: continue
            u, v = EP.L(x, y) if lot == 'west' else (x, y)
            steps.append((round(zin - zo, 3), round(u, 1), round(v, 1)))
    worst = sorted(steps, key=lambda s: -abs(s[0]))[:8]; nb = sum(1 for s in steps if abs(s[0]) > 0.06); bad += sum(1 for s in steps if abs(s[0]) > 0.15)
    rep[lot] = {'samples': len(steps), 'over_6cm': nb, 'worst': worst}
print('SLAB_EDGE', json.dumps(rep))
sys.exit(1 if bad else 0)
