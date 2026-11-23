"""The lawn's grass blades: a kept lawn grown with the game's own grass, as ymap grass batches (GrassInstanceList) the way Rockstar
grows its park grass (Mirror Park, survey/grass_mirror.txt: proc_grasses01 / 01b, each blade tinted by its own colour).
Antonio 2026-11-23: a "nice yard, but still with grass blades". The park mix (several archetypes, random spots, Mirror Park's
0.3..0.8 scales, dandelions) read as a raggedy yard: clumps with bare ground between them, mixed heights, weeds. So here:
  * one fine archetype (proc_grasses01b), planted on an even SPACING grid with a little jitter: no gaps, no clumping;
  * one short height (SCALE, a narrow range) and one lush green (RGB, +-JITTER): a mown, watered lawn;
  * on every point site_plan.in_lawn says is lawn, at least EDGE m from ground that is not lawn (the edging, the driveway, the
    house), clear of the timber patio (KEEP_OUT);
  * one batch per TILE x TILE m square, so each patch loads and fades on its own like the vanilla ones;
  * its own ymap (jy_lawn), laid out like Rockstar's grass ymaps (cs4_02_grass_*: no entities, contentFlags 1024 = instance data).
Run: python lawn_grass.py   Output ../site/lawn/jy_lawn.ymap (+ .xml; assemble.py copies it)"""
import math, random, subprocess
from pathlib import Path
import site_plan as SP, pave_ground as PG, house_plan as H
M = Path(__file__).resolve().parents[1]; OUT = M / 'site' / 'lawn'
TB = 'C:/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/work/bin/Release/net48/TequiBuild.exe'
SEED = 20261123; TILE = 12.0; EDGE = 0.30; LIFT = 0.03
ARCH = 'proc_grasses01b'
SPACING, JIT = 0.40, 0.13                                       # m: grid pitch, random offset either way
SCALE = (0.20, 0.26, 0.05)                                      # ScaleRange: min, max, random z
LOD, FADE, FADE_RANGE = 100, 18, 0.75                           # Mirror Park's values for this archetype
RGB, JITTER = (88, 112, 62), 3                                  # one lush green (Mirror Park's park blades: ~(105, 107, 83))
KEEP_OUT = [(H.PATIO[0] - .2, H.PATIO[1] + .2, H.PATIO[2] - .2, H.PATIO[3] + .2)]          # the timber deck


def grows(x, y):
    if any(SP.in_rect(x, y, r) for r in KEEP_OUT): return False
    return all(SP.in_lawn(x + dx, y + dy) and SP.on_site(x + dx, y + dy) for dx in (-EDGE, 0, EDGE) for dy in (-EDGE, 0, EDGE))


def blades():
    """{(tile i, tile j): [(x, y, z, (r, g, b), scale byte)]} over the house lot's lawn."""
    rnd = random.Random(SEED); tiles = {}
    lx = [p[0] for p in SP.HOUSE_LOT]; ly = [p[1] for p in SP.HOUSE_LOT]
    xa, xb, ya, yb = min(lx), max(lx), max(min(ly), SP.LAWN_Y), max(ly)
    for i in range(int((xb - xa) / SPACING) + 1):
        for j in range(int((yb - ya) / SPACING) + 1):
            x = xa + i * SPACING + rnd.uniform(-JIT, JIT); y = ya + j * SPACING + rnd.uniform(-JIT, JIT)
            if not grows(x, y): continue
            k = rnd.randint(-JITTER, JITTER); rgb = tuple(max(0, min(255, c + k)) for c in RGB)
            tiles.setdefault((math.floor(x / TILE), math.floor(y / TILE)), []).append((x, y, PG.pave_z(x, y) + LIFT, rgb, rnd.randint(0, 255)))
    return tiles


def item(pts):
    lo = [min(p[k] for p in pts) - .05 for k in range(3)]; hi = [max(p[k] for p in pts) + .05 for k in range(3)]
    q = lambda v, k: int(round((v - lo[k]) / (hi[k] - lo[k]) * 65535))
    ins = ''.join(f"""
     <Item>
      <Position>{q(x, 0)} {q(y, 1)} {q(z, 2)}</Position>
      <NormalX value="128" />
      <NormalY value="128" />
      <Color>{r} {g} {b}</Color>
      <Scale value="{s}" />
      <Ao value="255" />
      <Pad>0 0 0</Pad>
     </Item>""" for x, y, z, (r, g, b), s in pts)
    return f"""   <Item>
    <BatchAABB>
     <min x="{lo[0]:.5f}" y="{lo[1]:.5f}" z="{lo[2]:.5f}" w="0" />
     <max x="{hi[0]:.5f}" y="{hi[1]:.5f}" z="{hi[2]:.5f}" w="0" />
    </BatchAABB>
    <ScaleRange x="{SCALE[0]}" y="{SCALE[1]}" z="{SCALE[2]}" />
    <archetypeName>{ARCH}</archetypeName>
    <lodDist value="{LOD}" />
    <LodFadeStartDist value="{FADE}" />
    <LodInstFadeRange value="{FADE_RANGE}" />
    <OrientToTerrain value="1" />
    <InstanceList itemType="rage__fwGrassInstanceListDef__InstanceData">{ins}
    </InstanceList>
   </Item>
"""


def ymap(items, pts):
    lo = [min(p[k] for p in pts) for k in range(3)]; hi = [max(p[k] for p in pts) for k in range(3)]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CMapData>
 <name>jy_lawn</name>
 <parent />
 <flags value="0" />
 <contentFlags value="1024" />
 <streamingExtentsMin x="{lo[0] - 100:.3f}" y="{lo[1] - 100:.3f}" z="{lo[2] - 20:.3f}" />
 <streamingExtentsMax x="{hi[0] + 100:.3f}" y="{hi[1] + 100:.3f}" z="{hi[2] + 20:.3f}" />
 <entitiesExtentsMin x="{lo[0]:.3f}" y="{lo[1]:.3f}" z="{lo[2]:.3f}" />
 <entitiesExtentsMax x="{hi[0]:.3f}" y="{hi[1]:.3f}" z="{hi[2]:.3f}" />
 <entities />
 <containerLods />
 <boxOccluders />
 <occludeModels />
 <physicsDictionaries />
 <instancedData>
  <ImapLink />
  <PropInstanceList />
  <GrassInstanceList itemType="rage__fwGrassInstanceListDef">
{items}  </GrassInstanceList>
 </instancedData>
 <timeCycleModifiers />
 <carGenerators />
 <LODLightsSOA>
  <direction />
  <falloff />
  <falloffExponent />
  <timeAndStateFlags />
  <hash />
  <coneInnerAngle />
  <coneOuterAngleOrCapExt />
  <coronaIntensity />
 </LODLightsSOA>
 <DistantLODLightsSOA>
  <position />
  <RGBI />
  <numStreetLights value="0" />
  <category value="0" />
 </DistantLODLightsSOA>
 <block>
  <version value="0" />
  <flags value="0" />
  <name>jy_lawn</name>
  <exportedBy>graveyard_towyard</exportedBy>
  <owner />
  <time />
 </block>
</CMapData>
"""


if __name__ == '__main__':
    tiles = {k: v for k, v in blades().items() if len(v) >= 2}
    pts = [p for v in tiles.values() for p in v]
    if OUT.exists():
        for f in OUT.iterdir(): f.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'jy_lawn.ymap.xml').write_text(ymap(''.join(item(v) for _, v in sorted(tiles.items())), pts), encoding='utf-8')
    r = subprocess.run([TB, 'compile', str(OUT / 'jy_lawn.ymap.xml'), str(OUT / 'jy_lawn.ymap')], capture_output=True, text=True)
    assert (OUT / 'jy_lawn.ymap').exists(), (r.stdout + r.stderr)[-400:]
    bad = [p for p in pts if not grows(p[0], p[1])]
    assert not bad, f'{len(bad)} blades off the lawn'
    print('LAWN_GRASS_PASS', len(tiles), 'batches,', len(pts), ARCH, 'blades, max', max(len(v) for v in tiles.values()), 'per batch')
