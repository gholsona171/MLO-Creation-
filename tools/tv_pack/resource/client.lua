-- tc_tv: the screen of tc_prop_tv samples the render target 'tc_tvscreen' (texture script_rt_tc_tvscreen, 1024 x 512).
-- While a player is near a listed TV (config.lua) and no TV script is using the screen, this draws an idle screen into it.
-- A TV / DUI script takes the screen over by drawing into the same target and setting LocalPlayer.state.tcTvBusy = true
-- (or calling exports.tc_tv:SetBusy(true)) while it does. README.md has the whole pattern.
local MODEL, RT = `tc_prop_tv`, 'tc_tvscreen'
local screens = {}
for _, s in ipairs(Config.Screens or {}) do screens[#screens + 1] = s end

-- other resources can list their TVs too: exports.tc_tv:AddScreens({ { pos = vector3(x, y, z), title = '...', sub = '...' } })
exports('AddScreens', function(list) for _, s in ipairs(list or {}) do screens[#screens + 1] = s end end)
exports('SetBusy', function(on) LocalPlayer.state:set('tcTvBusy', on and true or nil, false) end)
exports('GetRenderTarget', function() return { model = 'tc_prop_tv', target = RT, texture = 'script_rt_tc_tvscreen', width = 1024, height = 512 } end)

local function nearest()
    local p, best, bd = GetEntityCoords(PlayerPedId()), nil, Config.Range or 22.0
    for _, s in ipairs(screens) do
        local d = #(p - s.pos)
        if d < bd then best, bd = s, d end
    end
    return best
end
local function rtId()
    if not IsNamedRendertargetRegistered(RT) then RegisterNamedRendertarget(RT, false) end
    if not IsNamedRendertargetLinked(MODEL) then LinkNamedRendertarget(MODEL) end
    return GetNamedRendertargetRenderId(RT)
end
local function text(s, x, y, scale, r, g, b, a, font)
    SetTextFont(font or 4); SetTextScale(scale, scale); SetTextColour(r, g, b, a); SetTextCentre(true); SetTextOutline()
    BeginTextCommandDisplayText('STRING'); AddTextComponentSubstringPlayerName(s); EndTextCommandDisplayText(x, y)
end

CreateThread(function()
    while true do
        local s = nearest()
        if not s or LocalPlayer.state.tcTvBusy then Wait(1500) else
            local id, t0 = rtId(), GetGameTimer()
            while not LocalPlayer.state.tcTvBusy do
                if GetGameTimer() - t0 > 1000 then s = nearest(); t0 = GetGameTimer(); if not s then break end end
                SetTextRenderId(id); SetScriptGfxDrawOrder(4); SetScriptGfxDrawBehindPausemenu(true)
                local t = GetGameTimer() / 1000.0
                DrawRect(0.5, 0.5, 1.0, 1.0, 6, 8, 14, 255)                                        -- night-blue field
                for i = 0, 7 do                                                                    -- slow drifting light bands
                    DrawRect(0.5, (i / 8.0 + t * 0.012) % 1.0, 1.0, 0.06, 20, 32, 60, 70)
                end
                DrawRect(0.5, 0.60, 0.42, 0.004, 235, 205, 125, 220)                                -- gold rule
                if s.title and s.title ~= '' then text(s.title, 0.5, 0.22, 2.2, 235, 205, 125, 255, 4) end
                if s.sub and s.sub ~= '' then text(s.sub, 0.5, 0.64, 0.6, 210, 214, 224, 255, 0) end
                text(('%02d:%02d'):format(GetClockHours(), GetClockMinutes()), 0.5, 0.74, 0.8, 230, 232, 240, 255, 0)
                SetTextRenderId(GetDefaultScriptRendertargetRenderId())
                Wait(0)
            end
        end
    end
end)
