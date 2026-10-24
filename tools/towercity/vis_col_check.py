"""Visible-but-not-solid check (Antonio 2026-10-23: "a layer you can walk through" at the mall entrance). Every visible surface a
player could stand on or walk into - each upward-facing triangle (area > 0.3 m2) of every built drawable (work/*/tris_*.npy) that
lies within 2.3 m above a floor level, at least 0.6 m wide and not covered by another drawn face - is probed in game: a ray straight down from 0.3 m above its centre must hit collision
within 0.1 m of it. Misses = a floor / step / slab / ledge drawn without collision under it (or something visible poking up over
the real floor). Runs on client 1 of the C9Test rig (tower_city deployed), batch by batch so the area's collision is streamed in.
Run: py -3 vis_col_check.py   -> work/logs/vis_col.json + a summary per drawable; exit 1 if anything misses."""
GITBASH = r'C:\Program Files\Git\bin\bash.exe'   # NOT plain 'bash': from Python on Windows that is WSL's bash (no distro) - every call failed silently
import json, glob, subprocess, sys, re, time, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent
FLOORS = [11.0, 12.4, 17.0, 18.4, 23.0, 29.2, 30.8, 36.4, 43.6, 242.0, 246.4, 250.8, 256.0, 268.0]
TOL, BATCH = 0.10, 200


def samples():
    out = []
    for f in sorted(glob.glob(str(W / '*' / 'tris_*.npy'))):
        T = np.load(f).astype(np.float64); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1) / 2
        nz = n[:, 2] / np.maximum(2 * a, 1e-9); c = T.mean(1); band = np.zeros(len(T), bool)
        for fl in FLOORS: band |= (c[:, 2] > fl - 0.1) & (c[:, 2] < fl + 2.3)
        name = Path(f).stem[5:]
        # narrow faces (shelf boards, ledges, wall and kerb tops: nobody stands on them) are skipped - the narrowest side of a
        # triangle's footprint must be at least 0.6 m (its area / its longest edge)
        e = np.max(np.stack([np.linalg.norm(T[:, k] - T[:, (k + 1) % 3], axis=1) for k in range(3)], 1), 1)
        wide = (2 * a / np.maximum(e, 1e-9)) >= 0.6
        out += [(name, *map(float, c[i])) for i in np.where((nz > 0.9) & (a > 0.3) & band & wide)[0]]
    return out


def buried(S):
    """samples with another drawn upward face 0.05..0.6 m ABOVE them at the same spot: the face is covered (no one sees it)."""
    T = np.concatenate([np.load(f).astype(np.float64) for f in glob.glob(str(W / '*' / 'tris_*.npy'))])
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); up = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-9) > 0.9
    U = T[up]; lo, hi, zc = U.min(1), U.max(1), U[:, :, 2].mean(1); out = set()
    for k, (_, x, y, z) in enumerate(S):
        m = (lo[:, 0] <= x) & (hi[:, 0] >= x) & (lo[:, 1] <= y) & (hi[:, 1] >= y) & (zc > z + 0.05) & (zc < z + 0.6)
        for t in U[m]:
            A, B, C = t[:, :2]; v0, v1, v2 = C - A, B - A, np.array([x, y]) - A
            d00, d01, d02, d11, d12 = v0 @ v0, v0 @ v1, v0 @ v2, v1 @ v1, v1 @ v2; den = d00 * d11 - d01 * d01
            if abs(den) < 1e-12: continue
            u = (d11 * d02 - d01 * d12) / den; v = (d00 * d12 - d01 * d02) / den
            if u >= -1e-3 and v >= -1e-3 and u + v <= 1 + 1e-3: out.add(k); break
    return out


def cl(code, timeout=30):
    r = subprocess.run([GITBASH, '-c', f'cd /c/C9Test && ./t.sh cl 1 "$0" 30', code], capture_output=True, text=True, timeout=timeout)
    m = re.search(r'"result":"([^"]*)"', r.stdout)
    if not m: raise SystemExit('NO ANSWER FROM THE GAME CLIENT - nothing was tested: ' + (r.stdout + r.stderr)[:400])
    return m.group(1)


def main():
    S = samples(); hid = buried(S); S = [s for k, s in enumerate(S) if k not in hid]
    S.sort(key=lambda s: (round(s[3] / 4), round(s[1] / 40), round(s[2] / 40)))
    print('VIS_COL buried faces skipped', len(hid), flush=True)
    print('VIS_COL samples', len(S), flush=True)
    miss = []
    for b in range(0, len(S), BATCH):
        chunk = S[b:b + BATCH]; cx, cy, cz = (float(np.mean([s[k] for s in chunk])) for k in (1, 2, 3))
        pts = ','.join('{%.3f,%.3f,%.3f}' % s[1:] for s in chunk)
        cl("local p=PlayerPedId() SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true) "
           f"SetEntityCoordsNoOffset(p,{cx:.2f},{cy:.2f},{cz + 1.0:.2f},false,false,false) _G.__vc=nil "
           f"CreateThread(function() Wait(1800) local P={{{pts}}} local r={{}} "
           "for i,q in ipairs(P) do local h=StartShapeTestRay(q[1],q[2],q[3]+0.3,q[1],q[2],q[3]-0.6,1,p,0) local s,hit,e repeat Wait(0) s,hit,e=GetShapeTestResult(h) until s~=1 "
           f"if hit~=1 or math.abs(e.z-q[3])>{TOL} then r[#r+1]=i..':'..(hit==1 and string.format('%.2f',e.z) or 'none') end end _G.__vc=table.concat(r,' ') end) return 'ok'")
        res = None
        for _ in range(60):
            res = cl('return tostring(_G.__vc)')
            if res is not None and res != 'nil': break
            time.sleep(1.5)
        for tok in (res or '').split():
            i, z = tok.split(':'); s = chunk[int(i) - 1]; miss.append({'drawable': s[0], 'at': [round(v, 2) for v in s[1:]], 'hit': z})
        print(f'  batch {b // BATCH + 1}/{(len(S) + BATCH - 1) // BATCH}: {len((res or "").split())} miss', flush=True)
    # a miss is re-probed on its own, the ped parked right at it (a batch's far end may not have streamed in yet); stair treads
    # sit up to 0.22 m under their ramp collision by design (playbook: stairs = ramp collision) - listed apart, not as faults
    final, stairs = [], []
    for m in miss:
        x, y, z = m['at']
        r = cl(f"local p=PlayerPedId() SetEntityCoordsNoOffset(p,{x:.2f},{y:.2f},{z + 2.0:.2f},false,false,false) RequestCollisionAtCoord({x:.2f},{y:.2f},{z:.2f}) Wait(1500) "
               f"local h=StartExpensiveSynchronousShapeTestLosProbe({x:.3f},{y:.3f},{z + 0.3:.3f},{x:.3f},{y:.3f},{z - 0.6:.3f},1,p,0) local _,hit,e=GetShapeTestResult(h) "
               "return hit==1 and string.format('%.2f',e.z) or 'none'")
        if r != 'none' and abs(float(r) - z) <= TOL: continue
        if r != 'none' and 0 < float(r) - z <= 0.22: stairs.append(m); continue
        m['hit'] = r; final.append(m)
    print('VIS_COL stair treads under ramp collision (by design):', len(stairs))
    miss = final
    cl('local p=PlayerPedId() SetEntityVisible(p,true) SetEntityCollision(p,true,true) FreezeEntityPosition(p,false) return "ok"')
    json.dump(miss, open(W / 'logs/vis_col.json', 'w'), indent=1)
    by = {}
    for m in miss: by.setdefault(m['drawable'], []).append(m)
    print('VIS_COL', len(miss), 'visible surfaces without collision under them')
    for d, ms in sorted(by.items(), key=lambda kv: -len(kv[1])): print(f'  {len(ms):4d}  {d:28s} e.g. {ms[0]["at"]} (hit {ms[0]["hit"]})')
    sys.exit(1 if miss else 0)


if __name__ == '__main__': main()
