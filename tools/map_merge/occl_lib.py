# Occluder XML (CodeWalker MetaXml) reader: box occluders and occlude-model triangles, plus world-space helpers.
import math, struct, xml.etree.ElementTree as ET
def load_occl(p):
    r = ET.parse(p).getroot()
    boxes = []
    for it in r.find('boxOccluders'):
        g = {c.tag: int(c.get('value')) for c in it}
        boxes.append(g)
    models = []
    for it in r.find('occludeModels'):
        raw = bytes.fromhex(''.join(it.find('verts').text.split()))
        nvb = int(it.find('numVertsInBytes').get('value')); nt = int(it.find('numTris').get('value')) & 0x7FFF
        V = [struct.unpack_from('<3f', raw, i) for i in range(0, nvb, 12)]
        I = raw[nvb:nvb + nt * 3]
        tris = [tuple(V[I[k + j]] for j in range(3)) for k in range(0, nt * 3, 3)]
        models.append(dict(bmin=tuple(float(it.find('bmin').get(a)) for a in 'xyz'), bmax=tuple(float(it.find('bmax').get(a)) for a in 'xyz'),
                           tris=tris, flags=it.find('flags').get('value'), raw_ok=(len(raw) == int(it.find('dataSize').get('value')))))
    name = r.find('name').text if r.find('name') is not None else None
    parent = r.find('parent').text if r.find('parent') is not None else None
    return dict(boxes=boxes, models=models, name=name, parent=parent, root=r)
def box_key(g): return (g['iCenterX'], g['iCenterY'], g['iCenterZ'], g['iLength'], g['iWidth'], g['iHeight'])
def box_eq(a, b): return box_key(a) == box_key(b) and abs(a['iCosZ'] - b['iCosZ']) <= 2 and abs(a['iSinZ'] - b['iSinZ']) <= 2
def box_poly(g):
    cx, cy, cz = g['iCenterX'] / 4, g['iCenterY'] / 4, g['iCenterZ'] / 4; L, W, H = g['iLength'] / 4, g['iWidth'] / 4, g['iHeight'] / 4
    a = math.atan2(g['iSinZ'], g['iCosZ']); c, s = math.cos(a), math.sin(a)
    return [(cx + c * x - s * y, cy + s * x + c * y) for x, y in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2))], cz - H / 2, cz + H / 2
def box_desc(g):
    return f"({g['iCenterX']/4:.1f}, {g['iCenterY']/4:.1f}, {g['iCenterZ']/4:.1f}) L{g['iLength']/4:.1f} W{g['iWidth']/4:.1f} H{g['iHeight']/4:.1f} rot {math.degrees(math.atan2(g['iSinZ'], g['iCosZ'])):.0f}"
def tri_key(t): return frozenset((round(p[0], 3), round(p[1], 3), round(p[2], 3)) for p in t)
def tri_desc(t):
    xs = [p[0] for p in t]; ys = [p[1] for p in t]; zs = [p[2] for p in t]
    return f"x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f} z {min(zs):.1f}..{max(zs):.1f}"
def model_desc(m): return f"x {m['bmin'][0]:.1f}..{m['bmax'][0]:.1f} y {m['bmin'][1]:.1f}..{m['bmax'][1]:.1f} z {m['bmin'][2]:.1f}..{m['bmax'][2]:.1f} ({len(m['tris'])} tris)"
def _axes(poly):
    return [(-(poly[(i + 1) % len(poly)][1] - poly[i][1]), poly[(i + 1) % len(poly)][0] - poly[i][0]) for i in range(len(poly))]
def separated(a, b):
    for ax in _axes(a) + _axes(b):
        if ax == (0, 0) or ax == (0.0, 0.0): continue
        pa = [ax[0] * x + ax[1] * y for x, y in a]; pb = [ax[0] * x + ax[1] * y for x, y in b]
        if max(pa) < min(pb) or max(pb) < min(pa): return True
    return False
def hits(poly, z0, z1, F):
    return [f['id'] for f in F if z1 >= f['z'][0] and z0 <= f['z'][1] and not separated(poly, f['poly'])]
def quat_yaw(q, sign=-1):  # CEntityDef rotation is stored inverted: world yaw = -stored yaw
    return sign * 2 * math.atan2(q['z'], q['w'])
def oriented(pos, yaw, lo, hi, scale=(1, 1, 1)):
    c, s = math.cos(yaw), math.sin(yaw)
    pts = ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))
    return [(pos[0] + c * x * scale[0] - s * y * scale[0], pos[1] + s * x * scale[0] + c * y * scale[0]) for x, y in pts], (pos[2] + lo[2] * scale[2], pos[2] + hi[2] * scale[2])
