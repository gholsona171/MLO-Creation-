"""Preview the hand tattoo on its mesh layout: texture over the zone triangles + control points.  hand_preview.py <out.png>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image, ImageDraw
import hand_tattoo as H
tiles = []
for g in ('M', 'F'):
    for side in ('left', 'right'):
        img, uv, sc, lay, (tgt, src) = H.build(os.path.join(os.path.dirname(H.MESH['M']), '..', '..', 'src', 'skeleton_hand.png'), g, side)
        bg = Image.new('RGBA', img.size, (214, 176, 146, 255)); dr = ImageDraw.Draw(bg)
        for t in lay['tri']:
            if t[:, 0].max() - t[:, 0].min() > 0.4: continue
            px, py = H.zone_to_px(t[:, 0], t[:, 1]); dr.polygon(list(zip(px.tolist(), py.tolist())), outline=(150, 120, 100, 255))
        bg.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT)); dr = ImageDraw.Draw(bg)   # the texture is stored u-mirrored
        for x, y in tgt: dr.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 0, 0, 255))
        dr.text((8, 8), f'{g} {side}', fill=(0, 0, 255, 255))
        tiles.append(bg.convert('RGB').resize((768, 768)))
sheet = Image.new('RGB', (768 * 4, 768)); [sheet.paste(t, (i * 768, 0)) for i, t in enumerate(tiles)]
sheet.save(sys.argv[1])
