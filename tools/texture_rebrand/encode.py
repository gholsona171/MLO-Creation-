"""PNG -> DDS with the original's format and a full mip chain. usage: encode.py <png dir> <dds out dir> <name=FMT ...>"""
import sys, os
from PIL import Image
from dds_mips import make_levels, write_dds

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
for spec in sys.argv[3:]:
    name, fmt = spec.split('=')
    img = Image.open(os.path.join(src, name + '.png')).convert('RGBA')
    if fmt == 'DXT1':
        img.putalpha(255)
    lv = make_levels(img)
    write_dds(os.path.join(out, name + '.dds'), lv, fmt)
    print(name, fmt, img.size, len(lv), 'levels')
