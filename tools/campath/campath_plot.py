"""campath_plot.py <track.json> <solids.json> <out.png> [x0 y0 x1 y1] : a top-down drawing of a campath track over its solids: boxes in
grey (darker = taller), each shot's path in its own colour with a dot every second and the aim drawn every 2 s; the shot number
at its start. Env ZBAND="z0,z1" draws only the boxes crossing that height band (one storey of a building). For checking a route before it goes to the rig."""
import json, math, sys
from PIL import Image, ImageDraw

T = json.load(open(sys.argv[1])); S = json.load(open(sys.argv[2])); out = sys.argv[3]
xs = [x for s in T['shots'] for x in s['x']]; ys = [y for s in T['shots'] for y in s['y']]
x0, y0, x1, y1 = (map(float, sys.argv[4:8]) if len(sys.argv) >= 8 else (min(xs) - 10, min(ys) - 10, max(xs) + 10, max(ys) + 10))
W = 1800; k = W / (x1 - x0); Hh = int((y1 - y0) * k)
im = Image.new('RGB', (W, Hh), (245, 242, 232)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - x0) * k, (y1 - y) * k)
import os
ZB = [float(v) for v in os.environ['ZBAND'].split(',')] if os.environ.get('ZBAND') else None   # only boxes crossing this height band
for b in sorted(S, key=lambda b: b['hi'][2]):
    if ZB and (b['hi'][2] < ZB[0] or b['lo'][2] > ZB[1]): continue
    if b['hi'][0] < x0 or b['lo'][0] > x1 or b['hi'][1] < y0 or b['lo'][1] > y1: continue
    g = int(max(60, 200 - (b['hi'][2] - b['lo'][2]) * 18)); a, c = P(b['lo'][0], b['hi'][1]), P(b['hi'][0], b['lo'][1])
    d.rectangle([a, c], fill=(g, g, g))
COL = [(220, 40, 40), (30, 120, 220), (20, 150, 60), (200, 120, 0), (150, 40, 180), (0, 160, 160)]
for i, s in enumerate(T['shots']):
    c = COL[i % len(COL)]; pts = [P(x, y) for x, y in zip(s['x'], s['y'])]
    d.line(pts, fill=c, width=3)
    for q in range(0, len(pts), int(1 / s['dt'])): d.ellipse([pts[q][0] - 3, pts[q][1] - 3, pts[q][0] + 3, pts[q][1] + 3], fill=c)
    for q in range(0, len(pts), int(2 / s['dt'])):
        yaw = math.radians(s['yaw'][q]); L = 22
        d.line([pts[q], (pts[q][0] - math.sin(yaw) * L, pts[q][1] - math.cos(yaw) * L)], fill=(40, 40, 40), width=1)
    d.text((pts[0][0] + 6, pts[0][1] - 14), f"{i + 1} {s['name']}", fill=c)
im.save(out); print('CAMPATH_PLOT', out, W, Hh)
