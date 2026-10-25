# 11 · Cutting Rockstar props into modules (the C9 DJ counter kit, 2026-10-25)

Antonio wanted real GTA bar and restaurant counters he can attach himself: the full-size ones as Rockstar built them, plus cut
pieces (straights, corners, ends) that butt together into any bar. Everything below was built and checked for C9 DJ
(`scripts/c9_dj/prop/build/counters*.py`, copies in `tools/counter_kit/`). No Blender: the drawables are edited as CodeWalker XML.

## Find the candidates
- `tools/counters_scan.ps1` lists every archetype in the game whose name looks like a counter / desk / bar / till AND whose bounds are
  counter-sized (0.75 to 1.45 m high, 0.8 to 8 m long): name, ytyp, `int` (it lives in an interior's rpf) or `prop`, texture
  dictionary, size, physics dictionary, flags.
- `tools/arch_info.ps1 -Names a,b` prints the archetype's texture dictionary, flags, lodDist.
- **Interior-only = not spawnable** (proven on the rig, 2026-10-25): `IsModelInCdimage` is false for `bkr_bar_bar01`,
  `bkr_int02_recareabar`, `ba_*_lower_bar`; `prop_ff_counter_01` is fine. A script (a placer, a shop) can only use them as
  **our own copies**. Their texture dictionaries DO load anywhere (`RequestStreamedTextureDict('ba_int01_shell_txd')` = true).
- Many interior counters have **no collision in the drawable** (the interior's static collision has it): `ba_*_lower_bar`,
  `ch_chint01_reception_desk`, `v_53_shop_till`. Others carry a `<Bounds>` BVH (`bkr_bar_bar01`, `bkr_int02_recareabar`).

## The pipeline (`tools/counter_kit/`)
1. `ydr_xml.ps1 -Mode export` the sources; `cw.ps1 tex <names> <dir> <preferred txds>` finds every texture a shader names (the
   archetype's txd first, then every ytd, then drawables' embedded dictionaries) and writes the .dds. One ytd per style
   (`cw.ps1 ytd <folder> <out.ytd>`): textures once per style instead of embedded in every module.
2. `rsx.py` reads the XML into arrays per vertex component (keeps every layout, Rockstar's shader block verbatim), and can:
   `clip` by any plane (Sutherland-Hodgman per triangle, every attribute interpolated: UVs, colours incl. tint-palette indices,
   tangents), `transform` (a reflection re-winds triangles and flips tangent w), `merge`, write the XML back with box collision or
   with the source's own `<Bounds>` moved (`rockstar_bounds`).
3. `counters.py`: the **module frame** for a set: run along +X, patron side -Y (GTA's front), back edge of the top y = 0, floor z = 0.
   - **Straighten first.** `bkr_bar_bar01`'s long leg is 0.278 deg off square (its profile drifts 4.9 mm per metre): measure the
     front edge at several sections and turn the source by that before cutting, or the faces of two modules never match.
   - **Straight**: a slice of the run. **Outside / inside corner**: two slices of length D (the depth), the second turned +-90, both
     clipped on the square's diagonal (a picture-frame mitre: every layer of the profile meets on that line). **End**: Rockstar's own
     closed end when it has one; where the bar stood against a wall (open end), a stretch of the run closed by the run's own front band
     turned 90 deg and mitred at both corners (`end_band`). **Compose**: pieces of the run put together (the island's waterfall end).
     **Extras**: a box of the run copied into modules (a steel table's legs at each straight's end).
   - **Cut only where the profile is plain.** Scan sections along the run against one reference (`section_gap`): the cupboard
     counter differs where its handles and door seam are, the nightclub bars at their brackets. Put every joint face in the plain parts.
   - **Weld the joint faces** onto one canonical outline (vertices within 6 mm snap to its vertices, else onto its segments): a
     rounded trim's facets cross two cuts at slightly different points (3.7 mm on the After Hours trims).
   - **Collision by the same recipe**: each profile box is a little mesh run through the same slices, turns and mitres, then boxed,
     so a corner's collision is an L. Interior pieces without collision: `auto_boxes` (5 cm grid: a top slab where an upward face is
     above 0.6 m, solid from the floor where anything crosses 0.1-0.6 m, runs merged).
   - **The joint check gates the build**: every open face of every module against the straight's, outline to outline (segments,
     not points); 1.5 mm limit (4 mm on the faceted trims). A corner's other leg touches the face plane only along the mitre's edge:
     leave a 12 mm band there out of the check.
4. `counters_out.py` writes the ydrs (CodeWalker import), the ytds, a json with every archetype + joints, the placer's joint table, the
   shop rows, and a textured preview sheet (`rsxview.py`, a numpy rasteriser: check cuts and seams before anything goes in game).

## What only showed up in game (rig, 2026-10-25) - check these on every new streamed prop
- **Collision ignored with an empty `physicsDictionary`.** The ydrs carried their box collision (CodeWalker read it back) and still
  rays and a walking ped went straight through, Rockstar's own copied BVH too. With `physicsDictionary` = the archetype's own name
  (and the kit's flags 537002016) every piece is solid. Prove it: a down-ray grid over the bbox (`StartExpensiveSynchronousShapeTestLosProbe`,
  flag 16) must hit the entity, and a ped walked into the counter must stop (it stops 25 cm before the top's front edge).
- **Tint palettes.** `*_tnt` shaders colour from a palette row chosen by the ENTITY's tint (interiors set it per entity / entity set;
  the clubhouse bars are entity-set colours). A script-spawned object has tint 0, and some palettes keep a cyan placeholder in row 0
  (`int_02_bar_wood_pal`): copy the wanted row into row 0 of our own copy of the palette (`counters_out.palette_row`,
  `tools/counter_kit/tints.ps1` finds the tints Rockstar uses where it can).
- **Catalogue text limits.** C9 DJ cuts shop labels at 40 characters and descriptions at 140: the build now refuses longer text.
- **An end made by turning the run's front band** works for a one-sided profile with nothing at the back; with a back structure
  (the clubhouse bar's low shelf box) the back corner's mitre left an open slanted cut. Use Rockstar's own closed piece instead
  (the pedestal at the end of the bar's short leg): only the top must match across that joint.
- **Re-snap after a rebuild.** A placed piece keeps its pivot; if a module's length changes, move it again (the snap fixes it).
- **Aiming the laser from a script** (rig tools `tools/counter_kit/rig/`): point the gameplay camera at the floor point every frame
  from the camera's own position (`aimplace.sh`), in first person (`FP=1`) when the target is behind the ped, or the ray hits the
  player's own body. The tablet restores the heading it had when it was opened: close it, turn the ped, then open it.

## Joints and snapping
A joint = the floor point under the back edge of an open face + the heading out of it + its hand (right face / left face). Two
modules join when a left face sits on a right face with opposite headings: the back edges then line up, so any profile (one-sided
bar, island, table) meets itself. Never offer right-to-right (it would put the piece on the wrong side). Full-size copies keep their
Rockstar pivot in x / y but get the floor at z = 0 like the modules, so their open ends (the clubhouse bars' long legs) take modules.

## What it made (C9 DJ)
8 styles x 6 modules (two straights, outside + inside corner, left + right end): clubhouse grey wood, clubhouse cream, After
Hours traditional / edgy / glam, steel cupboard counter, stainless prep table, granite kitchen counter; 13 full-size copies (4
clubhouse L-bars, the 3 After Hours bars, the granite island, 24/7 checkout, casino gift shop counter, casino hotel desk, lobby desk,
office reception). 61 archetypes, ~12 MB of streamed files. Proven at Tower City Grill: an L-bar built from snapped modules (every
joint within 1 mm of the computed pose), the full clubhouse L-bar with a module snapped onto its open end, a station on a counter top,
a dropped bottle resting on it, a ped stopping at the edge, C9 Props photos of all 66 new shop rows.

## Rejected (and why)
`ex_office_01b_bar01` is only three loose top slabs; `prop_display_unit_01` a hat trolley; `v_9_kitchen_unit` an unfinished-looking
frame; `prop_food_bs_soda_02` / `cb_soda_02` are soda machines, not counters; `ch_chint02_counter_derelict` is a wrecked arcade
counter; anything with a wash basin (washrooms) was skipped.
