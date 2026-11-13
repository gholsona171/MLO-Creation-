"""Skeleton hand tattoo, laid onto the freemode hand by its real decoration UVs.

The arm zones' decoration space is the ped mesh's TexCoord1 (uppr_000_r): u = 1 + zone x, v = tile + (1 - zone y), tile -5 = right
arm, -7 = left arm. The hand is unwrapped flat at the bottom of the zone: the back of the hand above the knuckle line, each finger
a strip hanging down to its tip (y ~0.015), thumb beside the index; the palm side of the fingers is a small copy at the far side
(x > 0.8 right / < 0.2 left), which stays bare. hand_layout() reads every joint of that layout from the mesh (back-of-hand faces
only); the art is warped onto it with a thin-plate spline through matching joints in the source drawing.

Source: src/skeleton_hand.png, the back of a LEFT hand (thumb on the right). Left zone = art as drawn, right zone = art mirrored.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import RBFInterpolator

HERE = os.path.dirname(os.path.abspath(__file__))
MESH = {'M': os.path.join(HERE, 'ref', 'mesh', 'mp_m_freemode_01_uppr_000_r.ydd.xml.npz'),
        'F': os.path.join(HERE, 'ref', 'mesh', 'mp_f_freemode_01_uppr_000_r.ydd.xml.npz')}
# decal box in zone space: x 0.18..0.82, y 0..0.36  ->  uvPos (0.5, 0.18), scale (0.64, 0.36)
BOX = (0.18, 0.0, 0.82, 0.36)
TEX = 1024
# bone order per hand in the freemode skeleton (right hand; left hand = +29)
FINGERS = dict(thumb=(43, 44, 45), index=(48, 49, 50), middle=(52, 53, 54), ring=(55, 56, 57), pinky=(58, 59, 60))
HAND_BONE = 42
# joints in the source drawing (px, 1024 x 1536): metacarpal base, knuckle (MCP), middle joint, last joint, tip at the nail.
# thumb: CMC base, MCP, IP, -, tip.  Read off the drawing on a 50 px grid.
SRC_JOINTS = dict(
    pinky=[(450, 285), (240, 503), (105, 765), (60, 983), (45, 1133)],
    ring=[(540, 345), (345, 660), (255, 968), (195, 1245), (172, 1448)],
    middle=[(660, 375), (548, 735), (450, 1073), (405, 1320), (383, 1522)],
    index=[(750, 390), (735, 750), (702, 1088), (668, 1328), (645, 1492)],
    thumb=[(862, 375), (915, 660), (930, 908), None, (945, 1155)])
SRC_HALFW = [60, 58, 50, 42, 36]          # finger half-width in the drawing at each joint (bone + its packing)
SRC_WRIST = [(380, 200), (560, 190), (740, 200), (920, 225)]   # wrist line (top of the carpals), pinky side -> thumb side
SRC_W = 1024
GROW = 4                                  # px each drawn bone is grown by (bolder bones)
RING = 7                                  # px of solid black outline round every bone
FINGER_SPREAD = 1.5                       # finger art width / measured dorsal finger width
XCOV = 6.667                              # zone u covered per unit of overlay scale.x on the arm zones (measured)
SEAM = 3                                  # half-width of the dark seam kept between grown neighbours


def hand_layout(gender, side):
    """Joint positions of the hand in zone space (x, y), from the back-of-hand faces of the mesh."""
    d = np.load(MESH[gender])
    P, T, B, W, N = (d['g0_' + k] for k in ('Position', 'TexCoord1', 'BlendIndices', 'BlendWeights', 'Normal'))
    tile = -5 if side == 'right' else -7; off = 0 if side == 'right' else 29
    inz = np.floor(T[:, 1]).astype(int) == tile
    zx = T[:, 0] - 1; zy = 1 - (T[:, 1] - tile)
    bone = B.astype(int)[np.arange(len(B)), W.argmax(1)]
    hb = inz & (bone == HAND_BONE + off)
    up = N[hb & (N[:, 2] > 0.3)].mean(0); up /= np.linalg.norm(up)

    def dorsal(b):
        m = inz & (bone == b + off)
        p = P[m]; ax = np.linalg.svd(p - p.mean(0))[2][0]
        n = N[m] - np.outer(N[m] @ ax, ax); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        u = up - (up @ ax) * ax; u /= np.linalg.norm(u)
        k = (n @ u) > 0.5
        far = (zx[m] > 0.8) if side == 'right' else (zx[m] < 0.2)    # the palm-side copy is never the back
        k &= ~far
        return zx[m][k], zy[m][k]

    lay = {}
    for f, (b0, b1, b2) in FINGERS.items():
        x0, y0 = dorsal(b0); x1, y1 = dorsal(b1); x2, y2 = dorsal(b2)
        x = float(np.median(np.concatenate([x1, x2])))
        if f == 'thumb':     # CMC, MCP, IP, tip
            ys = [y0.max(), (y0.min() + y1.max()) / 2, (y1.min() + y2.max()) / 2, None, y2.min()]
            xs = [float(np.median(x0)), x, x, None, float(np.median(x2))]
        else:                # base (on the hand back), MCP, PIP, DIP, tip
            ys = [None, y0.max(), (y0.min() + y1.max()) / 2, (y1.min() + y2.max()) / 2, y2.min()]
            xs = [None, float(np.median(x0[y0 > np.percentile(y0, 60)])), x, x, float(np.median(x2))]
        lay[f] = [None if y is None else (xs[i], float(y)) for i, y in enumerate(ys)]
        # back-of-finger half width: the distal segment's dorsal faces near the strip centre (the thumb's wrap the whole way
        # round, so a plain spread would be meaningless); clamped to a sane band
        near = np.abs(x2 - np.median(x2)) < 0.06
        # x FINGER_SPREAD: what shows as the back of a finger in game is wider than the faces that point straight up (at 1x the
        # rig showed bare skin down both sides of every finger)
        lay[f + '_hw'] = float(np.clip(np.percentile(np.abs(x2[near] - np.median(x2)), 85) * FINGER_SPREAD, 0.024, 0.040))
    hx, hy = dorsal(HAND_BONE)
    lay['wrist_y'] = float(hy.max()); lay['back_x'] = (float(np.percentile(hx, 3)), float(np.percentile(hx, 97)))
    # where the back-of-hand + finger mesh actually is (decal texels elsewhere never show, or land on the palm)
    keep = inz & (zy < BOX[3]) & ((zx < 0.8) if side == 'right' else (zx > 0.2))
    tri = d['g0_tri']; tri = tri[keep[tri].all(1)]
    lay['tri'] = np.stack([zx[tri], zy[tri]], -1)
    return lay


def zone_to_px(x, y):
    return (np.asarray(x) - BOX[0]) / (BOX[2] - BOX[0]) * TEX, (BOX[3] - np.asarray(y)) / (BOX[3] - BOX[1]) * TEX


def control_points(lay, mirror):
    """(target px, source px) pairs: every joint, both sides of every finger, the wrist line, the metacarpal bases."""
    tgt, src = [], []
    sx = (lambda x: SRC_W - 1 - x) if mirror else (lambda x: x)

    def add(tx, ty, s):
        px, py = zone_to_px(tx, ty); tgt.append((float(px), float(py))); src.append((float(sx(s[0])), float(s[1])))

    wy = lay['wrist_y']; bx0, bx1 = lay['back_x']; cx = (bx0 + bx1) / 2
    tside = 1 if lay['thumb'][1][0] > cx else -1          # zone direction toward the thumb (+x left arm, -x right arm)
    for f in ('pinky', 'ring', 'middle', 'index', 'thumb'):
        J = list(lay[f]); S = SRC_JOINTS[f]; hw = lay[f + '_hw']
        if f == 'thumb':     # the drawn thumb base sits on the wrist line, level with the other metacarpal bases (the mesh's
            J[0] = (J[0][0], wy - 0.022)    # thumb-bone faces start lower; pinning the base there folds the art over itself)
        pts = [(i, J[i], S[i]) for i in range(5) if J[i] is not None and S[i] is not None]
        for k, (i, (tx, ty), s) in enumerate(pts):
            add(tx, ty, s)
            if i == 0:       # thumb base: no side points (the drawn thumb base is foreshortened; its sides crowd the index base
                continue     # and stretch the web between them ~2.5x)
            # sides: perpendicular to the finger in the drawing, sideways in the zone (fingers hang straight down there)
            j = pts[min(k + 1, len(pts) - 1)][2] if k + 1 < len(pts) else s
            jprev = pts[k - 1][2] if k > 0 else s
            dx, dy = (np.subtract(j, jprev) if k > 0 or k + 1 < len(pts) else (0, 1))
            n = np.array([dy, -dx], float); n /= np.linalg.norm(n) + 1e-9          # points to the drawing's +x side
            w = SRC_HALFW[i]
            for sgn in (-1, 1):
                ss = (s[0] + sgn * n[0] * w, s[1] + sgn * n[1] * w)
                # +n in the drawing points toward the thumb (left hand as drawn): in the zone that is `tside`
                add(tx + sgn * hw * tside, ty, ss)
    # metacarpal bases: under the wrist line, squeezed toward the middle of the hand back
    for f in ('pinky', 'ring', 'middle', 'index', 'thumb'):
        mx, my = lay[f][1]
        if f == 'thumb':     # base already placed above
            bx, by = lay[f][0][0], wy - 0.022
        else:
            bx, by = cx + (mx - cx) * 0.8, wy - 0.022
            add(bx, by, SRC_JOINTS[f][0])
        # mid-shaft sides keep each metacarpal its drawn width: where the mesh hand back is wider than the drawing (the
        # female index-thumb web) the stretch then goes into the dark packing, not into a fat bone
        s0, s1 = np.array(SRC_JOINTS[f][0], float), np.array(SRC_JOINTS[f][1], float); sm = (s0 + s1) / 2
        d = s1 - s0; n = np.array([d[1], -d[0]]) / (np.linalg.norm(d) + 1e-9)
        for sgn in (-1, 1):
            add((bx + mx) / 2 + sgn * lay[f + '_hw'] * tside, (by + my) / 2, sm + sgn * n * SRC_HALFW[1])
    # wrist line and the forearm bones above it
    order = (bx0, bx1) if (lay['thumb'][1][0] > cx) else (bx1, bx0)          # pinky side -> thumb side
    for k, s in enumerate(SRC_WRIST):
        tx = order[0] + (order[1] - order[0]) * k / (len(SRC_WRIST) - 1)
        add(tx, wy, s)
        add(tx, wy + 0.04, (s[0], s[1] - 150))
    return np.array(tgt), np.array(src)


def mask_from_tri(tris):
    from PIL import ImageDraw
    m = Image.new('L', (TEX, TEX), 0); dr = ImageDraw.Draw(m)
    for t in tris:
        if t[:, 0].max() - t[:, 0].min() > 0.4:
            continue
        px, py = zone_to_px(t[:, 0], t[:, 1])
        dr.polygon(list(zip(px.tolist(), py.tolist())), fill=255)
    m = np.asarray(m) > 0
    return ndi.binary_dilation(m, iterations=6)                      # bleed past the mesh edge: no hard rim on the skin


def ink(path):
    """Ink from the photo-style render: bones = the lightest parts, the dark packing between them = ink, nails / bare pink skin
    and the black surround = nothing."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    L = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    body = ndi.gaussian_filter(L, 3) > 9
    lab, n = ndi.label(body); body = lab == (1 + int(np.argmax(ndi.sum(body, lab, range(1, n + 1)))))
    body = ndi.binary_erosion(ndi.binary_fill_holes(body), iterations=4)
    ref = np.percentile(L[body], 99)
    dark = np.clip(1 - L / ref, 0, 1)                                 # 0 = brightest bone, 1 = black
    red = (a[..., 0] - a[..., 2]) / np.maximum(L, 8)
    base = np.percentile(red[body], 50)
    # nails and bare finger skin: noticeably pinker than the bone-and-ink, and not dark
    nail = ndi.gaussian_filter(((red > base + 0.10) & (dark < 0.75) & body).astype(np.float32), 4) > 0.5
    nail = ndi.binary_opening(nail, iterations=3); nail = ndi.binary_dilation(nail, iterations=3)
    # Bold re-cut of the same bones for game viewing distance: a clean light bone (a hint of its own shading kept), a thick
    # solid-black outline round every bone, near-solid dark packing between bones, and a dark seam wherever two neighbouring
    # bones meet (the joints) so each bone stays its own piece.
    # A bone is light in absolute terms AND lighter than its surroundings (local mean over ~30 px): this keeps each bone one
    # continuous shape instead of the broken pieces a plain threshold gives on the shaded bones.
    Ls = ndi.gaussian_filter(L, 3)
    bone = (Ls > 60) & (Ls > 1.1 * ndi.gaussian_filter(L, 30))
    bone = ndi.binary_closing(ndi.binary_opening(bone, iterations=3), iterations=3) & body & ~nail
    lab, n = ndi.label(bone)
    if n:
        sz = ndi.sum(bone, lab, range(1, n + 1)); keep = 1 + np.where(sz >= 600)[0]
        lab = np.where(np.isin(lab, keep), lab, 0)
    dist, (iy, ix) = ndi.distance_transform_edt(lab == 0, return_indices=True)
    own = lab[iy, ix]                                                 # nearest bone of every pixel
    fat = (dist <= GROW) & body & ~nail
    seam = np.zeros_like(fat)
    for ax in (0, 1):                                                 # where two different grown bones touch
        d = np.diff(own, axis=ax) != 0
        sl = [slice(None)] * 2; sl[ax] = slice(0, -1); seam[tuple(sl)] |= d
        sl[ax] = slice(1, None); seam[tuple(sl)] |= d
    seam = ndi.binary_dilation(seam & fat, iterations=SEAM)
    fat &= ~seam
    ring = (dist <= GROW + RING) & ~fat
    shade = np.clip((dark - 0.05) / 0.6, 0, 1)
    alpha = np.full(dark.shape, 0.86, np.float32)                    # packing: dark
    alpha = np.where(ring | seam, 1.0, alpha)                         # outline and joint seams: solid black
    alpha = np.where(fat, 0.04 + 0.30 * shade, alpha)                # bone: clean light fill with a hint of its shading
    alpha = ndi.gaussian_filter(alpha, 1.2)
    alpha *= 1 - np.clip(ndi.gaussian_filter(nail.astype(np.float32), 3) * 1.4, 0, 1)
    alpha *= np.clip(ndi.gaussian_filter(body.astype(np.float32), 4) * 2 - 1, 0, 1)
    alpha[~body] = 0
    return alpha


def build(path, gender, side):
    """-> (RGBA texture, uvPos, scale) for one gender / side."""
    lay = hand_layout(gender, side)
    tgt, src = control_points(lay, mirror=(side == 'right'))
    alpha = ink(path)
    if side == 'right':
        alpha = alpha[:, ::-1]
    f = RBFInterpolator(tgt, src, kernel='thin_plate_spline', smoothing=2.0)
    yy, xx = np.mgrid[0:TEX:2, 0:TEX:2].astype(np.float64)
    s = f(np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1)).reshape(TEX // 2, TEX // 2, 2)
    s = np.stack([ndi.zoom(s[..., k], 2, order=1) for k in range(2)], -1)
    out = ndi.map_coordinates(alpha, [s[..., 1], s[..., 0]], order=1, mode='constant')
    yzone = BOX[3] - (np.arange(TEX) + 0.5) / TEX * (BOX[3] - BOX[1])
    top = np.clip((lay['wrist_y'] + 0.05 - yzone) / 0.045, 0, 1)[:, None] ** 1.5   # long soft fade above the wrist: no cuff line
    out = out * top * mask_from_tri(lay['tri'])
    rgba = np.zeros((TEX, TEX, 4), np.uint8); rgba[..., :3] = (20, 20, 22); rgba[..., 3] = (out * 255 + 0.5).astype(np.uint8)
    # Placement on the arm zones, measured on the rig with colour-coded line probes (photos/iter/probe*):
    #   v: the decoration covers 2 x scale.y of TexCoord1 v, not flipped (rows at v .05 ... .30 land on the finger joints / wrist);
    #   u: it covers XCOV x scale.x of TexCoord1 u and runs mirrored (texture left = higher u), wrapping every 1.0.
    uv = ((BOX[0] + BOX[2]) / 2, (BOX[1] + BOX[3]) / 2)
    scale = ((BOX[2] - BOX[0]) / XCOV, (BOX[3] - BOX[1]) / 2)
    rgba = rgba[:, ::-1].copy()
    return Image.fromarray(rgba, 'RGBA'), uv, scale, lay, (tgt, src)


def ink_preview(path, out, mirror=False):
    """art/ cut-out of the bold ink (before the warp), for viewing."""
    a = ink(path)
    if mirror:
        a = a[:, ::-1]
    rgba = np.zeros(a.shape + (4,), np.uint8); rgba[..., :3] = (20, 20, 22); rgba[..., 3] = (a * 255 + 0.5).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(out)
