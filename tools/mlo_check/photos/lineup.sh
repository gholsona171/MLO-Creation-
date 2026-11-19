#!/bin/bash
# lineup.sh <name> <x> <y> <z> <dist> <height> [rooms=2] [px py pz]
# ring of 4 distance shots around (x,y,z), then corner sheets of the <rooms> biggest rooms of the interior at the probe point.
cd /c/C9Test/shots/mlo
N=$1; X=$2; Y=$3; Z=$4; D=$5; HH=$6; K=${7:-2}; PX=${8:-$2}; PY=${9:-$3}; PZ=${10:-$4}
./ring.sh "$N" $X $Y $Z $D $HH
[ "$K" = 0 ] && exit 0
H=$(cat helper.lua)
R=$(cd /c/C9Test && ./t.sh cl ${PL:-2} "$H
MS.off() FreezeEntityPosition(cache.ped,false) SetEntityCoords(cache.ped,$PX,$PY,$PZ+1.0) Wait(4000)
local i=GetInteriorAtCoords($PX,$PY,$PZ+1.0) if i==0 then return 'NOINT' end
PinInteriorInMemory(i) local t=0 while not IsInteriorReady(i) and t<50 do Wait(100) t=t+1 end
local n=GetInteriorRoomCount(i) local L={}
for r=1,n-1 do local a,b,c,d,e,f=GetInteriorRoomExtents(i,r) L[#L+1]={r,(d-a)*(e-b)} end
table.sort(L,function(p,q) return p[2]>q[2] end)
local o={} for k=1,math.min($K,#L) do o[#o+1]=L[k][1] end
return 'ROOMS '..n..' '..table.concat(o,' ')" 40 | grep -o '"result":"[^"]*"' | sed 's/"result":"//;s/"$//')
echo "$N interior: $R"
case "$R" in ROOMS*) set -- $R; shift 2; for r in "$@"; do P=$N IX=$PX IY=$PY IZ=$((${PZ%.*}+1)) R=$r ./corners.sh | grep -oE '"(result|err)":"[^"]*"'; echo "corners room $r done"; done;; esac
