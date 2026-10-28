"""Justice Center v1 plan sheet -> survey/plan_v1.png. The real complex (OpenStreetMap footprints) fitted to the whole sc1_19 block at
one uniform scale (fit_v1.py + design_v1.py -> v1_outlines.json), drawn on the rig's calibrated top-down (shots/survey/plan_top.png),
with entrances, sally port, skybridges, the lawn and the sculpture; legend + numbers on the right."""
import json, math, os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
site = json.load(open(os.path.join(SV, 'site.json')))
V = json.load(open(os.path.join(SV, 'v1_outlines.json'))); D = V['design']
OX, OY = site['frame']['origin_world']; H = math.radians(site['frame']['heading_deg'])
pts = [tuple(map(float, l.split())) for l in open(os.path.join(ROOT, 'shots', 'survey', 'plan_top_calib.txt')).read().splitlines() if l and not l.startswith('cam')]
xs = sorted({p[0] for p in pts}); ys = sorted({p[1] for p in pts})
a = [p for p in pts if p[1] == ys[0]]; b = [p for p in pts if p[0] == xs[0]]
kx = (a[-1][2] - a[0][2]) / (a[-1][0] - a[0][0]); bx = a[0][2] - kx * a[0][0]
ky = (b[-1][3] - b[0][3]) / (b[-1][1] - b[0][1]); by = b[0][3] - ky * b[0][1]
img = Image.open(os.path.join(ROOT, 'shots', 'survey', 'plan_top.png')).convert('RGBA'); W, Hh = img.size
MPP = 1 / (kx * W)                                   # metres per pixel


def px(u, v):
    x = OX + u * math.cos(H) - v * math.sin(H); y = OY + u * math.sin(H) + v * math.cos(H)
    return ((kx * x + bx) * W, (ky * y + by) * Hh)


try:
    F = ImageFont.truetype('arialbd.ttf', 14); FS = ImageFont.truetype('arial.ttf', 13); FT = ImageFont.truetype('arialbd.ttf', 21)
except OSError:
    F = FS = FT = ImageFont.load_default()
# grey wash over the old block so the new plan reads
ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
kerb = site['block']['kerb_outline_uv']
d.polygon([px(*q) for q in kerb], fill=(30, 30, 30, 110))
d.polygon([px(*q) for q in D['lawn']['uv']], fill=(90, 150, 70, 200))
d.polygon([px(*q) for q in D['secure_yard']['uv']], fill=(120, 120, 120, 220))
P = V['parts']
FILL = [('plaza', (215, 210, 200, 235)), ('jail_2', (236, 228, 205, 240)), ('police_hq', (200, 168, 138, 240)),
        ('jail_1', (186, 166, 146, 240))]
for n, c in FILL:
    d.polygon([px(*q) for q in P[n]['uv']], fill=c, outline=(40, 30, 20, 255))
d.polygon([px(*q) for q in D['atrium']['uv']], fill=(130, 190, 230, 235), outline=(40, 30, 20, 255))
d.polygon([px(*q) for q in P['courts_tower']['uv']], fill=(212, 168, 132, 250), outline=(40, 30, 20, 255))
d.polygon([px(*q) for q in D['sally_port']['uv']], fill=(230, 80, 60, 240), outline=(40, 30, 20, 255))
d.line([px(*q) for q in D['vanilla_tower']['uv'] + D['vanilla_tower']['uv'][:1]], fill=(255, 255, 255, 200), width=2)
for sb in D['skybridges']:
    d.line([px(*q) for q in sb['uv']], fill=(230, 80, 60, 255), width=7)
d.line([px(*q) for q in kerb + kerb[:1]], fill=(255, 230, 0, 255), width=3)
img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
x, y = px(*D['sculpture']['uv']); d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(20, 20, 20), outline=(255, 255, 255), width=2)
lab = {'courts_tower': 'COURTS TOWER\n26 fl, 93 m', 'jail_1': 'JAIL I\n10 fl', 'police_hq': 'POLICE HQ\n9 fl', 'jail_2': 'JAIL II\n11 fl', 'plaza': 'PLAZA'}
for n, t in lab.items():
    q = P[n]['uv']; c = (sum(p[0] for p in q) / len(q), sum(p[1] for p in q) / len(q))
    if n == 'plaza': c = (55, -48)
    d.multiline_text(px(*c), t, font=F, fill=(0, 0, 0), anchor='mm', align='center', stroke_width=2, stroke_fill=(255, 255, 255))
d.multiline_text(px(3, 8), 'ATRIUM\n(glass, 4 fl)\nentrance +\nsecurity', font=F, fill=(0, 0, 0), anchor='mm', align='center', stroke_width=2, stroke_fill=(255, 255, 255))
d.multiline_text(px(0, 88), 'LAWN + sloped walk\n(the Lakeside side)', font=F, fill=(255, 255, 255), anchor='mm', align='center', stroke_width=2, stroke_fill=(0, 60, 0))
d.text(px(-25, -15.5), 'secure yard', font=FS, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
d.text(px(-35, 0), 'SALLY PORT', font=F, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(120, 0, 0))
d.text((x - 70, y - 22), 'sculpture', font=FS, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
d.text(px(0, -24), 'old tower', font=FS, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
ARW = {'public main entrance (atrium)': (68, 26), 'police HQ front desk (public door)': (82, -38), 'police cars + staff (garage door)': (28, -80),
       'sally port gate': (-70, -15), 'jail visitors': (-70, 30), 'judges / court staff (secure door + drop-off)': (40, 78)}
for e in D['entrances']:
    f = ARW[e['name']]; p0, p1 = px(*f), px(*e['uv'])
    col = (255, 255, 255) if 'public' in e['name'] or 'front' in e['name'] else (255, 210, 60)
    d.line([p0, p1], fill=col, width=4); ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (0.45, -0.45):
        d.line([p1, (p1[0] - 16 * math.cos(ang + da), p1[1] - 16 * math.sin(ang + da))], fill=col, width=4)
    d.text(p0, e['name'], font=FS, fill=col, anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
for t, (u, v) in [('Davis Ave', (10, 132)), ('Innocence Blvd', (82, 30)), ('Roy Lowenstein Blvd', (0, -90)), ('Macdonald St', (-66, 70))]:
    d.text(px(u, v), t, font=F, fill=(255, 255, 0), anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0))
xs_ = [px(*q)[0] for q in kerb]; ys_ = [px(*q)[1] for q in kerb]
crop = img.crop((int(min(xs_) - 170), int(min(ys_) - 70), int(max(xs_) + 170), int(max(ys_) + 70))).convert('RGB')
c2 = ImageDraw.Draw(crop)
c2.line([(40, 110), (40, 60)], fill=(255, 255, 255), width=4); c2.polygon([(40, 46), (31, 64), (49, 64)], fill=(255, 255, 255))
c2.text((40, 125), 'N', font=F, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
c2.line([(20, crop.height - 30), (20 + 50 / MPP, crop.height - 30)], fill=(255, 255, 255), width=4)
c2.text((20 + 25 / MPP, crop.height - 46), '50 m', font=F, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
B = D['buildings']
LW = 600; sheet = Image.new('RGB', (crop.width + LW, max(crop.height, 900)), (24, 26, 30)); sheet.paste(crop, (0, 0))
L = ImageDraw.Draw(sheet); x0 = crop.width + 20; y = 20
L.text((x0, y), 'Cleveland Justice Center - plan v1', font=FT, fill=(255, 255, 255)); y += 34
lines = [f"The real complex (OpenStreetMap footprints) on the whole",
         f"sc1_19 block at ONE scale: {V['scale']:.2f} (max {V['max_scale']:.3f}),",
         f"turned {V['rotation_deg_real_to_lot']:+.1f} deg, no mirroring: Lakeside -> Davis Ave,",
         "Ontario -> Innocence Blvd, St Clair -> Roy Lowenstein,",
         "W 3rd -> Macdonald St. The block's width (115 m) sets",
         "the scale; the spare length becomes the Lakeside lawn.",
         "Every vanilla building on the block goes (sheriff + library too).", "",
         f"Courts Tower  {B['courts_tower']['height_m']} m, 26 fl x {B['courts_tower']['floor_to_floor_m']} m, roof z {B['courts_tower']['z_roof']}",
         "   (vanilla tower roof z 91.7 / top 97.5, white outline)",
         f"Police HQ     {B['police_hq']['height_m']} m, 9 fl, roof z {B['police_hq']['z_roof']}",
         f"Jail I        {B['jail_1']['height_m']} m, 10 fl, roof z {B['jail_1']['z_roof']}",
         f"Jail II       {B['jail_2']['height_m']} m, 11 fl (shell only)",
         f"Atrium        {B['atrium']['height_m']} m, 4 storeys of glass", f"Ground floor z {D['z_ground']} (sidewalks 27.6-28.6)", "",
         "Interiors: atrium entrance + security; tower lobby,",
         "courtroom A floor (L3-4), courtroom B floor (L5-6),",
         "chambers + offices (L7), one office at L25; police lobby",
         "+ front desk (L1) and offices (L2); Jail I sally port +",
         "booking (L1), one cell block (L2-3). Everything else is",
         "an empty shell behind the same dark glass.", "",
         "Sally port: Macdonald St -> gated yard between Jail I and",
         "Jail II -> enclosed bay in the Jail I base.",
         "Skybridges (red): Jail I - Jail II, police HQ - Jail II.",
         "Sculpture: our own bent dark tube at the plaza's NW end."]
for t in lines:
    L.text((x0, y), t, font=FS, fill=(225, 225, 225)); y += 19
y += 8
for col, t in [((212, 168, 132), 'courts tower'), ((130, 190, 230), 'atrium'), ((200, 168, 138), 'police HQ'), ((186, 166, 146), 'Jail I'),
               ((236, 228, 205), 'Jail II'), ((215, 210, 200), 'plaza'), ((90, 150, 70), 'lawn'), ((230, 80, 60), 'sally port / skybridges'),
               ((255, 230, 0), 'block kerb')]:
    L.rectangle([x0, y, x0 + 22, y + 14], fill=col); L.text((x0 + 30, y), t, font=FS, fill=(225, 225, 225)); y += 20
sheet.save(os.path.join(SV, 'plan_v1.png')); print('plan_v1.png', sheet.size)
