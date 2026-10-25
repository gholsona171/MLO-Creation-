#!/bin/bash
# tc_release.sh: give client 1 back to the player after any shot / probe run (Antonio plays on the rig): the scripted camera off
# (tcshot_off.sh), and every _G thread a shot run starts stopped (__hold clock hold, __lodt / __lods LOD-scale override).
# Use it as a trap in every shot script:  trap 'bash /c/C9Test/tc_release.sh' EXIT
cd /c/C9Test
./t.sh cl 1 "_G.__hold=false _G.__lodt=false _G.__lods=nil local p=PlayerPedId() FreezeEntityPosition(p,false) SetEntityVisible(p,true) SetEntityCollision(p,true,true) return 'released'" 5 | grep -o '"result":"[^"]*"'
bash tcshot_off.sh
