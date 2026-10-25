# 02 · MLO structure — the rules the engine enforces silently

## Rooms and portals
- **At most 31 rooms + limbo per MLO.** The room id lives in 5 bits of the collision material. Group small spaces into one room
  (a bedroom and its en-suite can share an id; stalls and closets too).
- Room ids must run 0..n without gaps.
- Portal corners: the winding normal points INTO `roomTo`. Every window bay needs a limbo portal or you see nothing outside.
- A wall section with no geometry between two rooms shows as a floor-to-ceiling "sky strip" seam. When a partition stops short of a
  core or corner, add the missing piece as its own partition (Tower City spa: the stretch beside the lift core was missing).

## Collision
- **Embedded bounds in an MLO entity never collide.** Interior collision is a separate static ybn listed in the manifest's
  `Interiors > Bounds`.
- **The interior ybn must be in MLO-local coordinates** (the lot frame), not world. A world-frame ybn lands ~190 m away.
- Glass gets no useful collision (flag 64 does nothing); use a thin invisible box if a pane must block.
- Shape-test material hashes are not joaat of the material name.
- **A drawable's own (embedded) collision loads only when its archetype's `physicsDictionary` names it** (set it to the model's
  own name). Left empty, the model draws but rays, peds and cars pass through - found 2026-10-23 on the wow2easy roadside sign, asphalt
  lot, junkyard wall and gates (a box test: same ydr, empty -> no hit, own name -> hit). Probe every new collider in game.
- **Merge collision per room: one `BoundGeometryBVH` child per room, never one per box.** Sollumz
  `convert_objs_to_single_composite` makes one child per Blender object, and the game appears to spend one physics instance
  (phInstGta pool, 16384) per child: Tower City's thousands of one-box children went with the "phInstGta Pool Full" crash.
  Rockstar's interiors have 3-47 children. Before the composite, join every collision object of a room into one mesh and give it
  fresh collision materials per (room id, flags) - e.g. one plain + one FLAG_STAIRS - with `m.update_tag()` (see the RoomID rule
  below). Tool: `tools/merge_cols.py`. Residence floors 2026-10-23: 3,446 boxes -> 22 children (one per room).
  PROVEN 2026-10-23: merging all of Tower City (about 7,500 children -> 75) stopped the crash: the lift ride that crashed at the
  lobby stop and 4 of 4 noclip flights across the map ran with 0 pool errors. Put the merge inside the shared export step so
  every build gets it, and after a big merge rebuild every lot that uses the shared kit and run its clash sweep (a kit change made for one lot can surface overlaps in another).
- Probe with real floats: in Lua 5.4 `2395` is an integer and a shape-test native reads it as a garbage float (every ray "misses").
  Write `2395.0` or add `+ 0.0`.
- **The interior collision ybn must carry the MLO archetype's own name** (`<mlo>.ybn`). Any other name: the interior loads
  (`IsInteriorReady` = 1) but nobody is ever inside it.
- **Check the shipped ybn's RoomID, not the Blender value.** Run headless, Sollumz exports Blender's *evaluated* copy of each
  material. A `collision_properties.room_id` set from Python after import stays 0 in the file until you call `m.update_tag()` +
  `bpy.context.view_layer.update()`. Symptom: `GetInteriorFromEntity` = 0 standing on the floor, and since room props draw only
  when you are in the room, "all the props are gone". Verify: CodeWalker `YbnXml.GetXml` → every `<RoomID>` in `<Materials>` ≥ 1.

- **Out of room ids? A second MLO at the same origin.** A 31-room MLO that is full gets a sibling MLO for new floors (same lot
  origin, heading and z, its own ytyp registered with `DLC_ITYP_REQUEST`, its own `<mlo>.ybn`). Put floors linked by an internal
  stair in ONE MLO so the stair is one room through them. The two MLOs' boxes overlap; the room id in the collision under the
  player decides which interior he is in (verify `GetInteriorAtCoords` on the rig).

## Metadata
- The MLO's `itypDepArray` must list the ytyp of **every** prop placed in it. Build it from a survey (`find_arch_ytyp.ps1` →
  `arch_ytyp.json`) and fail the build on any unknown prop. A hand-kept list once missed `int_residential` and the tables never streamed.
- **Exterior archetypes never go in the INTERIOR_DATA ytyp** (they silently don't draw).
- Plain entity rotation quaternion = the conjugate of the intuitive one: (0, 0, -sin(h/2), cos(h/2)).
- **Stale archetype bounds** → blue sky / missing walls at certain camera angles. Recompute bbMin/bbMax from the exported geometry
  before every compile.
- Added room entity lodDist ~300–600; props 80–150.
- **Register every custom prop ytyp with `data_file 'DLC_ITYP_REQUEST'`.** A plain ymap pulls its custom ytyps in on demand; an
  MLO does not. Entities whose archetype isn't registered are silently skipped (`IsModelInCdimage` = false). Converting a prop-ymap
  shop to an MLO made every custom prop and door vanish until this was added.
- **An MLO room drawable needs `textureDictionary` set if its textures live in a ytd.** With it null, non-embedded textures bind to
  whatever was bound last (walls rendered with the floor's marble). The same goes for an exterior skin sharing the shell's ytd.
- Some door props are never instantiated as MLO entities even with an identical archetype and flags to one that works (wow2easy
  junkyard: the bay roll-up `rocky_door113`). A roll-up door sitting in an outer-wall opening can be a plain exterior map entity
  instead; keep its portal.

## Hiding vanilla buildings and LODs
- Hide a vanilla LOD by swapping its archetype for our own empty model in our ytyp (not lodDist 1, not a .ydr stand-in).
- Exterior lights of removed buildings fade at 60 m: remove their LOD lights too (`l0_lodlights.py` in Tower City).
- **Swap a LOD whose every descendant is gone - in EVERY ymap, the road ymaps included** (Tower City, 2026-10-24: "dark props
  floating in the air from far away, gone when you get close"). The removed roofs' AC units, masts and dishes were HD children of
  the ROAD ymap's prop-combo LODs (`dt1_props_combo0412_06_lod` ...), which the level-0 rule never touched ("road LODs stay"): the
  HD went, the LOD kept drawing them at distance. Rule (l0_maps.py): walk each LOD / SLOD1's descendants (parentIndex points into
  the `<parent>` ymap; a LOD's SLOD1 sits in the same ymap); all removed -> swap it to the empty model. Leaves you have no copy of
  count as kept (conservative). A LOD/SLOD1 with only SOME descendants removed keeps its entity; cut its MODEL by the lot outline
  instead (l0_cut_lod.py on the district dictionary that holds it - find it with `arch_dict.ps1`, the archetype's
  `drawableDictionary`). Tower City: 70 LODs swapped, 6 prop-combo SLOD1 / LOD models cut.
- **A vanilla piece you MOVE must move in its LOD and SLOD models too** (Tower City driveway pillar, 2026-10-24: moved 12.3 m in
  the HD deck model, but from a distance the deck's LOD and the SLOD1 over it still drew the column at its old spot). Swapping the
  LOD to an empty model would drop the whole deck at distance, so apply the same move rule to the LOD models: find the LOD entity
  (the HD entity's parentIndex into the `<parent>` ymap; its archetype is often only a hash, e.g. `hash_D50B466A`), find its
  drawable dictionary with `arch_dict.ps1` (matches hash names too: here `dt1_rd1_r1f_slod1_children.ydd`, not yet in our LOD
  folder - extract it with `extract_by_name.ps1`), and move the same faces there (LOD materials are the HD names + `_lod`; an SLOD
  has one material, so select by position + |normal z| <= 0.5). A LOD whose HD model is exempt from the lot cut must not be lot-cut
  either. Tower City: the move rule's `lod` entries in `ext_plan.py`, applied by `l0_cut_lod.py` (`ext_rules.apply_lod`); the build
  fails unless the expected face counts moved.
- **See a LOD up close: `OverrideLodscaleThisFrame(s)` every frame** (a thread) makes the game pick lower LODs near the camera - far
  views of a spot under a deck are always blocked by something. Distances scale by s: with 0.08 a 145 m HD fades at 12 m and its
  400 m LOD draws to 32 m; with 0.04 the SLOD1 shows. Same camera, three shots (normal / 0.08 / 0.04), before and after
  (`tc_ext_final.sh` i4). The before showed the ghost column fading in at 0.07-0.09.
- Find a floating thing's position from two or three screenshots: set a scripted camera, then `GetScreenCoordFromWorldCoord` on a
  3 m grid of candidate points and keep those landing on the thing's pixel in every view (the rays cross at the thing).

## Stairs
- 0.20 m rise / 0.27 m going, ramp collision under the treads. Size the stair first, then build the shaft around it.

## Windows
- Each window bay = a real hole in the shell + a reveal + one glass pane in the face plane + a limbo portal. Two glass layers close
  together flicker (draw-order swap); keep one.

## Mirrors (real reflections)
Copied from the Diamond penthouse (`vw_dlc_casino_apart.ytyp`, its bathroom mirrors):
- The mirror surface is a flat panel with shader **`mirror_default.sps`** (white diffuse + white spec, specularIntensityMult 1,
  render bucket 1). Glass shaders and vanilla mirror props on their own render grey or black.
- Each mirror gets an MLO **portal from its room to limbo (room 0)** whose four corners are exactly the mirror rectangle, on the
  mirror's plane, winding normal pointing into the mirror (away from the room). **Portal flags 260** in Rockstar's bathrooms
  (4 = mirror, + 256); 4 alone on a lounge mirror; 1284 on another bath. No attached objects.
- Rockstar's mirror entity uses entity flags 1572864; a community guide quotes archetype flag 8192, entity flag 559415298 and portal
  flag 1284 — verify on the rig, the Rockstar values are the reference.
- The game renders one mirror at a time (the nearest visible); keep mirrors where players look into them.
- **Merges are for COLLISION only.** The per-room collision merge (above) joins invisible bound pieces; it must never join visible
  models. Never merge a mirror (or any prop) into a room drawable to save entities: a mirror inside the model that holds it reflects
  nothing (next rule). After any merge, look into one mirror in game.
- **The mirror must be its own entity.** The reflection skips the entity that holds the mirror surface. Our first mirrors were
  part of the room shell, so the reflection showed the room's props floating on black (flag 4) or on sky (260 / 1284). Rockstar's
  mirror is a separate archetype (`vw_vwint02_pent_*_mirror`), and so is ours now: `tc_prop_mirror`, a 1 × 1 m panel placed with
  scaleXY = width, scaleZ = height (MLO entities take separate XY and Z scale). Portal flags 4.
- Test with the ped standing at the mirror: `tc_mirrorflag.sh <flags>` re-runs only the metadata (no Blender) for flag experiments.
- **A reflection draws only the mirror's own room - every opening in front of the mirror reflects BLACK** (Tower City salon /
  barber / dance studio, 2026-10-24: the mirrors on the back walls faced the shop windows, the shopfront and the doorway onto the
  gallery - another room - and showed black patches exactly there). Mirrors are portals into a mirrored copy of the room; portals
  out of the room are not followed. So put the mirror on a wall whose half-space in front holds only solid walls of the same room:
  e.g. a full-width "mirror wall" across the shop (open at both ends) with the mirror on its back face, the reception and the
  shopfront behind it. Anything behind the mirror's plane (the doorway, the windows, the wall's own end openings) is never
  reflected. Proven offline by reflected rays (Tower City `work/mall_gap_check.py`, pass 3: eye points on the floor, every ray
  reflected off the mirror must meet a face of the mirror's room before any portal).

## A wing of an existing building as its own MLO (Tower City parking, 2026-10-23)
- A wing with its own use (the podium's parking decks) is a separate MLO at the building's origin, like the residence floors:
  its own ytyp (`DLC_ITYP_REQUEST`), its own `<mlo>.ybn`, its own timecycle (`carpark_dt1_03` for parking).
- **Line every outer-wall face inside the wing with the new MLO's own geometry** (a 0.2 m lining per room). The building's
  exterior model draws its inside faces only through a portal: from inside an MLO room they are simply not there.
- Openings in the outer wall: cut the hole in the exterior model's wall (and leave out any fake window it crosses), add the
  same hole + arch to the lining, and put the portal on the **room side of the lining** - the exterior's reveal then lies beyond
  the portal and is drawn through it. A portal on the outer face leaves the reveal on the room side, where the exterior is not
  drawn (void reveals).
- Ramps between decks: a smooth profile (parabolic vertical curves of 4 m at both ends, <= 1:7 between); the slab over the ramp
  opens where the headroom drops under ~2.6 m. The air over the ramp belongs to the ramp's room: portals on the guard parapets'
  middle lines link it to the upper deck.
- Check the facade grid from the numbers, not from memory: the podium's pilasters were at -70.25 + 7.5 k, not where assumed.
  Put an opening inside one pilaster bay so no pilaster is cut.

## Cutting vanilla models by their own polygon (footprint cuts)
- The level-0 lot cut removes faces inside the lot outline. Where the outline takes in something that must stay (a freeway
  ramp along the lot edge), cut the model by **its own polygon only**: Tower City `plan/footprint_cuts.json` (model -> world
  polygons, written from the plan module) is read by `l0_cut.py`; models listed there ignore the lot outline.
- Prove it with a dry run (`l0_cut.py -- --dry <models>`: dead / kept counts + every dead face centre) and check every dead
  centre lies inside its polygons before cutting for real.
- The lot cut also removed collision you may still need: a freeway barrier's collision on the lot edge was cut while its
  drawable stayed (a barrier you can drive through). Probe the cut collision along every edge a car can reach.
- Joining a new road to a vanilla one: take the join line and heights from the vanilla **visual** vertices (a polyline that
  follows the road's vertical curve - a straight fit was 2 cm off) and start your **collision** where the (cut) vanilla
  collision stops (it ended 0.35 m short of the visual edge). Then there is neither a visual seam nor a collision step.
- A lot slab built from measured edge heights: replace outliers one at a time, worst first. A one-pass median filter let three
  edge points sitting on a raised freeway pull true ground points 2.3 m up (a cliff at the parking's doors).

## Ground around a building: lots, cuts and blending (wow2easy junkyard, round 7, 2026-10-23)
Five ground defects at one garage, each from a different source step - check all of them on every new lot:
- **Cut along the outline before deleting by centre.** A rule "delete the vanilla ground face if its centre is inside the lot"
  on Rockstar's 2-7 m terrain triangles deletes triangles that stick out past the lot's edge: holes in a strip beside the lot.
  Split (bmesh `bisect_plane`) along every edge of the outline first, then the centre test is exact.
- **The lot's hole is the building's FLOOR outline, not its outer walls.** The lot stopped on the walls' outer faces, the
  interior floor collision starts on their inner lines: a 4-6 cm slit with no collision under every door. Run the lot under
  the outer skins to meet the floor. Same for a door-hole cut: keep the floor faces in the cut box (a cut from 1 cm under the
  floor took the floor out of the doorway - an 11 cm slit under the front doors).
- **A space you call "office" may be an open porch.** A rect left out of the lot "because the building steps out there" was a
  porch: no blacktop, and the porch slab's collision had been dropped with the slab - a fall-through under the porch roof.
- **"Not a ground material" is not "wall".** Removing an old wall's collision by "non-ground material within 0.9 m of the
  line" also took the yard's CONCRETE floor beside it: holes along both sides of the new wall. Never remove a flat face that
  lies on the ground (up-facing, within 0.4 m of the ground height).
- **Blend a lot's edge with graded ground, in the drawn terrain AND the collision, from one function.** `lot_plan.apron_z`:
  around the blacktop the ground is held between a fill bank and a cut bank measured from the NEAREST edge (1 m shoulder 1 cm
  under the edge, rounded crest, then 1:3), plus 1:3 cones from the ground near the lot (an old pad's 2 m drop behind a ridge).
  `ground.py ground_z` gives the same height to the drawn sand (`terrain.py`) and the collision (`site_col.py`); both first cut
  their triangles on the outline and a 1 m grid where the grading reaches; moved / new vertices get normals from the new shape.
  Never grade inside the client's yard. Overlay layers (hard surface, decals) are not moved - the graded sand covers them.
- **Drape a lot on its own ground.** The lot's height grid sagged 0.4 m at a corner: nodes on the plan's boundary got no
  height and were filled from the cliff below, and the "pole" median filter took the pad's own corner for a pole. Keep plan
  nodes exact (boundary included), never filter them, fill dips under the blacktop (it may not fall faster than 6 cm/m), and let
  ground BESIDE it only lift its edge (ground higher than the edge), never drag it down (the apron fills lower ground).
- Where the lot runs into a gateway of a yard that must not change, ease the lot down to the yard's ground (2 m taper).
- Vegetation the bank buries by more than 0.5 m goes (`site_clear.py` `buried`); shallower bushes stay.

## Hairline cracks in reshaped ground (wow2easy junkyard, round 7 seams, 2026-10-23)
Antonio: "very thin lines in the perimeter, like it did not meet". The collision was closed (hole grid clean) - these were in
the DRAWN ground, so only a drawn-mesh check finds them (`wow2easy_move/tools/crack_check.py`).
- **A 1 cm step at an open mesh edge reads as a crack.** The sand shoulder sat 1 cm under the blacktop's open edge. Seen low
  across the edge, that 1 cm slot looks under the blacktop into its shadow, and shows as a dark, sky-coloured line. Make the
  meeting edges coincide: the shoulder exactly at the edge's height, and the sand cut at every node of the blacktop's edge.
- **Rockstar's terrain is one mesh per material, so every material seam is a pair of duplicated edges.** Cut only "the faces
  that move" and a seam edge gets cut on one side and not the other. That is a T-junction, and once grading moves the vertex it
  becomes a crack. Cut EVERY face across each line within the grading's reach (both terrain models, same rule, so their shared
  border is cut alike). Then split every edge that still has a foreign vertex lying on it (`terrain.py close_t_junctions`).
- Keep the blacktop's height straight between the sand's nodes. Along integer grid lines the lot's bilinear height is straight
  between 1 m nodes. An eased taper (the gateway) is not, so the sand needs a node at every one of the blacktop's 0.5 m nodes.
- Cut the collision on the same grid as the drawn sand, or the drawn and walked banks part by up to 10 cm at creases.
- crack_check reports T (a vertex on another edge's inside, 1 mm-2 cm off it, that no other edge meets) and G (an open edge no
  other edge meets within 2 mm / 3 mm). It leaves out the decal feather, ground under the blacktop and the wall's foot. It lists
  open edges Rockstar ships himself (found in his unedited model) apart and does not count them. Proven on the known crack: the
  deployed build gave 908 T + 501 G, including the west-edge line.
- **A collision BVH child holds at most 32,767 primitives** (Sollumz refuses to export more). Fine cuts in Rockstar's ground
  pushed one child to 38,000. Don't cut under the blacktop (it's hidden and never graded). Split an oversized child into
  sibling BVH children by x (`site_col.py split_bvh`) - his own files have several children each. A failed export leaves the
  OLD file in place, so read the build log for `Error exporting`, not just the file count.

## Removing vanilla: long collision boxes and removed interiors (Tower City, 2026-10-23)
Two ways vanilla collision survives a lot cut and blocks cars with nothing visible:
- **Long box primitives.** Rockstar's plaza edges / kerbs are single boxes up to 100 m long. Judging a box by its centre misses
  one whose centre lands in a notch of the lot outline. Sample the box's footprint instead: all inside -> delete; partly inside
  -> triangulate it, BAKE its transform into the mesh (`ob.data.transform(ob.matrix_basis)`, identity basis, then
  `view_layer.update()` - the cut planes assume no scale and `matrix_world` is stale until updated) and cut it like triangles.
  Cut our own building / bridge outlines in every collision file, not only the lot outlines.
- **Removed interiors still collide.** Deleting a vanilla MLO instance from its ymap does NOT remove its collision: the
  interior stays registered (GetInteriorAtCoords still returns it, IsInteriorReady false) and its static bounds - the ybn named
  after the MLO archetype's physicsDictionary (find it by Jenkins hash in the RPFs) - keep loading. Ship that ybn emptied
  (Tower City: l0_maps writes work/l0_mlo_gone.json, l0_col empties those). Only for interiors unique to your block: shared
  ones (CEO offices, import garages) are used by other buildings.
- Find such walls in game with horizontal rays per shape-test flag (only flag 1 hits = map), then
  `DisableInterior(GetInteriorAtCoords(...), true)` as a diagnostic: if the ray clears, it is the interior.

## Clearing the EDGES of a cleared block (Tower City exterior review, 2026-10-24)
A lot outline traced at the kerb keeps everything outside it - including the old building's pieces that stood outside it. The
owner found them all from the street: a car-park entrance block (PARKING letters, mesh gates, a louvred vent wall) standing in
front of the new portico, a road branch on a freeway deck running into the new facade, a deck pillar with no collision in the new
garage's driveway. Rules (Tower City `work/ext_plan.py` -> `plan/ext_cuts.json`, applied by `ext_rules.py` inside l0_cut / l0_col):
- **Walk the outline from the street before building.** Anything of the old block's own models (`dt1_11_*`) left outside the lot
  is a leftover. Find which model draws a thing by hiding candidates one at a time (`CreateModelHide(x, y, z, r, hash, true)`,
  screenshot, `RemoveModelHide`) - the PARKING block was the plaza model's part outside the lot, not a "parking" model.
- **Zone rules, not a bigger lot**: per zone a polygon + height band (+ a material regex) and the models it applies to (regex).
  A height band lets a deck-level zone leave the street under it alone; a material rule (`road|marking|damage`) takes a drive's
  tarmac and paint and leaves its kerbs and planters. Models that only need zone rules (the freeway structure, the street model)
  are flagged `ext_only` so the lot outline never cuts them.
- **Close a cut road with Rockstar's own edge**: the deck's west edge across the removed branch mouth is the sidewalk + kerb +
  barrier of the straight stretch beside it, CLONED (faces in a source box copied with a shift, clipped to the gap) - drawable and
  collision by the same rule. Pick a source stretch with no dropped kerb (probe it). Cloned / moved faces are protected from every
  later cut (a bmesh face layer), or the lot cut eats them again.
- **Moving a vanilla piece** (a pillar in a driveway): split its faces (material regex: never the cap beam over it), shift, stretch
  the top to the deck soffit if the new spot has no cap; its collision moves by the same rule (walls only: `col_nz_max`, below the
  cap). Keep it on the same structural line (the deck edge) and well clear of the doors' turning paths.
- **A zone rule's edge leaves whatever overhangs it.** The PARKING block's cut stopped at its south wall face; its louvre ledge and
  roof-planter lip stuck out 0.95 m past that and stayed, floating, as "dark wedges" in front of the new facade (reported as the
  portico entablature's end - it was not; ray the pixel before blaming the nearest new model). Dump the triangles 0-2 m beyond every
  zone edge (`tri_dump.py`, per material) and add an overhang zone with a height band that spares what sits under it (planters).
- **A kept vanilla piece next to a cut must end on structure.** The planter island beside the removed branch had been carried by the
  old building; with it gone the island hung 2.5 m past the deck fascia. Cut it at the deck-edge barrier's inner face, run the
  cloned barrier + fascia (and the barrier's collision) on beside it, and fill a curved gap (a rounded kerb leaving asphalt beside
  the new straight kerb) with the cloned sidewalk clipped to a polygon along the kerb's foot line (Rockstar's own gutter vertices).
  Clone clips may be any simple polygon: bisect along every edge, keep faces whose centre is inside.
- **What a removed piece hid**: the branch deck covered the old car park's down-ramp pit (to z 15.9, drawn only by the removed
  interior). Probe the ground under every piece you remove (rays down per 1 m, collision + material) BEFORE cutting it; close
  pits with ground at the neighbours' height.
- **New paving that meets kerbs exactly**: copy the removed tarmac's own BASE triangles (the material that tiles the drive; patches,
  damage, dirt, blends and paint are overlays on top of it - copying them all clashed) 12 mm up as the paving. Then it meets every
  kerb and planter with no gap and no overlap.
- Paving over a drive mouth stays flush with the street: bollards on the mouth line make it plaza, not a driveway.
- Switch the zones' AI off in script (`area_clear.lua` OFF_ZONES: roads in an angled area, ped paths in 1.5 m tiles - an axis box
  around an angled zone switches off the neighbouring sidewalk too, a navmesh block only beyond the new edge).
- Remove occluders over every zone too, and test triangles by overlap (21 points + corners), boxes by a 5 x 5 footprint grid:
  centre-only tests miss big pieces that span an outline (`l0_occl.ps1`, every `*occl*` ymap near the lots, best-ranked copy).

## The lot slab's edge (Tower City, item 6, 2026-10-24)
- A slab draped from heights at its outline's CORNERS only is a straight line between corners up to 99 m apart; the sidewalk
  beside it is not: on Alta St the slab stood up to 1.18 m proud of the sidewalk ("a tan ring hovering round the base").
- Sample the edge every 0.5 m at the ground 0.25 m OUTSIDE it (`lot_ground.py`): your own exterior paving where it is there, else
  Rockstar's unedited collision - the LOWEST up-facing surface from 2 m under to 0.8 m over the old line (a deck over the edge, a
  planter or hedge top never lifts it, a pit never drops it). Drape the inside on a 2 m grid from those samples (inverse distance,
  d^-3); never move an edge vertex; the skirt runs down the subdivided edge (extrude the boundary, not the original corners).
- ~~Give it the read of the sidewalk round it (light grey flags)~~ - not enough. Antonio, 2026-10-24: "either your sidewalk colour
  takes over the entire sidewalk, or you leave it to the base sidewalk colour - two different colours look crazy and patchy".
  Our ground outside the buildings IS Rockstar's sidewalk: copy his material from the road model beside the lot (shader
  `normal_spec_detail.sps`, its parameters, its sampler texture NAMES, textures NOT embedded - bind his road txd through the
  archetype's `textureDictionary`), his UV scale + direction (median metres-per-UV of his faces, aligned with the street grid) and
  his vertex colour 0 (inverse-distance mean of his nearest sidewalk corners). Tower City: `sidewalk_mat.py`, survey
  `tools/sidewalk_dump.py` (west lot dc_sidewalk001, east dc_sidewalk004, txd dt1_rd1_1). The only exception is a deliberately
  different plaza surface ending at a clean kerbed / banded edge.
  Two traps found on the rig: (1) his sidewalk texture is a STRIP texture - dc_sidewalk001 is 4 x 4 flags over u 0..0.9 plus a
  cobble / drain band at u 0.9..1 that he lays along the kerb; tiled over a wide area the band repeats every 5 m. Cut the paving
  every 0.9 tile across u and give each face u 0..0.9 inside its tile (the seam falls on a flag joint). Look at the texture first
  (extract it: CodeWalker DDSIO.GetDDSFile; a texture missing from the model's txd lives in a parent, e.g. globalroads.ytd).
  (2) Vertex colours: read and write `color_srgb` (what Sollumz stores in the file); `.color` is linearised and came out dark.

## Inside a lot there is ONE ground, and what you see is what you stand on (Tower City, Antonio's shots 71-81, 2026-10-24)
Waist-deep in the Power St sidewalk, knee-deep in a planter's lawn, dark jagged patches and a red kerb piece "floating" in our
paving, a hole beside the steps. All the same family: the drawn ground and the collision were cut by DIFFERENT rules.
- A drawable whose entity origin is OUTSIDE a lot is never swapped and only cut if it is in the cut list - but the lot cut takes
  the collision of EVERY file inside the lot. So Rockstar's street models reaching into the lot (sidewalks, old dropped kerbs,
  road overlays) stayed drawn on/under the slab with no collision (you sink into them, they poke through), and the planters / hedges
  we meant to keep whole lost their collision inside the lot (knee-deep in the lawn). Rules:
  * every vanilla STREET model reaching into a lot is cut by the lot (drawable) - find them all from the drawn set (below), not a
    keyword list; models cut only by their own rules (footprint / ext_only) also lose their street-level faces inside the lots
    (a z band, so decks over the lot stay)
  * every feature kept whole (planters, hedges, the freeway / off-ramp structure) keeps its collision: survey its drawn triangles
    inside the lots (`kept_features.py`) and protect the collision faces on them from every cut (`ext_rules.on_kept`, l0_col; a box
    primitive reaching one is turned into triangles first). A height rule ("road collision above z 34.5 stays") is not enough: the
    off-ramp's low end dips under it.
  * where our paving owns an area the lot slab has a HOLE there, and the slab's hole edge takes the paving's height (no two
    surfaces on one spot, no step between them).
- Gate: `tools/ground_check.py` - on the BUILT files, a 0.5 m grid round both lots, two looks (to z 50 for decks, to z 38.5 for the
  street under them): the TOP up-facing drawn face (every vanilla model round the lots placed like the game - `drawn_dump.py` from
  `near_entities.tsv` + the cut models + our exteriors) against the TOP up-facing collision face (every shipped ybn + every vanilla
  ybn round the lots the resource does not ship, `ybn_near_lots.ps1`). MISMATCH (> 5 cm, under 2.2 m - above that it is something
  you walk under), NOCOL (drawn, no collision), HOLE (inside our area: nothing drawn). It names the model and the collision file
  per cluster; `ground_probe.py u,v` lists every face at a point. Proven first on the deployed build: it found the waist-deep sidewalk
  (the off-ramp model drawn 1.3-2.2 m over the slab's collision), the knee-deep planters and the hole by the steps.
- A rule edge near a curved Rockstar kerb or a road whose kerb is at an angle: clone his kerb BENT onto the line you need (clone kind
  'bend', `ext_rules._bend`: the source strip is cut every 0.5 m across its line, copied along the target polyline - offset kept,
  heights shifted by the target's foot height). Used for the San Andreas deck's new west kerb (following the road's gutter line) and
  Power St's kerb across the old car-park mouths.
- Gate: `tools/slab_edge_check.py` (slab top 0.1 m inside vs the ground 0.25 m outside, every metre): proven on the old slab
  (116 + 27 points over 6 cm, worst 1.18 m) -> new slab 0 + 1 (a kerb crossing). After a re-drape, run the cross-drawable
  check: a building's ground-level ledge that sat 3 cm over a sagging slab is now coplanar with the true ground.

## Signs (Tower City signage audit, 2026-10-24)
- A sign is a panel 5 cm off a wall. Every one must lie on a free surface: not across a pilaster, a ceiling, a soffit, a frame, an
  opening (a sign over a doorway's void "floats"), and not taller than the band of wall it sits in (0.4 m over a door: 0.34 m sign).
  Centre facade / court signs in ONE pilaster bay (work the bay grid out from the numbers).
- Facing must be one of +u / -u / +v / -v: a helper that mirrors layouts (a-frame '+a') passed '+a' through unchanged on one side, and
  the sign routine read it as a v-facing panel: every north-side sign stood ACROSS its wall, through it ("CLEVELAND ... LESS").
  tc_kit.sign now asserts the facing.
- Where no wall carries a sign (over an opening or a stair foot), hang it: a backing board and two rods into the ceiling
  (`tc_kit.hanging_sign`).
- Check every sign offline against every triangle and prop: `work/sign_check.py` (CLIP / FRONT / VIEW / WALL / TEXT).

## Nothing floats (2026-10-24)
- Chandeliers under a glass vault hang from the vault's STRUCTURE: a rib at a purlin joint, a saddle clamped round the rib, the rose
  under it, a jointed drop rod. A rod ending under glass, or 9 m short of anything, reads as floating. Every lamp / pendant /
  chandelier / hanging sign / flag wire records its support point and direction (tc_kit.ANCHORS); `work/hang_check.py` casts 8 cm
  from each toward its support and fails on any that meets nothing.
- A glazed fan / end window: put every member (hub, spokes, concentric bars, rim) on ONE centre plane with distinct depths (no shared
  face planes), spokes on the rays from the hub from inside the hub to inside the rim, concentric bars as scaled copies of the rim
  line (they cross each spoke on its centre line), glazing bars on every pane joint. Bars in two different planes look detached.
- An underground room has no sky: a "skylight" of clear glass with nothing over it shows the void (sky, distant city LODs). Use an
  opaque backlit laylight (emissive panel in a frame) as part of the closed ceiling, and lights under it.

## Tenant floors inside one big room (Tower City upper floors, 2026-10-23)
- A big empty space that has to become many shops does NOT need a room per shop. With the MLO near the 31-room cap, the units are
  partition walls inside the one room (Tower City: each side's levels 2 + 3 = one room, 9 units + corridor per storey). Everything
  in the room is drawn together, so no unit can show void; keep one view portal per storey along the whole frontage (gallery ->
  room) instead of one per opening, and a mirror portal (flags 4) per mirror.
- Put corridor / partition walls that meet a street wall in the gaps between its window bays (work the bay grid out from the
  numbers first): a wall ending in a pane looks wrong from outside and cuts the window portal.
  Don't trust a plan to do it: Tower City's tenant floors claimed it and four walls still met the glass. Make the window layout
  read the partitions and put a stone pier wherever one lands in a bay (split the bay, drop pieces under 1.2 m), and check it.
- Partitions must TOUCH, never overlap: two boxes overlapping at a corner put two same-facing faces on one plane (a sweep clash).
  Give each corner square to one wall.
- Floor slabs meet at the walls' centre lines (no gap under a doorway, no overlap); ceilings the same.
- A stair through a ceiling: cut the hole in the lower storey's ceiling too and line the hole's ends between the ceiling and the
  slab (the first build left the level-2 ceiling across the stair: you climbed through it).
- Every metadata writer must pass portal `flags` through: east_meta.py dropped them, so a mirror portal would have been plain.
- Ambient people for new floors get their OWN life area (Tower City `shops`) with its own spot fill (`Config.AreaSpotFill`): the
  spot-ped cap is global, and spots built earlier in a script fill first, so 90 new upper-floor seats in the mall's area would
  have emptied the court's benches.
- Light-gap audit on floors that open onto a glazed court: a ray that leaves through a shopfront and out of the vault's glass is
  not a hole. Classify rays by where they cross the frontage (opening / window) before counting gaps (Tower City
  `upper_gap_check.py`: 10,602 raw "gaps", 47 left after that, all single rays grazing a bay edge).

## Room timecycle names must be lower case (2026-10-25)
CodeWalker hashes a room's `timecycleName` exactly as written; the game looks timecycle modifiers up by the **lower-case** hash. A name with any capital (`INT_mall`, `MP_casino_apartment_exec`, `int_GasStation`) silently gives the room NO timecycle. On Tower City every room except the all-lower-case `carpark_dt1_03` ran with none for weeks, so the night bloom fixes did nothing. Write `tc.lower()` in the meta writer and gate it with a test over the built ytyp XML. Check in game: `GetInteriorRoomTimecycle(interior, room)` must equal `GetHashKey(name)` (GetHashKey lower-cases). Try presets live with `SetTimecycleModifier` first; it uses the right hash, so a live test can pass while the built room still fails.
