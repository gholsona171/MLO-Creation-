"""Door fitting the way Rockstar does it (measured in Mission Row, v_policehub / v_20_policedlc_shell, 2026-11-01): the shell's opening is
the leaf's bounding box - jamb faces on the hinge and latch edges of the leaf's bbox, the head face on its top, the floor under its bottom
(0 mm, +-2 mm). Our first openings were leaf + 5 cm a side + 10 cm over the head: a visible slit round every door.

Library (pure Python + numpy, no Blender):
  leaf_bbox(arch, model)                          -> (lo, hi) of the leaf in model space (arch_ytyp.json from find_arch_ytyp.ps1)
  fit_single(lo, hi, a0, z, clearance=0.0)         -> {'a0','a1','z0','z1','hinge','zc','sense'}: the opening starting at a0 along the wall,
                                                      the hinge at the end the model's pivot sits on, the pivot height that stands the
                                                      leaf on the floor z
  fit_pair(lo1, hi1, lo2, hi2, a0, z, clearance)   -> the same for a double door (leaf 1 hinged at a0, leaf 2 at a1, meeting in the middle)
  fillers(opening, leaves_a0, leaves_a1, z_top)    -> frame pieces that close an opening you cannot cut to size (a curtain-wall bay,
                                                      another phase's facade hole) down to the leaves: [(a0, a1, z0, z1)] along the wall
  casing(op, face, side, width=0.07, proud=0.055)  -> [(n0, n1, a0, a1, z0, z1)]: a casing (architrave) round the opening on one wall face
Gate:
  check(tris, doors, arch, tol=0.005, shrink=None) -> one finding per door: side / head gaps and see-through slits; ok = every gap <= tol
                                                      and no slit
     tris  : (N, 3, 3) triangles of everything drawn round the doors, in the doors' frame
     doors : [{'name', 'model', 'pos': (x, y, z) of the pivot, 'heading': degrees (the model's +x -> (cos h, sin h))}]
  Rays: 5 points along each side and the head, 2 / 5 / 10 / 20 / 40 mm outside the leaf's bbox, shot through the wall (along the leaf's
  normal, +-0.6 m): a ray that meets nothing is a see-through slit, unless it runs inside a solid (a perpendicular wall: an odd count of
  faces above the point). A gap = the distance from the leaf's edge to the first face met along
  the wall at mid-edge, 12 mm either side of the leaf's mid plane (two rooms' linings meet on it). The other leaves of the list are solid
  (a pair's meeting edge). shrink={name: m} narrows that leaf at its latch edge: the planted-defect proof.
  clearance(dr, arch, boxes, floor_z, depth=1.5) -> the walking lane through the leaf and the leaf's swing (to 80 deg) both ways,
                                                      against props' AABBs and solids: [(lane|swing, side, point)]
CLI: py -3 door_fit.py   (fits gendoor005 into a test wall, proves the gate on a planted 5 cm opening and the clearance check on a
     planted box in the door's path: DOOR_FIT_PROVEN)
See docs/06-doors-lifts.md, "Door openings and frames"."""
import math
import numpy as np


def leaf_bbox(arch, model):
    a = arch[model.lower()]
    f = lambda s: [float(x[2:]) for x in s.split()]
    return f(a['bbMin']), f(a['bbMax'])


def fit_single(lo, hi, a0, z, clearance=0.0):
    w = hi[0] - lo[0]
    a1 = a0 + w + 2 * clearance
    pivot_end = 'a1' if abs(hi[0]) < abs(lo[0]) else 'a0'                 # the pivot (x = 0) sits on the leaf's hinge edge
    hinge = a1 - clearance if pivot_end == 'a1' else a0 + clearance
    return {'a0': a0, 'a1': a1, 'z0': z, 'z1': z + (hi[2] - lo[2]) + clearance, 'hinge': hinge, 'zc': z - lo[2], 'sense': pivot_end}


def fit_pair(lo1, hi1, lo2, hi2, a0, z, clearance=0.0):
    w1, w2 = hi1[0] - lo1[0], hi2[0] - lo2[0]
    a1 = a0 + w1 + w2 + 2 * clearance
    return {'a0': a0, 'a1': a1, 'z0': z, 'z1': z + max(hi1[2] - lo1[2], hi2[2] - lo2[2]) + clearance,
            'hinges': (a0 + clearance, a1 - clearance), 'zc': (z - lo1[2], z - lo2[2])}


def fillers(op, la0, la1, z_top):
    out = []
    if la0 - op['a0'] > 1e-4:
        out.append((op['a0'], la0, op['z0'], op['z1']))
    if op['a1'] - la1 > 1e-4:
        out.append((la1, op['a1'], op['z0'], op['z1']))
    if op['z1'] - z_top > 1e-4:
        out.append((la0, la1, z_top, op['z1']))
    return out


def casing(op, face, side, width=0.07, proud=0.055):
    n0, n1 = (face, face + proud) if side > 0 else (face - proud, face)
    a0, a1, z0, z1 = op['a0'], op['a1'], op['z0'], op['z1']
    return [(n0, n1, a0 - width, a0, z0, z1 + width), (n0, n1, a1, a1 + width, z0, z1 + width), (n0, n1, a0, a1, z1, z1 + width)]


def _hit(T, p, d, maxd):
    if not len(T):
        return None
    e1 = T[:, 1] - T[:, 0]
    e2 = T[:, 2] - T[:, 0]
    h = np.cross(d, e2)
    a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = p - T[:, 0]
    u = f * (s * h).sum(1)
    q = np.cross(s, e1)
    v = f * (q * d).sum(1)
    t = f * (q * e2).sum(1)
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 0) & (t < maxd)
    return float(t[m].min()) if m.any() else None


def _inside(T, p, X):
    """p inside a wall that runs along the slit ray (a perpendicular wall beside the hinge): faces within 0.3 m both ways along the door's
    wall direction X. (A real slit beside a leaf has the jamb one way and the open leaf space the other.) Counting faces above the point
    broke on single-sided surfaces (roofs, decals)."""
    return _hit(T, p, X, 0.3) is not None and _hit(T, p, -X, 0.3) is not None


def leaf_tris(arch, dr):
    """a door leaf's bbox as triangles in the doors' frame (the other leaf of a pair is solid for this one's meeting edge)."""
    lo, hi = leaf_bbox(arch, dr['model'])
    h = math.radians(dr['heading'])
    R = np.array([[math.cos(h), -math.sin(h), 0.0], [math.sin(h), math.cos(h), 0.0], [0.0, 0.0, 1.0]])
    return _box_tris(lo, hi) @ R.T + np.array(dr['pos'], np.float64)


def check(tris, doors, arch, tol=0.005, shrink=None):
    T0 = np.asarray(tris, np.float64)
    leaves = {dr['name']: leaf_tris(arch, dr) for dr in doors}
    out = []
    for dr in doors:
        P_ = np.array(dr['pos'], np.float64)
        mates = [v for k, v in leaves.items() if k != dr['name'] and np.linalg.norm(v.mean((0, 1)) - P_) < 4.0]
        T = np.concatenate([T0] + mates) if mates else T0
        C = T.mean(1)
        lo, hi = (list(x) for x in leaf_bbox(arch, dr['model']))
        if shrink and dr['name'] in shrink:
            d = shrink[dr['name']]
            if abs(hi[0]) < abs(lo[0]):
                lo[0] += d                                                    # the latch edge is the far one from the pivot
            else:
                hi[0] -= d
        h = math.radians(dr['heading'])
        X = np.array([math.cos(h), math.sin(h), 0.0])
        Y = np.array([-math.sin(h), math.cos(h), 0.0])
        Z = np.array([0.0, 0.0, 1.0])
        P0 = np.array(dr['pos'], np.float64)

        def W(x, y, z):
            return P0 + X * x + Y * y + Z * z
        lo_, hi_ = T.min(1), T.max(1)                                        # near by bounding box, not centroid (a long wall
        Tn = T[np.linalg.norm(np.maximum(0, np.maximum(lo_ - P0, P0 - hi_)), axis=1) < 4.0]   # face's centre lies metres away)
        gaps, slits = {}, []
        edges = (('x-', lambda s: (lo[0], 0.0, s), (lo[2] + 0.1, hi[2] - 0.1), -X),
                 ('x+', lambda s: (hi[0], 0.0, s), (lo[2] + 0.1, hi[2] - 0.1), X),
                 ('head', lambda s: (s, 0.0, hi[2]), (lo[0] + 0.1, hi[0] - 0.1), Z))
        for edge, base, rng, outward in edges:
            for s in np.linspace(rng[0], rng[1], 5):
                b = W(*base(s))
                for d in (0.002, 0.005, 0.010, 0.020, 0.040):
                    if _hit(Tn, b + outward * d - Y * 0.6, Y, 1.2) is None and not _inside(Tn, b + outward * d, X):
                        slits.append((edge, round(float(s), 2), d))
            gs = [_hit(Tn, W(*base(sum(rng) / 2)) - outward * 0.01 + Y * dy, outward, 1.0) for dy in (-0.012, 0.012)]   # either side of
            gs = [g for g in gs if g is not None]                                                                     # the mid plane: two
            gaps[edge] = round(min(gs) - 0.01, 4) if gs else None                                                     # walls meet there
        known = [v for v in gaps.values() if v is not None]
        worst = max(known) if len(known) == len(gaps) else None
        out.append({'name': dr['name'], 'gaps': gaps, 'slits': len(slits), 'first_slit': slits[0] if slits else None,
                    'ok': worst is not None and worst <= tol and not slits})
    return out


def clearance(dr, arch, boxes, floor_z, depth=1.5, half=0.35, max_angle=80.0, r0=0.25):
    """what a door needs round it besides the fit (rig 2026-11-01: three doors the walker could not get through, all fitted to 0 mm):
      lane  - a walking lane 2 x half wide through the middle of the leaf, `depth` m out on both sides (the probe walks 1.5 m through)
      swing - the leaf swung to max_angle both ways, sampled from r0 m out from the hinge (inside r0 it may touch its own casing / jamb)
    against boxes [(lo, hi)] (props' AABBs and built solids) that overlap 0.2 .. 1.8 m over the floor. -> [(kind, side, point)]."""
    lo, hi = leaf_bbox(arch, dr['model'])
    h = math.radians(dr['heading'])
    X = np.array([math.cos(h), math.sin(h)])
    Y = np.array([-math.sin(h), math.cos(h)])
    P0 = np.array(dr['pos'][:2], np.float64)
    sx = 1.0 if abs(lo[0]) < abs(hi[0]) else -1.0                        # the leaf runs along +x or -x from the hinge
    w = hi[0] - lo[0]
    B = [(b[0], b[1]) for b in boxes if b[0][2] < floor_z + 1.8 and b[1][2] > floor_z + 0.2]
    def blocked(p):
        return any(l[0] < p[0] < u[0] and l[1] < p[1] < u[1] for l, u in B)
    out = []
    mid = P0 + X * sx * w / 2
    for side in (1, -1):
        for t in np.arange(0.05, depth + 1e-6, 0.05):
            for c in np.arange(-half, half + 1e-6, 0.05):                   # every 5 cm across (a 10 cm post must not slip between)
                p = mid + Y * side * t + X * c
                if blocked(p):
                    out.append(('lane', side, tuple(np.round(p, 2))))
                    break
            else:
                continue
            break
        for a in np.radians(np.arange(10.0, max_angle + 1e-6, 10.0)):
            hit = None
            for r in np.arange(r0, w + 1e-6, 0.05):
                p = P0 + (X * sx * math.cos(a) + Y * side * math.sin(a)) * r
                if blocked(p):
                    hit = p
                    break
            if hit is not None:
                out.append(('swing', side, tuple(np.round(hit, 2))))
                break
    return out


def _box_tris(lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    V = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    F = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2), (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    return V[np.array(F)]


def _demo():
    arch = {'v_ilev_ph_gendoor005': {'bbMin': 'x:-1.30208 y:-0.060203 z:-1.15', 'bbMax': 'x:-0.000101 y:0.059798 z:1.15'}}
    lo, hi = leaf_bbox(arch, 'v_ilev_ph_gendoor005')
    op = fit_single(lo, hi, 0.0, 0.0)
    print('single:', {k: round(v, 4) if isinstance(v, float) else v for k, v in op.items()})
    wall = np.concatenate([_box_tris((-3, -0.1, 0), (op['a0'], 0.1, 3)), _box_tris((op['a1'], -0.1, 0), (5, 0.1, 3)),
                           _box_tris((op['a0'], -0.1, op['z1']), (op['a1'], 0.1, 3)), _box_tris((-3, -1, -0.4), (5, 1, 0))])
    door = [{'name': 'd', 'model': 'v_ilev_ph_gendoor005', 'pos': (op['hinge'], 0.0, op['zc']), 'heading': 0.0}]
    good = check(wall, door, arch)
    bad = check(wall, door, arch, shrink={'d': 0.05})
    print('exact opening:', good[0])
    print('planted 5 cm:', bad[0])
    assert good[0]['ok'] and not bad[0]['ok'] and bad[0]['slits'] > 0, 'the door gate did not prove itself'
    clear = clearance(door[0], arch, [], 0.0)
    planted = clearance(door[0], arch, [((0.4, 0.5, 0.0), (0.9, 0.9, 1.0))], 0.0)        # a box 0.5 m in front of the leaf
    print('clear door:', clear, ' planted box:', planted)
    assert not clear and any(k == 'lane' for k, _, _ in planted) and any(k == 'swing' for k, _, _ in planted), 'the clearance check did not prove itself'
    print('DOOR_FIT_PROVEN')


if __name__ == '__main__':
    _demo()
