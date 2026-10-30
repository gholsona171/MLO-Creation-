#!/bin/bash
# tc_glow_shots.sh <tag> <hour> [set]: Tower City night-glow check (vertex colour G = artificial ambient, 2026-10-29) at a held hour
#   -> shots/towercity/glow/<tag>_<hour>/ : the 6 standard tc_views exteriors (vanilla neighbours in frame), 500 m + 1 km distance
#   views (LOD / far streaming), and 3 interiors (mall court, tower lobby, casino). set: all (default) | ext | far | int
cd /c/C9Test; trap 'bash /c/C9Test/tc_release.sh' EXIT
T=$1; H=${2:-23}; S=${3:-all}; D=shots/towercity/glow/${T}_$H; mkdir -p $D
./t.sh cl 1 "_G.__hh=$H if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(_G.__hh,0,0) Wait(0) end end) end return 'hold'" 5 >/dev/null
export HOUR=$H
if [ $S = all ] || [ $S = ext ]; then
bash tcshot.sh $D/1_aerial_south.png    30 -1040 210    10 -860 30 60 9
bash tcshot.sh $D/2_east_from_legion.png 185 -925 55    75 -880 31 60 8
bash tcshot.sh $D/3_west_from_south.png  -55 -990 70   -75 -825 36 60 8
bash tcshot.sh $D/4_west_ne_corner.png   35 -770 70    -40 -815 35 60 8
bash tcshot.sh $D/5_east_lane_street.png 25 -965 33    75 -845 31 60 8
bash tcshot.sh $D/6_aerial_top.png      -20 -880 330   -18 -860 30 65 9
fi
if [ $S = all ] || [ $S = far ]; then
bash tcshot.sh $D/7_far_500m.png   171 -1260 150   -40 -840 110 50 12
bash tcshot.sh $D/8_far_1km.png    421 -1693 250   -40 -840 120 40 14
bash tcshot.sh $D/9_far_500m_n.png -79  -327 160   -40 -840 110 50 12
fi
if [ $S = all ] || [ $S = int ]; then
OX=71.0 OY=-884.0 WAIT=9 bash tc_tviews.sh glow/${T}_$H/int "mall_court 11.5 0 30.9 70 0 40"
OX=-78.897 OY=-827.328 WAIT=9 bash tc_tviews.sh glow/${T}_$H/int "tower_lobby 0 -40 32.9 0 -10 32.0" "casino 0 0 25.1 15 10 24.0"
fi
echo done $D
