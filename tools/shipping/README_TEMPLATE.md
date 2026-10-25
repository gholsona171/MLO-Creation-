# <Map name> (FiveM map)

<One paragraph: where it is (streets, x / y), what it replaces, what is inside.>

| Folder | What it is | Needed? |
|---|---|---|
| `<resource>` | The map | **Yes** |

## 1. Install

1. **Check for conflicts first.** Run this from your server's `resources` folder (before or after installing):

       powershell -ExecutionPolicy Bypass -File .\<resource>\tools\check_conflicts.ps1

   It reads files only and changes nothing. It reports:
   - **SAME FILE**: another resource ships a Rockstar file this map also replaces. Only one copy loads, so you get holes,
     missing roads or old buildings showing through. Remove that file from the other resource (or the other resource), or keep
     theirs and not this map.
   - **same area**: another resource replaces a different Rockstar file in the same block. Usually fine, but check that area in
     game.
   - **scripts that use the area**: a script loads an interior / IPL here (e.g. an IPL loader). See section 5 for what this map
     already turns off for you.

   It can't see another MLO placed at the same spot under different file names. Check around <streets>, x <x> y <y> by hand.
2. Copy `<resource>` into `resources`, and add `ensure <resource>` to `server.cfg` after its dependencies (<deps>).
3. **Restart the whole server.** A map's streamed files only load cleanly on a full restart.

## 2. Settings (`<resource>/config.lua`)
<Every switch with its shipped default, and what it does.>

## 3. Access / locks
<If any: how checks combine, full identifier examples (`license:...`, `discord:...`, `fivem:...`), where to copy them
(txAdmin, Players, the player, IDs), and the empty-list trap.>

## 4. Render targets / TVs
<If any: model, target name, texture name, how to plug in another TV / DUI script, the busy flag, the one-target-per-model limit.>

## 5. Rockstar files replaced, IPLs kept off, water
<Which files and why they conflict; which IPLs the map keeps off; the water map rule if it ships water.>

## 6. Data files for other scripts (`mlo-data/`)

## 7. Troubleshooting
| You see | Cause and fix |
|---|---|
| Holes, missing roads, old building showing | A file conflict: run `tools/check_conflicts.ps1` |
| Map looks broken after `restart <resource>` | Do a full server restart |
