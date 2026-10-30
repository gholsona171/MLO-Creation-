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
'debug' (read only, rig 2026-10-30: close / hold left the same 14 doors 'not shut' every time): per door the object found at its spot,
whether its model is the door's, its coords and heading against the placement (dh, dp), the distance from the object to the nearest
OTHER placement of the same model (a lookup that picked a neighbour shows here), frozen, and the door-system state; writes
<out>/doordebug.json and photographs every door that is not shut (camera 2.2 m in front of the leaf's middle, both sides) into
shots/p4_jail_doordebug/.
Run: py -3 jj_doorctl.py open|close|hold|release|debug   ->  DOORCTL_OK <mode> <n> ... | DOORCTL_FAIL ... (exit 1)"""
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
CX, CY, CZ = (sum(d[k] for d in doors) / len(doors) for k in (1, 2, 3))           # the jail's doors' centre: the streaming focus
BX, BY = F.W(-20.0, 9.0); BZ = J.G + 1.0                                           # the player's stand while the doors are worked: booking
def code(mode):
    """the Lua for every mode (jj_luasim.py executes it offline). Each run first STREAMS the jail in (rig 2026-10-30, after a restart:
    0 of 51 door objects found - the player was far away): the player stands in booking (frozen) and the focus sits on the doors'
    centre until all 51 objects are found (at most 20 s); at the end the focus is cleared and the player put back.
    close / hold (rig 2026-10-30: 14 doors LOCKED part-open at ~10 / 30 / 46 deg - a locked door-system door freezes where it is, so
    driving ratio 0 after locking can never bring it home): every door UNLOCKED, not held, ratio 0 (forced), polled physically every
    0.5 s and driven again; a door still open after 8 s is nudged (its heading set to the placement, unlocked) - then 'hold' LOCKS them
    (only once every leaf is shut) and 'close' releases them to the map default; both read again after.
    Returns n:found:bad:ms:list:stream_ms:nudges (debug: the per-door records)."""
    items = ','.join('{"%s",%.3f,%.3f,%.3f,%.2f}' % d for d in doors)
    lua = ('local D={%s} local H={} for i,d in ipairs(D) do H[i]=GetHashKey("jjfilm_"..i) end '
           'local function obj(d) return GetClosestObjectOfType(d[2],d[3],d[4],1.6,GetHashKey(d[1]),false,false,false) end '
           'local function isshut(d) local o=obj(d) if o==0 then return nil end local dh=math.abs(math.fmod((GetEntityHeading(o)-d[5])+540.0,360.0)-180.0) '
           'return dh<=3.0 and #(GetEntityCoords(o)-vector3(d[2],d[3],d[4]))<=0.15 end '
           'local function read(want) local found,bad,list=0,0,{} for i,d in ipairs(D) do local s=isshut(d) if s~=nil then found=found+1 '
           'if s~=want then bad=bad+1 if #list<8 then list[#list+1]=tostring(i) end end end end return found,bad,list end '
           'local function reg(i,d) if not IsDoorRegisteredWithSystem(H[i]) then AddDoorToSystem(H[i],GetHashKey(d[1]),d[2],d[3],d[4],false,false,false) end end '
           'local function opendoor(i,d) reg(i,d) DoorSystemSetDoorState(H[i],0,false,true) DoorSystemSetOpenRatio(H[i],1.0,false,true) DoorSystemSetHoldOpen(H[i],true) end '
           'local function shutdoor(i,d) reg(i,d) DoorSystemSetHoldOpen(H[i],false) DoorSystemSetDoorState(H[i],0,false,true) DoorSystemSetOpenRatio(H[i],0.0,false,true) end '
           'local p=PlayerPedId() local pc=GetEntityCoords(p) SetEntityCoords(p,%.3f,%.3f,%.3f) FreezeEntityPosition(p,true) SetFocusPosAndVel(%.3f,%.3f,%.3f,0.0,0.0,0.0) '
           'local ts=GetGameTimer() local f0=0 repeat Wait(250) f0=0 for i,d in ipairs(D) do if obj(d)~=0 then f0=f0+1 end end until f0==#D or GetGameTimer()-ts>20000 '
           'local sm=GetGameTimer()-ts local nudges=0 local out="" '
           'local function leave() ClearFocus() SetEntityCoords(p,pc.x,pc.y,pc.z) FreezeEntityPosition(p,false) end ') % (items, BX, BY, BZ, CX, CY, CZ)
    tail = 'leave() return out..":"..tostring(sm)..":"..tostring(nudges)'
    if mode == 'open':
        lua += ('for i,d in ipairs(D) do opendoor(i,d) end local t0=GetGameTimer() local f,b,l=read(false) '
                'while b>0 and GetGameTimer()-t0<15000 do Wait(500) f,b,l=read(false) end '
                'out=tostring(#D)..":"..tostring(f)..":"..tostring(b)..":"..tostring(GetGameTimer()-t0)..":"..table.concat(l,",") ') + tail
    elif mode == 'debug':
        lua += ('local R={} for i,d in ipairs(D) do local o=obj(d) local rec if o==0 then rec=tostring(i)..",0" else local c=GetEntityCoords(o) '
                'local dh=math.abs(math.fmod((GetEntityHeading(o)-d[5])+540.0,360.0)-180.0) local dp=#(c-vector3(d[2],d[3],d[4])) '
                'local st=IsDoorRegisteredWithSystem(H[i]) and DoorSystemGetDoorState(H[i]) or -1 '
                'rec=string.format("%d,%d,%s,%.3f,%.3f,%.3f,%.2f,%.2f,%.3f,%s,%d",i,o,tostring(GetEntityModel(o)==GetHashKey(d[1])),c.x,c.y,c.z,GetEntityHeading(o),dh,dp,tostring(IsEntityPositionFrozen(o)),st) end '
                'R[#R+1]=rec end leave() return table.concat(R,";")')
    elif mode == 'release':
        lua += ('local f=0 for i,d in ipairs(D) do if IsDoorRegisteredWithSystem(H[i]) then DoorSystemSetDoorState(H[i],0,false,true) RemoveDoorFromSystem(H[i]) end '
                'if obj(d)~=0 then f=f+1 end end out=tostring(#D)..":"..tostring(f)..":0:0:" ') + tail
    else:                                                                       # close / hold
        lua += ('for i,d in ipairs(D) do shutdoor(i,d) end local t0=GetGameTimer() local f,b,l=read(true) '
                'while b>0 and GetGameTimer()-t0<30000 do Wait(500) for i,d in ipairs(D) do if isshut(d)==false then shutdoor(i,d) '
                'if GetGameTimer()-t0>8000 then local o=obj(d) if o~=0 then SetEntityHeading(o,d[5]) nudges=nudges+1 end end end end f,b,l=read(true) end '
                'local ms=GetGameTimer()-t0 ')
        if mode == 'hold':                                                      # locked only once every leaf is shut, then read again
            lua += 'if b==0 then for i=1,#D do DoorSystemSetDoorState(H[i],1,false,true) end Wait(500) f,b,l=read(true) end '
        else:                                                                   # released only once every leaf is shut, then read again
            lua += 'if b==0 then for i=1,#D do DoorSystemSetDoorState(H[i],0,false,true) RemoveDoorFromSystem(H[i]) end Wait(2000) f,b,l=read(true) end '
        lua += 'out=tostring(#D)..":"..tostring(f)..":"..tostring(b)..":"..tostring(ms)..":"..table.concat(l,",") ' + tail
    return lua
def debug(res):
    """the per-door records -> (rows, the doors not shut); writes <out>/doordebug.json."""
    import math
    rows = []
    for rec in (res or '').split(';'):
        f = rec.split(',')
        if len(f) < 2: continue
        i = int(f[0]) - 1; d = doors[i]
        if f[1] == '0': rows.append({'door': names[i], 'found': False}); continue
        x, y, z, hd, dh, dp = map(float, f[3:9])
        others = [math.dist((x, y, z), e[1:4]) for j, e in enumerate(doors) if j != i and e[0] == d[0]]
        rows.append({'door': names[i], 'found': True, 'handle': int(f[1]), 'model_matches': f[2] in ('true', '1'), 'obj': [round(x, 3), round(y, 3), round(z, 3)],
                     'placement': [round(v, 3) for v in d[1:4]], 'heading': hd, 'placement_heading': round(d[4], 2), 'dh_deg': dh, 'dp_m': dp,
                     'nearest_other_same_model_m': round(min(others), 2) if others else None, 'frozen': f[9] in ('true', '1'), 'door_system_state': int(f[10]),
                     'shut': dh <= 3.0 and dp <= 0.15})
    (JL / OD / 'doordebug.json').write_text(json.dumps(rows, indent=1))
    return rows, [r for r in rows if not r.get('shut')]
def photos(bad):
    """one frame of each door not shut, from 2.2 m in front of its closed leaf's middle on both sides (tcshot.sh, 13:00)."""
    import math
    SD = JL.parent.parent / 'shots' / 'p4_jail_doordebug'; SD.mkdir(parents=True, exist_ok=True); out = []
    for r in bad:
        if not r.get('found'): continue
        i = names.index(r['door']); _, x, y, z, h = doors[i]; a = math.radians(h)
        mx, my = x - 0.65 * math.cos(a), y - 0.65 * math.sin(a); nx, ny = -math.sin(a), math.cos(a); fz = z - J.LEAF_H / 2
        for k, side in ((1, 'a'), (-1, 'b')):
            cx, cy = mx + k * 2.2 * nx, my + k * 2.2 * ny; png = SD / f'{r["door"]}_{side}.png'
            subprocess.run([GB, '-c', 'cd /c/C9Test && HOUR=13 bash tcshot.sh "$0" %.3f %.3f %.3f %.3f %.3f %.3f 60 4' % (cx, cy, fz + 1.6, mx, my, fz + 1.1), str(png)], capture_output=True, text=True, timeout=120)
            out.append(str(png))
    subprocess.run([GB, '-c', 'cd /c/C9Test && bash tcshot_off.sh'], capture_output=True, text=True, timeout=60)
    return out
def verdict(mode, res):
    """(ok, line) from the Lua's answer."""
    m = re.search(r'(\d+):(\d+):(\d+):(\d+):([\d,]*):?(\d*):?(\d*)', res or '')
    if not m: return False, 'DOORCTL_FAIL no answer from the rig: ' + (res or '')[-300:]
    n, found, bad, ms = map(int, m.groups()[:4]); which = [names[int(i) - 1] for i in m.group(5).split(',') if i]
    extra = f' [streamed in {int(m.group(6)) / 1000:.1f} s, {m.group(7) or 0} nudges]' if m.group(6) else ''
    if found != len(doors): return False, f'DOORCTL_FAIL {mode}: only {found} of {len(doors)} door objects found at their spots after streaming the jail in{extra}'
    if mode in ('close', 'hold') and bad: return False, f'DOORCTL_FAIL {mode}: {bad} of {n} doors not shut after {ms / 1000:.1f} s (physical check), e.g. {which}{extra}'
    if mode == 'release': return True, f'DOORCTL_OK release {n} doors (back to the map default){extra}'
    if mode == 'hold': return True, f'DOORCTL_OK hold {n} doors (all shut by physical check in {ms / 1000:.1f} s, held LOCKED shut: run release after){extra}'
    if mode == 'open' and bad: return True, f'DOORCTL_WARN open: {bad} of {n} doors did not swing open in {ms / 1000:.1f} s, e.g. {which}{extra}'
    return True, f'DOORCTL_OK {mode} {n} doors{extra}' + (f' (all shut by physical check, settled in {ms / 1000:.1f} s, released to the map default and still shut 2 s later)' if mode == 'close' else f' (all open in {ms / 1000:.1f} s)')
if __name__ == '__main__':
    mode = sys.argv[1]; assert mode in ('open', 'close', 'hold', 'release', 'debug'), 'usage: jj_doorctl.py open|close|hold|release|debug'
    lua = code(mode)
    if '--dry' in sys.argv: print(lua); sys.exit(0)                             # the Lua only
    r = subprocess.run([GB, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 90', lua], capture_output=True, text=True, timeout=150)
    m = re.search(r'"result":"([^"]*)"', r.stdout)
    if mode == 'debug':
        if not m: print('DOORCTL_FAIL debug: no answer from the rig: ' + (r.stdout + r.stderr)[-300:]); sys.exit(1)
        rows, bad = debug(m.group(1))
        for b in bad: print('  NOT SHUT', json.dumps(b))
        shots = photos(bad) if '--no-photos' not in sys.argv else []
        print(f'DOORCTL_DEBUG {len(rows)} doors read, {len(bad)} not shut; {OD}/doordebug.json; {len(shots)} photos in shots/p4_jail_doordebug/'); sys.exit(0)
    ok, line = verdict(mode, m.group(1) if m else r.stdout + r.stderr); print(line); sys.exit(0 if ok else 1)
