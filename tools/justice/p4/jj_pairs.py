"""13:00 / 23:00 pair sheet of the Jail I rig shots (jc_pair.sh writes <name>.png at 13:00 and <name>_n.png at 23:00): one row per view,
13:00 left, 23:00 right, labelled. Fails on a missing frame. Run: py -3 jj_pairs.py <shots dir> <out.jpg>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
D, OUT = Path(sys.argv[1]), Path(sys.argv[2])
names = sorted(p.stem for p in D.glob('*.png') if not p.stem.endswith('_n'))
assert names, 'no shots'
W = 720; rows = []
for n in names:
    a, b = D / f'{n}.png', D / f'{n}_n.png'
    assert a.exists() and b.exists(), f'missing frame for {n}'
    ims = []
    for p, tag in ((a, '13:00'), (b, '23:00')):
        im = Image.open(p).convert('RGB'); im = im.resize((W, int(im.height * W / im.width))); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 330, 26], fill=(0, 0, 0)); d.text((8, 6), f'{tag}  {n}', fill=(255, 255, 0)); ims.append(im)
    rows.append(ims)
H = rows[0][0].height
sheet = Image.new('RGB', (2 * W, H * len(rows)), (0, 0, 0))
for i, (x, y) in enumerate(rows): sheet.paste(x, (0, i * H)); sheet.paste(y, (W, i * H))
sheet.save(OUT, quality=82); print('PAIRS', len(rows), OUT)
