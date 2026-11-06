# Hood exterior footprints: archetype bbox (hood_exterior_f_va_metadata2) rotated to each placement in hood_exterior_f_va_placement
import sys, math, xml.etree.ElementTree as ET
def footprints(ymap_xml, ytyp_xml, sign):
    a = ET.parse(ytyp_xml).getroot().find('archetypes')[0]
    lo = [float(a.find('bbMin').get(k)) for k in 'xyz']; hi = [float(a.find('bbMax').get(k)) for k in 'xyz']
    out = []
    for i, e in enumerate(ET.parse(ymap_xml).getroot().find('entities')):
        p = [float(e.find('position').get(k)) for k in 'xyz']; q = e.find('rotation').attrib
        yaw = sign * 2 * math.atan2(float(q['z']), float(q['w']))
        c, s = math.cos(yaw), math.sin(yaw)
        corners = [(p[0] + c * x - s * y, p[1] + s * x + c * y) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
        out.append(dict(i=i + 1, pos=p, yaw=math.degrees(yaw), poly=corners, z=(p[2] + lo[2], p[2] + hi[2])))
    return out
if __name__ == '__main__':
    for sign in (1, -1):
        F = footprints(sys.argv[1], sys.argv[2], sign)
        xs = [x for f in F for x, y in f['poly']]; ys = [y for f in F for x, y in f['poly']]
        print('sign', sign, 'union x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (min(xs), max(xs), min(ys), max(ys), min(f['z'][0] for f in F), max(f['z'][1] for f in F)))
