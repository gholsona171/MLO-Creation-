"""c9_tattoos build: client artwork PNGs -> ink cut-outs -> tattoo textures laid out like Rockstar's own -> ytd + overlay XML +
shop_tattoo.meta + fxmanifest + rcore list. Everything in build/ is rebuilt from src/ on every run.

  py -3 build.py            build the pack into build/c9_tattoos (+ art/ previews)
  py -3 build.py cal        build the rig-only UV calibration pack build/c9_tattoos_cal (grid over each zone's whole UV square)
  py -3 build.py deploy     build, then copy the resource into the Cleveland-RP clone and the rig, and C9Tattoos.json into rcore

Placement values (uvPos / scale / rotation per gender) come from the Rockstar references named in TATTOOS and from the
in-game UV calibration (photos/cal_*), see README.md.
"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\MLO-Creation\tools\texture_rebrand')
from dds_mips import make_levels, write_dds  # noqa: E402

SRC = os.path.join(HERE, 'src')
ART = os.path.join(HERE, 'art')
BUILD = os.path.join(HERE, 'build')
REPO_RES = r'C:\C9Test\export\Cleveland-RP\resources\[scripts]\[rcore]'
LIVE_RES = r'C:\C9Test\live\resources\[scripts]\[rcore]'
RES = 'c9_tattoos'
COLLECTION = 'c9_tattoos_overlays'
TEX = 1024
INK_RGB = (20, 20, 22)

# Each tattoo: source art, how to cut it out, the box (fractions of the texture) its art fills, and per-gender overlay values.
# ref = the Rockstar tattoo whose layout and overlay values it copies (see README.md for the numbers and the calibration).
TATTOOS = [
    dict(key='c9_tat_cleveland_sleeve', label='Cleveland Sleeve', price=3000, zone='ZONE_RIGHT_ARM', group='ARM_RIGHT_FULL_SLEEVE',
         facing='TATTOO_RIGHT', src='cleveland_sleeve.png', cut='paper', fit='sleeve',
         ref='MP_Sum2_Tat_013 (mpsum2_overlays, ARM_RIGHT_FULL_SLEEVE)',
         M=dict(uv=(0.510, 0.620), scale=(0.320, 0.420), rot=7.20),
         F=dict(uv=(0.520, 0.620), scale=(0.324, 0.450), rot=9.36),
         box=(0.35, 0.12, 0.65, 0.87)),
    dict(key='c9_tat_faith_sleeve', label='Faith Over Fear Sleeve', price=3000, zone='ZONE_LEFT_ARM', group='ARM_LEFT_FULL_SLEEVE',
         facing='TATTOO_LEFT', src='faith_sleeve.png', cut='paper', fit='sleeve',
         ref='MP_Sum2_Tat_049 (mpsum2_overlays, ARM_LEFT_FULL_SLEEVE)',
         M=dict(uv=(0.530, 0.635), scale=(0.250, 0.410), rot=-3.50),
         F=dict(uv=(0.530, 0.620), scale=(0.250, 0.460), rot=-5.40),
         box=(0.29, 0.11, 0.70, 0.89)),
    dict(key='c9_tat_cleveland_chest', label='Cleveland Chest Piece', price=5000, zone='ZONE_TORSO', group='CHEST_STOM_FULL',
         facing='TATTOO_FRONT', src='cleveland_chest.png', cut='skin', fit='fill',
         ref='MP_Luxe_Tat_012 (mpluxe2_overlays, CHEST_STOM_FULL), rig: raised 0.03 (text clear of the belt), 12 % wider (shoulders)',
         M=dict(uv=(0.730, 0.420), scale=(0.380, 0.350), rot=0.0),
         F=dict(uv=(0.745, 0.480), scale=(0.370, 0.310), rot=0.0),
         box=(0.05, 0.01, 0.92, 0.99)),
    dict(key='c9_tat_cleveland_back', label='Cleveland Back Piece', price=5000, zone='ZONE_TORSO', group='BACK_FULL',
         facing='TATTOO_BACK', src='cleveland_back.png', cut='skin', fit='fill',
         ref='BACK_FULL family (MP_Luxe_Tat_022 / MP_Security_Tat_004, x 0.22-0.25) + rig markers: spine at x 0.245, same height band as the chest',
         M=dict(uv=(0.245, 0.420), scale=(0.420, 0.380), rot=0.0),
         F=dict(uv=(0.250, 0.470), scale=(0.410, 0.340), rot=0.0),
         box=(0.00, 0.00, 1.00, 1.00)),
    dict(key='c9_tat_crown144_neck', label='144 Crown Neck', price=2500, zone='ZONE_HEAD', group='NECK_FRONT',
         facing='TATTOO_FRONT', src='crown144_neck.png', cut='photo', fit='fill',
         photo=dict(bg='grey', jaw=(890, 150, 0.000514), side=(380, 1400, 110), skin_box=(0.0, 0.80, 1.0, 1.0), light=False),
         ref='MP_Heist3_Tat_014 (mpheist3_overlays, NECK_FRONT, 0.498/0.25), grown to jaw-to-collar and round the sides',
         M=dict(uv=(0.498, 0.255), scale=(0.520, 0.120), rot=0.0),
         F=dict(uv=(0.498, 0.255), scale=(0.520, 0.120), rot=0.0),
         box=(0.00, 0.00, 1.00, 1.00)),
    dict(key='c9_tat_smoke_back_neck', label='Smoke Back Neck', price=2500, zone='ZONE_HEAD', group='NECK_BACK',
         facing='TATTOO_BACK', src='smoke_back_neck.png', cut='photo', fit='fill',
         photo=dict(bg='white', jaw=(1090, 130, 0.0003), side=(0, 99999, 0), skin_box=(0.0, 0.93, 1.0, 1.0), light=True),
         ref='MP_Buis_M_Neck_003 / MP_Bus_Tat_M_006 (mpbusiness_overlays, NECK_BACK, 0.0/0.45), grown hairline-to-shoulders',
         M=dict(uv=(0.000, 0.430), scale=(0.500, 0.180), rot=0.0),
         F=dict(uv=(0.000, 0.430), scale=(0.500, 0.180), rot=0.0),
         box=(0.00, 0.00, 1.00, 1.00)),
]
LIGHT_RGB = (205, 205, 205)


# ---------------------------------------------------------------- ink extraction
def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def curve(x, lo, hi, gamma=1.0):
    return np.clip((x - lo) / (hi - lo), 0, 1) ** gamma


def crop_to_ink(alpha, pad=8):
    ys, xs = np.where(alpha > 0.03)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, alpha.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, alpha.shape[1])
    return alpha[y0:y1, x0:x1]


def cut_paper(path):
    """Black-and-grey ink on white paper: alpha = ink density (1 - luminance) with paper white and the faint grey wash at 0."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    ink = 1.0 - lum(a) / 255.0
    alpha = curve(ink, 0.10, 0.92, 1.1)
    # the arm silhouette: everything not reachable from the paper border through near-white pixels
    paper = ndi.binary_opening(ink < 0.06, iterations=1)
    lab, _ = ndi.label(paper)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    outside = np.isin(lab, list(border))
    alpha[outside] = 0
    return crop_to_ink(unwrap_arm(alpha, ~outside)), None


def unwrap_arm(alpha, inside):
    """The drawing is a front view of a round arm: its width is the arm's diameter, but on the skin the visible front covers
    half the circumference (pi/2 x wider), squeezed most at the sides. Unroll it per row as a cylinder: output column
    x_o (centred) samples the drawing at x = c + r sin(x_o / r), r and c from that row's arm outline. The sides (|angle| near
    90 deg, where the front wraps round to the inner arm) fade out."""
    rows = np.where(inside.any(1))[0]
    h, w = alpha.shape
    left = np.full(h, np.nan); right = np.full(h, np.nan)
    for y in rows:
        xs = np.where(inside[y])[0]; left[y], right[y] = xs.min(), xs.max()
    idx = np.arange(h); ok = ~np.isnan(left)
    left = np.interp(idx, idx[ok], left[ok]); right = np.interp(idx, idx[ok], right[ok])
    c = ndi.gaussian_filter1d((left + right) / 2, 12); r = np.maximum(ndi.gaussian_filter1d((right - left) / 2, 12), 4)
    half = int(np.ceil(np.pi / 2 * r.max())); xo = np.arange(-half, half + 1)[None, :].astype(np.float64)
    theta = xo / r[:, None]
    valid = np.abs(theta) <= np.pi / 2
    sx = c[:, None] + r[:, None] * np.sin(np.clip(theta, -np.pi / 2, np.pi / 2))
    sy = np.repeat(idx[:, None].astype(np.float64), xo.shape[1], 1)
    out = ndi.map_coordinates(alpha, [sy, sx], order=1, mode='constant')
    t = np.clip((np.pi / 2 - np.abs(theta)) / (np.pi / 2 * 0.22), 0, 1)       # fade over the outer 22 % of the angle
    out = out * (t * t * (3 - 2 * t)) * valid
    out[~ok] = 0
    return out


def fill_holes(v, hole, shift=48):
    """Fill v inside hole: smooth tone from the ring around it (normalized convolution), plus fine detail borrowed from the
    same-sized area just above the hole, blended in with a feathered edge."""
    known = (~hole).astype(np.float32)
    tone = v.copy()
    for s in (24, 12, 6):
        t = ndi.gaussian_filter(v * known, s) / np.maximum(ndi.gaussian_filter(known, s), 1e-4)
        tone = np.where(hole, t, v)
    detail = v - ndi.gaussian_filter(v, 3)
    detail = np.roll(detail, shift, axis=0)                       # rows above the hole land on it
    filled = np.clip(tone + 0.9 * detail, 0, 1)
    feather = np.clip(ndi.gaussian_filter(hole.astype(np.float32), 4) * 1.6, 0, 1)
    return v * (1 - feather) + filled * feather


def cut_skin(path):
    """Ink rendered on skin (a mock-up on a body): the body silhouette from the black / transparent surround, then alpha = how much
    darker each pixel is than the local bare-skin tone. Reddish skin features (nipples / areolas, red fringe on the cut edge)
    are skin, not ink: they are filled from the ink around them / dropped."""
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).astype(np.float32)
    L = lum(a); src_alpha = a[..., 3] / 255.0
    # body silhouette: not the near-black surround reachable from the border, and opaque in the source alpha. Judged on a
    # blurred luminance so deep-black ink touching the body outline (armpit shadows) does not leak into the surround.
    dark = (ndi.gaussian_filter(L, 4) < 6) | (src_alpha < 0.5)
    lab, _ = ndi.label(dark)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    body = ~np.isin(lab, list(border))
    body = ndi.binary_fill_holes(body)
    body = ndi.binary_opening(body, iterations=3)
    lab2, n = ndi.label(body)                       # keep the largest piece only (drops stray fringe islands)
    if n > 1:
        sizes = ndi.sum(body, lab2, range(1, n + 1)); body = lab2 == (1 + int(np.argmax(sizes)))
    body = ndi.binary_erosion(body, iterations=10)                   # blur grew the outline + the mock-up's light / dark rim
    # local bare-skin tone: bright envelope of the body at 1/4 scale (120 px window), smoothed, with a floor
    s = 4; Ls = np.where(body, L, 0)[::s, ::s]
    env = ndi.maximum_filter(Ls, size=31)
    env = ndi.gaussian_filter(env, 8)
    env = np.asarray(Image.fromarray(env).resize((L.shape[1], L.shape[0]), Image.BILINEAR))
    env = np.maximum(env, 0.75 * np.percentile(L[body], 99.5))
    ink = 1.0 - L / np.maximum(env, 1.0)
    alpha = curve(ink, 0.12, 0.90, 1.0)
    # reddish skin features: smoothed redness, blobs well above the body's own warm tint
    red = (a[..., 0] - a[..., 2]) / np.maximum(L, 8.0)
    reds = ndi.gaussian_filter(np.where(body, red, 0), 5)
    base = np.percentile(red[body], 90)
    blobs = reds > base + 0.07
    lab3, n3 = ndi.label(blobs)
    spots = np.zeros_like(blobs)
    edge = ndi.binary_dilation(~body, iterations=14)
    for i in range(1, n3 + 1):
        m = lab3 == i; sz = m.sum()
        if sz >= 120 and not (m & edge).any():
            spots |= m
    spots = ndi.binary_dilation(spots, iterations=12)
    alpha = fill_holes(alpha, spots)
    # red fringe along the cut edge: drop reddish pixels in a band inside the silhouette
    band = body & ndi.binary_dilation(~body, iterations=10)
    alpha[band & (red > base)] = 0
    alpha = alpha * np.clip(ndi.gaussian_filter(body.astype(np.float32), 6) * 2 - 1, 0, 1)   # soft silhouette edge, no outline
    alpha[~body] = 0
    print(f'  {os.path.basename(path)}: skin features filled: {int(ndi.label(spots)[1])} spot(s), red-fringe band cleared')
    return crop_to_ink(alpha, pad=2), None


def cut_photo(path, cfg):
    """Photo mock-up of a neck tattoo on real skin: studio background (grey / white) and hair / beard above the jaw or hairline
    are dropped; ink = darker than the bare skin (sampled in skin_box, a strip of bare skin below the tattoo). With light=True the
    smoke highlights that are LIGHTER than their surroundings become light-grey ink, so the smoke reads on dark skin too."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    L = lum(a); h, w = L.shape
    sat = a.max(2) - a.min(2)
    bgpix = (sat < 22) & (L > (150 if cfg['bg'] == 'grey' else 225))
    lab, _ = ndi.label(ndi.binary_opening(bgpix, iterations=2))
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    body = ndi.binary_fill_holes(~np.isin(lab, list(border)))
    body = ndi.binary_erosion(body, iterations=3)
    # jaw line / hairline: a parabola y = cy - k (x - cx)^2; outside the side columns everything above y_side goes (hair)
    cx, cy, k = cfg['jaw']; x0s, x1s, yside = cfg['side']
    xs = np.arange(w); ycut = cy - k * (xs - cx) ** 2
    ycut = np.where((xs < x0s) | (xs > x1s), np.maximum(ycut, yside), ycut)
    keep = np.clip((np.arange(h)[:, None] - ycut[None, :]) / 25.0, 0, 1)       # 25 px feather below the line
    keep = keep * keep * (3 - 2 * keep)
    bx0, by0, bx1, by1 = cfg['skin_box']
    box = np.zeros_like(body); box[int(by0 * h):int(by1 * h), int(bx0 * w):int(bx1 * w)] = True
    skin = np.percentile(L[box & body], 60)
    dark = curve(1.0 - L / skin, 0.15, 0.85)
    light = None
    if cfg['light']:
        known = body.astype(np.float32)
        local = ndi.gaussian_filter(L * known, 30) / np.maximum(ndi.gaussian_filter(known, 30), 1e-4)
        lift = curve((L - local) / skin, 0.04, 0.30) * curve(1.0 - local / skin, 0.10, 0.35)   # only inside the dark packing
        lighter = lift > dark * 0.5
        light = np.where(lighter, 1.0, 0.0)
        dark = np.where(lighter, lift, dark)
    alpha = dark * keep * ndi.gaussian_filter(body.astype(np.float32), 1.5)
    alpha[~body] = 0
    print(f'  {os.path.basename(path)}: skin L {skin:.0f}' + (f', light-ink share {float((alpha * light).sum() / max(alpha.sum(), 1)):.2f}' if light is not None else ''))
    ys, xs2 = np.where(alpha > 0.03)
    sl = (slice(max(ys.min() - 2, 0), ys.max() + 3), slice(max(xs2.min() - 2, 0), xs2.max() + 3))
    alpha = alpha[sl].copy()
    fy = np.clip((alpha.shape[0] - 1 - np.arange(alpha.shape[0])) / (0.06 * alpha.shape[0]), 0, 1)   # soft bottom edge:
    alpha *= (fy * fy * (3 - 2 * fy))[:, None]                     # the head zone ends at the neck base, no hard cut there
    return alpha, (light[sl] if light is not None else None)


def to_rgba(alpha, light=None):
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.float32)
    lt = np.zeros((h, w), np.float32) if light is None else light
    for c in range(3):
        out[..., c] = INK_RGB[c] * (1 - lt) + LIGHT_RGB[c] * lt
    out[..., 3] = alpha * 255
    return Image.fromarray((out + 0.5).clip(0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- layout into the tattoo texture
def edge_fade(alpha, side_frac=0.07, end_frac=0.02):
    """Soft fade at the sleeve's left / right edges (where the wrap meets the inner arm) and a short one at shoulder / wrist."""
    h, w = alpha.shape
    x = np.arange(w) / max(w - 1, 1); y = np.arange(h) / max(h - 1, 1)
    fx = np.clip(np.minimum(x, 1 - x) / side_frac, 0, 1); fy = np.clip(np.minimum(y, 1 - y) / end_frac, 0, 1)
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    return alpha * fy[:, None] * fx[None, :]


def layout(t, alpha, light=None):
    x0, y0, x1, y1 = t['box']
    bw, bh = (x1 - x0) * TEX, (y1 - y0) * TEX
    h, w = alpha.shape
    if t['fit'] == 'sleeve':          # arm length fills the reference sleeve's height, natural width, centred on the outer arm
        sh = bh; sw = w * bh / h
        alpha = edge_fade(alpha, side_frac=0.0001)                     # sides already faded by the unwrap
    else:                             # chest / back: the body outline fills the reference outline box
        sw, sh = bw, bh
    img = to_rgba(alpha, light).convert('RGBa').resize((max(1, round(sw)), max(1, round(sh))), Image.LANCZOS)
    canvas = Image.new('RGBa', (TEX, TEX), (0, 0, 0, 0))
    cx, cy = (x0 + x1) / 2 * TEX, (y0 + y1) / 2 * TEX
    canvas.paste(img, (round(cx - img.width / 2), round(cy - img.height / 2)))
    return canvas.convert('RGBA')


# ---------------------------------------------------------------- calibration grid (rig only)
def cal_texture(colour):
    img = Image.new('RGBA', (TEX, TEX), (255, 255, 255, 255)); d = ImageDraw.Draw(img)
    f = ImageFont.truetype('arialbd.ttf', 34)
    for i in range(10):
        for j in range(10):
            if (i + j) % 2:
                d.rectangle([i * TEX // 10, j * TEX // 10, (i + 1) * TEX // 10, (j + 1) * TEX // 10], fill=(225, 225, 225, 255))
    for k in range(21):
        p = k * TEX // 20; wdt = 5 if k % 2 == 0 else 1
        d.line([(p, 0), (p, TEX)], fill=(0, 0, 0, 255), width=wdt); d.line([(0, p), (TEX, p)], fill=(0, 0, 0, 255), width=wdt)
    for i in range(10):
        for j in range(10):
            d.text((i * TEX // 10 + 8, j * TEX // 10 + 30), f'{i}{j}', font=f, fill=colour)
    d.polygon([(TEX // 2, 4), (TEX // 2 - 40, 60), (TEX // 2 + 40, 60)], fill=(0, 160, 0, 255))   # green arrow = texture top
    d.rectangle([4, 4, 60, 60], fill=(255, 140, 0, 255))                                          # orange box = texture top-left
    return img


# ---------------------------------------------------------------- resource writers
def overlay_xml(entries):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<PedDecorationCollection>', '  <bRequiredForSync value="true" />', '  <presets>']
    for e in entries:
        out += ['    <Item>',
                f'      <uvPos x="{e["uv"][0]:.6f}" y="{e["uv"][1]:.6f}" />',
                f'      <scale x="{e["scale"][0]:.6f}" y="{e["scale"][1]:.6f}" />',
                f'      <rotation value="{e["rot"]:.6f}" />',
                f'      <nameHash>{e["name"]}</nameHash>', f'      <txdHash>{e["tex"]}</txdHash>', f'      <txtHash>{e["tex"]}</txtHash>',
                f'      <zone>{e["zone"]}</zone>', '      <type>TYPE_TATTOO</type>', '      <faction>FM</faction>', '      <garment>All</garment>',
                f'      <gender>{e["gender"]}</gender>', '      <award />', '      <awardLevel />', '    </Item>']
    out += ['  </presets>', f'  <nameHash>{COLLECTION if entries and not entries[0]["name"].startswith("c9cal") else "c9_tattoos_cal_overlays"}</nameHash>',
            '  <medalLocations />', '  <medalScale x="0.000000" y="0.000000" />', '</PedDecorationCollection>', '']
    return '\n'.join(out)


def shop_meta(entries, collection):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<TattooShopItemArray>', '  <TattooShopItems>']
    for e in entries:
        out += ['    <Item>', '      <id value="0" />', f'      <cost value="{e["price"]}" />', f'      <textLabel>{e["label_key"]}</textLabel>',
                f'      <collection>{collection}</collection>', f'      <preset>{e["name"]}</preset>', f'      <zone>{e["zone"]}</zone>',
                f'      <eFacing>{e["facing"]}</eFacing>', f'      <updateGroup>{e["group"]}</updateGroup>', '      <eFaction>TATTOO_MP_FM</eFaction>',
                '      <lockHash />', '    </Item>']
    out += ['  </TattooShopItems>', '</TattooShopItemArray>', '']
    return '\n'.join(out)


FXMANIFEST = """fx_version 'cerulean'
game 'gta5'
lua54 'yes'

author 'Cleveland RP'
description '{desc}'
version '1.0.0'

-- Add-on tattoos: one texture dictionary per tattoo in stream/, the overlay collection and the shop list as data files.
-- Must start before rcore_tattoos (server.cfg ensures it just above [rcore]).
files {{
    '{xml}',
    'shop_tattoo.meta',
}}

data_file 'PED_OVERLAY_FILE' '{xml}'
data_file 'TATTOO_SHOP_DLC_FILE' 'shop_tattoo.meta'
"""


def write_resource(res_dir, collection, entries, textures, desc):
    if os.path.isdir(res_dir):
        shutil.rmtree(res_dir)
    stream = os.path.join(res_dir, 'stream'); os.makedirs(stream)
    tmp = os.path.join(BUILD, '_dds_' + os.path.basename(res_dir))
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    for name, img in textures.items():
        write_dds(os.path.join(tmp, name + '.dds'), make_levels(img), 'DXT5')
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(HERE, 'tools', 'make_ytds.ps1'),
                        '-Dds', tmp, '-Out', stream], capture_output=True, text=True)
    print(r.stdout.strip()); assert r.returncode == 0, r.stderr
    shutil.rmtree(tmp)
    xml = collection + '.xml'
    open(os.path.join(res_dir, xml), 'w', encoding='utf-8', newline='\n').write(overlay_xml(entries))
    open(os.path.join(res_dir, 'shop_tattoo.meta'), 'w', encoding='utf-8', newline='\n').write(shop_meta(entries, collection))
    open(os.path.join(res_dir, 'fxmanifest.lua'), 'w', encoding='utf-8', newline='\n').write(FXMANIFEST.format(desc=desc, xml=xml))


def build_cal():
    zones = [('c9cal_torso', 'ZONE_TORSO', (0, 0, 0, 255)), ('c9cal_larm', 'ZONE_LEFT_ARM', (0, 0, 230, 255)),
             ('c9cal_rarm', 'ZONE_RIGHT_ARM', (220, 0, 0, 255)), ('c9cal_head', 'ZONE_HEAD', (0, 140, 0, 255))]
    entries, textures = [], {}
    for tex, zone, col in zones:
        textures[tex] = cal_texture(col)
        textures[tex].save(os.path.join(BUILD, tex + '.png'))
        for g, gs in (('M', 'GENDER_MALE'), ('F', 'GENDER_FEMALE')):
            entries.append(dict(name=f'{tex}_{g}', tex=tex, zone=zone, gender=gs, uv=(0.5, 0.5), scale=(1.0, 1.0), rot=0.0,
                                price=0, label_key=tex.upper(), facing='TATTOO_FRONT', group='TORSO_CAL'))
    # point markers at known overlay values: where each lands on the grid gives the uvPos -> body mapping per zone
    markers = [('A', 'ZONE_TORSO', 0.73, 0.38), ('B', 'ZONE_TORSO', 0.73, 0.48), ('C', 'ZONE_TORSO', 0.83, 0.38),
               ('D', 'ZONE_TORSO', 0.227, 0.46), ('E', 'ZONE_TORSO', 0.327, 0.46), ('H', 'ZONE_HEAD', 0.498, 0.25),
               ('K', 'ZONE_HEAD', 0.498, 0.35), ('N', 'ZONE_HEAD', 0.0, 0.45), ('P', 'ZONE_HEAD', 0.1, 0.45),
               ('R', 'ZONE_RIGHT_ARM', 0.51, 0.62), ('S', 'ZONE_RIGHT_ARM', 0.51, 0.72), ('T', 'ZONE_RIGHT_ARM', 0.61, 0.62),
               ('L', 'ZONE_LEFT_ARM', 0.47, 0.635), ('M', 'ZONE_LEFT_ARM', 0.47, 0.735), ('O', 'ZONE_LEFT_ARM', 0.57, 0.635)]
    f = ImageFont.truetype('arialbd.ttf', 300)
    for ch, zone, u, v in markers:
        tex = 'c9cal_mk_' + ch.lower(); img = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        d.ellipse([16, 16, 496, 496], outline=(200, 0, 200, 255), width=24); d.line([(256, 0), (256, 512)], fill=(200, 0, 200, 255), width=10)
        d.line([(0, 256), (512, 256)], fill=(200, 0, 200, 255), width=10); d.text((256, 140), ch, font=f, fill=(0, 120, 0, 255), anchor='mt')
        d.rectangle([0, 0, 90, 90], fill=(255, 120, 0, 255))      # texture top-left corner
        textures[tex] = img
        for g, gs in (('M', 'GENDER_MALE'), ('F', 'GENDER_FEMALE')):
            entries.append(dict(name=f'{tex}_{g}', tex=tex, zone=zone, gender=gs, uv=(u, v), scale=(0.1, 0.1), rot=0.0,
                                price=0, label_key=tex.upper(), facing='TATTOO_FRONT', group='TORSO_CAL'))
    write_resource(os.path.join(BUILD, 'c9_tattoos_cal'), 'c9_tattoos_cal_overlays', entries, textures, 'Rig-only UV calibration grid')


def build_pack():
    os.makedirs(ART, exist_ok=True)
    entries, textures, rcore = [], {}, []
    for t in TATTOOS:
        src = os.path.join(SRC, t['src'])
        if t['cut'] == 'paper':
            alpha, light = cut_paper(src)
        elif t['cut'] == 'skin':
            alpha, light = cut_skin(src)
        else:
            alpha, light = cut_photo(src, t['photo'])
        to_rgba(alpha, light).save(os.path.join(ART, t['key'] + '.png'))    # full-resolution transparent cut-out
        tex = layout(t, alpha, light); textures[t['key']] = tex
        tex.save(os.path.join(BUILD, t['key'] + '_texture.png'))
        for g, gs in (('M', 'GENDER_MALE'), ('F', 'GENDER_FEMALE')):
            v = t[g]
            entries.append(dict(name=f'{t["key"]}_{g}', tex=t['key'], zone=t['zone'], gender=gs, uv=v['uv'], scale=v['scale'],
                                rot=v['rot'], price=t['price'], label_key=t['key'].upper(), facing=t['facing'], group=t['group']))
        rcore.append(dict(collection=COLLECTION, hashFemale=f'{t["key"]}_F', hashMale=f'{t["key"]}_M', name=t['label'],
                          price=t['price'], zone=t['zone']))
    write_resource(os.path.join(BUILD, RES), COLLECTION, entries, textures, 'Cleveland RP custom tattoos (add-on, for rcore_tattoos)')
    json.dump(rcore, open(os.path.join(BUILD, 'C9Tattoos.json'), 'w', encoding='utf-8', newline='\n'), indent=2)
    preview_sheet()


def preview_sheet():
    """art/ preview: each tattoo texture over a light and a dark skin tone, the way the ink reads on a body."""
    keys = [t['key'] for t in TATTOOS]; tones = [(214, 176, 146), (92, 62, 44)]
    sheet = Image.new('RGB', (512 * len(keys), 512 * len(tones)))
    for i, k in enumerate(keys):
        tx = Image.open(os.path.join(BUILD, k + '_texture.png')).resize((512, 512), Image.LANCZOS)
        for j, tone in enumerate(tones):
            bg = Image.new('RGBA', (512, 512), tone + (255,)); bg.alpha_composite(tx)
            ImageDraw.Draw(bg).rectangle([0, 0, 511, 511], outline=(60, 60, 200))
            sheet.paste(bg.convert('RGB'), (512 * i, 512 * j))
    sheet.save(os.path.join(ART, 'textures_on_skin.png'))


def deploy():
    for root in (REPO_RES, LIVE_RES):
        dst = os.path.join(root, RES)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(BUILD, RES), dst)
        shutil.copy2(os.path.join(BUILD, 'C9Tattoos.json'), os.path.join(root, 'rcore_tattoos', 'assets', 'tattooLists', 'C9Tattoos.json'))
        print('deployed ->', dst)


if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if mode == 'cal':
        build_cal()
    else:
        build_pack()
        if mode == 'deploy':
            deploy()
