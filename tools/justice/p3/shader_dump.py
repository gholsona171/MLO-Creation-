"""Rockstar's materials in a CodeWalker ydr XML: per shader the file, bucket, samplers (texture names) and parameters, plus how many
floor / wall / ceiling vertices use it (to pick his recipe for a surface). Usage: py -3 shader_dump.py file.ydr.xml [min_verts]"""
import sys
import xml.etree.ElementTree as ET
r = ET.parse(sys.argv[1]).getroot(); mn = int(sys.argv[2]) if len(sys.argv) > 2 else 0
shaders = [s for S in r.iter('Shaders') for s in S.findall('Item')]
use = {}
for g in r.iter('Geometries'):
    for it in g.findall('Item'):
        si = int(it.find('ShaderIndex').get('value')); vb = it.find('VertexBuffer'); lay = [c.tag for c in vb.find('Layout')]
        ni = lay.index('Normal') if 'Normal' in lay else None
        for line in (vb.findtext('Data') or '').strip().splitlines():
            if ni is None: continue
            nz = float(line.strip().split('   ')[ni].split()[2]); c = 'F' if nz > .7 else 'C' if nz < -.7 else 'W'
            u = use.setdefault(si, {'F': 0, 'W': 0, 'C': 0}); u[c] += 1
for i, s in enumerate(shaders):
    u = use.get(i, {'F': 0, 'W': 0, 'C': 0})
    if sum(u.values()) < mn: continue
    tex = {p.get('name'): p.findtext('Name') for p in s.find('Parameters') if p.get('type') == 'Texture'}
    par = {p.get('name'): p.get('x') for p in s.find('Parameters') if p.get('type') == 'Vector' and p.get('name') not in ('HardAlphaBlend', 'useTessellation', 'wetnessMultiplier', 'globalAnimUV0', 'globalAnimUV1')}
    print(i, s.findtext('FileName'), 'bucket', s.find('RenderBucket').get('value'), u, tex, par)
