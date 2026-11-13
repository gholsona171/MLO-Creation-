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
- A decal's size on the body = its scale (a 0.1 marker covers 0.1 of the grid). +uvPos.y moves a decal UP the body.
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
- Hands (arm zones, HAND_LEFT / HAND_RIGHT references MP_Security_Tat_019 / 020): back of hand runs uv.y ~0.30 (wrist) to ~0.20
  (knuckles); fingers only take a thin band near ~0.15-0.17 (finger UVs are tiny islands), so a hand piece can't run bones down
  the fingers. The tattoo blend is also low resolution on the hand: fine bone detail reads as soft stripes.
