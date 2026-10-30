"""FILMING AID ONLY (never shipped, never a lock): open or close every jc_jail door on client 1 for a fly-through, so the camera never
passes through a closed leaf (playbook: no camera through a closed door). Doors are added to the client's DoorSystem under hashes of
our own and opened by ratio; 'close' drives every one of them shut (ratio 0, briefly locked so it swings home), waits, reads each door's
ratio back, and only then removes them (the doors fall back to plain native doors). The roll-up too.
'close' is ALWAYS safe to run (also when nothing was opened: it registers, closes and removes) - jj_rig_tests.sh runs it in a trap after
the fly and before the pairs shots (2026-10-29: a fly that failed before its close left the roll-up open in the pair shots).
Run: py -3 jj_doorctl.py open|close   ->  DOORCTL_OK <mode> <n> | DOORCTL_FAIL ... (exit 1)"""
import json, re, subprocess, sys
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')
import jj_plan as J, jc_frame as F
GB = r'C:\Program Files\Git\bin\bash.exe'
L = json.load(open(JL / OD / 'jj_layout.json'))
doors = [(d['model'], *F.W(d['pos'][0], d['pos'][1]), d['pos'][2]) for d in L['doors']]
s0, s1 = J.SALLY['s']; x, y = F.W(J.JBOX[0] + 0.275, (s0 + s1) / 2); doors.append((J.ROLLUP[0], x, y, J.SALLY_Z + J.ROLLUP[2] / 2))
mode = sys.argv[1]; assert mode in ('open', 'close'), 'usage: jj_doorctl.py open|close'
items = ','.join('{"%s",%.3f,%.3f,%.3f}' % d for d in doors)
reg = 'local D={%s} local H={} for i,d in ipairs(D) do H[i]=GetHashKey("jjfilm_"..i) if not IsDoorRegisteredWithSystem(H[i]) then AddDoorToSystem(H[i],GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end end ' % items
if mode == 'open':
    code = reg + 'for _,h in ipairs(H) do DoorSystemSetDoorState(h,0,false,false) DoorSystemSetOpenRatio(h,1.0,false,false) DoorSystemSetHoldOpen(h,true) end return tostring(#H)..":0"'
else:
    code = (reg + 'for _,h in ipairs(H) do DoorSystemSetHoldOpen(h,false) DoorSystemSetOpenRatio(h,0.0,false,false) DoorSystemSetDoorState(h,1,false,true) end '
            'Wait(5000) local open=0 for _,h in ipairs(H) do if math.abs(DoorSystemGetOpenRatio(h)) > 0.05 then open=open+1 end end '
            'for _,h in ipairs(H) do DoorSystemSetDoorState(h,0,false,false) RemoveDoorFromSystem(h) end return tostring(#H)..":"..tostring(open)')
r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 40', code], capture_output=True, text=True, timeout=100)
m = re.search(r'"result":"(\d+):(\d+)"', r.stdout)
if not m: print('DOORCTL_FAIL no answer from the rig: ' + (r.stdout + r.stderr)[-300:]); sys.exit(1)
n, still_open = int(m.group(1)), int(m.group(2))
if n != len(doors) or still_open: print(f'DOORCTL_FAIL {mode}: {n} of {len(doors)} doors handled, {still_open} still open'); sys.exit(1)
print(f'DOORCTL_OK {mode} {n} doors' + (' (all shut)' if mode == 'close' else ''))
