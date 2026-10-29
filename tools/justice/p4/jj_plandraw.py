"""Area 4 (Jail I) plan drawings, lot frame: L1 (sally port, booking, holding, property, stair, the secure corridor + the route options to
the courts tower's secure lift), L2 (the cell block's lower tier + the dayroom) and L3 (the upper tier, walkways, bridge). Reads jj_plan,
and out/jj_layout.json when the build has run (props from their real bounds, sit points).
Run: py -3 jj_plandraw.py <out_L1.png> <out_L2.png>"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
JL = Path(__file__).resolve().parent; sys.path.insert(0, str(JL))
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
import jj_plan as J
PL = J.PL
LAY = JL / OD / 'jj_layout.json'
L = json.load(open(LAY)) if LAY.exists() else None
A = {k.lower(): v for k, v in json.load(open(JL / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()} if (JL / 'survey/arch_ytyp.json').exists() else {}
def bb(m): a = A[m.lower()]; f = lambda s: [float(x[2:]) for x in s.split()]; return f(a['bbMin']), f(a['bbMax'])
def foot(m, u, v, h):
    lo, hi = bb(m); t = math.radians(h); c, s = math.cos(t), math.sin(t)
    return [(u + x * c - y * s, v + x * s + y * c) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
COL = {'sally': (205, 205, 200), 'sallyv': (226, 206, 206), 'book': (236, 228, 214), 'hold': (226, 206, 206), 'prop': (214, 222, 236),
       'stair': (200, 200, 205), 'corr': (226, 206, 206), 'block': (232, 226, 210), 'dstair': (200, 200, 205), 'tunnel': (226, 206, 206)}
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 14), ImageFont.truetype('arial.ttf', 18), ImageFont.truetype('arialbd.ttf', 22)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
def draw(level, out, title, notes, box, routes=False):
    U0, U1, V0, V1 = box; S = 22 if routes else 30
    W, H = int((U1 - U0) * S), int((V1 - V0) * S) + 150
    im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, v: ((u - U0) * S, (V1 - v) * S + 150)
    def rect(u0, u1, v0, v1, fill, ol=None, w=1): d.rectangle([X(u0, v1), X(u1, v0)], fill=fill, outline=ol, width=w)
    def line(p, q, c, w=2): d.line([X(*p), X(*q)], fill=c, width=w)
    jb = J.JBOX; rect(jb[0], jb[1], jb[2], jb[3], (190, 170, 150), (90, 70, 54), 2)
    d.text(X(jb[0] + 0.5, jb[3] - 0.5), 'Jail I (hull)', fill=(70, 50, 40), font=F1)
    if routes:
        for k in ('atrium', 'tower', 'police'):
            for r in PL.rects(k): rect(r[0], r[1], r[2], r[3], (222, 226, 232) if k == 'atrium' else (200, 188, 172), (110, 110, 120), 2)
        d.text(X(0.0, 30.0), 'GALLERIA (public)', fill=(80, 80, 110), font=F2, anchor='mm')
        d.text(X(32.0, 52.0), 'COURTS TOWER lobby (public)', fill=(80, 60, 40), font=F2, anchor='mm')
        sl = PL.TOWER_SECLIFT; rect(sl[0], sl[1], sl[2], sl[3], (150, 60, 60), (0, 0, 0), 2); d.text(X(sl[1] + 0.3, sl[2] + 1.5), 'secure lift', fill=(150, 30, 30), font=F2, anchor='lm')
        co = PL.TOWER_CORE; rect(co[0], co[1], co[2], co[3], (170, 160, 150), (0, 0, 0), 1); d.text(X((co[0] + co[1]) / 2, (co[2] + co[3]) / 2), 'core', fill=(40, 40, 40), font=F1, anchor='mm')
        if level == 'L1':                                              # the tunnel 6 m below, dashed
            for u0, u1, v0, v1 in J.R['tunnel']['rects']:
                for a, b in (((u0, v0), (u1, v0)), ((u1, v0), (u1, v1)), ((u1, v1), (u0, v1)), ((u0, v1), (u0, v0))):
                    n = max(1, int(math.dist(a, b) / 0.8))
                    for i in range(0, n, 2): line((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n), (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n), (200, 30, 30), 3)
            d.text(X(12.0, 32.0), 'tunnel below (B1, z 22.8) - nothing changes up here', fill=(200, 30, 30), font=F2, anchor='mm')
    zc = {'B1': J.B1, 'L1': J.G, 'L2': J.L2, 'L3': J.TIER2}[level]
    for k, r in J.R.items():
        if not (r['z0'] - 0.5 <= zc <= r['z1'] - 0.3): continue
        for u0, u1, v0, v1 in r['rects']: rect(u0, u1, v0, v1, COL[k], (80, 80, 80), 2)
        u0, u1, v0, v1 = r['rects'][0]; d.text(X((u0 + u1) / 2, (v0 + v1) / 2), k, fill=(40, 40, 40), font=F3, anchor='mm')
    if L:
        for b in L.get('fit_boxes', []):
            if b[4] - 0.5 <= zc <= b[5] + 0.3 or (zc - 0.01 <= b[4] <= zc + 2.0): rect(b[0], b[1], b[2], b[3], (150, 120, 90))
        for q in L['placed']:
            if zc - 0.6 <= q['base'] <= zc + 2.0 and q['model'].lower() in A:
                d.polygon([X(*p) for p in foot(q['model'], q['u'], q['v'], q['heading'])], fill=(70, 110, 160), outline=(0, 0, 0))
        for s in L['seats']:
            if zc - 0.2 <= s[2] <= zc + 1.2: x, y = X(s[0], s[1]); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(230, 126, 34))
    if level in ('L1', 'B1'):
        for base, dd, zb, zt, lane in J.ds_flights():
            if level == 'B1' and zb > J.B1 + 1: continue
            a0, a1 = sorted((base, base + dd * 14 * J.GO)); rect(lane[0], lane[1], a0, a1, (120, 120, 120))
            for k in range(15): y0 = base + dd * k * J.GO; line((lane[0], y0), (lane[1], y0), (60, 60, 60), 1)
            d.text(X((lane[0] + lane[1]) / 2, a0 - 0.5), 'down' if level == 'L1' else 'up', fill=(0, 0, 0), font=F1, anchor='mm')
    if level == 'B1':
        sc = J.SEC_CAB; rect(sc[0], sc[1], sc[2], sc[3], (150, 60, 60), (0, 0, 0), 2); d.text(X(J.CAB_C, sc[2] - 0.6), 'secure lift B1 stop', fill=(150, 30, 30), font=F2, anchor='mm')
        line((J.CAB_C - 0.65, J.CAB_EP - 0.15), (J.CAB_C + 0.65, J.CAB_EP - 0.15), (20, 20, 20), 5)
        rect(J.CAB_C - 0.65, J.CAB_C + 0.65, J.CAB_EP, J.CAB_EP + 1.5, None, (230, 126, 34), 2); d.text(X(J.CAB_C, J.CAB_EP + 2.2), 'landing 1.5 m', fill=(230, 126, 34), font=F1, anchor='mm')
        d.text(X(2.6, 31.5), 'under the GALLERIA', fill=(80, 80, 110), font=F2, anchor='mm'); d.text(X(24.0, 31.5), 'under the COURTS TOWER lobby', fill=(80, 60, 40), font=F2, anchor='mm')
    if level == 'L1':
        p = J.PLATFORM; rect(p[0], p[1], p[2], p[3], (180, 180, 170), (0, 0, 0)); d.text(X((p[0] + p[1]) / 2, 19.0), 'platform', fill=(0, 0, 0), font=F1, anchor='mm')
        rp = J.RAMP; rect(rp[0], rp[1], rp[2], rp[3], (200, 190, 150), (0, 0, 0)); d.text(X((rp[0] + rp[1]) / 2, 11.5), 'ramp', fill=(0, 0, 0), font=F1, anchor='mm')
        for nm, (w, h, l) in J.VEHICLES.items():
            if nm != 'policet': continue
            rect(J.DRIVE_STOP - l, J.DRIVE_STOP, J.DRIVE_V - w / 2, J.DRIVE_V + w / 2, None, (30, 90, 200), 3)
            d.text(X(J.DRIVE_STOP - l / 2, J.DRIVE_V), 'transport van 6.2 x 2.3', fill=(30, 90, 200), font=F1, anchor='mm')
        line((J.JBOX[0] - 4, J.DRIVE_V), (J.DRIVE_STOP, J.DRIVE_V), (30, 90, 200), 1)
        s0, s1 = J.SALLY['s']; line((J.JBOX[0], s0), (J.JBOX[0], s1), (31, 119, 180), 7); d.text(X(J.JBOX[0] - 0.3, (s0 + s1) / 2), 'roll-up 6.22 m', fill=(31, 119, 180), font=F1, anchor='rm')
        for base, dd, zb, zt, lane in J.st_flights():
            a0, a1 = sorted((base, base + dd * (J.ST_RISERS - 1) * J.GO)); rect(a0, a1, lane[0], lane[1], (120, 120, 120))
            for k in range(J.ST_RISERS - 1): x0 = base + dd * k * J.GO; line((x0, lane[0]), (x0, lane[1]), (60, 60, 60), 1)
            d.text(X(a1 + 0.1, (lane[0] + lane[1]) / 2), 'up' if zb < J.G + 1 else '', fill=(0, 0, 0), font=F1, anchor='lm')
        for k in range(J.CELLS_HOLD):
            v = k * J.HOLD_P; line((-14.0, v), (-10.8, v), (60, 60, 60), 3); d.text(X(-12.0, v + 2.2), f'HOLD {k + 1}', fill=(120, 30, 30), font=F2, anchor='mm')
    elif level != 'B1':
        for side, (plane, _) in J.BLOCK_FRONT.items():
            inner = J.B_IN[0] if side == 'w' else J.B_IN[1]
            line((plane, J.B_IN[2]), (plane, J.B_IN[3]), (60, 60, 60), 4)
            for k in range(J.BLOCK_CELLS):
                v = J.cell_v0(k) + J.CELL_W; line((inner, v), (plane, v), (60, 60, 60), 3)
                d.text(X((inner + plane) / 2, J.cell_v0(k) + J.CELL_W / 2), f'{side.upper()}{"1" if level == "L2" else "2"}{k + 1:02d}', fill=(90, 60, 40), font=F1, anchor='mm')
        if level == 'L3':
            b = J.BRIDGE; rect(b[0], b[1], b[2], b[3], (170, 170, 175), (0, 0, 0))
            for u0, u1 in ((J.WEST_FRONT + 0.1, J.WEST_FRONT + 0.1 + J.WALK_W), (J.EAST_FRONT - 0.1 - J.WALK_W, J.EAST_FRONT - 0.1)):
                rect(u0, u1, J.B_IN[2], J.B_IN[3], (170, 170, 175), (0, 0, 0))
            d.text(X(-23.0, 33.0), 'open to the dayroom below', fill=(90, 90, 90), font=F2, anchor='mm')
        a0, a1 = J.TSTAIR_W; rect(a0, a1, J.TSTAIR_BASE - 0.27, J.BRIDGE[2], (120, 120, 120))
        for k in range(J.TSTAIR_RISERS): line((a0, J.TSTAIR_BASE + k * 0.27), (a1, J.TSTAIR_BASE + k * 0.27), (60, 60, 60), 1)
    for dd in J.DOORS:
        u, v, z = dd['pos']
        if abs((z - J.LEAF_H / 2) - zc) > 0.3: continue
        t = math.radians(dd['heading']); ex, ey = -math.cos(t) * J.LEAF, -math.sin(t) * J.LEAF
        line((u, v), (u + ex, v + ey), (20, 20, 20), 4)
        x, y = X(u, v); r = J.LEAF * S; d.ellipse([x - r, y - r, x + r, y + r], outline=(170, 170, 170))
    for o in J.OPENINGS:
        if o.get('glass') and abs(o['z0'] - zc - 1.1) < 0.5: line((o['plane'], o['a0']), (o['plane'], o['a1']), (31, 119, 180), 5)
    d.rectangle([0, 0, W, 142], fill=(30, 30, 34)); d.text((14, 10), title, fill=(255, 255, 255), font=F3)
    for i, n in enumerate(notes): d.text((14, 46 + 22 * i), n, fill=(220, 220, 220), font=F1)
    im.save(out); print('PLAN_DRAWN', out)
def section(out):
    """side section along the tunnel (cut at v 27.3, looking north): Jail I, the galleria, the tower; the secure stair down, the tunnel,
    the secure lift shaft B1 -> L5 and its stops."""
    U0, U1, Z0, Z1, S = -48.0, 54.0, 18.0, 64.0, 18
    W_, H_ = int((U1 - U0) * S), int((Z1 - Z0) * S) + 150
    im = Image.new('RGB', (W_, H_), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, z: ((u - U0) * S, (Z1 - z) * S + 150)
    def rect(u0, u1, z0, z1, fill, ol=None, w=1): d.rectangle([X(u0, z1), X(u1, z0)], fill=fill, outline=ol, width=w)
    rect(U0, U1, Z0, PL.SLAB, (196, 180, 150)); d.text(X(U0 + 1, PL.SLAB - 1.0), 'ground', fill=(90, 70, 40), font=F2, anchor='lm')
    for k, col in (('jail1', (190, 170, 150)), ('atrium', (222, 226, 232)), ('tower', (214, 206, 192))):
        for r in PL.rects(k):
            if r[2] <= 27.3 <= r[3]: rect(r[0], r[1], PL.G, min(PL.B[k]['top'], Z1 - 0.5), col, (90, 70, 54), 2)
    for k, lv in (('jail1', [J.G, J.L2, J.TIER2]), ('tower', PL.B['tower']['levels'][:7])):
        r = PL.rects(k)[0]
        for z in lv: d.line([X(r[0], z), X(r[1], z)], fill=(120, 110, 100), width=2)
    d.text(X(-27.0, J.G + 1.5), 'Jail I  L1 (booking)', fill=(60, 40, 30), font=F2, anchor='mm'); d.text(X(-27.0, J.L2 + 1.4), 'L2-L3 cell block', fill=(60, 40, 30), font=F2, anchor='mm')
    d.text(X(2.6, 36.0), 'GALLERIA (untouched)', fill=(80, 80, 110), font=F2, anchor='mm'); d.text(X(24.0, 31.0), 'tower lobby (untouched)', fill=(80, 60, 40), font=F2, anchor='mm')
    ds = J.R['dstair']['rects'][0]; rect(ds[0], ds[1], J.B1 - J.SLAB_T, J.G + J.CEIL, (200, 200, 205), (0, 0, 0), 2)
    d.text(X((ds[0] + ds[1]) / 2, J.B1 + 4.4), 'secure', fill=(0, 0, 0), font=F1, anchor='mm'); d.text(X((ds[0] + ds[1]) / 2, J.B1 + 3.6), 'stair', fill=(0, 0, 0), font=F1, anchor='mm')
    t = J.R['tunnel']['rects'][0]; rect(t[0], t[1], J.B1 - J.SLAB_T, J.R['tunnel']['z1'] + J.ROOF_T, (226, 206, 206), (200, 30, 30), 3)
    d.text(X((t[0] + t[1]) / 2, J.B1 + 1.4), 'TUNNEL  floor %.1f  2.8 m clear  2.4 m wide' % J.B1, fill=(150, 20, 20), font=F3, anchor='mm')
    sl = PL.TOWER_SECLIFT; LV = PL.B['tower']['levels']
    rect(sl[0], sl[1], J.B1, LV[5], None, (150, 60, 60), 3)
    for name, z in (('B1', J.B1), ('L3', LV[2]), ('L5', LV[4])):
        rect(sl[0] + 0.2, sl[1] - 0.2, z, z + 2.8, (150, 60, 60)); d.text(X(sl[1] + 0.6, z + 1.2), 'secure lift ' + name, fill=(150, 30, 30), font=F2, anchor='lm')
    d.text(X(sl[1] + 0.6, LV[2] + 2.6), '-> holding -> defendant door, courtroom 3A', fill=(150, 30, 30), font=F1, anchor='lm')
    for z, lab in ((PL.SLAB, 'lot slab %.2f' % PL.SLAB), (PL.G - 1.0, 'hull bottoms 27.8'), (J.R['tunnel']['z1'] + J.ROOF_T, 'tunnel top 25.8')):
        d.text(X(U1 - 0.5, z + 0.3), lab, fill=(60, 60, 60), font=F1, anchor='rm')
    d.rectangle([0, 0, W_, 142], fill=(30, 30, 34)); d.text((14, 10), 'Justice Center area 4: section along the prisoner tunnel (cut at v 27.3, looking north; lot frame, z = world z)', fill=(255, 255, 255), font=F3)
    d.text((14, 50), 'Jail I L1 -> secure stair (30 risers) -> B1 tunnel under the galleria and the tower lobby -> the secure lift B1 stop -> L3 / L5 holding', fill=(220, 220, 220), font=F1)
    im.save(out); print('SECTION_DRAWN', out)
# the route options to the courts tower's secure lift (history: superseded by the tunnel, Antonio 2026-10-29) (jj_hooks.ROUTE): drawn on the L1 site plan for Antonio's choice
ROUTES = [('A (recommended)', [(-11.0, 47.8), (-8.5, 47.8), (13.7, 47.8), (33.1, 47.8), (33.1, 27.4)], (200, 30, 30)),
          ('B', [(-15.0, 24.3), (-8.5, 24.3), (31.2, 24.3)], (30, 140, 60))]
if __name__ == '__main__':
    J.plan_doors()
    notes = ['grey = Jail I hull (solid), coloured = MLO jc_jail rooms; black = door leaves + swing; blue = glass (vision windows) / roll-up door',
             'blue outline = the transport van (6.2 x 2.3 m) at its stop; it drives in along the blue line and backs out; police cars the same',
             'red dashed: the prisoner tunnel 6 m below (B1) - the galleria and the tower lobby are not touched']
    draw('L1', sys.argv[1], 'Justice Center area 4: Jail I L1 - sally port, booking, holding, property, stair, secure corridor (lot frame, m)', notes,
         (-48.0, 52.0, -8.0, 66.0), routes=True)
    draw('L2', sys.argv[2], 'Justice Center area 4: Jail I L2 - the cell block: dayroom + lower tier (9 + 9 cells), stair arrival', notes[:1], (-46.0, -6.0, 14.0, 50.0))
    if len(sys.argv) > 3: draw('L3', sys.argv[3], 'Justice Center area 4: Jail I L3 - upper tier (9 + 9 cells), walkways, north bridge, tier stair', notes[:1], (-46.0, -6.0, 14.0, 50.0))
    if len(sys.argv) > 4: draw('B1', sys.argv[4], 'Justice Center area 4: B1 (z 22.8) - the secure stair down, the prisoner tunnel, the secure lift B1 stop', notes[:1], (-20.0, 40.0, 14.0, 36.0), routes=True)
    if len(sys.argv) > 5: section(sys.argv[5])
