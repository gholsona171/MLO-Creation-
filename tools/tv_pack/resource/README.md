# tc_tv: wall TV with a script screen

This resource adds one wall-mounted TV model, **`tc_prop_tv`**. Its screen is a **script render target**: any TV, media or DUI
script can draw on it, the same way it draws on GTA's own TVs (`prop_tv_flat_01` with `tvscreen`).

Out of the box it shows an idle screen (a title, a subtitle and the in-game clock) while a player is near one of the TVs listed in
`config.lua`.

## Install

1. Put the `tc_tv` folder in your `resources` folder.
2. Add `ensure tc_tv` to your `server.cfg`, **before** any map that uses the TV. A map that uses it already lists
   `dependency 'tc_tv'`, so it will not start without it.

## The render target

| | |
|---|---|
| Model | `tc_prop_tv` |
| Render target name | **`tc_tvscreen`** |
| Texture the screen samples | `script_rt_tc_tvscreen` (1024 x 512, stretched to the 16:9 screen) |
| Model size at scale 1 | 4.00 x 2.25 m screen; maps place it smaller (scale 0.3 = 1.2 m wide) |

## Hooking your TV script in

Most TV scripts keep a list of TV models, each with its render target name. **Add `tc_prop_tv` with render target `tc_tvscreen`**
to that list, the same way `prop_tv_flat_01` is listed with `tvscreen`.

Then tell the idle screen to step aside while your script draws: set `LocalPlayer.state.tcTvBusy = true` on that client (or call
`exports.tc_tv:SetBusy(true)`), and set it back to `false` when you stop.

Writing your own? This is the whole pattern:

```lua
if not IsNamedRendertargetRegistered('tc_tvscreen') then RegisterNamedRendertarget('tc_tvscreen', false) end
if not IsNamedRendertargetLinked(`tc_prop_tv`) then LinkNamedRendertarget(`tc_prop_tv`) end
local rt = GetNamedRendertargetRenderId('tc_tvscreen')

local dui = CreateDui('https://example.com/your-player.html', 1280, 720)      -- a web page as a texture
local txd = CreateRuntimeTxd('my_tv_txd')
CreateRuntimeTextureFromDuiHandle(txd, 'my_tv_tex', GetDuiHandle(dui))

exports.tc_tv:SetBusy(true)                                                     -- the idle screen stops drawing
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
-- when you stop: exports.tc_tv:SetBusy(false) ; DestroyDui(dui)
```

## Things to know

- **Every `tc_prop_tv` shows the same picture.** GTA links a render target to a model, not to one TV, so every copy in view shows
  what is drawn into `tc_tvscreen`. Rockstar's own TVs have the same limit.
- **Map TVs can't be found by scripts.** TVs placed inside a building (MLO) are part of the map, not spawned objects, so
  `GetClosestObjectOfType` won't find them. Their positions are listed in `config.lua` (`Config.Screens`); use those to know when
  a player is in front of one. Other resources can add theirs with `exports.tc_tv:AddScreens({ { pos = vector3(x, y, z), title = '', sub = '' } })`.
- **Drawing happens on each player's own game.** Keeping players in sync (which video, the time in it) is your TV script's job.
- `exports.tc_tv:GetRenderTarget()` returns the model, target and texture names above.
- Already running our Tower City map? It carries the same TV (same model, same render target). Both work side by side, and
  the game uses one copy of the model.
