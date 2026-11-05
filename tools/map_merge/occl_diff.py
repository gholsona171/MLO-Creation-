import sys, math, hashlib, xml.etree.ElementTree as ET
def load(p):
    r = ET.parse(p).getroot()
    boxes = []
    for it in r.find('boxOccluders'):
        boxes.append(tuple(int(it.find(k).get('value')) for k in ['iCenterX','iCenterY','iCenterZ','iCosZ','iLength','iWidth','iHeight','iSinZ']))
    models = []
    for it in r.find('occludeModels'):
        bmin = tuple(float(it.find('bmin').get(a)) for a in 'xyz'); bmax = tuple(float(it.find('bmax').get(a)) for a in 'xyz')
        v = ''.join(it.find('verts').text.split())
        models.append(dict(bmin=bmin, bmax=bmax, h=hashlib.md5(v.encode()).hexdigest()[:10], size=it.find('dataSize').get('value'), tris=it.find('numTris').get('value'), nv=it.find('numVertsInBytes').get('value'), flags=it.find('flags').get('value')))
    hdr = {k: tuple(r.find(k).attrib.values()) for k in ['streamingExtentsMin','streamingExtentsMax','entitiesExtentsMin','entitiesExtentsMax']}
    hdr['flags'] = r.find('flags').get('value'); hdr['contentFlags'] = r.find('contentFlags').get('value')
    return boxes, models, hdr
def bdesc(b):
    cx,cy,cz,c,l,w,h,s = b; a = math.degrees(math.atan2(s, c))
    return f"centre ({cx/4:.1f}, {cy/4:.1f}, {cz/4:.1f}) L{l/4:.1f} W{w/4:.1f} H{h/4:.1f} rot {a:.0f}deg"
def mdesc(m): return f"x {m['bmin'][0]:.1f}..{m['bmax'][0]:.1f} y {m['bmin'][1]:.1f}..{m['bmax'][1]:.1f} z {m['bmin'][2]:.1f}..{m['bmax'][2]:.1f} tris={m['tris']} verts#{m['h']}"
V = load(sys.argv[1])
for p in sys.argv[2:]:
    B, M, H = load(p); print('=====', p); print(f'boxes {len(B)} (vanilla {len(V[0])}), models {len(M)} (vanilla {len(V[1])})')
    for k in H:
        if H[k] != V[2][k]: print(f'  header {k}: vanilla {V[2][k]} -> {H[k]}')
    vb = list(V[0]); removed = [b for b in vb if b not in B]; added = [b for b in B if b not in vb]
    print(f'  boxes removed {len(removed)}, added {len(added)}, order same for kept: {[b for b in vb if b in B] == [b for b in B if b in vb]}')
    xs = [b[0]/4 for b in removed]; ys = [b[1]/4 for b in removed]
    if removed: print(f'  removed boxes centre span x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f}')
    for b in removed: print('   - ' + bdesc(b))
    for b in added: print('   + ' + bdesc(b))
    vh = [m['h'] for m in V[1]]
    for i, m in enumerate(V[1]):
        hits = [j for j, n in enumerate(M) if n['h'] == m['h']]
        if not hits: print(f'  vanilla model #{i} {mdesc(m)} : CHANGED/REMOVED')
    for j, n in enumerate(M):
        if n['h'] not in vh: print(f'  new/changed model #{j} {mdesc(n)}')
