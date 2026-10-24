"""Offline door-swing clearance (round 7 door fix, 2026-10-23): for every door of the shop MLO (jy_shop8_mlo.ytyp, Rocky's
swinging doors jy_rocky_door67 / 68; the roll-ups 112 / 113 lift and are listed apart) the whole swing - the half disc the leaf
sweeps from shut to 90 degrees open, BOTH ways (the doors swing both ways) - is sampled every 5 cm against the BUILT collision (every shipped ybn + our
placed drawables' bounds, as hole_grid_offline.py reads them), every flat face (|nz| > 0.5, either way up: the door's own physics is
not a ray) within 0.3 m of the door's bottom. Clearance = door bottom - highest such face. Below CLEAR the door drags (the north
porch door jammed at -0.009 m).
Run after hole_grid_offline.py has exported the build: py -3 door_swing_check.py   -> DOOR lines; exit 1 if any swing door drags."""
import math, sys, numpy as np, xml.etree.ElementTree as ET
from pathlib import Path
import hole_grid_offline as H
M = Path(__file__).resolve().parents[1]
CLEAR = 0.0                                             # the shop's own doors clear its floor by 1-4 mm: anything above that drags
SWING = {'jy_rocky_door67', 'jy_rocky_door68'}


def main():
    Tr = H.load_all()
    n = np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0]); nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    Tr = Tr[np.abs(nz) > 0.5]
    bb = {}
    for f in (M / 'xml').glob('jy_rocky_door*.ytyp.xml'):
        for a in ET.parse(f).getroot().iter('Item'):
            if a.findtext('name'): bb[a.findtext('name')] = (float(a.find('bbMin').get('x')), float(a.find('bbMax').get('x')), float(a.find('bbMin').get('z')))
    ox, oy, oz = H.MLO_ORIGIN; bad = 0
    for e in ET.parse(M / 'xml' / 'jy_shop8_mlo.ytyp.xml').getroot().iter('Item'):
        a = e.findtext('archetypeName')
        if a not in bb: continue
        p = e.find('position'); q = e.find('rotation')
        x, y, z = float(p.get('x')) + ox, float(p.get('y')) + oy, float(p.get('z')) + oz
        h = -2 * math.atan2(float(q.get('z')), float(q.get('w')))
        x0, x1, zb = bb[a]; bottom = z + zb; w = max(abs(x0), abs(x1))
        if a not in SWING:
            print(f'DOOR {a:17s} ({x:.2f}, {y:.2f})  roll-up, lifts vertically: bottom {bottom:.3f} (not a swing)'); continue
        sgn = 1.0 if x1 > -x0 else -1.0                                     # the leaf runs along local +x (or -x) from its hinge
        pts = [(x + r * math.cos(h + (0 if sgn > 0 else math.pi) + t), y + r * math.sin(h + (0 if sgn > 0 else math.pi) + t))
               for r in np.arange(0.05, w + 0.001, 0.05) for t in np.radians(np.arange(-90, 91, 2.5))]   # swept both ways from shut
        P = np.array(pts); top = -1e9
        lo = Tr.min(axis=1); hi = Tr.max(axis=1)
        near = Tr[(hi[:, 0] >= x - w) & (lo[:, 0] <= x + w) & (hi[:, 1] >= y - w) & (lo[:, 1] <= y + w) & (hi[:, 2] > bottom - 0.3) & (lo[:, 2] < bottom + 0.3)]
        for t in near:
            (ax, ay, az), (bx, by_, bz), (cx, cy, cz) = t
            d = (by_ - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-12: continue
            l1 = ((by_ - cy) * (P[:, 0] - cx) + (cx - bx) * (P[:, 1] - cy)) / d; l2 = ((cy - ay) * (P[:, 0] - cx) + (ax - cx) * (P[:, 1] - cy)) / d; l3 = 1 - l1 - l2
            ins = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
            if ins.any():
                zz = (l1 * az + l2 * bz + l3 * cz)[ins]; zz = zz[(zz > bottom - 0.3) & (zz < bottom + 0.3)]
                if len(zz): top = max(top, float(zz.max()))
        c = bottom - top; bad += c < CLEAR
        print(f'DOOR {a:17s} ({x:.2f}, {y:.2f}) heading {math.degrees(h):6.1f}  bottom {bottom:.3f}  highest ground in its swing {top:.3f}  '
              f'clearance {c:+.3f}  {"OK" if c >= CLEAR else "DRAGS"}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__': main()
