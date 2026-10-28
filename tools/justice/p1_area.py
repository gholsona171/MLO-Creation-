"""Justice Center phase 1: writes work/scripts/area_clear.lua (the client script that switches the old block's AI off), from the lot
outline - Tower City's area_clear.lua pattern, generated so it can never drift from the outline.
Rockstar's AI data for the block is not in the files we ship and is shared with every other map (paths nodes400.ynd, the navmesh,
scenario regions davis.ymt / rancho.ymt): left on, cars would drive the old car-park ramps through the empty lot, peds would loiter on
the old plaza heights and car generators would spawn on decks that are gone. Switched off in script, never by editing those files.
  * AREA = the lot shrunk by INSET (1 m): the sidewalks round the block keep their pedestrians and their path nodes
  * traffic lanes:     SetRoadsInAngledArea over lot-frame strips (10 m along u, the v range inside AREA across the whole strip)
  * walkers:           SetPedPathsInArea over a few axis boxes inside AREA (the 4 m strips merged, P_BOXES): proven on the rig
                       2026-10-28 (0 walkers in the lot over 3 min); the navmesh blocking objects alone left walkers on the old plaza
                       navmesh, floating at its old height (z 30.5 over the z 28.3 slab)
  * car generators: SetAllVehicleGeneratorsActiveInArea / RemoveVehiclesFromGeneratorsInArea over world-axis strips (4 m along x, the y
    range inside AREA across the whole strip: those natives take axis boxes)
  * scenarios: AddScenarioBlockingArea over ONE box, the lot's world-axis bounding box, z 20-130 (see SB below)
  No per-tile SetPedPathsInArea (Tower City: ~140 small switches crashed the game on load).
  * once, after the blocks: ambient peds already standing inside AREA (spawned while the client loaded, before the blocks) are removed.
    No loop: the blocks stop new ones (rig, 2026-10-28: a permanent 1 s sweep was a workaround - removed)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import jc_frame as F
from shapely.geometry import Polygon, box
from shapely import affinity
J = F.J; INSET = 1.0; Z0, Z1 = 15.0, 110.0
LOT = Polygon([p[:2] for p in F.lot_w()]); AREA = LOT.buffer(-INSET, join_style=2)
UV = Polygon([F.L(x, y) for x, y in AREA.exterior.coords])
def strip(P, x, xe):
    """the widest y range [lo, hi] with the box x..xe x lo..hi inside P (shrunk from P's extent until it fits), or None"""
    y0, y1 = P.bounds[1], P.bounds[3]; ys = None
    for xs in [x + 0.02 + (xe - x - 0.04) * k / 6 for k in range(7)]:          # y range inside P at 7 lines across the strip
        c = P.intersection(box(xs - 0.005, y0 - 1, xs + 0.005, y1 + 1))
        if c.is_empty: return None
        lo, hi = c.bounds[1], c.bounds[3]; ys = (lo, hi) if ys is None else (max(ys[0], lo), min(ys[1], hi))
    if ys[1] < ys[0] + 0.5: return None
    while not P.buffer(1e-6).contains(box(x, ys[0], xe, ys[1])) and ys[1] - ys[0] > 1.0: ys = (ys[0] + 0.25, ys[1] - 0.25)
    return ys if P.buffer(1e-6).contains(box(x, ys[0], xe, ys[1])) else None
def strips(P, step, x=None, x1=None):
    """axis strips of P (in its own frame): [x0, y0, x1, y1]; a strip that does not fit (a corner, a protrusion at its edge) is split
    in two, down to 0.5 m, so the lot's ends are covered too"""
    x = P.bounds[0] if x is None else x; x1 = P.bounds[2] if x1 is None else x1; out = []
    while x < x1 - 0.01:
        xe = min(x + step, x1); ys = strip(P, x, xe)
        if ys and ys[1] - ys[0] > 0.6 * (P.intersection(box(x, P.bounds[1] - 1, xe, P.bounds[3] + 1)).bounds[3] - P.intersection(box(x, P.bounds[1] - 1, xe, P.bounds[3] + 1)).bounds[1]):
            out.append([round(x, 2), round(ys[0], 2), round(xe, 2), round(ys[1], 2)])
        elif step > 0.5: out += strips(P, step / 2, x, xe)
        elif ys: out.append([round(x, 2), round(ys[0], 2), round(xe, 2), round(ys[1], 2)])
        x = xe
    return out
U = strips(UV, 8.0); X = strips(AREA, 4.0)
# scenario blocking: ONE box, the world-axis bounding box of the lot outline, z 20-130 (below grade to above the planned tower floors).
# The game's scenario-blocking pool is shared by every resource on a client and holds about 45 areas (proven on the rig 2026-10-28:
# Tower City's 75 strips loading first held 45, every later add failed - Justice Center's included). One box per lot keeps both maps
# well inside it (Antonio's decision). It overlaps the sidewalks at the lot's corners: only loiterers there, walkers are not affected.
PB = []; cur = None; acc = []                                 # ped-path boxes: consecutive x-strips merged while the common y range
for st in X:                                                   # keeps >= 85 % of their area; boxes under 2 m wide dropped (few calls:
    if cur is not None:                                        # Tower City's ~140 small SetPedPathsInArea calls crashed the game on load)
        m = [cur[0], max(cur[1], st[1]), st[2], min(cur[3], st[3])]
        if m[3] > m[1] and (m[2] - m[0]) * (m[3] - m[1]) >= 0.85 * sum((t[2] - t[0]) * (t[3] - t[1]) for t in acc + [st]): cur = m; acc.append(st); continue
        PB.append(cur)
    cur = list(st); acc = [st]
PB.append(cur); PB = [b for b in PB if b[2] - b[0] >= 2.0]
X0b, Y0b, X1b, Y1b = LOT.bounds
SB = [(X0b, Y0b, 20.0, X1b, Y1b, 130.0)]
SB = [tuple(round(t, 2) for t in b) for b in SB]
cover_u = sum((s[2] - s[0]) * (s[3] - s[1]) for s in U) / UV.area; cover_x = sum((s[2] - s[0]) * (s[3] - s[1]) for s in X) / AREA.area
lua = f'''-- area_clear.lua (GENERATED by work/p1_area.py from plan/lot_poly.json - do not edit; rebuild): Justice Center, phase 1.
-- The old Davis block (sc1_19: courts tower, library, sheriff station, car park, plaza) is gone, but Rockstar's AI data for it is not in
-- the files this map ships (paths, navmesh and scenario regions are shared with every other map): left on, cars would drive the old
-- car-park ramps across the empty lot, people would loiter on the old plaza heights and car generators would spawn on decks that are
-- gone. Switched off here, once, inside the lot ({INSET:.0f} m in from the sidewalk, which keeps its pedestrians).
local H = {F.HDEG:.1f}                                          -- the block's street grid (degrees)
local O = vector2({F.OX}, {F.OY})                       -- lot frame origin: u towards Innocence Blvd, v towards Davis Ave
local Z0, Z1 = {Z0}, {Z1}
local function W(u, v) local h = math.rad(H) return vector2(O.x + u * math.cos(h) - v * math.sin(h), O.y + u * math.sin(h) + v * math.cos(h)) end
-- lot-frame strips {{u0, v0, u1, v1}}: traffic lanes off ({len(U)} strips, {cover_u * 100:.0f} % of the area)
local U_STRIPS = {{
{chr(10).join('    { %.2f, %.2f, %.2f, %.2f },' % tuple(s) for s in U)}
}}
-- world-axis strips {{x0, y0, x1, y1}}: car generators off ({len(X)} strips, {cover_x * 100:.0f} % of the area)
local X_STRIPS = {{
{chr(10).join('    { %.2f, %.2f, %.2f, %.2f },' % tuple(s) for s in X)}
}}
-- AREA (the lot 1 m in from the sidewalk), world x / y: the sweep's point-in-polygon
local AREA = {{
{chr(10).join('    { %.2f, %.2f },' % p for p in list(AREA.simplify(0.05).exterior.coords)[:-1])}
}}
local AX0, AY0, AX1, AY1 = {AREA.bounds[0]:.2f}, {AREA.bounds[1]:.2f}, {AREA.bounds[2]:.2f}, {AREA.bounds[3]:.2f}
local function inArea(x, y)
    if x < AX0 or x > AX1 or y < AY0 or y > AY1 then return false end
    local c, n = false, #AREA
    for i = 1, n do local a, b = AREA[i], AREA[i % n + 1]
        if ((a[2] > y) ~= (b[2] > y)) and (x < (b[1] - a[1]) * (y - a[2]) / (b[2] - a[2]) + a[1]) then c = not c end end
    return c
end
-- ped paths off (walkers on the old plaza / car-park navmesh, at the old heights): the 4 m strips merged into larger boxes inside AREA
local P_BOXES = {{
{chr(10).join('    { %.2f, %.2f, %.2f, %.2f },' % tuple(b) for b in PB)}
}}
-- scenario blocking: ONE box (the lot's bounding box, z 20-130): the blocking pool (~45 areas) is shared by every resource
local S_BOXES = {{
{chr(10).join('    { %.2f, %.2f, %.2f, %.2f, %.2f, %.2f },' % b for b in SB)}
}}
CreateThread(function()
    for _, s in ipairs(U_STRIPS) do
        local um, w = (s[1] + s[3]) / 2, s[3] - s[1]
        local a, b = W(um, s[2]), W(um, s[4])
        SetRoadsInAngledArea(a.x, a.y, Z0, b.x, b.y, Z1, w, false, false, false)                  -- traffic lanes off
    end
    for _, b in ipairs(P_BOXES) do SetPedPathsInArea(b[1], b[2], Z0, b[3], b[4], Z1, false, 0) end   -- walkers' ped paths off (few calls)
    for _, s in ipairs(X_STRIPS) do
        SetAllVehicleGeneratorsActiveInArea(s[1], s[2], Z0, s[3], s[4], Z1, false, false)
        RemoveVehiclesFromGeneratorsInArea(s[1], s[2], Z0, s[3], s[4], Z1)
    end
    local held, hs = 0, {{}}                                   -- the scenario blocking pool is shared by every resource: report what held
    for _, b in ipairs(S_BOXES) do
        hs[#hs + 1] = tostring(AddScenarioBlockingArea(b[1], b[2], b[3], b[4], b[5], b[6], false, true, true, true))
        if DoesScenarioBlockingAreaExist(b[1], b[2], b[3], b[4], b[5], b[6]) then held = held + 1 end
    end
    print(('justice_center area_clear: %d of %d scenario blocks held (handles %s)'):format(held, #S_BOXES, table.concat(hs, ',')))
    Wait(5000)                                                -- once: peds that spawned before the blocks (no loop)
    for _, e in ipairs(GetGamePool('CPed')) do
        if not IsPedAPlayer(e) and GetEntityPopulationType(e) >= 1 and GetEntityPopulationType(e) <= 5 and not IsPedInAnyVehicle(e, false) then
            local c = GetEntityCoords(e)
            if inArea(c.x, c.y) and (not NetworkGetEntityIsNetworked(e) or NetworkHasControlOfEntity(e)) then SetEntityAsMissionEntity(e, true, true) DeleteEntity(e) end
        end
    end
end)
'''
(J / 'work/scripts').mkdir(parents=True, exist_ok=True); (J / 'work/scripts/area_clear.lua').write_text(lua, encoding='utf-8')
json.dump({'u_strips': U, 'x_strips': X, 'scenario_boxes': SB, 'cover_u': cover_u, 'cover_x': cover_x, 'inset': INSET}, open(J / 'work/p1_area.json', 'w'), indent=0)
print('P1_AREA', len(U), 'lot-frame strips (%.0f %%),' % (cover_u * 100), len(X), 'world strips (%.0f %%),' % (cover_x * 100), len(PB), 'ped-path boxes,', len(SB), 'scenario box')
