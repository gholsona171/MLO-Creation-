"""Area 3 garage drive probes (rig: main runs them through handoff_area3.sh; agents never touch the rig).
One driving method for the self-test, the control and the drives: jc-jail's proven one (work/jail/jj_probe.py DRV / PURGE / SLICE_MS,
imported, not copied): TaskVehicleTempAction gas (23) / reverse (22) / brake (1) in 300 ms slices, speed capped with SetEntityMaxSpeed,
steering = the heading turned toward the next waypoint by at most 0.9 deg a frame (the jail's heading hold, generalised to a route with
turns). The car is spawned on a purged street, keyed by the server, the engine started THROUGH c9_vehiclekeys' ToggleEngine (its
disableAutoStart guard switches a raw SetVehicleEngineOn off every frame) - the jail's _spawn, with the garage's spot and heading.
The police roll-ups are plain map doors that do NOT open for a car by themselves (rig 2026-10-30, as Jail I's sally port): the buyer's
door-lock system opens them (Antonio: "client add locks"), so the probe opens them through the DOOR SYSTEM (registered, open ratio 1,
held open) for the run and shuts and releases them after. Each door's opening is read from the door object found anew at every read,
against its placement (position offset + pitch / roll).
  gdrive_selftest  both read-backs read shut / open / shut; a car on the IN lane moves >= 2 m on 8 gas slices; it is deleted
  gdrive_control   the open IN lane (u 62 -> 50, nothing built in it: jc3_corridor.py) arrives with 0 impacts; a run into the solid
                   stone at v -46.1 (target inside the building) does NOT arrive and counts impacts
  gdrive / _van    police3 / policet: IN door -> ramp -> loop -> nose into a row-4 bay -> back out -> U-turn -> OUT ramp -> OUT door"""
import json, math, sys, subprocess
from pathlib import Path
P3 = Path(__file__).resolve().parent; WK = P3.parent; sys.path[:0] = [str(P3), str(WK), str(WK / 'jail')]
import jc_frame as F
L = json.load(open(P3 / 'out/jc3_layout.json'))
MODEL = 'prop_gar_door_05'
def _pr():
    import jc3_probe as PR                                   # lazily: jc3_probe imports this module
    return PR
def _jj():
    import jj_probe as JJ                                    # jc-jail's driving method (DRV, PURGE, SLICE_MS)
    return JJ
def doors_lua():
    """the two roll-ups' door-system and read-back helpers (keys IN / OUT)."""
    R = {d['name']: d for d in L['rollups']}
    pts = {}
    for k, n in (('IN', 'pramp_in_rollup'), ('OUT', 'pramp_out_rollup')):
        u, v, z = R[n]['pos']; x, y = F.W(u, v); pts[k] = (x, y, z)
    return ('local RM=GetHashKey("%s") local DOORS={IN={h=GetHashKey("jcp_rollup_in"),p=vector3(%.3f,%.3f,%.3f)},OUT={h=GetHashKey("jcp_rollup_out"),p=vector3(%.3f,%.3f,%.3f)}} '
            'local function dopen(k) local D=DOORS[k] local o=GetClosestObjectOfType(D.p.x,D.p.y,D.p.z,4.0,RM,false,false,false) if o==0 then return -1.0 end '
            'local r_=GetEntityRotation(o,2) return #(GetEntityCoords(o)-D.p)+(math.abs(r_.x)+math.abs(r_.y))/30.0 end '
            'local function dsys(k,open) local D=DOORS[k] if not IsDoorRegisteredWithSystem(D.h) then AddDoorToSystem(D.h,RM,D.p.x,D.p.y,D.p.z,false,false,false) end '
            'if open then DoorSystemSetDoorState(D.h,0,false,true) DoorSystemSetOpenRatio(D.h,1.0,false,true) DoorSystemSetHoldOpen(D.h,true) '
            'else DoorSystemSetHoldOpen(D.h,false) DoorSystemSetOpenRatio(D.h,0.0,false,true) DoorSystemSetDoorState(D.h,1,false,true) Wait(5000) '
            'DoorSystemSetDoorState(D.h,0,false,true) RemoveDoorFromSystem(D.h) end end ') % (MODEL, *pts['IN'], *pts['OUT'])
def _lanes():
    import jc3_pgarage as G
    return G.IN_C, G.OUT_C
def heading_minus_u(): return (90.0 + F.HDEG) % 360.0            # a car facing -u (into the garage from the street)
def _gspawn(m, su, sv, h_world, z=28.4):
    """jc-jail's _spawn (jj_probe.py), at the garage: ped ready, purge 30 m, spawn networked + owned, the server's key, the driver's seat,
    CanDrive, ToggleEngine, engine running 1.5 s later, fuel > 0. Any step failing raises 'nothing was tested'."""
    PR, JJ = _pr(), _jj(); sx, sy = F.W(su, sv)
    PR.revive(); PR.stand(su + 3.0, sv + 4.0, z); __import__('time').sleep(1)
    sp = PR.lua((JJ.PURGE + 'local p=PlayerPedId() local t=GetGameTimer() if IsPedInAnyVehicle(p,false) then TaskLeaveVehicle(p,GetVehiclePedIsIn(p,false),16) end '
                 'while GetGameTimer()-t<5000 and (IsPedInAnyVehicle(p,true) or IsPedRagdoll(p) or IsPedFalling(p) or IsPedGettingIntoAVehicle(p)) do Wait(100) end '
                 'local rdy=not IsPedInAnyVehicle(p,true) and not IsPedRagdoll(p) and not IsPedFalling(p) '
                 'local h=GetHashKey("%s") RequestModel(h) t=GetGameTimer() while not HasModelLoaded(h) and GetGameTimer()-t<8000 do Wait(50) end '
                 'local n,left=purge(%.3f,%.3f,%.3f,30.0) '
                 'local v=CreateVehicle(h,%.3f,%.3f,%.3f,%.1f,true,false) SetEntityAsMissionEntity(v,true,true) SetVehicleOnGroundProperly(v) SetEntityHeading(v,%.1f) '
                 'FreezeEntityPosition(v,false) SetVehicleUndriveable(v,false) _G.__gv=v t=GetGameTimer() '
                 'while GetGameTimer()-t<4000 and not (NetworkGetEntityIsNetworked(v) and NetworkHasControlOfEntity(v)) do NetworkRequestControlOfEntity(v) Wait(50) end '
                 'local net=NetworkGetEntityIsNetworked(v) and NetworkHasControlOfEntity(v) Wait(300) local c=GetEntityCoords(v) '
                 'return GetVehicleNumberPlateText(v)..";"..string.format("%%.2f;%%.2f;%%.1f;%%d;%%d;",c.x,c.y,GetEntityHeading(v),n,left)..tostring(rdy)..";"..tostring(net)')
                % (m, sx, sy, z, sx, sy, z + 0.5, h_world, h_world), 40).split(';')
    plate = sp[0].strip(); cu, cv = F.L(float(sp[1]), float(sp[2])); hd = abs(((float(sp[3]) - h_world) + 540.0) % 360.0 - 180.0); purged, left = int(sp[4]), int(sp[5])
    rdy, net = sp[6].strip() in ('true', '1'), sp[7].strip() in ('true', '1')
    def gone(why):
        PR.lua('local v=_G.__gv if v and DoesEntityExist(v) then SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) end return "x"')
        raise SystemExit(f'PROBE: {why} - nothing was tested')
    if left > 0: gone(f'{left} vehicle(s) still near the spawn after the purge')
    if not rdy: gone('the player was still in / getting out of a vehicle, ragdolled or falling 5 s after being stood up')
    if not net: gone(f'{m} was not networked and owned by the test client within 4 s')
    if abs(cv - sv) > 0.6 or abs(cu - su) > 0.6 or hd > 3.0: gone(f'{m} did not spawn on the line ({cu:.2f}, {cv:.2f}, heading off {hd:.1f})')
    r = subprocess.run([PR.GB, '-c', 'cd /c/C9Test && ./t.sh srv "$0" 20', "return tostring(exports.c9_vehiclekeys:GiveKeysByPlate(1,'%s',true))" % plate], capture_output=True, text=True, timeout=60)
    if 'true' not in r.stdout: gone('the server gave no key: ' + r.stdout[-200:])
    w = PR.lua('local p=PlayerPedId() local v=_G.__gv local tries,how=0,"" '
               'while GetPedInVehicleSeat(v,-1)~=p and tries<6 do tries=tries+1 ClearPedTasksImmediately(p) '
               'if tries<=3 then TaskWarpPedIntoVehicle(p,v,-1) how="warp" else SetPedIntoVehicle(p,v,-1) how="set" end '
               'local t=GetGameTimer() while GetGameTimer()-t<1000 and GetPedInVehicleSeat(v,-1)~=p do Wait(50) end end '
               'local seat=GetPedInVehicleSeat(v,-1)==p '
               'local can=false if seat then local t=GetGameTimer() while GetGameTimer()-t<6000 and not exports.c9_vehiclekeys:CanDrive(v) do Wait(100) end Wait(500) '
               'can=exports.c9_vehiclekeys:CanDrive(v) if can and not GetIsVehicleEngineRunning(v) then exports.c9_vehiclekeys:ToggleEngine() end Wait(1500) end '
               'local tf=GetGameTimer() while seat and Entity(v).state.fuel==nil and GetGameTimer()-tf<3000 do Wait(100) end '
               'return tostring(seat)..";"..tostring(can)..";"..tostring(GetIsVehicleEngineRunning(v))..";"..string.format("%.1f",GetVehicleFuelLevel(v))..";"..tries..";"..how', 40).split(';')
    seat, can, run = (x in ('true', '1') for x in w[:3]); fuel = float(w[3])
    if not seat: gone(f"the player is not in {m}'s driver seat after {w[4]} tries ({w[5]})")
    if not can: gone('the keys script says the player cannot drive it (CanDrive false)')
    if not run: gone('the engine is not running 1.5 s after the keys script started it')
    if fuel <= 0: gone(f'fuel {fuel:.1f}')
    return purged, {'engine': run, 'fuel': fuel, 'seat_tries': f'{w[4]} {w[5]}'}
def _leg(u, v, spd, brake_first=False, tmax=25000):
    """drive the spawned car (_G.__gv) to lot (u, v): gas (spd > 0) or reverse (spd < 0) slices up to |spd| m/s, the heading turned toward
    the point (reverse: the tail toward it) by at most 0.9 deg a frame; arrival within 1.2 m. Counts impacts (not the ground's normal,
    0.6 s apart), logs the first three (lot u / v + normal), and the most each roll-up was open while the car was within 6 m of it."""
    PR, JJ = _pr(), _jj(); tx, ty = F.W(u, v)
    code = (doors_lua() + JJ.DRV + 'local v=_G.__gv local T=vector2(%.3f,%.3f) local want=%.2f local rev=%s local hits,last,imp,fr=0,-1000,{},0 local dmax={IN=0.0,OUT=0.0} '
            'local O=vector2(%.3f,%.3f) local cH,sH=math.cos(math.rad(%.4f)),math.sin(math.rad(%.4f)) '
            'local function tick() local c=GetEntityCoords(v) fr=fr+1 '
            'local dx,dy=T.x-c.x,T.y-c.y local w=(math.deg(math.atan(dy,dx))-90.0)%%360.0 if rev then w=(w+180.0)%%360.0 end '
            'local h=GetEntityHeading(v) local dh=((w-h+540.0)%%360.0)-180.0 if math.abs(dh)>0.3 then if dh>0.9 then dh=0.9 elseif dh<-0.9 then dh=-0.9 end SetEntityHeading(v,h+dh) end '
            'if HasEntityCollidedWithAnything(v) then local n=GetCollisionNormalOfLastHitForEntity(v) if math.abs(n.z)<0.6 and GetGameTimer()-last>600 then hits=hits+1 last=GetGameTimer() '
            'if #imp<3 then local d=vector2(c.x,c.y)-O imp[#imp+1]=string.format("%%.2f/%%.2f/%%.2f/%%.2f",d.x*cH+d.y*sH,-d.x*sH+d.y*cH,n.x,n.y) end end end '
            'if fr%%10==0 then for k,D in pairs(DOORS) do if #(c-D.p)<6.0 then dmax[k]=math.max(dmax[k],dopen(k)) end end end end '
            '%s local reached=false local t0=GetGameTimer() SetEntityMaxSpeed(v,want+0.3) '
            'while GetGameTimer()-t0<%d do local c=GetEntityCoords(v) if #(vector2(c.x,c.y)-T)<1.2 then reached=true break end '
            'local sp=GetEntitySpeed(v) slice(v,sp<want and (rev and 22 or 23) or 1,tick) end '
            'local c=GetEntityCoords(v) local d=vector2(c.x,c.y)-O '
            'return string.format("%%s|%%d|%%.2f,%%.2f,%%.2f|%%.2f|%%.2f|",tostring(reached),hits,d.x*cH+d.y*sH,-d.x*sH+d.y*cH,c.z,dmax.IN,dmax.OUT)..table.concat(imp,",")') % (
            tx, ty, abs(spd), 'true' if spd < 0 else 'false', F.OX, F.OY, F.HDEG, F.HDEG,
            'for i=1,4 do slice(v,1,tick) end' if brake_first else '', tmax)
    r = PR.lua(code, tmax // 1000 + 30).split('|')
    at = [float(x) for x in r[2].split(',')]
    return {'to': [round(u, 2), round(v, 2)], 'reached': r[0] in ('true', '1'), 'impacts': int(r[1]), 'at_u_v_z': at,
            'door_in_open': float(r[3]), 'door_out_open': float(r[4]), 'first_impacts_u_v_nx_ny': [x for x in r[5].split(',') if x]}
def _delete():
    return _pr().lua('local p=PlayerPedId() local v=_G.__gv TaskLeaveVehicle(p,v,16) Wait(1500) SetEntityAsMissionEntity(v,true,true) DeleteVehicle(v) Wait(200) '
                     'return tostring(not DoesEntityExist(v))', 20) in ('true', '1')
def _doors(open_):
    """open (True) or shut + release (False) both roll-ups through the door system; returns their read-back (IN, OUT) after. The player
    stands on the plaza between the two doors first (rig 2026-10-30: read from wherever the previous step left the player, the door
    objects were not there - every read -1)."""
    PR = _pr(); ic, oc = _lanes(); PR.stand(52.0, (ic + oc) / 2, 28.4); __import__('time').sleep(2.5)
    r = PR.lua(doors_lua() + ('dsys("IN",true) dsys("OUT",true) Wait(4000)' if open_ else 'dsys("IN",false) dsys("OUT",false) Wait(500)')
                  + ' return string.format("%.2f:%.2f",dopen("IN"),dopen("OUT"))', 60).split(':')
    return float(r[0]), float(r[1])
def gdrive_selftest():
    """each piece on its own: (1) both read-backs: shut ~0, opened by the door system > 1.0, shut again ~0; (2) a car on the IN lane
    moves >= 2 m on 8 gas slices (the shared method, the keys script's engine); (3) it is deleted."""
    import jc3_pgarage as G
    shut0 = _doors(False); opened = _doors(True); shut1 = _doors(False)
    door_ok = all(0 <= x < 0.3 for x in shut0 + shut1) and all(x > 1.0 for x in opened)
    purged, eng = _gspawn('police3', 62.0, G.IN_C, heading_minus_u())
    r = _pr().lua(_jj().DRV + 'local v=_G.__gv local c0=GetEntityCoords(v) local off=0 SetEntityMaxSpeed(v,30.0) '
                  'for i=1,8 do slice(v,23) hold(v,%.1f) if not GetIsVehicleEngineRunning(v) then off=off+1 end end for i=1,4 do slice(v,1) end '
                  'return string.format("%%.2f:%%d",#(GetEntityCoords(v)-c0),off)' % heading_minus_u(), 40).split(':')
    moved, off = float(r[0]), int(r[1]); gone = _delete()
    res = {'rollups_shut_open_shut': {'IN': [shut0[0], opened[0], shut1[0]], 'OUT': [shut0[1], opened[1], shut1[1]]}, 'purged_before_spawn': purged,
           'engine_fuel': eng, 'moved_m_on_8_gas_slices': moved, 'engine_off_reads_during_gas': off, 'deleted': gone}
    ok = door_ok and moved >= 2.0 and gone; res['ok'] = ok
    return res, ok
def gdrive_control():
    """the drive method proven before any drive verdict: the open IN lane (nothing built in it from u 62 to 50: jc3_corridor.py) must
    arrive with 0 impacts; a run into the police east face's solid stone (v -46.1, full height at u 44.65; the target is inside the
    building) must NOT arrive and must count impacts."""
    import jc3_pgarage as G
    res = {}
    for name, (u0, v0, u1, v1) in (('open lane', (62.0, G.IN_C, 50.0, G.IN_C)), ('planted wall', (56.0, -46.1, 40.0, -46.1))):
        _gspawn('police3', u0, v0, heading_minus_u())
        res[name] = _leg(u1, v1, 3.0, tmax=15000 if name == 'planted wall' else 25000); res[name]['deleted'] = _delete()
    ok = (res['open lane']['reached'] and res['open lane']['impacts'] == 0 and not res['planted wall']['reached'] and res['planted wall']['impacts'] > 0)
    return res, ok
def route():
    """the drive's waypoints: the plan's loop_route (jc3_pgarage), the same points the swept-path gate (jc3_drive_sweep.py) checks."""
    import jc3_pgarage as G
    return G.loop_route()
def gdrive(model='police3'):
    """the garage drive: both roll-ups opened through the door system (held), the car spawned on the IN lane facing the door, driven leg
    by leg (brakes first where the direction flips), then deleted and the doors shut and released. Pass: every waypoint reached with 0
    impacts, each roll-up read open (> 1.0) while the car was at it, the car out on the plaza past the OUT door, deleted, both doors read
    shut again (< 0.3)."""
    pts = route(); pre = _doors(True)
    if not all(x > 1.0 for x in pre):
        _doors(False); raise SystemExit(f'PROBE: the door system did not open the roll-ups (read {pre}) - nothing was tested')
    purged, eng = _gspawn(model, pts[0][0], pts[0][1], heading_minus_u())
    legs = []; prev = 1
    for u, v, spd in pts[1:]:
        leg = _leg(u, v, spd, brake_first=(spd > 0) != (prev > 0)); prev = spd; legs.append(leg)
        if not leg['reached']: break
    gone = _delete(); post = _doors(False)
    din = max(l['door_in_open'] for l in legs); dout = max(l['door_out_open'] for l in legs)
    ok = (len(legs) == len(pts) - 1 and all(l['reached'] and l['impacts'] == 0 for l in legs) and din > 1.0 and dout > 1.0
          and legs[-1]['at_u_v_z'][0] > 50.0 and gone and all(0 <= x < 0.3 for x in post))
    return {'vehicle': model, 'purged_before_spawn': purged, 'engine_fuel': eng, 'doors_open_before': pre, 'door_in_open_at_car': din,
            'door_out_open_at_car': dout, 'doors_after_shut': post, 'deleted': gone, 'impacts': sum(l['impacts'] for l in legs),
            'legs_done': f'{len(legs)}/{len(pts) - 1}', 'legs': legs, 'ok': ok}, ok
def gdrive_van(): return gdrive('policet')
