"""Justice Center survey: one sheet with the block's map data in the lot frame (origin = courts tower centre, u towards Innocence
Blvd, v towards Davis Ave). Four panels, all with the kerb outline, the vanilla parts (grey) and the plan v1 buildings (orange, from v1_outlines.json):
  1. collision ground / roof height (lotframe.npz, from the 8 collision files)
  2. traffic: vehicle path nodes + car generators
  3. AI scenario points by kind
  4. live map entities by kind
Usage: py -3 survey/scripts/map_data_sheet.py  ->  survey/map_data_sheet.png"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
site = json.load(open(os.path.join(SV, 'site.json')))
lf = np.load(os.path.join(SV, 'lotframe.npz'))
Z, U0, V0, C = lf['Z'], float(lf['U0']), float(lf['V0']), float(lf['C'])
U1, V1 = U0 + Z.shape[1] * C, V0 + Z.shape[0] * C

S = 2.6                                            # pixels per metre
PW, PH = int((U1 - U0) * S), int((V1 - V0) * S)    # panel size
TOP, PAD, LEG = 46, 24, 150                        # title band, gaps, legend band under each panel
W, H = 2 * PW + 3 * PAD, 2 * (TOP + PH + LEG) + PAD
try:
    F = ImageFont.truetype('arial.ttf', 15); FB = ImageFont.truetype('arialbd.ttf', 18); FS = ImageFont.truetype('arial.ttf', 13)
except OSError:
    F = FB = FS = ImageFont.load_default()

PV1 = json.load(open(os.path.join(SV, 'v1_outlines.json')))          # plan v1 (fit_v1.py + design_v1.py): the one outline source
NEW = {'Courts tower': PV1['parts']['courts_tower']['uv'], 'Jail I': PV1['parts']['jail_1']['uv'], 'Police HQ': PV1['parts']['police_hq']['uv'],
       'Jail II': PV1['parts']['jail_2']['uv'], 'Plaza': PV1['parts']['plaza']['uv'], 'Atrium': PV1['design']['atrium']['uv'],
       'Sally port': PV1['design']['sally_port']['uv']}


def px(ox, oy, u, v):
    return ox + (u - U0) * S, oy + (V1 - v) * S


def frame(dr, ox, oy, title):
    dr.text((ox, oy - TOP + 12), title, font=FB, fill=(20, 20, 20))
    kerb = site['block']['kerb_outline_uv']
    dr.line([px(ox, oy, u, v) for u, v in kerb + kerb[:1]], fill=(230, 200, 0), width=3)
    for name, p in site['parts'].items():
        if 'uv' in p:
            dr.line([px(ox, oy, u, v) for u, v in p['uv'] + p['uv'][:1]], fill=(150, 150, 150), width=1)
    for name, poly in NEW.items():
        dr.line([px(ox, oy, u, v) for u, v in poly + poly[:1]], fill=(235, 110, 30), width=2)
    for txt, u, v in (('Davis Ave', 0, 95), ('Innocence Blvd', 72, 0), ('Roy Lowenstein Blvd', -10, -80), ('Macdonald St', -72, 0)):
        x, y = px(ox, oy, u, v); dr.text((x, y), txt, font=FS, fill=(30, 30, 120), anchor='mm')
    x, y = px(ox, oy, U0 + 5, V0 + 6); dr.line([(x, y), (x + 50 * S, y)], fill=(0, 0, 0), width=3); dr.text((x, y - 16), '50 m', font=FS, fill=(0, 0, 0))


def legend(dr, ox, oy, items):
    y = oy + PH + 12
    for i, (col, txt) in enumerate(items):
        cx, cy = ox + (i % 2) * (PW // 2), y + (i // 2) * 22
        dr.rectangle([cx, cy + 3, cx + 14, cy + 17], fill=col); dr.text((cx + 22, cy + 2), txt, font=F, fill=(20, 20, 20))


def heat(z):
    t = np.clip(np.nan_to_num((z - 25.0) / 75.0), 0, 1)       # 25 m (street) .. 100 m (tower top); empty cells painted grey below
    stops = np.array([[30, 60, 140], [40, 160, 160], [240, 220, 80], [220, 70, 40]], float)
    k = np.minimum((t * 3).astype(int), 2); f = (t * 3 - k)[..., None]
    rgb = stops[k] * (1 - f) + stops[k + 1] * f
    rgb[np.isnan(z)] = (60, 60, 60)
    return rgb.astype(np.uint8)


img = Image.new('RGB', (W, H), (250, 250, 248)); dr = ImageDraw.Draw(img)
slots = [(PAD, TOP), (2 * PAD + PW, TOP), (PAD, 2 * TOP + PH + LEG + PAD), (2 * PAD + PW, 2 * TOP + PH + LEG + PAD)]

# 1. collision heights
ox, oy = slots[0]
hm = Image.fromarray(heat(Z)[::-1]).resize((PW, PH), Image.NEAREST); img.paste(hm, (int(ox), int(oy)))
frame(dr, ox, oy, '1. Collision height (ground / roofs)')
legend(dr, ox, oy, [((30, 60, 140), 'street ~25-30 m'), ((40, 160, 160), 'plaza / podium ~31-45 m'), ((240, 220, 80), 'car park / low roofs'),
                    ((220, 70, 40), 'tower roof ~92-98 m'), ((60, 60, 60), 'no collision in survey'), ((235, 110, 30), 'proposed buildings')])

# 2. traffic
ox, oy = slots[1]; dr.rectangle([ox, oy, ox + PW, oy + PH], fill=(240, 240, 236)); frame(dr, ox, oy, '2. Traffic: path nodes + car spawns')
for n in site['path_nodes_in_block']:
    x, y = px(ox, oy, n['u'], n['v']); dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(40, 90, 200))
for g in site['cargens_in_block']:
    x, y = px(ox, oy, g['u'], g['v']); dr.rectangle([x - 4, y - 4, x + 4, y + 4], fill=(200, 40, 40))
legend(dr, ox, oy, [((40, 90, 200), f"vehicle path nodes ({len(site['path_nodes_in_block'])})"),
                    ((200, 40, 40), f"parked car spawns ({len(site['cargens_in_block'])})"), ((235, 110, 30), 'proposed buildings'),
                    ((150, 150, 150), 'vanilla buildings')])

# 3. scenarios
GROUPS = [('car', 'VEHICLE', (200, 40, 40)), ('standing / hanging out', 'HANG_OUT|STAND|LEANING|GUARD', (40, 140, 60)),
          ('walk routes', 'WALK', (40, 90, 200)), ('smoking / drinking', 'SMOKING|DRINKING', (160, 60, 170)), ('other', '', (120, 120, 120))]
ox, oy = slots[2]; dr.rectangle([ox, oy, ox + PW, oy + PH], fill=(240, 240, 236)); frame(dr, ox, oy, '3. AI scenario points')
cnt = {g[0]: 0 for g in GROUPS}
for s in site['scenarios_in_block']:
    t = s['type'].upper()
    g = next(g for g in GROUPS if g[1] == '' or any(k in t for k in g[1].split('|')))
    cnt[g[0]] += 1; x, y = px(ox, oy, s['u'], s['v']); dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=g[2])
legend(dr, ox, oy, [(g[2], f'{g[0]} ({cnt[g[0]]})') for g in GROUPS] + [((235, 110, 30), 'proposed buildings')])

# 4. entities
KINDS = {'vegetation': (60, 150, 60), 'street furniture': (40, 90, 200), 'lights': (230, 180, 0), 'other props': (160, 60, 170),
         'block model': (120, 120, 120), 'road / LOD': (200, 120, 120)}
ox, oy = slots[3]; dr.rectangle([ox, oy, ox + PW, oy + PH], fill=(240, 240, 236)); frame(dr, ox, oy, '4. Map entities (what removal touches)')
for e in site['entities_in_block_live']['list']:
    x, y = px(ox, oy, e['u'], e['v']); col = KINDS.get(e['kind'], (0, 0, 0)); dr.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=col)
bk = site['entities_in_block_live']['by_kind']
legend(dr, ox, oy, [(c, f'{k} ({bk.get(k, 0)})') for k, c in KINDS.items()])

out = os.path.join(SV, 'map_data_sheet.png'); img.save(out); print('MAP_DATA_SHEET', out, img.size)
