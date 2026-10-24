"""Hole grid (Antonio 2026-10-23: a player stepping out of the north porch door fell through the gravel - its collision had been cut
with the old porch slab and nothing put back; the surface probe missed it because that gravel is not one of our models).
Model-independent: over the whole site (the yard wall loop + a margin, building, porch, lot, deck) a 0.5 m grid of rays is fired
straight down from 60 m in game, passing through every layer (roof, deck, floor) to the LOWEST collision. A cell is flagged when
  * nothing is hit down to 30 m (a hole: you fall), or
  * its lowest hit lies more than 0.6 m below every one of its 8 neighbours' lowest hits (a pit / a missing patch), or
  * its lowest hit lies more than 1.2 m ABOVE the lowest ground within 2 m (a 'floating' cell: only a roof / canopy / deck has
    collision there and nothing under it - the porch hole read as 'porch roof' to a lowest-hit-only rule).
Plus the asphalt edge: along every edge of lot_plan.ASPH_RECTS the ground just inside (0.25 m) and just outside (0.75 m) is compared;
a step of more than STEP_MAX between them is listed (the lot sitting proud of the terrain instead of blending in).
Runs on client 1 of the C9Test rig tile by tile (the ped parked at each tile so its collision streams in).
Run: py -3 hole_grid.py [x0 x1 y0 y1]   -> ../site/hole_grid.json + a cluster list; exit 1 if anything is flagged."""
GITBASH = r'C:\Program Files\Git\bin\bash.exe'   # NOT plain 'bash': from Python on Windows that is WSL's bash (no distro) - every call failed silently
import json, re, subprocess, sys, time, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yard_plan as Y
OUT = Path(__file__).resolve().parents[1] / 'site' / 'hole_grid.json'
STEP, TILE, MARGIN, PIT, FLOAT, STEP_MAX = 0.5, 30.0, 8.0, 0.6, 1.2, 0.06


def cl(code, timeout=90):
    r = subprocess.run([GITBASH, '-c', 'cd /c/C9Test && ./t.sh cl 1 "$0" 60', code], capture_output=True, text=True, timeout=timeout)
    m = re.search(r'"result":"([^"]*)"', r.stdout)
    if not m: raise SystemExit('NO ANSWER FROM THE GAME CLIENT - nothing was tested: ' + (r.stdout + r.stderr)[:400])
    return m.group(1)


def main():
    if len(sys.argv) == 5: x0, x1, y0, y1 = map(float, sys.argv[1:])
    else:
        xs = [p[0] for p in Y.LOOP]; ys = [p[1] for p in Y.LOOP]
        x0, x1, y0, y1 = min(xs) - MARGIN, max(xs) + MARGIN, min(ys) - MARGIN, max(ys) + MARGIN
    nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
    Z = np.full((ny, nx), np.nan)
    tiles = [(tx, ty) for ty in np.arange(y0, y1, TILE) for tx in np.arange(x0, x1, TILE)]
    print('HOLE_GRID', nx * ny, 'cells in', len(tiles), 'tiles', flush=True)
    for k, (tx, ty) in enumerate(tiles):
        i0, j0 = int(round((tx - x0) / STEP)), int(round((ty - y0) / STEP))
        n = int(TILE / STEP)
        code = (f"local p=PlayerPedId() SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true) "
                f"SetEntityCoordsNoOffset(p,{tx + TILE / 2:.1f},{ty + TILE / 2:.1f},60.0,false,false,false) _G.__hg=nil "
                f"CreateThread(function() for a=0,2 do for b=0,2 do RequestCollisionAtCoord({tx:.1f}+a*{TILE / 2:.1f},{ty:.1f}+b*{TILE / 2:.1f},48.0) end end Wait(2500) "
                f"local out={{}} for j=0,{n - 1} do local row={{}} for i=0,{n - 1} do local x,y={tx:.2f}+i*{STEP}+0.0137,{ty:.2f}+j*{STEP}+0.0171 local top,low=60.0,nil "
                "for l=1,6 do local h=StartExpensiveSynchronousShapeTestLosProbe(x,y,top,x,y,30.0,1,p,0) local _,hit,e=GetShapeTestResult(h) "
                "if hit~=1 then break end low=e.z top=e.z-0.05 end row[#row+1]=low and string.format('%.2f',low) or 'n' end out[#out+1]=table.concat(row,',') "
                "if j%10==9 then Wait(0) end end _G.__hg=table.concat(out,';') end) return 'ok'")
        cl(code)
        res = None
        for _ in range(120):
            res = cl('return tostring(_G.__hg)')
            if res and res != 'nil': break
            time.sleep(1.0)
        for j, row in enumerate((res or '').split(';')):
            for i, v in enumerate(row.split(',')):
                if 0 <= j0 + j < ny and 0 <= i0 + i < nx and v: Z[j0 + j, i0 + i] = -999.0 if v == 'n' else float(v)
        print(f'  tile {k + 1}/{len(tiles)}', flush=True)
    cl('local p=PlayerPedId() SetEntityVisible(p,true) SetEntityCollision(p,true,true) FreezeEntityPosition(p,false) return "ok"')
    flags = []
    for j in range(ny):
        for i in range(nx):
            z = Z[j, i]
            if np.isnan(z): continue
            x, y = x0 + i * STEP, y0 + j * STEP
            if z == -999.0: flags.append((x, y, 'hole', None)); continue
            nb = [Z[jj, ii] for jj in (j - 1, j, j + 1) for ii in (i - 1, i, i + 1) if (jj, ii) != (j, i) and 0 <= jj < ny and 0 <= ii < nx]
            nb = [v for v in nb if not np.isnan(v) and v != -999.0]
            if len(nb) >= 5 and all(z < v - PIT for v in nb): flags.append((x, y, 'pit', round(float(z), 2))); continue
            win = Z[max(0, j - 4):j + 5, max(0, i - 4):i + 5]; win = win[~np.isnan(win) & (win != -999.0)]
            if len(win) and z > win.min() + FLOAT: flags.append((x, y, 'floating', round(float(z), 2)))
    import lot_plan as L
    def zat(x, y):
        i, j = int(round((x - x0) / STEP)), int(round((y - y0) / STEP))
        return Z[j, i] if 0 <= j < ny and 0 <= i < nx and not np.isnan(Z[j, i]) and Z[j, i] != -999.0 else None
    edges = []                                                      # the asphalt's edge against the ground beside it
    for ax0, ax1, ay0, ay1 in L.ASPH_RECTS:
        for side, pts in (('W', [(ax0, y) for y in np.arange(ay0, ay1, 1.0)]), ('E', [(ax1, y) for y in np.arange(ay0, ay1, 1.0)]),
                          ('S', [(x, ay0) for x in np.arange(ax0, ax1, 1.0)]), ('N', [(x, ay1) for x in np.arange(ax0, ax1, 1.0)])):
            dx, dy = {'W': (-1, 0), 'E': (1, 0), 'S': (0, -1), 'N': (0, 1)}[side]
            for x, y in pts:
                if any(r[0] < x + dx * 0.75 < r[1] and r[2] < y + dy * 0.75 < r[3] for r in L.ASPH_RECTS): continue   # inner seam
                zi, zo = zat(x - dx * 0.25, y - dy * 0.25), zat(x + dx * 0.75, y + dy * 0.75)
                if zi is not None and zo is not None and abs(zi - zo) > STEP_MAX: edges.append((round(x, 1), round(y, 1), side, round(float(zi - zo), 2)))
    clusters = []                                                   # group flagged cells within 1 m of each other
    for f in flags:
        for c in clusters:
            if c['kind'] == f[2] and any(abs(f[0] - p[0]) <= 1.0 and abs(f[1] - p[1]) <= 1.0 for p in c['cells']): c['cells'].append(f[:2]); break
        else: clusters.append({'kind': f[2], 'cells': [f[:2]], 'z': f[3]})
    for c in clusters:
        xs = [p[0] for p in c['cells']]; ys = [p[1] for p in c['cells']]
        c['box'] = [min(xs), max(xs), min(ys), max(ys)]; c['n'] = len(c['cells']); del c['cells']
    json.dump({'origin': [x0, y0], 'step': STEP, 'clusters': clusters, 'asphalt_edge_steps': edges}, open(OUT, 'w'), indent=1)
    np.save(OUT.with_suffix('.npy'), Z)
    print('ASPHALT_EDGE', len(edges), f'points where the lot sits more than {STEP_MAX} m above / below the ground beside it')
    for e in edges[:60]: print('  ', e)
    print('HOLE_GRID', len(flags), 'flagged cells in', len(clusters), 'clusters')
    for c in sorted(clusters, key=lambda c: -c['n']):
        b = c['box']; print(f"  {c['kind']:4s} {c['n']:5d} cells  x {b[0]:.1f}..{b[1]:.1f}  y {b[2]:.1f}..{b[3]:.1f}" + (f"  z {c['z']}" if c['z'] else ''))
    sys.exit(1 if flags or edges else 0)


if __name__ == '__main__': main()
