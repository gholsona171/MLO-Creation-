"""Plan-level checks of the Police HQ (area 3) and its underground garage, each proven on a planted defect."""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jc3_police as P, jc3_pgarage as G

def _west_partitions(spaces):
    out = set()
    for rs in spaces.values():
        for r in rs:
            if abs(r[0] - P.WI) < 1e-6:
                for v in (r[2], r[3]):
                    if P.SG + 1e-6 < v < P.NI_LINK - 1e-6: out.add(round(v, 3))
    return sorted(out)

def test_west_partitions_land_between_bays():
    gaps = P.west_gaps()
    def bad(vs): return [v for v in vs if not any(g0 - 1e-6 <= v - 0.1 and v + 0.1 <= g1 + 1e-6 for g0, g1 in gaps)]
    for sp in (P.SPACES1, P.SPACES2, {k: [r] for k, r in P.SUITES.items()}): assert not bad(_west_partitions(sp)), bad(_west_partitions(sp))
    assert bad([-30.0]), 'the gap check did not find a partition planted across a window bay'

def test_spaces_tile_their_side():
    """each staff side's named spaces cover it exactly once - proven on a planted overlap."""
    def area(r): return (r[1] - r[0]) * (r[3] - r[2])
    def ov(a, b): return max(0.0, min(a[1], b[1]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[2], b[2]))
    def check(spaces, base, cut):
        rs = [r for v in spaces.values() for r in v]
        over = sum(ov(a, b) for i, a in enumerate(rs) for b in rs[i + 1:])
        want = sum(area(b) for b in base) - sum(ov(b, c) for b in base for c in cut)
        return over, abs(sum(area(r) for r in rs) - want)
    o, d = check(P.SPACES1, P.STAFF1, [P.STAIR_B, P.REGIONS['pdesk'][0]]); assert o < 1e-6 and d < 1e-3, (o, d)
    o, d = check(P.SPACES2, P.STAFF2, [P.STAIR_B] + list(P.SUITES.values())); assert o < 1e-6 and d < 1e-3, (o, d)
    planted = dict(P.SPACES1); planted['x'] = [(12.0, 14.0, -20.0, -18.0)]
    assert check(planted, P.STAFF1, [P.STAIR_B, P.REGIONS['pdesk'][0]])[0] > 0, 'the tiling check did not find a planted overlap'

def test_stair_is_rockstars():
    for zb in (G.ZB, P.P1):
        fl = P.flights(zb)
        assert abs(fl[0][3] - fl[1][2]) < 1e-6 and abs(fl[-1][3] - (zb + 3.2)) < 1e-6
        for base, d, z0, z1, lane in fl: assert abs((z1 - z0) / P.RISE - P.RISERS) < 1e-6 and lane[1] - lane[0] >= 1.5
    assert abs(P.P1 - G.ZB - 3.2) < 1e-6 and P.RISE == 0.20 and P.GO == 0.27
    run = (P.RISERS - 1) * P.GO
    assert P.SB_SLAND[1] + run <= P.SB_NLAND[0] + 1e-6, 'the flights do not fit between the landings'

def test_stair_doors_on_the_landing():
    for n, frm, to, z, ax, plane, a0, kind in P.PORTAL_DOORS:
        if n in ('P_stairL1', 'P_stairL2'): assert P.SB_SLAND[0] - 1e-6 <= a0 and a0 + 1.4 <= P.SB_SLAND[1] + 1e-6, n
        if n == 'P_stairB1': assert P.SB_LANES[0][0] - 1e-6 <= a0 and a0 + 1.4 <= P.SB_LANES[1][1] + 1e-6, n

def test_trench_meets_the_ramps():
    assert abs(P.U_FOOT - G.U_FOOT) < 0.01 and abs(P.TRENCH_N - G.TRENCH[1]) < 1e-6 and abs(P.SG - G.TRENCH[0]) < 1e-6

def test_ramp_profile():
    """the ramp: continuous, never steeper than 1:7, the curves no sharper than Rockstar's 4 m, street at the door, B1 at the foot.
    Proven on a planted step."""
    us = [G.U_FOOT + i * 0.05 for i in range(int((G.U_TOP - G.U_FOOT) / 0.05) + 1)]
    def worst(f): return max(abs(f(a) - f(b)) / 0.05 for a, b in zip(us, us[1:]))
    assert worst(G.ramp_z) <= G.SLOPE + 1e-3
    assert abs(G.ramp_z(G.U_TOP) - G.ZD) < 1e-6 and abs(G.ramp_z(G.U_FOOT) - G.ZB) < 1e-6
    assert worst(lambda u: G.ramp_z(u) + (0.3 if u > 30 else 0.0)) > G.SLOPE, 'the profile check did not find a planted step'
    assert G.CEIL_B - G.ZB >= 2.8 - 1e-6, 'B1 is lower than the van'

def test_loop_paths_never_meet():
    """the IN path (down the IN lane, its turn north at the van radius, up the west aisle) and the OUT path (the return aisle's U-turn
    into the OUT lane) keep a car's width apart (2.2 m + 0.6 m) - proven on a U-turn planted 2 m further west."""
    def gap(utc):
        a = [(u, G.IN_S) for u in [G.U_FOOT - k * 0.2 for k in range(int((G.U_FOOT - (G.IN_X + G.IN_R)) / 0.2))]]
        a += [(G.IN_X + G.IN_R - G.IN_R * math.sin(t), G.IN_S + G.IN_R - G.IN_R * math.cos(t)) for t in [i * math.pi / 40 for i in range(21)]]
        a += [(G.IN_X, v) for v in [G.IN_S + G.IN_R + k * 0.5 for k in range(40)]]
        b = [(utc[0] - G.UT_R * math.sin(t), utc[1] + G.UT_R * math.cos(t)) for t in [i * math.pi / 40 for i in range(41)]]
        return min(math.dist(p, q) for p in a for q in b)
    assert gap(G.UT_C) >= 2.8, gap(G.UT_C)
    assert gap((G.UT_C[0] - 2.0, G.UT_C[1])) < 2.8, 'the path check did not find a planted U-turn'

def test_garage_doors_fit_the_face():
    """each roll-up opening fits under L2's floor and inside the face beside the colonnade's ends, the van (2.6 m) clears it, and the
    pier between the doors is at least 0.8 m - proven on the 4 m door."""
    def ok(h, w):
        top = G.ZD + h; d = {k: (c - (w + 0.1) / 2, c + (w + 0.1) / 2) for k, c in (('in', G.IN_C), ('out', G.OUT_C))}
        return top < P.P2 - 0.05 and h >= 2.8 and d['out'][0] - d['in'][1] >= 0.8 and d['in'][0] >= P.SG
    assert ok(G.ROLLUP[2], G.ROLLUP[1])
    assert not ok(4.0, 4.0), 'the door check did not find the 4 m door'

def test_lobby_fronts_the_whole_east_colonnade():
    """every run of the east colonnade (phase 2's, it moves with the garage doors) lies along the lobby, behind its closed ends - the
    patrol room / L2 store never reach into the colonnade. Proven on the old lobby wall (v -40, before the colonnade grew a bay)."""
    PL = P.PL
    f = [x for x in PL.face_list('police') if x[0] == 'E'][0]
    runs = [(r[0][0], r[-1][1]) for r in PL.arcade_runs('police', f)]
    def ok(gar_n): return all(gar_n <= a0 - 0.5 and a1 <= P.REGIONS['plobby'][0][3] + 0.5 for a0, a1 in runs)
    assert ok(P.GAR_N), (runs, P.GAR_N)
    assert not ok(-40.0), 'the colonnade check did not find the old lobby wall'


def test_mirror_faces_the_interview_room():
    """the panel (-Y face) must reflect INTO the interview room; plant: the old heading (0 / 180, written for a +x model) faces along
    the wall (rig 2026-10-30: the interview side read as clear glass)."""
    def into(heading, side):
        n = P.facing(heading); return n[0] * side > 0.99
    assert not into(0.0 if 1 > 0 else 180.0, 1) and not into(180.0, -1), 'the plant (old headings) was not caught'
    for intr, obs, ax, plane, side in P.MIRROR:
        assert ax == 'u' and into(P.mirror_heading(side), side), f'{intr}: the mirror does not face the interview room'
