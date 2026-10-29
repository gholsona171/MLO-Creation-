"""Phase 3 plan drawing (lot frame, north-ish up = +v): the galleria with its walls, fins, curtain walls and door openings, portals,
the checkpoint (screen line, lanes, queue), every placed prop's footprint from its real bounds (pivot-aware), door leaves and their
swing, seats, wall lights, reserved door stretches and the neighbouring buildings. Reads jc3_plan + out/jc3_layout.json.
Run: py -3 jc3_plandraw.py <out.png>"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_plan as JP, p2_plan as PL
L = json.load(open(P3 / 'out/jc3_layout.json'))
A = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
def bb(m): a = A[m.lower()]; f = lambda s: [float(x[2:]) for x in s.split()]; return f(a['bbMin']), f(a['bbMax'])
def foot(m, u, v, h):
    lo, hi = bb(m); t = math.radians(h); c, s = math.cos(t), math.sin(t)
    return [(u + x * c - y * s, v + x * s + y * c) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
U0, U1, V0, V1, S = -13.0, 48.0, -12.0, 54.0, 30            # view box (lot frame) and pixels per metre
W, H = int((U1 - U0) * S), int((V1 - V0) * S) + 170
im = Image.new('RGB', (W, H), (244, 241, 234)); d = ImageDraw.Draw(im)
def X(u, v): return ((u - U0) * S, (V1 - v) * S + 170)
def rect(u0, u1, v0, v1, fill, outline=None, w=1): d.rectangle([X(u0, v1), X(u1, v0)], fill=fill, outline=outline, width=w)
def poly(pts, fill, outline=(0, 0, 0)): d.polygon([X(*p) for p in pts], fill=fill, outline=outline)
def line(p, q, col, w=2): d.line([X(*p), X(*q)], fill=col, width=w)
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 15), ImageFont.truetype('arial.ttf', 20), ImageFont.truetype('arialbd.ttf', 22)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
def text(u, v, t, f=None, col=(40, 40, 40)): d.multiline_text(X(u, v), t, fill=col, font=f or F1, anchor='mm', align='center')
for g in range(int(U0), int(U1) + 1, 5): d.line([X(g, V0), X(g, V1)], fill=(222, 218, 210))
for g in range(int(V0), int(V1) + 1, 5): d.line([X(U0, g), X(U1, g)], fill=(222, 218, 210))
for k in ('tower', 'police', 'jail1'):
    u0, u1, v0, v1 = PL.B[k]['box']; rect(max(u0, U0), min(u1, U1), max(v0, V0), min(v1, V1), (217, 196, 176), (122, 100, 80))
text(-11.0, 30.0, 'JAIL I', F3, (90, 70, 54)); text(40.0, 30.0, 'COURTS\nTOWER', F3, (90, 70, 54)); text(28.0, -10.0, 'POLICE HQ', F3, (90, 70, 54))
for r in PL.rects('atrium'): rect(r[0], r[1], r[2], r[3], (255, 255, 255), (80, 80, 80))
for u0, u1, v0, v1, kind in JP.floor_rects(): rect(u0, u1, v0, v1, (236, 230, 218) if kind == 'field' else (120, 128, 108))
for w, (axis, (lo, hi), a0, a1, b) in JP.WALLS.items():
    if axis == 'u': rect(lo, hi, a0, a1, (185, 150, 122), (90, 70, 54))
    else: rect(a0, a1, lo, hi, (185, 150, 122), (90, 70, 54))
    for c in JP.fins(w):
        if axis == 'u': x0 = hi if lo < 0 else lo - JP.FIN_P; rect(x0, x0 + JP.FIN_P, c - JP.FIN_W / 2, c + JP.FIN_W / 2, (138, 106, 80))
        else: y0 = hi if w == 'police' else lo - JP.FIN_P; rect(c - JP.FIN_W / 2, c + JP.FIN_W / 2, y0, y0 + JP.FIN_P, (138, 106, 80))
for k, (w, a0, a1, z0, z1, what) in JP.RESERVED.items():
    axis, (lo, hi), *_ = JP.WALLS[w]; m = (lo + hi) / 2
    line((a0, m), (a1, m), (192, 57, 43), 7); text((a0 + a1) / 2, m + (1.0 if w != 'police' else -1.0), 'reserved: ' + what, F1, (192, 57, 43))
for s0, s1 in JP.E_BAYS: line((37.75, s0 + .04), (37.75, s1 - .04), (127, 179, 213), 5)
for face in (JP.FACE_S, JP.FACE_N):
    for s0, s1 in JP.curtain(face): at = face[1] + face[5] * -0.15; line((s0 + .04, at), (s1 - .04, at), (127, 179, 213), 5)
for _, _, s0, s1, _, _ in JP.door_openings(): line((37.75, s0), (37.75, s1), (255, 255, 255), 6)
for a, b, kind, p in JP.portals():
    if p[0] == 'u': line((p[1], p[2]), (p[1], p[3]), (31, 119, 180), 2)
    elif p[0] == 'v': line((p[2], p[1]), (p[3], p[1]), (31, 119, 180), 2)
for dd in L['doors']:
    u, v, z = dd['pos']; sg = 1 if dd['model'] == JP.DOOR_L else -1; line((u, v), (u, v + sg * JP.LEAF_W), (20, 20, 20), 4)
    bx = [X(u - JP.LEAF_W, v - JP.LEAF_W), X(u + JP.LEAF_W, v + JP.LEAF_W)]; d.arc([bx[0][0], bx[1][1], bx[1][0], bx[0][1]], 0, 360, fill=(170, 170, 170))
for v0, v1 in JP.screen_runs(): line((JP.SCREEN_U, v0), (JP.SCREEN_U, v1), (22, 160, 133), 5)
line((JP.EXIT_SPLIT_U[0], JP.EXIT_SPLIT_V), (JP.EXIT_SPLIT_U[1], JP.EXIT_SPLIT_V), (22, 160, 133), 5)
dk = JP.DESK; rect(dk['u'][0], dk['u'][1], dk['v'][0], dk['v'][1], (107, 86, 68), (0, 0, 0)); rect(dk['u'][0] - .45, dk['u'][0], dk['v'][0] + .05, dk['v'][1] - .05, (140, 120, 100))
pd = JP.PODIUM; rect(pd['u'][0], pd['u'][1], pd['v'][0], pd['v'][1], (107, 86, 68), (0, 0, 0))
COL = {'ch_prop_baggage_scanner_01a': (59, 110, 165), 'ch_prop_ch_metal_detector_01a': (208, 138, 26), 'v_corp_bk_rope': (138, 90, 43), 'v_ilev_ph_bench': (47, 93, 138),
       'ch_prop_ch_planter_01': (79, 138, 58), 'apa_mp_h_acc_plant_palm_01': (79, 138, 58)}
for q in L['placed']: poly(foot(q['model'], q['u'], q['v'], q['heading']), COL.get(q['model'], (150, 150, 150)))
for s_ in L['seats']:
    h = math.radians(s_[3]); x, y = X(s_[0], s_[1]); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(230, 126, 34)); line((s_[0], s_[1]), (s_[0] - .4 * math.sin(h), s_[1] + .4 * math.cos(h)), (230, 126, 34), 2)
for u, v, z, m in JP.wall_lights(): x, y = X(u, v); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(241, 196, 15), outline=(125, 102, 8))
for (u, v), t in [((33.5, 1.0), 'PUBLIC SIDE\nqueue'), ((19.0, 6.5), 'SECURE SIDE'), ((32.5, 11.5), 'exit flow'), ((43.0, 2.1), 'ENTRY\ndoors'),
                  ((43.0, 8.0), 'EXIT\ndoors'),
                  ((5.0, 12.0), 'GALLERIA (rect A)'), ((2.5, 41.0), 'GALLERIA (rect B)\nlawn glass north'), ((21.0, -4.6), 'security desk'),
                  ((-4.5, 19.5), 'flags +\ninscription'),
                  ((31.6, -1.4), 'lane A'), ((31.6, 2.2), 'lane B'), ((44.0, 14.0), 'PLAZA')]: text(u, v, t, F2)
d.rectangle([0, 0, W, 165], fill=(30, 30, 34))
d.text((16, 10), 'Justice Center phase 3, area 1: the atrium galleria, main entrance and security checkpoint (lot frame, 5 m grid)', fill=(255, 255, 255), font=F3)
leg = ['blue line = exit portals on the room side of the glass; light blue = curtain bays; white gaps = the two door openings (2 x 1.30 m native leaves each, swing circles grey)',
       'green = 2.4 m glass screen line + the queue / exit split; blue boxes = X-ray belts, orange = walk-through detectors, brown chains = rope stanchions',
       'dark blue = Mission Row row seats (orange dots = sit points, untested), green = planters / palms, yellow dots = wall lights; dark green bands = the floor border',
       'red = wall stretches kept free for the next areas’ doors (tower lift lobby, police HQ link); brown fins = granite ribs on the neighbours’ walls']
for i, t in enumerate(leg): d.text((16, 48 + i * 28), t, fill=(220, 220, 220), font=F1)
out = sys.argv[1] if len(sys.argv) > 1 else str(P3 / 'plan_area1.png'); im.save(out); print('PLAN_DRAWN', out)
