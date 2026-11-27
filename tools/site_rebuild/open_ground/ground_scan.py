"""The vanilla ground under the Block Boyz site, read back from Rockstar's own collision (../vanilla/*.ybn, vanilla_extract.ps1; never
edited): every static collision file is exported to CodeWalker XML (cw_xml.ps1 -> ../site/xml_vanilla) and one vertical ray per 1 m
cell finds the LOWEST up-facing hit between z 25 and 60 (junk, sheds and fences stand on the ground, so the lowest up-facing hit is the
ground). A second pass over the road files only (cs4_roads*, hi@ copies), on a 0.25 m grid, marks where a road's collision is: the
road edges the site keeps 3 m off (site_outline.py, site_plan.py) are measured from the collision, not from path nodes (doc 12).
Run: py -3 ground_scan.py     Output ../site/ground_raw.npz (low, box = x0, y0, step, nx, ny; road on the ROAD_STEP grid)
Also importable: tris_of(Bounds element) and cast(triangles, ...) for the offline gates."""
import math, subprocess, sys, xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
T = Path(__file__).resolve().parent; M = T.parent
BOX = (985.0, 1325.0, 3515.0, 3670.0); STEP = 1.0                      # world x0, x1, y0, y1 (= vanilla_extract.ps1 -Box)
ROAD_STEP = 0.25
ZLO, ZHI = 25.0, 60.0
JX, JY = 0.0137, 0.0171                                                # rays off the mesh lines (a ray exactly on a shared edge slips through)


def export(files, xmld):
    ps = ','.join("'%s'" % str(f) for f in files)
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                        f"& '{T / 'cw_xml.ps1'}' -OutDir '{xmld}' -Files @({ps})"], capture_output=True, text=True)
    if r.returncode: raise SystemExit('CodeWalker export failed: ' + r.stdout[-400:] + r.stderr[-400:])


def mat4(txt): return np.array([float(a) for a in txt.split()]).reshape(4, 4)    # CodeWalker: row-vector matrix, translation in row 4


def tris_of(bounds_el, place=lambda V: V):
    """every triangle (n x 3 x 3 world points) of a Bounds element tree; place(points) maps file space to world."""
    out = []
    def walk(b, parent):
        m = parent; ct = b.find('CompositeTransform')
        if ct is not None: m = mat4(ct.text) @ parent
        kids = b.find('Children')
        if kids is not None:
            for c in kids: walk(c, m)
        vs = b.find('Vertices')
        if vs is None or not (vs.text or '').strip(): return
        gc = b.find('GeometryCenter'); g = np.array([float(gc.get(k)) for k in 'xyz']) if gc is not None else np.zeros(3)
        V = np.array([[float(a) for a in ln.split(',')] for ln in vs.text.strip().splitlines()]) + g
        V = np.c_[V, np.ones(len(V))] @ m; V = place(V[:, :3])
        idx = [(int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))) for t in b.iter('Triangle')]
        if idx: out.append(V[np.array(idx)])
    walk(bounds_el, np.eye(4))
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def bounds_of(xml_path):
    r = ET.parse(xml_path).getroot(); return r if r.tag == 'Bounds' else r.find('.//Bounds')


def cast(Tr, x0, y0, nx, ny, step, lowest=True):
    """lowest (or highest) up-facing hit per cell centre; nan = nothing between ZLO and ZHI."""
    Z = np.full((ny, nx), np.nan)
    up = np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0])[:, 2] > 0   # one-sided: a ray down only hits a face turned up
    Tr = Tr[up]; lo = Tr.min(axis=1); hi = Tr.max(axis=1)
    keep = (hi[:, 2] > ZLO) & (lo[:, 2] < ZHI) & (hi[:, 0] >= x0 - 1) & (lo[:, 0] <= x0 + nx * step + 1) & (hi[:, 1] >= y0 - 1) & (lo[:, 1] <= y0 + ny * step + 1)
    cx0, cy0 = x0 + step / 2 + JX, y0 + step / 2 + JY
    for t in Tr[keep]:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12: continue
        i0, i1 = max(0, int(math.ceil((min(ax, bx, cx) - cx0) / step))), min(nx - 1, int(math.floor((max(ax, bx, cx) - cx0) / step)))
        j0, j1 = max(0, int(math.ceil((min(ay, by, cy) - cy0) / step))), min(ny - 1, int(math.floor((max(ay, by, cy) - cy0) / step)))
        if i1 < i0 or j1 < j0: continue
        px, py = np.meshgrid(cx0 + np.arange(i0, i1 + 1) * step, cy0 + np.arange(j0, j1 + 1) * step)
        l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d; l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d; l3 = 1 - l1 - l2
        ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not ins.any(): continue
        z = l1 * az + l2 * bz + l3 * cz; ok = ins & (z > ZLO) & (z < ZHI)
        sub = Z[j0:j1 + 1, i0:i1 + 1]
        better = (z < sub) if lowest else (z > sub)
        Z[j0:j1 + 1, i0:i1 + 1] = np.where(ok & (np.isnan(sub) | better), z, sub)
    return Z


def main():
    files = sorted((M / 'vanilla').glob('*.ybn')); xmld = M / 'site' / 'xml_vanilla'
    export(files, xmld)
    nx, ny = int(round((BOX[1] - BOX[0]) / STEP)), int(round((BOX[3] - BOX[2]) / STEP))
    allT, roadT = [], []
    for f in files:
        Tr = tris_of(bounds_of(xmld / (f.name + '.xml')))
        allT.append(Tr)
        if 'roads' in f.name: roadT.append(Tr)
    low = cast(np.concatenate(allT), BOX[0], BOX[2], nx, ny, STEP)
    k = int(round(STEP / ROAD_STEP))
    road = ~np.isnan(cast(np.concatenate(roadT), BOX[0], BOX[2], nx * k, ny * k, ROAD_STEP))
    np.savez_compressed(M / 'site' / 'ground_raw.npz', low=low, road=road, box=np.array([BOX[0], BOX[2], STEP, nx, ny]), road_step=ROAD_STEP)
    print('GROUND_SCAN_PASS files', len(files), 'cells', nx * ny, 'empty', int(np.isnan(low).sum()), 'road cells', int(road.sum()))


if __name__ == '__main__': main()
