"""Area 3 basement drawings: the B1 plan (aisles with their one-way arrows, the two ramp lanes and doors, the U-turn and the IN turn at
the van's radius, parking bays, the workshop, fuel island, wash bay, columns, the police stair) and the ramp section (both lanes'
profile from the street to B1, L1's slab, the door heads, the van's 2.8 m headroom). Run: py -3 jc3_plandraw_pgarage.py <plan.png> <section.png>"""
import sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_pgarage as G, jc3_police as P, p2_plan as PL
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 13), ImageFont.truetype('arialbd.ttf', 15), ImageFont.truetype('arialbd.ttf', 22)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
def plan(out):
    U0, U1, V0, V1, S = 6.0, 66.0, -64.0, -3.0, 22
    W, H = int((U1 - U0) * S), int((V1 - V0) * S) + 110
    im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, v: ((u - U0) * S, (V1 - v) * S + 110)
    def rect(r, fill=None, ol=None, w=1): d.rectangle([X(r[0], r[3]), X(r[1], r[2])], fill=fill, outline=ol, width=w)
    def line(p, q, c, w=2): d.line([X(*p), X(*q)], fill=c, width=w)
    def text(u, v, s, f=F1, c=(50, 50, 50)): d.text(X(u, v), s, fill=c, font=f, anchor='mm')
    def arrow(p, q, c=(200, 40, 40)):
        line(p, q, c, 4); a = math.atan2(q[1] - p[1], q[0] - p[0])
        for da in (2.6, -2.6): line(q, (q[0] + 1.0 * math.cos(a + da), q[1] + 1.0 * math.sin(a + da)), c, 4)
    b = PL.B['police']['box']; rect((b[0], b[1], b[2], b[3]), (188, 170, 150), (90, 70, 54), 2)
    rect(G.B1, (222, 222, 218), (60, 60, 60), 3)
    for i, (u0, u1, v0, v1, f) in enumerate(G.ROWS): rect((u0, u1, v0, v1), (205, 214, 226), (120, 120, 120))
    for u, v, h, row in G.bays():
        r = G.ROWS[row]
        if r[4] in ('u-', 'u+'): line((r[0], v - G.BAY_W / 2), (r[1], v - G.BAY_W / 2), (255, 255, 255), 2)
        else: line((u - G.BAY_W / 2, r[2]), (u - G.BAY_W / 2, r[3]), (255, 255, 255), 2)
    rect(G.WORKSHOP, (236, 214, 170), (140, 100, 40)); text((G.WORKSHOP[0] + G.WORKSHOP[1]) / 2, (G.WORKSHOP[2] + G.WORKSHOP[3]) / 2,
                                                            'FLEET WORKSHOP: 3 service bays with car lifts, workbenches, tool chests, tyre racks, oil drums, jerry cans, parts shelf, air compressor', F1)
    rect(G.FUEL, (230, 120, 60), (120, 50, 20)); text((G.FUEL[0] + G.FUEL[1]) / 2, G.FUEL[2] - 0.8, 'fuel island (2 pumps)', F1)
    rect(G.WASH, (150, 200, 230), (40, 90, 140)); text((G.WASH[0] + G.WASH[1]) / 2, (G.WASH[2] + G.WASH[3]) / 2, 'wash bay', F2)
    rect(G.PARALLEL, (205, 214, 226), (120, 120, 120)); text((G.PARALLEL[0] + G.PARALLEL[1]) / 2, -40.0, 'parallel', F1)
    for u, v in G.COLUMNS: rect((u - 0.25, u + 0.25, v - 0.25, v + 0.25), (90, 90, 90))
    rect((u0 := G.U_FOOT, G.B1[1] + G.RW, G.TRENCH[0], G.TRENCH[1]), (180, 180, 172), (60, 60, 60), 2)
    rect((G.U_FOOT, G.B1[1] + G.RW, G.DIV[0], G.DIV[1]), (90, 90, 90))
    text(33.0, G.IN_C, 'IN ramp (down, 1:7, 4 m curves)', F2); text(33.0, G.OUT_C, 'OUT ramp (up)', F2)
    for k, (a0, a1) in G.DOORS.items():
        line((b[1], a0), (b[1], a1), (20, 20, 20), 8); text(b[1] + 2.2, (a0 + a1) / 2, f'{k.upper()} door', F2)
        rect((b[1], 62.7, a0 - 0.3, a1 + 0.3), (200, 200, 196), (90, 90, 90))
        for u in [45.8 + 1.7 * i for i in range(10)]:
            for v in (a0 - 0.55, a1 + 0.55): x, y = X(u, v); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(60, 60, 60))
    text(54.0, -57.6, 'two driveways: Rockstar concrete, dipped kerbs at Innocence Blvd, prop_bollard_04 both sides of each', F1)
    # the one-way loop: the plan's own drive route (jc3_pgarage.loop_route: the rig drive and the swept-path gate use the same points)
    R = [(u, v, spd) for u, v, spd in G.loop_route() if u <= G.U_TOP + 1.0]
    for (pu, pv, _), (qu, qv, sq) in zip(R, R[1:]):                       # red forward, blue reversing (out of the test bay)
        p, q = (pu, pv), (qu, qv)
        if sq < 0: line(p, q, (40, 90, 200), 4)
        elif math.dist(p, q) < 8.0: line(p, q, (200, 40, 40), 4)
        else: arrow(p, q)
    arrow(((G.MID_AISLE[0] + G.MID_AISLE[1]) / 2, -14.0), ((G.MID_AISLE[0] + G.MID_AISLE[1]) / 2, G.RET_V + 2.5))
    bu, bv = G.drive_bay()[:2]; text(bu, bv, 'test bay', F1)
    text(G.IN_X + 2.0, -30.0, 'IN lane north', F1); text(G.UT_C[0] - 2.5, G.UT_C[1], f'U-turn r {G.UT_R}', F1)
    S_ = P.STAIR_B
    rect(S_, (196, 196, 204), (60, 60, 60), 2); text((S_[0] + S_[1]) / 2, (S_[2] + S_[3]) / 2, 'police stair (B1-L1-L2)', F1)
    d.rectangle([0, 0, W, 100], fill=(30, 30, 34))
    d.text((12, 10), f'Police HQ basement B1 (floor {G.ZB}, clear {G.CEIL_B - G.ZB:.1f} m): {len(G.bays())} parking bays + workshop, fuel, wash - lot frame, m', fill=(255, 255, 255), font=F3)
    d.text((12, 44), 'red = the drive route (jc3_pgarage.loop_route): IN ramp -> west aisle north -> north aisle east -> east aisle south -> return aisle west (test bay: in, blue = backing out) -> U-turn -> OUT ramp',
           fill=(220, 220, 220), font=F1)
    d.text((12, 66), f'car centre line; IN turn r {G.IN_R}, corners r {G.RC}, U-turn r {G.UT_R}; IN lane {G.IN_X:.2f} vs U-turn west {G.UT_C[0] - G.UT_R:.2f}; swept-path gate: jc3_drive_sweep.py; grey squares = columns',
           fill=(220, 220, 220), font=F1)
    im.save(out); print('PLAN_DRAWN', out)
def section(out):
    U0, U1, Z0, Z1, S = 15.0, 66.0, 23.5, 36.5, 30
    W, H = int((U1 - U0) * S), int((Z1 - Z0) * S) + 90
    im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, z: ((u - U0) * S, (Z1 - z) * S + 90)
    def rect(u0, u1, z0, z1, fill, ol=None): d.rectangle([X(u0, z1), X(u1, z0)], fill=fill, outline=ol)
    rect(U0, 62.7, 24.8, PL.SLAB, (200, 190, 170)); rect(45.1, 62.7, PL.SLAB - 0.05, PL.SLAB, (120, 120, 120))
    rect(U0, P.EI, G.CEIL_B, P.P1, (150, 150, 150)); rect(U0, P.EI, P.P2 - 0.4, P.P2, (150, 150, 150)); rect(U0, P.EI, P.CEIL, P.P3L, (150, 150, 150))
    rect(U0, G.B1[1], G.ZB - 0.4, G.ZB, (150, 150, 150))
    us = [G.U_FOOT + i * 0.25 for i in range(int((G.U_TOP - G.U_FOOT) / 0.25) + 1)]
    pts = [X(u, G.ramp_z(u)) for u in us] + [X(G.U_TOP, G.ramp_z(G.U_TOP) - 0.3), X(G.U_FOOT, G.ZB - 0.3)]
    rect(G.B1[0], G.B1[1], G.ZB, G.CEIL_B, (255, 255, 255))                  # B1's space
    rect(G.U_FOOT, P.EI, G.ramp_z(G.U_FOOT), P.P1, (255, 255, 255))         # L1's floor opened over the ramp
    d.polygon(pts, fill=(150, 150, 140), outline=(40, 40, 40))              # the ramp slab
    for u in us[::4]: zt = G.ramp_z(u); d.line([X(u, zt), X(u, zt + 2.8)], fill=(120, 170, 220), width=1)
    rect(P.EI, P.EI + 0.45, ZD := G.ZD, ZD + 3.0, (40, 40, 40)); rect(P.EI, P.EI + 0.45, ZD + 3.0, ZD + 3.25, (90, 90, 90))
    for u, z, s in ((G.U_TOP, G.ZD + 0.3, f'door {G.ZD:.2f}'), (G.U_FOOT, G.ZB + 0.3, f'foot {G.ZB:.2f}'), (33.0, G.ramp_z(33.0) + 0.3, '1 : 7'),
                    (40.0, G.ramp_z(40.0) + 0.3, '4 m curve'), (24.0, G.ramp_z(24.0) + 0.3, '4 m curve'), (18.0, P.P1 + 0.3, 'L1 28.8'),
                    (18.0, P.P2 + 0.3, 'L2 32.0'), (18.0, G.ZB + 0.3, 'B1 25.6'), (55.0, PL.SLAB + 0.3, 'plaza / driveway (at grade)')):
        d.text(X(u, z), s, fill=(30, 30, 30), font=F1, anchor='mm')
    d.rectangle([0, 0, W, 80], fill=(30, 30, 34))
    d.text((12, 10), 'Police HQ garage: section along both ramp lanes (IN and OUT have the same profile), u -> (east = right), z', fill=(255, 255, 255), font=F3)
    d.text((12, 46), 'blue ticks = the van envelope (2.8 m) over the ramp: L1 is open over the whole ramp (white), the door head clears 3.0 m; B1 clear 2.8 m',
           fill=(220, 220, 220), font=F1)
    im.save(out); print('SECTION_DRAWN', out)
plan(sys.argv[1]); section(sys.argv[2])
