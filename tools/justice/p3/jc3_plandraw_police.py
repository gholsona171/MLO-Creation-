"""Area 3 plan drawings (lot frame): Police HQ L1 and L2 from jc3_police - the rooms (MLO rooms in colour, the staff spaces inside
them outlined and named), the doors (portal doors magenta, inner doors black), the stair, the west / north window bays and the
colonnade glass (blue: limbo portals), the front desk counter, the garage door and Antonio's driveway (concrete strip, dipped kerb,
bollards) across the plaza to Innocence Blvd. Run: py -3 jc3_plandraw_police.py <out_L1.png> <out_L2.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_police as P, jc3_pgarage as GG, p2_plan as PL
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 13), ImageFont.truetype('arialbd.ttf', 15), ImageFont.truetype('arialbd.ttf', 22)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
COL = {'plobby': (232, 226, 210), 'pdesk': (214, 222, 236), 'pstaff1': (226, 232, 222), 'pgarage': (210, 210, 210), 'pstair': (196, 196, 204),
       'pstaff2': (226, 232, 222)}
def draw(level, out):
    U0, U1, V0, V1, S = 6.0, 66.0, -64.0, -3.0, 22
    W, H = int((U1 - U0) * S), int((V1 - V0) * S) + 110
    im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, v: ((u - U0) * S, (V1 - v) * S + 110)
    def rect(r, fill=None, ol=None, w=1): d.rectangle([X(r[0], r[3]), X(r[1], r[2])], fill=fill, outline=ol, width=w)
    def line(p, q, c, w=2): d.line([X(*p), X(*q)], fill=c, width=w)
    def text(u, v, s, f=F1, c=(50, 50, 50)): d.text(X(u, v), s, fill=c, font=f, anchor='mm')
    b = PL.B['police']['box']; rect((b[0], b[1], b[2], b[3]), (188, 170, 150), (90, 70, 54), 2)       # the facade ring
    rect((10.1, 37.9, -7.2, -3.0), (222, 214, 196)); text(24.0, -5.0, 'galleria (area 1)', F2)
    for v in P.voids(): rect(v[:4], (240, 238, 232))
    if level == 1:
        for k, rs in P.REGIONS.items():
            for r in rs: rect(r, COL[k], (120, 120, 120))
        for n, rs in P.SPACES1.items():
            for r in rs: rect(r, COL['pstaff1'], (120, 120, 120))
            text((rs[0][0] + rs[0][1]) / 2, (rs[0][2] + rs[0][3]) / 2, n)
        rect((P.U_FOOT, P.EI, P.SG, P.TRENCH_N), (180, 180, 172), (60, 60, 60), 2)
        for k, (a0, a1) in GG.LANES.items(): rect((P.U_FOOT, P.EI, a0, a1), (160, 160, 152)); text(33.0, (a0 + a1) / 2, f'{k.upper()} ramp (down to B1)', F1)
        for k, (a0, a1) in GG.DOORS.items(): line((PL.B['police']['box'][1], a0), (PL.B['police']['box'][1], a1), (40, 40, 40), 6)
        for k, r in (('PUBLIC LOBBY (double height)', P.REGIONS['plobby'][0]), ('public hall', P.REGIONS['plobby'][2]),
                     ('DESK OFFICE', P.REGIONS['pdesk'][0])):
            text((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, k, F2)
        line((P.LOB_W, P.COUNTER[0]), (P.LOB_W, P.COUNTER[1]), (200, 120, 20), 6); text(P.LOB_W + 2.2, sum(P.COUNTER) / 2, 'counter', F1)
        for k, (a0, a1) in GG.DOORS.items(): rect((PL.B['police']['box'][1], 65.6, a0 - 0.3, a1 + 0.3), (200, 200, 196), (90, 90, 90))
        text(55.0, -58.0, 'two driveways to Innocence Blvd, prop_bollard_04 lines', F1)
        for face, glass in (('E', P.EG), ('S', P.SG)):
            for run in PL.arcade_runs('police', next(f for f in PL.face_list('police') if f[0] == face)):
                a0, a1 = run[0][0], run[-1][1]
                if face == 'E': line((glass, a0), (glass, a1), (31, 119, 180), 4)
                else: line((a0, glass), (a1, glass), (150, 150, 150), 4); text(27.0, glass - 1.2, 'south colonnade glass: solid linings behind it (no see-out)', F1)
        F = P.P1
    else:
        for n, rs in P.SPACES2.items():
            for r in rs: rect(r, COL['pstaff2'], (120, 120, 120))
            text((rs[0][0] + rs[0][1]) / 2, (rs[0][2] + rs[0][3]) / 2, n)
        line((12.5, P.SG), (42.7, P.SG), (150, 150, 150), 4)
        for r in P.REGIONS['plobby'][:2]: rect(r, (250, 250, 250), (170, 170, 170)); text((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, 'lobby void (below)', F1)
        for k, r in P.SUITES.items(): rect(r, (214, 206, 230), (100, 80, 140)); text((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, k[1:], F1)
        for intr, obs, ax, plane, side in P.MIRROR: line((plane, P.MIRROR_SPAN[0]), (plane, P.MIRROR_SPAN[1]), (40, 160, 200), 6)
        F = P.P2
    for a0, a1, z0, z1 in P.west_bays(F): line((P.WI, a0), (P.WI, a1), (31, 119, 180), 4)
    for a0, a1, z0, z1 in P.north_bays(F): line((a0, P.NI_FACE), (a1, P.NI_FACE), (31, 119, 180), 4)
    rect(P.STAIR_B, COL['pstair'], (80, 80, 80)); text((P.STAIR_B[0] + P.STAIR_B[1]) / 2, (P.STAIR_B[2] + P.STAIR_B[3]) / 2, 'stair B1-L2', F1)
    for n, z, ax, plane, a0 in P.INNER_DOORS:
        if z != F: continue
        if ax == 'u': line((plane, a0), (plane, a0 + 1.4), (20, 20, 20), 5)
        else: line((a0, plane), (a0 + 1.4, plane), (20, 20, 20), 5)
    for n, frm, to, z, ax, plane, a0, kind in P.PORTAL_DOORS:
        if z != F: continue
        w = 2.7 if 'pair' in kind else 1.4
        if ax == 'u': line((plane, a0), (plane, a0 + w), (200, 60, 160), 7)
        else: line((a0, plane), (a0 + w, plane), (200, 60, 160), 7)
    d.rectangle([0, 0, W, 100], fill=(30, 30, 34))
    d.text((12, 10), f'Justice Center area 3: Police HQ L{level} (lot frame, m) - rooms of MLO jc_courts', fill=(255, 255, 255), font=F3)
    d.text((12, 44), 'magenta = doors on portals (front pair to the plaza, galleria link, staff doors), black = inner doors, blue = window bays / colonnade glass (see-out)',
           fill=(220, 220, 220), font=F1)
    d.text((12, 66), 'partitions meeting the west face land between its window bays; the staff sides are one MLO room per floor (inner doors without portals)',
           fill=(220, 220, 220), font=F1)
    im.save(out); print('PLAN_DRAWN', out)
draw(1, sys.argv[1]); draw(2, sys.argv[2])
