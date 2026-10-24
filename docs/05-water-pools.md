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
