"""Justice Center: CodeWalker ybn XML -> world-space triangles (pure python + numpy).
Triangles as stored (material = the game material Type of the child's material list); Box primitives as their 12 hull triangles (4 alternate corners + their reflections through the centre);
spheres / capsules / cylinders as their bounding boxes (kind 2, a ray down sees a trunk or a pole) and their centres (prims). Vertices are relative to each child's GeometryCenter, then the
child's CompositeTransform (row vectors) is applied (doc 12 trap)."""
import re, numpy as np
from scipy.spatial import ConvexHull
NUM = r'(-?[\d.]+(?:E[-+]?\d+)?)'
def read(path):
    xml = open(path, encoding='utf-8').read(); tris = []; mats = []; kind = []; prims = []
    for ch in re.finditer(r'<Item type="Geometry(?:BVH)?">(.*?)</Polygons>', xml, re.S):
        b = ch.group(1)
        m = re.search(r'<CompositeTransform>(.*?)</CompositeTransform>', b, re.S)
        T = np.array([float(v) for v in m.group(1).split()]).reshape(4, 4) if m else np.eye(4)
        g = re.search(r'<GeometryCenter x="%s" y="%s" z="%s"' % (NUM, NUM, NUM), b)
        gc = np.array([float(g.group(i)) for i in (1, 2, 3)]) if g else np.zeros(3)
        vt = re.search(r'<Vertices>(.*?)</Vertices>', b, re.S)
        if not vt or not vt.group(1).strip(): continue
        V = np.array([[float(c) for c in l.split(',')] for l in vt.group(1).strip().splitlines()]) + gc
        V = V @ T[:3, :3] + T[3, :3]
        mb = re.search(r'<Materials>(.*?)</Materials>', b, re.S)
        mt = [int(v) for v in re.findall(r'<Type value="(\d+)"', mb.group(1))] if mb else []
        MT = lambda i: mt[i] if i < len(mt) else -1                       # the child's material index -> the game material (Type)
        for t in re.finditer(r'<Triangle m="(\d+)" v1="(\d+)" v2="(\d+)" v3="(\d+)"', b):
            tris.append(V[[int(t.group(2)), int(t.group(3)), int(t.group(4))]]); mats.append(MT(int(t.group(1)))); kind.append(0)
        for t in re.finditer(r'<Box m="(\d+)" v1="(\d+)" v2="(\d+)" v3="(\d+)" v4="(\d+)"', b):
            P = V[[int(t.group(i)) for i in (2, 3, 4, 5)]]; c = P.mean(0); C = np.vstack([P, 2 * c - P])
            try:
                h = ConvexHull(C)
                for s in h.simplices:
                    tri = C[s]; n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                    if np.dot(n, tri.mean(0) - c) < 0: tri = tri[[0, 2, 1]]          # outward winding
                    tris.append(tri); mats.append(MT(int(t.group(1)))); kind.append(1)
            except Exception: pass
        for t in re.finditer(r'<(Sphere|Capsule|Cylinder) m="(\d+)" v1="(\d+)"(?: v2="(\d+)")? radius="([\d.Ee+-]+)"', b):
            a = V[int(t.group(3))]; e = V[int(t.group(4))] if t.group(4) else a; r = float(t.group(5))
            prims.append((t.group(1), (a + e) / 2))
            lo = np.minimum(a, e) - r; hi = np.maximum(a, e) + r                 # as its bounding box (12 triangles, outward): a ray sees it
            C = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            h = ConvexHull(C); c = C.mean(0)
            for sx in h.simplices:
                tri = C[sx]; n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                if np.dot(n, tri.mean(0) - c) < 0: tri = tri[[0, 2, 1]]
                tris.append(tri); mats.append(MT(int(t.group(2)))); kind.append(2)
    return (np.array(tris) if tris else np.zeros((0, 3, 3))), np.array(mats, int), np.array(kind, int), prims
