"""FILMING AID ONLY (never shipped, never a lock): open or close every jc_jail door on client 1 for a fly-through, so the camera never
passes through a closed leaf (playbook: no camera through a closed door). Doors are added to the client's DoorSystem under hashes of
our own. The roll-up too.
Every read is PHYSICAL (2026-10-29: DoorSystemGetOpenRatio read 1.0 for 50 doors after a close - it reports the system's target, not the
leaf): each door object is found at its spot and its heading / position compared with the door's own placement (shut = within 3 deg
and 0.15 m).
'open': unlocked, ratio 1, held open; polled every 0.5 s until every leaf has left its shut position (at most 15 s).
'close': held shut by the door system (ratio 0, LOCKED) and polled every 0.5 s - the doors not yet shut are driven again - until every
leaf is physically shut (at most 30 s); only then released to the map default (unlocked, out of the door system) and read again after
2 s (rig 2026-10-30: the old close waited a fixed 4 s and released, and a leaf still swinging stopped where it was - a released map door
has no spring: 50 of 51 left open after the fly, 14 after a second close). Reports the time it took and which doors are not shut.
'hold': as 'close' but the doors stay LOCKED shut in the door system (for photos: the roll-up is a map garage door that opens by itself
as soon as the player is near - the 23:00 pair shots of 2026-10-29 show it open); 'release' hands every door back to the map default.
'close' is ALWAYS safe to run (also when nothing was opened) - jj_rig_tests.sh runs it in a trap after the fly; the pairs step runs
'hold' before its shots and 'release' in its exit trap.
Run: py -3 jj_doorctl.py open|close|hold|release   ->  DOORCTL_OK <mode> <n> ... | DOORCTL_FAIL ... (exit 1)"""
import json, re, subprocess, sys
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')
import jj_plan as J, jc_frame as F
GB = r'C:\Program Files\Git\bin\bash.exe'
L = json.load(open(JL / OD / 'jj_layout.json'))
doors = [(d['model'], *F.W(d['pos'][0], d['pos'][1]), d['pos'][2], (d['heading'] + F.HDEG) % 360.0) for d in L['doors']]
names = [d['name'] for d in L['doors']]
s0, s1 = J.SALLY['s']; x, y = F.W(J.JBOX[0] + 0.275, (s0 + s1) / 2); doors.append((J.ROLLUP[0], x, y, J.SALLY_Z + J.ROLLUP[2] / 2, (90.0 + F.HDEG) % 360.0)); names.append('rollup')
def code(mode):
    """the Lua for 'open' / 'close' (jj_luasim.py executes it offline). Returns n:found:bad:ms:list - bad = doors not shut ('close') or
    still shut ('open'), ms = how long the poll took, list = the first eight bad doors' indexes."""
    items = ','.join('{"%s",%.3f,%.3f,%.3f,%.2f}' % d for d in doors)
    lua = ('local D={%s} local H={} for i,d in ipairs(D) do H[i]=GetHashKey("jjfilm_"..i) end '
           'local function obj(d) return GetClosestObjectOfType(d[2],d[3],d[4],1.6,GetHashKey(d[1]),false,false,false) end '
           'local function isshut(d) local o=obj(d) if o==0 then return nil end local dh=math.abs(math.fmod((GetEntityHeading(o)-d[5])+540.0,360.0)-180.0) '
           'return dh<=3.0 and #(GetEntityCoords(o)-vector3(d[2],d[3],d[4]))<=0.15 end '
           'local function read(want) local found,bad,list=0,0,{} for i,d in ipairs(D) do local s=isshut(d) if s~=nil then found=found+1 '
           'if s~=want then bad=bad+1 if #list<8 then list[#list+1]=tostring(i) end end end end return found,bad,list end '
           'local function reg(i,d) if not IsDoorRegisteredWithSystem(H[i]) then AddDoorToSystem(H[i],GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end end '
           'local function drive(i,d,open) reg(i,d) if open then DoorSystemSetDoorState(H[i],0,false,true) DoorSystemSetOpenRatio(H[i],1.0,false,true) DoorSystemSetHoldOpen(H[i],true) '
           'else DoorSystemSetHoldOpen(H[i],false) DoorSystemSetOpenRatio(H[i],0.0,false,true) DoorSystemSetDoorState(H[i],1,false,true) end end ') % items
    if mode == 'open':
        lua += ('for i,d in ipairs(D) do drive(i,d,true) end local t0=GetGameTimer() local f,b,l=read(false) '
                'while b>0 and GetGameTimer()-t0<15000 do Wait(500) f,b,l=read(false) end '
                'return tostring(#D)..":"..tostring(f)..":"..tostring(b)..":"..tostring(GetGameTimer()-t0)..":"..table.concat(l,",")')
    elif mode == 'release':
        lua += ('local f=0 for i,d in ipairs(D) do if IsDoorRegisteredWithSystem(H[i]) then DoorSystemSetDoorState(H[i],0,false,true) RemoveDoorFromSystem(H[i]) end '
                'if obj(d)~=0 then f=f+1 end end return tostring(#D)..":"..tostring(f)..":0:0:"')
    else:                                                                       # close / hold: held shut and polled until every leaf is shut
        lua += ('for i,d in ipairs(D) do drive(i,d,false) end local t0=GetGameTimer() local f,b,l=read(true) '
                'while b>0 and GetGameTimer()-t0<30000 do Wait(500) for i,d in ipairs(D) do if isshut(d)==false then drive(i,d,false) end end f,b,l=read(true) end '
                'local ms=GetGameTimer()-t0 ')
        if mode == 'close':                                                     # released only once every leaf is shut, then read again
            lua += 'if b==0 then for i=1,#D do DoorSystemSetDoorState(H[i],0,false,true) RemoveDoorFromSystem(H[i]) end Wait(2000) f,b,l=read(true) end '
        lua += 'return tostring(#D)..":"..tostring(f)..":"..tostring(b)..":"..tostring(ms)..":"..table.concat(l,",")'
    return lua
def verdict(mode, res):
    """(ok, line) from the Lua's answer."""
    m = re.search(r'(\d+):(\d+):(\d+):(\d+):([\d,]*)', res or '')
    if not m: return False, 'DOORCTL_FAIL no answer from the rig: ' + (res or '')[-300:]
    n, found, bad, ms = map(int, m.groups()[:4]); which = [names[int(i) - 1] for i in m.group(5).split(',') if i]
    if found != len(doors): return False, f'DOORCTL_FAIL {mode}: only {found} of {len(doors)} door objects found at their spots (stream them in first)'
    if mode in ('close', 'hold') and bad: return False, f'DOORCTL_FAIL {mode}: {bad} of {n} doors not shut after {ms / 1000:.1f} s (physical check), e.g. {which}'
    if mode == 'release': return True, f'DOORCTL_OK release {n} doors (back to the map default)'
    if mode == 'hold': return True, f'DOORCTL_OK hold {n} doors (all shut by physical check in {ms / 1000:.1f} s, held LOCKED shut: run release after)'
    if mode == 'open' and bad: return True, f'DOORCTL_WARN open: {bad} of {n} doors did not swing open in {ms / 1000:.1f} s, e.g. {which}'
    return True, f'DOORCTL_OK {mode} {n} doors' + (f' (all shut by physical check, settled in {ms / 1000:.1f} s, released to the map default and still shut 2 s later)' if mode == 'close' else f' (all open in {ms / 1000:.1f} s)')
if __name__ == '__main__':
    mode = sys.argv[1]; assert mode in ('open', 'close', 'hold', 'release'), 'usage: jj_doorctl.py open|close|hold|release'
    lua = code(mode)
    if '--dry' in sys.argv: print(lua); sys.exit(0)                             # the Lua only
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 60', lua], capture_output=True, text=True, timeout=120)
    m = re.search(r'"result":"([^"]*)"', r.stdout)
    ok, line = verdict(mode, m.group(1) if m else r.stdout + r.stderr); print(line); sys.exit(0 if ok else 1)
