"""Vanilla models that reach INTO a lot from outside (Antonio 2026-10-23: Legion Square's sidewalk dt1_rd1_r1_10 showed through the
mall's entrance floor as a grey wedge with no collision). l0_maps.py swaps an entity only when its ORIGIN is inside a lot, and
l0_cut.py cuts only the models it is told to; a road / sidewalk / decal model centred on the street but spreading over a lot is
missed. Input: survey/near_entities.tsv (survey/near_entities.ps1). Lists every HD / orphan-HD entity whose origin is outside the
lots and whose rotated bounding box overlaps a lot polygon at ground height (z 20..45), and says whether the build already cuts it.
Run: py -3 lot_intruders.py   (exit 1 if an uncut ground model reaches into a lot)"""
import json, math, sys
from pathlib import Path
T = Path(__file__).resolve().parents[1]
POLYS = list(json.load(open(T / 'plan/lot_polys.json')).values())
CUT = set(json.load(open(T / 'work/l0_cut_result.json'))['cut'])
GROUND = ('_rd', 'rd1', 'road', 'ovly', 'kerb', 'decal', 'ground', 'pave', 'glue', 'plaza', 'sw')
def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def in_lots(x, y): return any(inside(p, x, y) for p in POLYS)
def corners(r):
    x, y, z, qx, qy, qz, qw = r[2:9]; lo, hi = r[10:13], r[13:16]
    yaw = -2 * math.atan2(qz, qw)                                  # ymap quaternions are stored conjugated (playbook: entity gotchas)
    c, s = math.cos(yaw), math.sin(yaw); out = []
    for fx in (0.0, 0.25, 0.5, 0.75, 1.0):                          # a 5 x 5 grid over the bounding box's footprint
        for fy in (0.0, 0.25, 0.5, 0.75, 1.0):
            lx, ly = lo[0] + (hi[0] - lo[0]) * fx, lo[1] + (hi[1] - lo[1]) * fy
            out.append((x + lx * c - ly * s, y + lx * s + ly * c))
    return out
rows = []
for line in open(T / 'survey/near_entities.tsv', encoding='utf-8'):
    f = line.rstrip('\n').split('\t')
    if len(f) < 16: continue
    rows.append([f[0], f[1]] + [float(v) for v in f[2:9]] + [f[9]] + [float(v) for v in f[10:16]])
seen, bad = set(), []
for r in rows:
    if r[9] not in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD') or in_lots(r[2], r[3]): continue
    if not (r[4] + r[12] < 45.0 and r[4] + r[15] > 20.0): continue
    hits = sum(in_lots(x, y) for x, y in corners(r))
    if not hits or (r[1], round(r[2], 1)) in seen: continue
    seen.add((r[1], round(r[2], 1)))
    ground = any(g in r[1] for g in GROUND)
    state = 'cut' if r[1] in CUT else ('UNCUT ground' if ground else 'uncut (prop / building - check)')
    if state == 'UNCUT ground': bad.append(r[1])
    print(f'{state:32s} {r[1]:34s} {r[0]:28s} at ({r[2]:.1f}, {r[3]:.1f}, {r[4]:.1f})  bbox points inside a lot: {hits}/25')
print('LOT_INTRUDERS', len(seen), 'reach in;', len(bad), 'uncut ground:', sorted(set(bad)))
sys.exit(1 if bad else 0)
