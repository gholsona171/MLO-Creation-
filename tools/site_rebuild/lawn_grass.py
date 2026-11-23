"""The lawn's grass blades, grown the way Rockstar grows its park grass (Mirror Park, survey/grass_mirror.txt): ymap grass batches
(GrassInstanceList) of the vanilla proc_ grass archetypes, each blade tinted by its own colour, standing on the lawn surface.
Rockstar's city lawns (Rockford Hills, the golf club) carry no blades at all; their park lawns do, so this is the native look.
  * Where: every point site_plan.in_lawn says is lawn, at least EDGE m from any ground that is not lawn (the edging, the
    driveway, the house), and clear of the pool + coping, the patio deck and the loungers (KEEP_OUT).
  * What: the mix and the archetype settings (scale range, lod / fade distances) copied from Mirror Park's batches; densities
    per square metre are ours (a lawn, not a field); blades kept short (a kept lawn, not a meadow: Antonio's first look read as long grass).
  * Batches: one per TILE x TILE m square, so each loads and fades with its own patch like the vanilla ones.
  * Its own ymap (jy_lawn), laid out like Rockstar's grass ymaps (cs4_02_grass_*: no entities, contentFlags 1024 = instance data).
Run: python lawn_grass.py   Output ../site/lawn/jy_lawn.ymap (+ .xml; assemble.py copies it)"""
import math, random, subprocess
from pathlib import Path
import site_plan as SP, pave_ground as PG, house_plan as H
M = Path(__file__).resolve().parents[1]; OUT = M / 'site' / 'lawn'
TB = 'C:/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/work/bin/Release/net48/TequiBuild.exe'
SEED = 20261123; TILE = 16.0; EDGE = 0.35; LIFT = 0.03
# archetype, blades per m2, ScaleRange (min, max, random z), lodDist, LodFadeStartDist, LodInstFadeRange   (Mirror Park values)
MIX = [('proc_grasses01',        0.90, (0.16, 0.30, 0.2), 100, 18, 0.75),     # (Mirror Park grows these at 0.3..0.8: meadow;
       ('proc_grasses01b',       0.70, (0.14, 0.26, 0.2), 100, 18, 0.75),     #  a kept lawn is about a third of that height)
       ('proc_grassplantmix_01', 0.04, (0.30, 0.45, 0.3), 100, 18, 0.75),
       ('proc_grassdandelion01', 0.05, (0.40, 0.60, 0.2), 35, 15, 0.75)]
BASE_RGB = (100, 108, 78); RGB_JITTER = 14                     # Mirror Park's park blades read 80..130 with green leading
X0, X1, Y0, Y1 = H.POOL
KEEP_OUT = [(X0 - H.COPING - .3, X1 + H.COPING + .3, Y0 - H.COPING - .3, Y1 + H.COPING + .3),   # pool + coping
            (H.PATIO[0] - .2, H.PATIO[1] + .2, H.PATIO[2] - .2, H.PATIO[3] + .2),           # timber deck
            (2346.0, 2354.0, 3153.4, 3156.0)]                                              # loungers (house_meta.py)


def grows(x, y):
    if any(SP.in_rect(x, y, r) for r in KEEP_OUT): return False
    return all(SP.in_lawn(x + dx, y + dy) and SP.on_site(x + dx, y + dy) for dx in (-EDGE, 0, EDGE) for dy in (-EDGE, 0, EDGE))


def batches():
    rnd = random.Random(SEED); tiles = {}
    lx = [p[0] for p in SP.HOUSE_LOT]; ly = [p[1] for p in SP.HOUSE_LOT]
    xa, xb, ya, yb = min(lx), max(lx), max(min(ly), SP.LAWN_Y), max(ly)
    for name, dens, srange, lod, fade, frange in MIX:
        n = int((xb - xa) * (yb - ya) * dens)
        for _ in range(n):
            x, y = rnd.uniform(xa, xb), rnd.uniform(ya, yb)
            if not grows(x, y): continue
            z = PG.pave_z(x, y) + LIFT; j = rnd.randint(-RGB_JITTER, RGB_JITTER)
            rgb = tuple(max(0, min(255, c + j + rnd.randint(-4, 4))) for c in BASE_RGB)
            key = (name, math.floor(x / TILE), math.floor(y / TILE))
            tiles.setdefault(key, (srange, lod, fade, frange, []))[4].append((x, y, z, rgb, rnd.randint(0, 255)))
    return tiles


def item(name, srange, lod, fade, frange, pts):
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
    <ScaleRange x="{srange[0]}" y="{srange[1]}" z="{srange[2]}" />
    <archetypeName>{name}</archetypeName>
    <lodDist value="{lod}" />
    <LodFadeStartDist value="{fade}" />
    <LodInstFadeRange value="{frange}" />
    <OrientToTerrain value="1" />
    <InstanceList itemType="rage__fwGrassInstanceListDef__InstanceData">{ins}
    </InstanceList>
   </Item>
"""


def ymap(items, tiles):
    pts = [p for v in tiles.values() for p in v[4]]
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
    tiles = {k: v for k, v in batches().items() if len(v[4]) >= 2}
    if OUT.exists():
        for f in OUT.iterdir(): f.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'jy_lawn.ymap.xml').write_text(ymap(''.join(item(k[0], *v[:4], v[4]) for k, v in sorted(tiles.items())), tiles), encoding='utf-8')
    r = subprocess.run([TB, 'compile', str(OUT / 'jy_lawn.ymap.xml'), str(OUT / 'jy_lawn.ymap')], capture_output=True, text=True)
    assert (OUT / 'jy_lawn.ymap').exists(), (r.stdout + r.stderr)[-400:]
    per = {}
    for k, v in tiles.items(): per[k[0]] = per.get(k[0], 0) + len(v[4])
    bad = [p for v in tiles.values() for p in v[4] if not grows(p[0], p[1])]
    assert not bad, f'{len(bad)} blades off the lawn'
    print('LAWN_GRASS_PASS', len(tiles), 'batches;', ', '.join(f'{k} {n}' for k, n in per.items()))
