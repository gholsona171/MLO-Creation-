"""Justice Center survey: plan sheet v0 (proposed fit of the three parts on the Davis City Hall block) -> survey/plan_v0.png.
Left: the rig's calibrated top-down shot (shots/survey/plan_top.png + plan_top_calib.txt, north up) with the proposal drawn on it.
Right: the same proposal in the lot frame (u, v metres; origin = courts tower centre, heading 50 deg) with sizes. All geometry in
the lot frame comes from PROPOSAL below; site numbers from site.json."""
import json, math
from PIL import Image, ImageDraw, ImageFont
ROOT = r'C:\Users\anton\Documents\Codex\JusticeCenter'
site = json.load(open(ROOT + r'\survey\site.json'))
OX, OY = site['frame']['origin_world']
H = math.radians(site['frame']['heading_deg'])
BLOCK = site['block']['kerb_outline_uv']

# --- the proposal (lot frame, metres) ---
PROPOSAL = [  # name, polygon uv, fill rgba, label
    ('courts', [(-24, -24), (24, -24), (24, 24), (-24, 24)], (219, 186, 158, 200), 'COURTS TOWER\n48 x 48 m (same spot)'),
    ('atrium', [(-12, 24), (35, 24), (35, 37), (-12, 37)], (120, 190, 230, 200), 'ATRIUM (glass)\npublic entrance\n+ security'),
    ('police', [(35, 30), (66, 30), (66, 70), (62, 74), (35, 74)], (196, 160, 130, 210), 'POLICE HQ\n31 x 44 m'),
    ('jail', [(-40, -69), (28, -69), (28, -30), (-40, -30)], (170, 150, 135, 210), 'COUNTY JAIL\n68 x 39 m'),
    ('sallyport', [(12, -44), (28, -44), (28, -30), (12, -30)], (230, 90, 70, 220), 'SALLY\nPORT'),
    ('link', [(-8, -30), (8, -30), (8, -24), (-8, -24)], (230, 90, 70, 220), ''),
]
KEPT = [('davis sheriff (kept)', [(33, -30), (66, -30), (66, 22), (33, 22)]),
        ('library (kept?)', [(-48, 83), (-18, 83), (-18, 113), (-48, 113)])]
PLAZA = ((-1, 62), 28)
ARROWS = [  # from uv, to uv, colour, label
    ((-20, 130), (2, 40), (255, 255, 255), 'public: Davis Ave -> plaza -> atrium'),
    ((22, 100), (34, 58), (255, 255, 255), 'police front desk (off the plaza)'),
    ((90, -27), (30, -36), (255, 70, 50), 'sally port drive (existing car-park drive off Innocence Blvd)'),
    ((-75, 0), (-26, 0), (255, 220, 60), 'judges / staff (secure parking, Macdonald St)'),
    ((-75, -50), (-42, -50), (255, 220, 60), 'jail visitors'),
    ((90, 52), (68, 52), (255, 220, 60), 'police staff + cars'),
]


def world(u, v):
    return OX + u * math.cos(H) - v * math.sin(H), OY + u * math.sin(H) + v * math.cos(H)


# calibration of plan_top.png: fit sx, sy (fractions) linear in world x, y
pts = [l.split() for l in open(ROOT + r'\shots\survey\plan_top_calib.txt').read().splitlines() if l and not l.startswith('cam')]
pts = [tuple(map(float, p)) for p in pts]
xs = sorted({p[0] for p in pts}); ys = sorted({p[1] for p in pts})
a = [p for p in pts if p[1] == ys[0]]; b = [p for p in pts if p[0] == xs[0]]
kx = (a[-1][2] - a[0][2]) / (a[-1][0] - a[0][0]); bx = a[0][2] - kx * a[0][0]
ky = (b[-1][3] - b[0][3]) / (b[-1][1] - b[0][1]); by = b[0][3] - ky * b[0][1]
img = Image.open(ROOT + r'\shots\survey\plan_top.png').convert('RGB')
W, Hh = img.size


def px(u, v):
    x, y = world(u, v)
    return ((kx * x + bx) * W, (ky * y + by) * Hh)


ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
try:
    F = ImageFont.truetype('arialbd.ttf', 15); FS = ImageFont.truetype('arial.ttf', 13); FT = ImageFont.truetype('arialbd.ttf', 22)
except OSError:
    F = FS = FT = ImageFont.load_default()
d.polygon([px(*q) for q in BLOCK], outline=(255, 255, 0, 255), width=3)
for n, poly in KEPT:
    d.polygon([px(*q) for q in poly], outline=(150, 255, 150, 255), width=2)
c, r = PLAZA
cx, cy = px(*c); rp = r / 0.2554
d.ellipse([cx - rp, cy - rp, cx + rp, cy + rp], outline=(255, 255, 255, 230), width=2)
for n, poly, col, lab in PROPOSAL:
    d.polygon([px(*q) for q in poly], fill=col, outline=(30, 30, 30, 255))
for f, t, col, lab in ARROWS:
    p0, p1 = px(*f), px(*t)
    d.line([p0, p1], fill=col + (255,), width=4)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (0.45, -0.45):
        d.line([p1, (p1[0] - 18 * math.cos(ang + da), p1[1] - 18 * math.sin(ang + da))], fill=col + (255,), width=4)
img = Image.alpha_composite(img.convert('RGBA'), ov)
d = ImageDraw.Draw(img)
for n, poly, col, lab in PROPOSAL:
    if not lab: continue
    us = [q[0] for q in poly]; vs = [q[1] for q in poly]
    x, y = px((min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2)
    d.multiline_text((x, y), lab, font=F, fill=(0, 0, 0), anchor='mm', align='center', stroke_width=2, stroke_fill=(255, 255, 255))
for n, poly in KEPT:
    us = [q[0] for q in poly]; vs = [q[1] for q in poly]
    x, y = px((min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2)
    d.text((x, y), n, font=FS, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 90, 0))
d.text((cx, cy + rp + 4), 'PLAZA + MONUMENT (kept)', font=FS, fill=(255, 255, 255), anchor='ma', stroke_width=2, stroke_fill=(0, 0, 0))
for f, t, col, lab in ARROWS:
    x, y = px(*f)
    d.text((x, y), lab, font=FS, fill=col, anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
for txt, (u, v) in [('Davis Ave', (10, 128)), ('Innocence Blvd', (80, 10)), ('Roy Lowenstein Blvd', (0, -84)), ('Macdonald St', (-62, 40))]:
    x, y = px(u, v); d.text((x, y), txt, font=F, fill=(255, 255, 0), anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0))
# crop around the block, then add the title / legend strip
xs_ = [px(*q)[0] for q in BLOCK]; ys_ = [px(*q)[1] for q in BLOCK]
box = (int(min(xs_) - 150), int(min(ys_) - 60), int(max(xs_) + 150), int(max(ys_) + 60))
crop = img.crop(box)
# north arrow
d2 = ImageDraw.Draw(crop); d2.line([(40, 110), (40, 60)], fill=(255, 255, 255), width=4); d2.polygon([(40, 48), (32, 64), (48, 64)], fill=(255, 255, 255))
d2.text((40, 125), 'N', font=F, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
d2.line([(20, crop.height - 30), (20 + 50 / 0.2554, crop.height - 30)], fill=(255, 255, 255), width=4)
d2.text((20 + 25 / 0.2554, crop.height - 45), '50 m', font=F, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
LW = 560
sheet = Image.new('RGB', (crop.width + LW, max(crop.height, 760)), (24, 26, 30))
sheet.paste(crop.convert('RGB'), (0, 0))
L = ImageDraw.Draw(sheet); x0 = crop.width + 20; y = 20
L.text((x0, y), 'Cleveland Justice Center - plan v0 (fit proposal)', font=FT, fill=(255, 255, 255)); y += 36
lines = [
    'Site: GTA block sc1_19 ("Davis City Hall"), Davis / Rancho.',
    'Kerb block about 115 x 190 m, grid heading 50 deg.',
    'Tower centre x 335.87, y -1640.11; street z 28.3, plaza 29.5-31.5.',
    '',
    'Proposal (rebuilt from source, nothing patched):',
    '- Courts tower on the vanilla tower spot, 48 x 48 m',
    '  (real 54 x 51 m). Lobby + security in the atrium,',
    '  2 courtrooms, judges chambers, offices inside.',
    '- Atrium: glass link, the public entrance off the',
    '  plaza, joins tower and police HQ (as in Cleveland).',
    '- Police HQ on the low "city hall" block at the',
    '  Davis Ave / Innocence Blvd corner, 31 x 44 m',
    '  (real 72 x 47 m). Front desk faces the plaza.',
    '- County jail replaces the multi-storey car park',
    '  behind the tower, 68 x 39 m (real Jail I 97 x 50 m):',
    '  booking, holding, cell block.',
    '- Sally port: the existing car-park drive off',
    '  Innocence Blvd, between sheriff and jail.',
    '- Secure link jail -> tower holding (red, 16 x 6 m).',
    '- Kept: plaza + monument, Davis sheriff station,',
    '  library (to confirm).',
    '',
    'Open: tower height (vanilla ~60 m vs ~110 m to keep',
    'the real proportion), sheriff site, library, monument.',
    'Windows: dark tinted glass on every part.',
]
for t in lines:
    L.text((x0, y), t, font=FS, fill=(225, 225, 225)); y += 19
y += 10
for col, t in [((219, 186, 158), 'courts tower'), ((120, 190, 230), 'atrium'), ((196, 160, 130), 'police HQ'), ((170, 150, 135), 'jail'),
               ((230, 90, 70), 'sally port / secure link'), ((255, 255, 0), 'block kerb'), ((150, 255, 150), 'kept vanilla')]:
    L.rectangle([x0, y, x0 + 22, y + 14], fill=col); L.text((x0 + 30, y), t, font=FS, fill=(225, 225, 225)); y += 20
sheet.save(ROOT + r'\survey\plan_v0.png')
print('plan_v0.png', sheet.size, 'calib kx %.6f ky %.6f' % (kx, ky))
