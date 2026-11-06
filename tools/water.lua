-- Tower City swimmable pool: loads the game's water map + the penthouse pool's swim cells (water/tc_water.xml, built by
-- work/pool_water.py; every vanilla ocean / river / reservoir quad is in it unchanged) ONLY while the player is near the pool,
-- and puts the game's own map back (ResetWater) as soon as they leave.
-- Why: with the pool cells loaded, the Land Act reservoir draws no water surface (rig A/B tests ab1-ab15, 2026-11-05: any water
-- quad at the pool's downtown spot at a height vanilla doesn't use does it; count, order, flags and the calming quad are innocent).
-- The reservoir is ~2 km away, so loading the pool only near the tower keeps it everywhere else.
-- Only one water map is active at a time: a server that already streams its own water.xml must merge the pool's cells into that
-- file and set Config.PoolWater = false. Cayo Perico has its own water map: ours is never loaded (or reset) on the island.
if not Config.PoolWater then return end
local FILE   = 'water/tc_water.xml'
local POOL   = vector2(-96.0, -810.0)   -- centre of the pool's swim cells (x -102..-90, y -816..-804; water line z 255.55)
local NEAR   = 150.0                    -- load the pool water inside this distance (2D)...
local FAR    = 200.0                    -- ...and drop it beyond this one (hysteresis: no flapping at the edge)
local TICK   = 1500                     -- ms between checks
local loaded = false
local function onIsland(p) return p.x > 3000.0 and p.y < -3500.0 end   -- Cayo Perico
local function load()
    if LoadWaterFromPath(GetCurrentResourceName(), FILE) then loaded = true
    else print('[tower_city] pool water did not load') end
end
local function unload(island)
    if not loaded then return end
    loaded = false
    if not island then ResetWater() end   -- on the island its own water map is in force: leave it alone
end
CreateThread(function()
    while true do
        local p = GetEntityCoords(PlayerPedId())
        local island = onIsland(p)
        local d = #(vector2(p.x, p.y) - POOL)
        if not loaded and not island and d < NEAR then load()
        elseif loaded and (island or d > FAR) then unload(island) end
        Wait(TICK)
    end
end)
AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() and loaded then ResetWater() end
end)
