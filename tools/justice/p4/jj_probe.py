"""Area 4 (Jail I) rig probes (C9Test client 1), each proven on a known answer first (playbook 07); a rig call with no answer raises.
Take the rig with `rig_lock.sh try jc-jail ...` first; this script releases client 1 (tc_release.sh) when it ends, the caller drops the lock.
  rooms   control: the ped on the street outside the sally port is in NO interior; then the ped stood in every room reports the jc_jail
          interior and that room's key (GetRoomKeyFromEntity = GetHashKey(room name)), and the room's timecycle hash
  models  every room drawable registered (IsModelInCdimage), the roll-up registered; control: a planted unstreamed name must read false
  doors   every door (48: airlock, booking, property, stair, corridor, 6 holding cells, 36 cell gates) is a real door object of the right
          model, and the walker goes through the middle of its leaf BOTH ways (pass = past the line by the depth - 0.6 m arrival radius)
  sit     every seat: TaskStartScenarioAtPosition at the sit point, using the scenario after 6 s, root within 0.25 m / 0.15 m
  walk    the prisoner route inside Jail I, leg by leg on the floors and up both stairs: no ragdoll / climb / fall, z never under the floor
  drive   each test vehicle (jj_plan.DRIVE_TEST) driven by the test player from Macdonald St into the sally port to its stop and backed
          out to the street: body health, collisions (HasEntityCollidedWithAnything) and the roll-up's open state logged. Control: the
          same check on a planted kerb-hit (the car driven into the platform) must report a collision
Run: py -3 jj_probe.py rooms models doors sit walk drive   -> out/probe_<name>.json; exit 1 on any FAIL"""
import json, math, sys, time, re, subprocess
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
import jj_plan as J, jj_fit as JF, jc_frame as F
GB = r'C:\Program Files\Git\bin\bash.exe'
L = json.load(open(JL / OD / 'jj_layout.json'))
def lua(code, timeout=60):
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" %d' % timeout, code], capture_output=True, text=True, timeout=timeout + 30)
    m = re.search(r'"result":"(.*?)"(,|\})', r.stdout, re.S)
    if not m: raise SystemExit('PROBE: no answer from the rig - nothing was tested: ' + (r.stdout + r.stderr)[-400:])
    return m.group(1)
def W(u, v): return F.W(u, v)
def feed():
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh srv "$0"', "local P = exports.qbx_core:GetPlayer(1) P.Functions.SetMetaData('hunger', 100) P.Functions.SetMetaData('thirst', 100) return 'fed'"], capture_output=True, text=True, timeout=60)
    if 'fed' not in r.stdout: raise SystemExit('PROBE: could not feed the test player - nothing was tested: ' + r.stdout[-300:])
def revive():
    feed()
    return lua("local p=PlayerPedId() if IsEntityDead(p) or GetEntityHealth(p) < 150 then local c=GetEntityCoords(p) NetworkResurrectLocalPlayer(c.x,c.y,c.z+0.5,GetEntityHeading(p),true,false) Wait(500) p=PlayerPedId() TriggerEvent('qbx_medical:client:playerRevived') end SetEntityHealth(p,200) ClearPedTasksImmediately(p) return tostring(GetEntityHealth(p))", 30)
def stand(u, v, z, h=0.0):
    x, y = W(u, v)
    return lua('local p=PlayerPedId() if IsPedInAnyVehicle(p,false) then TaskLeaveVehicle(p,GetVehiclePedIsIn(p,false),16) Wait(800) end SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) ClearPedTasksImmediately(p) SetEntityCoords(p,%.3f,%.3f,%.3f) SetEntityHeading(p,%.1f) SetFocusPosAndVel(%.3f,%.3f,%.3f,0.0,0.0,0.0) return "ok"' % (x, y, z + 0.9, (h + F.HDEG) % 360, x, y, z))
def walk_to(u, v, z, tmax=20.0, speed=1.0):
    x, y = W(u, v)
    code = ('local p=PlayerPedId() TaskGoStraightToCoord(p,%.3f,%.3f,%.3f,%.2f,%d,0.0,0.0) local o={} local t0=GetGameTimer() local ok=false '
            'while GetGameTimer()-t0 < %d do Wait(250) local c=GetEntityCoords(p) o[#o+1]=string.format("%%.2f:%%.2f:%%.3f:%%d%%d%%d",c.x,c.y,c.z,IsPedRagdoll(p) and 1 or 0,IsPedClimbing(p) and 1 or 0,IsPedFalling(p) and 1 or 0) '
            'if #(vector2(c.x,c.y)-vector2(%.3f,%.3f)) < 0.6 and math.abs(c.z-%.3f) < 1.6 then ok=true break end end return (ok and "OK" or "NO")..";"..table.concat(o,";")') % (x, y, z, speed, int(tmax * 1000), int(tmax * 1000), x, y, z + 1.0)
    # (arrived = within 0.6 m in plan AND the root about 1 m over the target floor: never 'arrived' on another level)
    r = lua(code, int(tmax) + 30).split(';'); log = [tuple(float(a) if i < 3 else a for i, a in enumerate(e.split(':'))) for e in r[1:] if e]
    return r[0] == 'OK', log
STREET = (J.JBOX[0] - 9.0, J.DRIVE_V, J.SALLY_Z - 0.05)             # Macdonald St in front of the sally port (the control spot)
def rooms():
    revive(); stand(*STREET); time.sleep(3)
    o = int(lua('Wait(1500) return tostring(GetInteriorFromEntity(PlayerPedId()))'))
    out = []; ok_all = o == 0
    for r in L['rooms']:
        c = JF.clear(r['key'])[0]; u, v = (c[0] + c[1]) / 2, (c[2] + c[3]) / 2; z = L['zones'][r['key']][0][4]
        if r['key'] == 'stair': u, v = J.ST_IN[0] + 0.7, J.ST_LANE_S[0] + 0.8
        if r['key'] == 'corr': u, v = -15.0, 23.0
        if r['key'] == 'book': u, v = -17.0, 9.0
        if r['key'] == 'hold': u, v = -12.6, 1.5
        if r['key'] == 'block': u, v = -23.0, 27.0
        if r['key'] == 'dstair': u, v = -9.95, 27.3                     # the B1 landing (the region's centre is the wall between the flights)
        if r['key'] == 'tunnel': u, v = 13.5, 27.3
        revive(); stand(u, v, z); time.sleep(2.5)
        res = lua('local p=PlayerPedId() Wait(1000) local i=GetInteriorFromEntity(p) local rk=GetRoomKeyFromEntity(p) local tc=0 if i~=0 then tc=GetInteriorRoomTimecycle(i,GetInteriorRoomIndexByHash(i,rk)) end '
                  'return string.format("%%d:%%d:%%d:%%d:%%d",i,rk,GetHashKey("%s"),tc,GetHashKey("%s"))' % (r['name'], r['timecycle'])).split(':')
        good = int(res[0]) != 0 and int(res[1]) == int(res[2]) and int(res[3]) == int(res[4]); ok_all &= good
        out.append({'room': r['key'], 'interior': int(res[0]), 'room_key': int(res[1]), 'want': int(res[2]), 'timecycle': int(res[3]), 'want_tc': int(res[4]), 'ok': good})
    return {'street_control': o, 'rooms': out}, ok_all
def models():
    names = sorted(L['drawables']) + [J.ROLLUP[0], 'jc_jail_planted_missing']
    revive(); stand(-17.0, 9.0, J.G); time.sleep(4)
    r = lua('local o={} for _,n in ipairs({"%s"}) do o[#o+1]=tostring(IsModelInCdimage(GetHashKey(n))) end return table.concat(o,",")' % '","'.join(names), 30).split(',')
    got = {n: v in ('true', '1') for n, v in zip(names, r)}
    return got, len(r) == len(names) and not got['jc_jail_planted_missing'] and all(v for n, v in got.items() if n != 'jc_jail_planted_missing')
DEPTH = {'sally_lock': 1.0, 'stair_block': 0.9, 'book_stair': 1.2}
def doors(only=None):
    out = []; ok_all = True
    for d in L['doors']:
        if only and not d['name'].startswith(only): continue
        u, v, z = d['pos']; t = math.radians(d['heading']); lu, lv = -math.cos(t), -math.sin(t)          # the leaf runs along the model's -x
        mu, mv = u + lu * 0.65, v + lv * 0.65; nu, nv = -lv, lu; fz = z - J.LEAF_H / 2
        D = DEPTH.get(d['name'], 1.0 if d['name'].startswith(('hold', 'cell')) else 1.5); res = {'door': d['name']}
        for name, k in (('a', 1), ('b', -1)):
            revive(); stand(mu + nu * D * k, mv + nv * D * k, fz); time.sleep(0.8)
            ok, log = walk_to(mu - nu * D * k, mv - nv * D * k, fz, 12.0)
            far = max(((F.L(e[0], e[1])[0] - mu) * nu + (F.L(e[0], e[1])[1] - mv) * nv) * -k for e in log) if log else -9
            res[name] = {'arrived': ok, 'past_line': round(far, 2)}; ok_all &= ok and far > D - 0.65
        x, y = W(u, v)
        found = lua('local o=GetClosestObjectOfType(%.3f,%.3f,%.3f,1.6,GetHashKey("%s"),false,false,false) return tostring(o~=0)' % (x, y, z, d['model']))
        res['object'] = found; ok_all &= found in ('true', '1'); out.append(res)
    return out, ok_all
def sit(rooms=None):
    out = []; ok_all = True
    for i, s in enumerate(L['seats']):
        u, v, z, h, room, sc, what = s
        if rooms and room not in rooms: continue
        x, y = W(u, v); revive(); stand(u, v, z - 0.5); time.sleep(0.5)
        r = lua('local p=PlayerPedId() TaskStartScenarioAtPosition(p,"%s",%.3f,%.3f,%.3f,%.1f,0,true,true) Wait(6000) local c=GetEntityCoords(p) '
                'local u=IsPedUsingScenario(p,"%s") or IsPedActiveInScenario(p) return string.format("%%s:%%.3f:%%.3f:%%.3f",tostring(u),c.x,c.y,c.z)' % (sc, x, y, z, (h + F.HDEG) % 360, sc), 40).split(':')
        using = r[0] in ('true', '1'); dx = math.hypot(float(r[1]) - x, float(r[2]) - y); dz = float(r[3]) - z
        good = using and dx < 0.25 and abs(dz) < 0.15; ok_all &= good
        out.append({'i': i, 'seat': [round(u, 2), round(v, 2), round(z, 2)], 'room': room, 'what': what, 'scenario': sc, 'using': using, 'dxy': round(dx, 3), 'dz_root_minus_seat': round(dz, 3), 'ok': good})
        lua('ClearPedTasksImmediately(PlayerPedId()) return "c"')
    return {'seats': out}, ok_all
G = J.G; ls, ln = sum(J.ST_LANE_S) / 2, sum(J.ST_LANE_N) / 2
WALK = {   # the prisoner's way in Jail I, legs on clear aisles: from the van's side to the platform, booking, a holding cell, the corridor
    'intake': [(-32.0, 11.0, J.SALLY_Z), (-27.35, 8.7, J.SALLY_Z), (-27.35, 15.5, G), (-27.35, 21.2, G), (-24.8, 21.2, G), (-24.8, 16.6, G),
               (-18.5, 15.5, G), (-17.0, 10.0, G), (-15.4, 4.05, G), (-12.4, 4.05, G), (-15.4, 4.05, G), (-15.4, 16.5, G), (-15.5, 19.5, G), (-15.0, 27.3, G),
               (-12.4, 27.3, G), (-12.4, J.DS_BASE1 - 0.7, J.B1 + 3.0), (-9.95, J.DS_BASE1 - 0.7, J.B1 + 3.0), (-9.95, 27.3, J.B1), (-6.0, 27.3, J.B1),
               (30.0, 27.3, J.B1), (J.CAB_C, 26.4, J.B1)],
    'upstairs': [(-17.0, 15.6, G), (-22.6, 16.8, G), (-22.6, ls, G), (J.ST_BASE1 - 0.4, ls, G), (J.ST_TOP1 + 0.6, ls, G + 3.0), (J.ST_TOP1 + 0.6, ln, G + 3.0),
                 (J.ST_BASE1 - 0.6, ln, J.L2), (-22.6, ln, J.L2), (-22.6, 23.4, J.L2), (-23.6, 40.2, J.L2), (-23.6, 44.9, J.TIER2), (-29.1, 44.9, J.TIER2),
                 (-29.1, 24.0, J.TIER2), (-29.1, 44.9, J.TIER2), (-23.6, 44.9, J.TIER2), (-23.6, 40.2, J.L2), (-22.6, 23.4, J.L2)],
}
WALK_SPEED = 1.1                                                    # m/s the walker keeps at speed 1.0 (rig: ~1.2-1.4); time limit per leg
def leg_time(a, b):
    """the time a leg may take: its length at WALK_SPEED, x1.5, + 6 s to start and turn (rig 2026-10-29: a flat 20 s cut the 36 m tunnel
    leg short - the walker was still walking; the next leg arrived)."""
    return 6.0 + 1.5 * math.dist(a[:2], b[:2]) / WALK_SPEED
WALK_PLANT = [(-17.0, 9.0, G), (-29.0, -1.6, G)]                     # booking -> a spot INSIDE Jail I's solid hull, south-west of the property
                                                                    # room: no path of any kind leads there, open doors or not (rig 2026-10-29:
                                                                    # a target in the property room was reached - its door was standing open)
def walk(walks=None):
    out = {}; ok_all = True
    for name, pts in (walks or WALK).items():
        revive(); stand(*pts[0]); time.sleep(1.5); legs = []; prev = pts[0]
        for u, v, z in pts[1:]:
            ok, log = walk_to(u, v, z, leg_time(prev, (u, v))); prev = (u, v, z)
            bad = sum(1 for e in log if e[3] != '000'); zmin = min((e[2] for e in log), default=0)
            zf = min(z, legs[-1]['z'] if legs else pts[0][2]); good = ok and bad == 0 and zmin > zf + 0.6; ok_all &= good     # the root (~1 m up) never sinks under the floor
            legs.append({'to': [u, v], 'z': z, 'arrived': ok, 'bad_states': bad, 'zmin_root': round(zmin, 2), 'ok': good})
        out[name] = legs
    return out, ok_all
def walk_plant():
    """proof: a leg into a wall (booking -> through the property room's wall) must NOT arrive within its scaled time."""
    res, ok = walk({'plant': WALK_PLANT})
    return res, not res['plant'][0]['arrived']
def lift_b1():
    """on screen, like a player (jc-interiors' lifts probe): stood on the B1 landing, walk into the secure cab, [E] (a real key press),
    click L3 in ox_lib's menu, arrive in the L3 cab; then back L3 -> B1. Control: [E] on the landing (outside the cab) opens nothing.
    Needs the deployed resource's lifts.json to carry the B1 stop (jc-interiors' hook)."""
    banks = json.load(open('C:/C9Test/live/resources/[localtest]/justice_center/lifts.json'))
    b = next(b for b in banks if b['bank'] == 'secure'); fl = {f['name']: f for f in b['floors']}
    if 'B1' not in fl: raise SystemExit('PROBE: the deployed secure bank has no B1 stop - nothing was tested')
    def key_e(): subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'C:/C9Test/key.ps1', '-Vk', '69', '-Scan', '18'], capture_output=True, timeout=30)
    def menu(): return lua('return tostring(lib and lib.getOpenContextMenu and lib.getOpenContextMenu() or exports.ox_lib:getOpenContextMenu())', 10)
    out = []; ok_all = True; h = math.radians(b['heading']); fx, fy = -math.sin(h), math.cos(h)
    for a, t in (('B1', 'L3'), ('L3', 'B1')):
        cx, cy, cz = fl[a]['cabs'][0]; u, v = F.L(cx + fx * 2.2, cy + fy * 2.2); revive(); stand(u, v, cz, (b['heading'] + 180.0) % 360); time.sleep(1.0)
        ctl = None
        if a == 'B1': key_e(); time.sleep(1.0); ctl = menu()
        cu, cv = F.L(cx, cy); arrived, log = walk_to(cu, cv, cz, 10.0); time.sleep(0.8); key_e(); time.sleep(1.2); opened = menu()
        r = subprocess.run([GB, '-c', "bash /c/C9Test/oxclick.sh '^%s$'" % t], capture_output=True, text=True, timeout=60).stdout.strip(); time.sleep(4.5)
        e = lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f:%.2f:%.2f",c.x,c.y,c.z)', 10).split(':')
        tx, ty, tz = fl[t]['cabs'][0]; d = math.hypot(float(e[0]) - tx, float(e[1]) - ty); dz = float(e[2]) - (tz + 1.0)
        good = arrived and opened == 'jc_lift' and 'clicked' in r and d < 1.1 and abs(dz) < 0.4 and ctl in (None, 'nil'); ok_all &= good
        out.append({'from': a, 'to': t, 'walked_in': arrived, 'menu': opened, 'click': r[-40:], 'xy_off': round(d, 2), 'dz': round(dz, 2), 'outside_control': ctl, 'ok': good})
        lua('exports.ox_lib:hideContext() return "x"', 10)
    return out, ok_all
ROUTE_L3 = [(31.9, 26.4), (31.9, 36.25), (30.2, 36.25), (29.0, 36.25)]      # courts tower L3 (jc-interiors' secure route): the secure lift's landing,
                                                                               # the secure corridor, through the defendant door into courtroom 3A
def route():
    """the prisoner's whole way, walked by the player ped (gameplay camera, for the route video): sally port platform -> airlock ->
    booking -> holding cell 2 and out -> corridor -> secure stair down -> tunnel -> into the secure lift at B1 -> [E] + L3 in the menu ->
    the L3 secure corridor -> the defendant door -> courtroom 3A. Every leg must arrive with no ragdoll / climb / fall; the lift must
    deliver the ped to the L3 cab. Needs the secure bank's B1 stop deployed (lifts.json)."""
    legs = []; ok_all = True
    revive(); pts = WALK['intake']; stand(*pts[0]); time.sleep(1.5)
    prev = pts[0]
    for u, v, z in pts[1:] + [(J.CAB_C, J.SEC_CAB[2] + 1.1, J.B1)]:
        ok, log = walk_to(u, v, z, leg_time(prev, (u, v))); prev = (u, v, z); bad = sum(1 for e in log if e[3] != '000'); good = ok and bad == 0; ok_all &= good
        legs.append({'to': [round(u, 2), round(v, 2)], 'z': z, 'arrived': ok, 'bad_states': bad, 'ok': good})
    banks = json.load(open('C:/C9Test/live/resources/[localtest]/justice_center/lifts.json'))
    b = next(b for b in banks if b['bank'] == 'secure'); fl = {f['name']: f for f in b['floors']}
    if 'B1' not in fl: raise SystemExit('PROBE: the deployed secure bank has no B1 stop - nothing was tested')
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'C:/C9Test/key.ps1', '-Vk', '69', '-Scan', '18'], capture_output=True, timeout=30); time.sleep(1.2)
    r = subprocess.run([GB, '-c', "bash /c/C9Test/oxclick.sh '^L3$'"], capture_output=True, text=True, timeout=60).stdout.strip(); time.sleep(5.0)
    e = lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f:%.2f:%.2f",c.x,c.y,c.z)', 10).split(':')
    tx, ty, tz = fl['L3']['cabs'][0]; arrived = math.hypot(float(e[0]) - tx, float(e[1]) - ty) < 1.1 and abs(float(e[2]) - (tz + 1.0)) < 0.4
    legs.append({'lift': 'B1 -> L3', 'click': r[-40:], 'arrived': arrived, 'ok': arrived}); ok_all &= arrived
    prev = F.L(tx, ty)
    for u, v in ROUTE_L3:
        ok, log = walk_to(u, v, tz, leg_time(prev, (u, v))); prev = (u, v); bad = sum(1 for e_ in log if e_[3] != '000'); good = ok and bad == 0; ok_all &= good
        legs.append({'to': [u, v], 'z': tz, 'arrived': ok, 'bad_states': bad, 'ok': good})
    return legs, ok_all
RUX_ = None
def _rollup():
    """the roll-up's placement (world) and its door-system / read-back Lua helpers: the door object is looked up AGAIN at every read
    (rig 2026-10-30: a handle taken before the door was registered read 0 while a car drove under the open door) and its opening is
    measured against its PLACEMENT (position + pitch / roll), not against a first reading.
    dsys(mode): "shut" = registered, ratio 0, LOCKED, not held open, rolled down (5 s); "open" = registered, unlocked, ratio 1, held open
    (5 s); "release" = unlocked and out of the door system (the map default: rig 2026-10-30, the roll-up as a plain map door opens by
    itself as soon as the player stands near it - it read 5.41 open at the start of the self-test, right after DOORCTL close)."""
    rux, ruy = W(J.JBOX[0] + 0.275, J.DRIVE_V); ruz = J.SALLY_Z + J.ROLLUP[2] / 2
    lua_ = ('local DH=GetHashKey("jjdrive_rollup") local RP=vector3(%.3f,%.3f,%.3f) local RM=GetHashKey("%s") '
            'local function dopen() local o=GetClosestObjectOfType(RP.x,RP.y,RP.z,4.0,RM,false,false,false) if o==0 then return -1.0 end '
            'local r_=GetEntityRotation(o,2) return #(GetEntityCoords(o)-RP)+(math.abs(r_.x)+math.abs(r_.y))/30.0 end '
            'local function reg() if not IsDoorRegisteredWithSystem(DH) then AddDoorToSystem(DH,RM,RP.x,RP.y,RP.z,false,false,false) end end '
            'local function dsys(mode) if mode=="open" then reg() DoorSystemSetDoorState(DH,0,false,true) DoorSystemSetOpenRatio(DH,1.0,false,true) DoorSystemSetHoldOpen(DH,true) Wait(5000) '
            'elseif mode=="shut" then reg() DoorSystemSetHoldOpen(DH,false) DoorSystemSetOpenRatio(DH,0.0,false,true) DoorSystemSetDoorState(DH,1,false,true) Wait(5000) '
            'else if IsDoorRegisteredWithSystem(DH) then DoorSystemSetDoorState(DH,0,false,true) RemoveDoorFromSystem(DH) end end end ') % (rux, ruy, ruz, J.ROLLUP[0])
    return lua_
# every vehicle near the bay goes before a test car is made - mission entities too (ClearAreaOfVehicles leaves those: a car left by an
# earlier run blocked two test cars at their spawn, rig 2026-10-30). Returns how many were removed and how many are still there.
# ONE driving method for the self-test, the plant and the drive (rig 2026-10-30: the self-test's 300 ms gas slices moved the car 27 m;
# the drive's 200 ms slices left it standing, -0.01 m). A slice = the temp action (23 gas, 22 reverse, 1 brake) issued for SLICE_MS and
# re-issued after it, never shorter; meanwhile tk() runs every frame. Speed is capped with SetEntityMaxSpeed so a gas slice cannot
# overshoot. Steering = heading hold on the drive line: a drift over 1.5 deg is set back to the line heading (the plant starts 4.5 m off
# the line and holds the same heading, so it drives straight into the wall). No AI drive task.
SLICE_MS = 300
DRV = ('local function slice(v,a,tk) TaskVehicleTempAction(PlayerPedId(),v,a,%d) local t=GetGameTimer() while GetGameTimer()-t<%d do Wait(0) if tk then tk() end end end '
       'local drift=0.0 local function hold(v,h) local d=math.abs(math.fmod((GetEntityHeading(v)-h)+540.0,360.0)-180.0) if d>drift then drift=d end if d>1.5 then SetEntityHeading(v,h) end end '
       % (SLICE_MS, SLICE_MS))
PURGE = ('local function purge(x,y,z,rad) local n=0 for _,veh in ipairs(GetGamePool("CVehicle")) do if #(GetEntityCoords(veh)-vector3(x,y,z))<rad then '
         'SetEntityAsMissionEntity(veh,true,true) DeleteVehicle(veh) if DoesEntityExist(veh) then DeleteEntity(veh) end n=n+1 end end Wait(300) local left=0 '
         'for _,veh in ipairs(GetGamePool("CVehicle")) do if #(GetEntityCoords(veh)-vector3(x,y,z))<rad then left=left+1 end end return n,left end ')
def _spawn(m, su, sv, h_in):
    """the car on the line, then the player in its driver's seat with the engine started THROUGH THE KEYS SCRIPT.
    (1) the ped ready: out of any vehicle (also one it is still getting out of), not ragdolled / falling / entering, up to 5 s;
    (2) purge the bay and the street in front of it (30 m), spawn, wait until the car is networked and ours (request control), up to 4 s;
    (3) the server's key; (4) the seat: up to 3 warps then up to 3 direct seatings, each given 1 s, until GetPedInVehicleSeat(v,-1) is
    the player (rig 2026-10-30: the warp into the plant car straight after the self-test left the player outside);
    (5) the keys script's CanDrive, then its ToggleEngine (rig 2026-10-30: c9_vehiclekeys disableAutoStart switches a raw
    SetVehicleEngineOn off every frame; the car crept 0.14 m), the engine still running 1.5 s later, fuel > 0 (ox_fuel state bag).
    Any step failing raises 'nothing was tested' with what the game reported. Returns (purged, {engine, fuel, fuel_state, seat_tries})."""
    sx, sy = W(su, sv); bx, by = W(J.JBOX[0] - 2.0, J.DRIVE_V)
    revive(); stand(J.JBOX[0] - 16.0, J.DRIVE_V + 4.0, J.SALLY_Z); time.sleep(1)
    sp = lua((PURGE + 'local p=PlayerPedId() local t=GetGameTimer() if IsPedInAnyVehicle(p,false) then TaskLeaveVehicle(p,GetVehiclePedIsIn(p,false),16) end '
              'while GetGameTimer()-t<5000 and (IsPedInAnyVehicle(p,true) or IsPedRagdoll(p) or IsPedFalling(p) or IsPedGettingIntoAVehicle(p)) do Wait(100) end '
              'local rdy=not IsPedInAnyVehicle(p,true) and not IsPedRagdoll(p) and not IsPedFalling(p) '
              'local h=GetHashKey("%s") RequestModel(h) t=GetGameTimer() while not HasModelLoaded(h) and GetGameTimer()-t<8000 do Wait(50) end '
              'local n,left=purge(%.3f,%.3f,%.3f,30.0) '
              'local v=CreateVehicle(h,%.3f,%.3f,%.3f,%.1f,true,false) SetEntityAsMissionEntity(v,true,true) SetVehicleOnGroundProperly(v) SetEntityHeading(v,%.1f) '
              'FreezeEntityPosition(v,false) SetVehicleUndriveable(v,false) _G.__jjv=v t=GetGameTimer() '
              'while GetGameTimer()-t<4000 and not (NetworkGetEntityIsNetworked(v) and NetworkHasControlOfEntity(v)) do NetworkRequestControlOfEntity(v) Wait(50) end '
              'local net=NetworkGetEntityIsNetworked(v) and NetworkHasControlOfEntity(v) Wait(300) local c=GetEntityCoords(v) '
              'return GetVehicleNumberPlateText(v)..";"..string.format("%%.2f;%%.2f;%%.1f;%%d;%%d;",c.x,c.y,GetEntityHeading(v),n,left)..tostring(rdy)..";"..tostring(net)')
             % (m, bx, by, J.SALLY_Z, sx, sy, J.SALLY_Z + 0.5, h_in, h_in), 40).split(';')
    plate = sp[0].strip(); cu, cv = F.L(float(sp[1]), float(sp[2])); hd = abs(((float(sp[3]) - h_in) + 540.0) % 360.0 - 180.0); purged, left = int(sp[4]), int(sp[5])
    rdy, net = sp[6].strip() in ('true', '1'), sp[7].strip() in ('true', '1')
    def gone(why):
        lua('local v=_G.__jjv if v and DoesEntityExist(v) then SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) end return "x"')
        raise SystemExit(f'PROBE: {why} - nothing was tested')
    if left > 0: gone(f'{left} vehicle(s) still in the bay / street after the purge')
    if not rdy: gone('the player was still in / getting out of a vehicle, ragdolled or falling 5 s after being stood up')
    if not net: gone(f'{m} was not networked and owned by the test client within 4 s')
    if abs(cv - sv) > 0.4 or abs(cu - su) > 0.6 or hd > 3.0: gone(f'{m} did not spawn on the line ({cu:.2f}, {cv:.2f}, heading off {hd:.1f})')
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh srv "$0" 20', "return tostring(exports.c9_vehiclekeys:GiveKeysByPlate(1,'%s',true))" % plate], capture_output=True, text=True, timeout=60)
    if 'true' not in r.stdout: gone('the server gave no key: ' + r.stdout[-200:])
    w = lua('local p=PlayerPedId() local v=_G.__jjv local tries,how=0,"" '
            'while GetPedInVehicleSeat(v,-1)~=p and tries<6 do tries=tries+1 ClearPedTasksImmediately(p) '
            'if tries<=3 then TaskWarpPedIntoVehicle(p,v,-1) how="warp" else SetPedIntoVehicle(p,v,-1) how="set" end '
            'local t=GetGameTimer() while GetGameTimer()-t<1000 and GetPedInVehicleSeat(v,-1)~=p do Wait(50) end end '
            'local seat=GetPedInVehicleSeat(v,-1)==p local occ=GetPedInVehicleSeat(v,-1) '
            'local diag=string.format("occupant %d, ped in a vehicle %s, ragdoll %s, dead %s, door lock %d, car exists %s",occ,tostring(IsPedInAnyVehicle(p,true)),'
            'tostring(IsPedRagdoll(p)),tostring(IsEntityDead(p)),GetVehicleDoorLockStatus(v),tostring(DoesEntityExist(v))) '
            'local can=false if seat then local t=GetGameTimer() while GetGameTimer()-t<6000 and not exports.c9_vehiclekeys:CanDrive(v) do Wait(100) end Wait(500) '
            'can=exports.c9_vehiclekeys:CanDrive(v) if can and not GetIsVehicleEngineRunning(v) then exports.c9_vehiclekeys:ToggleEngine() end Wait(1500) end '
            'local tf=GetGameTimer() while seat and Entity(v).state.fuel==nil and GetGameTimer()-tf<3000 do Wait(100) end local fs=Entity(v).state.fuel return tostring(seat)..";"..tostring(can)..";"..tostring(GetIsVehicleEngineRunning(v))..";"'
            '..string.format("%.1f",GetVehicleFuelLevel(v))..";"..tostring(fs)..";"..tries..";"..how..";"..diag', 40).split(';')
    seat, can, run = (x in ('true', '1') for x in w[:3]); fuel = float(w[3]); fs = w[4].strip(); tries, how, diag = int(w[5]), w[6], w[7]
    if not seat: gone(f"the player is not in {m}'s driver seat after {tries} tries ({how}): {diag}")
    if not can: gone('the keys script says the player cannot drive it (CanDrive false)')
    if not run: gone('the engine is not running 1.5 s after the keys script started it')
    if fuel <= 0: gone(f'fuel {fuel:.1f} (state bag {fs})')
    return purged, {'engine': run, 'fuel': fuel, 'fuel_state': fs, 'seat_tries': f'{tries} {how}'.strip()}
def drive_selftest():
    """each piece of the drive test on its own (rig 2026-10-30: the first two cars never moved, the roll-up read 0 while a car drove
    under it): (1) the roll-up read-back through the door system: forced shut (locked) ~0, opened > 1.0, shut again ~0, then released; (2) a car spawned in the cleared
    street on the line moves >= 2 m on 2 s of gas; (3) it is deleted for certain."""
    h_in = (270.0 + F.HDEG) % 360; res = {}
    r = lua((_rollup() + 'dsys("shut") local a=dopen() dsys("open") local b=dopen() dsys("shut") local c=dopen() dsys("release") return string.format("%.2f:%.2f:%.2f",a,b,c)'), 60).split(':')
    a, b, c = map(float, r); res['rollup_shut_open_shut'] = [a, b, c]; door_ok = a >= 0 and a < 0.3 and b > 1.0 and c < 0.3
    su = J.JBOX[0] - 16.0; purged, eng = _spawn('police', su, J.DRIVE_V, h_in)
    # the shared method (DRV): 8 gas slices on the line heading, then brake; the engine is read during the gas (the keys guard)
    r = lua((DRV + 'local p=PlayerPedId() local v=_G.__jjv local c0=GetEntityCoords(v) local off=0 SetEntityMaxSpeed(v,30.0) '
             'for i=1,8 do slice(v,23) hold(v,%.1f) if not GetIsVehicleEngineRunning(v) then off=off+1 end end slice(v,1) slice(v,1) slice(v,1) slice(v,1) '
             'local d=#(GetEntityCoords(v)-c0) local fr=IsEntityPositionFrozen(v) TaskLeaveVehicle(p,v,16) Wait(1500) SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) Wait(200) '
             'return string.format("%%.2f:%%s:%%s:%%d:%%.1f",d,tostring(fr),tostring(not DoesEntityExist(v)),off,drift)') % h_in, 40).split(':')
    moved, frozen, gone, off = float(r[0]), r[1], r[2] in ('true', '1'), int(r[3]); res['engine_off_reads_during_gas'] = off; res['max_heading_drift_deg'] = float(r[4])
    res.update({'purged_before_spawn': purged, 'engine_fuel': eng, 'moved_m_on_2s_gas': moved, 'frozen': frozen, 'deleted': gone})
    ok = door_ok and moved >= 2.0 and gone; res['ok'] = ok
    return res, ok
def drive(models=None, plant=False):
    """the test player drives each vehicle from Macdonald St straight into the sally port to its stop and backs it straight out to the
    street. The roll-up is opened through the DOOR SYSTEM for the car's whole run (in and out), as the client's lock system will (Antonio
    2026-10-29: "client add locks"), then shut and released. Every car starts on a purged street, on the line, keyed, engine on
    (_spawn) and must be seen moving; it is driven by the shared method DRV (gas / reverse slices, heading hold); the stop: the speed tapers with the distance left and the brakes go on in time (rig 2026-10-30:
    the van overshot to -28.02). Logged: impacts (wall / door / kerb faces, debounced - not floor contact) going in and backing out
    with the first five impacts' spot and normal; body health; the nose stop; the final spot; the roll-up's opening on each leg
    (read from the door object found anew each time, against its placement). plant=True: 4.5 m off the line - it must hit the wall."""
    out = []; ok_all = True; h_in = (270.0 + F.HDEG) % 360
    dv = J.DRIVE_V + (-4.5 if plant else 0.0)
    for m in (models or J.DRIVE_TEST):
        L_ = J.VEHICLES.get({'police': 'police4', 'police3': 'police4'}.get(m, m), (2.0, 1.6, 5.0))[2]
        purged, eng = _spawn(m, J.JBOX[0] - 9.0 - L_ / 2, dv, h_in)
        r = lua((_rollup() + DRV + 'local p=PlayerPedId() local v=_G.__jjv local b0=GetVehicleBodyHealth(v) local hits,last,hin=0,0,0 local imp={} '
                 'local O=vector2(%.3f,%.3f) local Hd=vector2(math.cos(math.rad(%.4f)),math.sin(math.rad(%.4f))) local Nm=vector2(-Hd.y,Hd.x) '
                 'local function uv() local c=GetEntityCoords(v) local d=vector2(c.x,c.y)-O return d.x*Hd.x+d.y*Hd.y, d.x*Nm.x+d.y*Nm.y end local function u() local a=uv() return a end '
                 'local half=%.2f local ud=%.3f local dIn,dOut=0.0,0.0 local u0=u() '
                 'local function tick() if HasEntityCollidedWithAnything(v) then local n=GetCollisionNormalOfLastHitForEntity(v) if math.abs(n.z)<0.6 and GetGameTimer()-last>600 then '
                 'hits=hits+1 last=GetGameTimer() if #imp<5 then local a,b=uv() imp[#imp+1]=string.format("%%.2f/%%.2f/%%.2f/%%.2f/%%.2f",a,b,n.x,n.y,n.z) end end end end '
                 'local Hh=%.1f '
                 'dsys("open") local dPre=dopen() '
                 'local t0=GetGameTimer() while GetGameTimer()-t0<50000 do local rem=%.3f-(u()+half) local sp=GetEntitySpeed(v) '
                 'if rem<=0.25+sp*0.5 then break end if math.abs(u()+half-ud)<4.0 then dIn=math.max(dIn,dopen()) end '
                 'local want=math.max(0.6,math.min(2.5,rem*0.3)) SetEntityMaxSpeed(v,want+0.3) slice(v,sp<want and 23 or 1,tick) hold(v,Hh) end '
                 'for i=1,8 do slice(v,1,tick) end hin=hits local cin=GetEntityCoords(v) local moved=u()-u0 local t1=GetGameTimer() SetEntityMaxSpeed(v,2.0) '
                 'while GetGameTimer()-t1<60000 and u() > %.3f do local rear=u()-half if math.abs(rear-ud)<4.0 then dOut=math.max(dOut,dopen()) end '
                 'slice(v,GetEntitySpeed(v)<1.8 and 22 or 1,tick) hold(v,Hh) end '
                 'for i=1,7 do slice(v,1,tick) end SetEntityMaxSpeed(v,500.0) local c2=GetEntityCoords(v) local b1=GetVehicleBodyHealth(v) TaskLeaveVehicle(p,v,16) Wait(1500) '
                 'SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) Wait(200) local gone=not DoesEntityExist(v) dsys("shut") dsys("release") '
                 'return string.format("%%d:%%.1f:%%.1f:%%.2f:%%.2f:%%.2f:%%.2f:%%.2f:%%.2f:%%d:%%s:%%.2f:%%.2f:%%.1f:",hits,b0,b1,cin.x,cin.y,c2.x,c2.y,dIn,dOut,hin,tostring(gone),dPre,moved,drift)..table.concat(imp,",")')
                % (F.OX, F.OY, F.HDEG, F.HDEG, L_ / 2, J.JBOX[0] + 0.275, h_in, J.DRIVE_STOP, J.JBOX[0] - 8.0), 220).split(':')
        hits, b0, b1 = int(r[0]), float(r[1]), float(r[2]); ui, vi = F.L(float(r[3]), float(r[4])); uo, vo = F.L(float(r[5]), float(r[6]))
        d_in, d_out, h_in_ = float(r[7]), float(r[8]), int(r[9]); gone = r[10] in ('true', '1'); d_pre, moved = float(r[11]), float(r[12])
        drift = float(r[13]); imps = [x for x in r[14].split(',') if x]; nose = ui + L_ / 2
        if moved < 2.0: raise SystemExit(f'PROBE: {m} never moved ({moved:.2f} m; engine {eng}) - nothing was tested')
        good = hits == 0 and b1 >= b0 - 1.0 and J.DRIVE_STOP - 1.0 < nose < J.PLATFORM[0] - 0.3 and uo < J.JBOX[0] - 5.0 and gone and d_pre > 1.0
        out.append({'vehicle': m, 'purged_before_spawn': purged, 'impacts': hits, 'impacts_going_in': h_in_, 'impacts_backing_out': hits - h_in_,
                    'first_impacts_u_v_nx_ny_nz': imps, 'max_heading_drift_deg': drift, 'body_before': b0, 'body_after': b1, 'stop_nose_u': round(nose, 2), 'planned_stop_u': J.DRIVE_STOP,
                    'pass_window': [round(J.DRIVE_STOP - 1.0, 2), round(J.PLATFORM[0] - 0.3, 2)], 'stop_v': round(vi, 2), 'out_uv': [round(uo, 2), round(vo, 2)],
                    'car_deleted': gone, 'rollup_open_before_driving': round(d_pre, 2), 'rollup_open_going_in': round(d_in, 2), 'rollup_open_backing_out': round(d_out, 2), 'ok': good})
        ok_all &= good
    return out, ok_all
def drive_plant():
    res, ok = drive(models=['police'], plant=True)                      # aimed 2 m past the stop and 4 m to the side: into the platform / ramp
    return res, any(r['impacts'] > 0 for r in res)                     # proof: an off-line drive must register an IMPACT (not just contact)
if __name__ == '__main__':
    fails = 0
    try:
        for name in sys.argv[1:]:
            res, ok = globals()[name]()
            json.dump(res, open(JL / OD / f'probe_{name}.json', 'w'), indent=1)
            print(f'PROBE_{name.upper()}_{"PASS" if ok else "FAIL"}', json.dumps(res)[:700], flush=True); fails += not ok
    finally:
        try: revive(); stand(*STREET)
        except SystemExit: pass
        subprocess.run([GB, '-c', 'bash /c/C9Test/tc_release.sh'], capture_output=True, text=True, timeout=60)
    sys.exit(1 if fails else 0)
