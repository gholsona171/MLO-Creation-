"""Phase 3 rig probes (C9Test client 1), each proven on a known answer first (playbook 07). Rig calls with no answer raise.
  interior  the galleria is a loaded interior: GetInteriorAtCoords at the room's centre != 0 and ready; the ped stood on its floor
            reports that interior and room key; the room's timecycle hash = GetHashKey(name). Control: a point on the plaza outside
            must report interior 0.
  doors     each of the 4 entrance leaves is a real door object (GetClosestObjectOfType at its spot, the right model); the ped walks
            through the middle of each LEAF both ways (from 2 m outside to 1.5 m inside and back): pass = 1 m past the door line.
            No lock script touches them (none is registered).
  walk      the visitor's route: plaza -> ENTRY doors -> queue -> lane A's walk-through detector -> the secure side -> the galleria ->
            rect B -> back through the exit lane -> EXIT doors -> plaza; z logged every 0.25 s: never under the floor - 0.1, no climb /
            ragdoll / fall, every leg arrives.
  sit       every seat: TaskStartScenarioAtPosition(PROP_HUMAN_SEAT_BENCH) at its sit point; after 6 s the ped must be using the
            scenario and stand within 0.25 m of the point (xy) and 0.15 m (z); prints each seat's error.
Run: py -3 jc3_probe.py interior doors walk sit   -> work/p3/out/probe_<name>.json; exit 1 on any FAIL."""
import json, math, sys, time, re, subprocess
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc3_plan as JP, jc_frame as F
GB = r'C:\Program Files\Git\bin\bash.exe'
L = json.load(open(P3 / 'out/jc3_layout.json'))
def lua(code, timeout=60):
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" %d' % timeout, code], capture_output=True, text=True, timeout=timeout + 30)
    m = re.search(r'"result":"(.*?)"(,|\})', r.stdout, re.S)
    if not m: raise SystemExit('PROBE: no answer from the rig - nothing was tested: ' + (r.stdout + r.stderr)[-400:])
    return m.group(1)
def W(u, v): return F.W(u, v)
def feed():
    """Qbox drains health to 'downed' when hunger / thirst reach 0 (a walker collapsed mid-route on the open floor, rig 2026-10-29)."""
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh srv "$0"', "local P = exports.qbx_core:GetPlayer(1) P.Functions.SetMetaData('hunger', 100) P.Functions.SetMetaData('thirst', 100) return 'fed'"], capture_output=True, text=True, timeout=60)
    if 'fed' not in r.stdout: raise SystemExit('PROBE: could not feed the test player - nothing was tested: ' + r.stdout[-300:])
def revive():
    feed()
    return lua("local p=PlayerPedId() if IsEntityDead(p) or GetEntityHealth(p) < 150 then local c=GetEntityCoords(p) NetworkResurrectLocalPlayer(c.x,c.y,c.z+0.5,GetEntityHeading(p),true,false) Wait(500) p=PlayerPedId() TriggerEvent('qbx_medical:client:playerRevived') end SetEntityHealth(p,200) ClearPedTasksImmediately(p) return tostring(GetEntityHealth(p))", 30)
def stand(u, v, z, h=0.0):
    x, y = W(u, v)
    return lua('local p=PlayerPedId() SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) ClearPedTasksImmediately(p) SetEntityCoords(p,%.3f,%.3f,%.3f) SetEntityHeading(p,%.1f) SetFocusPosAndVel(%.3f,%.3f,%.3f,0.0,0.0,0.0) return "ok"' % (x, y, z + 0.9, (h + F.HDEG) % 360, x, y, z))
def walk_to(u, v, tmax=25.0, speed=1.0):
    """walk the ped to (u, v) (TaskGoStraightToCoord); log z / states every 0.25 s; returns (arrived, log)."""
    x, y = W(u, v)
    code = ('local p=PlayerPedId() TaskGoStraightToCoord(p,%.3f,%.3f,%.3f,%.2f,%d,0.0,0.0) local o={} local t0=GetGameTimer() local ok=false '
            'while GetGameTimer()-t0 < %d do Wait(250) local c=GetEntityCoords(p) o[#o+1]=string.format("%%.2f:%%.2f:%%.3f:%%d%%d%%d",c.x,c.y,c.z,IsPedRagdoll(p) and 1 or 0,IsPedClimbing(p) and 1 or 0,IsPedFalling(p) and 1 or 0) '
            'if #(vector2(c.x,c.y)-vector2(%.3f,%.3f)) < 0.6 then ok=true break end end return (ok and "OK" or "NO")..";"..table.concat(o,";")') % (x, y, JP.G, speed, int(tmax * 1000), int(tmax * 1000), x, y)
    r = lua(code, int(tmax) + 30).split(';'); log = [tuple(float(a) if i < 3 else a for i, a in enumerate(e.split(':'))) for e in r[1:] if e]
    return r[0] == 'OK', log
def interior():
    """control first: the ped stood on the plaza outside the doors must be in NO interior (GetInteriorFromEntity 0); then stood in the
    galleria it must be in the jc_courts interior, ready, in a room whose timecycle is ours."""
    stand(50.0, 4.0, JP.G); time.sleep(3)
    o = int(lua('local p=PlayerPedId() Wait(1500) return tostring(GetInteriorFromEntity(p))'))
    cu, cv = (JP.UA0 + JP.UA1) / 2, (JP.VA0 + JP.VA1) / 2; x, y = W(cu, cv)
    stand(cu, cv, JP.G); time.sleep(4)
    r = lua('local i=GetInteriorAtCoords(%.2f,%.2f,%.2f) local p=PlayerPedId() Wait(1500) local pi=GetInteriorFromEntity(p) local rk=GetRoomKeyFromEntity(p) '
            'local tc=0 if pi~=0 then local rid=GetInteriorRoomIndexByHash(pi,rk) tc=GetInteriorRoomTimecycle(pi,rid) end '
            'return string.format("%%d:%%s:%%d:%%d:%%d:%%d",i,tostring(IsInteriorReady(i)),pi,rk,tc,GetHashKey("%s"))' % (x, y, JP.G + 1.0, JP.TCYC['galleria'])).split(':')
    i, ready, pi, rk, tc, want = int(r[0]), r[1], int(r[2]), int(r[3]), int(r[4]), int(r[5])
    proven = o == 0
    ok = proven and i != 0 and ready in ('true', '1') and pi == i and rk != 0 and tc == want
    return {'interior': i, 'ready': ready, 'plaza_ped_interior': o, 'ped_interior': pi, 'room_key': rk, 'timecycle': tc, 'want_tc': want, 'proven': proven}, ok
def doors():
    out = []; allok = True
    for d in L['doors']:
        u, v, z = d['pos']; sg = 1 if d['model'] == JP.DOOR_L else -1; mid = v + sg * JP.LEAF_W / 2; x, y = W(u, v)
        found = lua('local o=GetClosestObjectOfType(%.3f,%.3f,%.3f,1.5,GetHashKey("%s"),false,false,false) return tostring(o~=0 and DoesEntityExist(o))' % (x, y, z, d['model']))
        res = {'door': d['name'], 'object': found}
        for name, (a, b) in (('in', (u + 2.0, u - 1.5)), ('out', (u - 1.5, u + 2.0))):
            revive(); stand(a, mid, JP.G, 90.0 if b < a else 270.0); time.sleep(1.0)
            ok, log = walk_to(b, mid, 15.0)
            far = max((F.L(e[0], e[1])[0] - u) * (1 if b > a else -1) for e in log) if log else -9
            res[name] = {'arrived': ok, 'past_line': round(far, 2)}; allok &= ok and far > 1.0
        allok &= found in ('true', '1'); out.append(res)
    return out, allok
ROUTE = [(44.0, 2.14), (36.0, 2.14), (31.0, 0.35), (27.5, 0.35), (20.0, 6.0), (4.0, 10.0), (4.0, 26.0), (6.0, 43.0), (10.5, 22.0), (10.5, 13.0),
         (20.0, 10.0), (26.0, 7.4), (31.5, 7.4), (36.0, 7.96), (44.0, 7.96)]      # aisles clear of the islands, planters and benches
def walk():
    revive(); u0, v0 = ROUTE[0]; stand(u0, v0, JP.G, 270.0); time.sleep(2); legs = []; ok_all = True
    for (u, v) in ROUTE[1:]:
        ok, log = walk_to(u, v, 30.0)
        zmin = min(e[2] for e in log) if log else 0; states = sum(1 for e in log if e[3] != '000')
        good = ok and zmin > JP.G - 0.1 and states == 0
        legs.append({'to': [u, v], 'arrived': ok, 'zmin': round(zmin, 3), 'bad_states': states}); ok_all &= good
    return legs, ok_all
def sit(rooms=None):
    """every seat (or those of `rooms`): the ped is stood 1 m off and told to take the seat's scenario at its sit point (snapped); after
    6 s it must be in the scenario at the point. The visual check (on the seat, not in it) is the clone photos."""
    out = []; ok_all = True
    for s in L['seats']:
        u, v, z, h = s[:4]; room = s[4] if len(s) > 4 else 'galleria'; sc = s[5] if len(s) > 5 else 'PROP_HUMAN_SEAT_BENCH'
        if rooms and room not in rooms: continue
        x, y = W(u, v); fz = z - 0.6; revive(); stand(u, v, fz); time.sleep(0.5)
        r = lua('local p=PlayerPedId() TaskStartScenarioAtPosition(p,"%s",%.3f,%.3f,%.3f,%.1f,0,true,true) Wait(6000) local c=GetEntityCoords(p) '
                'local u=IsPedUsingScenario(p,"%s") or IsPedActiveInScenario(p) return string.format("%%s:%%.3f:%%.3f:%%.3f",tostring(u),c.x,c.y,c.z)' % (sc, x, y, z, (h + F.HDEG) % 360, sc), 40).split(':')
        using = r[0] in ('true', '1'); dx = math.hypot(float(r[1]) - x, float(r[2]) - y); dz = float(r[3]) - z
        good = using and dx < 0.25 and abs(dz) < 0.15; ok_all &= good
        out.append({'seat': [round(u, 2), round(v, 2), round(z, 2)], 'room': room, 'scenario': sc, 'using': using, 'dxy': round(dx, 3), 'dz_root_minus_seat': round(dz, 3), 'ok': good})
        lua('ClearPedTasksImmediately(PlayerPedId()) return "c"')
    return out, ok_all
def sit2(): return sit(rooms=set(L['zones']) - {'galleria'})
def sit_sec(): return sit(rooms={'secA', 'secB'})
def rooms():
    """the ped stood in each room (the middle of its first region rect, on its floor) must report the jc_courts interior and the room's
    own key (GetRoomKeyFromEntity = the hash of the room's name). Control: the plaza is no interior."""
    out = []; ok_all = True
    stand(50.0, 4.0, JP.G); time.sleep(2)
    o = int(lua('Wait(1200) return tostring(GetInteriorFromEntity(PlayerPedId()))'))
    for r in L['rooms']:
        z = L['zones'][r['key']][0]; u, v = (z[0] + z[1]) / 2, (z[2] + z[3]) / 2
        if r['key'] == 'stair': u, v = 41.1, 33.9
        revive(); stand(u, v, z[4]); time.sleep(2.5)
        res = lua('local p=PlayerPedId() Wait(1000) return string.format("%%d:%%d:%%d",GetInteriorFromEntity(p),GetRoomKeyFromEntity(p),GetHashKey("%s"))' % r['name']).split(':')
        good = int(res[0]) != 0 and int(res[1]) == int(res[2]); ok_all &= good
        out.append({'room': r['key'], 'interior': int(res[0]), 'room_key': int(res[1]), 'want': int(res[2]), 'ok': good})
    return {'plaza_control': o, 'rooms': out}, ok_all and o == 0
def doors2():
    """every area-2 door (and the galleria -> lobby pair): through the middle of each LEAF both ways, 1.5 m either side."""
    out = []; ok_all = True
    for d in L['doors']:
        if d['name'].startswith(('entry', 'exit')) or 'rollup' in d['name']: continue      # (the garage roll-ups are driven through: gdrive)
        u, v, z = d['pos']; t = math.radians(d['heading']); sgn = 1.0 if d['model'] in ('v_ilev_ph_door01',) else -1.0
        lu, lv = sgn * math.cos(t), sgn * math.sin(t); mu, mv = u + lu * 0.65, v + lv * 0.65; nu, nv = -lv, lu
        fz = z - 1.15; res = {'door': d['name']}
        D = 1.0 if d['model'] == 'v_ilev_ph_cellgate' else 1.5      # the secure corridor west of the cells is 1.3 m: start 1.0 m out, not in its wall
        for name, k in (('a', 1), ('b', -1)):
            revive(); stand(mu + nu * D * k, mv + nv * D * k, fz); time.sleep(0.8)
            ok, log = walk_to(mu - nu * D * k, mv - nv * D * k, 12.0)
            far = max(((F.L(e[0], e[1])[0] - mu) * nu + (F.L(e[0], e[1])[1] - mv) * nv) * -k for e in log) if log else -9
            res[name] = {'arrived': ok, 'past_line': round(far, 2)}; ok_all &= ok and far > D - 0.65    # arrival radius 0.6: through by D - 0.6
        found = lua('local o=GetClosestObjectOfType(%.3f,%.3f,%.3f,1.6,GetHashKey("%s"),false,false,false) return tostring(o~=0)' % (*W(u, v), z, d['model']))
        res['object'] = found; ok_all &= found in ('true', '1'); out.append(res)
    return out, ok_all
def models():
    """every room drawable the layout exports is registered in the game (IsModelInCdimage) - control: a planted name that is not
    streamed must read false (2026-10-29: case-hashed names left every L3 / L5 room unregistered and undrawn; no offline gate saw it)."""
    names = sorted(L['drawables']) + ['jc_courts_planted_missing']
    revive(); stand(5.0, 20.0, JP.G); time.sleep(4)                     # the MLO's ytyp is loaded only near the lot: stand in the galleria
    r = lua('local o={} for _,n in ipairs({"%s"}) do o[#o+1]=tostring(IsModelInCdimage(GetHashKey(n))) end return table.concat(o,",")' % '","'.join(names), 30).split(',')
    got = {n: v in ('true', '1') for n, v in zip(names, r)}
    return got, len(r) == len(names) and not got['jc_courts_planted_missing'] and all(v for n, v in got.items() if n != 'jc_courts_planted_missing')
def lifts():
    """on screen, like a player: stood 2.2 m out from each cab's landing, the ped walks in through the landing door, [E] (a real key
    press into the game window) opens the floor list, the floor row is clicked in ox_lib's menu, and the ped must arrive in the same cab
    on that floor. Rides: courts L1->L3->L5->L1 (both cabs), secure L3->L5->L3. Control: [E] stood outside the cab must open nothing."""
    import json as J
    banks = J.load(open(P3 / 'out/lifts.json')); out = []; ok_all = True
    def key_e(): subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', r'C:\C9Test\key.ps1', '-Vk', '69', '-Scan', '18'], capture_output=True, timeout=30)
    def menu_open(): return lua('return tostring(lib and lib.getOpenContextMenu and lib.getOpenContextMenu() or exports.ox_lib:getOpenContextMenu())', 10)
    for b in banks:
        fl = b['floors']; h = math.radians(b['heading']); fx, fy = -math.sin(h), math.cos(h)        # the cab's front (the rider faces out)
        order = [0, 1, 2, 0] if len(fl) == 3 else [0, 1, 0]
        for ci in range(len(fl[0]['cabs'])):
            for a, t in zip(order, order[1:]):
                cx, cy, cz = fl[a]['cabs'][ci]; ox, oy = cx + fx * 2.2, cy + fy * 2.2
                u, v = F.L(ox, oy); revive(); stand(u, v, cz, (b['heading'] + 180.0) % 360); time.sleep(1.0)
                ctl = None
                if a == order[0] and ci == 0:
                    key_e(); time.sleep(1.0); ctl = menu_open()
                cu, cv = F.L(cx, cy); arrived, log = walk_to(cu, cv, 10.0)
                time.sleep(0.8); key_e(); time.sleep(1.2); opened = menu_open()
                r = subprocess.run([GB, '-c', "bash /c/C9Test/oxclick.sh '^%s$'" % fl[t]['name']], capture_output=True, text=True, timeout=60).stdout.strip()
                time.sleep(4.5)
                e = lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f:%.2f:%.2f",c.x,c.y,c.z)', 10).split(':')
                tx, ty, tz = fl[t]['cabs'][ci]; d = math.hypot(float(e[0]) - tx, float(e[1]) - ty); dz = float(e[2]) - (tz + 1.0)
                good = arrived and opened == 'jc_lift' and 'clicked' in r and d < 1.1 and abs(dz) < 0.4 and (ctl in (None, 'nil'))
                ok_all &= good
                out.append({'bank': b['bank'], 'cab': ci, 'from': fl[a]['name'], 'to': fl[t]['name'], 'walked_in': arrived, 'menu': opened,
                            'click': r[-40:], 'xy_off': round(d, 2), 'dz': round(dz, 2), 'outside_control': ctl, 'ok': good})
                lua("exports.ox_lib:hideContext() return \"x\"", 10)
    return out, ok_all
WALK2 = {   # courtroom floor L3 (lot u, v): each route walked leg by leg; every leg must arrive with no ragdoll / climb / fall state
    'public':   [(16.0, 19.4), (29.4, 19.4), (29.4, 21.9), (30.0, 24.0), (30.0, 29.3), (25.65, 29.3), (25.65, 31.2), (25.65, 33.0),
                 (25.65, 29.3), (30.0, 29.3), (30.0, 24.0), (29.4, 21.9), (29.4, 19.4)],
    'secure':   [(33.1, 26.4), (31.9, 26.4), (31.9, 36.25), (30.2, 36.25), (31.9, 36.25), (31.9, 26.4), (33.1, 26.4)],
    'restricted': [(16.5, 25.0), (16.5, 42.6), (20.15, 42.6), (20.15, 40.4), (20.15, 42.6), (35.0, 42.6), (16.5, 42.6), (16.5, 25.0)],
}
def walk2():
    import jc3_tower as JT
    out = {}; ok_all = True
    for name, pts in WALK2.items():
        revive(); stand(*pts[0], JT.F3); time.sleep(1.5); legs = []
        for u, v in pts[1:]:
            ok, log = walk_to(u, v, 15.0)
            bad = sum(1 for e in log if e[3] != '000'); zs = [e[2] for e in log] or [0]
            good = ok and bad == 0 and max(zs) - min(zs) < 0.6; ok_all &= good
            legs.append({'to': [u, v], 'arrived': ok, 'bad_states': bad, 'z_range': round(max(zs) - min(zs), 2), 'ok': good})
        out[name] = legs
    return out, ok_all
GDRIVE_STEP = 'local v=_G.__gv local t0=GetGameTimer() local hits=0 local last=-1000 local hat="" local reached=false\nwhile GetGameTimer()-t0<20000 do local c=GetEntityCoords(v) local dx,dy=%.3f-c.x,%.3f-c.y local d=math.sqrt(dx*dx+dy*dy)\n if d<1.2 then reached=true break end\n local want=(math.deg(math.atan(dy,dx))-90.0)%%360.0 local h=GetEntityHeading(v) if %.2f<0 then want=(want+180.0)%%360.0 end\n local dh=((want-h+540.0)%%360.0)-180.0 local cap=2.2 if dh>cap then dh=cap elseif dh<-cap then dh=-cap end\n SetEntityHeading(v,h+dh) SetVehicleForwardSpeed(v,%.2f)\n if HasEntityCollidedWithAnything(v) then local n=GetCollisionNormalOfLastHitForEntity(v) local now=GetGameTimer() if math.abs(n.z)<0.6 and now-last>600 then last=now hits=hits+1 if hat=="" then hat=string.format("%%.1f,%%.1f,%%.2f",c.x,c.y,c.z) end end end\n Wait(30) end\nSetVehicleForwardSpeed(v,0.0) local c=GetEntityCoords(v)\nreturn string.format("%%s|%%d|%%s|%%.2f,%%.2f,%%.2f",tostring(reached),hits,hat,c.x,c.y,c.z)'
def _garage_route():
    """the drive test's waypoints (lot u, v, speed m/s; negative = reverse): in through the IN door, down the ramp, the IN turn, up the
    west aisle, the north aisle, the east aisle, the return aisle, into a bay of row 4 (nose in), out backwards, the U-turn, up the OUT
    ramp, out through the OUT door. The turns follow the plan's arcs (jc3_pgarage) as polylines."""
    import jc3_pgarage as G
    pts = [(60.0, G.IN_C, 6.0), (45.5, G.IN_C, 4.0), (G.U_FOOT + 1.0, G.IN_C, 4.0)]
    cx, cy = G.IN_X + G.UT_R, G.IN_C + G.UT_R
    pts += [(cx - G.UT_R * math.sin(t), cy - G.UT_R * math.cos(t), 3.0) for t in [i * math.pi / 2 / 6 for i in range(1, 7)]]
    pts += [(G.IN_X, -16.0, 4.0), (G.IN_X + 3.0, -11.2, 3.0), (36.0, -11.2, 4.0), (41.4, -15.0, 3.0), (41.4, G.RET_V + 1.0, 4.0), (32.5, G.RET_V, 3.0)]
    bay = [b for b in G.bays() if b[3] == 3][0]                              # row 4: south of the return aisle, nose-in heading south
    pts += [(bay[0], G.RET_V - 2.0, 2.0), (bay[0], bay[1] - 1.0, 1.5), (bay[0], G.RET_V - 1.0, -1.5)]   # in, then back out
    pts += [(G.UT_C[0] + 1.0, G.RET_V, 3.0)]
    pts += [(G.UT_C[0] - G.UT_R * math.sin(t), G.UT_C[1] + G.UT_R * math.cos(t), 3.0) for t in [i * math.pi / 8 for i in range(1, 9)]]
    pts += [(G.U_FOOT + 2.0, G.OUT_C, 4.0), (44.0, G.OUT_C, 4.0), (47.0, G.OUT_C, 4.0), (60.0, G.OUT_C, 6.0)]
    return pts
def gdrive(model='police3'):
    """the garage drive test, script-steered (no path nodes underground): the vehicle is pointed at each waypoint in turn (a capped
    turn rate, as a steering lock) and driven at the waypoint's speed; every collision with anything is counted and its place logged.
    Pass: every waypoint reached, no collision, out on the plaza at the end."""
    import jc3_pgarage as G
    pts = _garage_route(); x0, y0 = W(pts[0][0], pts[0][1])
    revive(); stand(64.0, G.IN_C + 4.0, 28.3); time.sleep(2)
    lua('local m=GetHashKey("%s") RequestModel(m) local t=GetGameTimer() while not HasModelLoaded(m) and GetGameTimer()-t<10000 do Wait(50) end '
        'local _,gz=GetGroundZFor_3dCoord(%.2f,%.2f,40.0,false) local v=CreateVehicle(m,%.2f,%.2f,gz+0.3,%.1f,false,false) SetVehicleOnGroundProperly(v) '
        'SetEntityAsMissionEntity(v,true,true) _G.__gv=v local p=PlayerPedId() SetPedIntoVehicle(p,v,-1) return "spawned"' % (model, x0, y0, x0, y0, (F.HDEG + 90.0) % 360), 40)
    out = []; ok_all = True
    for u, v, spd in pts[1:]:
        x, y = W(u, v)
        r = lua(GDRIVE_STEP % (x, y, spd, spd), 40).split('|')
        reached = r[0] in ('true', '1'); hits = int(r[1]); good = reached and hits == 0; ok_all &= good
        out.append({'to': [round(u, 2), round(v, 2)], 'reached': reached, 'collisions': hits, 'first_hit_at': r[2], 'at': r[3], 'ok': good})
        if not reached: break
    lua('local p=PlayerPedId() TaskLeaveVehicle(p,_G.__gv,16) Wait(1500) if _G.__gv then DeleteEntity(_G.__gv) end return "gone"', 20)
    return out, ok_all
def gdrive_van(): return gdrive('policet')
WALK3 = {   # area 3 (lot u, v, floor z): leg by leg, every leg must arrive with no ragdoll / climb / fall state
    'public':  [(20.0, -5.6, 28.8), (20.0, -9.5, 28.8), (30.0, -10.5, 28.8), (36.0, -20.0, 28.8), (36.0, -33.0, 28.8), (36.0, -20.0, 28.8), (30.0, -10.5, 28.8), (20.0, -9.5, 28.8), (20.0, -5.6, 28.8)],
    'staff':   [(23.0, -11.5, 28.8), (23.0, -15.0, 28.8), (23.0, -34.9, 28.8), (21.0, -34.9, 28.8)],
    'garage':  [(17.0, -37.0, 25.6), (19.3, -36.6, 25.6), (13.0, -36.6, 25.6), (13.0, -20.0, 25.6), (25.0, -12.6, 25.6), (30.0, -30.0, 25.6), (19.3, -36.6, 25.6)],
}
def walk3():
    out = {}; ok_all = True
    for name, pts in WALK3.items():
        revive(); stand(pts[0][0], pts[0][1], pts[0][2]); time.sleep(1.5); legs = []
        for u, v, z in pts[1:]:
            ok, log = walk_to(u, v, 20.0)
            bad = sum(1 for e in log if e[3] != '000'); good = ok and bad == 0; ok_all &= good
            legs.append({'to': [u, v], 'arrived': ok, 'bad_states': bad, 'z_end': round(log[-1][2], 2) if log else None, 'ok': good})
        out[name] = legs
    return out, ok_all
def gdrive_control():
    """proves the drive probe before it is trusted: a straight run along the IN driveway's lane (nothing built in it from u 64 to the door:
    checked offline against every drawn + collision triangle) must count no impact and arrive; a run into the police east face's solid
    stone between the OUT door and the colonnade's end (v -46.1, full-height stone at u 44.65; the target lies inside the building) must
    count one or more and NOT arrive. (2026-10-30 rig: the old plaza line crossed a site planter and the old wall line ran into the open
    arcade, so the control read inverted.)"""
    import jc3_pgarage as G
    res = {}
    for name, (u0, v0, u1, v1) in (('open lane', (62.0, G.IN_C, 50.0, G.IN_C)), ('planted wall', (56.0, -46.1, 40.0, -46.1))):
        x0, y0 = W(u0, v0); revive(); stand(u0 + 3.0, v0 + 3.0, 28.8); time.sleep(1.5)
        lua('local m=GetHashKey("police3") RequestModel(m) local t=GetGameTimer() while not HasModelLoaded(m) and GetGameTimer()-t<10000 do Wait(50) end '
            'local _,gz=GetGroundZFor_3dCoord(%.2f,%.2f,40.0,false) local v=CreateVehicle(m,%.2f,%.2f,gz+0.3,%.1f,false,false) SetVehicleOnGroundProperly(v) '
            'SetEntityAsMissionEntity(v,true,true) _G.__gv=v local p=PlayerPedId() SetPedIntoVehicle(p,v,-1) return "spawned"' % (x0, y0, x0, y0, (F.HDEG + 90.0) % 360), 40)
        x, y = W(u1, v1); r = lua(GDRIVE_STEP % (x, y, 4.0, 4.0), 40).split('|')
        res[name] = {'reached': r[0] in ('true', '1'), 'collisions': int(r[1])}
        lua('local p=PlayerPedId() TaskLeaveVehicle(p,_G.__gv,16) Wait(1500) if _G.__gv then DeleteEntity(_G.__gv) end return "gone"', 20)
    return res, (res['open lane']['reached'] and res['open lane']['collisions'] == 0 and not res['planted wall']['reached']
                 and res['planted wall']['collisions'] > 0)
STAIR_ROUTE = []
def stair():
    """L1 lobby -> the stair door -> both flights of each storey -> L3 landing -> out into pubA (and on to L5)."""
    import jc3_tower as JT
    S = JT.SC; ls, ln = sum(JT.LANE_S) / 2, sum(JT.LANE_N) / 2
    revive(); stand(44.0, 33.95, JT.F1, 90.0); time.sleep(2); legs = []; ok_all = True
    pts = [(41.6, 33.95), (40.4, ls)]
    for k in range(4): pts += [(36.6, ls), (36.2, ln), (40.4, ln), (40.6, ls)] if k < 3 else [(36.6, ls), (36.2, ln), (40.4, ln)]
    pts += [(41.6, 33.95), (44.0, 33.95)]
    for u, v in pts:
        ok, log = walk_to(u, v, 20.0)
        zmax = max(e[2] for e in log) if log else 0; states = sum(1 for e in log if e[3] != '000')
        legs.append({'to': [u, v], 'arrived': ok, 'z_end': round(log[-1][2], 2) if log else None, 'bad_states': states}); ok_all &= ok and states == 0
    zend = legs[-1]['z_end'] or 0
    return legs, ok_all and abs(zend - (JT.F5 + 1.0)) < 0.3
if __name__ == '__main__':
    fails = 0
    try:
        for name in sys.argv[1:]:
            res, ok = globals()[name]()
            json.dump(res, open(P3 / f'out/probe_{name}.json', 'w'), indent=1)
            print(f'PROBE_{name.upper()}_{"PASS" if ok else "FAIL"}', json.dumps(res)[:600], flush=True); fails += not ok
    finally:
        revive(); stand(50.0, 4.0, JP.G); subprocess.run([GB, '-c', 'bash /c/C9Test/tc_release.sh'], capture_output=True, text=True, timeout=60)
    sys.exit(1 if fails else 0)
