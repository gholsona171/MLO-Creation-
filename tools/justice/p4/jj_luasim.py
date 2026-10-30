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
local POS, HD, CREATED, ENG, SEAT, WANT, VEL, ACT, CAP, COLL, SPAWNP = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}   -- every table a mock function uses, declared before any of them
-- the roll-up as the rig has it (2026-10-30): a map garage door that opens by itself while the player is near, unless the door system
-- holds it (registered + locked -> shut; registered + unlocked -> the set ratio). Object 7 at the first spot asked for; opening = 2.6 m up.
local DOOR = {base = nil, reg = false, locked = false, ratio = 0.0}
-- the swing doors, when a run injects DOORP = {{x, y, z, heading}, ...} and SD = {{ang = deg}, ...} (rig 2026-10-30: after the fly 50 of
-- 51 doors were left open by a close that released them after a fixed 4 s): object 100+i; in the door system (hash -> door i) a leaf
-- swings toward its target at 10 deg/s (locked = shut); released, it stays where it is (a map door has no spring)
DOORP, SD = false, false   -- real keys in _G (the catch-all stub would answer a missing one with a function)
local LINK, LOCK, RATIO = {}, {}, {}
local function nearestDoor(x, y, z, r) if not DOORP then return nil end local best, bd = nil, r or 1.6
    for i, d in ipairs(DOORP) do local dd = math.sqrt((d[1] - x) ^ 2 + (d[2] - y) ^ 2 + (d[3] - z) ^ 2) if dd <= bd then best, bd = i, dd end end return best end
function GetClosestObjectOfType(x, y, z, r) if DOORP then local i = nearestDoor(x, y, z, r) return i and (100 + i) or 0 end
    if not DOOR.base then DOOR.base = vector3(x, y, z) end return 7 end
function AddDoorToSystem(h, m, x, y, z) if DOORP then LINK[h] = nearestDoor(x, y, z, 1.6) return end DOOR.reg = true end
function RemoveDoorFromSystem(h) if DOORP then LINK[h] = nil LOCK[h] = nil RATIO[h] = nil return end DOOR.reg, DOOR.locked = false, false end
function IsDoorRegisteredWithSystem(h) if DOORP then return LINK[h] ~= nil end return DOOR.reg end
function DoorSystemSetDoorState(h, st) if DOORP then LOCK[h] = (st == 1) return end DOOR.locked = (st == 1) end
function DoorSystemSetOpenRatio(h, r) if DOORP then RATIO[h] = r return end DOOR.ratio = r end
local function stepDoors(dt) if not DOORP then return end
    for h, i in pairs(LINK) do local tgt = (LOCK[h] and 0.0) or (RATIO[h] or 0.0) * 90.0 local a = SD[i].ang
        if a < tgt then SD[i].ang = math.min(tgt, a + 10.0 * dt) elseif a > tgt then SD[i].ang = math.max(tgt, a - 10.0 * dt) end end end
local function doorOpen() if not DOOR.reg then return 1.0 end if DOOR.locked then return 0.0 end return (DOOR.ratio > 0) and 1.0 or 0.0 end
function GetEntityCoords(e) if DOORP and e >= 100 and DOORP[e - 100] then local d = DOORP[e - 100] return vector3(d[1], d[2], d[3]) end if e == 7 and DOOR.base then return DOOR.base + vector3(0.0, 0.0, 2.6 * doorOpen()) end return POS[e] or vector3(300.0, -1660.0, 29.0) end
function SetEntityCoords(e, x, y, z) POS[e] = vector3(x, y, z) end
function CreateVehicle(h, x, y, z, hd) local e = 1000 + math.random(1, 999) POS[e] = vector3(x, y, z) HD[e] = hd or 0.0 CREATED[e] = T SPAWNP[e] = vector3(x, y, z) return e end
function SetEntityHeading(e, h) HD[e] = h end
function GetEntityHeading(e) if DOORP and e >= 100 and DOORP[e - 100] then return math.fmod(DOORP[e - 100][4] + SD[e - 100].ang, 360.0) end return HD[e] or 0.0 end
function GetEntityRotation(e) return vector3(0.0, 0.0, 0.0) end
-- a new car rests against something at its spawn (rig 2026-10-30: contacts logged AT the spawn, normals like (-0.35, -0.94)) until it
-- has moved 0.3 m: a contact flag with a horizontal normal
local function resting(e) return SPAWNP[e] and POS[e] and #(POS[e] - SPAWNP[e]) < 0.3 end
function GetCollisionNormalOfLastHitForEntity(e) if resting(e) and not (COLL[e] and COLL[e] >= T - 1000) then return vector3(-0.35, -0.94, 0.0) end if COLL[e] and COLL[e] >= T - 1000 and WALL then local h = math.rad(WALL.hd) return vector3(-math.cos(h), -math.sin(h), 0.0) end return vector3(0.0, 0.0, 1.0) end
function HasEntityCollidedWithAnything(e) return (COLL[e] or -1) >= T or resting(e) == true end
function GetVehicleNumberPlateText(v) return "TEST1234" end
function GetGamePool(n) return {} end
function GetHashKey(s) local h = 7 for c in tostring(s):gmatch(".") do h = (h * 31 + c:byte()) % 2147483647 end return h end   -- distinct per string (door-system hashes must not collide)
function PlayerPedId() return 1 end
function DoesEntityExist(e) return POS[e] ~= nil end
function DeleteVehicle(e) POS[e] = nil SEAT[e] = nil VEL[e] = nil ACT[e] = nil CAP[e] = nil COLL[e] = nil SPAWNP[e] = nil end
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
-- motion over game time, fitted to the rig (2026-10-30 self-test, 300 ms slices: speeds 1.05, 3.01, 5.65, 2.99, 0.1, ...): a temp action
-- acts from ~one slice after it is issued until ~one slice after it ends (lag), gas +8 m/s2, reverse -6 m/s2, brake 9 m/s2 toward 0,
-- no action = coasting 1 m/s2; only actions issued for >= 300 ms drive (200 ms slices left the car standing); a SetEntityMaxSpeed cap
-- under 3 m/s keeps a standing car standing; SetVehicleForwardSpeed sets the speed outright. WALL (the jail's west face, set by reset()
-- from the plan): a car whose nose (2.5 m ahead) crosses it outside the sally opening stops there and has collided (COLL).
local LAST = 0
local function step()
    local dt = (T - LAST) / 1000.0 LAST = T
    if dt <= 0 then return end
    stepDoors(dt)
    for v, pos in pairs(POS) do
        local a = ACT[v] if a and T > a.untl then ACT[v] = nil a = nil end
        if a and T < a.from then a = nil end
        local vel = VEL[v] or 0.0 local run = GetIsVehicleEngineRunning(v)
        local stuck = CAP[v] and CAP[v] < 3.0 and math.abs(vel) < 0.1
        if a and run and a.a == 23 and not stuck then vel = vel + 8.0 * dt
        elseif a and run and a.a == 22 and not stuck then vel = vel - 6.0 * dt
        else local dec = (a and a.a == 1) and 9.0 or 1.0 if vel > 0 then vel = math.max(0.0, vel - dec * dt) else vel = math.min(0.0, vel + dec * dt) end end
        if CAP[v] then vel = math.max(-CAP[v], math.min(CAP[v], vel)) end
        VEL[v] = vel
        if vel ~= 0.0 then
            local h = math.rad(HD[v] or 0.0) local np = vector3(pos.x - math.sin(h) * vel * dt, pos.y + math.cos(h) * vel * dt, pos.z)
            if WALL and vel > 0 then
                local hw = math.rad(WALL.hd) local function uvw(p) local dx, dy = p.x - WALL.ox, p.y - WALL.oy return dx * math.cos(hw) + dy * math.sin(hw), -dx * math.sin(hw) + dy * math.cos(hw) end
                local u0 = uvw(pos) local u1, v1 = uvw(np)
                if u0 + 2.5 <= WALL.face and u1 + 2.5 > WALL.face and (v1 - 1.0 < WALL.s0 or v1 + 1.0 > WALL.s1) then np = pos VEL[v] = 0.0 COLL[v] = T + 300 end
            end
            POS[v] = np
        end
    end
end
-- the clock: Wait(0) is one 16 ms frame, Wait(ms) at least one frame; GetGameTimer only ticks 1 ms (so no loop can hang) - a governor
-- ramping per frame sees real frame times (a 50 ms tick per GetGameTimer call made the mock clock outrun the car)
function GetGameTimer() T = T + 1 step() return T end
function Wait(ms) T = T + math.max(16, ms or 0) step() end
function GetEntitySpeed(e) return math.abs(VEL[e] or 0.0) end
function SetEntityMaxSpeed(e, c) CAP[e] = c end
function TaskVehicleTempAction(p, v, a, ms)
    if not POS[v] or (ms or 0) < 300 then return end
    ACT[v] = {a = a, from = T + 300, untl = T + ms + 300}
end
function SetVehicleForwardSpeed(v, sp) if POS[v] then VEL[v] = sp end end
function IsDoorRegisteredWithSystem(h) return false end

function tostring_(x) return tostring(x) end
setmetatable(_G, {__index = function(t, k) return function() return 0 end end})   -- every other native: a stub
'''
_rt = None
def reset():
    global _rt
    import jj_plan as JP, jc_frame as FR
    _rt = lupa.LuaRuntime(); _rt.execute(MOCK)
    _rt.execute('WALL = {ox = %.3f, oy = %.3f, hd = %.4f, face = %.3f, s0 = %.3f, s1 = %.3f}' % (FR.OX, FR.OY, FR.HDEG, JP.JBOX[0], *JP.SALLY['s']))
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
    MV = ('local v=CreateVehicle(1,0.0,0.0,0.0,0.0) _G.__jjv=v Wait(2000) TaskWarpPedIntoVehicle(1,v,-1) exports.c9_vehiclekeys:ToggleEngine() local c0=GetEntityCoords(v) %s '
          'for i=1,10 do TaskVehicleTempAction(1,v,23,%d) Wait(%d) end return tostring(#(GetEntityCoords(v)-c0))')
    reset(); assert float(run(MV % ('', 200, 200))) == 0.0, 'the mock moved the car on 200 ms slices (an unproven drive method)'
    reset(); assert float(run(MV % ('SetEntityMaxSpeed(v,2.8)', 300, 300))) == 0.0, 'the mock moved a standing car under a 2.8 m/s cap'
    reset(); assert float(run(MV % ('', 300, 300))) > 2.0, 'the mock did not move the car on 300 ms slices'
    # the old slice cruise (gas below want-0.8, brake above want+1.0, coast between) must swing far outside 1.5-3.5 under the rig's lag
    reset(); sw = run('local v=CreateVehicle(1,0.0,0.0,0.0,0.0) _G.__jjv=v Wait(2000) TaskWarpPedIntoVehicle(1,v,-1) exports.c9_vehiclekeys:ToggleEngine() local lo,hi=99,0 '
                      'for i=1,40 do local sp=GetEntitySpeed(v) if i>8 then lo=math.min(lo,sp) hi=math.max(hi,sp) end local a=0 if sp<1.7 then a=23 elseif sp>3.5 then a=1 end '
                      'if a~=0 then TaskVehicleTempAction(1,v,a,300) end Wait(300) end return string.format("%.2f:%.2f",lo,hi)')
    lo_, hi_ = map(float, sw.split(':')); print(f'  plant: the old slice cruise swings {lo_:.2f}-{hi_:.2f} m/s in the rig-fitted mock (rig: 0.0-5.75)')
    assert lo_ < 1.5 and hi_ > 3.5, 'the rig-fitted mock lets the old slice cruise hold its speed'
    reset()   # plant: the old raw engine start (spawn engine on, warp, SetVehicleEngineOn) must leave the car dead under the keys guard
    assert run('local v=CreateVehicle(1,0.0,0.0,0.0,0.0) SetVehicleEngineOn(v,true,true,false) Wait(2000) TaskWarpPedIntoVehicle(1,v,-1) SetVehicleEngineOn(v,true,true,false) '
               'local c0=GetEntityCoords(v) TaskVehicleTempAction(1,v,23,300) return tostring(#(GetEntityCoords(v)-c0))') == '0.0', 'the mock keys guard did not stop a raw engine start'
    assert static_check('x = lua("return string.format(\\"%%.2f\\", 1)")'), 'the static check did not catch its planted %%'
    for f in ('jj_probe.py', 'jj_doorctl.py'): bad += [f'{f} {e}' for e in static_check((JL / f).read_text(encoding='utf-8'))]
    import jj_probe as P, jj_doorctl as D
    import tempfile; P.OD = tempfile.mkdtemp(prefix='jj_luasim_')   # the probe's json files from the mock run never land in out/
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
        print('  self-test cruise held 5 s:', st.get('cruise_2_5_held_5s'), 'speeds per slice:', st.get('speeds_per_slice', [])[:40])
        if st.get('moved_m', 0) < 2.0: bad.append(f"drive_selftest: the car did not move in the mock ({st.get('moved_m')} m)")
        if not st.get('ok'): bad.append(f"drive_selftest: not ok in the mock (roll-up {st.get('rollup_shut_open_shut')}, speed held {st.get('cruise_2_5_held_5s')}, speeds {st.get('speeds_per_slice', [])[:12]})")
        pl = P.drive_plant()[0][0]; print('  drive_plant (same Lua state, straight after the self-test as on the rig): impacts', pl['impacts'], pl['first_impacts_u_v_nx_ny_nz'][:2])
        if pl['impacts'] < 1: bad.append('drive_plant: no impact registered while the governor set the speed (the plant must hit the wall)')
    except SystemExit as e: bad.append(f'drive_selftest stopped: {str(e)[:160]}')
    except Exception as e: bad.append(f'drive_selftest: {type(e).__name__}: {e}')
    for name in ('walk_plant', 'rooms', 'models'):
        reset()
        try: print(f'  {name}:', str(getattr(P, name)())[:300])
        except SystemExit as e: print(f'  {name}: probe stopped (expected with mock values): {str(e)[:90]}')
        except Exception as e: bad.append(f'{name}: {type(e).__name__}: {e}')
    reset()
    try:
        dr = P.drive(models=['police'])[0][0]; print('  drive:', str(dr)[:300])
        if not dr.get('ok'): bad.append(f"drive: not ok in the mock (impacts {dr.get('impacts')}, stop {dr.get('stop_nose_u')}, out {dr.get('out_uv')})")
    except SystemExit as e: bad.append(f'drive stopped: {str(e)[:160]}')
    except Exception as e: bad.append(f'drive: {type(e).__name__}: {e}')
    def doors_in(ang):
        reset(); _rt.execute('DOORP = {%s} SD = {}' % ','.join('{%.3f,%.3f,%.3f,%.2f}' % d[1:] for d in D.doors))
        _rt.execute('for i = 1, #DOORP do SD[i] = {ang = %.1f} end' % ang)
    for mode, ang in (('open', 0.0), ('close', 90.0)):
        doors_in(ang); res = run(D.code(mode)); e = check_result(res)
        if e: bad.append(f'doorctl {mode}: {e}')
        ok_, line = D.verdict(mode, res); print(f'  doorctl {mode} (doors start {ang:.0f} deg, swing 10 deg/s):', line)
        if not ok_ or 'WARN' in line: bad.append(f'doorctl {mode}: {line}')
    for b in bad: print(' ', b)
    print(f'chunks executed: {len(seen) + 2}'); print('JJ_LUASIM_PASS' if not bad else 'JJ_LUASIM_FAIL'); sys.exit(1 if bad else 0)
