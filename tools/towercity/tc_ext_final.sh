#!/bin/bash
# tc_ext_final.sh <tag> [set]: the last four exterior items (2026-10-24) from fixed cameras (tower lot frame, tcx.sh) -> shots/towercity/ext/<tag>/
#   i1  the planter island's overhang past the deck edge (from the parking drive under it, from the north, on the deck)
#   i2  the asphalt wedge at the new kerb's north end (on the deck, from above)
#   i3  the dark wedges east of the portico (the PARKING block's ledge left over) + the portico's east end
#   i4  the driveway pillar from far away (its LOD / SLOD1 drawn), old spot v -21.3 / new spot v -9.0
# set: all (default) | i1 | i2 | i3 | i4. Holds the clock at 13:00 for the whole run.
cd /c/C9Test; T=${1:-final}; S=${2:-all}; D=shots/towercity/ext/$T; mkdir -p $D
./t.sh cl 1 "if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(13,0,0) Wait(0) end end) end return 'hold'" 5 >/dev/null
if [ $S = all ] || [ $S = i1 ]; then
bash tcx.sh $D/i1_under.png 69.5 -46 32.6 72.5 -33 43 70 8
bash tcx.sh $D/i1_north.png 69.5 -14 33 72 -34 43 70 5
bash tcx.sh $D/i1_deckn.png 75.5 -44 45.2 74 -25 43.5 70 5
bash tcx.sh $D/i1_deckn2.png 77 -20 45.2 73.5 -36 43.5 70 5
fi
if [ $S = all ] || [ $S = i2 ]; then
bash tcx.sh $D/i2_deck.png 82 -45 45.5 77.5 -34 43.2 70 6
bash tcx.sh $D/i2_top.png 76.5 -38 58 77.0 -35.5 43 60 5
fi
if [ $S = all ] || [ $S = i3 ]; then
bash tcx.sh $D/g1.png 20 -76 33 20 -58 33 70 6
bash tcx.sh $D/i3_w1.png 26 -70 36 30 -58.5 41 50 5
bash tcx.sh $D/i3_w2.png 40 -66 37 29 -58.5 41 50 5
bash tcx.sh $D/i3_side.png 34 -62 40 22 -60.5 43 60 5
fi
if [ $S = all ] || [ $S = i4 ]; then
# the same camera 24 m east of the column line, three ways: HD (normal), the LOD forced (lod scale 0.08: fwy02's HD fades at 12 m, its
# LOD 'hash_d50b466a' draws to 32 m) and the SLOD1 forced (scale 0.04: the LOD fades at 16 m, 'dt1_rd1_r1f_slod1' draws to 40 m) -
# what a player sees of the deck from ~150-400 m and from 400 m+. OverrideLodscaleThisFrame runs every frame in a thread.
lods() { ./t.sh cl 1 "_G.__lods=$1 if not _G.__lodt then _G.__lodt=true CreateThread(function() while _G.__lodt do if _G.__lods then OverrideLodscaleThisFrame(_G.__lods) end Wait(0) end end) end return 'lods'" 5 >/dev/null; }
lods nil;  bash tcx.sh $D/i4_hd.png 100 -15 34 75.9 -15 37 60 8
lods 0.08; bash tcx.sh $D/i4_lod.png 100 -15 34 75.9 -15 37 60 8
lods 0.04; bash tcx.sh $D/i4_slod.png 100 -15 34 75.9 -15 37 60 8
lods nil
fi
bash tcshot_off.sh >/dev/null 2>&1; echo done $D
