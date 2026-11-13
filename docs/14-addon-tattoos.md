# Add-on tattoos (GTA V / FiveM, rcore_tattoos)

Learned building `c9_tattoos` for Cleveland RP (Nov 12 2026: two full sleeves, a chest piece, a back piece, front and back of
neck). Tools in `tools/tattoos/`; the full build lives in `C:\C9Test\rebuild\install\tattoos\` (`build.py` rebuilds everything
from the client's PNGs).

## Resource format
- One texture dictionary per tattoo in `stream/`: `<name>.ytd` holding one texture `<name>` (the overlay's `txdHash` = `txtHash`
  = that name). 1024 x 1024 DXT5 with a full mip chain works (Rockstar ships 512 DXT5 or A8).
- The overlay collection (`PedDecorationCollection`, `<nameHash>` = collection name at the end) and `shop_tattoo.meta` go in the
  resource ROOT (not in stream/), declared as `files` and:
  `data_file 'PED_OVERLAY_FILE' '<collection>.xml'` and `data_file 'TATTOO_SHOP_DLC_FILE' 'shop_tattoo.meta'`.
- One overlay `Item` per gender (`_M` / `_F` names, `GENDER_MALE` / `GENDER_FEMALE`), `type TYPE_TATTOO`, `zone ZONE_*`.
- rcore_tattoos: a list `assets/tattooLists/<X>.json` with `collection, hashMale, hashFemale, name, price, zone`, added to
  `Config.TattooLists`. rcore's id for a tattoo is `hashMale .. '-' .. hashFemale`. The tattoo resource must start BEFORE
  rcore_tattoos (explicit `ensure` above `ensure [rcore]`).
- Proof without clicking the shop: server `TriggerEvent('rcore_tattoos:buyTattoo', src, name, hashMale..'-'..hashFemale, false, 1, cb)`
  (charges the list price, saves to `rcore_tattoos`, rcore applies it); `addPlayerTattoo` does the same without charging.

## Finding Rockstar's reference values
`tools/tattoos/scan_overlays.ps1` extracts every `*overlays.xml` and every `shop_tattoo.meta` from the install (and named tattoo
ytds). The shop meta's `updateGroup` names the body area (`ARM_RIGHT_FULL_SLEEVE`, `ARM_LEFT_FULL_SLEEVE`, `CHEST_FULL`,
`CHEST_STOM_FULL`, `BACK_FULL`, `NECK_FRONT`, `NECK_BACK`...) and `eFacing` the side: join it to the overlay XML by preset name to
list every full sleeve / chest / back with its uvPos, scale and rotation. `tools/tattoos/ref_sheet.py` makes a contact sheet of
their textures. References used: sleeves `MP_Sum2_Tat_013` (right) / `MP_Sum2_Tat_049` (left), chest `MP_Luxe_Tat_012`
(collection `mpluxe2_overlays`), back `MP_Luxe_Tat_022`, front neck `mpHeist3_Tat_014`, back neck `MP_Buis_M_Neck_003`.

## The decal space (measured on the rig with a UV grid + point markers, `build.py cal`)
- Relative to that calibration grid a decal's size = its scale (a 0.1 marker covers 0.1 of the grid). +uvPos.y moves a decal UP
  the body. Absolute numbers against the mesh UV channel are in the hands section below (they differ per axis).
- ZONE_TORSO: chest centre x ~0.73, spine x ~0.245, collar-to-belt ~0.33 tall. Female torsos sit higher: raise female uv.y
  (~+0.06 for a chest piece) or the bottom ends up under the jeans.
- ZONE_HEAD: throat x 0.5, back of neck x 0.0 (a decal there wraps the seam fine). The front of the neck is only ~0.12 tall
  (uv.y ~0.19 neck base to ~0.31 under the jaw); anything below the neck base is cut off hard, so fit neck art inside that band
  and fade its bottom edge.
- Arms: +uv.y goes toward the shoulder; +uv.x turns the decal toward the FRONT of the arm on both arms. Rockstar's full sleeves
  span ~0.32 of uv.y shoulder to wrist; centre ~0.5 = outer arm.
- Positive scale = not mirrored (text reads); Rockstar uses negative x scale only to flip art.

## Art
- Tattoo blending can only DARKEN skin: white / light grey on an opaque texture render as bare skin (the calibration grid's white
  background never showed). Highlights in a design = transparent ink; black-and-grey = alpha from ink density, colour near black.
- A drawing of a sleeve is a FRONT VIEW of a round arm: unroll it as a cylinder (output x_o samples x = c + r sin(x_o / r) per row,
  r and c from the arm outline) so the front covers half the circumference, and fade the sides where it wraps to the inner arm.
- Body mock-ups (art painted on a torso): alpha = how much darker than the local skin tone; find nipples / areolas by redness and
  fill them from the surrounding ink; erode the body outline ~10 px and feather it, or the mock-up's rim shows as a line.

## Rig traps
- After changing a tattoo ytd, reconnecting the SAME game process crashed it right after loading the overlay files
  (GTA5_b3258.exe+1792752, gta-streaming-five). Quit FiveM completely (drop the player, then end the processes and check they are
  gone), `refresh` + `restart` the tattoo resource and rcore_tattoos with nobody on, then start a fresh client.
- illenium-appearance re-applies the skin right after spawn and wipes decorations added by script before it: wait a few seconds
  after spawning before `AddPedDecorationFromHashes` checks.
- Photos: freeze the clock with a per-frame `NetworkOverrideClockTime` thread (weathersync resets a one-off call).

## Full-wrap sleeves, hands, closing gaps (Nov 13 2026)
- A sleeve decal can cover the WHOLE arm: make the texture one full turn wide (2 pi r at the arm's median radius) and centre
  the drawn front on the outer arm. The back / inside half is synthesized from the design's own background (clouds, smoke,
  ribbons: named source boxes per tattoo) by patch quilting with smooth windows, jittered positions and random flips, as a strip
  that is periodic round the arm so the inner-arm seam meets itself. Give the background columns ONE constant radius (not the
  per-row arm radius) or the narrow shoulder / wrist rows get bare wedges. Lay the background UNDER the drawing wherever the
  drawing has no ink (its own outline mask), or the drawing's pale paper edge shows as a light outline.
- The shoulder cap: add background-only rows above the drawing (12 % of its height) so the sleeve meets the chest / back.
- Chest / back pieces reach the neck base: grow the texture up (~27 % of the art height) and out at the top (10 % each side) with
  the design's own top background, feathered into the art; recompute uvPos / scale so the original art keeps its place.
- Hands: see the next section (the round-2 note that fingers can't be covered was wrong; it came from a wrong u scale).

## Hands and fingers: the real UV layout (Nov 13 2026, round 3)
Skeleton hands that run every bone down every finger. Tools: `tools/tattoos/ped_ydd_xml.ps1`, `mesh_uv.py`, `hand_tattoo.py`,
`hand_preview.py`.
- The decoration UV is the body mesh's **TexCoord1** (not TexCoord0). Export the base freemode drawable with CodeWalker
  (`ped_ydd_xml.ps1 -Names uppr_000_r -Ped mp_m_freemode_01`, same for `mp_f_freemode_01`; filter on `streamedpeds_mp.rpf\<ped>\`
  or you get DLC variants), parse with `mesh_uv.py`. Zone coords: x = u - 1, y = 1 - (v - tile); tile -5 = right arm, -7 = left
  arm (left = mirror, x -> 1 - x).
- The hand is unwrapped flat at the bottom of the arm zone: back of hand male y ~0.18-0.32 (wrist 0.322), female wrist 0.266,
  knuckles ~0.165-0.20; each finger is a strip hanging straight down to its tip at y ~0.015-0.02. Male right-arm finger centres x:
  index .415, middle .50, ring .58, pinky .677, thumb .31 (short strip). The palm side of the fingers is a small copy at
  x > 0.8 (right) / < 0.2 (left). Pick back-of-hand faces by blend bone (hand 42, thumb 43-45, index 48-50, middle 52-54,
  ring 55-57, pinky 58-60; left +29) and normal.
- **Overlay scale vs the mesh UV, measured with colour-coded line probes on the rig (arm zones):** v covers 2 x scale.y, not
  flipped; u covers 6.667 x scale.x and runs MIRRORED (texture left = higher u), wrapping every 1.0. So a texture laid out over
  zone box (x0..x1, y0..y1) needs uvPos = box centre, scale = ((x1-x0)/6.667, (y1-y0)/2) and the image flipped left-right.
  Getting u wrong squeezes the whole hand into ~0.1 of the texture, which is why round 2 looked like blobs.
- Resolution is fine once placed right (1024 texture over 0.64 x 0.36 zone): thin probe lines render crisp. Bold art still
  reads best: solid dark packing, black outline round each bone, light bone fill, dark seams at the joints.
- Finger art must be ~1.5x the width of the faces that point straight up, or bare skin shows down both sides of each finger.
- Warp: thin-plate spline from mesh joint positions (knuckle, PIP, DIP, tip, thumb CMC/MCP/IP) to the same joints read off the
  drawing; side points per joint; metacarpal mid-shaft sides so a too-wide mesh hand stretches the packing, not a bone; the
  drawing's wrist line at the top of the carpals; thumb base level with the other metacarpal bases (pinning it lower folds the
  art). Check folds with a warped grid over the source (`hand_preview.py`).
- Rig habits: full FiveM quit before reconnecting after a texture change; clear blood damage before photos; judge every
  iteration against the source art side by side at the same framing.

