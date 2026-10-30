"""Offline EXECUTION of the Lua our rig probes send (rig 2026-10-30: a chunk returned the literal '%.2f' - a Python string that was never
%-formatted kept '%%' - and a stubbed dry run that returned made-up numbers could not see it). Each chunk runs in Lua 5.4 (lupa) against
a mock of the FiveM natives it uses: vector2 / vector3 with arithmetic and # length, GetGameTimer that advances, Wait that advances it,
every other native a stub returning a plausible default (0 / false / a vector). The probe functions are then driven with `lua` routed
here, so their own Python parsing reads what the Lua really returns.
Proof: a chunk returning string.format("%%.2f", 1) must be caught (it returns '%.2f', not a number).
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
local POS, HD = {}, {}
function GetEntityCoords(e) return POS[e] or vector3(300.0, -1660.0, 29.0) end
function SetEntityCoords(e, x, y, z) POS[e] = vector3(x, y, z) end
function CreateVehicle(h, x, y, z, hd) local e = 1000 + math.random(1, 999) POS[e] = vector3(x, y, z) HD[e] = hd or 0.0 return e end
function SetEntityHeading(e, h) HD[e] = h end
function GetEntityHeading(e) return HD[e] or 0.0 end
function GetEntityRotation(e) return vector3(0.0, 0.0, 0.0) end
function GetCollisionNormalOfLastHitForEntity(e) return vector3(0.0, 0.0, 1.0) end
function GetVehicleNumberPlateText(v) return "TEST1234" end
function GetGamePool(n) return {} end
function GetHashKey(s) return 12345 end
function PlayerPedId() return 1 end
function GetPedInVehicleSeat(v, s) return 1 end
function DoesEntityExist(e) return POS[e] ~= nil end
function DeleteVehicle(e) POS[e] = nil end
function GetIsVehicleEngineRunning(v) return true end
function GetEntitySpeed(e) return 0.0 end
function IsDoorRegisteredWithSystem(h) return false end
function GetClosestObjectOfType() return 0 end
function tostring_(x) return tostring(x) end
setmetatable(_G, {__index = function(t, k) return function() return 0 end end})   -- every other native: a stub
'''
_rt = None
def run(code):
    """execute one chunk the way t.sh does (as a function body) and return its result as the string the rig would send back."""
    global _rt
    _rt = lupa.LuaRuntime(); _rt.execute(MOCK)
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
    for name in ('drive_selftest', 'walk_plant', 'rooms', 'models'):
        try: getattr(P, name)()
        except SystemExit as e: print(f'  {name}: probe stopped (expected with mock values): {str(e)[:90]}')
        except Exception as e: bad.append(f'{name}: {type(e).__name__}: {e}')
    try: P.drive(models=['police'])
    except SystemExit as e: print(f'  drive: probe stopped (expected with mock values): {str(e)[:90]}')
    except Exception as e: bad.append(f'drive: {type(e).__name__}: {e}')
    for mode in ('open', 'close'):
        res = run(D.code(mode)); e = check_result(res)
        if e: bad.append(f'doorctl {mode}: {e}')
    for b in bad: print(' ', b)
    print(f'chunks executed: {len(seen) + 2}'); print('JJ_LUASIM_PASS' if not bad else 'JJ_LUASIM_FAIL'); sys.exit(1 if bad else 0)
