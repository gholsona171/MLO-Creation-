#!/bin/bash
# ctr/tab.sh : opens the tablet's Venues app on Tower City Grill > Business > Furniture (opens the tablet when it is closed)
cd /c/C9Test
open=$(bash ctr/nui.sh "return document.querySelectorAll('button.tab').length" 2>/dev/null | grep -o '"value":[0-9]*' | cut -d: -f2)
if [ -z "$open" ] || [ "$open" = "0" ]; then
  ./t.sh cl 1 "pcall(function() exports.C9_Laptop:Open() end) Wait(2200) return true" 20 >/dev/null
  node nui.mjs 13172 C9_Laptop "const b=document.querySelector('.grid button.ico[data-id=clubs]'); if(b){const r=b.getBoundingClientRect(); const o={bubbles:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,pointerId:1,isPrimary:true,button:0}; for (const t of ['pointerdown','mousedown','pointerup','mouseup','click']) b.dispatchEvent(new (t.startsWith('pointer')?PointerEvent:MouseEvent)(t,o));} await new Promise(r=>setTimeout(r,3000)); return !!b" >/dev/null
fi
bash ctr/nui.sh "const v=[...document.querySelectorAll('button.tab')].find(x=>x.textContent.trim()=='Tower City Grill'); if(!v) return 'no venue tab'; v.click(); await new Promise(r=>setTimeout(r,2000)); const b=[...document.querySelectorAll('button.tab')].find(x=>x.textContent.trim()=='Business'); b.click(); await new Promise(r=>setTimeout(r,1500)); const f=[...document.querySelectorAll('button.tab,button')].find(x=>x.textContent.trim()=='Furniture'); f.click(); await new Promise(r=>setTimeout(r,2500)); return 'TCG furniture'"
