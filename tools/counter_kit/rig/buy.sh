#!/bin/bash
# ctr/buy.sh '<shop card name>' : scrolls to the card and presses its Buy (tablet open at Business > Furniture)
bash /c/C9Test/ctr/nui.sh "const want='$1'; const c=[...document.querySelectorAll('.shop-card')].find(x=>x.querySelector('.shop-name').textContent.trim()==want); if(!c) return 'no card '+want; c.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,700)); [...c.querySelectorAll('button')].find(x=>x.textContent.trim()=='Buy').click(); await new Promise(r=>setTimeout(r,2200)); return 'bought '+want"
