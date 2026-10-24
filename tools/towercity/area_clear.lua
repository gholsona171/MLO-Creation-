-- area_clear.lua: Tower City replaces two whole blocks, but Rockstar's AI data for the old blocks is not in the map files we ship:
-- the old car-park service lane through the mall block (22 traffic nodes), the walkable ground (navmesh) of the old streets and
-- the Maze Bank plaza, and ambient scenario points (people loitering, scenario cars). Left on, cars drive into the mall and the
-- casino and pedestrians walk into the walls (Antonio, 2026-10-24). Switched off here, once, inside each lot (1 m in from the
-- kept sidewalk, which keeps its pedestrians). A script and not edited path / navmesh / scenario files: those exist in several
-- game-update versions and other maps on a server often edit the same files (only one copy loads - see the buyer conflict check).
-- Our own people (tower_city_life) walk by direct tasks, not the navmesh, so they are not affected.
-- AddNavmeshBlockingObject takes its heading in degrees (tested: radians left the walker crossing the lot).
local H = math.rad(69.5)
local LOTS = {                                                       -- origin + the lot's inner box in the building grid (u, v), metres
    { o = vector2(71.0, -884.0),    u = { -77.0, 77.0 }, v = { -52.0, 52.0 } },   -- east: the mall
    { o = vector2(-78.897, -827.328), u = { -78.0, 73.0 }, v = { -57.0, 58.0 } }, -- west: the tower
}
local Z0, Z1 = 5.0, 80.0                                             -- from the station level to above the podium roof
local function W(o, u, v) return vector2(o.x + u * math.cos(H) - v * math.sin(H), o.y + u * math.sin(H) + v * math.cos(H)) end
local function inside(L, x, y)
    local dx, dy = x - L.o.x, y - L.o.y
    local u, v = dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H)
    return u >= L.u[1] and u <= L.u[2] and v >= L.v[1] and v <= L.v[2]
end

-- the lot as world-axis strips (scenario / car-generator areas are axis-aligned boxes): 4 m slices along x, each kept to the
-- y-range that lies inside the lot across the whole slice
local function strips(L)
    local c = { W(L.o, L.u[1], L.v[1]), W(L.o, L.u[2], L.v[1]), W(L.o, L.u[2], L.v[2]), W(L.o, L.u[1], L.v[2]) }
    local x0, x1 = math.huge, -math.huge
    for _, p in ipairs(c) do x0 = math.min(x0, p.x); x1 = math.max(x1, p.x) end
    local out = {}
    for x = x0, x1 - 0.01, 4.0 do
        local lo, hi = nil, nil
        for _, xs in ipairs({ x, math.min(x + 4.0, x1) }) do
            local a, b = math.huge, -math.huge
            for y = -1200.0, -600.0, 0.5 do if inside(L, xs, y) then a = math.min(a, y); b = math.max(b, y) end end
            if a > b then lo = nil; break end
            lo = lo and math.max(lo, a) or a; hi = hi and math.min(hi, b) or b
        end
        if lo and hi and hi > lo then out[#out + 1] = { x, lo, math.min(x + 4.0, x1), hi } end
    end
    return out
end

-- sidewalk path points that sit inside our walls (a straight ped link ends in the building's corner, so walkers walk into it):
-- switched off, the pedestrians turn before the corner. Found by tracing every ped link of the area (2026-10-24).
local PED_POINTS_OFF = {
    vector3(147.75, -829.5, 30.09),                                  -- the mall's Legion Square / south-east corner
}

CreateThread(function()
    for _, p in ipairs(PED_POINTS_OFF) do SetPedPathsInArea(p.x - 1.0, p.y - 1.0, p.z - 2.0, p.x + 1.0, p.y + 1.0, p.z + 2.0, false, 0) end
    for _, L in ipairs(LOTS) do
        local vm = (L.v[1] + L.v[2]) / 2
        local a, b = W(L.o, L.u[1], vm), W(L.o, L.u[2], vm)
        SetRoadsInAngledArea(a.x, a.y, Z0, b.x, b.y, Z1, L.v[2] - L.v[1], false, false, false)   -- traffic lanes off
        local c = W(L.o, (L.u[1] + L.u[2]) / 2, vm)
        AddNavmeshBlockingObject(c.x, c.y, (Z0 + Z1) / 2, L.u[2] - L.u[1], L.v[2] - L.v[1], Z1 - Z0, 69.5, true, 7)   -- ambient peds don't path in (heading in DEGREES)
        for _, s in ipairs(strips(L)) do
            AddScenarioBlockingArea(s[1], s[2], Z0, s[3], s[4], Z1, false, true, true, true)      -- loitering peds + scenario cars
            SetAllVehicleGeneratorsActiveInArea(s[1], s[2], Z0, s[3], s[4], Z1, false, false)
            RemoveVehiclesFromGeneratorsInArea(s[1], s[2], Z0, s[3], s[4], Z1)
        end
    end
end)
