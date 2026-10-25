# Tower City (FiveM map)

Tower City replaces the two blocks by Legion Square where the Maze Bank Tower stood, between Power St, San Andreas Ave and
Vespucci Blvd. It adds:

- **The mall** (east lot, around `71, -884`): three levels of shops and restaurants round a central court, the Eatery, and the
  Skylight Concourse.
- **The tower** (west lot, around `-79, -827`): the lobby, a casino level with the VIP Tower Club, and residence floors 98 to 100.
  At the top are the penthouse (two levels, with a swimmable pool) and the head office.
- **Underground**: parking P1 and P2 under both lots, the RTA station (concourse and platform), and the promenade that links the
  mall and the tower under the street.
- **Tower parking**: two decks on the tower podium, reached from the street and from the freeway off-ramp bridge.

The package holds two resources:

| Folder | What it is | Needed? |
|---|---|---|
| `tower_city` | The map: models, collision, interiors, lifts, escalators, the pool, the TVs | **Yes** |
| `tower_city_life` | Ambient people: shoppers, staff, guests, gamblers | Optional |

---

## 1. Install

1. **Check for conflicts first.** From your server's `resources` folder, run:
   ```
   powershell -ExecutionPolicy Bypass -File .\tower_city\tools\check_conflicts.ps1
   ```
   It reads files and changes nothing. It lists any resource you already have that replaces the same Rockstar map files
   (see section 7), plus any script that loads the old Maze Bank interiors. Two resources streaming the same file fight, and only
   one copy loads. Fix every line it reports before you start the map.
2. Copy `tower_city` (and `tower_city_life` if you want people) into your `resources` folder.
3. Add these lines to `server.cfg`, **after** `ox_lib` (and after `ox_inventory` if you use the item checks):
   ```
   ensure tower_city
   ensure tower_city_life
   ```
4. **Restart the whole server.** A map's streamed files only load cleanly on a full restart, not on `restart tower_city`.
   Players who were in before the restart should rejoin.

**Requires:** `ox_lib`. **Optional:** `ox_inventory`, only if you turn on the elevator item check (section 3).

---

## 2. Settings (`tower_city/config.lua`)

Shipped defaults:

| Setting | Default | What it does |
|---|---|---|
| `Config.Escalators` | `false` | The escalators stand still and work as normal stairs. Set it to `true` to make them move: stand still to ride, W to walk up faster. |
| `Config.PoolWater` | `true` | Makes the penthouse pool swimmable. See section 5 if your server already streams its own `water.xml`. |
| `Config.Access` | every check off | Every elevator floor is open to everyone, and no items are needed. |
| `Config.RestrictedMessage` | `'Restricted'` | The text shown when a locked floor refuses a player. |

Restart the resource after changing `config.lua`.

---

## 3. Elevators and locking floors

There are three elevator banks:

| Bank | Floors |
|---|---|
| Mall east | P2, P1, L1, L2, L3 |
| Mall west | P2, P1, L1, L2, L3 |
| Tower | VIP, CASINO, LOBBY, 98, 99, 100, PENTHOUSE, OFFICE |

Stand inside a cab and press **E** to open the floor list. The landing doors are real game doors, so they slide open on their own.

**Every floor is open by default.** Only `PENTHOUSE` and `OFFICE` can be locked, in `Config.Access`. Each of those floors has four
checks. **A floor is open when every check is off** (`enabled = false`). Once you turn on one or more checks, a player gets in by
passing **any one** of them. The server decides, never the player's game.

| Check | Passes when | Example of a list entry |
|---|---|---|
| `item` | the player carries the ox_inventory item `name` (you create the item yourself) | `name = 'penthouse_key'` |
| `licenses` | the player's Rockstar licence is in `list` | `'license:4e1b2a9c7d0f3e5a6b8c9d0e1f2a3b4c5d6e7f80'` |
| `discord` | the player's Discord id is in `list` | `'discord:123456789012345678'` |
| `cfx` | the player's Cfx.re (FiveM) account id is in `list` | `'fivem:1234567'` |

Write identifiers **in full, with the prefix** (`license:`, `discord:`, `fivem:`), each in quotes and separated by commas. You
can copy them from txAdmin: **Players**, pick the player, then **IDs**.

**Example 1:** lock the penthouse to two players by licence, plus anyone holding a key item:
```lua
PENTHOUSE = {
    item     = { enabled = true,  name = 'penthouse_key' },
    licenses = { enabled = true,  list = {
        'license:4e1b2a9c7d0f3e5a6b8c9d0e1f2a3b4c5d6e7f80',
        'license:0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b',
    } },
    discord  = { enabled = false, list = {} },
    cfx      = { enabled = false, list = {} },
},
```

**Example 2:** lock the head office to staff by Discord id:
```lua
OFFICE = {
    item     = { enabled = false, name = 'admin_keycard' },
    licenses = { enabled = false, list = {} },
    discord  = { enabled = true,  list = {
        'discord:123456789012345678',
        'discord:876543210987654321',
    } },
    cfx      = { enabled = false, list = {} },
},
```

Things to watch:
- A check that is turned on with an **empty list** lets nobody through that check. If it is the only check on, the floor is
  locked to everyone.
- Item names must match your ox_inventory items exactly. If ox_inventory isn't running, the item check always fails.
- `Config.Housing` holds spare slots for a housing script (owner, stash, wardrobe). Nothing reads them yet.
  `mlo-data/crown.json` lists every door, entry point and suggested stash or wardrobe spot for the penthouse and the office.

---

## 4. TVs and the render target

The penthouse and the head office have 7 wall TVs. They all use our own model, **`tc_prop_tv`**: a 4.0 x 2.25 m screen at full
size (181 in). It is placed at different sizes from about 108 in to 235 in. Each TV's room, position, heading and size are in
`mlo-data/crown.json` under `tvs`.

**Yes, the screen is a render target**, and it works the same way as Rockstar's own TVs (`prop_tv_flat_01` with `tvscreen`):

| | |
|---|---|
| Model | `tc_prop_tv` |
| Render target name | **`tc_tvscreen`** |
| Texture the screen samples | `script_rt_tc_tvscreen` (1024 x 512, about 16:9 once stretched onto the screen) |

Out of the box, `tower_city/tv.lua` draws a Tower City idle screen (logo and clock) into the target while a player is within about
22 m of a TV.

### Using it with another TV system (DUI / YouTube / Twitch / media scripts)

Most TV scripts keep a list of TV models, each with its render target name. **Add `tc_prop_tv` with render target `tc_tvscreen`** to
that list, the same way `prop_tv_flat_01` is listed with `tvscreen`. Then tell our idle screen to step aside: while your script is
drawing, set `LocalPlayer.state.tcTvBusy = true` on that client, and set it back to `false` (or `nil`) when you stop.

If you are writing your own, this is the whole pattern:
```lua
-- once: register and link the target, get its id
if not IsNamedRendertargetRegistered('tc_tvscreen') then RegisterNamedRendertarget('tc_tvscreen', false) end
if not IsNamedRendertargetLinked(`tc_prop_tv`) then LinkNamedRendertarget(`tc_prop_tv`) end
local rt = GetNamedRendertargetRenderId('tc_tvscreen')

-- a browser page (DUI) as a texture
local dui = CreateDui('https://example.com/your-player.html', 1280, 720)
local txd = CreateRuntimeTxd('my_tv_txd')
CreateRuntimeTextureFromDuiHandle(txd, 'my_tv_tex', GetDuiHandle(dui))

LocalPlayer.state.tcTvBusy = true          -- our idle screen stops drawing
CreateThread(function()
    while LocalPlayer.state.tcTvBusy do
        SetTextRenderId(rt)
        SetScriptGfxDrawOrder(4)
        SetScriptGfxDrawBehindPausemenu(true)
        DrawSprite('my_tv_txd', 'my_tv_tex', 0.5, 0.5, 1.0, 1.0, 0.0, 255, 255, 255, 255)
        SetTextRenderId(GetDefaultScriptRendertargetRenderId())
        Wait(0)
    end
end)
-- when you stop: LocalPlayer.state.tcTvBusy = false ; DestroyDui(dui)
```

Know before you plan around it:
- **All copies of one model share one render target.** GTA links targets per model, not per TV, so every `tc_prop_tv` in view
  shows the same picture. That's the same limit Rockstar's own TVs have. Showing different channels on different TVs needs a
  separate model (with its own target name) for each one.
- The TVs are part of the building, not spawned objects, so a script can't find them by spawning them. Use the positions in
  `crown.json` (or `GetClosestObjectOfType` near those positions) to know when a player is in front of one.
- Drawing happens on each player's own game. Syncing what is playing (which video, the time in it) is your TV script's job.

---

## 5. The penthouse pool (water)

The pool is swimmable because the map loads a full copy of the game's water map with the pool's water added
(`water/tc_water.xml`). Every ocean, river and lake is in it unchanged. **GTA only uses one water map at a time.** If another
resource on your server already streams or loads its own `water.xml`, you have two choices:
- keep ours and remove theirs, or
- merge the pool's water cells from our `water/tc_water.xml` into theirs and set `Config.PoolWater = false`.

Otherwise either the pool or their water will be missing.

---

## 6. Ambient people (`tower_city_life`, optional)

People shop, eat, work the counters, gamble, ride the trains and sit around the complex. They are created on each player's own game
(nothing is networked), so they add no server load. They only appear while a player is near that area. Turn areas on or off in
`tower_city_life/config.lua` (`Config.Areas`), or the whole thing with `Config.Enabled = false`, or simply don't ensure it.

Traffic, parked-car spawns and wandering Rockstar pedestrians are kept out of the two blocks by `tower_city/area_clear.lua`, so cars
don't drive into the mall and people don't walk into walls. The pavements around the blocks keep their pedestrians.

---

## 7. Rockstar files this map replaces (conflicts)

To remove the old buildings cleanly, `tower_city/stream` ships edited copies of Rockstar's own files for the two blocks, under
their original names. These are the `dt1_11*`, `dt1_12*`, `dt1_rd1*` and `hei_` versions of them, the `hi@` / `ma@` collision,
the `dt1_lod_*` distant models, the `dt1_occl_*` occluders and the `*distlodlights*` far-away night lights. Our own files all
start with `tc_`.

If another resource also replaces any of these files, only one copy loads. You'd see half of the old Maze Bank, holes, or
missing roads. `tools/check_conflicts.ps1` finds them for you. Common sources are other MLOs at the Maze Bank or Legion
Square, "Maze Bank interior" packs, and road or map-fix packs for downtown.

Map loaders such as `bob74_ipl` switch on the old Maze Bank's executive offices and CEO garages. Those would sit inside our
residence floors, so `vanilla_off.lua` keeps them switched off. You don't need to edit your loader.

**rcore_casino:** the tower's casino floor is built to work with rcore_casino as its own map type. That set-up edits rcore's files
and isn't included here; ask us for it if you run rcore_casino.

---

## 8. Data files for other scripts (`tower_city/mlo-data`)

| File | What's in it |
|---|---|
| `crown.json` | Penthouse and head office: floor heights, rooms, every door, lift stops, stand spots (desks, beds, wardrobe, stash, bar, pool edge), TVs |
| `residences.json` | Floors 98 to 100: units, doors, lift stops |
| `garage.json` | Tower parking: entrances, doors, parking bays |
| `README.md` | How to read them from another resource, with examples |

They are written by the build, so they always match the map.

---

## 9. Quick troubleshooting

| You see | Cause and fix |
|---|---|
| Parts of the old Maze Bank, holes in the ground, or roads missing | A file conflict: run `tools/check_conflicts.ps1` |
| An office or garage floating inside the residences | An IPL loader started after us and re-enabled them. `vanilla_off.lua` turns them off again within a few seconds; if it keeps happening, start `tower_city` after your loader. |
| The pool is empty or the ocean is missing | Two water maps: see section 5 |
| Elevator says "Restricted" | A check is on in `Config.Access` and the player isn't in its list (section 3) |
| Escalators don't move | That's the shipped default: `Config.Escalators = true` turns them on |
| Map looks broken after `restart tower_city` | Do a full server restart (section 1, step 4) |
