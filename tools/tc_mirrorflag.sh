#!/bin/bash
# tc_mirrorflag.sh <flags> : rig experiment - set every mirror portal's flags in the built layout, re-run meta + gates + assemble,
# restart, stand the ped at the master-bath vanity and shoot the mirror -> shots/towercity/mirflag_<flags>.png
F=$1; cd /c/Users/anton/Documents/Codex/TowerCity/work
py -3 -c "
import json; p='l3/l3_layout.json'; L=json.load(open(p)); n=0
for q in L['portals']:
    if q.get('flags',0) in (4,260,1284,1028,1280,5,6,12): q['flags']=$F; n+=1
json.dump(L,open(p,'w')); print('mirror portals',n)"
py -3 west_meta.py >/dev/null && py -3 site_meta.py >/dev/null && py -3 sweep_gate.py | tail -1 && bash assemble.sh 2>&1 | grep -c deployed
cd /c/C9Test && bash tc_restart.sh >/dev/null 2>&1
./t.sh cl 1 "local O=vector2(-78.897,-827.328) local H=math.rad(69.5) local function W(u,v,z) return vector3(O.x+u*math.cos(H)-v*math.sin(H), O.y+u*math.sin(H)+v*math.cos(H), z) end
Wait(2000) local p=PlayerPedId() SetEntityVisible(p,true) FreezeEntityPosition(p,false) ClearPedTasksImmediately(p)
local w=W(-20.0,-1.3,261.6) SetEntityCoords(p,w.x,w.y,w.z,false,false,false,false) SetEntityHeading(p,(69.5+270)%360) Wait(3000) return 'placed'" 20 >/dev/null
OX=-78.897 OY=-827.328 WAIT=5 bash tc_tviews.sh mirflag_$F "m -21.8 -2.0 263.4 -18.1 -1.0 262.9" | tail -1; bash tcshot_off.sh >/dev/null
