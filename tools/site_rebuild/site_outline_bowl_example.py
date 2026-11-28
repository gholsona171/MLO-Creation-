"""How site_plan's LOT and SITE outlines were measured at the Vinewood Bowl (Antonio 2026-11-27: "I want my MLO placed in place of the
bowl ... you're gonna have to delete a lot of that because it won't look proper if that stuff is left behind"). Run once; its output
is pasted into site_plan.py as data, which then checks itself against the collision every build.
  LOT   the paved part: the Bowl's hollow (inside HOLLOW), less the grass BANK along the site's outline: the flat lot (grade.py's
        plane) meets the old ground round the site (the Bowl's rim up to 9 m above it, Marlowe Dr level with it) on a grass slope
        of BANK_SLOPE, so a cell stays paved only when it is at least |old ground at the nearest outline point - plane| / BANK_SLOPE
        + BANK_MIN m in from the outline; plus the driveway (DRIVE). The bank is cut into the hill OUTSIDE the hollow: the site is
        grown BANK_ROOM m round the hollow (3 m off the roads, east of the Executives mansion: x > MANSION_X, and CLIFF_PAD m short
        of any cliff in the old ground, slope > CLIFF: the outline never runs along a rock face), so the lot keeps its
        size ("make nothing smaller") and only the road side loses paving to its bank,
        plus CLUB_PAVE m round the club's roof (site.json + concept_v3: the club always stands on the paving). The strip along
        Marlowe Dr south of the driveway (SPUR) stays on the site, cleared and graded natural: paved it would be a dead end.
        The hollow: the ground (ground_scan.py 'low', the empty cells under the Bowl's own structures filled from the nearest
        ground) under Z_LOT, the part that holds SEED (the Bowl's front parking), kept ROAD_CLEAR (+ MARGIN) off every road's collision
        edge (Marlowe Dr loops round its east and south), opened / closed by SMOOTH m and with its holes filled (the Bowl's raised
        building pads are islands over Z_LOT inside it: they go, the lot is graded over them). Paved (ground.py blacktop).
  SITE  LOT plus the amphitheater: the seating rows are the only surface there (box primitives, nothing under them: ground_scan's
        empty cells inside BOWL), so when they go the ground under them is new. Those cells, grown by SEAT_PAD, join the site, clipped
        to the same ROAD_CLEAR. Graded (grade.py) and drawn as natural ground (ground.py), not paved.
  distance to a road edge = Euclidean distance from each 0.25 m sample to the nearest road sample (ground_scan.py's mask) minus half
  a sample, so the 3 m is kept from the outer edge of the road's collision.
  DRIVE the one way in and out (Marlowe Dr's west edge, east of the lot, the loop's south-east corner: lot_plan): a paved apron
        WIDTH m wide (an in lane over an out lane) from the lot across the 3 m verge onto the road, ROAD_LAP m over the road's own
        collision edge all along (traced per 0.25 m row: the edge is not straight), with a curb return of FLARE_R m each side (a
        quarter circle tangent to the road edge and the throat). It joins both outlines.
Run: py -3 site_outline.py      Output ../site_outline.json {lot, site, drive} (world x, y, counter-clockwise) + ../review/site_outline.png"""
import json, math
import numpy as np
from pathlib import Path
from scipy import ndimage
import shapely
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
M = Path(__file__).resolve().parents[1]
ROAD_CLEAR, MARGIN, SIMPLIFY, Z_LOT, SMOOTH, SEAT_PAD, CLUB_PAVE = 3.0, 0.35, 0.6, 130.0, 4.0, 4.0, 16.0
CLIFF, CLIFF_PAD = 1.5, 2.0
BANK_SLOPE, BANK_MIN, BANK_ROOM, MANSION_X = 1.0, 1.0, 10.0, 563.0   # the bank: 1 up in 1 (Rockstar's own hillside cuts), >= 1 m of grass
SPUR = (840.0, 400.0, 910.0, 484.0)                         # x0, y0, x1, y1: not paved (south of the driveway's curb)
DRIVE = dict(name='in_out', yc=498.0, width=13.0, flare=4.0, road_lap=0.10, inner_x=884.0)   # yc: its centre line (world y);
#   inner_x: how far west the apron runs (into the lot, past its 3 m verge)
SEED = (760.0, 635.0)                                       # the Bowl's front parking, north-east of the stage (the stage's pad is over Z_LOT)
BOWL = (560.0, 905.0, 400.0, 720.0)                         # x0, x1, y0, y1: where the Bowl's own empty cells count as its seating
HOLLOW = [(560.0, 470.0), (840.0, 470.0), (840.0, 420.0), (905.0, 420.0), (905.0, 538.0), (940.0, 545.0), (940.0, 700.0),
          (905.0, 720.0), (560.0, 720.0)]                   # the Bowl's hollow: the valley falling away south of y 470 (to Marlowe
#   Dr's south loop) stays out; the strip along the road south-east of the hollow (x 840-905, y 420-470) stays in; north of where
#   Marlowe Dr turns east (y 536) the Bowl's open ground east of the hollow (to x 940, bushes only) comes in: room for the bank


def cells_poly(mask, xs, ys, st):
    """a cell mask -> one shapely (multi)polygon of its cells."""
    jj, ii = np.nonzero(mask)
    return unary_union([box(xs[i] - st / 2, ys[j] - st / 2, xs[i] + st / 2, ys[j] + st / 2) for j, i in zip(jj, ii)])


def outlines():
    G = np.load(M / 'site' / 'ground_raw.npz'); low = G['low']; x0, y0, st = (float(v) for v in G['box'][:3]); R = G['road']; rs = float(G['road_step'])
    xs = x0 + (np.arange(low.shape[1]) + .5) * st; ys = y0 + (np.arange(low.shape[0]) + .5) * st
    X, Y = np.meshgrid(xs, ys)
    hole = np.isnan(low)
    idx = ndimage.distance_transform_edt(hole, return_distances=False, return_indices=True); lf = low[tuple(idx)]
    D = ndimage.distance_transform_edt(~R) * rs - rs / 2                                   # road distance on the 0.25 m grid
    k = int(round(st / rs)); Dc = D[k // 2::k, k // 2::k][:low.shape[0], :low.shape[1]]   # ... sampled at the 1 m cell centres
    clear = Dc > ROAD_CLEAR + MARGIN
    lab, _ = ndimage.label((lf < Z_LOT) & clear)
    j, i = int((SEED[1] - y0) / st), int((SEED[0] - x0) / st); assert lab[j, i], 'the seed is not in the hollow'
    lot = ndimage.binary_fill_holes(lab == lab[j, i])
    seats = hole & (X > BOWL[0]) & (X < BOWL[1]) & (Y > BOWL[2]) & (Y < BOWL[3])
    seats = ndimage.binary_closing(seats, iterations=2)
    safe = cells_poly(clear, xs, ys, st)                                                   # (the road clearance as a polygon)
    def clean(P):
        if P.geom_type != 'Polygon': P = max(P.geoms, key=lambda g: g.area)
        return Polygon(P.exterior).simplify(SIMPLIFY, preserve_topology=True).buffer(-SIMPLIFY, join_style='mitre').simplify(0.05)
    L = clean(cells_poly(lot, xs, ys, st).intersection(Polygon(HOLLOW)).buffer(-SMOOTH).buffer(2 * SMOOTH).buffer(-SMOOTH).intersection(safe))
    Sx = clean(unary_union([L, cells_poly(seats, xs, ys, st).buffer(SEAT_PAD)]).buffer(-SMOOTH).buffer(2 * SMOOTH).buffer(-SMOOTH).intersection(safe))
    Sx = Sx.simplify(1.0).buffer(-1.0, join_style='mitre')            # (the 1 m cell steps out; never further out than measured)
    A = apron(R, rs, x0, y0)
    gy, gx = np.gradient(lf, st); cliff = cells_poly(ndimage.binary_dilation(np.hypot(gx, gy) > CLIFF, iterations=int(CLIFF_PAD)), xs, ys, st)
    room = L.buffer(BANK_ROOM).intersection(safe.buffer(-0.6)).intersection(box(MANSION_X, Sx.bounds[1] - 50, Sx.bounds[2] + 50, Sx.bounds[3] + 50))
    room = room.difference(cliff.difference(Sx))                         # (the hollow's own cliffs - the Bowl's raised pads - go anyway)
    Sx = unary_union([Sx, room, L.buffer(0.05, join_style='mitre'), A.buffer(0.05, join_style='mitre')])   # the site round the hollow + driveway
    Sx = Polygon(Sx.exterior if Sx.geom_type == 'Polygon' else max(Sx.geoms, key=lambda g: g.area).exterior)
    core = L.intersection(cells_poly(paveable(Sx, lf, xs, ys, R, rs, x0, y0), xs, ys, st)).difference(box(*SPUR))
    core = core.buffer(-SMOOTH).buffer(SMOOTH)                                                       # the hollow less the bank, the spur
    core = max(core.geoms, key=lambda g: g.area) if core.geom_type != 'Polygon' else core
    club = club_roof().buffer(CLUB_PAVE).intersection(L)
    L = unary_union([core, club, A]).buffer(1.0).buffer(-1.0).intersection(Sx.buffer(-0.05)).simplify(0.05)   # + the club, the driveway
    L = Polygon(L.exterior if L.geom_type == 'Polygon' else max(L.geoms, key=lambda g: g.area).exterior)
    return [shapely.geometry.polygon.orient(P, 1.0) for P in (L, Sx)], (lf, xs, ys, R, rs, x0, y0)


def paveable(Sx, lf, xs, ys, R, rs, x0, y0):
    """the 1 m cells far enough in from the site's outline for the bank: distance to the outline >= |old ground just outside the
    nearest outline point - the lot's plane there| / BANK_SLOPE + BANK_MIN."""
    import sys; sys.path.insert(0, str(M / 'tools')); import grade as GR, site_plan as SP
    X, Y = np.meshgrid(xs, ys); site = shapely.contains_xy(Sx, X, Y)
    d, idx = ndimage.distance_transform_edt(site, return_indices=True)        # (to the nearest cell outside the site, and which)
    out_z = lf[tuple(idx)]
    road_x = road_edge(R, rs, x0, y0, DRIVE['yc']); j, i = int(DRIVE['yc'] - ys[0] + .5), int(road_x + .5 - xs[0] + .5)
    pz = GR.plane(X, Y, SP.ORIGIN, SP.HEADING, SP.PAD_Z, (road_x, DRIVE['yc']), float(lf[j, i]))
    return site & (d - 0.5 >= np.abs(out_z - pz) / BANK_SLOPE + BANK_MIN)


def club_roof():
    """the club's roof outline (world): concept_v3's plan grown by its overhang, placed by ../site.json."""
    import sys; sys.path.insert(0, str(M / 'tools')); import concept_v3 as C
    S = json.load(open(M / 'site.json')); h = math.radians(S['heading']); c, s = math.cos(h), math.sin(h)
    return Polygon([(S['x'] + c * u - s * v, S['y'] + s * u + c * v) for u, v in C.grown(*C.OVERHANG, n=192)])


def road_edge(R, rs, x0, y0, y):
    """Marlowe Dr's west collision edge (world x) at world y: the first road sample east of the lot in that 0.25 m row."""
    j = int((y - y0) / rs); xs = x0 + rs * (np.nonzero(R[j])[0] + .5); xs = xs[(xs > 880) & (xs < 960)]
    assert len(xs), f'no road east of the lot at y {y}'
    return float(xs.min() - rs / 2)


def apron(R, rs, x0, y0, n=12):
    """the driveway's outline (counter-clockwise): the road side on the traced road edge minus road_lap (south -> north), the north
    curb return (from the road edge round to the throat's north side, FLARE_R in), the throat west to inner_x and back, the south
    curb return. A curb return's point at offset o past the throat's side lies u = R - sqrt(R^2 - (R - o)^2) in from the road edge."""
    D = DRIVE; h, Rf = D['width'] / 2, D['flare']; e = lambda y: road_edge(R, rs, x0, y0, y) - D['road_lap']
    u = lambda o: Rf - math.sqrt(max(0.0, Rf * Rf - (Rf - o) ** 2))
    side = [(e(y), y) for y in np.arange(D['yc'] - h - Rf, D['yc'] + h + Rf + 1e-6, 0.25)]
    north = [(e(D['yc'] + h + o) - u(o), D['yc'] + h + o) for o in np.linspace(Rf, 0, n + 1)[1:]]
    south = [(e(D['yc'] - h - o) - u(o), D['yc'] - h - o) for o in np.linspace(0, Rf, n + 1)[:-1]]
    return Polygon(side + north + [(D['inner_x'], D['yc'] + h), (D['inner_x'], D['yc'] - h)] + south).buffer(0)


def main():
    (L, S), (lf, xs, ys, R, rs, x0, y0) = outlines()
    assert S.contains(L.buffer(-0.1)), 'LOT inside SITE'
    out = {'drive': dict(DRIVE, road_x=round(road_edge(R, rs, x0, y0, DRIVE['yc']), 2))}   # (+ the road's edge on its centre line)
    for name, P in (('lot', L), ('site', S)):
        pts = [(round(x, 2), round(y, 2)) for x, y in list(P.simplify(0.02).exterior.coords)[:-1]]
        out[name] = [q for k, q in enumerate(pts) if q != pts[k - 1]]                 # (no zero-length edge after rounding)
        print('SITE_OUTLINE %s: vertices %d, area %.0f m2, bounds %s' % (name, len(out[name]), P.area, [round(v, 1) for v in P.bounds]))
    json.dump(out, open(M / 'site_outline.json', 'w'), indent=0)
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(lf, origin='lower', extent=[xs[0] - .5, xs[-1] + .5, ys[0] - .5, ys[-1] + .5], cmap='terrain', vmin=95, vmax=200)
    rx = x0 + (np.arange(R.shape[1]) + .5) * rs; ry = y0 + (np.arange(R.shape[0]) + .5) * rs
    ax.contour(rx[::4], ry[::4], R[::4, ::4].astype(float), levels=[.5], colors='k')
    ax.plot(*S.exterior.xy, 'r-', lw=2, label='SITE (graded) %.0f m2' % S.area); ax.plot(*L.exterior.xy, 'm-', lw=2, label='LOT (paved) %.0f m2' % L.area)
    ax.legend(); ax.set_title('Block Boyz at the Vinewood Bowl: site outlines'); fig.savefig(M / 'review' / 'site_outline.png', dpi=80, bbox_inches='tight')


if __name__ == '__main__': main()
