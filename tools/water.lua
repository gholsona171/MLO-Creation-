-- Tower City swimmable pool: loads the game's water map + the penthouse pool's swim cells (water/tc_water.xml, built by
-- work/pool_water.py; every vanilla ocean / river / reservoir quad is in it unchanged). Only one water map is active at a time: a
-- server that already streams its own water.xml must merge the pool's cells into that file and set Config.PoolWater = false.
-- Cayo Perico swaps the water map; ours is loaded again when the player comes back.
if not Config.PoolWater then return end
local FILE = 'water/tc_water.xml'
local function load()
    if not LoadWaterFromPath(GetCurrentResourceName(), FILE) then print('[tower_city] pool water did not load') end
end
CreateThread(function()
    Wait(1000); load()
    local away = false
    while true do
        Wait(5000)
        local p = GetEntityCoords(PlayerPedId())
        local island = p.x > 3000.0 and p.y < -3500.0                    -- Cayo Perico
        if away and not island then load() end
        away = island
    end
end)
AddEventHandler('onResourceStop', function(res) if res == GetCurrentResourceName() then ResetWater() end end)
