"""Justice Center v1: fit the REAL complex (OpenStreetMap footprints, survey/real/real_local.json) onto the whole sc1_19 block at
ONE uniform scale, by rotation + scale + translation only (no mirroring, no per-building moves).
For each rotation the largest scale is found by bisection; a scale is feasible when a translation exists that keeps every vertex
of the buildings `MARGIN_B` m and of the plaza `MARGIN_P` m inside the GTA kerb outline (convex: linear constraints, scipy linprog,
Chebyshev centre so the fit sits centred). Writes survey/v1_outlines.json (every v1 outline in the lot frame + world) - the one
source for plan_v1.py, section_v1.py and map_data_sheet.py."""
import json, math, os
import numpy as np
from scipy.optimize import linprog
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
site = json.load(open(os.path.join(SV, 'site.json')))
real = json.load(open(os.path.join(SV, 'real', 'real_local.json')))['features']
OX, OY = site['frame']['origin_world']; HG = math.radians(site['frame']['heading_deg'])
KERB = np.array(site['block']['kerb_outline_uv'], float)
MARGIN_B, MARGIN_P = 4.0, 3.0            # sidewalk kept round the buildings / plaza edge to the kerb
REAL = {  # role: OSM id (reference.md section 1.3)
    'complex_base': 'way/189749443', 'courts_tower': 'way/333533679', 'jail_1': 'way/354191885',
    'police_hq': 'way/122151929', 'jail_2': 'way/150720143', 'plaza': 'way/1416750951'}
P = {k: np.array(real[v]['xy'], float) for k, v in REAL.items()}
for k in P:
    if np.allclose(P[k][0], P[k][-1]): P[k] = P[k][:-1]
# Portal: no OSM node. Wikipedia: "at the northwestern end of this plaza" -> the plaza vertex furthest towards Lakeside Ave
# (the block's long axis, bearing 326 deg = direction (-0.559, 0.829)), pulled 6 m into the plaza. Estimated, not surveyed.
ax = np.array([-0.559, 0.829]); pl = P['plaza']; far = pl[np.argmax(pl @ ax)]
PORTAL = far + (pl.mean(0) - far) / np.linalg.norm(pl.mean(0) - far) * 6.0

# kerb half-planes n.x <= c (kerb is convex, counter-clockwise check)
k = KERB; area = sum(k[i - 1, 0] * k[i, 1] - k[i, 0] * k[i - 1, 1] for i in range(len(k)))
if area < 0: k = k[::-1]
HP = []
for i in range(len(k)):
    a, b = k[i], k[(i + 1) % len(k)]; e = b - a; n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
    HP.append((n, n @ a))


def place(theta, s, t):  # real local xy (east, north) -> lot frame uv: world rotation, then into the lot frame
    c, sn = math.cos(theta), math.sin(theta)
    R = np.array([[c, -sn], [sn, c]])
    return lambda xy: (np.asarray(xy) @ R.T) * s + t


def feasible(theta, s, push_se=False):
    f = place(theta, s, np.zeros(2))
    pts = [(f(P[n]), MARGIN_B) for n in ('complex_base', 'police_hq', 'jail_2')] + [(f(P['plaza']), MARGIN_P)]
    A, b = [], []
    for n, c in HP:
        for q, m in pts:
            A.append([n[0], n[1], 1.0]); b.append(c - m - (q @ n).max())   # n.t + r <= c - m - max n.q  (r = slack radius)
    # push_se: the real complex sits close to St Clair Ave with a deep lawn towards Lakeside Ave (real gaps along the long axis:
    # 13.8 m to St Clair's centre line, 32.8 m to Lakeside's), so put it against the SE kerb (Roy Lowenstein) and leave the
    # slanted NW part of the block (Davis Ave) as the Lakeside lawn and sloped walk.
    r = linprog([0, 1, 0] if push_se else [0, 0, -1], A_ub=A, b_ub=b, bounds=[(None, None), (None, None), (0, None)])
    return (r.status == 0, r.x[:2] if r.status == 0 else None, r.x[2] if r.status == 0 else None)


best = None
for deg in np.arange(-40, 41, 0.5):
    th = math.radians(deg)
    lo, hi = 0.3, 1.2
    if not feasible(th, lo)[0]: continue
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if feasible(th, mid)[0] else (lo, mid)
    if best is None or lo > best[1]: best = (deg, lo)
deg, smax = best
S = math.floor(smax * 100) / 100                      # round the scale down to 0.01
ok, t, slack = feasible(math.radians(deg), S, push_se=True)
f = place(math.radians(deg), S, t)
world = lambda uv: [(round(OX + u * math.cos(HG) - v * math.sin(HG), 2), round(OY + u * math.sin(HG) + v * math.cos(HG), 2)) for u, v in uv]
rnd = lambda a: [(round(float(x), 2), round(float(y), 2)) for x, y in a]
out = dict(source='OpenStreetMap (ODbL) via Overpass, survey/real/', method=__doc__.strip().splitlines()[0],
           rotation_deg_real_to_lot=deg, scale=S, max_scale=round(smax, 4), translation_uv=[round(float(x), 2) for x in t],
           spare_m=round(float(slack), 2), margins=dict(buildings=MARGIN_B, plaza=MARGIN_P), parts={})
for n, xy in P.items():
    uv = rnd(f(xy)); out['parts'][n] = dict(osm=REAL[n], uv=uv, world=world(uv), tags=real[REAL[n]]['tags'])
uv = rnd(f([PORTAL])); out['parts']['portal'] = dict(osm=None, uv=uv, world=world(uv), note='estimated: NW end of the Ontario St plaza (Wikipedia), 11 m tall')
# the real streets (centre lines) in the same transform, for the drawings
streets = {}
for kk, ft in real.items():
    if ft['kind'] == 'street' and ft['tags'].get('highway') in ('tertiary', 'primary', 'secondary') and ft['tags'].get('name'):
        streets.setdefault(ft['tags']['name'], []).append(rnd(f(ft['xy'])))
out['real_streets_uv'] = streets
json.dump(out, open(os.path.join(SV, 'v1_outlines.json'), 'w'), indent=1)
print('rotation %.1f deg  max scale %.4f  -> scale %.2f  translation %s  spare %.2f m' % (deg, smax, S, t.round(2), slack))
for n, p in out['parts'].items():
    a = np.array(p['uv']); print(n, 'u %.1f..%.1f  v %.1f..%.1f' % (a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()))
