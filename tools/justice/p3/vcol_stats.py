"""Vertex colour 0 / 1 of Rockstar's interior drawables (CodeWalker ydr XML), per surface class: floor (normal up), ceiling (normal
down), wall (horizontal normal), with the shader each uses. Interiors: R = natural ambient, G = artificial ambient (the baked
interior light), B = a third term (0 in most shells). Our interior meshes copy these medians per surface (never the 1.0 default).
Usage: py -3 vcol_stats.py <dir of *.ydr.xml> [names...]   -> prints a table + writes vcol_stats.json beside the XML."""
import sys, re, json, statistics as st
from pathlib import Path
import xml.etree.ElementTree as ET
def geoms(path):
    r = ET.parse(path).getroot(); shaders = [s.findtext('FileName') for s in r.iter('Shaders') for s in s.findall('Item')]
    for g in r.iter('Geometries'):
        for it in g.findall('Item'):
            si = int(it.find('ShaderIndex').get('value')); vb = it.find('VertexBuffer'); lay = [c.tag for c in vb.find('Layout')]
            if 'Colour0' not in lay: continue
            yield shaders[si] if si < len(shaders) else '?', lay, vb.findtext('Data') or ''
WIDTH = {'Position': 3, 'Normal': 3, 'Colour0': 4, 'Colour1': 4, 'TexCoord0': 2, 'TexCoord1': 2, 'TexCoord2': 2, 'TexCoord3': 2, 'Tangent': 4, 'BlendWeights': 4, 'BlendIndices': 4}
def main(d, names):
    out = {}
    files = [Path(d) / f'{n}.ydr.xml' for n in names] if names else sorted(Path(d).glob('*.ydr.xml'))
    for f in files:
        acc = {}
        for sh, lay, data in geoms(f):
            for line in data.strip().splitlines():
                parts = [p.split() for p in line.strip().split('   ')]
                rec = dict(zip(lay, parts))
                if 'Normal' not in rec: continue
                nz = float(rec['Normal'][2]); cls = 'floor' if nz > 0.7 else 'ceiling' if nz < -0.7 else 'wall'
                c0 = tuple(int(x) for x in rec['Colour0']); c1 = tuple(int(x) for x in rec['Colour1']) if 'Colour1' in rec else None
                a = acc.setdefault((cls, sh), {'c0': [], 'c1': []}); a['c0'].append(c0)
                if c1: a['c1'].append(c1)
        res = {}
        for (cls, sh), a in sorted(acc.items()):
            med = lambda L, i: st.median(x[i] for x in L) if L else None
            res[f'{cls}|{sh}'] = {'n': len(a['c0']), 'c0': [med(a['c0'], i) for i in range(4)], 'c1': [med(a['c1'], i) for i in range(4)] if a['c1'] else None}
            print(f.name[:-8].ljust(34), cls.ljust(8), sh.ljust(28), str(len(a['c0'])).rjust(6), 'c0', res[f'{cls}|{sh}']['c0'], 'c1', res[f'{cls}|{sh}']['c1'])
        out[f.name[:-8]] = res
    json.dump(out, open(Path(d) / 'vcol_stats.json', 'w'), indent=1)
if __name__ == '__main__': main(sys.argv[1], sys.argv[2:])
