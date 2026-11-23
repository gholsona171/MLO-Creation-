#!/bin/bash
# rig_swap.sh in|out : put graveyard_towyard on the rig in place of Cleveland's rocky_shop8_junkyard (in), or put the rig back (out).
# The game client is closed first: stopping a map resource under a connected player crashes the client. Take the rig lock first.
cd /c/C9Test
R="live/resources/[localtest]"
powershell -NoProfile -Command "Get-Process | ? { \$_.Name -like 'FiveM*' -or \$_.Name -like 'GTA*' } | Stop-Process -Force" ; sleep 5
if [ "$1" = "in" ]; then
  bash t.sh con "stop rocky_shop8_junkyard" >/dev/null; rm -rf "$R/graveyard_towyard"
  cp -r /c/Users/anton/Documents/Codex/graveyard_towyard/resource/graveyard_towyard "$R/"
  bash t.sh con "refresh" >/dev/null; bash t.sh con "ensure graveyard_towyard" >/dev/null; echo "RIG_SWAP in"
else
  bash t.sh con "stop graveyard_towyard" >/dev/null; rm -rf "$R/graveyard_towyard"
  bash t.sh con "refresh" >/dev/null; bash t.sh con "ensure rocky_shop8_junkyard" >/dev/null; echo "RIG_SWAP out"
fi
