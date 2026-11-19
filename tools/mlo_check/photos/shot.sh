#!/bin/bash
# shot.sh <outname> '<lua that calls MS.cam(...) and returns a string>' [settle seconds]
cd /c/C9Test
H=$(cat /c/C9Test/shots/mlo/helper.lua)
./t.sh cl ${PL:-2} "$H
$2" 40 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${3:-4}
powershell -NoProfile -ExecutionPolicy Bypass -File winshot.ps1 -Proc FiveM_b3258_GTAProcess -Out "C:/C9Test/shots/mlo/$1.png" 2>&1 | tail -1
