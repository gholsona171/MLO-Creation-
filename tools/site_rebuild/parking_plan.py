"""Parking at the Graveyard tow yard (Antonio, Nov 23: "parking lanes that make sense"), as paint on the paving. Laid round what
stands there (power poles kept by Antonio, the shop's lamp posts, both gates, the shop's roll-up doors, both pole barns):
  CUSTOMERS   outside the yard, along the lawn edge of the house lot by the road: 15 stalls (2 rows either side of the house's
              garage driveway + front path), the accessible stall nearest the yard's walk-in door. Customers park outside the
              gate, as at any tow yard, and walk in through the side door.
  STAFF       inside, nose to the south fence between the first barn and the shop: 15 stalls (finished cars waiting for pickup).
  TOW TRUCKS  4 long stalls (4.5 x 14 m) nose to the west fence, north of the first barn: wreckers and flatbeds.
  HOTSHOT     4 long back-in stalls (4.5 x 22 m) along the east fence between the shop's bays and the second barn: truck +
              gooseneck trailer.
  IMPOUND     inside the pen: a north row, a back-to-back double row and a short south row (29 stalls) round two one-way-free
              aisles, the entry lane from the pen gate kept clear; the pen's two power poles get yellow hatched islands.
  KEEP CLEAR  yellow hatched aprons in front of the shop's two north bays and its west roll-up door.
  ARROWS      from the main gate: in, to the pen gate, to the shop.
White paint for cars, yellow for trucks / keep-clear. All world coordinates (x, y), metres.
paint() -> list of ('line', x0, y0, x1, y1, colour, width) | ('arrow', x, y, heading_deg, length) | ('sign', x, y, heading_deg, size)
Run: py -3 parking_plan.py    draws ../review/parking_plan.png (the layout over the site outlines, for Antonio)"""
import math
import site_plan as SP

STALL, CAR_DEPTH, LINE_W, BOLD_W = 3.0, 5.5, 0.12, 0.15
POLES_IN_PEN = [(2416.4, 3127.3), (2425.8, 3142.7)]                         # prop_telegraph_01e (kept)
# the buildings' real footprints (x0, y0, x1, y1): the shop's walls (move_shop.py, its doors), the barns' geometry (barn_copy.py)
BUILT = {(2404.0, 3027.0, 2429.6, 3052.2): 'SHOP', (2329.0, 3026.2, 2347.1, 3059.2): 'BARN', (2416.7, 3087.6, 2434.8, 3120.6): 'BARN 2'}


def _row(x0, n, y0, y1, colour='white', w=LINE_W, step=STALL):
    """n stalls side by side along x from x0, their separators running y0..y1."""
    return [('line', x0 + k * step, y0, x0 + k * step, y1, colour, w) for k in range(n + 1)]


def _col(y0, n, x0, x1, colour='yellow', w=BOLD_W, step=4.5):
    """n long stalls one above the other along y from y0, their separators running x0..x1."""
    return [('line', x0, y0 + k * step, x1, y0 + k * step, colour, w) for k in range(n + 1)]


def _box(x0, y0, x1, y1, colour='yellow', w=BOLD_W):
    return [('line', x0, y0, x1, y0, colour, w), ('line', x1, y0, x1, y1, colour, w), ('line', x1, y1, x0, y1, colour, w),
            ('line', x0, y1, x0, y0, colour, w)]


def _hatch(x0, y0, x1, y1, gap=1.4, w=0.25):
    """a yellow keep-clear box: its border plus 45-degree stripes clipped to it."""
    out = _box(x0, y0, x1, y1)
    c = x0 - y1 + gap / 2
    while c < x1 - y0:                                   # stripe x - y = c
        pts = []
        for x in (x0, x1):
            y = x - c
            if y0 <= y <= y1: pts.append((x, y))
        for y in (y0, y1):
            x = y + c
            if x0 < x < x1: pts.append((x, y))
        if len(pts) >= 2:
            (a, b), (p, q) = sorted(pts)[0], sorted(pts)[-1]
            if math.hypot(p - a, q - b) > 0.3: out.append(('line', a, b, p, q, 'yellow', w))
        c += gap
    return out


def paint():
    P = []
    # ---- customers, outside the gate along the lawn edge (y 3120): nose north, the lawn's concrete edging is the stop line
    P += _row(2310.0, 8, 3114.0, 3119.5)                                      # west of the garage driveway (pole at 2337.5 clear)
    P += _row(2349.0, 7, 3114.0, 3119.5)                                      # east of the front path, up to the gate approach
    P += [('sign', 2368.5, 3116.6, 0.0, 1.6)]                                 # accessible stall: nearest the walk-in door
    # ---- staff / finished cars: nose to the south fence, first barn (x 2347.1) to the shop's lamp post (x 2396.8)
    P += _row(2349.0, 15, 3026.6, 3032.1)
    # ---- tow trucks: nose to the west fence, north of the first barn (y 3059.2) to the fence corner (y 3079.9)
    P += _col(3060.5, 4, 2329.4, 2343.4)
    # ---- hotshot rigs: back-in along the east fence, the bay apron (to y 3064) to the second barn (y 3087.6)
    P += _col(3066.5, 4, 2412.5, 2434.6)
    # ---- keep clear: the two north bays (x 2415.5..2427.0 at y 3052) and the west roll-up (y 3040.7..3048.9 at x 2404)
    P += _hatch(2414.0, 3052.6, 2428.5, 3064.0)
    P += _hatch(2392.0, 3040.2, 2403.6, 3049.4)
    # ---- the impound pen (y 3121.5..3160.7; gate x 2400..2408 on its south line)
    P += _row(2403.5, 10, 3155.0, 3160.3)                                     # north row, nose to the fence
    P += _row(2403.0, 7, 3137.0, 3148.0)                                      # double row, back to back ...
    P += [('line', 2403.0, 3142.5, 2424.0, 3142.5, 'white', LINE_W)]          # ... split down the middle
    P += _row(2419.0, 5, 3122.2, 3127.7)                                      # south row, east of the entry lane and the pole
    for x, y in POLES_IN_PEN: P += _hatch(x - 1.6, y - 1.6, x + 1.6, y + 1.6, gap=1.0, w=0.2)
    # ---- arrows: in from the main gate, then to the pen gate and to the shop
    P += [('arrow', 2390.0, 3106.0, -25.0, 3.2), ('arrow', 2404.0, 3110.0, 90.0, 3.2), ('arrow', 2400.0, 3082.0, -90.0, 3.2),
          ('arrow', 2404.0, 3134.0, 90.0, 3.2)]
    return P


def counts():
    return {'customers': 15, 'staff': 15, 'tow trucks': 4, 'hotshot': 4, 'impound': 10 + 14 + 5}


if __name__ == '__main__':
    from PIL import Image, ImageDraw, ImageFont
    from pathlib import Path
    X0, X1, Y0, Y1, S = 2290.0, 2445.0, 3018.0, 3168.0, 9.0
    W, H = int((X1 - X0) * S), int((Y1 - Y0) * S)
    im = Image.new('RGB', (W, H), (236, 226, 200)); d = ImageDraw.Draw(im)
    p = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
    try: F = ImageFont.truetype('arialbd.ttf', 26); f = ImageFont.truetype('arial.ttf', 20)
    except OSError: F = f = ImageFont.load_default()
    d.polygon([p(*q) for q in SP.HOUSE_LOT], fill=(150, 150, 150)); d.polygon([p(*q) for q in SP.YARD], fill=(130, 130, 130))
    d.polygon([p(*q) for q in SP.DRIVEWAY], fill=(150, 150, 150))
    for x in range(int(X0), int(X1), 2):
        for y in range(int(Y0), int(Y1), 2):
            if SP.in_lawn(x + 1, y + 1): d.rectangle([p(x, y + 2), p(x + 2, y)], fill=(120, 165, 90))
    d.line([p(*q) for q in SP.YARD + [SP.YARD[0]]], fill=(20, 20, 20), width=5)
    d.line([p(*SP.PEN_W), p(SP.L[4][0], SP.PEN_LINE_Y)], fill=(20, 20, 20), width=5)
    for (a, b, c, e), t in BUILT.items():
        d.rectangle([p(a, e), p(c, b)], fill=(95, 95, 105)); d.text(p(a + 2, e - 2), t, font=F, fill='white')
    d.rectangle([p(SP.HOUSE_RECT[0], SP.HOUSE_RECT[3]), p(SP.HOUSE_RECT[1], SP.HOUSE_RECT[2])], fill=(200, 110, 80)); d.text(p(SP.HOUSE_RECT[0] + 2, SP.HOUSE_RECT[3] - 2), 'HOUSE', font=F, fill='white')
    col = {'white': (255, 255, 255), 'yellow': (245, 200, 40)}
    for it in paint():
        if it[0] == 'line': d.line([p(it[1], it[2]), p(it[3], it[4])], fill=col[it[5]], width=max(2, int(it[6] * S * 1.6)))
        elif it[0] == 'arrow':
            x, y, h, L = it[1:]; a = math.radians(h); tip = (x + math.cos(a) * L / 2, y + math.sin(a) * L / 2); tail = (x - math.cos(a) * L / 2, y - math.sin(a) * L / 2)
            d.line([p(*tail), p(*tip)], fill=(255, 255, 255), width=6)
            for s in (2.5, -2.5): d.line([p(*tip), p(tip[0] - math.cos(a + s * .3) * 1.2, tip[1] - math.sin(a + s * .3) * 1.2)], fill=(255, 255, 255), width=6)
        else: d.ellipse([p(it[1] - .8, it[2] + .8), p(it[1] + .8, it[2] - .8)], fill=(60, 110, 230))
    for x, y in POLES_IN_PEN + [(2337.5, 3113.2), (2382.3, 3026.3), (2354.6, 3055.5), (2369.5, 3050.3), (2333.8, 3080.2), (2349.1, 3079.6)]:
        d.ellipse([p(x - .5, y + .5), p(x + .5, y - .5)], fill=(90, 60, 30))
    for x, y in ((2366.3, 3037.1), (2366.9, 3068.4), (2409.3, 3070.7), (2396.8, 3026.7)):
        d.ellipse([p(x - .5, y + .5), p(x + .5, y - .5)], fill=(30, 30, 30))
    for x, y, t in ((2312, 3112.5, 'CUSTOMERS (8)'), (2350, 3112.5, 'CUSTOMERS (7, accessible at the end)'), (2350, 3036, 'STAFF / FINISHED CARS (15)'),
                    (2329.5, 3083.5, 'TOW TRUCKS (4)'), (2397, 3088.0, 'HOTSHOT RIGS (4, back in)'), (2405, 3168, 'IMPOUND (29)'),
                    (2414, 3067, 'KEEP CLEAR: BAYS'), (2378, 3053, 'KEEP CLEAR'), (2384, 3101, 'MAIN GATE'), (2398, 3124.5, 'PEN GATE')):
        d.text(p(x, y), t, font=f, fill=(10, 10, 10))
    d.text((12, 10), 'Graveyard tow yard: parking (north up). Brown dots = power poles, black = lamp posts. ' +
           ', '.join(f'{k} {v}' for k, v in counts().items()), font=f, fill=(10, 10, 10))
    out = Path(__file__).resolve().parents[1] / 'review' / 'parking_plan.png'; im.save(out); print('PARKING_PLAN', out, counts())
