#!/usr/bin/env python3
"""
c9_dj 1.9.x: Rockstar drawables as data (the counter kit, prop/build/counters.py). Reads a CodeWalker ydr XML exported from the game
(MLO-Creation tools/ydr_xml.ps1 -Mode export), keeps Rockstar's shaders, vertex layouts and texture names exactly, and lets the build
cut it with planes (every vertex attribute interpolated on the cut), turn / move / mirror it, put pieces of it together and write it
back as a ydr XML with our own box collision. No Blender. MIT, our own code (the geometry it reads is the game's, never stored here).
"""
import re
import numpy as np

# values per layout component
WIDTH = {'Position': 3, 'Normal': 3, 'Tangent': 4, 'BlendWeights': 4, 'BlendIndices': 4, 'Colour0': 4, 'Colour1': 4}
for _i in range(8): WIDTH['TexCoord%d' % _i] = 2
INTS = {'Colour0', 'Colour1', 'BlendIndices', 'BlendWeights'}


class Geo:
    """one geometry: a shader index, a layout (ordered component names) and per-component arrays (n x width), triangles (m x 3)"""
    def __init__(self, shader, comps, data, tris):
        self.shader, self.comps, self.data, self.tris = shader, comps, data, tris

    def copy(self):
        return Geo(self.shader, list(self.comps), {k: v.copy() for k, v in self.data.items()}, self.tris.copy())

    @property
    def pos(self): return self.data['Position']


class Model:
    """a drawable: its Rockstar shader list (the XML text of <Shaders>), its texture names, its geometries"""
    def __init__(self, name, shaders_xml, geos, textures):
        self.name, self.shaders_xml, self.geos, self.textures = name, shaders_xml, geos, textures

    def copy(self):
        return Model(self.name, self.shaders_xml, [g.copy() for g in self.geos], dict(self.textures))

    def bounds(self):
        P = np.vstack([g.pos for g in self.geos if len(g.tris)])
        return P.min(0), P.max(0)

    def tri_count(self): return sum(len(g.tris) for g in self.geos)


def read(path, name=None):
    t = open(path, encoding='utf-8').read()
    sh = re.search(r'<Shaders>(.*?)\n  </Shaders>', t, re.S).group(1)
    # every texture a shader samples (embedded or not): the build finds them all for the style's own ytd
    tex = {}
    for m in re.finditer(r'<Item name="(\w+)" type="Texture">\s*<Name>([^<]+)</Name>', sh):
        tex[m.group(2).lower()] = m.group(1)
    geos = []
    for m in re.finditer(r'<ShaderIndex value="(\d+)" />.*?<Layout type="\w+">(.*?)</Layout>\s*<Data>(.*?)</Data>.*?<IndexBuffer>\s*<Data>(.*?)</Data>', t, re.S):
        shader, lay, data, idx = m.groups()
        comps = re.findall(r'<(\w+) />', lay)
        rows = [l.strip().split('   ') for l in data.strip().split('\n')]
        arr = {}
        for k, c in enumerate(comps):
            arr[c] = np.array([[float(x) for x in r[k].split()] for r in rows], dtype=float)
        tris = np.array([int(x) for x in idx.split()], dtype=np.int64).reshape(-1, 3)
        geos.append(Geo(int(shader), comps, arr, tris))
    return Model(name or re.search(r'<Name>([^<.]+)', t).group(1), sh, geos, tex)


# ── transforms ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def rot_z(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def transform(m, R=None, t=(0, 0, 0)):
    """p' = R p + t (R a rotation, or a reflection: then triangles are re-wound and tangent handedness flipped)"""
    R = np.eye(3) if R is None else np.asarray(R, float)
    det = np.linalg.det(R)
    out = m.copy()
    for g in out.geos:
        g.data['Position'] = g.data['Position'] @ R.T + np.asarray(t, float)
        if 'Normal' in g.data:
            g.data['Normal'] = g.data['Normal'] @ R.T
        if 'Tangent' in g.data:
            T = g.data['Tangent']
            T[:, :3] = T[:, :3] @ R.T
            if det < 0: T[:, 3] = -T[:, 3]
        if det < 0:
            g.tris = g.tris[:, [0, 2, 1]]
    return out


def mirror_x(m, x0=0.0):
    """reflect across the plane x = x0"""
    return transform(m, np.diag([-1.0, 1.0, 1.0]), (2 * x0, 0, 0))


# ── cutting ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _lerp(g, i, j, t):
    v = {}
    for c, a in g.data.items():
        x = a[i] + (a[j] - a[i]) * t
        v[c] = x
    if 'Normal' in v:
        n = np.linalg.norm(v['Normal'])
        if n > 1e-9: v['Normal'] = v['Normal'] / n
    if 'Tangent' in v:
        n = np.linalg.norm(v['Tangent'][:3])
        if n > 1e-9: v['Tangent'][:3] = v['Tangent'][:3] / n
        v['Tangent'][3] = g.data['Tangent'][i][3]
    for c in INTS:
        if c in v: v[c] = np.round(v[c])
    return v


def clip(m, n, d, eps=1e-6):
    """keeps what lies where dot(n, p) <= d; triangles across the plane are cut (new vertices interpolate every attribute)"""
    n = np.asarray(n, float)
    out = m.copy()
    for g in out.geos:
        P = g.data['Position']
        s = P @ n - d
        keep = []
        new = {c: [] for c in g.data}
        base = len(P)
        cache = {}

        def cut(i, j):
            key = (min(i, j), max(i, j))
            if key in cache: return cache[key]
            t = s[i] / (s[i] - s[j])
            v = _lerp(g, i, j, t)
            for c in g.data: new[c].append(v[c])
            k = base + len(new['Position']) - 1
            cache[key] = k
            return k

        for tri in g.tris:
            inside = [s[k] <= eps for k in tri]
            ni = sum(inside)
            if ni == 3: keep.append(tuple(tri)); continue
            if ni == 0: continue
            # walk the triangle in order: Sutherland-Hodgman on one plane keeps the winding
            poly = []
            for k in range(3):
                a, b = tri[k], tri[(k + 1) % 3]
                ia, ib = s[a] <= eps, s[b] <= eps
                if ia: poly.append(a)
                if ia != ib: poly.append(cut(a, b))
            for k in range(1, len(poly) - 1):
                keep.append((poly[0], poly[k], poly[k + 1]))
        if new['Position']:
            for c in g.data: g.data[c] = np.vstack([g.data[c], np.array(new[c])])
        g.tris = np.array(keep, dtype=np.int64).reshape(-1, 3)
        _compact(g)
    out.geos = [g for g in out.geos if len(g.tris)]
    return out


def box_clip(m, lo, hi):
    """keeps what is inside the axis box lo..hi (None = no limit on that side)"""
    for ax in range(3):
        if lo[ax] is not None:
            e = np.zeros(3); e[ax] = -1; m = clip(m, e, -lo[ax])
        if hi[ax] is not None:
            e = np.zeros(3); e[ax] = 1; m = clip(m, e, hi[ax])
    return m


def _compact(g):
    used = np.unique(g.tris)
    remap = -np.ones(len(g.data['Position']), dtype=np.int64)
    remap[used] = np.arange(len(used))
    for c in g.data: g.data[c] = g.data[c][used]
    g.tris = remap[g.tris]


def merge(parts, name):
    """pieces of ONE source model (same shader list) into one model; geometries of the same shader are joined"""
    first = parts[0]
    if first.shaders_xml == 'boxes':          # collision box meshes (counters.box_mesh): every piece of every box stays its own box
        return Model(name, 'boxes', [g.copy() for p in parts for g in p.geos], {})
    by = {}
    for p in parts:
        assert p.shaders_xml == first.shaders_xml, 'merge: pieces of different models'
        for g in p.geos:
            key = (g.shader, tuple(g.comps))
            if key not in by: by[key] = g.copy(); continue
            h = by[key]
            off = len(h.pos)
            for c in h.data: h.data[c] = np.vstack([h.data[c], g.data[c]])
            h.tris = np.vstack([h.tris, g.tris + off])
    return Model(name, first.shaders_xml, list(by.values()), dict(first.textures))


# ── writing ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def fnum(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def _row(g, i):
    parts = []
    for c in g.comps:
        a = g.data[c][i]
        parts.append(' '.join(str(int(x)) for x in a) if c in INTS else ' '.join(fnum(x) for x in a))
    return '       ' + '   '.join(parts)


def geometry_xml(g):
    mn, mx = g.pos.min(0), g.pos.max(0)
    rows = '\n'.join(_row(g, i) for i in range(len(g.pos)))
    ids = g.tris.reshape(-1)
    ib = '\n'.join('       ' + ' '.join(str(x) for x in ids[k:k + 24]) for k in range(0, len(ids), 24))
    lay = ''.join('       <%s />\n' % c for c in g.comps)
    return ('    <Item>\n     <ShaderIndex value="%d" />\n     <BoundingBoxMin x="%s" y="%s" z="%s" w="0" />\n'
            '     <BoundingBoxMax x="%s" y="%s" z="%s" w="0" />\n     <VertexBuffer>\n      <Flags value="0" />\n'
            '      <Layout type="GTAV1">\n%s      </Layout>\n      <Data>\n%s\n      </Data>\n     </VertexBuffer>\n'
            '     <IndexBuffer>\n      <Data>\n%s\n      </Data>\n     </IndexBuffer>\n    </Item>\n') % (
        g.shader, fnum(mn[0]), fnum(mn[1]), fnum(mn[2]), fnum(mx[0]), fnum(mx[1]), fnum(mx[2]), lay, rows, ib)


def _box_child(lo, hi, mat):
    c = (np.asarray(lo) + np.asarray(hi)) / 2
    h = (np.asarray(hi) - np.asarray(lo)) / 2
    r = float(np.linalg.norm(h))
    vol = float(8 * h[0] * h[1] * h[2])
    return ('   <Item type="Box">\n    <BoxMin x="%s" y="%s" z="%s" />\n    <BoxMax x="%s" y="%s" z="%s" />\n'
            '    <BoxCenter x="0" y="0" z="0" />\n    <SphereCenter x="0" y="0" z="0" />\n    <SphereRadius value="%s" />\n'
            '    <Margin value="0.005" />\n    <Volume value="%s" />\n    <Inertia x="1" y="1" z="1" />\n'
            '    <MaterialIndex value="%d" />\n    <MaterialColourIndex value="0" />\n    <ProceduralID value="0" />\n'
            '    <RoomID value="0" />\n    <PedDensity value="0" />\n    <UnkFlags value="0" />\n    <PolyFlags value="0" />\n'
            '    <UnkType value="1" />\n    <CompositeTransform>\n     1 0 0 0\n     0 1 0 0\n     0 0 1 0\n     %s %s %s 1\n'
            '    </CompositeTransform>\n    <CompositeFlags1>MAP_WEAPON, MAP_DYNAMIC, MAP_ANIMAL, MAP_COVER, MAP_VEHICLE</CompositeFlags1>\n'
            '    <CompositeFlags2>VEHICLE_NOT_BVH, VEHICLE_BVH, PED, RAGDOLL, ANIMAL, ANIMAL_RAGDOLL, OBJECT, PLANT, PROJECTILE, EXPLOSION, '
            'FORKLIFT_FORKS, TEST_WEAPON, TEST_CAMERA, TEST_AI, TEST_SCRIPT, TEST_VEHICLE_WHEEL, GLASS</CompositeFlags2>\n   </Item>\n') % (
        fnum(-h[0]), fnum(-h[1]), fnum(-h[2]), fnum(h[0]), fnum(h[1]), fnum(h[2]), fnum(r), fnum(max(vol, 1e-6)), mat,
        fnum(c[0]), fnum(c[1]), fnum(c[2]))


def bounds_xml(boxes, mat):
    """boxes = [(lo, hi), ...] in the model's frame: a Composite of Box children (solid to peds, cars, objects, cameras)"""
    lo = np.min([b[0] for b in boxes], axis=0)
    hi = np.max([b[1] for b in boxes], axis=0)
    c = (lo + hi) / 2
    r = float(np.linalg.norm(hi - c))
    return ((' <Bounds type="Composite">\n  <BoxMin x="%s" y="%s" z="%s" />\n  <BoxMax x="%s" y="%s" z="%s" />\n'
             '  <BoxCenter x="%s" y="%s" z="%s" />\n  <SphereCenter x="%s" y="%s" z="%s" />\n  <SphereRadius value="%s" />\n'
             '  <Margin value="0" />\n  <Volume value="1" />\n  <Inertia x="1" y="1" z="1" />\n  <MaterialIndex value="0" />\n'
             '  <MaterialColourIndex value="0" />\n  <ProceduralID value="0" />\n  <RoomID value="0" />\n  <PedDensity value="0" />\n'
             '  <UnkFlags value="0" />\n  <PolyFlags value="0" />\n  <UnkType value="1" />\n  <Children>\n') % (
        fnum(lo[0]), fnum(lo[1]), fnum(lo[2]), fnum(hi[0]), fnum(hi[1]), fnum(hi[2]), fnum(c[0]), fnum(c[1]), fnum(c[2]),
        fnum(c[0]), fnum(c[1]), fnum(c[2]), fnum(r))
        + ''.join(_box_child(b[0], b[1], mat) for b in boxes) + '  </Children>\n </Bounds>\n'), lo, hi


def ydr_xml(m, boxes, mat=0, lod=100, bounds=None):
    """the drawable: Rockstar's shaders (their textures come from the archetype's texture dictionary: no embedded ones), our boxes
    (or `bounds`: a ready <Bounds> block, Rockstar's own collision moved with the copy)"""
    mn, mx = m.bounds()
    if bounds:
        bxml, blo, bhi = bounds, mn, mx
    else:
        bxml, blo, bhi = bounds_xml(boxes, mat)
    mn, mx = np.minimum(mn, blo), np.maximum(mx, bhi)
    c = (mn + mx) / 2
    r = float(np.linalg.norm(mx - c))
    geos = ''.join(geometry_xml(g) for g in m.geos)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<Drawable>\n <Name>%s</Name>\n'
            ' <BoundingSphereCenter x="%s" y="%s" z="%s" />\n <BoundingSphereRadius value="%s" />\n'
            ' <BoundingBoxMin x="%s" y="%s" z="%s" />\n <BoundingBoxMax x="%s" y="%s" z="%s" />\n'
            ' <LodDistHigh value="%d" />\n <LodDistMed value="9998" />\n <LodDistLow value="9998" />\n <LodDistVlow value="9998" />\n'
            ' <FlagsHigh value="1" />\n <FlagsMed value="0" />\n <FlagsLow value="0" />\n <FlagsVlow value="0" />\n'
            ' <ShaderGroup>\n  <Shaders>%s\n  </Shaders>\n </ShaderGroup>\n <DrawableModelsHigh>\n  <Item>\n'
            '   <RenderMask value="255" />\n   <Flags value="0" />\n   <HasSkin value="0" />\n   <BoneIndex value="0" />\n'
            '   <Unknown1 value="0" />\n   <Geometries>\n%s   </Geometries>\n  </Item>\n </DrawableModelsHigh>\n%s <Lights />\n</Drawable>\n') % (
        m.name, fnum(c[0]), fnum(c[1]), fnum(c[2]), fnum(r), fnum(mn[0]), fnum(mn[1]), fnum(mn[2]), fnum(mx[0]), fnum(mx[1]), fnum(mx[2]),
        lod, m.shaders_xml, geos, bxml), (mn, mx)


# ── checks ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def section(m, axis, value, tol=0.0015):
    """the outline of a model ON a plane (axis = 0 / 1 / 2, at value) as segments (k x 2 x 3): where each triangle crosses or
    touches it. Two modules join seamlessly when their outlines on the shared joint plane are the same."""
    out = []
    for g in m.geos:
        P = g.pos
        s = P[:, axis] - value
        for tri in g.tris:
            on = [abs(s[k]) <= tol for k in tri]
            if all(on):
                for k in range(3): out.append((P[tri[k]], P[tri[(k + 1) % 3]]))
                continue
            pts = [P[tri[k]] for k in range(3) if on[k]]
            for k in range(3):
                a, b = tri[k], tri[(k + 1) % 3]
                if (s[a] < -tol and s[b] > tol) or (s[a] > tol and s[b] < -tol):
                    t = s[a] / (s[a] - s[b]); pts.append(P[a] + (P[b] - P[a]) * t)
            if len(pts) >= 2: out.append((pts[0], pts[1]))
    return np.array(out, float).reshape(-1, 2, 3)


def section_points(seg):
    return seg.reshape(-1, 3)


def section_gap(A, B, axis, samples=4, skip=None):
    """the worst distance (in the plane) from any point along outline A to outline B, both ways: 0 = the same outline.
    skip = (coordinate index, value, band): points that close to that line are not judged (where a corner's mitre meets the face)"""
    if not len(A) or not len(B): return float('inf') if (len(A) or len(B)) else 0.0
    o = [i for i in range(3) if i != axis]
    def pts(S):
        t = np.linspace(0, 1, samples + 1)[:, None, None]
        P = (S[None, :, 0, :] + (S[None, :, 1, :] - S[None, :, 0, :]) * t).reshape(-1, 3)
        if skip: P = P[np.abs(P[:, skip[0]] - skip[1]) > skip[2]]
        return P[:, o]
    def dist(p, S):
        a, b = S[:, 0, o], S[:, 1, o]
        ab = b - a
        L2 = np.maximum((ab ** 2).sum(1), 1e-12)
        worst = 0.0
        for k in range(0, len(p), 256):
            q = p[k:k + 256][:, None, :]
            t = np.clip(((q - a[None]) * ab[None]).sum(2) / L2[None], 0, 1)
            d = np.linalg.norm(q - (a[None] + t[..., None] * ab[None]), axis=2).min(1)
            worst = max(worst, float(d.max()))
        return worst
    return max(dist(pts(A), B), dist(pts(B), A))


def rockstar_bounds(path, dz):
    """the source drawable's own collision (its <Bounds> block), moved up by dz: every centre / box z and every vertex"""
    t = open(path, encoding='utf-8').read()
    m = re.search(r' <Bounds type=.*?\n </Bounds>\n', t, re.S)
    if not m: return None
    b = m.group(0)
    b = re.sub(r'(<(?:BoxMin|BoxMax|BoxCenter|SphereCenter|GeometryCenter) x="[^"]*" y="[^"]*" z=")([^"]*)(")',
               lambda k: k.group(1) + fnum(float(k.group(2)) + dz) + k.group(3), b)

    def verts(k):
        rows = []
        for line in k.group(2).strip('\n').split('\n'):
            x, y, z = [float(v) for v in line.split(',')]
            rows.append('     %s, %s, %s' % (fnum(x), fnum(y), fnum(z + dz)))
        return k.group(1) + '\n'.join(rows) + '\n' + k.group(3)
    b = re.sub(r'(<Vertices>\n)(.*?)(\s*</Vertices>)', verts, b, flags=re.S)
    return b
