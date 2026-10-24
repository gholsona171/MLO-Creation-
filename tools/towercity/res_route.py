"""The residence floors' fly-through route (Antonio 2026-10-23: apartments, hallways, stairs; stay inside, change floors by the
fire stair, never through a wall). Pure Python: walks the plan of tower_residences (spaces, partitions, doors, the stair) and
writes C:\\C9Test\\routes\\fly_res.lua for tc_flythrough.sh. Inside a space the camera goes rect to rect through the middle of
their shared edge (no corner cutting); a door / opening is crossed square to the wall. Check: py -3 fly_check.py res (0 hits).
Run: py -3 res_route.py"""
from collections import deque
import tower_residences as R
EYE = 1.6; SPD = 1.9; SLOW = 1.2


def rects(fl, name): return [tuple(r) for r in R.spaces(fl)[name][1]] if name != 'stair' else [tuple(R.STAIR)]
def inside(r, p, e=1e-6): return r[0] - e <= p[0] <= r[1] + e and r[2] - e <= p[1] <= r[3] + e


def links(fl):
    """{(a, b): (axis, line, c)}: every way through between two spaces - door, cased opening or open plan (its crossing point)."""
    L = {}
    for axis, line, a0, a1, lo, hi, fits in R.parts(fl):
        if lo is None or hi is None: continue
        for f in fits:
            c = f[2] + 0.7 if f[0] == 'door' else (f[1] + f[2]) / 2
            L[(lo, hi)] = L[(hi, lo)] = (axis, line, c)
    rel = R.OPEN_PLAN[R.FLOORS[fl][3]]
    for axis, line, a0, a1, lo, hi in R.segments(fl):
        if lo and hi and rel.get(frozenset((lo, hi))) == 'none':
            L.setdefault((lo, hi), (axis, line, (a0 + a1) / 2)); L.setdefault((hi, lo), (axis, line, (a0 + a1) / 2))
    return L


def cross(link, frm_side, d=0.9):
    """(before, on, after) crossing a link from the - side of its line (frm_side = -1) or the + side (+1)."""
    axis, line, c = link
    P = lambda off: (line + off, c) if axis == 'u' else (c, line + off)
    return P(frm_side * d), P(0.0), P(-frm_side * d)


def side_of(fl, name, link):
    axis, line, c = link; k = 0 if axis == 'u' else 2; j = 2 if k == 0 else 0
    for r in rects(fl, name):
        if not (r[j] - 1e-6 <= c <= r[j + 1] + 1e-6): continue
        if abs(r[k + 1] - line) < 1e-6: return -1                 # the space lies on the - side of the line
        if abs(r[k] - line) < 1e-6: return 1
    raise ValueError((fl, name, link))


def within(fl, name, a, b):
    """points from a to b inside one space: through the shared edges of its rects."""
    rs = rects(fl, name); ia = next(i for i, r in enumerate(rs) if inside(r, a)); ib = next(i for i, r in enumerate(rs) if inside(r, b))
    if ia == ib: return [b]

    def edge(r1, r2):
        for k in (0, 2):
            j = 2 if k == 0 else 0
            for x, y in ((r1[k + 1], r2[k]), (r1[k], r2[k + 1])):
                if abs(x - y) < 1e-6:
                    lo, hi = max(r1[j], r2[j]), min(r1[j + 1], r2[j + 1])
                    if hi - lo > 0.6: return (x, (lo + hi) / 2) if k == 0 else ((lo + hi) / 2, x)
        return None
    prev = {ia: None}; q = deque([ia])
    while q:
        i = q.popleft()
        for j in range(len(rs)):
            if j not in prev and edge(rs[i], rs[j]): prev[j] = i; q.append(j)
    chain = [ib]
    while prev[chain[-1]] is not None: chain.append(prev[chain[-1]])
    chain = chain[::-1]; out = []
    for i, j in zip(chain, chain[1:]):
        r = rs[i]; out += [((r[0] + r[1]) / 2, (r[2] + r[3]) / 2), edge(rs[i], rs[j])]
    r = rs[ib]; return out + [((r[0] + r[1]) / 2, (r[2] + r[3]) / 2), b]


def tour(fl, stops, start):
    """camera points [((u, v), speed)] visiting the spaces in `stops` in order (shortest way through links) from `start` in the hall.
    A stop's camera point is the middle of its biggest rect; the stair stop ends just inside the stair door."""
    L = links(fl); here, pos, out = 'hall', start, []
    graph = {}
    for a, b in L: graph.setdefault(a, set()).add(b)
    for goal in stops:
        prev = {here: None}; q = deque([here])
        while q:
            s = q.popleft()
            for t in sorted(graph.get(s, ())):
                if t not in prev: prev[t] = s; q.append(t)
        way = [goal]
        while prev[way[-1]] is not None: way.append(prev[way[-1]])
        way = way[::-1]
        for a, b in zip(way, way[1:]):
            lk = L[(a, b)]; b0, on, b1 = cross(lk, side_of(fl, a, lk))
            out += [(p, SPD) for p in within(fl, a, pos, b0)] + [(on, SLOW), (b1, SLOW)]; pos = b1
        here = goal
        if goal == 'stair': break
        big = max(rects(fl, goal), key=lambda r: (r[1] - r[0]) * (r[3] - r[2]))
        cen = ((big[0] + big[1]) / 2, (big[2] + big[3]) / 2)
        out += [(p, SPD) for p in within(fl, goal, pos, cen)]; pos = cen
    return out, pos, here


def stair_up(fl, entry):
    """from just inside the stair door, up one storey to the next floor's south landing (the stair's own numbers)."""
    zb = R.FLOORS[fl][0]; uW = sum(R.LANE_W) / 2; uE = sum(R.LANE_E) / 2; vS = (R.STAIR[2] + R.F1_BASE) / 2; vN = (R.F2_BASE + R.LAND_N) / 2
    return [((entry[0], vS), zb + EYE, SLOW), ((uW, vS), zb + EYE, SLOW), ((uW, R.F1_BASE - 0.2), zb + EYE, SLOW),
            ((uW, R.F2_BASE + 0.3), zb + 2.2 + EYE, SLOW), ((uW, vN), zb + 2.2 + EYE, SLOW), ((uE, vN), zb + 2.2 + EYE, SLOW),
            ((uE, R.F2_BASE + 0.3), zb + 2.2 + EYE, SLOW), ((uE, R.F1_BASE - 0.2), zb + 4.4 + EYE, SLOW), ((uE, vS), zb + 4.4 + EYE, SLOW)]


PLAN = {'98': ['a_foy', 'a_den', 'a_kit', 'a_liv', 'a_kit', 'a_den', 'a_foy', 'a_hal', 'a_mst', 'a_hal', 'a_foy', 'hall',
               'c_foy', 'c_kit', 'c_liv', 'c_kit', 'c_foy', 'c_hal', 'c_mst', 'c_hal', 'c_foy', 'hall', 'stair'],
        '99': ['d_foy', 'd_hal', 'd_den', 'd_hal', 'd_liv', 'd_hal', 'd_foy', 'hall', 'stair'],
        '100': ['a_foy', 'a_bar', 'a_gr', 'a_bar', 'a_foy', 'a_hal', 'a_mst', 'a_hal', 'a_foy', 'hall', 'b_foy', 'b_med', 'b_gr']}


def main():
    P = []
    pos = ((R.LIFT[0] + R.LIFT[1]) / 2, R.LIFT[2] - 1.2)                    # in front of the lift doors on 98
    P.append((pos, R.FLOORS['98'][0] + EYE, SLOW))
    for fl, nxt in (('98', '99'), ('99', '100'), ('100', None)):
        z = R.FLOORS[fl][0] + EYE
        pts, pos, here = tour(fl, PLAN[fl], pos)
        P += [(p, z, s) for p, s in pts]
        if here == 'stair':                                                     # climb, then out through the next floor's stair door
            P += stair_up(fl, pos)
            L = links(nxt); lk = L[('stair', 'hall')]; b0, on, b1 = cross(lk, side_of(nxt, 'stair', lk))
            zn = R.FLOORS[nxt][0] + EYE; P += [(b0, zn, SLOW), (on, zn, SLOW), (b1, zn, SLOW)]; pos = b1
    lines = ',\n '.join("{'t', %.2f, %.2f, %.2f, %.1f}" % (u, v, z, s) for (u, v), z, s in P)
    src = ("-- Tower City residences 98 / 99 / 100: hall, apartments, the fire stair between floors (generated by work/res_route.py;\n"
           "-- checked by work/fly_check.py res). Frame 't' = the tower lot.\n"
           "local FR = {m = {vector2(71.0, -884.0)}, t = {vector2(-78.897, -827.328)}}\nlocal H = math.rad(69.5)\n"
           "local function W(f, u, v, z) local o = FR[f][1] return vector3(o.x + u * math.cos(H) - v * math.sin(H), o.y + u * math.sin(H) + v * math.cos(H), z) end\n"
           "local P = {\n " + lines + "\n}\n")
    open(r'C:\C9Test\routes\fly_res.lua', 'w', encoding='utf-8').write(src); print('RES_ROUTE', len(P), 'points')


if __name__ == '__main__': main()
