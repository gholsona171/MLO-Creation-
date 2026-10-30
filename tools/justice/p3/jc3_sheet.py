"""Side-by-side sheet for an area's hand-back: one row per view - Blender preview | game 13:00 | game 23:00 - each cell labelled; a view
with no Blender preview (street views) shows the note instead. Run:
  py -3 jc3_sheet.py <blender dir> <game shots dir> <out.jpg> <title> view [view ...]
(view = the shot's base name, e.g. p3_a3_lobby: <blender dir>/<view>.png, <game dir>/<view>.png and <view>_n.png)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
CW, CH, HEAD, LAB = 720, 405, 90, 34
def font(n):
    for f in ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()
def cell(path, note):
    im = Image.new('RGB', (CW, CH), (36, 36, 40))
    if path.exists(): src = Image.open(path).convert('RGB'); src.thumbnail((CW, CH)); im.paste(src, ((CW - src.width) // 2, (CH - src.height) // 2))
    else: ImageDraw.Draw(im).text((24, CH // 2 - 14), note, fill=(200, 200, 200), font=font(24))
    return im
def main():
    bdir, gdir, out, title, views = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5:]
    assert views, 'no views given'
    missing = [v for v in views if not (gdir / f'{v}.png').exists() or not (gdir / f'{v}_n.png').exists()]
    assert not missing, f'game shots missing (13:00 / 23:00): {missing}'
    sheet = Image.new('RGB', (3 * CW, HEAD + len(views) * (CH + LAB)), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    d.text((16, 14), title, fill=(240, 240, 240), font=font(34))
    for i, h in enumerate(('Blender preview', 'in game 13:00', 'in game 23:00')): d.text((i * CW + 16, 58), h, fill=(190, 190, 200), font=font(22))
    for r, v in enumerate(views):
        y = HEAD + r * (CH + LAB)
        d.text((16, y + 4), v.replace('p3_a3_', '').replace('_', ' '), fill=(235, 200, 90), font=font(22))
        for i, (p, note) in enumerate(((bdir / f'{v}.png', 'street view: in game only'), (gdir / f'{v}.png', 'missing'), (gdir / f'{v}_n.png', 'missing'))):
            sheet.paste(cell(p, note), (i * CW, y + LAB))
    sheet.save(out, quality=88); print('SHEET', out, sheet.size, len(views), 'views')
if __name__ == '__main__': main()
