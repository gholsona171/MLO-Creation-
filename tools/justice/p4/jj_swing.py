"""Door-swing gate: no walk route may run into a door's OPEN leaf (rig 2026-10-30: with every door shut, the upstairs walk stalled at the
foot of flight 1 - book_stair's hinge stood at the opening's east end, so the leaf the walker pushed open into the stair room lay along
+v across the stair's south lane, and the next leg walked straight into it. In the earlier run the door system held the doors open the
other way and the walk passed).
Each door's leaf, swung 90 deg to either side of its wall (a native door swings both ways), is a segment from the hinge; thickened by the
walker's body (0.30 m) it must not touch any other leg of a route that pushes that door open (on the side the walker went; the leaf's
last 0.30 m excepted - a tip is only nudged). Doors a route never crosses stay shut in their wall. Routes: jj_probe WALK (intake = the route probe's way, upstairs).
Proof: --plant puts book_stair's hinge back at the east end; the gate must find it.
Run: py -3 jj_swing.py [--plant]   -> JJ_SWING_PASS | JJ_SWING_FAIL (exit 1) | JJ_SWING_PLANT_FOUND"""
import math, sys
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
import jj_plan as J, jj_probe as P
BODY = 0.30
def seg_dist(a, b, c, d):
    """the shortest distance between 2D segments ab and cd."""
    def pd(p, q, r):
        qx, qy = r[0] - q[0], r[1] - q[1]; L2 = qx * qx + qy * qy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - q[0]) * qx + (p[1] - q[1]) * qy) / L2))
        return math.hypot(p[0] - q[0] - t * qx, p[1] - q[1] - t * qy)
    def cross(o, p, q): return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    if (cross(a, b, c) > 0) != (cross(a, b, d) > 0) and (cross(c, d, a) > 0) != (cross(c, d, b) > 0): return 0.0
    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))
def leaves(d):
    """(floor z, the two open-leaf segments, the closed leaf segment = the opening) of a door from its placement."""
    u, v, zc = d['pos']; h = math.radians(d['heading']); z = zc - J.LEAF_H / 2
    ax = (math.cos(h), math.sin(h)); n = (-ax[1], ax[0])                     # the leaf runs along the model's -x from the hinge
    closed = ((u, v), (u - J.LEAF * ax[0], v - J.LEAF * ax[1]))
    return z, [((u, v), (u + s * J.LEAF * n[0], v + s * J.LEAF * n[1])) for s in (1, -1)], closed
TIP = 0.30   # the last 0.30 m of a leaf: a walker passing the tip only nudges it (rig: intake legs past hold2's tip passed 20/20)
def check(doors):
    """for each route: the doors it pushes open (a leg crosses the opening), on the side the walker went; every OTHER leg of that route
    on that floor must keep the walker's body clear of that open leaf (hinge to tip less TIP)."""
    bad = []
    for name, pts in P.WALK.items():
        legs = [(pts[i - 1], pts[i]) for i in range(1, len(pts))]
        for d in doors:
            z, _, closed = leaves(d); u, v = closed[0]; h = math.radians(d['heading']); n = (-math.sin(h), math.cos(h))
            cross = [k for k, (a, b) in enumerate(legs) if min(a[2], b[2]) < z + 2.0 and max(a[2], b[2]) > z - 0.5 and seg_dist(a[:2], b[:2], *closed) == 0.0]
            sides = {1 if (legs[k][1][0] - u) * n[0] + (legs[k][1][1] - v) * n[1] > 0 else -1 for k in cross}
            for sd in sides:
                lf = ((u, v), (u + sd * (J.LEAF - TIP) * n[0], v + sd * (J.LEAF - TIP) * n[1]))
                for k, (a, b) in enumerate(legs):
                    if k in cross or max(a[2], b[2]) < z - 0.5 or min(a[2], b[2]) > z + 2.0: continue
                    g = seg_dist(a[:2], b[:2], *lf)
                    if g < BODY: bad.append(f'{name} leg {k + 1} {tuple(round(x, 2) for x in a[:2])}->{tuple(round(x, 2) for x in b[:2])} runs into the leaf of {d["name"]}, pushed open by the route (clear {g:.2f} m < {BODY})')
    return bad
if __name__ == '__main__':
    J.plan_doors(); doors = [dict(d) for d in J.DOORS]
    if '--plant' in sys.argv:
        d = next(d for d in doors if d['name'] == 'book_stair')
        d['pos'] = [-23.3 + J.JAMB + J.LEAF, d['pos'][1], d['pos'][2]]; d['heading'] = 0.0      # the old east-end hinge
        print('JJ_SWING_PLANT_FOUND' if any('book_stair' in e for e in check(doors)) else 'JJ_SWING_PLANT_MISSED'); sys.exit(0)
    bad = check(doors)
    for e in bad: print(' ', e)
    print(f'JJ_SWING_PASS {len(doors)} doors x {sum(len(p) - 1 for p in P.WALK.values())} walk legs' if not bad else f'JJ_SWING_FAIL {len(bad)}'); sys.exit(1 if bad else 0)
