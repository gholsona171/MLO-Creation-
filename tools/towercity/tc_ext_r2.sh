#!/bin/bash
# tc_ext_r2.sh <tag> [set]: Antonio's exterior shots 71-81 (2026-10-24) re-taken from approximately his cameras (tower lot frame, tcx.sh),
# plus the sidewalk faces round both lots (top-down + street level) -> shots/towercity/ext/<tag>/. Sets: ant | walk | all (default).
# Always gives client 1 back (tc_release.sh) - Antonio plays on it.
cd /c/C9Test; trap 'bash /c/C9Test/tc_release.sh >/dev/null' EXIT
T=${1:-r2}; S=${2:-all}; D=shots/towercity/ext/$T; mkdir -p $D
./t.sh cl 1 "if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(13,0,0) Wait(0) end end) end return 'hold'" 5 >/dev/null
if [ $S = all ] || [ $S = ant ]; then
bash tcx.sh $D/s71.png 79 -32 50 74 -10 42 60 8          # deck west side from above (dark patches, red kerb)
bash tcx.sh $D/s72.png 78 -30 46.5 72 10 40 60 5         # along San Andreas from the island
bash tcx.sh $D/s73.png -95 75 60 -70 50 35 70 5          # Alta / Vespucci corner of the podium
bash tcx.sh $D/s74.png 62 100 68 30 72 43 60 5            # the footbridge
bash tcx.sh $D/s75.png 85 35 60 72 45 42 60 5            # the lane / arrow slab off the deck
bash tcx.sh $D/s76.png -25 -70 33.5 -25 -62 30 70 5      # the Power St lawn by the podium
bash tcx.sh $D/s77.png 20 -71 31.8 40 -68 30.3 70 5      # the plaza: hedge planter
bash tcx.sh $D/s78.png 10 -66 32 30 -75 30 70 5          # the plaza looking SE
bash tcx.sh $D/s79.png 45 -72 31.8 25 -66 31 70 5        # under the freeway looking W
bash tcx.sh $D/s80.png 3 -66 33.5 3.5 -63 29.4 70 5      # between the planter and the steps (the hole)
bash tcx.sh $D/s81.png -28 -72 33 -40 -64 29.2 70 5      # Power St sidewalk by the low planter wall
fi
if [ $S = all ] || [ $S = walk ]; then
for spec in "pw_top 0 -64 70 0.01 -64 29 70" "pw_st -40 -78 31 0 -64 29.5 70" "sa_top 76 0 75 76.01 0 31 70" "sa_st 82 -10 33 70 10 31.5 70" \
            "al_top 0 60 75 0.01 60 30 70" "al_st -40 66 31 0 56 29.5 70" "ve_top -78 0 75 -78.01 0 28 70" "ve_st -88 -30 30 -76 0 28.5 70" \
            "ea_n_top 0 -108 75 0.01 -108 29 70" "ea_w_top -78 -160 75 -78.01 -160 28.5 70" "ea_s_top 0 -213 75 0.01 -213 30 70" "ea_e_top 78 -160 75 78.01 -160 30.5 70"; do
  set -- $spec; bash tcx.sh $D/$1.png $2 $3 $4 $5 $6 $7 $8 5
done
fi
echo done $D
