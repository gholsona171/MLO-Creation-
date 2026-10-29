"""Phase 3 area 2 plan drawings (lot frame): the tower lobby (L1) and a courtroom floor (L3; L5 is the same plan) - every room's
region and colour, the courtroom's fittings, every placed prop's footprint from its real bounds, the doors (leaf + swing circle),
the portals, the sit points, the lifts and the stair flights. Reads jc3_tower + out/jc3_layout.json.
Run: py -3 jc3_plandraw_tower.py <out_L1.png> <out_L3.png>"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_tower as JT, p2_plan as PL
L = json.load(open(P3 / 'out/jc3_layout.json'))
A = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
def bb(m): a = A[m.lower()]; f = lambda s: [float(x[2:]) for x in s.split()]; return f(a['bbMin']), f(a['bbMax'])
def foot(m, u, v, h):
    lo, hi = bb(m); t = math.radians(h); c, s = math.cos(t), math.sin(t)
    return [(u + x * c - y * s, v + x * s + y * c) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
COL = {'tlobby': (236, 228, 214), 'stair': (200, 200, 205), 'crt': (214, 196, 170), 'pub': (232, 232, 222), 'rst': (210, 222, 236), 'sec': (226, 206, 206)}
try: F1, F2, F3 = ImageFont.truetype('arial.ttf', 14), ImageFont.truetype('arial.ttf', 18), ImageFont.truetype('arialbd.ttf', 22)
except Exception: F1 = F2 = F3 = ImageFont.load_default()
def draw(level, z0, z1, out, title):
    U0, U1, V0, V1, S = 12.0, 52.5, 15.0, 58.0, 30
    W, H = int((U1 - U0) * S), int((V1 - V0) * S) + 120
    im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    X = lambda u, v: ((u - U0) * S, (V1 - v) * S + 120)
    def rect(u0, u1, v0, v1, fill, ol=None, w=1): d.rectangle([X(u0, v1), X(u1, v0)], fill=fill, outline=ol, width=w)
    def line(p, q, c, w=2): d.line([X(*p), X(*q)], fill=c, width=w)
    tb = PL.B['tower']['box']; rect(tb[0], tb[1], tb[2], tb[3], (190, 170, 150), (90, 70, 54), 2)
    for k, zs in L['zones'].items():
        if k == 'galleria': continue
        for r in zs:
            if r[4] <= z0 + 0.01 and r[5] >= z0 + 0.5 and (r[4] >= z0 - 3.0 or k == 'stair'):
                rect(r[0], r[1], r[2], r[3], COL.get(k[:3], COL.get(k)), (120, 120, 120))
    for k, zs in L['zones'].items():
        if k == 'galleria': continue
        for r in zs[:1]:
            if r[4] <= z0 + 0.01 and r[5] >= z0 + 0.5 and (r[4] >= z0 - 3.0 or k == 'stair'):
                d.text(X((r[0] + r[1]) / 2, (r[2] + r[3]) / 2), k, fill=(60, 60, 60), font=F2, anchor='mm')
    if level == 'L3':
        fit = JT.court_fittings('A')
        for u0, u1, v0, v1, zz0, zz1, mat, col in fit['boxes']:
            rect(u0, u1, v0, v1, {'plank': (176, 140, 100), 'panel': (110, 70, 40), 'block': (150, 150, 150)}.get(mat, (150, 150, 150)))
    for q in L['placed']:
        if z0 - 0.5 <= q['z'] <= z1 - 0.3:
            d.polygon([X(*p) for p in foot(q['model'], q['u'], q['v'], q['heading'])], fill=(70, 110, 160), outline=(0, 0, 0))
    for dd in L['doors']:
        u, v, z = dd['pos']
        if not (z0 <= z <= z1): continue
        t = math.radians(dd['heading']); ex, ey = -math.cos(t) * JT.LEAF, -math.sin(t) * JT.LEAF
        if dd['model'] in (JT.GLASS_L, 'v_ilev_finelevdoor01'): ex, ey = -ex, -ey
        line((u, v), (u + ex, v + ey), (20, 20, 20), 4)
        x, y = X(u, v); r = JT.LEAF * S; d.ellipse([x - r, y - r, x + r, y + r], outline=(170, 170, 170))
    for p in L['portals']:
        c = p['corners']; zs = [q[2] for q in c]
        if max(zs) < z0 or min(zs) > z1 or (max(zs) - min(zs)) < 0.01: continue
        us = [q[0] for q in c]; vs = [q[1] for q in c]
        line((min(us), min(vs)), (max(us), max(vs)), (31, 119, 180) if p['to'] == 'limbo' else (200, 60, 160), 3)
    for s in L['seats']:
        if z0 <= s[2] <= z1:
            x, y = X(s[0], s[1]); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(230, 126, 34))
    for base, dd_, zb, zt, lane in JT.flights():
        if z0 - 0.01 <= zb < z0 + 3.59:
            a0, a1 = sorted((base, base + dd_ * (JT.RISERS - 1) * JT.GO)); rect(a0, a1, lane[0], lane[1], (120, 120, 120))
            for k in range(JT.RISERS - 1): x0 = base + dd_ * k * JT.GO; line((x0, lane[0]), (x0, lane[1]), (60, 60, 60), 1)
    d.rectangle([0, 0, W, 112], fill=(30, 30, 34)); d.text((14, 10), title, fill=(255, 255, 255), font=F3)
    d.text((14, 48), 'blue lines = windows / colonnade glass (limbo portals), magenta = doorways between rooms (doors on their portals), black = door leaves + swing',
           fill=(220, 220, 220), font=F1)
    d.text((14, 72), 'blue shapes = Rockstar props (real bounds), browns = courtroom fittings (dais, bench, jury box, bar, pews), orange dots = sit points (rig-tested)',
           fill=(220, 220, 220), font=F1)
    im.save(out); print('PLAN_DRAWN', out)
draw('L1', JT.F1, JT.F1 + 3.0, sys.argv[1], 'Justice Center phase 3, area 2: courts tower L1 - the lobby, the lifts, the stair (lot frame, m)')
draw('L3', JT.F3, JT.F3 + 3.0, sys.argv[2], 'Justice Center phase 3, area 2: courtroom floor L3 (L5 the same) - courtroom 3A, public, restricted, secure')
