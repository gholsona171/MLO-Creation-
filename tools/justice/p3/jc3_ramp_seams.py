"""Seam gate for the garage ramps' COLLISION (rig 2026-10-30: police3 climbing the OUT ramp counted 4 impacts at u 24.95 / 26.48 / 29.49 -
exactly the 0.5 m slice boundaries of the ramp's prisms. Each prism brought its own closed collision box; merged per room, their end
faces stay as vertical triangles right under the driving surface, and wheels climbing the slope catch their top edges). A geometry sweep
cannot see this (nothing stands above the surface): this reads the compiled interior collision (out/xml/jc_courts.ybn.xml, CodeWalker
XML of out/jc_courts.ybn, MLO-local = the lot frame) and fails on any near-vertical collision triangle inside a ramp's clear lane (0.3 m
in from its edges, 0.25 m in from its foot and top: the joints with the deck and the street are flat - slope 0 - and drove clean on the
rig) whose top reaches the ramp surface there (within 5 cm) - a riser under the wheels.
Proof: --plant adds one 0.5 m slice end face on the OUT ramp; it must be found. Run: py -3 jc3_ramp_seams.py [--plant]"""
import sys, re
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc3_pgarage as G, jc3_police as P
def tris():
    s = (P3 / 'out/xml/jc_courts.ybn.xml').read_text(encoding='utf-8')
    out = []
    for item in re.findall(r'<Item type="GeometryBVH">(.*?)</Polygons>', s, re.S):
        c = re.search(r'<GeometryCenter x="([^"]+)" y="([^"]+)" z="([^"]+)"', item); c = np.array([float(x) for x in c.groups()])
        V = np.array([[float(x) for x in ln.replace(',', ' ').split()] for ln in re.search(r'<Vertices>(.*?)</Vertices>', item, re.S).group(1).strip().splitlines()]) + c
        for a, b, d in re.findall(r'<Triangle m="\d+" v1="(\d+)" v2="(\d+)" v3="(\d+)"', item): out.append(V[[int(a), int(b), int(d)]])
    assert out, 'no collision triangles read from the interior bound'
    return np.array(out)
def risers(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    bad = []
    for k, (l0, l1) in G.LANES.items():
        c0, c1 = l0 + 0.2 + 0.3, l1 - 0.2 - 0.3
        for t, nn in zip(T, n):
            if abs(nn[2]) >= 0.6: continue
            u, v = t[:, 0].mean(), t[:, 1].mean()
            if not (G.U_FOOT + 0.25 <= u <= G.U_TOP - 0.25 and c0 <= v <= c1): continue   # the ramp's own run (its ends are flat joints)
            if abs(t[:, 2].max() - G.ramp_z(min(max(u, G.U_FOOT), G.U_TOP))) < 0.05: bad.append((k, round(float(u), 2), round(float(v), 2)))
    return bad
def main():
    T = tris()
    if '--plant' in sys.argv:
        u = G.U_FOOT + 7 * 0.5; z = G.ramp_z(u); c0, c1 = G.LANES['out'][0] + 0.2, G.LANES['out'][1] - 0.2
        T = np.concatenate([T, np.array([[[u, c0, G.ZB - 0.4], [u, c1, G.ZB - 0.4], [u, c1, z]]])])
        assert any(b[0] == 'out' and abs(b[1] - u) < 0.3 for b in risers(T)), 'the planted slice end was not found - the seam gate is broken'
        print('RAMP_SEAMS_PLANT_FOUND'); return 0
    bad = risers(T); seen = sorted({(k, u) for k, u, v in bad})
    print(f'RAMP_SEAMS {len(bad)} riser triangle(s) under the ramps\' driving surface' + (': ' + ', '.join(f'{k} u {u}' for k, u in seen[:12]) if seen else ''))
    print('RAMP_SEAMS_PASS' if not bad else 'RAMP_SEAMS_FAIL'); return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
