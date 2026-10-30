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
def drive(models=None, plant=False):
    """the test player drives each vehicle from Macdonald St straight into the sally port to its stop and backs it straight out to the
    street. The ROLL-UP IS OPENED THROUGH THE DOOR SYSTEM BOTH WAYS, held open for the whole run of each car and shut + released after
    it (Antonio 2026-10-29: "client add locks" - the server's lock system runs this door; the game's own auto-open fired for the first
    car only, rig 2026-10-30). Each car: the spawn spot is cleared of vehicles first and the car must stand on the door's centre line
    facing the door before it moves (a leftover car from the previous run pushed police3 8 m off the line); it is deleted for certain
    afterwards (DeleteVehicle, then checked). Logged: impacts (wall / door / kerb faces, debounced - not floor contact) going in and
    backing out, with the first five impacts' spot and normal; body health; the nose stop (short of the platform kerb); the final spot;
    the roll-up's physical opening on each leg. plant=True: the same drive 4.5 m off the centre line - it must hit the wall."""
    out = []; ok_all = True; h_in = (270.0 + F.HDEG) % 360                 # facing +u (into the bay)
    dv = J.DRIVE_V + (-4.5 if plant else 0.0)
    rux, ruy = W(J.JBOX[0] + 0.275, J.DRIVE_V); ruz = J.SALLY_Z + J.ROLLUP[2] / 2
    door = ('local DH=GetHashKey("jjdrive_rollup") local function dsys(open) if not IsDoorRegisteredWithSystem(DH) then '
            'AddDoorToSystem(DH,GetHashKey("%s"),%.3f,%.3f,%.3f,false,false,false) end if open then DoorSystemSetDoorState(DH,0,false,true) '
            'DoorSystemSetOpenRatio(DH,1.0,false,true) DoorSystemSetHoldOpen(DH,true) else DoorSystemSetHoldOpen(DH,false) DoorSystemSetOpenRatio(DH,0.0,false,true) '
            'DoorSystemSetDoorState(DH,1,false,true) Wait(4500) DoorSystemSetDoorState(DH,0,false,true) RemoveDoorFromSystem(DH) end end ') % (J.ROLLUP[0], rux, ruy, ruz)
    for m in (models or J.DRIVE_TEST):
        L_ = J.VEHICLES.get({'police': 'police4', 'police3': 'police4'}.get(m, m), (2.0, 1.6, 5.0))[2]
        su = J.JBOX[0] - 9.0 - L_ / 2; sx, sy = W(su, dv)
        revive(); stand(J.JBOX[0] - 16.0, J.DRIVE_V + 4.0, J.SALLY_Z); time.sleep(1)
        sp = lua(('local h=GetHashKey("%s") RequestModel(h) local t=GetGameTimer() while not HasModelLoaded(h) and GetGameTimer()-t<8000 do Wait(50) end '
                  'ClearAreaOfVehicles(%.3f,%.3f,%.3f,12.0,false,false,false,false,false) Wait(500) '
                  'local v=CreateVehicle(h,%.3f,%.3f,%.3f,%.1f,true,false) SetEntityAsMissionEntity(v,true,true) SetVehicleOnGroundProperly(v) '
                  'SetEntityHeading(v,%.1f) SetVehicleEngineOn(v,true,true,false) _G.__jjv=v Wait(800) local c=GetEntityCoords(v) '
                  'return GetVehicleNumberPlateText(v)..";"..string.format("%%.2f;%%.2f;%%.1f",c.x,c.y,GetEntityHeading(v))')
                 % (m, sx, sy, J.SALLY_Z, sx, sy, J.SALLY_Z + 0.5, h_in, h_in), 30).split(';')
        plate = sp[0].strip(); cu, cv = F.L(float(sp[1]), float(sp[2])); hd = abs(((float(sp[3]) - h_in) + 540.0) % 360.0 - 180.0)
        if abs(cv - dv) > 0.4 or abs(cu - su) > 0.6 or hd > 3.0:
            lua('local v=_G.__jjv if v and DoesEntityExist(v) then SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) end return "x"')
            raise SystemExit(f'PROBE: {m} did not spawn on the line ({cu:.2f}, {cv:.2f}, heading off {hd:.1f}) - nothing was tested')
        r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh srv "$0" 20', "return tostring(exports.c9_vehiclekeys:GiveKeysByPlate(1,'%s',true))" % plate], capture_output=True, text=True, timeout=60)
        if 'true' not in r.stdout: raise SystemExit('PROBE: the server gave no key - nothing was tested: ' + r.stdout[-200:])
        # the lock system opens the door for the arriving car and keeps it open until the car is back on the street (dsys)
        r = lua((door + 'local p=PlayerPedId() local v=_G.__jjv TaskWarpPedIntoVehicle(p,v,-1) Wait(1500) local b0=GetVehicleBodyHealth(v) local hits,last,hin=0,0,0 local imp={} '
                 'local O=vector2(%.3f,%.3f) local Hd=vector2(math.cos(math.rad(%.4f)),math.sin(math.rad(%.4f))) local Nm=vector2(-Hd.y,Hd.x) '
                 'local function uv() local c=GetEntityCoords(v) local d=vector2(c.x,c.y)-O return d.x*Hd.x+d.y*Hd.y, d.x*Nm.x+d.y*Nm.y end local function u() local a=uv() return a end '
                 'local half=%.2f local ud=%.3f local dobj=GetClosestObjectOfType(%.3f,%.3f,%.3f,3.0,GetHashKey("%s"),false,false,false) '
                 'local dp0=dobj~=0 and GetEntityCoords(dobj) or vector3(0,0,0) local dr0=dobj~=0 and GetEntityRotation(dobj,2) or vector3(0,0,0) local dIn,dOut=0.0,0.0 '
                 'local function dopen() if dobj==0 then return -1.0 end local r_=GetEntityRotation(dobj,2) return #(GetEntityCoords(dobj)-dp0)+math.abs(r_.x-dr0.x)/30.0+math.abs(r_.y-dr0.y)/30.0 end '
                 'local function tick() if HasEntityCollidedWithAnything(v) then local n=GetCollisionNormalOfLastHitForEntity(v) if math.abs(n.z)<0.6 and GetGameTimer()-last>600 then '
                 'hits=hits+1 last=GetGameTimer() if #imp<5 then local a,b=uv() imp[#imp+1]=string.format("%%.2f/%%.2f/%%.2f/%%.2f/%%.2f",a,b,n.x,n.y,n.z) end end end end '
                 'local function drive(action,ms) TaskVehicleTempAction(p,v,action,ms) local t=GetGameTimer() while GetGameTimer()-t<ms do Wait(0) tick() end end '
                 'dsys(true) Wait(3500) '
                 'local t0=GetGameTimer() while GetGameTimer()-t0<45000 do local rem=%.3f-(u()+half) if rem<=0.0 then break end '
                 'if math.abs(u()+half-ud)<4.0 then dIn=math.max(dIn,dopen()) end local want=math.max(0.7,math.min(2.5,rem*0.35)) drive(GetEntitySpeed(v)<want and 23 or 6,250) end '
                 'drive(1,2000) hin=hits local cin=GetEntityCoords(v) local t1=GetGameTimer() '
                 'while GetGameTimer()-t1<60000 and u() > %.3f do local rear=u()-half if math.abs(rear-ud)<4.0 then dOut=math.max(dOut,dopen()) end '
                 'drive(GetEntitySpeed(v)<1.8 and 22 or 6,250) end '
                 'drive(1,2000) local c2=GetEntityCoords(v) local b1=GetVehicleBodyHealth(v) TaskLeaveVehicle(p,v,16) Wait(1500) '
                 'SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) Wait(200) local gone=not DoesEntityExist(v) dsys(false) '
                 'return string.format("%%d:%%.1f:%%.1f:%%.2f:%%.2f:%%.2f:%%.2f:%%.2f:%%.2f:%%d:%%s:",hits,b0,b1,cin.x,cin.y,c2.x,c2.y,dIn,dOut,hin,tostring(gone))..table.concat(imp,",")')
                % (F.OX, F.OY, F.HDEG, F.HDEG, L_ / 2, J.JBOX[0] + 0.275, rux, ruy, ruz, J.ROLLUP[0], J.DRIVE_STOP, J.JBOX[0] - 8.0), 200).split(':')
        hits, b0, b1 = int(r[0]), float(r[1]), float(r[2]); ui, vi = F.L(float(r[3]), float(r[4])); uo, vo = F.L(float(r[5]), float(r[6]))
        d_in, d_out, h_in_ = float(r[7]), float(r[8]), int(r[9]); gone = r[10] in ('true', '1'); imps = [x for x in r[11].split(',') if x]
        nose = ui + L_ / 2
        good = hits == 0 and b1 >= b0 - 1.0 and J.DRIVE_STOP - 1.0 < nose < J.PLATFORM[0] - 0.3 and uo < J.JBOX[0] - 5.0 and gone
        out.append({'vehicle': m, 'spawn_uv': [round(cu, 2), round(cv, 2)], 'impacts': hits, 'impacts_going_in': h_in_, 'impacts_backing_out': hits - h_in_,
                    'first_impacts_u_v_nx_ny_nz': imps, 'body_before': b0, 'body_after': b1, 'stop_nose_u': round(nose, 2), 'planned_stop_u': J.DRIVE_STOP,
                    'platform_kerb_u': J.PLATFORM[0], 'stop_v': round(vi, 2), 'out_uv': [round(uo, 2), round(vo, 2)], 'car_deleted': gone,
                    'rollup_open_going_in': round(d_in, 2), 'rollup_open_backing_out': round(d_out, 2), 'ok': good})
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
