# LOD light pair (vw_lodlights_X + vw_distlodlights_X) <-> per-light records; diff vs vanilla keyed by the light's hash
import xml.etree.ElementTree as ET
LOD_LISTS = ['falloff', 'falloffExponent', 'timeAndStateFlags', 'hash', 'coneInnerAngle', 'coneOuterAngleOrCapExt', 'coronaIntensity']
def xyz(el): return [tuple(it.find(a).get('value') for a in 'xyz') for it in el]
def load(lod_xml, dist_xml):
    L = ET.parse(lod_xml).getroot().find('LODLightsSOA'); D = ET.parse(dist_xml).getroot().find('DistantLODLightsSOA')
    cols = {'direction': xyz(L.find('direction')), 'position': xyz(D.find('position')), 'RGBI': (D.find('RGBI').text or '').split()}
    for k in LOD_LISTS: cols[k] = (L.find(k).text or '').split()
    n = len(cols['hash']); assert all(len(v) == n for v in cols.values()), {k: len(v) for k, v in cols.items()}
    recs = [{k: cols[k][i] for k in cols} for i in range(n)]
    ns = int(D.find('numStreetLights').get('value'))
    for i, r in enumerate(recs): r['street'] = i < ns
    return recs, ns, D.find('category').get('value')
def same(a, b, tol=1e-3):
    for k in a:
        x, y = a[k], b[k]
        if isinstance(x, tuple):
            if any(abs(float(p) - float(q)) > tol for p, q in zip(x, y)): return False
        elif x != y: return False
    return True
def diff(V, A):
    vk = {}; [vk.setdefault(r['hash'], []).append(r) for r in V]
    ak = {}; [ak.setdefault(r['hash'], []).append(r) for r in A]
    rem, add, chg = [], [], []
    for h, vs in vk.items():
        as_ = ak.get(h, [])
        if len(vs) == 1 and len(as_) == 1:
            if not same(vs[0], as_[0]): chg.append((vs[0], as_[0]))
        elif len(vs) != len(as_) or not all(any(same(v, a) for a in as_) for v in vs):
            # duplicate hashes: match by full record
            left = list(as_)
            for v in vs:
                m = next((a for a in left if same(v, a)), None)
                if m: left.remove(m)
                else: rem.append(v)
            add.extend(left)
    for h, as_ in ak.items():
        if h not in vk: add.extend(as_)
    return rem, add, chg
