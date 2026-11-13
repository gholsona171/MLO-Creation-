"""Contact sheet of extracted Rockstar tattoo DDS files (DXT / A8) with ink bounding boxes. usage: ref_sheet.py <dir>"""
import sys, glob, os, numpy as np
from PIL import Image, ImageDraw
def load(f):
    try: return Image.open(f).convert('RGBA')
    except Exception:
        b = open(f, 'rb').read(); h = int.from_bytes(b[12:16], 'little'); w = int.from_bytes(b[16:20], 'little')
        a = np.frombuffer(b[128:128 + w * h], np.uint8).reshape(h, w)
        arr = np.zeros((h, w, 4), np.uint8); arr[..., 3] = a; return Image.fromarray(arr)
d0 = sys.argv[1]; fs = sorted(glob.glob(os.path.join(d0, '*', '*.dds')))
cols = 3; rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (512 * cols, 532 * rows), 'white'); d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    im = load(f).resize((512, 512)); im.save(f[:-4] + '.png')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    a = np.array(im)[..., 3]; ys, xs = np.where(a > 20)
    x, y = (i % cols) * 512, (i // cols) * 532
    sheet.paste(bg.convert('RGB'), (x, y + 20))
    d.text((x + 5, y + 3), os.path.basename(f) + ' ink x%.2f-%.2f y%.2f-%.2f' % (xs.min() / 512, xs.max() / 512, ys.min() / 512, ys.max() / 512), fill='red')
    d.rectangle([x, y + 20, x + 511, y + 531], outline='blue')
sheet.save(os.path.join(d0, 'sheet.png'))
