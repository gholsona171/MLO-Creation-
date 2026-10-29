# 13 · Exterior shells and their LOD chain (Justice Center phase 2, 2026-10-28)

The new complex on a cleared block (doc 02, "clearing a whole block"): five buildings, skybridges, a plaza, a lawn, a sculpture,
built as exterior shells whose interiors come later as MLOs. Tools: `tools/justice/p2/` (copies; the project runs from
`JusticeCenter/work/p2`, pipeline `work/build_p1.sh`). Tower City's `tc_kit` is the Blender kit (imported, never edited).

## One source for every level
- A building = an axis box + floor levels; its facade = per face a list of **openings** (kind, s0, s1, z0, z1) in face coordinates,
  plus **covered** rects where a neighbour or a skybridge stands against it. Stone = face rect minus openings minus covered
  (`tc_kit.rects_minus`). `p2_plan.py` is pure Python, so the Blender build, the LOD baker, the night pattern, the collision hull,
  the gates and the rig probes all read the same numbers.
- The LOD atlas is the same openings rasterised (stone = the mean colour of Rockstar's own stone texture), the night pattern is the
  same `lit()` pick in the HD `_emi` model, the LOD and the SLOD, so nothing changes between levels but the detail.
- **N / S faces own the corners** (E / W faces stop DEPTH short): two faces never share a corner block.
- **A corner pier must be wider than anything that reaches back from the perpendicular face** (a colonnade's depth + its glass
  wall's backing box: 3 + 1.2 m). Jail I's 2.6 m corners let the two colonnades' backing boxes intersect - the sweep found it.

## Windows that never show sky
- Dark glass is not opaque: behind every shell bay sits a **window box** 1.2 m deep (backing panel, floor edge, ceiling strip, two
  sides) in a dark unlit material. One pane per bay (doc 02). Phase 3 hook: `SEE_OUT[building]` = levels that get an MLO room - their
  bays drop the box and the hull leaves that floor band to the MLO's collision.
- Clear (see-through) glass needs something behind it: the atrium gets a placeholder core (floor + the neighbours' walls) until its
  MLO exists (`MLO_BUILT`). Walls of the placeholder must stop where the atrium's own facade stone stands (box minus the stone
  strips) or they share faces at the corners.

## Collision on everything (outside)
- One static ybn for the whole site, world space, **one BVH child per material** (stone walls, grass lawn, concrete paving, metal):
  tc_kit's merge sets every face to CONCRETE, so the exterior keeps its own (`p2_kit.export_collision`).
- Each building's **hull** = its mass from under the slab to the roof + a parapet ring, minus the colonnades' walkable space and
  the vehicle bays. Climb-proof by construction: no ledges, no access to shell floors.
- **Box-minus must merge its cells** (z-columns per cell, then runs): a grid decomposition leaves internal split faces inside the
  solid at every cut height of any void - the ground check read them as ground (0.15 m "mismatches" over the colonnades).
- Rockstar's outdoor steps: visual treads, ONE collision ramp from one going in front of the bottom riser to the top riser.

## Plugging into Rockstar's LOD tree (never shipping the district LOD ymap)
Read the block's own tree first. Davis: SLOD3 `sc1_lod_slod4` 15000 -> SLOD2 `sc1_lod_19` 1500 (childLodDist 750) -> SLOD1
`sc1_19_slod1` 399 -> LODs 200-450 -> HD; night: `sc1_lod_emissive` -> `sc1_19_sc1_emissive_slod` 8000 -> emissive LODs 300.
- Re-use the block ymap's SLOD1 and emissive-SLOD entity slots (archetype swapped to ours, lodDist set inside the parent's
  childLodDist: 750) AND its own LOD slots for our LODs; put our HD entities in that SAME ymap (parentIndex -> our LOD slot). Do it in
  every prefix (lr_ / hei_ / base) through the same writer that swaps the old block.
- **Proven on the rig (2026-10-28): an HD in the child `_strm_0` ymap never swapped with its LOD** - both drew, the LOD's flat box
  z-fought the HD stone (smeared "blotchy" walls) and its top hid the HD roof (a flat cream roof). Data checked in the compiled
  files (indices, counts, distances all right) - it is the cross-ymap link. Moving the HDs into the LOD ymap fixed it at once.
- **A parent swaps to its children only when ALL of them are in range**: the old block's (emptied) LODs left under the re-used SLOD1
  slot (lodDist 200-450, spread over the block) kept it drawing - cut every stale child loose (parentIndex -1), and make the old
  (empty) HD children of re-used LOD slots orphans.
- Find which level draws: rebuild the LODs with each level in its own flat colour (`JC_LOD_DEBUG=1`: LOD red, SLOD1 blue,
  SLOD2/3 green) and shoot; `CreateModelHide` did not hide LOD entities, and hiding the HD changed nothing - a wrong lead.
- Keep the district LOD ymap (`lr_sc1_lod`) untouched (conflict surface): work inside its numbers. Davis: HD 300 (tower 350), LOD
  500, SLOD1 750, then the vanilla SLOD2 / SLOD3 with our massing ADDED to their models.
- **Adding to his SLOD models**: import the (already lot-cut) drawable, add one more model with an embedded atlas at the levels his
  models use (`p1_cut_lod.py --add=<drawable>`): massing + the lot's ground plates (lot / podium / lawn) so the cut hole is filled.
- The lot slab is an orphan: its lodDist = the SLOD1 / SLOD2 handover (750): beyond it the SLOD2's ground plate draws.
- Rig walk (`p2_probe.py round steps`): the whole block at street level and up every entrance kind. Both runs passed after the
  colonnade fix.
- Centre every model on its own bounds and put the entity there (Rockstar's LODs sit at their centres; lodDist is measured from
  the entity).
- Emissive overlays sit in front of the massing face of their level: HD quads 4 cm in front of the backing, LOD +0.15 m, SLOD +0.4 m.

## Night: vertex colours, not the shader (Antonio's 23:00 shots, 2026-10-28)
- Every wall glowed evenly pink at 23:00 while the vanilla blocks went dark. Cause: vertex colour 0 = 1.0 in every channel (tc_kit
  writes that on exteriors). In Rockstar's exterior models R = natural ambient, **G = artificial ambient** (the night "lit from
  inside" light), B a third term. His walls: sc1_19_courts 0.47 / 0.05 / 0.22, sheriff 0.58 / 0.13 / 0.37, hw1_26 0.48 / 0.02 / 0.49.
- Measure his model's colour with `color_srgb` (what Sollumz stores) and write ours the same way. LODs carry the same values, and
  only the night-light (_emi) models keep 1.0. A SLOD model added to his drawable copies his own material + his median colours (a
  fresh default.sps model with white colours drew BLACK in his SLOD).
- A night-light texture lit at full brightness reads as beige panels by DAY: keep its diffuse dark (x0.16) and raise the
  emissiveMultiplier by the same factor.

## Colonnades are one walk, not alcoves
- Group the colonnade bays into runs: one floor, one soffit, one glass wall per run, with free-standing piers 1.4 m deep and a walk
  behind them. Piers running back to the glass made each bay a dead end, and the rig walk along the colonnade stopped at the first pier.
- The run's floor passes under the piers, so the face stone has a hole there from under the slab up to the floor (or the floor and
  the pier stone share a face: the sweep finds it).

## Rockstar materials for a new look
- Survey textures by name over the city ytds (`tex_scan.ps1`), then **filter by colour** (mean RGB near the target - here the
  real granite `#DBBA9E`) and look at a sheet of the best 72 (`sheet.py`). Pink granite: Hollywood `hw1_26` `ko_gv_wall` (warm stone
  panels) with his `normal.sps` recipe from `hw1_26_build01`; Jail II's cream panels = the old block's own `mc_wall_0001`.
- When one drawable mixes his textures from several dictionaries, embed them (`p2_tex.ps1` copies the DDS from the game); one
  archetype binds only one txd.

## Driveways of the old block
- Profile Rockstar's drawn sidewalk heights outside each lot edge (0.5 - 6 m out, every metre): a dropped kerb shows as the sidewalk
  sloping to road level. Re-use the ones that fit (Davis: the sally port on Macdonald v 13-19, the police garage on Innocence
  v -51..-45), put bollards on the mouth line of the rest (doc 02).

## Gates (all offline, on the built files; the build stops on any)
- sweep: tc_kit's level sweep - outside, nothing is excused (every face can be seen from somewhere).
- cross: horizontal coplanar triangles across every drawable + the slab, 3 cm - **proven on a planted overlap** each run.
  Emissive quads 3 cm under a soffit read as 2.99 cm: keep overlays >= 6 cm off.
- ground_check (doc 07) extended: the complex's models in the drawn set; cells inside a building's mass are walls (counted, not
  tested); a "low look" under every soffit / bay ceiling; on steps the treads and the ramp may differ by one riser. Planted defects
  must sit on open slab (a planted hole under the podium is never seen).
