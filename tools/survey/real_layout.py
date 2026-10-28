"""Justice Center v1: the REAL footprint plan, top-down, north up, metres (OpenStreetMap via survey/real/real_local.json).
Draws the Justice Center outlines (base, Courts Tower, Jail I, police HQ, Jail II, plaza), the estimated Portal spot, the skybridges
(positions estimated: Wikipedia names their ends only), the neighbouring buildings and the street centre lines.
-> survey/real_layout.png"""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
R = json.load(open(os.path.join(SV, 'real', 'real_local.json')))['features']
V1 = json.load(open(os.path.join(SV, 'v1_outlines.json')))
X0, X1, Y0, Y1, S = -190, 190, -215, 135, 2.6        # metres shown, px per metre
W, H = int((X1 - X0) * S) + 380, int((Y1 - Y0) * S)
try:
    F = ImageFont.truetype('arial.ttf', 14); FB = ImageFont.truetype('arialbd.ttf', 15); FT = ImageFont.truetype('arialbd.ttf', 22)
except OSError:
    F = FB = FT = ImageFont.load_default()
img = Image.new('RGB', (W, H), (246, 245, 240)); d = ImageDraw.Draw(img)
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
JC = {'way/189749443': ('Justice Center base\n(tower + atrium + Jail I)', (226, 205, 185)), 'way/333533679': ('COURTS TOWER\n26 fl, 128 m', (205, 160, 125)),
      'way/354191885': ('JAIL I\n(Corrections Center)\n10 fl', (190, 172, 150)), 'way/122151929': ('POLICE HQ\n9-10 fl, 39.5 m', (200, 170, 140)),
      'way/150720143': ('JAIL II\n11 fl (cream panels)', (235, 228, 205)), 'way/1416750951': ('PLAZA', (215, 215, 215))}
for k, f in R.items():                                   # neighbours, light grey
    if f['kind'] in ('building',) and k not in JC and f.get('closed'):
        d.polygon([P(*p) for p in f['xy']], fill=(225, 225, 222), outline=(180, 180, 180))
for k, f in R.items():
    if f['kind'] == 'street' and f['tags'].get('highway') in ('tertiary', 'primary', 'secondary', 'residential', 'service'):
        w = 9 if f['tags'].get('highway') == 'tertiary' else 3
        d.line([P(*p) for p in f['xy']], fill=(190, 190, 200), width=int(w * S * 0.7))
for k in ['way/1416750951', 'way/189749443', 'way/354191885', 'way/333533679', 'way/122151929', 'way/150720143']:
    lab, col = JC[k]; d.polygon([P(*p) for p in R[k]['xy']], fill=col, outline=(60, 50, 40), width=2)
for k in JC:
    xy = np.array(R[k]['xy']); c = xy[:-1].mean(0) if len(xy) > 3 else xy.mean(0)
    if k == 'way/189749443': continue
    d.multiline_text(P(*c), JC[k][0], font=FB, fill=(20, 20, 20), anchor='mm', align='center')
# atrium label (the part of the base that is neither tower nor Jail I)
d.multiline_text(P(-2, -48), 'ATRIUM\n(4 storeys, glass)', font=F, fill=(30, 60, 120), anchor='mm', align='center')
# Portal (estimated) in real coordinates: undo the fit transform for the portal point is not needed - recompute as in fit_v1
pl = np.array(R['way/1416750951']['xy'][:-1]); ax = np.array([-0.559, 0.829]); far = pl[np.argmax(pl @ ax)]
po = far + (pl.mean(0) - far) / np.linalg.norm(pl.mean(0) - far) * 6.0
x, y = P(*po); d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(40, 40, 40)); d.multiline_text((x - 12, y - 40), 'PORTAL (Noguchi, 11 m)\nposition estimated', font=F, fill=(20, 20, 20), anchor='rm', align='right')
# skybridges (estimated: shortest link between the named buildings)
def nearest(a, b):
    A = np.array(R[a]['xy']); B = np.array(R[b]['xy']); best = None
    for p in A:
        for q in B:
            dd = np.linalg.norm(p - q)
            if best is None or dd < best[0]: best = (dd, p, q)
    return best
for a, b in (('way/354191885', 'way/150720143'), ('way/122151929', 'way/150720143')):
    dd, p, q = nearest(a, b); d.line([P(*p), P(*q)], fill=(200, 60, 40), width=6)
d.text(P(-75, -112), 'skybridges (red, estimated)', font=F, fill=(200, 60, 40))
for name, (x, y) in {'Lakeside Ave': (-75, 40), 'Ontario St': (95, -20), 'St Clair Ave': (55, -150), 'W 3rd St': (-105, -62),
                     'old County Courthouse (1912)': (-17, 133)}.items():
    d.text(P(x, y), name, font=FB, fill=(40, 40, 120), anchor='mm')
# north arrow + scale
d.line([(40, 120), (40, 60)], fill=(0, 0, 0), width=4); d.polygon([(40, 45), (31, 64), (49, 64)], fill=(0, 0, 0)); d.text((40, 135), 'N', font=FB, fill=(0, 0, 0), anchor='mm')
d.line([(30, H - 30), (30 + 50 * S, H - 30)], fill=(0, 0, 0), width=4); d.text((30 + 25 * S, H - 46), '50 m', font=FB, fill=(0, 0, 0), anchor='mm')
x0 = int((X1 - X0) * S) + 15; y = 20
d.text((x0, y), 'Cleveland Justice Center', font=FT, fill=(0, 0, 0)); y += 30
d.text((x0, y), 'real footprints, top-down, north up', font=FB, fill=(0, 0, 0)); y += 30
for t in ['Source: OpenStreetMap contributors (ODbL),', 'Overpass API, 2026-10-28 (survey/real/).', '',
          'Outlines (OSM way, box, area):', 'base 189749443  131 x 97 m  11,009 m2', 'tower 333533679  54 x 51 m  2,689 m2',
          '  26 levels, 128 m (OSM)', 'Jail I 354191885  97 x 50 m  4,828 m2', 'police 122151929  72 x 47 m  3,384 m2',
          '  10 levels, 39.5 m (OSM)', 'Jail II 150720143  53 x 45 m  2,370 m2', '  (untagged; position fits Wikipedia)',
          'plaza 1416750951  99 x 33 m  2,315 m2', '', 'Complex (buildings + plaza):', '  148 x 171 m, axis 34 deg off north', '',
          'Estimated, not in OSM:', '- Portal: NW end of the plaza', '  (Wikipedia text)', '- skybridges Jail I-Jail II and',
          '  police HQ-Jail II (Wikipedia: they', '  exist; ends only)', '- atrium = base minus tower', '  minus Jail I']:
    d.text((x0, y), t, font=F, fill=(30, 30, 30)); y += 19
img.save(os.path.join(SV, 'real_layout.png')); print('real_layout.png', img.size)
