"""Justice Center + Tower City joint scenario proof on the rig (both maps loaded, as a buyer runs them), after a FRESH client join:
  1. DoesScenarioBlockingAreaExist for every box both maps add (Justice Center's one box from work/scripts/area_clear.lua, Tower City's
     one per lot computed by its own deployed area_clear.lua's bbox())
  2. client 1 parked over each map for WAIT s (ambient population streams in), then: AMBIENT peds (population types 1-5) inside each lot
     (must be 0) - script / mission peds (the c9_dj cashier, tower_city_life) are listed with type and model, never counted as failures -
     and ambient pedestrians on the sidewalks round it (must be > 0; Tower City: a ring 2-8 m outside each lot rectangle at street z)
Every rig call that gets no answer raises. Client 1's ped is saved and put back; tc_release.sh runs at the end.
Run: py -3 tools/joint_proof.py [wait_s]   -> work/joint_proof.json, JOINT_PROOF PASS / FAIL"""
import sys, json, re, time
from pathlib import Path
W = Path(__file__).parent.parent; sys.path.insert(0, str(W)); import jc_probe as P, jc_frame as F
WAIT = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
TC = open(r'C:/C9Test/live/resources/[localtest]/tower_city/area_clear.lua').read()
TC_HEAD = TC[:TC.index('local function strips')]
JC = open(W / 'scripts/area_clear.lua').read()
JC_BOX = JC[JC.index('local S_BOXES'):JC.index('\n}\n', JC.index('local S_BOXES')) + 3]
def tc_boxes():
    r = P.lua(TC_HEAD + " local Z0=5.0 local o={} for _,L in ipairs(LOTS) do local x0,y0,x1,y1=bbox(L) o[#o+1]=string.format('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%s',x0,y0,Z0,x1,y1,ZS,tostring(DoesScenarioBlockingAreaExist(x0,y0,Z0,x1,y1,ZS))) end return table.concat(o,';')", 30)
    return [s.split(',') for s in r.split(';')]
def jc_box():
    r = P.lua(JC_BOX + " local o={} for _,b in ipairs(S_BOXES) do o[#o+1]=tostring(DoesScenarioBlockingAreaExist(b[1],b[2],b[3],b[4],b[5],b[6])) end return table.concat(o,',')", 30)
    return r.split(',')
# every ped: kind 1 = in the lot, 2 = sidewalk ring; population type (1-5 ambient / scenario, 6 permanent, 7 mission = script peds such as
# the c9_dj cashier or tower_city_life's people: listed, never counted as failures) and its model
COUNT = '''local function ring_or_in(x,y,z) %s end
local amb,scr,pring,lst=0,0,0,{} for _,e in ipairs(GetGamePool("CPed")) do if not IsPedAPlayer(e) and not IsPedInAnyVehicle(e,false) then local c=GetEntityCoords(e) local k=ring_or_in(c.x,c.y,c.z)
 local pt=GetEntityPopulationType(e)
 if k==1 then if pt>=1 and pt<=5 then amb=amb+1 else scr=scr+1 end lst[#lst+1]=string.format("%%.1f,%%.1f,%%.1f pop%%d sc%%s m%%d",c.x,c.y,c.z,pt,tostring(IsPedUsingAnyScenario(e)),GetEntityModel(e))
 elseif k==2 and pt>=1 and pt<=5 then pring=pring+1 end end end
return amb.."|"..scr.."|"..pring.."|"..table.concat(lst,";")'''
def jc_count():
    inl = P.POLY + "local function ring(x,y) for _,q in ipairs(P) do if (q[1]-x)^2+(q[2]-y)^2<100.0 then return true end end return false end "
    return P.lua(inl + COUNT % 'if inlot(x,y) then return 1 elseif ring(x,y) then return 2 end return 0', 40)
def tc_count():
    # TC sidewalks: a ring 2-8 m outside each lot's rectangle (lot frame), at street level (z 25-36, under the decks)
    body = ('for _,L in ipairs(LOTS) do if inside(L,x,y) then return 1 end end '
            'for _,L in ipairs(LOTS) do local dx,dy=x-L.o.x,y-L.o.y local u,v=dx*math.cos(H)+dy*math.sin(H),-dx*math.sin(H)+dy*math.cos(H) '
            'local du=math.max(L.u[1]-u,u-L.u[2],0.0) local dv=math.max(L.v[1]-v,v-L.v[2],0.0) local d=math.max(du,dv) '
            'if d>=2.0 and d<=8.0 and z>25.0 and z<36.0 then return 2 end end return 0')
    return P.lua(TC_HEAD + COUNT % body, 40)
if __name__ == '__main__':
    pos = P.lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f,%.2f,%.2f,%.1f",c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))')
    rep = {}
    try:
        rep['tc_boxes'] = tc_boxes(); rep['jc_boxes'] = jc_box()
        c = F.W(10, 20); P.park(c[0], c[1], 60.0); time.sleep(WAIT)
        a = jc_count().split('|', 3); rep['jc'] = {'ambient_in_lot': int(a[0]), 'script_peds_in_lot': int(a[1]), 'sidewalk_ambient': int(a[2]), 'in_lot': a[3]}
        P.park(-5.0, -855.0, 90.0); time.sleep(WAIT)
        a = tc_count().split('|', 3); rep['tc'] = {'ambient_in_lots': int(a[0]), 'script_peds_in_lots': int(a[1]), 'sidewalk_ambient': int(a[2]), 'in_lots': a[3]}
    finally:
        x, y, z, h = pos.split(','); P.lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) return "back"' % (x, y, z))   # before unfreezing
        P.release(); P.revive()
        P.lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) SetEntityHeading(p,%s) SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) ClearFocus() return "back"' % (x, y, z, h))
    T_ = ('true', '1'); held = all(b[-1] in T_ for b in rep['tc_boxes']) and all(b in T_ for b in rep['jc_boxes'])
    ok = held and rep['jc']['ambient_in_lot'] == 0 and rep['tc']['ambient_in_lots'] == 0 and rep['jc']['sidewalk_ambient'] > 0 and rep['tc']['sidewalk_ambient'] > 0
    json.dump(rep, open(W / 'joint_proof.json', 'w'), indent=1)
    print('JOINT_PROOF', 'PASS' if ok else 'FAIL', '| boxes held: TC', [b[-1] for b in rep['tc_boxes']], 'JC', rep['jc_boxes'], '| JC', rep['jc'], '| TC', rep['tc'])
    sys.exit(0 if ok else 1)
