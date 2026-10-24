"""The site's ground as built from source (ground-fix pass, 2026-10-23), for the lot's graded apron (lot_plan.py): Rockstar's own
collision (../vanilla/*.ybn, never edited) read back through CodeWalker, the lowest UP-facing hit per 0.5 m cell (a ray down only
hits faces turned up - checked against the in-game scan, see hole_grid_offline.py), and inside the old hangar footprint our own
flattened plan (ground.py, = what site_col.py / terrain.py make of it). Walls, roofs and props stand on the ground, so the lowest
up-facing hit is the ground; the hangar's pit is inside HANGAR and replaced by the plan.
Run: py -3 ground_map.py     Output ../site/ground_map.npy + ground_map.json (origin, step)   [rerun after vanilla_extract.ps1]"""
import json, numpy as np, xml.etree.ElementTree as ET
from pathlib import Path
import hole_grid_offline as H, ground as G
M = Path(__file__).resolve().parents[1]; VAN = M / 'vanilla'; XMLD = M / 'site' / 'xml_vanilla'
BOX = (2304.0, 2404.0, 3092.0, 3179.0)                 # the lot + every apron it can grow + margin (world x0, x1, y0, y1)
STEP = 0.5
FILES = sorted(VAN.glob('cs4_02_[0-9].ybn')) + sorted(VAN.glob('hi@cs4_02_*.ybn'))   # the base set (hei_ / lr_ are copies of it)


def main():
    H.export(FILES, XMLD)
    roots = [ET.parse(XMLD / (f.name + '.xml')).getroot() for f in FILES]
    Tr = np.concatenate([H.tris_of(r if r.tag == 'Bounds' else r.find('.//Bounds'), lambda V: V) for r in roots])
    nx, ny = int(round((BOX[1] - BOX[0]) / STEP)) + 1, int(round((BOX[3] - BOX[2]) / STEP)) + 1
    Z = H.cast(Tr, BOX[0], BOX[2], nx, ny, STEP)
    for j in range(ny):                                  # the hangar footprint: our flattened plan
        for i in range(nx):
            z = G.hangar_z(BOX[0] + i * STEP, BOX[2] + j * STEP, 'col')
            if z is not None: Z[j, i] = z
    miss = int((Z == -999.0).sum())
    assert miss < 0.002 * Z.size, f'{miss} cells with no ground (the box runs off the files read)'
    while (Z == -999.0).any():                           # (a stray miss: its neighbours' mean)
        P = np.pad(np.where(Z == -999.0, np.nan, Z), 1, mode='edge')
        nb = np.array([P[1 + dy:P.shape[0] - 1 + dy, 1 + dx:P.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        with np.errstate(all='ignore'): m = np.nanmean(nb, axis=0)
        Z = np.where((Z == -999.0) & ~np.isnan(m), m, Z)
    np.save(M / 'site' / 'ground_map.npy', Z)
    json.dump({'origin': [BOX[0], BOX[2]], 'step': STEP, 'shape': [ny, nx], 'filled_misses': miss}, open(M / 'site' / 'ground_map.json', 'w'))
    print('GROUND_MAP_PASS', Z.shape, 'z', round(float(Z.min()), 2), round(float(Z.max()), 2), 'misses filled', miss)


if __name__ == '__main__': main()
