#!/bin/bash
# corners.sh  env: P (prefix) IX IY IZ (point inside the interior) R (room index)  -> 4 corner shots of one room + sheet
# Loads the interior first (teleport next to it, pin, wait ready) and never calls room natives on interior 0
# (GetInteriorRoomExtents on an invalid interior throws inside extra-natives-five and can crash the client).
cd /c/C9Test/shots/mlo
for c in "-1 -1" "1 -1" "1 1" "-1 1"; do set -- $c; sx=$1; sy=$2
  ./shot.sh "${P}_r${R}_${sx}_${sy}" "MS.off() FreezeEntityPosition(cache.ped,false) SetEntityCoords(cache.ped,$IX+0.0,$IY+0.0,$IZ+0.0) Wait(4000)
local i=GetInteriorAtCoords($IX+0.0,$IY+0.0,$IZ+0.0) if i==0 then return 'NOINT' end
PinInteriorInMemory(i) local t=0 while not IsInteriorReady(i) and t<80 do Wait(100) t=t+1 end
if not IsInteriorReady(i) then return 'NOTREADY' end
if $R >= GetInteriorRoomCount(i) then return 'NOROOM' end
local a,b,cz,d,e,f=GetInteriorRoomExtents(i,$R) local ctr=MS.w(i,(a+d)/2,(b+e)/2,cz+1.0)
SetEntityCoords(cache.ped,ctr.x,ctr.y,ctr.z) Wait(2000)
local p,mid,hit,L=MS.corner(i,$R,$sx,$sy,1.1) SetEntityCoords(cache.ped,p.x,p.y,p.z-1.0) Wait(800) MS.cam(p,mid,70.0)
return ('corner $sx $sy wallhit %s dist %.1f'):format(tostring(hit),L)" 4
done
py -3 - "${P}_r${R}" <<'PY'
import sys, os
from PIL import Image
n=sys.argv[1]; fs=[f'{n}_{s}.png' for s in ('-1_-1','1_-1','1_1','-1_1')]
s=Image.new('RGB',(1920,1080))
for k,f in enumerate(fs):
    if os.path.exists(f): s.paste(Image.open(f).resize((960,540)),((k%2)*960,(k//2)*540))
s.save(f'{n}.jpg',quality=85); print('sheet',n)
PY
