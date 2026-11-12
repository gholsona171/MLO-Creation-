"""Police HQ audit cameras at ped eye height (floor + 1.65), from the plan's own spaces (jc3_police): per named space the two diagonal
views corner to corner (0.7 m in from the corners) plus a view of each corner from the middle - every wall join, corner and face
of the space is seen. Prints '<name> u v z tu tv tz' lines (lot frame). Run: py -3 jc5_audit_cams.py > audit_cams.txt"""
import sys, re
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent / 'p2'), str(Path(__file__).resolve().parent.parent)]
import jc3_police as P
EYE = 1.65; AIM = 1.0
def cams():
    out = []
    groups = [(P.P1, 'L1', P.SPACES_LOBBY), (P.P1, 'L1', P.SPACES_DESK), (P.P1, 'L1', P.SPACES1), (P.P2, 'L2', P.SPACES2),
              (P.P2, 'L2', {k: [r] for k, r in P.SUITES.items()})]
    for F, lv, spaces in groups:
        for name, rects in spaces.items():
            r = max(rects, key=lambda q: (q[1] - q[0]) * (q[3] - q[2])); u0, u1, v0, v1 = r
            if min(u1 - u0, v1 - v0) < 1.6: continue
            key = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_'); i = 0.7
            cs = [(u0 + i, v0 + i), (u1 - i, v0 + i), (u1 - i, v1 - i), (u0 + i, v1 - i)]
            for k, (a, b) in enumerate(((0, 2), (1, 3), (2, 0), (3, 1))):
                (cu, cv), (tu, tv) = cs[a], cs[b]
                out.append((f'{lv}_{key}_{k + 1}', cu, cv, F + EYE, tu, tv, F + AIM))
    return out
if __name__ == '__main__':
    for c in cams(): print(c[0], *[f'{x:.2f}' for x in c[1:]])
