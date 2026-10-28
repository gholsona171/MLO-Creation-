"""Justice Center v1 section sheet -> survey/section_v1.png (from v1_outlines.json 'design').
Left: elevation seen from Innocence Blvd (looking -u): every building at its v extent and real-proportion height, every floor line,
interior floors coloured, shell floors grey, the vanilla tower dashed (skyline change). Right: one column per building with every
floor listed (level, z, use)."""
import json, os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
V = json.load(open(os.path.join(SV, 'v1_outlines.json'))); D = V['design']; B = D['buildings']; P = V['parts']
try:
    F = ImageFont.truetype('arial.ttf', 12); FB = ImageFont.truetype('arialbd.ttf', 14); FT = ImageFont.truetype('arialbd.ttf', 20)
except OSError:
    F = FB = FT = ImageFont.load_default()
W, H = 2000, 1150
img = Image.new('RGB', (W, H), (248, 247, 243)); d = ImageDraw.Draw(img)
# ---- left: elevation from Innocence Blvd. screen x = -v (Davis Ave on the left), y = z
VX0, VX1, Z0, Z1 = 125, -80, 20, 135
LX, LY, LW, LH = 60, 70, 760, 1000
sx = lambda v: LX + (VX0 - v) / (VX0 - VX1) * LW
sz = lambda z: LY + (Z1 - z) / (Z1 - Z0) * LH
d.text((LX, 20), 'Elevation from Innocence Blvd (Davis Ave left, Roy Lowenstein right)', font=FT, fill=(0, 0, 0))
for z in range(20, 136, 10):
    d.line([(LX - 8, sz(z)), (LX + LW, sz(z))], fill=(225, 225, 225)); d.text((LX - 12, sz(z)), f'z {z}', font=F, fill=(90, 90, 90), anchor='rm')
d.line([(LX, sz(28.3)), (LX + LW, sz(28.3))], fill=(110, 90, 60), width=3); d.text((LX + 5, sz(28.3) + 4), 'sidewalk z 28.3', font=F, fill=(110, 90, 60))
COL = {'shell': (205, 200, 192)}
INT = (240, 150, 60); ATR = (140, 195, 235)
order = ['jail_1', 'jail_2', 'atrium', 'police_hq', 'courts_tower']    # back (small u) to front (large u)
vext = {k: (min(p[1] for p in P[k]['uv']), max(p[1] for p in P[k]['uv'])) for k in ('jail_1', 'jail_2', 'police_hq', 'courts_tower')}
vext['atrium'] = (min(p[1] for p in D['atrium']['uv']), max(p[1] for p in D['atrium']['uv']))
for k in order:
    bd = B[k]; v0, v1 = vext[k]; ff = bd['floor_to_floor_m']
    for f in bd['floors_list']:
        col = (ATR if k == 'atrium' else INT) if f['use'] != 'shell' else COL['shell']
        d.rectangle([sx(v1), sz(f['z'] + ff), sx(v0), sz(f['z'])], fill=col, outline=(120, 110, 100))
    d.rectangle([sx(v1), sz(bd['z_roof']), sx(v0), sz(bd['z_ground'])], outline=(40, 30, 20), width=2)
    LBL = {'jail_1': (16, 40, 'ld'), 'jail_2': (-30, 18, 'md'), 'atrium': (8, 0, 'md'), 'police_hq': (-30, 0, 'md'), 'courts_tower': (36, 0, 'md')}
    lv, dy, anc = LBL[k]
    nm = ('Jail I' if k == 'jail_1' else bd['name']) + (' (behind police HQ)' if k == 'jail_2' else ' (behind tower)' if k == 'jail_1' else '')
    if k == 'atrium':
        d.multiline_text((sx(lv), sz(bd['z_roof']) + 22), "Atrium\nroof z " + str(bd['z_roof']), font=F, fill=(0, 0, 0), anchor='mm', align='center')
    else:
        d.text((sx(lv), sz(bd['z_roof']) - 4 - dy), f"{nm}  roof z {bd['z_roof']}", font=FB, fill=(0, 0, 0), anchor=anc)
vt = D['vanilla_tower']
for z in (vt['z_roof'], vt['z_top']):
    pass
x0v, x1v = sx(24.2), sx(-24.2)
for yy in range(int(sz(vt['z_top'])), int(sz(28.3)), 12):
    d.line([(x0v, yy), (x0v, yy + 6)], fill=(200, 30, 30), width=2); d.line([(x1v, yy), (x1v, yy + 6)], fill=(200, 30, 30), width=2)
for xx in range(int(x0v), int(x1v), 12):
    d.line([(xx, sz(vt['z_top'])), (xx + 6, sz(vt['z_top']))], fill=(200, 30, 30), width=2)
d.text((x1v + 4, sz(vt['z_top']) - 16), 'vanilla tower (removed), top z 97.5', font=F, fill=(200, 30, 30))
# sculpture
xs = sx(D['sculpture']['uv'][1]); d.line([(xs, sz(28.8)), (xs, sz(28.8 + 8))], fill=(30, 30, 30), width=4); d.text((xs + 4, sz(37)), 'sculpture 8 m', font=F, fill=(30, 30, 30))
for t, v in (('Davis Ave', 118), ('lawn', 85), ('Roy Lowenstein', -68)):
    d.text((sx(v), sz(25)), t, font=FB, fill=(40, 40, 120), anchor='mm')
yl = LY + LH + 10
for col, t in ((INT, 'interior floor (MLO rooms, see-out dark glass)'), (ATR, 'atrium: glass, open galleria'), ((205, 200, 192), 'empty shell floor (exterior model only)')):
    d.rectangle([LX, yl, LX + 18, yl + 14], fill=col, outline=(0, 0, 0)); d.text((LX + 26, yl), t, font=F, fill=(0, 0, 0)); LX += 270
# ---- right: floor columns
RX = 900; d.text((RX, 20), 'Every floor (level, floor z, use)', font=FT, fill=(0, 0, 0))
cols = [('courts_tower', 26), ('police_hq', 9), ('jail_1', 10), ('jail_2', 11), ('atrium', 4)]
cw = [430, 320, 320, 0, 0]
x = RX; y0 = 60
for i, (k, n) in enumerate(cols):
    bd = B[k]
    if k in ('jail_2', 'atrium'):
        continue
    d.text((x, y0), f"{bd['name']}: {bd['floors']} fl x {bd['floor_to_floor_m']} m = {bd['height_m']} m", font=FB, fill=(0, 0, 0))
    y = y0 + 22
    for f in reversed(bd['floors_list']):
        col = INT if f['use'] != 'shell' else (230, 228, 222)
        d.rectangle([x, y, x + cw[i] - 12, y + 29], fill=col, outline=(150, 140, 130))
        n1 = 58 if i == 0 else 40
        txt = f"L{f['level']:>2}  z {f['z']:6.2f}  {f['use'][:n1]}"
        d.text((x + 4, y + 3), txt, font=F, fill=(0, 0, 0))
        if f['use'] != 'shell' and len(f['use']) > n1: d.text((x + 4, y + 16), '      ' + f['use'][n1:n1 * 2], font=F, fill=(0, 0, 0))
        y += 32
    x += cw[i]
# jail II + atrium as small blocks under the police / jail columns
y = 60 + 22 + 11 * 32 + 30; x = RX + 430
for k in ('atrium', 'jail_2'):
    bd = B[k]; d.text((x, y), f"{bd['name']}: {bd['floors']} fl, {bd['height_m']} m, roof z {bd['z_roof']}", font=FB, fill=(0, 0, 0)); y += 20
    for f in reversed(bd['floors_list']):
        col = (ATR if k == 'atrium' else INT) if f['use'] != 'shell' else (230, 228, 222)
        d.rectangle([x, y, x + 628, y + 18], fill=col, outline=(150, 140, 130)); d.text((x + 4, y + 2), f"L{f['level']:>2}  z {f['z']:6.2f}  {f['use'][:90]}", font=F, fill=(0, 0, 0)); y += 20
    y += 14
notes = ['Heights: real height x plan scale %.2f; floor counts as the real buildings.' % V['scale'],
         'Courtroom floors are double height (two window bands, as the real facade).',
         'Shell floors: no MLO rooms; dark glass + a dark backing 1.2 m behind it,',
         'night-lit windows from an emissive model (Rockstar pattern).',
         'Jail I / II floor heights are unverified (assumed 4.2 / 3.6 m real).']
for t in notes:
    d.text((x, y), t, font=F, fill=(40, 40, 40)); y += 17
img.save(os.path.join(SV, 'section_v1.png')); print('section_v1.png', img.size)
