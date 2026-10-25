"""Tower City review tool: before / after pair sheets from two shot folders (same camera names).
Run: py -3 pair_sheet.py <before_dir> <after_dir> <out.jpg> name1 name2 ...   (names without .png)
Each row: BEFORE <name> | AFTER <name>, each frame scaled to 800 px wide, labelled top-left. Fails on a missing frame."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
bdir, adir, out, names = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4:]
assert names, 'no shot names given'
W = 800; rows = []
for n in names:
    pair = []
    for tag, d in (('BEFORE', bdir), ('AFTER', adir)):
        p = d / f'{n}.png'
        if not p.exists(): raise SystemExit(f'PAIR_SHEET missing {p}')
        im = Image.open(p).convert('RGB'); im = im.resize((W, round(im.height * W / im.width)))
        dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 230, 22), fill=(0, 0, 0)); dr.text((5, 5), f'{tag} {n}', fill=(255, 255, 0))
        pair.append(im)
    rows.append(pair)
H = sum(r[0].height for r in rows); sheet = Image.new('RGB', (2 * W, H)); y = 0
for a, b in rows: sheet.paste(a, (0, y)); sheet.paste(b, (W, y)); y += a.height
out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out, quality=88)
print('PAIR_SHEET', out, len(rows), 'pairs')
