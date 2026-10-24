"""Crack check: hairline gaps in the DRAWN ground (round 7 seams, 2026-10-23). Antonio: "very thin lines in the perimeter, like it
did not meet - not a height difference, just not fully there". hole_grid / seen_vs_solid read the collision and cannot see them.
Every drawn ground surface around the garage is read back from the BUILT drawables (CodeWalker XML, high-detail vertex + index
buffers, each geometry at its entity position): the lot's blacktop (jy_lot_*), the terrain we reshape (cs4_02_land10 / 11 -
Rockstar's own copy where we ship none). The lot's sand feather is a see-through decal layer over both and is left out.
Inside the apron box it lists
  T  T-junctions: a vertex of one surface lying on the INSIDE of an edge of another (or the same) surface - within 2 mm across -
     whose height is 1 mm - 2 cm off that edge: the triangles beside it do not meet, a hairline opens along the edge;
  G  gaps: a boundary edge (used by one triangle only - Rockstar splits his terrain into one mesh per material, so seams are
     boundaries) that no other edge meets: at its quarter points no edge of any surface runs through within 2 mm across and 3 mm
     in height. The blacktop's outline must be met by the sand's edge, a material seam by the other material's edge. An open
     edge that lies on one of Rockstar's own open edges (the terrain as he ships it, same place, same height) is listed as
     ROCKSTAR and not counted: we neither made nor moved it. A 1 cm step down from the blacktop's edge to the sand is such a gap: seen low across the
     edge it is a slot under the blacktop, a dark line in the sand (the first crack Antonio saw, the lot's west edge).
     Not checked: the blacktop's edge round the building's floor (the floor is the MLO's), anything under the blacktop
     (hidden by it) or inside the junkyard wall's foot.
Each finding is a world point. Run: py -3 crack_check.py [stream dir] -> CRACK lines + ../site/crack_check.json; exit 1 if any.
Prove it on a known crack first (the deployed build of 2026-10-23 evening: the west edge at x 2318, y 3125-3132)."""
import json, sys, math, numpy as np, xml.etree.ElementTree as ET
from pathlib import Path
import hole_grid_offline as H, lot_plan as L
M = Path(__file__).resolve().parents[1]; XMLD = M / 'site' / 'xml_offline'; VAN = M / 'vanilla'
STREAM = Path(sys.argv[1]) if len(sys.argv) > 1 else M / 'resource' / 'rocky_shop8_junkyard' / 'stream'
BOX = L.apron_box()
TERRAIN = {'cs4_02_land10': (2325.05249, 3157.632, 47.31591), 'cs4_02_land11': (2367.22314, 3065.24146, 45.32363)}
XY_TOL, T_MIN, T_MAX, MATCH_Z = 0.002, 0.001, 0.02, 0.003


def surfaces():
    """(name, vertices world, triangles) per geometry of each ground drawable; the feather decal geometry left out."""
    lot = json.load(open(M / 'site' / 'lot' / 'lot_info.json'))
    want = {n: tuple(v['origin']) for n, v in lot.items()} | TERRAIN
    files = [(STREAM / f'{n}.ydr') if (STREAM / f'{n}.ydr').exists() else (VAN / f'{n}.ydr') for n in want]
    H.export(files)
    out = []
    for n, o in want.items():
        root = ET.parse(XMLD / f'{n}.ydr.xml').getroot(); hi = root.find('DrawableModelsHigh'); k = 0
        for g in hi.iter('Item'):
            vb = g.find('VertexBuffer'); ib = g.find('IndexBuffer')
            if vb is None or ib is None: continue
            V = np.array([[float(a) for a in ln.split()[:3]] for ln in vb.find('Data').text.strip().splitlines()]) + np.array(o)
            I = np.array([int(a) for a in ib.find('Data').text.split()]).reshape(-1, 3)
            k += 1
            if n.startswith('jy_lot') and max(L.d_asph(v[0], v[1]) for v in V[::7]) > 0.5: continue      # the feather (decal)
            out.append((f'{n}#{k - 1}', V, I))
    return out


def inbox(p, m=0.0): return BOX[0] - m <= p[0] <= BOX[1] + m and BOX[2] - m <= p[1] <= BOX[3] + m
import yard_plan as Y
def hidden(p):
    """under the blacktop (covered by it) or inside the junkyard wall's foot (Rockstar's own open edges under the old wall)."""
    return (L.depth_asph(p[0], p[1]) > 0.002 and not L.building(p[0], p[1])) or Y.dist_to_loop(p[0], p[1]) < Y.THICK / 2
def on_hole(A, B):
    h = L.HOLE; e = 0.01
    return all((abs(p[0] - h[0]) < e or abs(p[0] - h[1]) < e or abs(p[1] - h[2]) < e or abs(p[1] - h[3]) < e) and L.in_rect(h, p[0], p[1], e) for p in (A, B))


def find(S):
    edges = []                                                     # (a, b, surface, boundary?, third vertex)
    for si, (n, V, I) in enumerate(S):
        cnt = {}; key = lambda i: tuple(np.round(V[i], 4))
        for t in I:
            for a, b, c in ((t[0], t[1], t[2]), (t[1], t[2], t[0]), (t[2], t[0], t[1])):
                cnt.setdefault(tuple(sorted((key(a), key(b)))), []).append(V[c])
        for (pa, pb), thirds in cnt.items():
            A, B = np.array(pa), np.array(pb)
            if inbox(A, 1) or inbox(B, 1): edges.append((A, B, si, len(thirds) == 1, thirds[0]))
    grid = {}
    for ei, (A, B, si, bnd, C) in enumerate(edges):
        for gx in range(int(math.floor(min(A[0], B[0]) - 0.01)), int(math.floor(max(A[0], B[0]) + 0.01)) + 1):   # (a margin: a vertex at
            for gy in range(int(math.floor(min(A[1], B[1]) - 0.01)), int(math.floor(max(A[1], B[1]) + 0.01)) + 1):   #  3107.99999 is on 3108)
                grid.setdefault((gx, gy), []).append(ei)
    found = []; seen = set()
    def meets(v, si, sj):
        """an edge of the surface v lies against (sj, or another one - never v's own) runs through v (2 mm across, 1 mm in
        height) or ends on it: the ground is closed there, a sliver merely dives past."""
        for ej in grid.get((int(math.floor(v[0])), int(math.floor(v[1]))), []):
            if edges[ej][2] == si: continue
            A, B = edges[ej][0], edges[ej][1]
            if np.linalg.norm(v - A) < 1e-3 or np.linalg.norm(v - B) < 1e-3: return True
            d = B[:2] - A[:2]; L2 = d @ d
            if L2 < 1e-10: continue
            t = ((v[:2] - A[:2]) @ d) / L2
            if 0 <= t <= 1:
                q = A + (B - A) * t
                if np.hypot(*(v[:2] - q[:2])) <= XY_TOL and abs(v[2] - q[2]) <= T_MIN: return True
        return False
    for si, (n, V, I) in enumerate(S):                             # (T)
        for v in V[np.unique(I)]:
            if not inbox(v) or hidden(v): continue
            kv = tuple(np.round(v, 3))
            if kv in seen: continue
            seen.add(kv)
            for ei in grid.get((int(math.floor(v[0])), int(math.floor(v[1]))), []):
                A, B, sj, bnd, C = edges[ei]
                d = B[:2] - A[:2]; L2 = d @ d
                if L2 < 1e-10: continue
                t = ((v[:2] - A[:2]) @ d) / L2
                if t <= 1e-4 or t >= 1 - 1e-4: continue
                q = A + (B - A) * t
                if np.hypot(*(v[:2] - q[:2])) > XY_TOL or not T_MIN < abs(v[2] - q[2]) <= T_MAX: continue
                if meets(v, si, sj): continue                                   # (another edge / vertex of the ground meets it there: a sliver
                found.append(('T', S[si][0], S[sj][0], v, float(v[2] - q[2])))   #  dives past, the surface is closed)
                break
    def met(p, ei0):
        """another edge (any surface) runs through the point p of edge ei0 - within 2 mm across and MATCH_Z in height."""
        for ej in grid.get((int(math.floor(p[0])), int(math.floor(p[1]))), []):
            if ej == ei0: continue
            A, B = edges[ej][0], edges[ej][1]; d = B[:2] - A[:2]; L2 = d @ d
            if L2 < 1e-10: continue
            t = ((p[:2] - A[:2]) @ d) / L2
            if t < -1e-4 or t > 1 + 1e-4: continue
            q = A + (B - A) * min(max(t, 0.0), 1.0)
            if np.hypot(*(p[:2] - q[:2])) <= XY_TOL and abs(p[2] - q[2]) <= MATCH_Z: return True
        return False
    for ei, (A, B, si, bnd, C) in enumerate(edges):              # (G)
        if not bnd or not (inbox(A) and inbox(B)) or on_hole(A, B): continue
        for t in (0.25, 0.5, 0.75):
            p = A + (B - A) * t
            if hidden(p): continue
            if not met(p, ei): found.append(('G', S[si][0], '', p, None)); break
    return found


def vanilla_open_edges():
    """Rockstar's own open edges in the terrain we reshape (as he ships it): an opening of his that we did not make or move."""
    H.export([VAN / f'{n}.ydr' for n in TERRAIN]); out = []
    for n, o in TERRAIN.items():
        hi = ET.parse(XMLD / f'{n}.ydr.xml').getroot().find('DrawableModelsHigh')
        for g in hi.iter('Item'):
            vb = g.find('VertexBuffer'); ib = g.find('IndexBuffer')
            if vb is None or ib is None: continue
            V = np.array([[float(a) for a in ln.split()[:3]] for ln in vb.find('Data').text.strip().splitlines()]) + np.array(o)
            I = np.array([int(a) for a in ib.find('Data').text.split()]).reshape(-1, 3); cnt = {}
            for t in I:
                for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    k = tuple(sorted((tuple(np.round(V[a], 4)), tuple(np.round(V[b], 4))))); cnt[k] = cnt.get(k, 0) + 1
            out += [(np.array(a), np.array(b)) for (a, b), c in cnt.items() if c == 1 and (inbox(a, 1) or inbox(b, 1))]
    return out


def rockstars(p, R):
    for A, B in R:
        d = B[:2] - A[:2]; L2 = d @ d
        if L2 < 1e-10: continue
        t = ((p[:2] - A[:2]) @ d) / L2
        if -1e-4 <= t <= 1 + 1e-4:
            q = A + (B - A) * t
            if np.hypot(*(p[:2] - q[:2])) <= XY_TOL and abs(p[2] - q[2]) <= MATCH_Z: return True
    return False


def main():
    R = vanilla_open_edges()
    S = surfaces(); print('CRACK_CHECK surfaces', len(S), ', '.join(n for n, _, _ in S), flush=True)
    found = find(S)
    own = [f for f in found if f[0] == 'G' and rockstars(f[3], R)]
    found = [f for f in found if not any(f is o for o in own)]
    for f in own: print(f'ROCKSTAR G {f[1]} open edge at ({f[3][0]:.3f}, {f[3][1]:.3f}, {f[3][2]:.3f}): his own, open in the shipped game too (not counted)')
    for kind, a, b, v, dz in found:
        if kind == 'T': print(f'CRACK T {a} vertex ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f}) on an edge of {b}, {dz * 1000:+.1f} mm off it')
        else: print(f'CRACK G {a} open edge at ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f}): no ground carries on from it')
    print('CRACK_CHECK', sum(1 for f in found if f[0] == 'T'), 'T-junctions,', sum(1 for f in found if f[0] == 'G'), 'gaps')
    json.dump([[f[0], f[1], f[2], [round(float(c), 3) for c in f[3]]] for f in found], open(M / 'site' / 'crack_check.json', 'w'))
    sys.exit(1 if found else 0)


if __name__ == '__main__': main()
