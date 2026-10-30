"""Offline EXECUTION of the Lua our rig probes send (rig 2026-10-30: a chunk returned the literal '%.2f' - a Python string that was never
%-formatted kept '%%' - and a stubbed dry run that returned made-up numbers could not see it). Each chunk runs in Lua 5.4 (lupa) against
a mock of the FiveM natives it uses: vector2 / vector3 with arithmetic and # length, GetGameTimer that advances, Wait that advances it,
every other native a stub returning a plausible default (0 / false / a vector). The probe functions are then driven with `lua` routed
here, so their own Python parsing reads what the Lua really returns.
Proof: a chunk returning string.format("%%.2f", 1) must be caught (it returns '%.2f', not a number); the mock keys guard must stop a raw
engine start; the pre-fix probe (raw SetVehicleEngineOn) fails here with the car at 0.0 m, as on the rig.
Run: py -3 jj_luasim.py   (JJ_LUASIM_PASS)"""
import sys, re
from pathlib import Path
import lupa.lua54 as lupa
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
MOCK = r'''
local VM = {}
local function vec(x, y, z) return setmetatable({x = x or 0.0, y = y or 0.0, z = z}, VM) end
VM.__add = function(a, b) return vec(a.x + b.x, a.y + b.y, a.z and b.z and a.z + b.z or nil) end
VM.__sub = function(a, b) return vec(a.x - b.x, a.y - b.y, a.z and b.z and a.z - b.z or nil) end
VM.__mul = function(a, b) if type(a) == "number" then a, b = b, a end return vec(a.x * b, a.y * b, a.z and a.z * b or nil) end
VM.__len = function(a) return math.sqrt(a.x * a.x + a.y * a.y + (a.z or 0) * (a.z or 0)) end
function vector2(x, y) return vec(x, y, nil) end
function vector3(x, y, z) return vec(x, y, z or 0.0) end
local T = 0
function GetGameTimer() T = T + 50 return T end
function Wait(ms) T = T + (ms or 0) end
local POS, HD, CREATED, ENG, SEAT, WANT = {}, {}, {}, {}, {}, {}   -- every table a mock function uses, declared before any of them
function GetEntityCoords(e) return POS[e] or vector3(300.0, -1660.0, 29.0) end
function SetEntityCoords(e, x, y, z) POS[e] = vector3(x, y, z) end
function CreateVehicle(h, x, y, z, hd) local e = 1000 + math.random(1, 999) POS[e] = vector3(x, y, z) HD[e] = hd or 0.0 CREATED[e] = T return e end
function SetEntityHeading(e, h) HD[e] = h end
function GetEntityHeading(e) return HD[e] or 0.0 end
function GetEntityRotation(e) return vector3(0.0, 0.0, 0.0) end
function GetCollisionNormalOfLastHitForEntity(e) return vector3(0.0, 0.0, 1.0) end
function GetVehicleNumberPlateText(v) return "TEST1234" end
function GetGamePool(n) return {} end
function GetHashKey(s) return 12345 end
function PlayerPedId() return 1 end
function DoesEntityExist(e) return POS[e] ~= nil end
function DeleteVehicle(e) POS[e] = nil SEAT[e] = nil end
-- the c9_vehiclekeys guard (disableAutoStart, rig 2026-10-30): with a player in the driver's seat the engine runs only when the
-- keys script wants it (its ToggleEngine); a raw SetVehicleEngineOn is switched off again the next frame

-- a fresh car takes a ped only WARP_MS after it was created (rig 2026-10-30: the warp into the plant car did not take); the
-- ped sits in at most one car; leaving empties the seat
local WARP_MS = 1500
local function seatIn(v, s) if s == -1 and POS[v] and T - (CREATED[v] or -1e9) >= WARP_MS then for k in pairs(SEAT) do SEAT[k] = nil end SEAT[v] = true end end
function TaskWarpPedIntoVehicle(p, v, s) seatIn(v, s) end
function SetPedIntoVehicle(p, v, s) seatIn(v, s) end
function TaskLeaveVehicle(p, v, f) SEAT[v] = nil end
function IsPedInAnyVehicle(p) for k in pairs(SEAT) do if POS[k] then return true end end return false end
function NetworkGetEntityIsNetworked(e) return POS[e] ~= nil and T - (CREATED[e] or 0) >= 300 end
function NetworkHasControlOfEntity(e) return POS[e] ~= nil end
function IsPedRagdoll(p) return false end
function IsPedFalling(p) return false end
function IsPedGettingIntoAVehicle(p) return false end
function IsEntityDead(p) return false end
function GetPedInVehicleSeat(v, s) return (s == -1 and SEAT[v] and POS[v]) and 1 or 0 end
function GetIsVehicleEngineRunning(v) return ENG[v] == true and (not SEAT[v] or WANT[v] == true) end
function SetVehicleEngineOn(v, on) ENG[v] = on and true or nil end
function GetVehicleFuelLevel(v) return 65.0 end
function Entity(e) return {state = {fuel = 65.0}} end
-- c9_vehiclekeys as the rig runs it: CanDrive once keyed, ToggleEngine starts the car the player sits in
exports = setmetatable({c9_vehiclekeys = {CanDrive = function(self, v) return true end,
                                          ToggleEngine = function(self) local v = _G.__jjv local on = not GetIsVehicleEngineRunning(v) WANT[v] = on ENG[v] = on end}},
                       {__index = function() return setmetatable({}, {__index = function() return function() return true end end}) end})
-- gas / reverse move the car 0.5 m per call along its heading (GTA forward = (-sin h, cos h)) when the engine runs
function TaskVehicleTempAction(p, v, a, ms)
    if not GetIsVehicleEngineRunning(v) or not POS[v] or (a ~= 23 and a ~= 22) then return end
    local h = math.rad(HD[v] or 0.0) local s = (a == 23) and 0.5 or -0.5
    POS[v] = vector3(POS[v].x - math.sin(h) * s, POS[v].y + math.cos(h) * s, POS[v].z)
end
function GetEntitySpeed(e) return 0.0 end
function IsDoorRegisteredWithSystem(h) return false end
function GetClosestObjectOfType() return 0 end
function tostring_(x) return tostring(x) end
setmetatable(_G, {__index = function(t, k) return function() return 0 end end})   -- every other native: a stub
'''
_rt = None
def reset():
    global _rt
    _rt = lupa.LuaRuntime(); _rt.execute(MOCK)
def run(code):
    """execute one chunk the way t.sh does (as a function body) and return its result as the string the rig would send back."""
    global _rt
    if _rt is None: reset()                      # one Lua state per probe run: globals (_G.__jjv), cars and doors persist between chunks as on the rig
    f = _rt.eval('function(s) local f, e = load(s) if not f then return "LUA_COMPILE_ERROR: " .. e end local ok, r = pcall(f) if not ok then return "LUA_RUN_ERROR: " .. tostring(r) end return tostring(r) end')
    return f(code)
def check_result(text):
    """a result must not carry an unfilled format template or a Lua error."""
    if text.startswith(('LUA_COMPILE_ERROR', 'LUA_RUN_ERROR')): return text
    if re.search(r'%[-\d.]*[dfsx]', text): return 'UNFILLED FORMAT in the result: ' + text[:120]
    return None
def static_check(src):
    """every string literal that reaches Lua unformatted must not carry '%%' (it would reach Lua as a literal '%%' -> '%.2f' back).
    Catches chunks the mock run cannot reach. A literal is 'formatted' when it sits inside the left operand of a % BinOp."""
    import ast
    tree = ast.parse(src); fmt = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod):
            for m in ast.walk(n.left): fmt.add(id(m))
    return [f'line {n.lineno}: "%%" in a string that is never %-formatted: {n.value[:70]}' for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and '%%' in n.value and id(n) not in fmt]
if __name__ == '__main__':
    bad = []
    assert check_result(run('return string.format("%%.2f", 1)')), 'the simulator did not catch its planted unfilled format'
    reset()   # plant: the old raw engine start (spawn engine on, warp, SetVehicleEngineOn) must leave the car dead under the keys guard
    assert run('local v=CreateVehicle(1,0.0,0.0,0.0,0.0) SetVehicleEngineOn(v,true,true,false) Wait(2000) TaskWarpPedIntoVehicle(1,v,-1) SetVehicleEngineOn(v,true,true,false) '
               'local c0=GetEntityCoords(v) TaskVehicleTempAction(1,v,23,300) return tostring(#(GetEntityCoords(v)-c0))') == '0.0', 'the mock keys guard did not stop a raw engine start'
    assert static_check('x = lua("return string.format(\\"%%.2f\\", 1)")'), 'the static check did not catch its planted %%'
    for f in ('jj_probe.py', 'jj_doorctl.py'): bad += [f'{f} {e}' for e in static_check((JL / f).read_text(encoding='utf-8'))]
    import jj_probe as P, jj_doorctl as D
    seen = []
    def lua(code, timeout=60):
        res = run(code); e = check_result(res); seen.append((code[:60], res[:80]))
        if e: bad.append(e)
        return res
    P.lua = lua; P.revive = lambda: 'ok'; P.stand = lambda *a, **k: 'ok'; P.time.sleep = lambda s: None; P.feed = lambda: None
    class R: stdout = '"result":"true"'
    P.subprocess.run = lambda *a, **k: R()
    # the drive path is held to the mock's own world (keys guard, gas moves the car): the self-test car must move >= 2 m and the
    # drive must run to its result (rig 2026-10-30: under the keys guard the old raw engine start left the car dead - the sim showed 0.0 m)
    reset()
    try:
        st = P.drive_selftest()[0]; print('  drive_selftest:', str(st)[:300])
        if st.get('moved_m_on_2s_gas', 0) < 2.0: bad.append(f"drive_selftest: the car did not move in the mock ({st.get('moved_m_on_2s_gas')} m)")
        print('  drive_plant (same Lua state, straight after the self-test as on the rig):', str(P.drive_plant()[0])[:200])
    except SystemExit as e: bad.append(f'drive_selftest stopped: {str(e)[:160]}')
    except Exception as e: bad.append(f'drive_selftest: {type(e).__name__}: {e}')
    for name in ('walk_plant', 'rooms', 'models'):
        reset()
        try: print(f'  {name}:', str(getattr(P, name)())[:300])
        except SystemExit as e: print(f'  {name}: probe stopped (expected with mock values): {str(e)[:90]}')
        except Exception as e: bad.append(f'{name}: {type(e).__name__}: {e}')
    reset()
    try: print('  drive:', str(P.drive(models=['police']))[:300])
    except SystemExit as e: bad.append(f'drive stopped: {str(e)[:160]}')
    except Exception as e: bad.append(f'drive: {type(e).__name__}: {e}')
    for mode in ('open', 'close'):
        reset(); res = run(D.code(mode)); e = check_result(res)
        if e: bad.append(f'doorctl {mode}: {e}')
    for b in bad: print(' ', b)
    print(f'chunks executed: {len(seen) + 2}'); print('JJ_LUASIM_PASS' if not bad else 'JJ_LUASIM_FAIL'); sys.exit(1 if bad else 0)
