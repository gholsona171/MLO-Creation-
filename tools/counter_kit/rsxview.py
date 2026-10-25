#!/usr/bin/env python3
"""
c9_dj counter kit: a small textured software render of rsx models (prop/build/rsx.py) for the preview sheet and for checking cuts and
joints before anything goes in game. Perspective, z-buffer, Rockstar's diffuse textures (the .dds the build extracted), lambert light.
Not the game's look (no specular, tint palettes or decals), only shapes, textures and seams. MIT, our own code.
"""
import os, re
import numpy as np
from PIL import Image, ImageDraw

_TEX = {}


def _diffuse(shaders_xml):
    """shader index -> its diffuse texture name (or None)"""
    out = []
    for item in re.findall(r'<Item>\s*<Name>.*?</Parameters>', shaders_xml, re.S):
        m = re.search(r'<Item name="DiffuseSampler" type="Texture">\s*<Name>([^<]+)</Name>', item)
        out.append(m.group(1).lower() if m else None)
    return out


def _tex(texdir, name):
    key = (texdir, name)
    if key not in _TEX:
        img = None
        p = os.path.join(texdir, (name or '') + '.dds')
        if name and os.path.exists(p):
            try:
                im = Image.open(p).convert('RGB')
                if max(im.size) > 512: im = im.resize((min(512, im.size[0]), min(512, im.size[1])))
                img = np.asarray(im, dtype=np.float32) / 255.0
            except Exception:
                img = None
        _TEX[key] = img
    return _TEX[key]


def render(models, texdir, size=(640, 420), eye=(-2.5, -3.5, 2.2), at=None, fov=40.0, bg=(38, 40, 46)):
    """models = [(rsx.Model, 4x4 world matrix or None), ...]; returns a PIL image"""
    W, H = size
    tris, uvs, nrm, tex = [], [], [], []
    for m, M in models:
        M = np.eye(4) if M is None else np.asarray(M, float)
        dif = _diffuse(m.shaders_xml)
        for g in m.geos:
            P = g.pos @ M[:3, :3].T + M[:3, 3]
            N = (g.data['Normal'] @ M[:3, :3].T) if 'Normal' in g.data else None
            UV = g.data.get('TexCoord0')
            img = _tex(texdir, dif[g.shader] if g.shader < len(dif) else None)
            for t in g.tris:
                tris.append(P[t]); uvs.append(UV[t] if UV is not None else np.zeros((3, 2)))
                nrm.append(N[t].mean(0) if N is not None else np.cross(P[t][1] - P[t][0], P[t][2] - P[t][0]))
                tex.append(img)
    allp = np.vstack(tris) if tris else np.zeros((1, 3))
    at = np.asarray(at if at is not None else (allp.min(0) + allp.max(0)) / 2, float)
    eye = np.asarray(eye, float)
    f = at - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    foc = (H / 2) / np.tan(np.radians(fov / 2))
    zb = np.full((H, W), np.inf, np.float32)
    img = np.zeros((H, W, 3), np.float32); img[:] = np.array(bg) / 255.0
    L = np.array([0.35, -0.55, 0.75]); L /= np.linalg.norm(L)
    for P, UV, n, T in zip(tris, uvs, nrm, tex):
        d = P - eye
        z = d @ f
        if (z < 0.05).any(): continue
        sx = W / 2 + foc * (d @ r) / z
        sy = H / 2 - foc * (d @ u) / z
        x0, x1 = int(max(0, np.floor(sx.min()))), int(min(W - 1, np.ceil(sx.max())))
        y0, y1 = int(max(0, np.floor(sy.min()))), int(min(H - 1, np.ceil(sy.max())))
        if x0 > x1 or y0 > y1: continue
        den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
        if abs(den) < 1e-9: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a = ((sy[1] - sy[2]) * (X - sx[2]) + (sx[2] - sx[1]) * (Y - sy[2])) / den
        b = ((sy[2] - sy[0]) * (X - sx[2]) + (sx[0] - sx[2]) * (Y - sy[2])) / den
        c = 1 - a - b
        inside = (a >= -1e-4) & (b >= -1e-4) & (c >= -1e-4)
        if not inside.any(): continue
        iz = a / z[0] + b / z[1] + c / z[2]
        zz = 1.0 / np.maximum(iz, 1e-9)
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        ok = inside & (zz < sub)
        if not ok.any(): continue
        nn = n / max(1e-9, np.linalg.norm(n))
        if nn @ (eye - P.mean(0)) < 0: nn = -nn        # two-sided for the preview
        lam = 0.38 + 0.62 * max(0.0, float(nn @ L))
        if T is not None:
            w0, w1, w2 = a / z[0] * zz, b / z[1] * zz, c / z[2] * zz
            uu = (w0 * UV[0, 0] + w1 * UV[1, 0] + w2 * UV[2, 0]) % 1.0
            vv = (w0 * UV[0, 1] + w1 * UV[1, 1] + w2 * UV[2, 1]) % 1.0
            th, tw = T.shape[:2]
            col = T[(vv * th).astype(int).clip(0, th - 1), (uu * tw).astype(int).clip(0, tw - 1)]
        else:
            col = np.empty(a.shape + (3,), np.float32); col[:] = (0.7, 0.7, 0.72)
        sub[ok] = zz[ok]
        img[y0:y1 + 1, x0:x1 + 1][ok] = col[ok] * lam
    return Image.fromarray((img.clip(0, 1) * 255).astype(np.uint8))


def sheet(cells, cols, path, cell=(480, 320)):
    """cells = [(label, PIL image)] -> one labelled contact sheet"""
    rows = (len(cells) + cols - 1) // cols
    S = Image.new('RGB', (cols * cell[0], rows * (cell[1] + 18)), (20, 20, 24))
    d = ImageDraw.Draw(S)
    for i, (label, im) in enumerate(cells):
        x, y = (i % cols) * cell[0], (i // cols) * (cell[1] + 18)
        S.paste(im.resize(cell), (x, y))
        d.text((x + 4, y + cell[1] + 3), label, fill=(225, 225, 225))
    S.save(path)
