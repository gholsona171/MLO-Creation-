"""Area 2 sit photos (the visual half of the sit test: on the seat, not in it): clones of the player take their seat's scenario at the
sit point - every courtroom 3A chair (jury, judge, witness, clerk, counsel), a gallery pew row, the holding cell bench + the officer's
chair, the lobby / corridor benches, the jury-room chairs - then cameras 2.2 m in front of each group and the courtroom overviews.
Run: py -3 jc3_sitshots.py <out dir>   (rig: tc_release.sh runs at the end)"""
import json, math, sys, time, subprocess
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc3_probe as P, jc_frame as F
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
L = json.load(open(P3 / 'out/jc3_layout.json')); S = L['seats']
def group(room, sc): return [i for i, s in enumerate(S) if s[4:6] == [room, sc]]
chairs = group('crtA', 'PROP_HUMAN_SEAT_CHAIR'); pews = group('crtA', 'PROP_HUMAN_SEAT_BENCH')
picks = chairs + pews[:11] + pews[33:36] + group('secA', 'PROP_HUMAN_SEAT_BENCH')[:2] + group('secA', 'PROP_HUMAN_SEAT_CHAIR') \
        + group('tlobby', 'PROP_HUMAN_SEAT_BENCH')[:3] + group('tlobby', 'PROP_HUMAN_SEAT_CHAIR')[:1] + group('pubA', 'PROP_HUMAN_SEAT_BENCH')[:3] \
        + group('pubA', 'PROP_HUMAN_SEAT_CHAIR')[:2] + group('rstA', 'PROP_HUMAN_SEAT_CHAIR')
P.revive(); P.stand(15.0, 2.0, 28.8); time.sleep(2)
P.lua('_G.__sitters=_G.__sitters or {} for _,c in ipairs(_G.__sitters) do DeleteEntity(c) end _G.__sitters={} return "clear"', 20)
for b in range(0, len(picks), 8):                       # 8 clones per call (a long chunk is cut short by the rig's command channel)
    code = 'local P0=PlayerPedId() '
    for i in picks[b:b + 8]:
        u, v, z, h, room, sc = S[i][:6]; x, y = F.W(u, v)
        code += ('do local c=ClonePed(P0,false,false,true) SetEntityCoords(c,%.3f,%.3f,%.3f) TaskStartScenarioAtPosition(c,"%s",%.3f,%.3f,%.3f,%.1f,0,true,true) '
                 '_G.__sitters[#_G.__sitters+1]=c end ' % (x, y, z + 0.5, sc, x, y, z, (h + F.HDEG) % 360))
    P.lua(code + 'return "ok"', 30)
r = P.lua('Wait(5000) local n=0 for _,c in ipairs(_G.__sitters) do if IsPedUsingAnyScenario(c) then n=n+1 end end return tostring(#_G.__sitters)..":"..tostring(n)', 30)
print('SITTERS placed:using =', r, 'of', len(picks))
cams = [l.split() for l in open(P3 / 'cams_area2.txt') if l.startswith(('p3_a2_courtroom_gallery', 'p3_a2_courtroom_bench', 'p3_a2_courtroom_jury', 'p3_a2_holding'))]
seen = set()
for i in picks:                                          # one close camera per (room, scenario, facing) group
    u, v, z, h, room, sc = S[i][:6]; k = (room, sc, h)
    if k in seen: continue
    seen.add(k); hr = math.radians(h); fu, fv = -math.sin(hr), math.cos(hr)
    cu, cv = u + fu * 2.2 + fv * 0.8, v + fv * 2.2 - fu * 0.8; x, y = F.W(cu, cv); tx, ty = F.W(u, v)
    cams.append([f'sit_{room}_{i}', f'{x:.2f}', f'{y:.2f}', f'{z + 0.75:.2f}', f'{tx:.2f}', f'{ty:.2f}', f'{z + 0.15:.2f}', '50'])
try:
    for n, x, y, z, tx, ty, tz, f in cams:
        subprocess.run([P.GB, '-c', f'HOUR=13 bash /c/C9Test/tcshot.sh {OUT.as_posix()}/{n}.png {x} {y} {z} {tx} {ty} {tz} {f} 4'], capture_output=True, timeout=120)
finally:
    P.lua('for _,c in ipairs(_G.__sitters or {}) do DeleteEntity(c) end _G.__sitters={} return "gone"', 20)
    subprocess.run([P.GB, '-c', 'bash /c/C9Test/tc_release.sh'], capture_output=True, timeout=60)
print('SITSHOTS', len(cams), sorted(p.name for p in OUT.glob('*.png')))
