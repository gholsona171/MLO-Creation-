import xml.etree.ElementTree as ET
def load(p):
    r = ET.parse(p).getroot().find('Bounds'); kids = []
    for ch in r.find('Children'):
        gc = ch.find('GeometryCenter'); c = tuple(float(gc.get(a)) for a in 'xyz')
        verts = [tuple(float(x) + c[i] for i, x in enumerate(l.split(','))) for l in ch.find('Vertices').text.strip().splitlines()]
        mats = [int(m.find('Type').get('value')) for m in ch.find('Materials')]
        polys = []
        for p in ch.find('Polygons'):
            vk = [k for k in p.attrib if k.startswith('v')]
            pts = [verts[int(p.get(k))] for k in sorted(vk)]
            extra = tuple(sorted((k, p.get(k)) for k in p.attrib if not k.startswith('v') and k not in ('m','f1','f2','f3')))
            polys.append((p.tag, mats[int(p.get('m'))], pts, extra))
        bb = lambda t: tuple(round(float(ch.find(t).get(a)), 2) for a in 'xyz')
        kids.append(dict(bmin=bb('BoxMin'), bmax=bb('BoxMax'), f1=ch.findtext('CompositeFlags1'), f2=ch.findtext('CompositeFlags2'), nv=len(verts), polys=polys, nmat=len(mats)))
    return kids
