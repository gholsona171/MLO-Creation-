#!/bin/bash
# ctr/store.sh <id> ... : tablet > Store on each piece (back to the storeroom)
cd /c/C9Test
bash ctr/tab.sh >/dev/null
for i in "$@"; do
bash ctr/nui.sh "const row=[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.querySelector&&e.querySelector('button')&&/ #$i\b/.test(e.innerText.split('\n')[0])).sort((a,b)=>a.innerText.length-b.innerText.length)[0]; if(!row) return 'no row'; const b=[...row.querySelectorAll('button')].find(x=>x.textContent.trim()=='Store'); if(!b) return 'not placed'; b.click(); await new Promise(r=>setTimeout(r,1800)); return 'stored #$i'" | grep -o '"value":"[^"]*"'
done
