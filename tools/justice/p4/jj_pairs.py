"""The area-4 side-by-side sheet for Antonio: one row per view - Blender preview | game 13:00 | game 23:00 - labelled (jc_pair.sh writes
<name>.png at 13:00 and <name>_n.png at 23:00; jj_render.py writes the preview <name>.png from the same camera). No sit shots (client
builds skip sit tests, Antonio 2026-10-30). Fails on any missing frame. Without a preview dir it makes the two-column 13:00 / 23:00 sheet.
Run: py -3 jj_pairs.py <game shots dir> <out.jpg> [preview dir]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
D, OUT = Path(sys.argv[1]), Path(sys.argv[2]); PV = Path(sys.argv[3]) if len(sys.argv) > 3 else None
names = sorted(p.stem for p in D.glob('*.png') if not p.stem.endswith('_n'))
assert names, 'no shots'
W = 640; rows = []
for n in names:
    cols = ([(PV / f'{n}.png', 'Blender preview')] if PV else []) + [(D / f'{n}.png', 'game 13:00'), (D / f'{n}_n.png', 'game 23:00')]
    for p, _ in cols: assert p.exists(), f'missing frame for {n}: {p}'
    ims = []
    for p, tag in cols:
        im = Image.open(p).convert('RGB'); im = im.resize((W, int(W * 9 / 16))); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 360, 26], fill=(0, 0, 0)); d.text((8, 6), f'{tag}   {n.replace("p4_jail_", "")}', fill=(255, 255, 0)); ims.append(im)
    rows.append(ims)
H = rows[0][0].height; C = len(rows[0])
sheet = Image.new('RGB', (C * W, H * len(rows)), (0, 0, 0))
for i, row in enumerate(rows):
    for j, im in enumerate(row): sheet.paste(im, (j * W, i * H))
sheet.save(OUT, quality=82); print('PAIRS', len(rows), 'rows x', C, 'columns', OUT)
