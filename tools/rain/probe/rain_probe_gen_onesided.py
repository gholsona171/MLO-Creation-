"""rainprobe: 8 opaque slabs over Tower City's court at z 70, one per model RenderMask / entity flag variant -> which ones
block GTA's rain (height map) and which ones draw in the main view."""
import math, re, os, sys
from pathlib import Path
P = Path(sys.argv[1]); S = P / 'src'; OUT = P / 'build2'; OUT.mkdir(exist_ok=True)
src = (S / 'urinal.ydr.xml').read_text()
head = src[:src.index('<DrawableModelsHigh>')]
hw, hl, th = 20.0, 5.0, 0.3
SIDES = ('top', 'bottom')
def box(sides=None):
    V = []; I = []
    faces = [((0, 0, 1), [(-hw, -hl, th), (hw, -hl, th), (hw, hl, th), (-hw, hl, th)]),
             ((0, 0, -1), [(-hw, hl, 0), (hw, hl, 0), (hw, -hl, 0), (-hw, -hl, 0)])]
    for (n, q), s in zip(faces, ('top', 'bottom')):
        if sides and s not in sides: continue
        b = len(V)
        for k, p in enumerate(q):
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)][k]
            V.append(f'{p[0]} {p[1]} {p[2]}   {n[0]} {n[1]} {n[2]}   0 124 0 255   {uv[0]*8} {uv[1]*2}   1 0 0 -1')
        I += [b, b + 1, b + 2, b, b + 2, b + 3]
    return V, I
def ydr(name, mask, sides=None):
    V, I = box(sides)
    h = head.replace('<Name>tc_prop_urinal</Name>', f'<Name>{name}</Name>', 1)
    h = re.sub(r'<BoundingSphereCenter[^>]*/>', f'<BoundingSphereCenter x="0" y="0" z="0.15" />', h)
    h = re.sub(r'<BoundingSphereRadius value="[^"]*" />', f'<BoundingSphereRadius value="{math.hypot(hw, hl):.3f}" />', h)
    h = re.sub(r'<BoundingBoxMin[^>]*/>', f'<BoundingBoxMin x="{-hw}" y="{-hl}" z="0" />', h, count=1)
    h = re.sub(r'<BoundingBoxMax[^>]*/>', f'<BoundingBoxMax x="{hw}" y="{hl}" z="{th}" />', h, count=1)
    m = f''' <DrawableModelsHigh>
  <Item>
   <RenderMask value="{mask}" />
   <Flags value="0" />
   <HasSkin value="0" />
   <BoneIndex value="0" />
   <Unknown1 value="0" />
   <Geometries>
    <Item>
     <ShaderIndex value="0" />
     <BoundingBoxMin x="{-hw}" y="{-hl}" z="0" w="0" />
     <BoundingBoxMax x="{hw}" y="{hl}" z="{th}" w="0" />
     <VertexBuffer>
      <Flags value="0" />
      <Layout type="GTAV1">
       <Position />
       <Normal />
       <Colour0 />
       <TexCoord0 />
       <Tangent />
      </Layout>
      <Data>
''' + '\n'.join('       ' + v for v in V) + '''
      </Data>
     </VertexBuffer>
     <IndexBuffer>
      <Data>
       ''' + ' '.join(map(str, I)) + '''
      </Data>
     </IndexBuffer>
    </Item>
   </Geometries>
  </Item>
 </DrawableModelsHigh>
 <Lights />
</Drawable>
'''
    d = OUT / name; d.mkdir(exist_ok=True)
    for f in S.glob('*.dds'): (d / f.name).write_bytes(f.read_bytes())
    (OUT / f'{name}.ydr.xml').write_text(h + m)
VAR = [('rp_top255', 255, ('top',)), ('rp_top253', 253, ('top',)), ('rp_bot255', 255, ('bottom',))]
for nm, mk, sd in VAR: ydr(nm, mk, sd)
MASKS = [v[0] for v in VAR]
arch = ''.join(f'''  <Item type="CBaseArchetypeDef">
   <lodDist value="500" />
   <flags value="0" />
   <specialAttribute value="0" />
   <bbMin x="{-hw}" y="{-hl}" z="0" />
   <bbMax x="{hw}" y="{hl}" z="{th}" />
   <bsCentre x="0" y="0" z="0.15" />
   <bsRadius value="{math.hypot(hw, hl):.3f}" />
   <hdTextureDist value="300" />
   <name>{mk}</name>
   <textureDictionary />
   <clipDictionary />
   <drawableDictionary />
   <physicsDictionary />
   <assetType>ASSET_TYPE_DRAWABLE</assetType>
   <assetName>{mk}</assetName>
   <extensions />
  </Item>
''' for mk in MASKS)
(OUT / 'rainprobe.ytyp.xml').write_text(f'''<?xml version='1.0' encoding='UTF-8'?>
<CMapTypes>
 <extensions />
 <archetypes>
{arch} </archetypes>
 <name>rainprobe</name>
 <dependencies />
 <compositeEntityTypes itemType="CCompositeEntityType" />
</CMapTypes>
''')
ORG, H = (71.0, -884.0), math.radians(69.5)
def world(u, v): return ORG[0] + u * math.cos(H) - v * math.sin(H), ORG[1] + u * math.sin(H) + v * math.cos(H)
STRIPS = [('rp_top255', 32), ('rp_top253', 32), ('rp_bot255', 32)]
ents = ''; rows = []
for k, (a, fl) in enumerate(STRIPS):
    v = -43.0 + k * 11.5; x, y = world(0.0, v); rows.append((k + 1, a, fl, round(x, 2), round(y, 2), v))
    ents += f'''  <Item type="CEntityDef">
   <archetypeName>{a}</archetypeName>
   <flags value="{fl}" />
   <guid value="{3100000000 + k}" />
   <position x="{x:.3f}" y="{y:.3f}" z="70.000" />
   <rotation x="0.0000000" y="0.0000000" z="{-math.sin(H / 2):.7f}" w="{math.cos(H / 2):.7f}" />
   <scaleXY value="1" />
   <scaleZ value="1" />
   <parentIndex value="-1" />
   <lodDist value="500" />
   <childLodDist value="0" />
   <lodLevel>LODTYPES_DEPTH_ORPHANHD</lodLevel>
   <numChildren value="0" />
   <priorityLevel>PRI_REQUIRED</priorityLevel>
   <extensions />
   <ambientOcclusionMultiplier value="255" />
   <artificialAmbientOcclusion value="255" />
   <tintValue value="0" />
  </Item>
'''
(OUT / 'rainprobe.ymap.xml').write_text(f'''<?xml version='1.0' encoding='UTF-8'?>
<CMapData>
 <name>rainprobe</name>
 <parent />
 <flags value="0" />
 <contentFlags value="1" />
 <streamingExtentsMin x="-500" y="-1400" z="-500" />
 <streamingExtentsMax x="600" y="-400" z="600" />
 <entitiesExtentsMin x="0" y="-950" z="69" />
 <entitiesExtentsMax x="140" y="-810" z="71" />
 <entities>
{ents} </entities>
 <containerLods itemType="rage__fwContainerLodDef" />
 <boxOccluders itemType="BoxOccluder" />
 <occludeModels itemType="OccludeModel" />
 <physicsDictionaries />
 <instancedData>
  <ImapLink />
  <PropInstanceList itemType="rage__fwPropInstanceListDef" />
  <GrassInstanceList itemType="rage__fwGrassInstanceListDef" />
 </instancedData>
 <LodLightsSOA>
  <direction itemType="FloatXYZ" />
  <falloff />
  <falloffExponent />
  <timeAndStateFlags />
  <hash />
  <coneInnerAngle />
  <coneOuterAngleOrCapExt />
  <coronaIntensity />
 </LodLightsSOA>
 <DistantLodLightsSOA>
  <position itemType="FloatXYZ" />
  <RGBI />
  <numStreetLights value="0" />
  <category value="0" />
 </DistantLodLightsSOA>
 <block>
  <version value="0" />
  <flags value="0" />
  <name />
  <exportedBy />
  <owner />
  <time />
 </block>
</CMapData>
''')
for r in rows: print('STRIP', *r)
