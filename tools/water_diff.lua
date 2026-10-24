-- City-wide stray-water check (run in a client, e.g. through the rig's t.sh): samples GetWaterHeight on a grid across the whole
-- map twice - with the game's own water map (ResetWater) and with ours (LoadWaterFromPath) - and lists every sample that differs.
-- The only differences allowed are the pools you added. Arguments via globals before the chunk:
--   WD_RES, WD_FILE  resource + file of our water map;  WD_STEP grid step in m (50 = whole map in ~45k samples per pass)
--   WD_BOX = {x0, x1, y0, y1} to limit the area (default: the whole map)
--   WD_Z = {z, ...} probe heights. Limited-depth quads (HasLimitedDepth) are only seen by a probe just above their surface, so
--   probe at the height of every quad you added AND at the floors / street below it (default {1500}: open water only)
local res, file, step = WD_RES or 'tower_city', WD_FILE or 'water/tc_water.xml', WD_STEP or 50.0
local box = WD_BOX or {-4200.0, 4600.0, -4200.0, 8200.0}
local zs = WD_Z or {1500.0}
local function sample()
    local t = {}
    for x = box[1], box[2], step do
        for y = box[3], box[4], step do
            for _, z in ipairs(zs) do
                local ok, h = GetWaterHeight(x, y, z)
                t[#t + 1] = ok and math.floor(h * 100 + 0.5) or false
            end
        end
        Wait(0)
    end
    return t
end
ResetWater(); Wait(1000); local a = sample()
LoadWaterFromPath(res, file); Wait(1000); local b = sample()
local diffs, i = {}, 0
for x = box[1], box[2], step do
    for y = box[3], box[4], step do
        for _, z in ipairs(zs) do
            i = i + 1
            if a[i] ~= b[i] then diffs[#diffs + 1] = ('%.0f,%.0f z%.0f vanilla=%s ours=%s'):format(x, y, z, tostring(a[i]), tostring(b[i])) end
        end
    end
end
return ('samples %d, differences %d %s'):format(i, #diffs, table.concat(diffs, ' | ', 1, math.min(#diffs, 30)))
