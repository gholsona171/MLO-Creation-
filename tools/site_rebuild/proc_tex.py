"""Procedural, seamlessly tiling textures for the site (numpy only; Blender's pixel order: row 0 = the bottom, v = row / height).
Made here rather than taken from a photo set because a photo tile carries its own cracks and stains, and on a 140 m lot those
repeat every few metres as a grid (Antonio 2026-11-23: "it's like a tile"). These are feature-free grain; the cracks, patches,
stains and wear come as decals scattered over the lot (pave.py), so nothing repeats.
  asphalt(n)   diffuse, normal, roughness: aged blacktop grain (binder + aggregate), no features
  lawn(n)      diffuse, normal, roughness: short lawn
  gravel(n)    diffuse, normal, roughness: a flat roof's ballast gravel
  decals(n)    RGBA atlas (straight alpha) + ATLAS: {name: (u0, v0, u1, v1)} - fine cracks, sealed cracks (tar snakes), alligator
               cracking, oil stains, broad wear (darker / lighter). (Square repair patches read as grey tiles in game: none.)
Values are set against the game's sunlight, which lifts dark greys a lot: the blacktop is ~0.12 here to read as aged asphalt.
Run: py -3 proc_tex.py   writes ../tex/new/proc_*.png previews (numpy + the standard library only)."""
import numpy as np, math

ATLAS = {'crack1': (0, 0, 1, .0625), 'crack2': (0, .0625, 1, .125), 'tar1': (0, .125, 1, .1875), 'tar2': (0, .1875, 1, .25),
         'alligator': (0, .25, .25, .5), 'oil1': (.5, .25, .75, .5), 'oil2': (.75, .25, 1, .5),
         'wear_dark': (0, .5, .5, 1), 'wear_light': (.5, .5, 1, 1)}


def band(n, lo, hi, seed):
    """periodic band-pass noise (feature sizes lo..hi pixels), zero mean, unit std."""
    r = np.random.default_rng(seed); f = np.fft.fft2(r.normal(size=(n, n)))
    ky = np.fft.fftfreq(n)[:, None]; kx = np.fft.fftfreq(n)[None, :]; k = np.sqrt(kx * kx + ky * ky) + 1e-9
    m = ((k >= 1.0 / hi) & (k <= 1.0 / lo)).astype(float)
    x = np.real(np.fft.ifft2(f * m)); return (x - x.mean()) / (x.std() + 1e-9)


def normal_from(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    v = np.stack([-gx, -gy, np.ones_like(h)], -1); v /= np.linalg.norm(v, axis=-1, keepdims=True)
    out = np.ones(h.shape + (4,), np.float32); out[..., :3] = v * .5 + .5; return out


def rgba(rgb, a=1.0):
    out = np.ones(rgb.shape[:2] + (4,), np.float32); out[..., :3] = np.clip(rgb, 0, 1); out[..., 3] = a; return out


def asphalt(n=1024, seed=1):
    """blacktop: dark binder, aggregate stones (bright and dark specks), fine pits. Feature-free at any scale over ~10 cm."""
    r = np.random.default_rng(seed)
    grain = band(n, 1, 3, seed) * .5 + band(n, 2, 6, seed + 1) * .35 + band(n, 6, 24, seed + 2) * .12
    stones = np.clip(band(n, 2, 5, seed + 3) - 1.5, 0, None)                 # sparse light aggregate
    pits = np.clip(-band(n, 1, 3, seed + 4) - 1.9, 0, None)                  # small dark pores
    lv = .12 + grain * .014 + stones * .05 - pits * .035
    tint = np.stack([lv, lv * .99, lv * .975], -1)
    h = grain * .6 + stones * 1.2 - pits * 1.0
    rough = rgba(np.repeat((.88 - stones * .1)[..., None], 3, -1))
    return rgba(tint), normal_from(h, 2.0), rough


def lawn(n=1024, seed=11):
    """short, watered lawn: blade streaks (slightly directional), light and dark greens, a little straw."""
    b = band(n, 1, 2, seed) * .5 + band(n, 1, 4, seed + 1) * .35
    streak = np.roll(band(n, 1, 3, seed + 2), 1, 0) * .5 + band(n, 1, 3, seed + 2) * .5
    tone = band(n, 20, 120, seed + 3) * .5                                    # soft mowing / watering variation
    straw = np.clip(band(n, 3, 8, seed + 4) - 1.6, 0, None)
    mott = band(n, 40, 250, seed + 5) * .5                                      # half-metre to metre patches of lush / thinner turf
    g = .19 + b * .045 + streak * .03 + tone * .02 + mott * .025
    rgb = np.stack([g * .80 + straw * .16 + np.clip(-mott, 0, None) * .02, g, g * .42 + straw * .04], -1)   # (a muted, olive lawn)
    return rgba(rgb), normal_from(b + streak, 3.0), rgba(np.full(b.shape + (3,), .95))


def gravel(n=1024, seed=21):
    """roof ballast: packed rounded pebbles 1-3 cm (tile = 2 m -> ~2 mm / px), greys and beiges, dark gaps between."""
    r = np.random.default_rng(seed); yy, xx = np.mgrid[0:n, 0:n]
    h = np.zeros((n, n)); col = np.zeros((n, n, 3)); col[:] = (.20, .19, .18)
    for _ in range(int(n * n / 30)):
        cx, cy, rad = r.uniform(0, n), r.uniform(0, n), r.uniform(3.5, 8.0)
        x0, x1, y0, y1 = int(cx - rad) - 1, int(cx + rad) + 2, int(cy - rad) - 1, int(cy + rad) + 2
        X = np.arange(x0, x1) % n; Y = np.arange(y0, y1) % n
        dx = (np.arange(x0, x1) - cx)[None, :]; dy = (np.arange(y0, y1) - cy)[:, None]
        d = 1 - (dx * dx + dy * dy) / (rad * rad); m = d > 0
        hh = np.sqrt(np.clip(d, 0, 1)) * rad / 8
        sub = h[np.ix_(Y, X)]; upd = m & (hh > sub)
        tone = r.uniform(.45, .78); c = np.array([tone, tone * r.uniform(.94, 1.0), tone * r.uniform(.86, .98)])
        sh = (.75 + .25 * np.sqrt(np.clip(d, 0, 1)))[..., None]
        cs = col[np.ix_(Y, X)]; cs[upd] = (c[None, None, :] * sh)[upd]; col[np.ix_(Y, X)] = cs
        sub[upd] = hh[upd]; h[np.ix_(Y, X)] = sub
    return rgba(col), normal_from(h, 4.0), rgba(np.repeat((.9 - h[..., None] * .2), 3, -1))


def _crack_path(r, length, wander, bound=1e9):
    """a wandering polyline along x (0..length px) around y 0, kept within +-bound px of the axis (its atlas strip)."""
    pts = [(0.0, 0.0)]; ang = 0.0
    while pts[-1][0] < length:
        x0, y0 = pts[-1]
        ang = np.clip(ang + r.normal(0, .35) - .08 * y0 / max(bound, 1), -.6, .6)                 # (drawn back to the axis)
        step = r.uniform(4, 10); y1 = float(np.clip(y0 + step * math.sin(ang) * wander, -bound, bound))
        pts.append((x0 + step * math.cos(ang), y1))
    return pts


def _stroke(img_a, pts, width, ox, oy, val=1.0):
    """rasterise a polyline of given half-width (px) into an alpha array (max)."""
    H, W = img_a.shape
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        x0 += ox; x1 += ox; y0 += oy; y1 += oy
        xa, xb = int(min(x0, x1) - width - 2), int(max(x0, x1) + width + 2); ya, yb = int(min(y0, y1) - width - 2), int(max(y0, y1) + width + 2)
        xa, ya = max(xa, 0), max(ya, 0); xb, yb = min(xb, W), min(yb, H)
        if xa >= xb or ya >= yb: continue
        yy, xx = np.mgrid[ya:yb, xa:xb]; vx, vy = x1 - x0, y1 - y0; L2 = vx * vx + vy * vy + 1e-9
        t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1); d = np.hypot(xx - x0 - t * vx, yy - y0 - t * vy)
        a = np.clip(1 - (d - width) / 1.2, 0, 1) * val
        img_a[ya:yb, xa:xb] = np.maximum(img_a[ya:yb, xa:xb], a)


def decals(n=1024, seed=31):
    """the decal atlas (see ATLAS). Colour is straight (not premultiplied); alpha carries the shape."""
    r = np.random.default_rng(seed); A = np.zeros((n, n, 4), np.float32)
    def region(key):
        u0, v0, u1, v1 = ATLAS[key]; return int(v0 * n), int(v1 * n), int(u0 * n), int(u1 * n)
    for key, w, branch in (('crack1', .9, 3), ('crack2', 1.3, 2)):               # fine cracks: dark hairlines with spalled edges
        y0, y1, x0, x1 = region(key); a = np.zeros((y1 - y0, x1 - x0))
        hb = (y1 - y0) / 2 - 6; p = _crack_path(r, x1 - x0 - 12, 1.0, hb); _stroke(a, p, w, 6, (y1 - y0) / 2)
        for _ in range(branch):
            k = r.integers(5, len(p) - 5); q = _crack_path(r, r.uniform(15, 40), 1.0)
            ang = r.choice([-1, 1]) * r.uniform(.4, 1.0); px, py = p[k]
            q = [(px + x * math.cos(ang) - y * math.sin(ang), py + x * math.sin(ang) + y * math.cos(ang)) for x, y in q]
            _stroke(a, [pt for pt in q if 2 < pt[0] < x1 - x0 - 2 and abs(pt[1]) < hb], w * .7, 0, (y1 - y0) / 2)
        halo = np.clip(np.maximum.reduce([np.roll(a, s, ax) for s in (-2, 2) for ax in (0, 1)]) * .35, 0, .35)
        A[y0:y1, x0:x1, :3] = .025; A[y0:y1, x0:x1, 3] = np.maximum(a * .95, halo)
    for key, w in (('tar1', 4.0), ('tar2', 5.5)):                                  # sealed cracks: glossy black bands, ragged edges
        y0, y1, x0, x1 = region(key); a = np.zeros((y1 - y0, x1 - x0))
        hb = (y1 - y0) / 2 - w - 4; p = _crack_path(r, x1 - x0 - 16, .8, hb); _stroke(a, p, w, 8, (y1 - y0) / 2)
        A[y0:y1, x0:x1, :3] = .02; A[y0:y1, x0:x1, 3] = a * .92
    y0, y1, x0, x1 = region('alligator'); m = y1 - y0                               # alligator cracking: a crack net in a soft blob
    a = np.zeros((m, m)); yy, xx = np.mgrid[0:m, 0:m]; c = (m - 1) / 2
    blob = np.clip(1.15 - np.hypot(xx - c, yy - c) / (c * .9) + band(m, 8, 40, 5)[:m, :m] * .25, 0, 1)
    pts = r.uniform(0, m, (90, 2)); d1 = np.full((m, m), 1e9); d2 = np.full((m, m), 1e9)
    for px, py in pts:
        d = np.hypot(xx - px, yy - py); d2 = np.where(d < d1, d1, np.minimum(d2, d)); d1 = np.minimum(d1, d)
    net = np.clip(1 - (d2 - d1) / 1.6, 0, 1)
    A[y0:y1, x0:x1, :3] = .03; A[y0:y1, x0:x1, 3] = net * blob * .9
    for key, s in (('oil1', 41), ('oil2', 43)):                                    # oil stains: dark, soft-edged, uneven
        y0, y1, x0, x1 = region(key); m = y1 - y0; yy, xx = np.mgrid[0:m, 0:m]; c = (m - 1) / 2
        sh = np.clip(1.0 - np.hypot(xx - c, (yy - c) * 1.25) / (c * .8) + band(m, 6, 40, s)[:m, :m] * .35, 0, 1)
        drip = np.clip(band(m, 2, 10, s + 1)[:m, :m] * .25 + .75, 0, 1)
        A[y0:y1, x0:x1, :3] = .02; A[y0:y1, x0:x1, 3] = sh ** 1.4 * drip * .7
    for key, rgbv, amax in (('wear_dark', .06, .30), ('wear_light', .22, .20)):    # broad wear / sun-bleach: big soft tone shifts
        y0, y1, x0, x1 = region(key); m = y1 - y0; yy, xx = np.mgrid[0:m, 0:m]; c = (m - 1) / 2
        sh = np.clip(1.0 - np.hypot(xx - c, yy - c) / c + band(m, 80, 512, len(key))[:m, :m] * .25, 0, 1)
        A[y0:y1, x0:x1, :3] = rgbv; A[y0:y1, x0:x1, 3] = sh ** 1.6 * amax
    return A


def save_png(path, px):
    """preview writer (no PIL needed): 8-bit RGBA PNG, top row first."""
    import zlib, struct
    a = (np.clip(px[::-1], 0, 1) * 255).astype(np.uint8); h, w = a.shape[:2]
    raw = b''.join(b'\x00' + a[i].tobytes() for i in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


if __name__ == '__main__':
    from pathlib import Path
    o = Path(__file__).resolve().parents[1] / 'tex' / 'new'; o.mkdir(parents=True, exist_ok=True)
    save_png(o / 'proc_asphalt.png', asphalt(512)[0]); save_png(o / 'proc_lawn.png', lawn(512)[0])
    save_png(o / 'proc_gravel.png', gravel(512)[0])
    d = decals(1024); bg = asphalt(1024)[0]; comp = bg.copy(); comp[..., :3] = bg[..., :3] * (1 - d[..., 3:]) + d[..., :3] * d[..., 3:]
    save_png(o / 'proc_decals_on_asphalt.png', comp)
    print('PROC_TEX_PASS', o)
