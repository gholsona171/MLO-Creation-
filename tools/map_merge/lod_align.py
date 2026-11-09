# Check a LOD-light pair for index alignment: which hashes the lod file removed vs which positions the dist file removed (vs vanilla)
import sys, os, xml.etree.ElementTree as ET
d, X = sys.argv[1], sys.argv[2]
def L(who):
    l = ET.parse(f'{d}/{who}__vw_lodlights_{X}.ymap.xml').getroot().find('LODLightsSOA')
    D = ET.parse(f'{d}/{who}__vw_distlodlights_{X}.ymap.xml').getroot().find('DistantLODLightsSOA')
    h = l.find('hash').text.split()
    pos = [tuple(round(float(it.find(a).get('value')), 2) for a in 'xyz') for it in D.find('position')]
    return h, pos, int(D.find('numStreetLights').get('value'))
vh, vp, vns = L('vanilla')
for who in sys.argv[3:]:
    h, p, ns = L(who)
    rh = [i for i, x in enumerate(vh) if x not in set(h)]
    sp = set(p); rp = [i for i, x in enumerate(vp) if x not in sp]
    print(f'{who}: lod hashes removed at vanilla idx {rh}')
    print(f'{" " * len(who)}  dist positions removed at vanilla idx {rp}   street {vns}->{ns}')
    # aligned if remaining order identical
    kh = [i for i, x in enumerate(vh) if x in set(h)]; kp = [i for i, x in enumerate(vp) if x in sp]
    print('  aligned:', kh == kp, ' lod order kept:', [vh[i] for i in kh] == h, ' dist order kept:', [vp[i] for i in kp] == p)
