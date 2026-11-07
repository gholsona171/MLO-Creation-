"""DDS writer for GTA textures: BC1 (DXT1) / BC3 (DXT5) with a full mip chain down to 4x4, Pillow's own block encoder.

make_levels(img)  -> list of RGBA levels (premultiplied box/lanczos downsizing so transparent edges never go dark)
write_dds(path, levels, 'DXT5'|'DXT1')
"""
import io, struct
import numpy as np
from PIL import Image


def bleed(img):
    """Fill the RGB of fully transparent pixels from their neighbours (push-pull), so mips and DXT blocks never pull in black."""
    a = np.asarray(img.convert('RGBA')).astype(np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    w = (al > 0.02).astype(np.float32)
    pyr = [(rgb * w, w)]
    while pyr[-1][1].shape[0] > 1 and pyr[-1][1].shape[1] > 1:
        c, ww = pyr[-1]
        h, wd = c.shape[0] // 2 * 2, c.shape[1] // 2 * 2
        c = c[:h, :wd].reshape(h // 2, 2, wd // 2, 2, 3).sum((1, 3))
        ww = ww[:h, :wd].reshape(h // 2, 2, wd // 2, 2, 1).sum((1, 3))
        pyr.append((c, ww))
    fill = pyr[-1][0] / np.maximum(pyr[-1][1], 1e-6)
    for c, ww in reversed(pyr[:-1]):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        up = np.pad(up, ((0, c.shape[0] - up.shape[0]), (0, c.shape[1] - up.shape[1]), (0, 0)), mode='edge')
        known = c / np.maximum(ww, 1e-6)
        fill = np.where(ww > 0, known, up)
    out = np.where(w > 0, rgb, fill)
    res = np.concatenate([out, al], 2)
    return Image.fromarray((res * 255 + 0.5).clip(0, 255).astype(np.uint8), 'RGBA')


def make_levels(img, min_size=4):
    img = img.convert('RGBA')
    levels = [bleed(img)]
    a = np.asarray(img).astype(np.float32) / 255.0
    w, h = img.size
    while w > min_size and h > min_size:
        w, h = max(w // 2, min_size), max(h // 2, min_size)
        pm = a.copy(); pm[..., :3] *= pm[..., 3:4]
        small = np.asarray(Image.fromarray((pm * 255).astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0
        al = small[..., 3:4]
        rgb = np.where(al > 1e-3, small[..., :3] / np.maximum(al, 1e-3), 0).clip(0, 1)
        lv = Image.fromarray((np.concatenate([rgb, al], 2) * 255 + 0.5).clip(0, 255).astype(np.uint8), 'RGBA')
        levels.append(bleed(lv))
    return levels


def write_dds(path, levels, fmt='DXT5'):
    blobs = []
    for lv in levels:
        b = io.BytesIO(); lv.save(b, 'DDS', pixel_format=fmt); d = b.getvalue()
        assert d[84:88] == fmt.encode(), d[84:88]
        blobs.append(d[128:])
    w, h = levels[0].size
    bs = 8 if fmt == 'DXT1' else 16
    linear = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * bs
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000          # caps height width pixelformat mipmapcount linearsize
    hdr = struct.pack('<4sIIIIIII44x', b'DDS ', 124, flags, h, w, linear, 0, len(levels))
    pf = struct.pack('<II4sIIIII', 32, 0x4, fmt.encode(), 0, 0, 0, 0, 0)
    caps = struct.pack('<IIIII', 0x1000 | 0x8 | 0x400000, 0, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(hdr + pf + caps + b''.join(blobs))
    return path
