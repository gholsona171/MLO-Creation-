"""Route options for the prisoner link Jail I -> the courts tower's secure lift, drawn for Antonio's choice (lot frame, the style of
shots/p4_jail_plan_L1.png). Panels: C ground floor (the secure lift moved to the tower's NW corner, the short galleria corridor),
C on L3 (L5 the same: holding + secure corridor in the west ring, the courtroom's sides swapped; area 2's current positions ghosted in
grey), A ground floor for comparison (the 70 m corridor and the lobby strip it squeezes). Numbers from p2_plan / jc3_tower (read only).
Run: py -3 jj_routes_draw.py <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent / 'p3')]
import jj_plan as J
import jc3_tower as JT
PL = J.PL
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 14), ImageFont.truetype('arial.ttf', 17), ImageFont.truetype('arialbd.ttf', 20)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
S = 13                                                        # px per m
BOX = (-47.0, 53.0, 14.0, 60.0)                                # u0, u1, v0, v1 of each panel
PW, PH = int((BOX[1] - BOX[0]) * S), int((BOX[3] - BOX[2]) * S) + 40
RED, BLUE, GREEN, GREY, ORANGE = (200, 30, 30), (40, 90, 190), (40, 140, 60), (165, 165, 165), (230, 140, 20)
# ---- option C geometry ----
C_SHAFT = (14.45, 18.25, 46.6, 49.4)                          # the secure lift moved to the tower's NW corner (inside the W wall, at the
                                                              # galleria's north band - the only crossing that leaves the galleria in one piece)
C_CORR = (-8.5, 14.45, 46.6, 49.2)                            # galleria crossing (22 m) straight into the lift's west door
C_SEC_RING = (14.35, 19.05, 26.0, 41.2)                       # L3: holding + secure corridor in the west ring
C_STUB = (14.35, 18.25, 41.2, 46.6)                           # L3: from the lift's south door down to the ring
C_CELLS = [(14.35, 16.85, 28.0 + 2.7 * k, 28.0 + 2.7 * k + 2.5) for k in range(3)]
C_DEF_DOOR = ('u', JT.CB[0], 35.55)                           # defendant door on the courtroom's WEST wall
C_JURY = (JT.CU1 - 2.65, JT.CU1, 30.38, 35.8)                 # the jury box mirrored onto the EAST wall
C_WIT = (JT.CB[1], JT.CORE[0], 22.8, 30.0)                    # witness room + restricted link in the old secure area
def panel(title, draw_fn):
    im = Image.new('RGB', (PW, PH), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, v: ((u - BOX[0]) * S, (BOX[3] - v) * S + 40)
    def rect(r, fill=None, ol=None, w=1): d.rectangle([X(r[0], r[3]), X(r[1], r[2])], fill=fill, outline=ol, width=w)
    def line(p, q, c, w=3): d.line([X(*p), X(*q)], fill=c, width=w)
    def text(p, s, c=(40, 40, 40), f=F1, a='mm'): d.text(X(*p), s, fill=c, font=f, anchor=a)
    jb = J.JBOX; rect(jb, (190, 170, 150), (90, 70, 54), 2); text((-27.0, 58.0), 'Jail I', (70, 50, 40), F2)
    for r in PL.rects('atrium'): rect(r, (222, 226, 232), (110, 110, 120), 2)
    rect(PL.B['tower']['box'], (214, 206, 192), (90, 70, 54), 2)
    text((2.6, 33.0), 'GALLERIA', (80, 80, 110), F2)
    draw_fn(d, X, rect, line, text)
    d.rectangle([0, 0, PW, 34], fill=(30, 30, 34)); d.text((10, 7), title, fill=(255, 255, 255), font=F3)
    return im
def jail_corr(rect, line):
    for r in J.R['corr']['rects']: rect(r, (226, 206, 206), (120, 60, 60))
def c_l1(d, X, rect, line, text):
    jail_corr(rect, line)
    rect(PL.TOWER_SECLIFT, None, GREY, 3); text((33.1, 24.3), 'old shaft', GREY)
    rect(PL.TOWER_CORE, (190, 182, 172), (0, 0, 0)); text((38.8, 32.3), 'core', (40, 40, 40))
    rect(C_CORR, (240, 200, 200), RED, 3); text((3.0, 47.9), 'corridor 22 m', RED, F2)
    rect(C_SHAFT, (150, 60, 60), (0, 0, 0), 2); text((16.35, 45.6), 'new secure lift', RED, F2)
    line((14.45, 47.1), (14.45, 48.9), (255, 255, 255), 5); text((32.0, 52.5), 'tower lobby: no corridor inside it', (90, 70, 50), F2)
    text((2.6, 44.6), 'the galleria stays one space (crossing at its north band)', (80, 80, 110))
def c_l3(d, X, rect, line, text):
    CB = JT.CB; rect(CB, (214, 196, 170), (0, 0, 0), 2); text(((CB[0] + CB[1]) / 2, 38.5), 'COURTROOM 3A', (60, 40, 20), F2)
    # ghosts: the current secure area, lift, jury box, defendant door, witness room
    rect((CB[1], JT.CORE[0], CB[2], CB[3]), None, GREY, 2); rect(PL.TOWER_SECLIFT, None, GREY, 2); text((33.1, 33.0), 'old secure', GREY)
    rect((JT.CU0, 22.0, 30.38, 35.8), None, GREY, 2); text((20.7, 29.6), 'old jury', GREY)
    line((CB[1], 35.55), (CB[1], 36.95), GREY, 6); rect((JT.IU0, CB[0], JT.W_RING_V, JT.WIT_N), None, GREY, 1); text((16.7, 24.5), 'old witness', GREY)
    rect((JT.IU0, 24.75, 43.0, JT.IV1), None, GREY, 1); text((19.5, 53.0), 'jury room (shrinks)', (90, 90, 90))
    # option C
    rect(C_SHAFT, (150, 60, 60), (0, 0, 0), 2); rect(C_STUB, (240, 200, 200), RED, 2); rect(C_SEC_RING, (240, 200, 200), RED, 2)
    for c in C_CELLS: rect(c, (226, 170, 170), (0, 0, 0))
    text((16.7, 30.0), 'holding', RED); text((17.0, 44.0), 'secure', RED)
    line((CB[0], C_DEF_DOOR[2]), (CB[0], C_DEF_DOOR[2] + 1.4), RED, 7); text((CB[0] + 0.4, C_DEF_DOOR[2] + 0.7), 'defendant door', RED, F1, 'lm')
    rect(C_JURY, (176, 140, 100), (0, 0, 0)); text(((C_JURY[0] + C_JURY[1]) / 2, 29.6), 'jury box', (60, 40, 20))
    rect(C_WIT, (200, 214, 236), BLUE, 2); text((33.1, 26.4), 'witness +', BLUE); text((33.1, 25.4), 'restricted', BLUE)
    rect(PL.TOWER_CORE, (190, 182, 172), (0, 0, 0))
def a_l1(d, X, rect, line, text):
    jail_corr(rect, line)
    rect(PL.TOWER_SECLIFT, (150, 60, 60), (0, 0, 0), 2); rect(PL.TOWER_CORE, (190, 182, 172), (0, 0, 0))
    for p, q in (((-11.0, 47.9), (33.1, 47.9)), ((33.1, 47.9), (33.1, 27.4))): line(p, q, RED, 8)
    text((10.0, 49.5), 'corridor ~70 m (22 in the galleria, ~37 in the lobby)', RED, F2)
    rect((31.2, 35.0, JT.LV0, PL.TOWER_SECLIFT[2]), (250, 200, 120), ORANGE, 2); text((36.0, 21.3), 'lobby strip 2.2 m', ORANGE, F2, 'lm')
    text((24.0, 36.0), 'lobby west half', (90, 70, 50)); text((44.5, 44.0), 'east half', (90, 70, 50))
p1 = panel('Option C - ground floor (L1): secure lift moved to the tower NW corner', c_l1)
p2 = panel('Option C - L3 (L5 the same): grey = area 2 today, red = secure, blue = restricted', c_l3)
p3 = panel('Option A - ground floor (L1), for comparison', a_l1)
notes = ['A: courtroom floors unchanged; the lobby gets a ~37 m walled secure corridor (north side + down the core) and the secure lift an L1 stop - rebuild: tower lobby layout + lift panels; galleria loses 2 benches + 2 palms.',
         'C: the secure lift moves to the tower NW corner (west door at L1, south door at L3/L5); on L3 and L5 holding + secure corridor move to the west ring, the jury box to the east wall,',
         '    the defendant door to the west wall, witness room + restricted link into the old secure area, jury room shrinks - rebuild: both courtroom floors (plan, fittings, doors, rig re-test) + the lobby NW corner;',
         '    the prisoner corridor is ~25 m and never runs inside the tower lobby. Both: the galleria crossing is at its north band (any other line cuts the galleria in two).']
W = PW * 2; H = PH * 2 + 40 + 26 * len(notes)
out = Image.new('RGB', (W, H), (246, 244, 238)); out.paste(p1, (0, 0)); out.paste(p2, (PW, 0)); out.paste(p3, (0, PH))
d = ImageDraw.Draw(out)
d.text((PW + 20, PH + 30), 'Prisoner route options (lot frame, m):', fill=(30, 30, 30), font=F3)
d.text((PW + 20, PH + 70), 'red = secure route / rooms   grey = what moves (today)', fill=(60, 60, 60), font=F2)
d.text((PW + 20, PH + 100), 'orange = the lobby strip option A leaves between the halves', fill=(60, 60, 60), font=F2)
for i, n in enumerate(notes): d.text((14, PH * 2 + 20 + 26 * i), n, fill=(20, 20, 20), font=F2)
out.save(sys.argv[1]); print('ROUTES_DRAWN', sys.argv[1])
