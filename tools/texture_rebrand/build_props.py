"""Our own CPD props replacing Ibonoja's locked (FXAP) ones: same archetype bounds / pivot as the originals (read from the readable
ytyp), embedded textures, CodeWalker XML written here and imported by cw_import.ps1.
usage: build_props.py <work dir>   -> <work>/xml/<name>.ydr.xml (+ <name>/ textures) and <work>/png/ previews"""
import os, sys, math
import numpy as np
from PIL import Image
sys.path.insert(0, r'C:\C9Test\rebuild\install\cpd_station\build')
from dds_mips import make_levels, write_dds
import props_art as A

WORK = sys.argv[1]
XML = os.path.join(WORK, 'xml'); PNG = os.path.join(WORK, 'png')
os.makedirs(XML, exist_ok=True); os.makedirs(PNG, exist_ok=True)


def fnum(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class Mesh:
    def __init__(self): self.v, self.t = [], []

    def quad(self, p0, p1, p2, p3, n, uv=((0, 1), (1, 1), (1, 0), (0, 0))):
        """p0..p3 counter-clockwise seen from the front (bottom-left, bottom-right, top-right, top-left); uv v=0 at the top"""
        b = len(self.v)
        for p, t in zip((p0, p1, p2, p3), uv):
            self.v.append((p, n, t))
        self.t += [(b, b + 1, b + 2), (b, b + 2, b + 3)]

    def bounds(self):
        P = np.array([v[0] for v in self.v]); return P.min(0), P.max(0)


def plane_x(m, y0, y1, z0, z1, x, sign):
    """art plane perpendicular to X, readable from the side it faces (sign = +1 faces +X, -1 faces -X)"""
    if sign > 0:   # viewer at +X: right = +Y
        m.quad((x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1), (1, 0, 0))
    else:          # viewer at -X: right = -Y
        m.quad((x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1), (-1, 0, 0))


def plane_y(m, x0, x1, z0, z1, y, sign, uv=None):
    """perpendicular to Y; sign = -1 faces -Y (viewer at -Y: right = +X), +1 faces +Y (right = -X)"""
    uv = uv or ((0, 1), (1, 1), (1, 0), (0, 0))
    if sign < 0:
        m.quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1), (0, -1, 0), uv)
    else:
        m.quad((x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1), (0, 1, 0), uv)


def box_sides(m, x0, x1, y0, y1, z0, z1, uvs=((0, 1), (1, 1), (1, 0), (0, 0))):
    """the four edges and the back of a slab (front made separately)"""
    m.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0), uvs)
    m.quad((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (-1, 0, 0), uvs)
    m.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1), uvs)
    m.quad((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), (0, 0, -1), uvs)
    plane_y(m, x0, x1, z0, z1, y1, +1, uvs)


def disc_prism(m_cap, m_side, cx, cz, r, y0, y1, n=40):
    """raised round medallion: front cap at y0 (faces -Y, uv = the circle in its square texture), side ring y0..y1"""
    c = len(m_cap.v); m_cap.v.append(((cx, y0, cz), (0, -1, 0), (.5, .5)))
    for i in range(n):
        a = 2 * math.pi * i / n
        m_cap.v.append(((cx + r * math.cos(a), y0, cz + r * math.sin(a)), (0, -1, 0), (.5 + .5 * math.cos(a), .5 - .5 * math.sin(a))))
    for i in range(n):
        a, b = c + 1 + i, c + 1 + (i + 1) % n
        m_cap.t.append((c, b, a))           # seen from -Y the ring runs clockwise in x/z, so wind back for CCW
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p = lambda a, y: (cx + r * math.cos(a), y, cz + r * math.sin(a))
        nn = (math.cos((a0 + a1) / 2), 0, math.sin((a0 + a1) / 2))
        m_side.quad(p(a0, y0), p(a1, y0), p(a1, y1), p(a0, y1), nn, ((0, 0), (1, 0), (1, 1), (0, 1)))


def fix_winding(m):
    """make every triangle counter-clockwise about its own vertex normal (Rockstar's convention, checked on prop_flagpole_1a)"""
    P = np.array([v[0] for v in m.v], float); N = np.array([v[1] for v in m.v], float)
    out = []
    for a, b, c in m.t:
        g = np.cross(P[b] - P[a], P[c] - P[a])
        out.append((a, b, c) if g @ (N[a] + N[b] + N[c]) >= 0 else (a, c, b))
    m.t = out


TEX_XML = ('   <Item>\n    <Name>{n}</Name>\n    <Unk32 value="128" />\n    <Usage>DIFFUSE</Usage>\n    <UsageFlags>UNK24</UsageFlags>\n'
           '    <ExtraFlags value="0" />\n    <Width value="{w}" />\n    <Height value="{h}" />\n    <MipLevels value="{l}" />\n'
           '    <Format>D3DFMT_{f}</Format>\n    <FileName>{n}.dds</FileName>\n   </Item>\n')
SHADER_XML = ('   <Item>\n    <Name>default</Name>\n    <FileName>default.sps</FileName>\n    <RenderBucket value="0" />\n    <Parameters>\n'
              '     <Item name="DiffuseSampler" type="Texture">\n      <Name>{n}</Name>\n     </Item>\n'
              '     <Item name="matMaterialColorScale" type="Vector" x="1" y="0" z="0" w="1" />\n'
              '     <Item name="HardAlphaBlend" type="Vector" x="1" y="0" z="0" w="0" />\n'
              '     <Item name="useTessellation" type="Vector" x="0" y="0" z="0" w="0" />\n'
              '     <Item name="wetnessMultiplier" type="Vector" x="0.055" y="0" z="0" w="0" />\n'
              '     <Item name="globalAnimUV1" type="Vector" x="0" y="1" z="0" w="0" />\n'
              '     <Item name="globalAnimUV0" type="Vector" x="1" y="0" z="0" w="0" />\n    </Parameters>\n   </Item>\n')


def write_ydr(name, parts, lod=40):
    """parts = [(mesh, texture_name, PIL image, (tw, th), 'DXT1'|'DXT5')]; one shader + geometry per part, textures embedded"""
    tdir = os.path.join(XML, name); os.makedirs(tdir, exist_ok=True)
    texs, shaders, geos, seen = '', '', '', {}
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for si, (m, tn, img, size, fmt) in enumerate(parts):
        fix_winding(m)
        if tn not in seen:
            im = img.resize(size, Image.LANCZOS)
            im.save(os.path.join(PNG, tn + '.png'))
            lv = make_levels(im if fmt == 'DXT5' else im.convert('RGB').convert('RGBA'))
            write_dds(os.path.join(tdir, tn + '.dds'), lv, fmt)
            texs += TEX_XML.format(n=tn, w=size[0], h=size[1], l=len(lv), f=fmt); seen[tn] = 1
        shaders += SHADER_XML.format(n=tn)
        mn, mx = m.bounds(); lo, hi = np.minimum(lo, mn), np.maximum(hi, mx)
        rows = '\n'.join('       %s %s %s   %s %s %s   255 255 255 255   %s %s' % (*map(fnum, p), *map(fnum, n), fnum(t[0]), fnum(t[1])) for p, n, t in m.v)
        ids = [i for tri in m.t for i in tri]
        ib = '\n'.join('       ' + ' '.join(str(x) for x in ids[k:k + 24]) for k in range(0, len(ids), 24))
        geos += ('    <Item>\n     <ShaderIndex value="%d" />\n     <BoundingBoxMin x="%s" y="%s" z="%s" w="0" />\n'
                 '     <BoundingBoxMax x="%s" y="%s" z="%s" w="0" />\n     <VertexBuffer>\n      <Flags value="0" />\n'
                 '      <Layout type="GTAV1">\n       <Position />\n       <Normal />\n       <Colour0 />\n       <TexCoord0 />\n      </Layout>\n'
                 '      <Data>\n%s\n      </Data>\n     </VertexBuffer>\n     <IndexBuffer>\n      <Data>\n%s\n      </Data>\n     </IndexBuffer>\n    </Item>\n'
                 ) % (si, *map(fnum, mn), *map(fnum, mx), rows, ib)
    c = (lo + hi) / 2; r = float(np.linalg.norm(hi - c))
    x = ('<?xml version="1.0" encoding="UTF-8"?>\n<Drawable>\n <Name>%s</Name>\n <BoundingSphereCenter x="%s" y="%s" z="%s" />\n'
         ' <BoundingSphereRadius value="%s" />\n <BoundingBoxMin x="%s" y="%s" z="%s" />\n <BoundingBoxMax x="%s" y="%s" z="%s" />\n'
         ' <LodDistHigh value="%d" />\n <LodDistMed value="9998" />\n <LodDistLow value="9998" />\n <LodDistVlow value="9998" />\n'
         ' <FlagsHigh value="1" />\n <FlagsMed value="0" />\n <FlagsLow value="0" />\n <FlagsVlow value="0" />\n'
         ' <ShaderGroup>\n  <TextureDictionary>\n%s  </TextureDictionary>\n  <Shaders>\n%s  </Shaders>\n </ShaderGroup>\n'
         ' <DrawableModelsHigh>\n  <Item>\n   <RenderMask value="255" />\n   <Flags value="0" />\n   <HasSkin value="0" />\n'
         '   <BoneIndex value="0" />\n   <Unknown1 value="%d" />\n   <Geometries>\n%s   </Geometries>\n  </Item>\n </DrawableModelsHigh>\n <Lights />\n</Drawable>\n'
         ) % (name, *map(fnum, c), fnum(r), *map(fnum, lo), *map(fnum, hi), lod, texs, shaders, len(parts), geos)
    open(os.path.join(XML, name + '.ydr.xml'), 'w', encoding='utf-8').write(x)
    print(name, 'bounds', np.round(lo, 4).tolist(), np.round(hi, 4).tolist())


def p2(w, h):  # power-of-two texture size for an aspect, longest side 1024
    def r(v): return 2 ** int(round(math.log2(v)))
    s = 1024 / max(w, h); return (min(1024, r(w * s)), min(1024, r(h * s)))


# posters: plane through x = 0 (the originals' bounds: |x| < 0.0007), art readable from both faces
POSTERS = {   # name: (half y, half z, art)
    'cpd_poster_1': (0.3477936, 0.2812500, A.poster_911),
    'cpd_poster_2': (0.3015137, 0.4414063, A.poster_recruit),
    'cpd_poster_3': (0.2214356, 0.3281250, A.poster_safety),
    'cpd_poster_6': (0.4575043, 0.3066406, A.poster_map),
}
for name, (hy, hz, art) in POSTERS.items():
    img = art(int(hy * 2 * 1400), int(hz * 2 * 1400))
    front, back = Mesh(), Mesh()
    plane_x(front, -hy, hy, -hz, hz, 0.0002, +1)
    plane_x(back, -hy, hy, -hz, hz, -0.0002, -1)
    size = p2(hy * 2, hz * 2)
    write_ydr(name, [(front, name, img, size, 'DXT1'), (back, name, img, size, 'DXT1')])

# plaque (placa_ibonoja_gssh bounds x +-0.2534, y -0.0388..0.0150, z +-0.2507): wooden board on the wall (back at y = 0.015,
# front at y = -0.012), cast medallion standing proud to y = -0.0388
W, Z = 0.2534, 0.2505
face, sides, cap, ring = Mesh(), Mesh(), Mesh(), Mesh()
plane_y(face, -W, W, -Z, Z, -0.012, -1)
box_sides(sides, -W, W, -0.012, 0.015, -Z, Z)
disc_prism(cap, ring, 0, 0.045, 0.165, -0.0388, -0.012)
board = A.plaque_board(1024, 1024)
wood = board.crop((300, 300, 364, 364))
gold = Image.new('RGBA', (64, 64), A.GOLD_D + (255,))
write_ydr('cpd_plaque', [(face, 'cpd_plaque_board', board, (512, 512), 'DXT1'), (sides, 'cpd_plaque_wood', wood, (64, 64), 'DXT1'),
                         (cap, 'cpd_plaque_seal', A.medallion(1024), (512, 512), 'DXT1'), (ring, 'cpd_plaque_rim', gold, (64, 64), 'DXT1')], lod=50)

# station sign (cartel_comisaria_gssh bounds x +-0.3199, y 0..0.0015, z +-0.2051): a printed panel, art on both faces
W, Z = 0.3199215, 0.2050781
f1, f2, ed = Mesh(), Mesh(), Mesh()
plane_y(f1, -W, W, -Z, Z, 0.0, -1)
plane_y(f2, -W, W, -Z, Z, 0.0015, +1)
sign = A.station_sign(1280, 820)
write_ydr('cpd_station_sign', [(f1, 'cpd_station_sign', sign, (1024, 512), 'DXT1'), (f2, 'cpd_station_sign', sign, (1024, 512), 'DXT1')], lod=50)

# flag cloth textures (same size / format / mips as Rockstar's prop_flag_* : 256 x 128 DXT1, 6 levels)
for name, art in (('cpd_flag_police', A.flag_police), ('cpd_flag_city', A.flag_city)):
    im = A.as_flag(art(1024, 512)).resize((256, 128), Image.LANCZOS)
    im.save(os.path.join(PNG, name + '.png'))
    d = os.path.join(XML, name); os.makedirs(d, exist_ok=True)
    lv = make_levels(im.convert('RGB').convert('RGBA'))
    write_dds(os.path.join(d, name + '.dds'), lv, 'DXT1'); print(name, 'texture', len(lv), 'levels')
print('ok')
