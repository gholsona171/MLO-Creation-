"""Justice Center survey: the collision height map resampled into the LOT FRAME (origin = courts tower centre, u along heading
50 deg = towards Innocence Blvd, v along 140 deg = towards Davis Ave / the plaza). 0.5 m pixels, 10 m grid, 50 m labels.
Writes survey/lotframe_height.png and lotframe.npz (for the plan sheet)."""
import numpy as np
from PIL import Image, ImageDraw
ROOT = r'C:\Users\anton\Documents\Codex\JusticeCenter'
d = np.load(ROOT + r'\survey\heightmap.npz'); top, x0, y0, cell = d['top'], float(d['x0']), float(d['y0']), float(d['cell'])
OX, OY, H = 335.87, -1640.11, np.radians(50.0)
U0, U1, V0, V1, C = -80, 100, -100, 130, 0.5
us = np.arange(U0, U1, C) + C / 2; vs = np.arange(V0, V1, C) + C / 2
GU, GV = np.meshgrid(us, vs)
WX = OX + GU * np.cos(H) - GV * np.sin(H); WY = OY + GU * np.sin(H) + GV * np.cos(H)
i = ((WX - x0) / cell).astype(int); j = ((WY - y0) / cell).astype(int)
ok = (i >= 0) & (i < top.shape[1]) & (j >= 0) & (j < top.shape[0])
Z = np.full(GU.shape, np.nan); Z[ok] = top[j[ok], i[ok]]; Z[Z < -1e8] = np.nan
np.savez_compressed(ROOT + r'\survey\lotframe.npz', Z=Z, U0=U0, V0=V0, C=C, OX=OX, OY=OY, H=50.0)
g = np.nan_to_num(np.clip((Z - 24) / 16, 0, 1) ** 0.7, nan=0)          # 24..40 m in grey, above 40 white
rgb = np.stack([g, g, g], -1); hi = Z > 40; rgb[hi] = [1, .85, .6]
img = Image.fromarray((rgb[::-1] * 255).astype(np.uint8)).resize((GU.shape[1] * 2, GU.shape[0] * 2), Image.NEAREST)
dr = ImageDraw.Draw(img); s = 2 / C
for u in range(U0, U1 + 1, 10):
    x = (u - U0) * s; dr.line([(x, 0), (x, img.height)], fill=(60, 120, 220) if u % 50 else (220, 60, 60), width=1)
    if u % 50 == 0: dr.text((x + 2, 2), f'u{u}', fill=(255, 60, 60))
for v in range(V0, V1 + 1, 10):
    y = (V1 - v) * s; dr.line([(0, y), (img.width, y)], fill=(60, 120, 220) if v % 50 else (220, 60, 60), width=1)
    if v % 50 == 0: dr.text((2, y + 2), f'v{v}', fill=(255, 60, 60))
img.save(ROOT + r'\survey\lotframe_height.png'); print(img.size)
