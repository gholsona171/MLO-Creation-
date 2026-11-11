"""mlo_world_coords.py: a bought / escrowed MLO's rooms, exit portals and named entities in WORLD coordinates, from its readable
ytyp + the MLO instance in its ymap (both are often plain RSC7 even when every ydr is FXAP). Use it to find the entrance, front
desk, courtrooms ... before going in game (brnx_courthouse, 2026-11-11).
  1. export:  powershell -File tools/map_merge/ytyp_xml.ps1 <x.ytyp> <x.ytyp.xml>; tools/map_merge/cwxml.ps1 export <x.ymap> <x.ymap.xml>
  2. read the CMloInstanceDef position + rotation (z, w) from the ymap XML
  3. py -3 -I mlo_world_coords.py <x.ytyp.xml> <stream folder> <px> <py> <pz> <qz> <qw> [extra model names...]
Model names are resolved by joaat of every file name under <stream folder>. MLO instance rotation is NOT inverted (checked against the
author's own entrance coords); child entity headings are (inverted child rotation + MLO heading). EXIT PORTAL lines = doors to outside.
"""
import sys, os, re, math, xml.etree.ElementTree as ET
ytyp, stream, px, py, pz, qz, qw = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8])
def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF
    return h
names = {}
for d, _, fs in os.walk(stream):
    for f in fs: names[f'hash_{joaat(os.path.splitext(f)[0]):08X}'] = os.path.splitext(f)[0]
for extra in sys.argv[8:]: names[f'hash_{joaat(extra):08X}'] = extra
ang = 2*math.atan2(qz, qw)
def w(x, y, z):
    c, s = math.cos(ang), math.sin(ang); return (round(px + c*x - s*y, 2), round(py + s*x + c*y, 2), round(pz + z, 2))
r = ET.parse(ytyp).getroot()
for a in r.iter('Item'):
    if a.get('type') != 'CMloArchetypeDef': continue
    ents = a.find('entities').findall('Item'); rooms = a.find('rooms').findall('Item')
    room_of = {}
    for i, rm in enumerate(rooms):
        for j in (rm.findtext('attachedObjects') or '').split(): room_of[int(j)] = rm.findtext('name')
    for j, e in enumerate(ents):
        n = e.findtext('archetypeName'); p = e.find('position')
        q = e.find('rotation'); h = math.degrees(-2*math.atan2(float(q.get('z')), float(q.get('w'))) + ang)
        print('ENT', room_of.get(j, '-'), names.get(n, n), w(float(p.get('x')), float(p.get('y')), float(p.get('z'))), 'hdg', round(h % 360, 1))
    for i, p in enumerate(a.find('portals').findall('Item')):
        cs = [tuple(map(float, it.text.split(',')[:3])) for it in p.find('corners').findall('Item')]
        c = [sum(v[k] for v in cs)/len(cs) for k in range(3)]
        rf, rt = int(p.find('roomFrom').get('value')), int(p.find('roomTo').get('value'))
        if rt == 0 or rf == 0:
            print('EXIT PORTAL', i, rooms[rf].findtext('name'), '->', rooms[rt].findtext('name'), 'world', w(*c), 'floor', w(*c[:2], min(v[2] for v in cs))[2], 'width', round(max(math.dist(cs[0][:2], v[:2]) for v in cs),2))
