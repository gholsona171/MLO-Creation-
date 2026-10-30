"""FILMING AID ONLY (never shipped, never a lock): open or close every jc_jail door on client 1 for a fly-through, so the camera never
passes through a closed leaf (playbook: no camera through a closed door). Doors are added to the client's DoorSystem under hashes of
our own and opened by ratio; 'close' drives every one of them shut (ratio 0, briefly locked so it swings home), removes them from the
door system (the map default applies: plain native doors) and then checks every door OBJECT physically: heading within 3 deg and
position within 0.15 m of its placement. The roll-up too.
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
doors = [(d['model'], *F.W(d['pos'][0], d['pos'][1]), d['pos'][2], (d['heading'] + F.HDEG) % 360.0) for d in L['doors']]
s0, s1 = J.SALLY['s']; x, y = F.W(J.JBOX[0] + 0.275, (s0 + s1) / 2); doors.append((J.ROLLUP[0], x, y, J.SALLY_Z + J.ROLLUP[2] / 2, (90.0 + F.HDEG) % 360.0))
mode = sys.argv[1]; assert mode in ('open', 'close'), 'usage: jj_doorctl.py open|close'
items = ','.join('{"%s",%.3f,%.3f,%.3f,%.2f}' % d for d in doors)
# the PHYSICAL check (2026-10-29: DoorSystemGetOpenRatio read 1.0 for 50 doors after a close - it reports the system's target, not the
# leaf): find each door object at its spot and compare its heading and position with the door's own placement (closed = within 3 deg
# and 0.15 m). Returns how many are found / not closed.
phys = ('local function shut() local found,openn=0,0 for i,d in ipairs(D) do local o=GetClosestObjectOfType(d[2],d[3],d[4],1.6,GetHashKey(d[1]),false,false,false) '
        'if o~=0 then found=found+1 local dh=math.abs(((GetEntityHeading(o)-d[5])+540.0)%360.0-180.0) local dp=#(GetEntityCoords(o)-vector3(d[2],d[3],d[4])) '
        'if dh>3.0 or dp>0.15 then openn=openn+1 end end end return found,openn end ')
reg = ('local D={%s} local H={} for i,d in ipairs(D) do H[i]=GetHashKey("jjfilm_"..i) end ' % items) + phys
if mode == 'open':
    code = (reg + 'for i,d in ipairs(D) do if not IsDoorRegisteredWithSystem(H[i]) then AddDoorToSystem(H[i],GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end '
            'DoorSystemSetDoorState(H[i],0,false,true) DoorSystemSetOpenRatio(H[i],1.0,false,true) DoorSystemSetHoldOpen(H[i],true) end Wait(3000) '
            'local f,o=shut() return tostring(#D)..":"..tostring(f)..":"..tostring(#D-o)')        # n : found : still shut (after opening: should be 0)
else:
    # reset: drive every door shut (ratio 0, locked, forced), wait, take every one OUT of the door system (the map default applies:
    # a plain native door), wait, then the physical read-back
    code = (reg + 'for i,d in ipairs(D) do if not IsDoorRegisteredWithSystem(H[i]) then AddDoorToSystem(H[i],GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end '
            'DoorSystemSetHoldOpen(H[i],false) DoorSystemSetOpenRatio(H[i],0.0,false,true) DoorSystemSetDoorState(H[i],1,false,true) end Wait(4000) '
            'for i=1,#D do DoorSystemSetDoorState(H[i],0,false,true) RemoveDoorFromSystem(H[i]) end Wait(1500) '
            'local f,o=shut() return tostring(#D)..":"..tostring(f)..":"..tostring(o)')                # n : found : NOT shut (should be 0)
if '--dry' in sys.argv: print(code); sys.exit(0)                                # the Lua only (offline syntax check: jj_luacheck.py)
r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 40', code], capture_output=True, text=True, timeout=100)
m = re.search(r'"result":"(\d+):(\d+):(\d+)"', r.stdout)
if not m: print('DOORCTL_FAIL no answer from the rig: ' + (r.stdout + r.stderr)[-300:]); sys.exit(1)
n, found, x = map(int, m.groups())
if found != len(doors): print(f'DOORCTL_FAIL {mode}: only {found} of {len(doors)} door objects found at their spots (stream them in first)'); sys.exit(1)
if mode == 'close' and x: print(f'DOORCTL_FAIL close: {x} of {len(doors)} doors not shut (physical check: heading / position vs placement)'); sys.exit(1)
if mode == 'open' and x: print(f'DOORCTL_WARN open: {x} of {len(doors)} doors did not swing open'); sys.exit(0)
print(f'DOORCTL_OK {mode} {n} doors' + (' (all shut, physical check)' if mode == 'close' else ' (all open)'))
