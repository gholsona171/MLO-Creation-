#!/bin/bash
# ring.sh <prefix> <tx> <ty> <tz> <dist> <height>  -> 4 shots N/E/S/W + sheet
cd /c/C9Test/shots/mlo
for a in 0 90 180 270; do
  ./shot.sh "$1_ring$a" "local t=vector3($2,$3,$4) local r=math.rad($a) local p=vector3($2+math.sin(r)*$5,$3+math.cos(r)*$5,$4+$6) SetEntityCoords(cache.ped,p.x,p.y,p.z) FreezeEntityPosition(cache.ped,true) Wait(2500) MS.cam(p,t,50.0) return 'ring $a'" 5 >/dev/null
done
py -3 - "$1" <<'PY'
import sys
from PIL import Image
n=sys.argv[1]; ims=[Image.open(f'{n}_ring{a}.png').resize((960,540)) for a in (0,90,180,270)]
s=Image.new('RGB',(1920,1080))
for k,im in enumerate(ims): s.paste(im,((k%2)*960,(k//2)*540))
s.save(f'{n}_ring.jpg',quality=85); print('sheet', f'{n}_ring.jpg')
PY
