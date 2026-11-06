# 05 · Water and pools

## Water you can see
Interior pools in vanilla (Diamond penthouse spa, yacht jacuzzi) are a mesh, not game water: `normal_spec_alpha` (or `normal_alpha`)
with an aqua alpha diffuse, a tiled ripple normal map and a tight, strong specular. Our recipe (`tower_crown.water_mat`):
diffuse (0.16, 0.56, 0.64) alpha 0.5, normal map from summed low-frequency sine waves (integer frequencies so it tiles),
bumpiness 0.35, specular 1.0 / falloff 512 / fresnel 0.97. Pale aqua pool tiles under it; soft underwater lights (strong point lights
under the surface make a hard-edged bright square).

## Water you can swim in — what works (tested on the rig 2026-10-22)
**Use the game's water map.** Load a copy of the vanilla `water.xml` with the pool's cells added, via FiveM's
`LoadWaterFromPath(resource, file)` (file listed under `files {}` in the fxmanifest). Tools: `tools/pool_water.py` (build the file),
`tools/water.lua` (load it, reload after Cayo Perico, `ResetWater()` on stop), `tools/water_xml.ps1` (extract the vanilla map).

Rules found by testing:
- **Water cells register only on the 2 m grid.** A 2 × 2 m quad on even coordinates works; 1 m, 0.5 m and off-grid quads are
  silently ignored (`GetWaterHeight` returns false).
- `IsInvisible = true` (draw your own surface), `HasLimitedDepth = true` (the floors below the pool stay dry — verified).
- A ped swims (`IsPedSwimming`, submerged level ~0.9) in 1.76 m of water.
- **Turned pools** (the building is rotated, the grid is not): fill the pool with every 2 m cell whose four corners lie inside a
  **raised deck** round the pool (1.8 m wide, top 4 cm above the water line). Cells that reach past the pool edge lie under stone,
  never on an open floor. Coverage on the Tower City pool (8 x 8 m, turned 69.5 deg): 56 % with no deck, 97 % with a 1.8 m deck,
  100 % with a 2.4 m deck (26 cells). Rig test: the ped swims (`IsPedSwimming`, submerged 0.95) at every test point; the floor
  beside the deck and the floors under the pool stay dry. Cut the deck round anything standing in it (a sauna) and lift doors /
  props that end up on it.
- Only one water map can be active. A server that already streams its own `water.xml` must merge the pool's cells into it.
- Keep every vanilla quad unchanged in the file; after shipping, **check the whole city for stray water** with `tools/water_diff.lua`
  (vanilla vs ours on a grid). Two passes: the whole map at z 1500 (open water: Tower City 175 441 samples, 0 differences), and a 1 m
  grid round the pool at the pool's height AND at every floor and the street below. A probe from high up does NOT see
  limited-depth quads, so the first pass alone misses your pool entirely (it reported 0 differences at the pool itself).
  Tower City result: water only inside the pool deck; none outside it, none on any floor or street below.
- The game draws its own water surface on the cells even with `IsInvisible`; at the same height as your visible surface they
  z-fight (dark patches, caustic light on the deck). Put your surface 2 cm above the water line and the deck ≥ 12 cm above.

## What did not work
- **House pools are not in `water.xml`** (504 quads: ocean, rivers, reservoirs). Rockstar's pools use a static collision surface:
  a flat child at the water line with material WATER (125, `FLAG_SEE_THROUGH, FLAG_SHOOT_THROUGH_FX`), `CompositeFlags1 = MAP_RIVER`,
  `CompositeFlags2` without PED/vehicle (found with `tools/vanilla_bounds_by_material.ps1` around Rockford Hills). We added the same
  surface to our interior collision: `TestVerticalProbeAgainstAllWater` saw it at the right height, but **peds never entered water**
  (submerged 0). Community notes say the area must also be "designated swimmable" in `heightmap.dat`, which FiveM can't replace.
  For a high-rise pool, use the water map.

## Still water (review 2, 2026-10-22)
- The game draws pool water with its sea shader, so a water-map pool rolls like the ocean. Add a `CalmingQuads` item over the pool
  (minX/maxX/minY/maxY + `fDampening`; vanilla lakes use 0.05, we use 0.0) in the same water.xml - `pool_water.py` writes it.
- Water line: 25 cm under the deck still read as brim-full on screen; 45 cm reads right (and you still swim: 1.75 m deep).

## Which water.xml is the game's, and the missing-reservoir bug (2026-11-05)
- **The water map in force:** `common.rpf\data\levels\gta5\water.xml` (504 water / 542 calming / 116 wave quads,
  md5 `1a76f16bbeb4fccb4ec8d22f1a6d3d5f`). No update / dlc_patch copy exists: `update.rpf` only adds `water_heistisland.xml`
  (Cayo Perico, 62 quads). Checked in the Steam install AND in FiveM's game-build overlay
  (`%LOCALAPPDATA%\FiveM\FiveM.app\data\game-storage\update+update.rpf_<sha1>`, `update+update2.rpf_<sha1>`; with
  `sv_enforceGameBuild 3258` the client runs those instead of the Steam `update*.rpf`). If a newer build ever ships one, the newest
  patch copy wins: FiveM overlay > Steam, `update2.rpf` > `update.rpf` > `common.rpf`. `tools/water_xml.ps1` extracts every copy,
  prints md5s and names the one in force: rebuild the pool file from that one and diff the vanilla part before shipping.
- Opening the overlay with CodeWalker: give `RpfFile` its real name (`$r.Name = 'update.rpf'`); NG decryption keys off the
  archive's file name + size, so the hashed name fails with "Error in RPF7 file entry".
- **Bug (open):** with Tower City's `tc_water.xml` loaded by `LoadWaterFromPath`, the Land Act reservoir (z 160.339, x 1656..2088,
  y -114..806) shows no water surface; `ResetWater()` brings it back (seen in game twice). It is **not** a stale vanilla copy: the
  file's first 504 / 542 / 116 items are identical to the game's water.xml, item by item, and a rebuild from the game copy is
  byte-identical. What our file adds that the game never uses: 25 cells with `HasLimitedDepth = true` (vanilla has none), a new
  highest water level (z 255.55; vanilla max 196.409, an 8th distinct height; vanilla has 7) and one calming quad.
  A cfx.re report has the same symptom (dam surface not drawn, still swimmable) after adding quads to the default water.xml.
  Find the trigger with A/B files loaded one at a time: vanilla only (does `LoadWaterFromPath` itself lose it?), + cells without
  the calming quad, + calming quad only, + cells with `HasLimitedDepth = false`. Look at the reservoir AND Vinewood lake
  (x -8..56, y 732..988, z 196.409) each time. Write the result here.
