"""Pure-Python tests on the phase 3 plan tables (no Blender): py -3 -m pytest work/p3/tests -q"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jc3_plan as P

def test_room_ids():
    ids = sorted(P.ROOMS.values()); assert ids == list(range(1, len(ids) + 1)) and ids[-1] <= 31

def test_timecycles_lower_case():
    assert all(t == t.lower() for t in P.TCYC.values())

def test_doors_fill_their_openings():
    for k in P.ENTRANCES:
        s0, s1 = P.entrance_span(k); ls = [d for d in P.doors() if d[0].startswith(k)]
        l, r = ls; assert l[1] == P.DOOR_L and r[1] == P.DOOR_R
        assert abs((l[3] + P.LEAF_W) - (r[3] - P.LEAF_W)) < 1e-6, 'the two leaves meet in the middle'
        jamb = l[3] - s0; assert 0.1 <= jamb <= 0.2 and abs((s1 - r[3]) - jamb) < 1e-6
        assert abs(P.DOOR_TOP - P.G - (P.LEAF_H + 0.10)) < 1e-9

def test_openings_on_bay_edges():
    edges = {round(x, 6) for b in P.E_BAYS for x in b}
    for _, _, s0, s1, _, _ in P.door_openings(): assert round(s0, 6) in edges and round(s1, 6) in edges

def test_portals_point_out_of_the_room():
    for a, b, kind, p in P.portals():
        assert b == 'limbo'
        if p[0] == 'z': assert p[4] == 1 and abs(p[1] - P.PORTAL_Z) < 1e-9
        elif p[0] == 'u': assert (p[1] >= P.UA1 - 1e-9 and p[6] == 1)
        else: assert (p[1] <= P.VA0 + 1e-9 and p[6] == -1) or (p[1] >= P.VB1 - 1e-9 and p[6] == 1)

def test_roof_portal_under_the_beams():
    assert P.PORTAL_Z < P.ROOF - 0.5 and P.PORTAL_Z > P.ROOF - 0.6

def test_screen_line_closed():
    """the screen runs + the gaps cover the whole width; gaps never overlap (a belt / detector / exit lane per gap)."""
    g = P.screen_gaps()
    for (a0, a1), (b0, b1) in zip(g, g[1:]): assert a1 <= b0 + 1e-9
    covered = sorted(P.screen_runs() + g); x = P.VA0
    for a0, a1 in covered: assert abs(a0 - x) < 1e-9; x = a1
    assert abs(x - P.VA1) < 1e-9

def test_queue_clear_of_door_swings():
    """rope chains stay outside a 1.5 m radius of every hinge (leaves swing both ways)."""
    for u, v, h, n in P.QUEUE:
        du, dv = math.cos(math.radians(h)), math.sin(math.radians(h))
        for i in range(n + 1):
            pu, pv = u + du * P.ROPE_L * i, v + dv * P.ROPE_L * i
            for _, _, du_, dv_, _, _ in P.doors(): assert math.hypot(pu - du_, pv - dv_) > 1.5
            assert P.SCREEN_U + 0.5 < pu < P.UA1 - 0.3 and P.VA0 < pv < P.VA1

def test_fins_avoid_reserved_doors():
    for k, (w, a0, a1, *_ ) in P.RESERVED.items():
        assert all(not (a0 - 0.3 < c < a1 + 0.3) for c in P.fins(w))

def test_seats():
    pts = P.seat_points(P.BENCH, 0.0, 0.0, P.G, 0.0)
    assert len(pts) == 5 and all(0.40 <= p[2] - P.G <= 0.50 for p in pts)
    assert all(abs(p[3] - 180.0) < 1e-9 for p in pts), 'a bench at heading 0 seats face -v (GTA heading 180)'

def test_perimeter_collision_leaves_the_doors_open():
    for _, _, s0, s1, z0, z1 in P.door_openings():
        mid = (s0 + s1) / 2
        for lo, hi in P.perimeter_col():
            if lo[0] >= P.UA1 - 1e-6 and lo[1] < mid < hi[1]: assert lo[2] >= z1 - 1e-6
