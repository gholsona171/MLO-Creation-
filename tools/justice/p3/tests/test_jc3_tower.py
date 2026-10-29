"""Pure-Python tests on the tower plan (area 2): py -3 -m pytest work/p3/tests -q"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jc3_tower as T, jc3_plan as P

def test_room_ids_contiguous_and_capped():
    ids = sorted(T.rooms().values()); assert ids == list(range(1, len(ids) + 1)) and ids[-1] <= 31

def test_levels_are_whole_risers():
    for a, b in zip(T.LV[:7], T.LV[1:7]): assert abs((b - a) / 0.2 - round((b - a) / 0.2)) < 1e-6

def _in_fin(line, bays):
    """a wall line meeting an outer wall lies between two bays (or past all of them), never inside one (+ its 0.1 half thickness)."""
    return all(not (a0 - 0.1 < line < a1 + 0.1) for a0, a1, _, _ in bays)

def test_partitions_meet_outer_walls_between_bays():
    for F in T.FLOORS.values():
        assert _in_fin(T.W_RING_V, T.bays('W', F)), 'west ring wall in a W bay'
        assert _in_fin(T.WIT_N, T.bays('W', F)), 'witness room wall in a W bay'
        for line in (T.RST_E, T.JURY_E, T.CHAMB_E): assert _in_fin(line, T.bays('N', F)), f'u {line} in an N bay'
        assert _in_fin(T.CONF_S, T.bays('E', F)), 'conference wall in an E bay'

def test_stair_flights():
    fl = T.flights(); assert len(fl) == 8
    for base, d, zb, zt, lane in fl: assert abs((zt - zb) - 1.8) < 1e-9 and round((zt - zb) / 0.2) == T.RISERS
    assert abs(fl[-1][3] - T.STAIR_TOP) < 1e-9
    assert abs((T.E_LAND - T.W_LAND) - (T.RISERS - 1) * T.GO) < 1e-9

def test_courtroom_fits_its_box_and_counts():
    fit = T.court_fittings('A')
    for u0, u1, v0, v1, z0, z1, *_ in fit['boxes']: assert T.CU0 - 1e-6 <= u0 and u1 <= T.CU1 + 1e-6 and T.CV0 - 1e-6 <= v0 and v1 <= T.CV1 + 1e-6
    assert len(fit['seats']) == 66, 'gallery seats'
    assert sum(1 for p in fit['props'] if p[0] == 'v_ilev_leath_chr') == 12, 'jurors'

def test_doors_have_portals_or_rooms():
    T.DOORS.clear(); T.OPENINGS.clear(); T.PORTALS.clear()
    for f in T.FLOORS: T.floor_plan(f)
    names = {p['door'] for p in T.PORTALS}
    for d in T.DOORS:
        if d['portal']: assert any(d['name'].startswith(n) for n in names)

def test_galleria_doorway_has_no_fin():
    for c in P.fins('tower_s'): assert all(not (a0 - 0.5 < c < a1 + 0.5) for a0, a1 in P.TOWER_DOORS)

def test_leaves_lie_in_their_openings():
    """every leaf's far end (hinge + 1.30 along its leaf direction) lies inside its opening (rig 2026-10-29: leaves turned into the wall)."""
    import math
    T.DOORS.clear(); T.OPENINGS.clear(); T.PORTALS.clear()
    for f in T.FLOORS: T.floor_plan(f)
    for d in T.DOORS:
        o = next(o for o in T.OPENINGS if d['name'].startswith(o['name']))
        t = math.radians(d['heading']); sg = 1.0 if d['model'] == T.GLASS_L else -1.0
        u, v = d['pos'][0] + sg * math.cos(t) * T.LEAF, d['pos'][1] + sg * math.sin(t) * T.LEAF
        a = v if o['axis'] == 'u' else u
        assert o['a0'] - 1e-6 <= a <= o['a1'] + 1e-6, d['name']


def test_door_lanes_clear_of_fittings():
    """a 0.7 m walking lane through the middle of every leaf, 1.5 m either side, misses every fitting box (pews, bar, cell benches) -
    proven on the old 4-seat east pew block (rig 2026-10-29: the walker stuck on its ends in the public door's leaf 0 lane)."""
    import math
    def lanes():
        T.DOORS.clear(); T.OPENINGS.clear(); T.PORTALS.clear()
        for f in T.FLOORS: T.floor_plan(f)
        for d in T.DOORS:
            t = math.radians(d['heading']); sg = 1.0 if d['model'] == T.GLASS_L else -1.0
            lu, lv = sg * math.cos(t), sg * math.sin(t); mu, mv = d['pos'][0] + lu * 0.65, d['pos'][1] + lv * 0.65
            nu, nv = abs(lv), abs(lu)                    # the lane's long axis (the wall normal)
            yield d['name'], (mu - nu * 1.5 - nv * 0.35, mu + nu * 1.5 + nv * 0.35, mv - nv * 1.5 - nu * 0.35, mv + nv * 1.5 + nu * 0.35)
    def hits(boxes):
        bad = []
        for name, (a0, a1, b0, b1) in lanes():
            for bx in boxes:
                if bx[4] < 1.8 and bx[5] > 0.1 and bx[0] < a1 and bx[1] > a0 and bx[2] < b1 and bx[3] > b0: bad.append(name); break
        return bad
    boxes = T.court_fittings('A')['boxes'] + T.sec_fittings('A')['boxes']
    assert not hits(boxes), hits(boxes)
    plant = [(28.4, 28.88, 23.25, 23.8, 0.0, 0.7, 'panel')]                 # the old east pew block's east end
    assert hits(plant), 'the lane check did not find the planted pew end'

def test_secure_lift_has_a_landing():
    """the secure lift's door opens onto a landing at least 1.5 m deep and as wide as the door, clear of the cell block and the fittings
    (rig 2026-10-29: the cells' wall stood 0.3 m off the lift door). Proven on the old wall line (25.8)."""
    cu0, cu1, cv0, cv1 = T.SEC_CAB; c = (cu0 + cu1) / 2; face = cv1 + 0.3
    def ok(cell_s): return cell_s - face >= 1.5
    assert ok(T.CELL_S), T.CELL_S
    assert not ok(25.8), 'the landing test did not find the old 0.3 m slot'
    for bx in T.sec_fittings('A')['boxes']:
        assert not (bx[0] < c + 0.65 and bx[1] > c - 0.65 and bx[2] < T.CELL_S and bx[3] > face), bx
