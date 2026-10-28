"""Justice Center phase 1: in-game probes on the C9Test rig (client 1), each one proven on a known answer first (doc 07):
  grid   rays straight down every 2 m over the lot (+ control points: open sea must MISS, Rockstar's sidewalk must HIT ~28.3) -> every
         lot point must hit within 6 cm of the slab (jc_frame.slab_z) on the CONCRETE material; prints misses / steps
  walk   the player ped walks three lines across the lot (west -> east, south -> north, the diagonal); z logged every 0.25 s; it must
         arrive, never drop more than 0.5 m under the slab, never climb / ragdoll / fall
  ai     ped parked at the lot centre 75 s (ambient population streams in); counts peds / vehicles inside the lot (must be 0) and on the
         sidewalk ring (must be > 0: the sidewalks keep their people), asks GetClosestVehicleNode inside the lot (must be none) and on the
         street (must be some: control)
  drive  an AI driver drives a car round the block (Davis Ave -> Innocence Blvd -> Roy Lowenstein Blvd -> Macdonald St) and must reach
         every corner, never entering the lot
Every rig call that gets no answer raises (nothing was tested). Client 1's ped is saved first and put back; tc_release.sh always runs.
Run: py -3 jc_probe.py grid walk ai drive   -> work/probe_<name>.json, PROBE_<NAME>_PASS / _FAIL lines; exit 1 on any fail."""
import json, subprocess, sys, math, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import jc_frame as F
from shapely.geometry import Polygon, Point
J = F.J; GB = r'C:\Program Files\Git\bin\bash.exe'
LOT = Polygon([p[:2] for p in F.lot_w()]); RING = LOT.buffer(9.0).difference(LOT)
def lua(code, timeout=60):
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" %d' % timeout, code], capture_output=True, text=True, timeout=timeout + 30)
    m = re.search(r'"result":"(.*?)"(,|\})', r.stdout, re.S)
    if not m: raise SystemExit('PROBE: no answer from the rig - nothing was tested: ' + (r.stdout + r.stderr)[-400:])
    return m.group(1)
def release():
    subprocess.run([GB, '-c', 'bash /c/C9Test/tc_release.sh'], capture_output=True, text=True, timeout=60)
POLY = 'local P={' + ','.join('{%.2f,%.2f}' % (p[0], p[1]) for p in F.lot_w()) + '}\n' + '''
local function inlot(x,y) local c=false local n=#P for i=1,n do local a=P[i] local b=P[i%n+1] if ((a[2]>y)~=(b[2]>y)) and (x<(b[1]-a[1])*(y-a[2])/(b[2]-a[2])+a[1]) then c=not c end end return c end
'''
def revive():
    """never test with a dead / downed ped (Qbox last stand: health 0, ragdolls on every step - the console revive does not lift it)"""
    return lua("local p=PlayerPedId() if IsEntityDead(p) or GetEntityHealth(p) < 150 then local c=GetEntityCoords(p) NetworkResurrectLocalPlayer(c.x,c.y,c.z+0.5,GetEntityHeading(p),true,false) Wait(500) p=PlayerPedId() TriggerEvent('qbx_medical:client:playerRevived') end SetEntityHealth(p,200) ClearPedTasksImmediately(p) return tostring(GetEntityHealth(p))", 30)
def park(x, y, z, invisible=True):
    return lua('local p=PlayerPedId() SetEntityCoords(p,%.2f,%.2f,%.2f) %s SetFocusPosAndVel(%.2f,%.2f,%.2f,0.0,0.0,0.0) RequestCollisionAtCoord(%.2f,%.2f,%.2f) return "parked"'
               % (x, y, z, 'SetEntityVisible(p,false) FreezeEntityPosition(p,true) SetEntityCollision(p,false,false)' if invisible else 'SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true)', x, y, z, x, y, z))
def grid():
    pts = []
    x0, y0, x1, y1 = LOT.bounds
    for i in range(int((x1 - x0) / 2) + 1):
        for j in range(int((y1 - y0) / 2) + 1):
            x, y = x0 + 1.013 + i * 2, y0 + 1.017 + j * 2
            if LOT.contains(Point(x, y)): pts.append((x, y))
    sea = (-1800.0, -1400.0); side = F.W(70.0, 0.0)                    # controls: open sea west of the city; Rockstar's sidewalk (Innocence Blvd)
    out = {}; bad = []
    for cx, cy in ((F.W(10, -35)), (F.W(10, 45)), (F.W(-20, 95))):       # stream collision round three spots along the lot
        park(cx, cy, 40.0); time.sleep(4)
        todo = [p for p in pts if p not in out and math.dist(p, (cx, cy)) < 75]
        for k in range(0, len(todo), 120):
            chunk = todo[k:k + 120]
            code = 'local Q={' + ','.join('{%.3f,%.3f}' % p for p in chunk) + '} local o={} for i,q in ipairs(Q) do local h=StartExpensiveSynchronousShapeTestLosProbe(q[1],q[2],60.0,q[1],q[2],15.0,1,0,7) local _,hit,c,_,m=GetShapeTestResultIncludingMaterial(h) o[#o+1]=hit==1 and string.format("%.3f:%d",c.z,m) or "x" end return table.concat(o,";")'
            res = lua(code, 60).split(';')
            if len(res) != len(chunk): raise SystemExit('PROBE grid: %d answers for %d rays' % (len(res), len(chunk)))
            for p, r in zip(chunk, res): out[p] = r
    park(*side, 40.0); time.sleep(3)
    ctl = lua('local o={} for _,q in ipairs({{%.2f,%.2f},{%.2f,%.2f}}) do local h=StartExpensiveSynchronousShapeTestLosProbe(q[1],q[2],60.0,q[1],q[2],15.0,1,0,7) local _,hit,c=GetShapeTestResult(h) o[#o+1]=hit==1 and string.format("%%.3f",c.z) or "x" end return table.concat(o,";")' % (sea[0], sea[1], side[0], side[1])).split(';')
    proven = ctl[0] == 'x' and ctl[1] != 'x' and abs(float(ctl[1]) - 28.3) < 0.2
    mats = {}; obst = []; KEPT = json.load(open(J / 'work/p1_maps_report.json'))['kept_band_lr']
    for p, r in out.items():
        if r == 'x': bad.append(('MISS', p)); continue
        z, m = r.split(':'); z = float(z); mats[m] = mats.get(m, 0) + 1; zs = F.slab_z(*p)
        if abs(z - zs) > 0.06:
            if z > zs and any(math.hypot(p[0] - k[1], p[1] - k[2]) < 1.5 for k in KEPT): obst.append(('%s crown / trunk %.1f m up' % (next(k[0] for k in KEPT if math.hypot(p[0] - k[1], p[1] - k[2]) < 1.5), z - zs), p)); continue
            bad.append(('STEP %.2f' % (z - zs), p))
    missing = len(pts) - len(out)
    ok = proven and not bad and not missing
    json.dump({'points': len(pts), 'answered': len(out), 'controls': ctl, 'materials': mats, 'bad': [(b, [round(t, 1) for t in F.L(*p)]) for b, p in bad], 'kept_props_hit': [(b, [round(t, 1) for t in F.L(*p)]) for b, p in obst]}, open(J / 'work/probe_grid.json', 'w'), indent=0)
    print('PROBE_GRID', 'PASS' if ok else 'FAIL', '| rays', len(out), 'of', len(pts), '| controls sea=%s sidewalk=%s (%s)' % (ctl[0], ctl[1], 'proven' if proven else 'NOT PROVEN'),
          '| bad', len(bad), bad[:6], '| kept props hit (palm crowns: not ground)', len(obst), '| materials', mats)
    return ok
def walk():
    lines = [((-44, 20), (62, 20)), ((10, -66), (10, 98)), ((-42, -62), (55, 78))]
    res = []
    for (u0, v0), (u1, v1) in lines:
        a = F.W(u0, v0); b = F.W(u1, v1); za = F.slab_z(*a) + 1.0
        park(a[0], a[1], za, invisible=False); time.sleep(2); hp = revive(); time.sleep(2)
        if int(float(hp)) < 150: raise SystemExit('PROBE walk: the ped could not be revived (health %s) - nothing was tested' % hp)
        code = POLY + '''local p=PlayerPedId() if IsEntityDead(p) then NetworkResurrectLocalPlayer(GetEntityCoords(p),0.0,true,false) p=PlayerPedId() end
ClearPedTasksImmediately(p) SetEntityCoords(p,%.2f,%.2f,%.2f) Wait(1500) TaskGoStraightToCoord(p,%.2f,%.2f,%.2f,2.0,120000,0.0,0.0)
local log={} local t0=GetGameTimer() local bad=0 local minz=999.0 local lastd=1e9 local stuck=0
while GetGameTimer()-t0<110000 do local c=GetEntityCoords(p) local d=#(vector2(c.x,c.y)-vector2(%.2f,%.2f))
 if IsPedRagdoll(p) or IsPedClimbing(p) or IsPedFalling(p) or IsPedJumping(p) then bad=bad+1 end
 log[#log+1]=string.format("%%.2f,%%.2f,%%.3f",c.x,c.y,c.z) if d<1.2 then break end
 if d>lastd-0.05 then stuck=stuck+1 else stuck=0 end lastd=d if stuck>40 then break end Wait(250) end
local c=GetEntityCoords(p) return string.format("%%d|%%.2f|%%d|",bad,#(vector2(c.x,c.y)-vector2(%.2f,%.2f)),GetGameTimer()-t0)..table.concat(log,";")''' % (a[0], a[1], za, b[0], b[1], F.slab_z(*b), b[0], b[1], b[0], b[1])
        r = lua(code, 140); bad, dist, ms, log = r.split('|', 3)
        P_ = [tuple(map(float, s.split(','))) for s in log.split(';') if s]
        low = [round(z - F.slab_z(x, y), 2) for x, y, z in P_ if LOT.contains(Point(x, y))]
        ok = int(bad) == 0 and float(dist) < 1.5 and len(P_) > 10 and (min(low) if low else -9) > -0.5 and (max(low) if low else 9) < 1.4
        res.append({'line': [(u0, v0), (u1, v1)], 'ok': ok, 'bad_states': int(bad), 'end_dist': float(dist), 'ms': int(ms), 'samples': len(P_),
                    'ped_z_minus_slab': [min(low), max(low)] if low else None,
                    'path_uvz': [[round(t, 2) for t in F.L(x, y)] + [round(z - F.slab_z(x, y), 2)] for x, y, z in P_]})
        print('PROBE_WALK line %s -> %s: %s, %d samples, end %.2f m short, %d bad states, ped z - slab %s' % ((u0, v0), (u1, v1), 'ok' if ok else 'FAIL', len(P_), float(dist), int(bad), res[-1]['ped_z_minus_slab']))
    json.dump(res, open(J / 'work/probe_walk.json', 'w'), indent=1)
    ok = all(r['ok'] for r in res); print('PROBE_WALK', 'PASS' if ok else 'FAIL'); return ok
def ai():
    c = F.W(10, 20); park(c[0], c[1], 45.0)
    lua('SetPedDensityMultiplierThisFrame(1.0) return "ok"')
    time.sleep(75)
    st = F.W(75.0, 0.0)                                               # control: Innocence Blvd's own lanes
    code = POLY + '''local o={pin=0,pring=0,vin=0,vstreet=0,pinl={}}
local function ring(x,y) for _,q in ipairs(P) do if (q[1]-x)^2+(q[2]-y)^2<81.0 then return true end end return false end
for _,e in ipairs(GetGamePool("CPed")) do if not IsPedAPlayer(e) then local c=GetEntityCoords(e)
  if inlot(c.x,c.y) then o.pin=o.pin+1 o.pinl[#o.pinl+1]=string.format("%%.1f,%%.1f,%%.1f",c.x,c.y,c.z) elseif ring(c.x,c.y) then o.pring=o.pring+1 end end end
for _,e in ipairs(GetGamePool("CVehicle")) do local c=GetEntityCoords(e) if inlot(c.x,c.y) then o.vin=o.vin+1 elseif #(vector2(c.x,c.y)-vector2(%.2f,%.2f))<120.0 then o.vstreet=o.vstreet+1 end end
local nin=0 for _,q in ipairs({{%s},{%s},{%s}}) do local ok,pos=GetClosestVehicleNode(q[1],q[2],30.0,0,3.0,0) if ok and inlot(pos.x,pos.y) then nin=nin+1 end end
local ok2,pos2=GetClosestVehicleNode(%.2f,%.2f,28.5,0,3.0,0)
local sc=DoesScenarioExistInArea(%.2f,%.2f,30.0,40.0,false) local sc2=DoesScenarioExistInArea(%.2f,%.2f,30.0,40.0,false)
return string.format("%%d|%%d|%%d|%%d|%%d|%%s|%%s|%%s|",o.pin,o.pring,o.vin,o.vstreet,nin,tostring(ok2 and #(vector2(pos2.x,pos2.y)-vector2(%.2f,%.2f))<15.0),tostring(sc),tostring(sc2))..table.concat(o.pinl,";")''' % (
        st[0], st[1], '%.2f,%.2f' % F.W(-20, -45), '%.2f,%.2f' % F.W(40, -28), '%.2f,%.2f' % F.W(0, 60), st[0], st[1], *F.W(-10, 30), *F.W(-15, 160), st[0], st[1])
    r = lua(code, 60); pin, pring, vin, vstreet, nin, ctl_node, sc_in, sc_ctl, lst = r.split('|', 8)
    # control scenario point: the far side of Davis Ave (another block, untouched) - must exist, or the scenario question proves nothing
    ok_ctl = ctl_node == 'true'
    ok = int(pin) == 0 and int(vin) == 0 and int(nin) == 0 and ok_ctl and int(pring) > 0      # (DoesScenarioExistInArea answers for the POINT, not its use: reported only)
    rep = {'peds_in_lot': int(pin), 'peds_on_sidewalk_ring': int(pring), 'vehicles_in_lot': int(vin), 'vehicles_on_streets_120m': int(vstreet),
           'vehicle_nodes_in_lot': int(nin), 'street_node_control': ok_ctl, 'scenario_in_lot': sc_in, 'scenario_control_other_block': sc_ctl, 'peds_in_lot_at': lst}
    json.dump(rep, open(J / 'work/probe_ai.json', 'w'), indent=1)
    print('PROBE_AI', 'PASS' if ok else 'FAIL', rep)
    return ok
def drive():
    corners = [F.W(-56, 125), F.W(80, 90), F.W(76, -84), F.W(-60, -80), F.W(-56, 125)]
    s = corners[0]
    code = POLY + '''local m=GetHashKey("police3") RequestModel(m) local t=GetGameTimer() while not HasModelLoaded(m) and GetGameTimer()-t<10000 do Wait(50) end
local dm=GetHashKey("s_m_y_cop_01") RequestModel(dm) while not HasModelLoaded(dm) and GetGameTimer()-t<15000 do Wait(50) end
local _,gz=GetGroundZFor_3dCoord(%.2f,%.2f,40.0,false) local v=CreateVehicle(m,%.2f,%.2f,gz+0.5,%.1f,false,false) local d=CreatePedInsideVehicle(v,26,dm,-1,false,false)
SetDriverAbility(d,1.0) SetBlockingOfNonTemporaryEvents(d,true) _G.__jcv=v _G.__jcd=d return "spawned"''' % (s[0], s[1], s[0], s[1], (F.HDEG - 90.0 + 90) % 360)
    p0 = F.W(-56, 115); park(p0[0], p0[1], 60.0); time.sleep(4); revive()
    lua(code, 40); res = []
    for k, c in enumerate(corners[1:]):
        lua('local p=PlayerPedId() SetEntityCoords(p,%.2f,%.2f,70.0) SetFocusEntity(_G.__jcv) return "f"' % c)
        code = POLY + '''local v,d=_G.__jcv,_G.__jcd local okn,tg=GetClosestVehicleNode(%.2f,%.2f,28.3,1,3.0,0) TaskVehicleDriveToCoordLongrange(d,v,tg.x,tg.y,tg.z,14.0,786603,6.0)
local t0=GetGameTimer() local inl=0 local minh=1000.0
while GetGameTimer()-t0<90000 do local c=GetEntityCoords(v) if inlot(c.x,c.y) then inl=inl+1 end
 local dd=#(vector2(c.x,c.y)-vector2(tg.x,tg.y)) if dd<minh then minh=dd end if dd<8.0 then break end Wait(250) end
local c=GetEntityCoords(v) return string.format("%%.1f|%%d|%%d|%%.1f,%%.1f,%%.1f|%%.0f",minh,inl,GetGameTimer()-t0,c.x,c.y,c.z,GetEntityHealth(v))''' % (c[0], c[1])
        r = lua(code, 120).split('|')
        ok = float(r[0]) < 8.0 and int(r[1]) == 0
        res.append({'to_corner': k + 1, 'closest_m': float(r[0]), 'samples_in_lot': int(r[1]), 'ms': int(r[2]), 'at': r[3], 'health': r[4], 'ok': ok})
        print('PROBE_DRIVE corner %d: %s, closest %.1f m, %d samples in the lot, %.0f s' % (k + 1, 'ok' if ok else 'FAIL', float(r[0]), int(r[1]), int(r[2]) / 1000))
    lua('if _G.__jcd then DeleteEntity(_G.__jcd) end if _G.__jcv then DeleteEntity(_G.__jcv) end ClearFocus() return "gone"')
    json.dump(res, open(J / 'work/probe_drive.json', 'w'), indent=1)
    ok = all(r['ok'] for r in res); print('PROBE_DRIVE', 'PASS' if ok else 'FAIL'); return ok
if __name__ == '__main__':
    pos = lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f,%.2f,%.2f,%.1f",c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))')
    print('saved ped at', pos); ok = True
    try:
        for a in sys.argv[1:]: ok = {'grid': grid, 'walk': walk, 'ai': ai, 'drive': drive}[a]() and ok
    finally:                                                         # back to where he stood BEFORE unfreezing: released in the air the
        x, y, z, h = pos.split(',')                                  # ped fell and lay downed (health 0) for the next probes
        lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) SetEntityHeading(p,%s) return "back"' % (x, y, z, h))
        release(); revive()
        lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) SetEntityHeading(p,%s) SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) ClearFocus() return "back"' % (x, y, z, h))
    sys.exit(0 if ok else 1)
