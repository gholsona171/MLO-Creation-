"""Tower City survey: the vanilla features we KEEP WHOLE that stand partly inside a lot (Antonio 2026-10-24: knee-deep in the Power St
planters' lawn, waist-deep beside their wall). Their drawables are never cut (entity outside the lot), but the lot cut took their
collision inside the lot - so you sank into what you see. Lists each kept model's triangles (world) that reach into a lot / our
footprints (+0.5 m); ext_plan.py turns them into 'keep_col' rules and l0_col.py protects the collision faces on them from every cut.
Input: work/xml_ground/drawn_vanilla.npz (tools/drawn_dump.py: every drawn vanilla model round the lots, placed like the game).
Run: py -3 tools/kept_features.py  -> survey/kept_features.json"""
import json, re, sys, numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity')
KEEP = r'^dt1_11_(dt1_planter|hge_r2|hge_r2_d)$|^dt1_rd1_fwy0[25]$'   # planters, their hedges, the off-ramp, the deck's piers
ZMAX = {'dt1_rd1_fwy02': 40.8}                  # the deck itself: only its piers (under the cap beams) - the deck we reshape (C rules), and its
                                                # kept faces would protect collision those rules cut
Z = np.load(T / 'work/xml_ground/drawn_vanilla.npz'); tr = Z['tris'].astype(np.float64); mid = Z['mid']; names = [str(n) for n in Z['names']]
P = list(json.load(open(T / 'plan/lot_polys.json')).values()) + [q for v in json.load(open(T / 'plan/footprint_cuts.json')).values() for q in v]
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def near(x, y, d=0.5): return any(inside(q, x + dx, y + dy) for q in P for dx in (-d, 0, d) for dy in (-d, 0, d))
out = {}
for k in range(len(tr)):
    n = names[mid[k]]
    if not re.search(KEEP, n): continue
    t = tr[k]
    if t[:, 2].max() < 20 or t[:, 2].min() > 60 or t[:, 2].max() > ZMAX.get(n, 99.0): continue
    if any(near(p[0], p[1]) for p in t): out.setdefault(n, []).append([[round(float(c), 3) for c in p] for p in t])
assert out, 'no kept feature reaches a lot - nothing surveyed'
json.dump(out, open(T / 'survey/kept_features.json', 'w'))
print('KEPT_FEATURES', json.dumps({k: len(v) for k, v in out.items()}))
