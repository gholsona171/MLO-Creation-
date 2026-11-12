"""lot_shots.py <player> <outdir> <cams.txt> [HOUR] : Justice Center shots on the rig from lot-frame cameras ('name u v z tu tv tz' lines),
a live invisible ped parked under each camera (so the room streams and its timecycle applies), the clock held, the city's lights forced
on for the shot (the server's electrician job runs citywide blackouts). Needs bx_setup.lua loaded
in the client (BXcam / BXw) - this script registers the lot frame as BXI['j']. Every shot must land on disk or the run stops."""
import subprocess, sys, re, time, os
BASH = r'C:\Program Files\Git\bin\bash.exe'
P, OUT, CAMS = sys.argv[1], sys.argv[2], sys.argv[3]; HOUR = int(sys.argv[4]) if len(sys.argv) > 4 else 13
os.makedirs(OUT, exist_ok=True)
def cl(code, t=30):
    r = subprocess.run([BASH, '-c', f'cd /c/C9Test && ./t.sh cl {P} "$1" {t}', '_', code], capture_output=True, text=True).stdout
    m = re.search(r'"result":"([^"]*)"', r) or re.search(r'"result":([^,}]*)', r)
    if not m: raise SystemExit(f'NO ANSWER: {r[:300]}')
    return m.group(1)
cl("BXI = BXI or {} BXI['j'] = {id = 0, x = 335.87, y = -1640.11, z = 0.0, yaw = math.rad(50.0)} return 'lot'")
for line in open(CAMS):
    p = line.split()
    if len(p) < 7: continue
    n, u, v, z, tu, tv, tz = p[0], *map(float, p[1:7])
    cl(f"local x,y=BXw('j',{u},{v},0) local pd=PlayerPedId() SetEntityVisible(pd,false) SetEntityInvincible(pd,true) FreezeEntityPosition(pd,true) SetEntityCoords(pd,x,y,{z - 1.0},false,false,false,false) return 'mv'")
    time.sleep(1.2)
    cl(f"SetArtificialLightsState(false) SetArtificialLightsStateAffectsVehicles(false) return BXcam('j',{u},{v},{z},{tu},{tv},{tz},62,{HOUR})")
    time.sleep(2.8)
    f = f'{OUT}/{n}.png'; subprocess.run([BASH, '-c', 'cd /c/C9Test && bash gshot.sh "$1"', '_', f], capture_output=True)
    if not os.path.exists(f): raise SystemExit(f'SHOT NOT WRITTEN {f}')
    print(f, flush=True)
cl('return BXoff()')
print('LOT_SHOTS_DONE')
