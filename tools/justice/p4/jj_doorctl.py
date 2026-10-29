"""FILMING AID ONLY (never shipped, never a lock): open or close every jc_jail door on client 1 for a fly-through, so the camera never
passes through a closed leaf (playbook: no camera through a closed door). Doors are added to the client's DoorSystem under hashes of
our own, opened by ratio, and removed again with 'close' (the doors then fall back to plain native doors). The roll-up too.
Run: py -3 jj_doorctl.py open|close"""
import json, math, re, subprocess, sys
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')
import jj_plan as J, jc_frame as F
GB = r'C:\Program Files\Git\bin\bash.exe'
L = json.load(open(JL / OD / 'jj_layout.json'))
doors = [(d['model'], *F.W(d['pos'][0], d['pos'][1]), d['pos'][2]) for d in L['doors']]
s0, s1 = J.SALLY['s']; x, y = F.W(J.JBOX[0] + 0.275, (s0 + s1) / 2); doors.append((J.ROLLUP[0], x, y, J.SALLY_Z + J.ROLLUP[2] / 2))
for t in L.get('lifts', []):
    pass
mode = sys.argv[1]
items = ','.join('{"%s",%.3f,%.3f,%.3f}' % d for d in doors)
code = ('local D={%s} local n=0 for i,d in ipairs(D) do local h=GetHashKey("jjfilm_"..i) '
        'if "%s"=="open" then if not IsDoorRegisteredWithSystem(h) then AddDoorToSystem(h,GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end '
        'DoorSystemSetDoorState(h,0,false,false) DoorSystemSetOpenRatio(h,1.0,false,false) DoorSystemSetHoldOpen(h,true) n=n+1 '
        'else if IsDoorRegisteredWithSystem(h) then DoorSystemSetHoldOpen(h,false) DoorSystemSetOpenRatio(h,0.0,false,false) RemoveDoorFromSystem(h) n=n+1 end end end '
        'return tostring(n)') % (items, mode)
r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 30', code], capture_output=True, text=True, timeout=90)
m = re.search(r'"result":"(.*?)"', r.stdout)
if not m: raise SystemExit('DOORCTL: no answer from the rig: ' + (r.stdout + r.stderr)[-300:])
print('DOORCTL', mode, m.group(1), 'of', len(doors))
