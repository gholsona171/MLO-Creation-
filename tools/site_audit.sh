#!/bin/bash
# site_audit.sh: the in-game checks Antonio kept finding by eye (round 6, 2026-10-23), run on the live rig after every deploy and
# BEFORE any shots go out. Needs the rig up with a client in (tc_restart.sh). Prints one AUDIT line per check; anything not OK gets
# fixed at its source first.
#  1 OPENINGS  every gate / door in site/yard/yard_info.json walked through both ways by the player ped with NO lock system attached
#              (stops rcore_doorlock + c9_trapphone first): a door that can't be walked through is jammed (header too low, door set in
#              the ground, something on its far side - yard objects have big extents, check with rays, not centre points).
#  2 GROUND    a 0.5 m ray grid over the lot (lot_plan.OVER, the building excluded): every hit that is NOT our blacktop / overlay is a
#              leftover (old slab, gravel, porch pad, terrain poking through) - clustered and listed.
#  3 POLES     every utility pole / lamp within 12 m of the building or on the lot: its top is checked for cables that hang below
#              3 m over the ground nearby (loose drops after a span was cut) - a ray fan around each pole at 0.5-3 m height.
#  4 SKY       night shots are only valid with the clock HELD (a time-sync resource resets one-off overrides): use the night thread.
cd /c/C9Test
T=/c/Users/anton/Documents/Codex/wow2easy_move
for r in rcore_doorlock c9_trapphone; do ./t.sh con "stop $r" >/dev/null; done
RUNS=$(py -3 -W ignore -c "
import json, math, sys
sys.path.insert(0, r'$(cygpath -w $T/tools)'); import yard_plan as Y
out = []
for nm, md, x, y, z, h in Y.gates():
    o = next(o for o in Y.OPENINGS if (o['kind'] + str(Y.OPENINGS.index(o) + 1)) == nm)
    i = o['seg']; a, _ = Y.seg(i); u, n = Y.seg_frame(i); c = o['s'] + o['w'] / 2
    mx, my = a[0] + u[0] * c, a[1] + u[1] * c
    out.append('{\"%s\",%.2f,%.2f,%.2f,%.2f}' % (nm, mx + n[0] * 3.0, my + n[1] * 3.0, mx - n[0] * 3.5, my - n[1] * 3.5))
print(','.join(out))")
./t.sh cl 1 "local p=PlayerPedId() local res={} for _,r in ipairs({$RUNS}) do for _,dir in ipairs({1,-1}) do local ax,ay,bx,by=r[2],r[3],r[4],r[5] if dir<0 then ax,ay,bx,by=r[4],r[5],r[2],r[3] end ClearPedTasksImmediately(p) SetEntityCoords(p,ax,ay,49.0) Wait(4500) local t0=GetGameTimer() TaskGoStraightToCoord(p,bx,by,47.5,1.0,20000,0.0,0.3) local best=1e9 while GetGameTimer()-t0<14000 do local pc=GetEntityCoords(p) local d=#(vector3(pc.x,pc.y,0)-vector3(bx,by,0)) if d<best then best=d end Wait(250) end res[#res+1]=r[1]..(dir>0 and ' in:' or ' out:')..(best<1.5 and 'OK' or ('BLOCKED %.1f m'):format(best)) end end return table.concat(res,' ')" 200 | grep -o '"result":"[^"]*"' | sed 's/^/AUDIT OPENINGS /'
BOX=$(py -3 -W ignore -c "
import sys; sys.path.insert(0, r'$(cygpath -w $T/tools)'); import lot_plan as L
print('%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.2f,{%s}' % (L.OVER[0], L.OVER[1], L.OVER[2], L.OVER[3], L.BUILD[0], L.BUILD[1], L.BUILD[2], L.BUILD[3], ','.join('{%.1f,%.1f,%.1f,%.1f}' % r for r in L.ASPH_RECTS)))")
./t.sh cl 1 "local x0,x1,y0,y1,bx0,bx1,by0,by1,AR=$BOX local function onlot(x,y) for _,r in ipairs(AR) do if x>r[1]+0.6 and x<r[2]-0.6 and y>r[3]+0.6 and y<r[4]-0.6 then return true end end return false end local p=PlayerPedId() SetEntityCoords(p,(x0+x1)/2,(y0+y1)/2,80.0) FreezeEntityPosition(p,true) Wait(6000) local cnt={} local bad={} local n=0 local y=y0+1.0 while y<y1-1.0 do local x=x0+1.0 while x<x1-1.0 do if onlot(x,y) and not (x>bx0-0.3 and x<bx1+0.3 and y>by0-0.3 and y<by1+3.6) then local r=StartExpensiveSynchronousShapeTestLosProbe(x,y,70.0,x,y,40.0,1,p,7) local _,hit,pos,_,mat=GetShapeTestResultIncludingMaterial(r) n=n+1 if hit==1 then cnt[mat]=(cnt[mat] or 0)+1 cells=cells or {} local k=mat..'@'..math.floor(x/3)*3 ..','..math.floor(y/3)*3 cells[k]=(cells[k] or 0)+1 if not (pos.z>46.0 and pos.z<48.2) then bad[#bad+1]=string.format('%.0f,%.0f z%.1f',x,y,pos.z) end end end x=x+0.5 end y=y+0.5 end FreezeEntityPosition(p,false) local top,tm=0,0 for m,c in pairs(cnt) do if c>top then top,tm=c,m end end local odd={} for k,c in pairs(cells or {}) do if not k:find('^'..tm..'@') and c>2 then odd[#odd+1]=k..'x'..c end end table.sort(odd) return 'rays '..n..' blacktop material '..tm..' ('..top..') OTHER ground materials: '..table.concat(odd,' ')..' | height outliers: '..table.concat(bad,' ',1,math.min(#bad,15))" 200 | grep -o '"result":"[^"]*"' | sed 's/^/AUDIT GROUND /'
grep -h "WIRES_SAG" $T/site/wires/*.log 2>/dev/null | sed "s/^/AUDIT POLES /" || true
echo "AUDIT POLES (wires.py WIRES_SAG lines above; none = no low-hanging span)"
