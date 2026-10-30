"""Offline swept-path gate for the B1 garage drive (rig 2026-10-30: police3 and policet stopped at the IN turn, pressing the west wall -
the plan put the IN lane's centre line 0.8 m off the lining's face). The real vehicle footprint (jail's jj_plan.VEHICLES: width x
length, + MARGIN each side) is moved along the drive probe's own route (jc3_gdrive.route(): the same waypoints the rig drives, the car
centre on the polyline, heading = the travel direction, tail first on reverse legs) every STEP m, and tested against:
  * every built triangle of the garage rooms (pdeck, pramp_in, pramp_out) and the street (phase 2 police + site drawn, exterior
    collision, the lot slab) that is not a driving surface (near-horizontal faces at or under the floor there are skipped), whose height overlaps the body (floor + 0.15 .. floor +
    height - no roof margin: B1's lamps hang 2 cm over the 2.70 m van, the ceiling plate 8 cm - the floor taken where the obstacle stands; floor = B1 / the ramp profile / the street);
  * every placed prop in the garage rooms (its survey bounding box, turned by its heading, at its base);
  * the driveway bollards (p2_site.BOLLARDS, 0.25 m square).
Gated: jc3_pgarage.DRIVE_VEHICLES; any other vehicle's result is printed as INFO (not a pass / fail).
Proof: --plant puts a 0.6 m column on the route at the IN turn; it must be found. Run: py -3 jc3_drive_sweep.py [--plant]
Prints DRIVE_SWEEP_PASS / DRIVE_SWEEP_FAIL (per vehicle: hits with the route position, the thing hit and its source)."""
import json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.strtree import STRtree
from shapely import affinity
P3 = Path(__file__).resolve().parent; WK = P3.parent; sys.path[:0] = [str(P3), str(WK), str(WK / 'p2'), str(WK / 'jail')]
import jc_frame as F, jc3_pgarage as G, jc3_police as P
import jc3_gdrive as GD
STEP, MARGIN = 0.25, G.MARG
VEH = G.VEHICLES                                                            # width, length
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def floor_z(u, v):
    """the driving surface at lot (u, v): the street east of the face, a ramp lane between the foot and the face, B1 elsewhere."""
    if u > P.EI: return G.ZD
    if u >= G.U_FOOT and G.TRENCH[0] <= v <= G.TRENCH[1]: return G.ramp_z(u)
    return G.ZB
def obstacles(plant=False):
    """[(polygon, z0, z1, label)] in the lot frame."""
    out = []
    src = {n: P3 / f'out/tris_jc_courts_{n}.npy' for n in ('pdeck', 'pramp_in', 'pramp_out')}
    src.update({'p2 police': WK / 'p2/out/tris_jc_police.npy', 'p2 site': WK / 'p2/out/tris_jc_site.npy',
                'p2 ext collision': WK / 'p2/out/coltris_jc_ext_col.npy', 'lot slab': WK / 'slab/tris_jc_lot.npy'})
    for name, f in src.items():
        T = lot(np.load(f).astype(np.float64)); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        c = T.mean(1); fz = np.array([floor_z(u, v) for u, v in c[:, :2]])
        floorish = (np.abs(n[:, 2]) > 0.9) & (T[..., 2].max(1) < fz + 0.2)      # driving surfaces (either winding): never an obstacle
        keep = ~floorish & (c[:, 0] > 9.0) & (c[:, 0] < 70.0) & (c[:, 1] > -62.0) & (c[:, 1] < -5.0)
        for t in T[keep]:
            pg = Polygon(t[:, :2])
            if not pg.is_valid or pg.area < 1e-6: pg = pg.buffer(0.01)                # a vertical face: a sliver
            out.append((pg, t[:, 2].min(), t[:, 2].max(), name))
    S = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
    fv = lambda s_: [float(x[2:]) for x in s_.split()]
    L = json.load(open(P3 / 'out/jc3_layout.json'))
    for q in L['placed']:
        if q['room'] not in ('pdeck', 'pramp_in', 'pramp_out') or q['model'].lower() not in S: continue
        a = S[q['model'].lower()]; lo, hi = fv(a['bbMin']), fv(a['bbMax'])
        pg = affinity.translate(affinity.rotate(box(lo[0], lo[1], hi[0], hi[1]), q['heading'], origin=(0, 0)), q['u'], q['v'])
        out.append((pg, q['base'] + lo[2], q['base'] + hi[2], 'prop ' + q['model']))
    import p2_site as SITE
    for u, v in SITE.BOLLARDS: out.append((box(u - 0.125, v - 0.125, u + 0.125, v + 0.125), G.ZD, G.ZD + 1.0, 'bollard'))
    if plant:
        u, v = G.IN_X + G.UT_R - G.UT_R * math.sin(math.pi / 4), G.IN_C + G.UT_R - G.UT_R * math.cos(math.pi / 4)
        out.append((box(u - 0.3, v - 0.3, u + 0.3, v + 0.3), G.ZB, G.ZB + 2.6, 'PLANT'))
    return out
def poses(pts):
    """car centre + heading (radians, lot frame) every STEP m along the route; reverse legs point the nose against the travel (the probe
    turns the body about its centre, so the body centre is on the route)."""
    out = []
    for (u0, v0, _), (u1, v1, spd) in zip(pts, pts[1:]):
        d = math.hypot(u1 - u0, v1 - v0)
        assert d > 1e-6, f'the route repeats a waypoint at ({u0:.2f}, {v0:.2f})'
        a = math.atan2(v1 - v0, u1 - u0) + (math.pi if spd < 0 else 0.0)
        for k in range(max(1, int(d / STEP))): t = k * STEP / d; out.append((u0 + (u1 - u0) * t, v0 + (v1 - v0) * t, a))
    return out
HEIGHT = {'police3': 1.60, 'policet': 2.70}                                # jj_plan.VEHICLES heights (police3 = police4's)
def sweep(model, obs, tree, route):
    w, l = VEH[model]; h = HEIGHT[model]; hits = {}
    for u, v, a in poses(route):
        fp = affinity.translate(affinity.rotate(box(-l / 2 - MARGIN, -w / 2 - MARGIN, l / 2 + MARGIN, w / 2 + MARGIN), a, origin=(0, 0), use_radians=True), u, v)
        for i in tree.query(fp):
            pg, z0, z1, lab = obs[i]
            if not fp.intersects(pg): continue
            q = fp.intersection(pg).representative_point(); fz = floor_z(q.x, q.y)   # the floor where the body meets the obstacle (a 6 m
            if z1 < fz + 0.15 or z0 >= fz + h: continue                                # body spans 0.9 m of a 1:7 ramp; a ceiling spans rooms)
            key = (lab, round(pg.centroid.x, 1), round(pg.centroid.y, 1))
            hits.setdefault(key, (round(u, 2), round(v, 2), round(math.degrees(a) % 360, 1)))
    return hits
def main():
    plant = '--plant' in sys.argv; obs = obstacles(plant); tree = STRtree([o[0] for o in obs]); bad = 0
    for m in VEH:
        hits = sweep(m, obs, tree, G.loop_route())
        if plant:
            assert any(k[0] == 'PLANT' for k in hits), f'{m}: the planted column on the IN turn was not found - the sweep is broken'
            continue
        gated = m in G.DRIVE_VEHICLES; print(f'{"" if gated else "INFO (not gated) "}{m} ({VEH[m][0]} x {VEH[m][1]} m + {MARGIN}): {len(hits)} hit(s)')
        bad += len(hits) if gated else 0
        for (lab, x, y), at in list(hits.items())[:12]: print(f'   {lab:28s} at ({x}, {y})  car at u, v, heading {at}')
    if plant: print('DRIVE_SWEEP_PLANT_FOUND'); return 0
    print('DRIVE_SWEEP_PASS' if not bad else 'DRIVE_SWEEP_FAIL'); return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
