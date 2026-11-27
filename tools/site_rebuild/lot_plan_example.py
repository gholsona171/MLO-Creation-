"""(Example from the Block Boyz truck club build, 2026-11-27: a lot layout as data + checks + a plan PNG. Imports that project's site_plan.)
Block Boyz truck club, the lot (Antonio 2026-11-27, "Build all of it": the Large tier's 60+ truck stalls, 12+ trailer
pull-throughs, a loop road with its own way in and way out, a show pad with a photo ramp, lot lights). World metres, north up.
Numbers from docs/reference.md (lot research): stalls 3.2 x 7.5 m, 8 m aisle, pull-throughs 4 m wide at 60 degrees, a one-way
loop 6.5 m wide, lot poles ~8 m every ~24 m, photo ramp 8 x 4 m deck 1.2 m up with 6.5 m ramps.

  THE LOOP   one way, counter-clockwise (drive on the right, the lot on your left): IN from the south road at the lot's SE corner up
             the east lane, west along the north lane, down the west lane and OUT onto the south road at the SW corner (the two
             throats 180 m apart); the south lane runs back east from the exit to the way in (anyone not leaving goes round again).
  STALLS     two rows of 3.2 x 7.5 m truck stalls nose to nose along the whole lot: the south row off the south lane, the north row
             off aisle A (8 m, one way west, from the east lane to the west lane). The lamp posts stand on their shared nose line.
  PULL-THROUGHS  the north band between aisle A and the north lane, west end: 60-degree stalls 4 m wide (4.62 m along the row),
             the whole band deep (32.9 m along the stall: truck + trailer), in off aisle A, out forward onto the north lane.
  SHOW PAD   the north band's east part: 52 x 26 m, a bold white border, the photo ramp (lot_build.py) in its middle along x.
  THE CLUB   east of the loop: the way in also feeds a two-way plaza along the club's front (glass drive-ins) that runs round the east
             end to the back apron (bay doors, wash bay). No lane paint there: arrows and keep-clear boxes only (the bays, the glass
             drive-ins, the two kept power poles, the arch's front foot).
  LIGHTS     prop_streetlight_04 (double arm, 8.6 m) on the stall rows' nose line every 7 stalls; prop_streetlight_03 (one arm,
             8.9 m) on the site's north and west edges with the arm over the lane, and round the club. None along the south edge or
             the club's diagonal front edge: the kept power line runs there (check(): no lamp within WIRE_CLEAR of a kept span).
paint() -> parking_plan's format: ('line', x0, y0, x1, y1, colour, width) | ('arrow', x, y, heading_deg, length)
Run: py -3 lot_plan.py   check() + ../review/lot_plan.png (for Antonio)"""
import math, json
from pathlib import Path
import site_plan as SP, concept_v3 as C

LANE, STALL_W, STALL_D, AISLE, LINE_W, BOLD_W = 6.5, 3.2, 7.5, 8.0, 0.12, 0.15
WEST, EAST = (1012.5, 1019.0), (1198.5, 1205.0)                 # the loop's west and east lanes (x0, x1)
SOUTH, NORTH = (3548.5, 3555.0), (3606.5, 3613.0)               # its south and north lanes (y0, y1)
NOSE = SOUTH[1] + STALL_D                                       # 3562.5: the two stall rows' shared nose line
AISLE_A = (NOSE + STALL_D, NOSE + STALL_D + AISLE)              # 3570 .. 3578
N_STALLS = int((EAST[0] - WEST[1] - 1.0) // STALL_W)            # per row (55)
STALL_X0 = WEST[1] + (EAST[0] - WEST[1] - N_STALLS * STALL_W) / 2
PULL_ANG, PULL_W, N_PULL = 60.0, 4.0, 16
PULL_STEP = PULL_W / math.sin(math.radians(PULL_ANG))           # 4.62 m along the row
PULL_RUN = (NORTH[0] - AISLE_A[1]) / math.tan(math.radians(PULL_ANG))   # a separator's shift west over the band (16.45 m)
PULL_X0 = WEST[1] + 1.0 + PULL_RUN                              # the first separator's foot on aisle A
SHOW = (1130.0, 3579.25, 1182.0, 3605.25)                       # x0, y0, x1, y1 (52 x 26 m)
RAMP = dict(cx=(SHOW[0] + SHOW[2]) / 2, cy=(SHOW[1] + SHOW[3]) / 2, heading=0.0, deck=(8.0, 4.0), height=1.2, ramp=6.5)
MONUMENT = dict(x=1208.8, y=3547.9, heading=0.0, w=3.2, d=.6, h=3.4)   # the entrance sign (lot_build.py): beside the way in, facing the road
LAMP2, LAMP1 = 'prop_streetlight_04', 'prop_streetlight_03'    # double arm (+-2.45 m along local y) / one arm (local -y, 2.5 m)
WIRE_CLEAR, LEG_CLEAR = 4.0, 3.0


def lanes():
    """the loop's four lanes and aisle A as rectangles (x0, y0, x1, y1), plus the two throats to the south road."""
    return {'west': (WEST[0], SOUTH[0], WEST[1], NORTH[1]), 'east': (EAST[0], SOUTH[0], EAST[1], NORTH[1]),
            'south': (WEST[0], SOUTH[0], EAST[1], SOUTH[1]), 'north': (WEST[0], NORTH[0], EAST[1], NORTH[1]),
            'aisle': (WEST[1], AISLE_A[0], EAST[0], AISLE_A[1]),
            'out': (WEST[0], 3540.0, WEST[1], SOUTH[0]), 'in': (EAST[0], 3540.0, EAST[1], SOUTH[0])}


def stalls():
    """[(x0, y0, x1, y1, row)] of every truck stall."""
    out = []
    for k in range(N_STALLS):
        x0 = STALL_X0 + k * STALL_W
        out += [(x0, SOUTH[1], x0 + STALL_W, NOSE, 'south'), (x0, NOSE, x0 + STALL_W, AISLE_A[0], 'north')]
    return out


def pulls():
    """[4 corners] of every pull-through (a parallelogram: feet on aisle A, heads on the north lane)."""
    out = []
    for k in range(N_PULL):
        a = PULL_X0 + k * PULL_STEP; b = a + PULL_STEP
        out.append([(a, AISLE_A[1]), (b, AISLE_A[1]), (b - PULL_RUN, NORTH[0]), (a - PULL_RUN, NORTH[0])])
    return out


def ramp_outline():
    """the photo ramp's footprint (4 corners, world): ramp + deck + ramp along its heading."""
    L = RAMP['deck'][0] + 2 * RAMP['ramp']; Wd = RAMP['deck'][1]; h = math.radians(RAMP['heading']); c, s = math.cos(h), math.sin(h)
    return [(RAMP['cx'] + c * u - s * v, RAMP['cy'] + s * u + c * v) for u, v in ((-L / 2, -Wd / 2), (L / 2, -Wd / 2), (L / 2, Wd / 2), (-L / 2, Wd / 2))]


def _edge_lamp(x, y, inward_deg):
    """a one-arm lamp at (x, y) with its arm pointing inward_deg (world, 0 = east): the arm is the model's local -y."""
    return (LAMP1, round(x, 2), round(y, 2), round((inward_deg + 90) % 360, 1))


def lights():
    """[(model, x, y, heading)] of every lot lamp."""
    L = [(LAMP2, round(STALL_X0 + k * STALL_W, 2), NOSE, 0.0) for k in range(3, N_STALLS, 7)]          # nose line, every 7 stalls
    L += [_edge_lamp(x, NORTH[1] + .7, -90) for x in (1030.0, 1054.0, 1078.0, 1102.0, 1126.0, 1150.0, 1174.0)]
    L += [_edge_lamp(WEST[0] - .9, y, 0) for y in (3572.0, 3596.0)]
    L += [(LAMP2, 1254.0, 3560.5, SP.HEADING), (LAMP2, 1213.0, 3557.0, SP.HEADING)]                 # the club's front plaza
    L += [_edge_lamp(1250.3, 3623.4, -75.4)]                                                        # the back apron (north edge; the NE corner has a kept line)
    L += [_edge_lamp(1302.6, 3598.0, 180)]                                                          # the east end
    return L


# ---------------- the club's side: keep-clear boxes in the club's own frame (local, then to world) ----------------
def _front_y(x):
    """the club's front wall (local y) at local x: the outline's front half."""
    O = [p for p in C.outline(384) if p[1] < C.CY]
    return min(O, key=lambda p: abs(p[0] - x))[1]


def _back_y(x):
    O = [p for p in C.outline(384) if p[1] > C.CY]
    return min(O, key=lambda p: abs(p[0] - x))[1]


def _hatch_poly(Q, gap=1.4, w=0.22, colour='yellow', border=BOLD_W):
    """yellow keep-clear: a convex polygon's border + 45-degree stripes (world) clipped to it."""
    out = [('line', *Q[i], *Q[(i + 1) % len(Q)], colour, border) for i in range(len(Q))]
    us = [x - y for x, y in Q]; c = min(us) + gap / 2
    while c < max(us):
        pts = []
        for i in range(len(Q)):
            (ax, ay), (bx, by) = Q[i], Q[(i + 1) % len(Q)]; fa, fb = ax - ay - c, bx - by - c
            if (fa > 0) != (fb > 0): t = fa / (fa - fb); pts.append((ax + t * (bx - ax), ay + t * (by - ay)))
        if len(pts) >= 2 and math.dist(pts[0], pts[1]) > .4: out.append(('line', *pts[0], *pts[1], colour, w))
        c += gap
    return out


def _local_box(x0, x1, y0, y1): return [SP.W(p)[:2] for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
def _sq(x, y, r):
    """a square round (x, y), cut 0.3 m inside every site edge within reach (the site is counter-clockwise: inside = left)."""
    Q = [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)]; S = SP.SITE
    for i in range(len(S)):
        a, b = S[i], S[(i + 1) % len(S)]; L = math.dist(a, b); nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        side = lambda q: (q[0] - a[0]) * nx + (q[1] - a[1]) * ny - .3
        if _segd((x, y), a, b) > 2 * r: continue
        out = []
        for k in range(len(Q)):
            p0, p1 = Q[k - 1], Q[k]; f0, f1 = side(p0), side(p1)
            if (f0 >= 0) != (f1 >= 0): t = f0 / (f0 - f1); out.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
            if f1 >= 0: out.append(p1)
        Q = out
    return Q


def keep_clear():
    """[(what, world polygon)] of the club side's yellow boxes."""
    K = []
    for i, (b0, b1) in enumerate(C.BAYS):                                     # in front of each bay door, out to 6 m past the wall
        c = (b0 + b1) / 2; yb = max(_back_y(c - 2.2), _back_y(c + 2.2)) + .4
        K.append((f'bay{i}', _local_box(c - 2.2, c + 2.2, yb, yb + 6.0)))
    for g0, g1 in ((21.0, 26.0), (38.0, 43.0)):                               # the glass drive-ins
        yf = min(_front_y(g0), _front_y(g1)) - .4
        K.append(('glass', _local_box(g0 + .1, g1 - .1, yf - 6.0, yf)))
    for x, y in SP.kept_poles_on_site(): K.append(('power pole', _sq(x, y, 1.6)))
    K.append(('arch foot', _sq(*SP.LEGS[0], 2.2)))
    return K


def paint():
    P = []
    xa, xb = STALL_X0, STALL_X0 + N_STALLS * STALL_W
    P += [('line', xa + k * STALL_W, SOUTH[1] + .3, xa + k * STALL_W, AISLE_A[0] - .3, 'white', LINE_W) for k in range(N_STALLS + 1)]
    P += [('line', xa, NOSE, xb, NOSE, 'white', LINE_W)]
    for k in range(N_PULL + 1):                                               # pull-through separators (yellow: trucks + trailers)
        a = PULL_X0 + k * PULL_STEP; e = .3 / math.tan(math.radians(PULL_ANG))       # (0.3 m short of each lane, on the 60-degree line)
        P.append(('line', a - e, AISLE_A[1] + .3, a - PULL_RUN + e, NORTH[0] - .3, 'yellow', BOLD_W))
    x0, y0, x1, y1 = SHOW; P += [('line', x0, y0, x1, y0, 'white', .3), ('line', x1, y0, x1, y1, 'white', .3), ('line', x1, y1, x0, y1, 'white', .3),
                                ('line', x0, y1, x0, y0, 'white', .3)]
    P += [('line', WEST[0], SOUTH[0] - 1.2, WEST[1], SOUTH[0] - 1.2, 'white', .45)]          # stop bar at the way out
    A = 4.5                                                                   # arrows: the loop's direction
    P += [('arrow', x, (SOUTH[0] + SOUTH[1]) / 2, 0.0, A) for x in (1045.0, 1095.0, 1145.0, 1185.0)]
    P += [('arrow', (EAST[0] + EAST[1]) / 2, y, 90.0, A) for y in (3562.0, 3590.0)]
    P += [('arrow', x, (NORTH[0] + NORTH[1]) / 2, 180.0, A) for x in (1185.0, 1125.0, 1065.0)]
    P += [('arrow', (WEST[0] + WEST[1]) / 2, y, 270.0, A) for y in (3595.0, 3565.0)]
    P += [('arrow', x, (AISLE_A[0] + AISLE_A[1]) / 2, 180.0, A) for x in (1185.0, 1125.0, 1065.0)]
    P += [('arrow', (EAST[0] + EAST[1]) / 2, 3550.5, 90.0, A), ('arrow', (WEST[0] + WEST[1]) / 2, 3551.0, 270.0, A)]   # IN / OUT
    P += [('arrow', 1222.0, 3553.0, SP.HEADING, A), ('arrow', 1222.0, 3549.6, SP.HEADING + 180, A)]                   # club plaza, both ways
    for _, Q in keep_clear(): P += _hatch_poly(Q)
    return P


def counts():
    return {'truck stalls': 2 * N_STALLS, 'pull-throughs': N_PULL, 'lamp posts': len(lights()),
            'show pad': f'{SHOW[2] - SHOW[0]:.0f} x {SHOW[3] - SHOW[1]:.0f} m'}


def kept_spans():
    """[(x0, y0, x1, y1)] of every power line span the build keeps (wires.py's reports)."""
    out = []
    for f in sorted((SP.M / 'site' / 'wires').glob('*.json')):
        for s in json.load(open(f)):
            if s.get('fate') == 'kept': (a, b) = s['ends']; out.append((a[0], a[1], b[0], b[1]))
    return out


def _segd(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def check():
    from shapely.geometry import Polygon, box, Point, LineString
    from shapely.ops import unary_union
    import grade as GR
    S = Polygon(SP.SITE); pad = unary_union([Polygon(p) for p in SP.derived()['pad']])
    for k, r in lanes().items():
        if k in ('in', 'out'): continue
        assert S.buffer(-1.0).contains(box(*r)), f'lane {k} not 1 m inside the site'
        assert box(*r).distance(pad) >= 5.0, f'lane {k} within 5 m of the club pad'
    for x0, y0, x1, y1, _ in stalls(): assert S.contains(box(x0, y0, x1, y1)) and box(x0, y0, x1, y1).distance(pad) > 5
    lane_u = unary_union([box(*r) for k, r in lanes().items()])
    for Q in pulls():
        q = Polygon(Q); assert S.contains(q) and q.intersection(lane_u).area < 1e-6, 'a pull-through off the site or on a lane'
        L = math.dist(Q[0], Q[3]); assert L >= 22.0, f'pull-through only {L:.1f} m long'
    sp = box(*SHOW); assert S.contains(sp) and sp.intersection(lane_u).area < 1e-6 and sp.distance(unary_union([Polygon(q) for q in pulls()])) > 5
    rp = Polygon(ramp_outline()); assert sp.buffer(-4.0).contains(rp), 'the photo ramp 4 m inside the show pad'
    # the ground under the ramp and the show pad (grade.py): the ramp's skirt takes up to RAMP_FALL (lot_build.py)
    zs = [GR.grade_z(x, y) for x, y in ramp_outline()]; ramp_fall = max(zs) - min(zs)
    show_z = [GR.grade_z(x, y) for x in range(int(SHOW[0]), int(SHOW[2]) + 1, 2) for y in range(int(SHOW[1]), int(SHOW[3]) + 1, 2)]
    spans = kept_spans(); legs = SP.LEGS; kp = SP.kept_poles_on_site()
    for m, x, y, h in lights():
        assert S.buffer(-.3).contains(Point(x, y)), f'lamp {x, y} off the site'
        assert not pad.contains(Point(x, y)) or m == LAMP2, f'lamp {x, y} on the pad'
        d = min((_segd((x, y), (a, b), (c, e)) for a, b, c, e in spans), default=99)
        assert d >= WIRE_CLEAR, f'lamp {x, y} {d:.1f} m from a kept power line'
        assert min(math.dist((x, y), q) for q in legs) >= LEG_CLEAR + SP.LEG_R and min(math.dist((x, y), q) for q in kp) > 3
        for k, r in lanes().items(): assert not box(*r).contains(Point(x, y)), f'lamp {x, y} in lane {k}'
        assert not any(Polygon(q).contains(Point(x, y)) for q in pulls()) and not sp.contains(Point(x, y))
    for it in paint():
        pts = [(it[1], it[2]), (it[3], it[4])] if it[0] == 'line' else [(it[1], it[2])]
        for p in pts: assert S.buffer(-.1).contains(Point(p)), f'paint {it} off the site'
    mo = box(MONUMENT['x'] - MONUMENT['w'] / 2, MONUMENT['y'] - MONUMENT['d'] / 2, MONUMENT['x'] + MONUMENT['w'] / 2, MONUMENT['y'] + MONUMENT['d'] / 2)
    assert S.buffer(-.5).contains(mo) and mo.distance(lane_u) > 1.5, 'the monument: on the site, clear of the lanes and the way in'
    rep = dict(counts(), ramp_ground_fall=round(ramp_fall, 2), show_pad_z=[round(min(show_z), 2), round(max(show_z), 2)],
               kept_spans=len(spans), loop_throats_apart=round(EAST[0] - WEST[1], 1))
    assert 2 * N_STALLS >= 60 and N_PULL >= 12
    return rep


def draw(path):
    from PIL import Image, ImageDraw, ImageFont
    X0, X1, Y0, Y1, Sc = 1000.0, 1315.0, 3536.0, 3648.0, 6.0
    W_, H_ = int((X1 - X0) * Sc), int((Y1 - Y0) * Sc)
    im = Image.new('RGB', (W_, H_ + 120), (226, 214, 186)); d = ImageDraw.Draw(im)
    p = lambda x, y: ((x - X0) * Sc, (Y1 - y) * Sc + 110)
    try: F = ImageFont.truetype('arialbd.ttf', 24); f = ImageFont.truetype('arial.ttf', 18)
    except OSError: F = f = ImageFont.load_default()
    d.polygon([p(*q) for q in SP.SITE], fill=(52, 54, 58))
    for k, (x0, y0, x1, y1) in lanes().items(): d.rectangle([p(x0, y1), p(x1, y0)], fill=(70, 74, 80))
    d.polygon([p(*q) for q in SP.derived()['pad'][0]], fill=(84, 84, 90))
    d.polygon([p(*q) for q in SP.derived()['building']], fill=(225, 225, 228))
    d.rectangle([p(SHOW[0], SHOW[3]), p(SHOW[2], SHOW[1])], fill=(64, 66, 74))
    d.polygon([p(*q) for q in ramp_outline()], fill=(200, 60, 40))
    col = {'white': (250, 250, 250), 'yellow': (245, 200, 40)}
    for it in paint():
        if it[0] == 'line': d.line([p(it[1], it[2]), p(it[3], it[4])], fill=col[it[5]], width=max(1, int(it[6] * Sc * 1.4)))
        else:
            x, y, h, L = it[1:]; a = math.radians(h); tip = (x + math.cos(a) * L / 2, y + math.sin(a) * L / 2); tail = (x - math.cos(a) * L / 2, y - math.sin(a) * L / 2)
            d.line([p(*tail), p(*tip)], fill=(255, 255, 255), width=4)
            for s in (1, -1): d.line([p(*tip), p(tip[0] - math.cos(a + s * .5) * 1.6, tip[1] - math.sin(a + s * .5) * 1.6)], fill=(255, 255, 255), width=4)
    for a, b, c, e in kept_spans(): d.line([p(a, b), p(c, e)], fill=(80, 140, 255), width=2)
    for x, y in SP.kept_poles_on_site(): d.ellipse([p(x - .8, y + .8), p(x + .8, y - .8)], fill=(120, 80, 40))
    for x, y in SP.LEGS: d.ellipse([p(x - 1, y + 1), p(x + 1, y - 1)], fill=(230, 60, 200))
    for m, x, y, h in lights():
        d.ellipse([p(x - .9, y + .9), p(x + .9, y - .9)], fill=(255, 235, 120), outline=(0, 0, 0))
    for x, y, t in ((1025, 3600, f'TRAILER PULL-THROUGHS ({N_PULL})'), (1135, 3603, 'SHOW PAD 52 x 26 + PHOTO RAMP'),
                    (1030, 3567.5, f'TRUCK STALLS ({N_STALLS} + {N_STALLS})'), (1240, 3595, 'CLUB'), (1007, 3545.5, 'OUT'), (1196, 3545.5, 'IN'),
                    (1080, 3611.5, 'LOOP (one way)'), (1060, 3576.5, 'AISLE A'), (1236, 3622, 'BACK APRON: BAYS + WASH')):
        d.text(p(x, y), t, font=f, fill=(255, 255, 255) if t not in ('OUT', 'IN') else (10, 10, 10))
    d.text((14, 10), 'Block Boyz truck club: the lot (north up, Marina Dr at the top, the south road at the bottom).', font=F, fill=(10, 10, 10))
    d.text((14, 44), '  '.join(f'{k}: {v}' for k, v in counts().items()) + '.  Yellow dots = lamp posts, brown = kept power poles, pink = arch feet, blue = kept power lines.',
           font=f, fill=(10, 10, 10))
    d.text((14, 70), 'Traffic: IN at the SE corner -> up the east lane -> west along the top -> down the west side -> OUT at the SW corner; the club plaza is two-way.',
           font=f, fill=(10, 10, 10))
    im.save(path)


if __name__ == '__main__':
    rep = check(); out = SP.M / 'review' / 'lot_plan.png'; draw(out)
    print('LOT_PLAN_PASS', json.dumps(rep), out)
