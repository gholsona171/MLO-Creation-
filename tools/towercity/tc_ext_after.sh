#!/bin/bash
# tc_ext_after.sh <tag>: the exterior review's viewpoints (same cameras as the 'before' shots in shots/towercity/ext)
cd /c/C9Test; T=${1:-after}; D=shots/towercity/ext/$T; mkdir -p $D
./t.sh cl 1 "if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(13,0,0) Wait(0) end end) end return 'hold'" 5 >/dev/null
HOUR=13 bash tcshot.sh $D/b1_nw_far.png -380 -520 260 -10 -860 60 50 14
HOUR=13 bash tcshot.sh $D/b1_nw_mid.png -250 -650 180 -10 -860 50 50 8
HOUR=13 bash tcshot.sh $D/b1_nw_lo.png -300 -600 120 0 -850 60 45 8
HOUR=13 bash tcshot.sh $D/b1_n.png 60 -600 160 60 -850 140 50 8
bash tcx.sh $D/g1.png 20 -76 33 20 -58 33 70 8
bash tcx.sh $D/g2.png 10 -98 32 10 -60 31 70 5
bash tcx.sh $D/g3.png -20 -90 33 30 -70 31 70 5
bash tcx.sh $D/g4.png 60 -95 33 30 -70 31 70 5
bash tcx.sh $D/f_20.png 20 -100 40 20 -60 33 60 5
bash tcx.sh $D/k1.png 80 -10 46 72 -45 43 70 6
bash tcx.sh $D/k2.png 82 -70 46 72 -35 43 70 5
bash tcx.sh $D/k3.png 85 -40 46 66 -40 40 70 5
bash tcx.sh $D/s1.png 100 -40 47 66 -45 42 70 5
bash tcx.sh $D/s3.png 100 -20 37 70 -40 36 70 5
bash tcx.sh $D/s4.png 72 -10 34 72 -50 34 75 5
bash tcx.sh $D/e4.png 85 -25 33 66 -24 33 75 5
bash tcx.sh $D/p1.png 50 -105 34 72 -45 40 70 5
bash tcx.sh $D/p3.png 72 -20 36 72 -55 40 75 5
bash tcx.sh $D/o2.png 10 -65 95 10 -64.9 30 80 6
bash tcx.sh $D/t1.png 85 -45 110 85 -44.9 30 75 6
bash tcx.sh $D/a5.png -40 66 31.5 -40 56 30.6 60 6
bash tcx.sh $D/a6.png -82 -20 31.5 -73 -20 30.4 60 5
bash tcx.sh $D/a7.png -60 70 34 -60 58 30 50 5
bash tcx.sh $D/a8.png -86 30 33 -74 30 30 50 5
bash tcx.sh $D/a3.png -88 70 32 -72 55 30 70 5
bash tcshot_off.sh >/dev/null 2>&1; echo done $D
