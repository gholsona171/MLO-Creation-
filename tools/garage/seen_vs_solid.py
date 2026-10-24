"""Offline 'what you see is what you walk on' check for the ground around the garage (ground-fix pass, 2026-10-23).
The drawn ground is read back from the BUILT drawables (CodeWalker XML of the high-detail models, every geometry's vertex + index
buffers), the walked ground from the offline hole grid (hole_grid_offline.py: the built collision, lowest up-facing hit):
  * on the blacktop (lot_plan.in_asph, the building's floor excluded): the lot drawables (jy_lot_*: blacktop + overlay 2 cm over it)
  * around it (where lot_plan.apron_z grades the ground) and on the rest of the site: the terrain (terrain.py's cs4_02_land10 / 11)
Per cell the LOWEST up-facing drawn face of that set is compared with the collision; a cell over TOL apart is listed ('site' =
Rockstar's untouched ground, printed for reference: his own drawn / collision meshes differ by up to ~8 cm).
Run after hole_grid_offline.py: py -3 seen_vs_solid.py   -> SEEN_VS_SOLID summary + the worst cells; exit 1 if any cell is off."""
import json, sys, numpy as np, xml.etree.ElementTree as ET
from pathlib import Path
import hole_grid_offline as H, lot_plan as L
M = Path(__file__).resolve().parents[1]; ST = H.STREAM; XMLD = M / 'site' / 'xml_offline'
TOL = 0.06                                         # (two triangulations of one surface on a 1:3 bank differ ~5 cm)
TERRAIN = {'cs4_02_land10': (2325.05249, 3157.632, 47.31591), 'cs4_02_land11': (2367.22314, 3065.24146, 45.32363)}   # entity positions


def drawn_tris(xml_path, origin):
    root = ET.parse(xml_path).getroot(); out = []
    hi = root.find('DrawableModelsHigh')
    for g in (hi.iter('Item') if hi is not None else []):
        vb = g.find('VertexBuffer'); ib = g.find('IndexBuffer')
        if vb is None or ib is None: continue
        V = np.array([[float(a) for a in ln.split()[:3]] for ln in vb.find('Data').text.strip().splitlines()]) + np.array(origin)
        I = np.array([int(a) for a in ib.find('Data').text.split()]).reshape(-1, 3)
        out.append(V[I])
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def main():
    lot = json.load(open(M / 'site' / 'lot' / 'lot_info.json'))
    H.export([ST / f'{n}.ydr' for n in list(TERRAIN) + list(lot)])
    T_ter = np.concatenate([drawn_tris(XMLD / f'{n}.ydr.xml', o) for n, o in TERRAIN.items()])
    T_lot = np.concatenate([drawn_tris(XMLD / f'{n}.ydr.xml', v['origin']) for n, v in lot.items()])
    Zt, Zl = H.cast(T_ter), H.cast(T_lot)
    C = np.load(M / 'site' / 'hole_grid_offline.npy')
    rows = {'blacktop': [], 'apron': [], 'site': []}
    for j in range(C.shape[0]):
        for i in range(C.shape[1]):
            x, y = H.X0 + i * H.STEP, H.Y0 + j * H.STEP
            if L.building(x, y) or L.d_asph(x, y) > L.APRON_MAX + 2 or L.in_yard(x, y): continue
            on = L.in_asph(x, y) and L.depth_asph(x, y) > 0.05
            near = L.d_asph(x, y) < 0.05 and L.depth_asph(x, y) < 0.05            # (the outline itself: skipped)
            z = Zl[j, i] if on else Zt[j, i]
            if near or C[j, i] == -999.0 or z == -999.0: continue
            k = 'blacktop' if on else ('apron' if L.apron_z(x, y) is not None else 'site')
            rows[k].append((round(x, 2), round(y, 2), round(float(z - C[j, i]), 3)))
    bad = 0
    for k, r in rows.items():
        if not r: print(f'SEEN_VS_SOLID {k:8s} cells     0'); continue
        d = np.array([a[2] for a in r]); off = [a for a in r if abs(a[2]) > TOL]
        if k != 'site': bad += len(off)                                     # (site: Rockstar's own, untouched - for reference)
        print(f'SEEN_VS_SOLID {k:8s} cells {len(r):5d}  drawn - collision: median {np.median(d):+.3f}  max |d| {np.abs(d).max():.3f}  over {TOL} m: {len(off)}')
        for a in sorted(off, key=lambda a: -abs(a[2]))[:8]: print('    ', a)
    sys.exit(1 if bad else 0)


if __name__ == '__main__': main()
