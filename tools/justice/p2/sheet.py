import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1])); out = sys.argv[2]; W = int(sys.argv[3]) if len(sys.argv) > 3 else 10
ims = [(os.path.basename(f), Image.open(f).convert('RGB').resize((128, 128))) for f in fs]
H = (len(ims) + W - 1) // W; s = Image.new('RGB', (W * 132, H * 146), 'white'); d = ImageDraw.Draw(s)
for i, (n, im) in enumerate(ims): x, y = (i % W) * 132, (i // W) * 146; s.paste(im, (x + 2, y + 2)); d.text((x + 2, y + 131), n[:22], fill='black')
s.save(out); print(len(ims))
