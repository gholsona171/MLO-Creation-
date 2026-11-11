"""Crumpled paper balls, one per paper colour (c9_stickynotes, Nov 2026). No Blender: the shape comes straight from the crumple
simulation the NUI uses (paper_ball_geom.mjs), so the ball on the ground matches the 3D ball in the UI.

  py -3 paper_balls.py <sim.js> <out dir>        -> <out>/bin/<name>.ydr for each colour + c9sn_balls.ytyp

Each model: a crumpled sheet ~7 cm across (a real balled sticky note is 3-4 cm; larger so it reads on the floor), drawn
double-sided (the sheet has two faces; the back copy sits 0.4 mm inside so the two never z-fight), pivot centred in x/y with z = 0 at its lowest point (it sits on the ground: place it at the
ground z, no PlaceObjectOnGroundProperly needed). Shader default.sps like Rockstar's prop_paper_ball, one embedded 128 px
A8R8G8B8 texture: the paper colour, grain and faint ink lines. Sphere bounds. Archetypes via mlo_meta (TequiBuild), lodDist 40."""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\TowerCity\work')
import mlo_meta as MM  # plain_ytyp + compile_all (TequiBuild)

COLOURS = {'yellow': '#fde68a', 'pink': '#fbcfe8', 'blue': '#bfdbfe', 'green': '#bbf7d0', 'orange': '#fed7aa'}
SIZE = 0.07         # metres across (a real balled sticky note is 3-4 cm; 7 cm reads on the floor from standing height)
TEX = 128
YDR_XML = HERE.parent / 'ydr_xml.ps1'


def geometry(sim_js, seed):
    out = subprocess.run(['node', str(HERE / 'paper_ball_geom.mjs'), sim_js, '20', str(seed)], capture_output=True, text=True, check=True)
    g = json.loads(out.stdout)
    p = np.array(g['pos'], np.float64).reshape(-1, 3)
    uv = np.array(g['uv'], np.float64).reshape(-1, 2)
    tri = np.array(g['index'], np.int64).reshape(-1, 3)
    # sheet units -> metres; the sim's z is the sheet normal, keep it as up
    ext = p.max(0) - p.min(0)
    p *= SIZE / max(ext[0], ext[1])
    p[:, 0] -= (p[:, 0].max() + p[:, 0].min()) / 2
    p[:, 1] -= (p[:, 1].max() + p[:, 1].min()) / 2
    p[:, 2] -= p[:, 2].min()
    return p, uv, tri


def normals(p, tri):
    n = np.zeros_like(p)
    f = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])
    for k in range(3): np.add.at(n, tri[:, k], f)
    # point away from the ball's centre (the sheet is folded every which way; outward reads best under GTA's lighting)
    c = p.mean(0)
    flip = np.einsum('ij,ij->i', n, p - c) < 0
    n[flip] *= -1
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def texture(hexcol, seed):
    rng = np.random.default_rng(seed)
    rgb = np.array([int(hexcol[i:i + 2], 16) for i in (1, 3, 5)], np.float64) / 255
    # the UI's pastel paper bleaches to white under GTA's sun; squaring keeps the hue and gives back the saturation
    rgb = rgb ** 2.0
    px = np.ones((TEX, TEX, 4))
    px[:, :, :3] = rgb * (1 + rng.normal(0, 0.035, (TEX, TEX, 1)))
    # faint ink: a few wavy handwriting lines
    ink = np.array([0.16, 0.18, 0.24])
    for row in range(26, TEX - 16, 18):
        x0, x1 = 12, TEX - 12 - rng.integers(0, 40)
        xs = np.arange(x0, x1)
        ys = (row + 2.5 * np.sin(xs / 3.1 + rng.uniform(0, 6)) + rng.normal(0, 0.4, xs.size)).astype(int)
        for dy in (0, 1):
            px[np.clip(ys + dy, 0, TEX - 1), xs, :3] = px[np.clip(ys + dy, 0, TEX - 1), xs, :3] * 0.35 + ink * 0.65
    return (np.clip(px, 0, 1) * 255).astype(np.uint8)


def dds_argb(path, rgba):
    import struct
    h, w = rgba.shape[:2]
    hdr = struct.pack('<4sIIIIIII44xII4sIIIIII16x', b'DDS ', 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, w, w * 4, 0, 1,
                      32, 0x41, b'\0\0\0\0', 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000, 0x1000)
    path.write_bytes(hdr + rgba[:, :, [2, 1, 0, 3]].tobytes())


def f(v): return f'{v:.7g}'


def ydr_xml(name, p, uv, tri):
    n = normals(p, tri)
    # two-sided: a second copy with flipped normals and winding
    # the back copy is pushed 0.4 mm inwards: two faces at the same depth flicker dark under GTA's lighting
    P = np.vstack([p, p - n * 0.0004]); N = np.vstack([n, -n]); UV = np.vstack([uv, uv])
    T = np.vstack([tri, tri[:, ::-1] + len(p)])
    lo, hi = P.min(0), P.max(0); c = (lo + hi) / 2; r = float(np.linalg.norm(hi - lo) / 2)
    verts = '\n'.join(f'       {f(a[0])} {f(a[1])} {f(a[2])}   {f(b[0])} {f(b[1])} {f(b[2])}   255 255 255 255   {f(t[0])} {f(1 - t[1])}'
                      for a, b, t in zip(P, N, UV))
    flat = T.reshape(-1)
    idx = '\n'.join('       ' + ' '.join(str(i) for i in flat[k:k + 24]) for k in range(0, flat.size, 24))
    v = lambda tag, a: f'<{tag} x="{f(a[0])}" y="{f(a[1])}" z="{f(a[2])}" />'
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Drawable>
 <Name>{name}</Name>
 {v('BoundingSphereCenter', c)}
 <BoundingSphereRadius value="{f(r)}" />
 {v('BoundingBoxMin', lo)}
 {v('BoundingBoxMax', hi)}
 <LodDistHigh value="9998" />
 <LodDistMed value="9998" />
 <LodDistLow value="9998" />
 <LodDistVlow value="9998" />
 <FlagsHigh value="1" />
 <FlagsMed value="0" />
 <FlagsLow value="0" />
 <FlagsVlow value="0" />
 <ShaderGroup>
  <TextureDictionary>
   <Item>
    <Name>{name}</Name>
    <Unk32 value="128" />
    <Usage>DIFFUSE</Usage>
    <UsageFlags>UNK24</UsageFlags>
    <ExtraFlags value="0" />
    <Width value="{TEX}" />
    <Height value="{TEX}" />
    <MipLevels value="1" />
    <Format>D3DFMT_A8R8G8B8</Format>
    <FileName>{name}.dds</FileName>
   </Item>
  </TextureDictionary>
  <Shaders>
   <Item>
    <Name>default</Name>
    <FileName>default.sps</FileName>
    <RenderBucket value="0" />
    <Parameters>
     <Item name="DiffuseSampler" type="Texture">
      <Name>{name}</Name>
     </Item>
     <Item name="matMaterialColorScale" type="Vector" x="1" y="0" z="0" w="1" />
     <Item name="HardAlphaBlend" type="Vector" x="1" y="0" z="0" w="0" />
     <Item name="useTessellation" type="Vector" x="0" y="0" z="0" w="0" />
     <Item name="wetnessMultiplier" type="Vector" x="1" y="0" z="0" w="0" />
     <Item name="globalAnimUV1" type="Vector" x="0" y="1" z="0" w="0" />
     <Item name="globalAnimUV0" type="Vector" x="1" y="0" z="0" w="0" />
    </Parameters>
   </Item>
  </Shaders>
 </ShaderGroup>
 <DrawableModelsHigh>
  <Item>
   <RenderMask value="255" />
   <Flags value="0" />
   <HasSkin value="0" />
   <BoneIndex value="0" />
   <Unknown1 value="0" />
   <Geometries>
    <Item>
     <ShaderIndex value="0" />
     <BoundingBoxMin x="{f(lo[0])}" y="{f(lo[1])}" z="{f(lo[2])}" w="{f(lo[0])}" />
     <BoundingBoxMax x="{f(hi[0])}" y="{f(hi[1])}" z="{f(hi[2])}" w="{f(hi[0])}" />
     <VertexBuffer>
      <Flags value="0" />
      <Layout type="GTAV1">
       <Position />
       <Normal />
       <Colour0 />
       <TexCoord0 />
      </Layout>
      <Data>
{verts}
      </Data>
     </VertexBuffer>
     <IndexBuffer>
      <Data>
{idx}
      </Data>
     </IndexBuffer>
    </Item>
   </Geometries>
  </Item>
 </DrawableModelsHigh>
 <Bounds type="Sphere">
  {v('BoxMin', lo)}
  {v('BoxMax', hi)}
  {v('BoxCenter', c)}
  {v('SphereCenter', c)}
  <SphereRadius value="{f(r * 0.8)}" />
  <Margin value="{f(r * 0.8)}" />
  <Volume value="{f(4 / 3 * math.pi * (r * 0.8) ** 3)}" />
  <Inertia x="0.0001" y="0.0001" z="0.0001" />
  <MaterialIndex value="0" />
  <MaterialColourIndex value="0" />
  <ProceduralID value="0" />
  <RoomID value="0" />
  <PedDensity value="0" />
  <UnkFlags value="0" />
  <PolyFlags value="0" />
  <UnkType value="1" />
 </Bounds>
 <Lights />
</Drawable>
''', lo, hi


def main(sim_js, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True); (out / 'bin').mkdir(exist_ok=True)
    D = {}
    for k, (colour, hexcol) in enumerate(COLOURS.items()):
        name = f'c9sn_ball_{colour}'
        p, uv, tri = geometry(sim_js, 101 + k)
        xml, lo, hi = ydr_xml(name, p, uv, tri)
        (out / f'{name}.ydr.xml').write_text(xml, encoding='utf-8')
        (out / name).mkdir(exist_ok=True)
        dds_argb(out / name / f'{name}.dds', texture(hexcol, 7 + k))
        r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(YDR_XML), '-Mode', 'import',
                            '-In', str(out / f'{name}.ydr.xml'), '-Out', str(out / 'bin' / f'{name}.ydr')], capture_output=True, text=True)
        assert (out / 'bin' / f'{name}.ydr').exists(), r.stdout + r.stderr
        D[name] = {'bb_lo': [round(float(x), 4) for x in lo], 'bb_hi': [round(float(x), 4) for x in hi]}
        print(name, r.stdout.strip(), D[name])
    MM.plain_ytyp('c9sn_balls', list(D), D, 40, 20, out)
    bad = MM.compile_all(out, ('c9sn_balls.ytyp',)); assert not bad, bad
    print('PAPER_BALLS_PASS', sorted(x.name for x in (out / 'bin').iterdir()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
