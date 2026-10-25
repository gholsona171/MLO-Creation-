#!/bin/bash
# ctr/placeat.sh <id> <aimx> <aimy> <standx> <standy> <tag> : the owner's way: tablet > Place on piece #id, the laser aimed at the floor
# point (the ped stands at stand, facing it), a shot, Enter. Prints where the server saved it.
cd /c/C9Test
H=$(py -3 -c "import math;dx=$2-($4);dy=$3-($5);print(round(math.degrees(math.atan2(-dx,dy))%360,3))")
./t.sh cl 1 "pcall(function() exports.C9_Laptop:Close() end) Wait(900) local p=PlayerPedId() SetEntityCoordsNoOffset(p,$4+0.0,$5+0.0,29.25,false,false,false) SetEntityHeading(p,$H+0.0) Wait(300) return true" 10 >/dev/null
bash ctr/tab.sh >/dev/null
bash ctr/nui.sh "const row=[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.querySelector&&e.querySelector('button')&&/ #$1\b/.test(e.innerText.split('\n')[0])).sort((a,b)=>a.innerText.length-b.innerText.length)[0]; if(!row) return 'no row'; row.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,600)); [...row.querySelectorAll('button')].find(x=>/^(Place|Move)$/.test(x.textContent.trim())).click(); return 'place #$1'" | grep -o '"value":"[^"]*"'
sleep 1.5
bash ctr/aimplace.sh $2 $3 ${AIMZ:-29.2} place_$6
./t.sh srv "for _, l in pairs(GlobalState.c9dj_props or {}) do for _, p in ipairs(l) do if p.id == $1 then return ('#%d %s at %.3f, %.3f, %.3f h %.2f'):format(p.id, p.model, p.x or 0, p.y or 0, p.z or 0, p.h or 0) end end end return 'not placed'" | grep -o '"result":"[^"]*"'
