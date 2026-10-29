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
def sit():
    out = []; ok_all = True
    for s in L['seats']:
        u, v, z, h = s; x, y = W(u, v); revive(); stand(u + 1.2 * math.sin(math.radians(h)) * 0, v - 1.0, JP.G); time.sleep(0.5)
        r = lua('local p=PlayerPedId() TaskStartScenarioAtPosition(p,"PROP_HUMAN_SEAT_BENCH",%.3f,%.3f,%.3f,%.1f,0,true,true) Wait(6000) local c=GetEntityCoords(p) '
                'local u=IsPedUsingScenario(p,"PROP_HUMAN_SEAT_BENCH") or IsPedActiveInScenario(p) return string.format("%%s:%%.3f:%%.3f:%%.3f",tostring(u),c.x,c.y,c.z)' % (x, y, z, (h + F.HDEG) % 360), 40).split(':')
        using = r[0] in ('true', '1'); dx = math.hypot(float(r[1]) - x, float(r[2]) - y); dz = float(r[3]) - z
        good = using and dx < 0.25 and abs(dz) < 0.15; ok_all &= good
        out.append({'seat': [round(u, 2), round(v, 2)], 'using': using, 'dxy': round(dx, 3), 'dz_root_minus_seat': round(dz, 3), 'ok': good})
        lua('ClearPedTasksImmediately(PlayerPedId()) return "c"')
    return out, ok_all
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
