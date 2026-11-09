# Variant-aware occluder merge (field note 2026-11-06): apply every pack's occluder edits to ANY variant of the same occluder file
# (sc1_occl_00 / hei_sc1_occl_00 / lr_sc1_occl_00 ...), matching by geometry, never by index. The variants are not byte-identical
# (different box sets, different models), so an index-based copy would cut the wrong things.
#
#   occl_variant_merge.py --target <vanilla variant .ymap.xml> --out <out .ymap.xml>
#                         --author NAME <author .ymap.xml> <the file that author started from .ymap.xml>  (repeat)
#
# Each author's edit = author file vs its own base (box removed / box added / whole model deleted / triangles removed).
# Boxes match on centre + size exactly and iCosZ/iSinZ within +-2 (CodeWalker re-derives them on save). Models match on their
# exact triangle set. Triangle removals find the target model that holds all those triangles. Anything else STOPS (exit 1):
# an author ADDING triangles, a deleted model or cut triangles not present in the target. A removed box missing from the target is
# reported (nothing to remove there) - check the report. Everything else in the target (all other boxes, every untouched model,
# header) is kept byte-for-byte as the target's XML has it. Removed triangles compact the model's vertices (used vertices in their
# original order) and recompute bmin/bmax, like CodeWalker's RemoveOccludeModelTriangle. Import the result with ymap_import.ps1.
import sys, struct, copy, argparse, xml.etree.ElementTree as ET

def boxes_of(root): return list(root.find('boxOccluders'))
def bvals(it): return {c.tag: int(c.get('value')) for c in it}
def bkey(g): return (g['iCenterX'], g['iCenterY'], g['iCenterZ'], g['iLength'], g['iWidth'], g['iHeight'])
def beq(a, b): return bkey(a) == bkey(b) and abs(a['iCosZ'] - b['iCosZ']) <= 2 and abs(a['iSinZ'] - b['iSinZ']) <= 2
def bdesc(g):
    import math
    return f"({g['iCenterX']/4:.2f}, {g['iCenterY']/4:.2f}, {g['iCenterZ']/4:.2f}) L{g['iLength']/4:.2f} W{g['iWidth']/4:.2f} H{g['iHeight']/4:.2f} rot {math.degrees(math.atan2(g['iSinZ'], g['iCosZ'])):.0f}"
def mdecode(it):
    raw = bytes.fromhex(''.join(it.find('verts').text.split()))
    nvb = int(it.find('numVertsInBytes').get('value')); nt = int(it.find('numTris').get('value')) & 0x7FFF
    V = [struct.unpack_from('<3f', raw, i) for i in range(0, nvb, 12)]
    I = list(raw[nvb:nvb + nt * 3])
    return V, I
def tkey(V, I, t): return frozenset((round(V[I[t*3+j]][0], 3), round(V[I[t*3+j]][1], 3), round(V[I[t*3+j]][2], 3)) for j in range(3))
def tset(it): V, I = mdecode(it); return {tkey(V, I, t) for t in range(len(I) // 3)}
def tdesc(k):
    xs = [p[0] for p in k]; ys = [p[1] for p in k]; zs = [p[2] for p in k]
    return f"x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f} z {min(zs):.1f}..{max(zs):.1f}"
def mdesc(it):
    a = it.find('bmin').attrib; b = it.find('bmax').attrib
    return f"x {float(a['x']):.1f}..{float(b['x']):.1f} y {float(a['y']):.1f}..{float(b['y']):.1f} z {float(a['z']):.1f}..{float(b['z']):.1f} ({len(tset(it))} tris)"

def author_edits(name, ap, bp):
    A = ET.parse(ap).getroot(); B = ET.parse(bp).getroot()
    ab = [bvals(x) for x in boxes_of(A)]; bb = [bvals(x) for x in boxes_of(B)]
    rem = [g for g in bb if not any(beq(g, x) for x in ab)]
    add = [(g, it) for g, it in zip(ab, boxes_of(A)) if not any(beq(g, x) for x in bb)]
    am = [tset(m) for m in A.find('occludeModels')]; bm = [tset(m) for m in B.find('occludeModels')]
    deleted, cuts = [], []
    for i, s in enumerate(bm):
        if s in am: continue
        best = max(range(len(am)), key=lambda j: len(s & am[j])) if am else None
        if best is None or not (s & am[best]): deleted.append(s)            # nothing of it left: whole model deleted
        elif am[best] <= s: cuts.append((s, s - am[best]))                   # pure triangle removal
        else: sys.exit(f'STOP: {name} changed model #{i} in a way that is not a pure triangle removal')
    for j, s in enumerate(am):
        if not any(s <= x for x in bm): sys.exit(f'STOP: {name} model #{j} has triangles that are not in its base (added geometry) - not handled')
    return dict(name=name, rem=rem, add=add, deleted=deleted, cuts=cuts)

def rebuild_model(it, drop):
    V, I = mdecode(it); keep = [t for t in range(len(I) // 3) if tkey(V, I, t) not in drop]
    remap = {}                                    # vertices in first-use order of the kept triangles (what CodeWalker writes)
    for t in keep:
        for j in range(3): remap.setdefault(I[t*3+j], len(remap))
    NV = [V[o] for o in remap]; NI = [remap[I[t*3+j]] for t in keep for j in range(3)]
    raw = b''.join(struct.pack('<3f', *v) for v in NV) + bytes(NI)
    hexs = ' '.join(f'{b:02X}' for b in raw)
    it.find('verts').text = '\n' + '\n'.join('    ' + hexs[i:i + 96] for i in range(0, len(hexs), 96)) + '\n   '
    it.find('dataSize').set('value', str(len(raw))); it.find('numVertsInBytes').set('value', str(len(NV) * 12))
    flag = int(it.find('numTris').get('value')) & 0x8000
    it.find('numTris').set('value', str(flag | len(keep)))
    def f(v):                                     # float32 as CodeWalker writes it: 7 digits if that round-trips, else 9
        s = '%.7g' % v
        return s if struct.pack('<f', float(s)) == struct.pack('<f', v) else '%.9g' % v
    for tag, fn in (('bmin', min), ('bmax', max)):
        for k, ax in zip('xyz', range(3)): it.find(tag).set(k, f(fn(v[ax] for v in NV)))
    return len(I) // 3 - len(keep)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--target', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--author', nargs=3, action='append', metavar=('NAME', 'AUTHOR_XML', 'BASE_XML'), required=True)
    a = ap.parse_args()
    tree = ET.parse(a.target); T = tree.getroot(); TB = T.find('boxOccluders'); TM = T.find('occludeModels')
    print(f"target {T.find('name').text}: {len(TB)} boxes, {len(TM)} models")
    E = [author_edits(*x) for x in a.author]
    # 1. whole-model deletions first (they cover any other author's triangle cuts in the same model)
    gone = []
    for e in E:
        for s in e['deleted']:
            hit = [m for m in TM if tset(m) == s]
            if not hit:
                if s in gone: print(f"  {e['name']}: model already deleted"); continue
                sys.exit(f"STOP: {e['name']} deleted a model ({len(s)} tris) that this variant does not have identically")
            print(f"  {e['name']}: model deleted {mdesc(hit[0])}"); TM.remove(hit[0]); gone.append(s)
    # 2. boxes
    bgone = []
    for e in E:
        for g in e['rem']:
            hit = [it for it in TB if beq(bvals(it), g)]
            if hit: TB.remove(hit[0]); bgone.append(g); print(f"  {e['name']}: box removed {bdesc(g)}")
            elif any(beq(g, x) for x in bgone): print(f"  {e['name']}: box {bdesc(g)} already removed by an earlier author (covered)")
            else: print(f"  {e['name']}: box {bdesc(g)} NOT IN THIS VARIANT (nothing removed)")
        for g, it in e['add']:
            if any(beq(bvals(x), g) for x in TB): print(f"  {e['name']}: box already present {bdesc(g)}"); continue
            TB.append(copy.deepcopy(it)); print(f"  {e['name']}: box added {bdesc(g)}")
    # 3. triangle cuts. Two authors may cut the same triangles (a pack whose file already holds another pack's cut): triangles an
    #    earlier author already removed are covered, the rest must still sit in one model.
    done = set()
    for e in E:
        for s, drop in e['cuts']:
            if any(s == x for x in gone): print(f"  {e['name']}: {len(drop)} cut triangles fall in a model already deleted (covered)"); continue
            if drop & done:
                print(f"  {e['name']}: {len(drop & done)} of its {len(drop)} cut triangles already removed by an earlier author (covered)")
                drop = drop - done
                if not drop: continue
            hit = [m for m in TM if drop <= tset(m)]
            if len(hit) != 1: sys.exit(f"STOP: {e['name']}'s {len(drop)} cut triangles are not all in one model of this variant")
            done |= drop
            n = rebuild_model(hit[0], drop); print(f"  {e['name']}: {n} triangles removed from model {mdesc(hit[0])}")
            for k in sorted(drop, key=lambda k: min(p[0] for p in k)): print(f"      - {tdesc(k)}")
    TB.set('itemType', TB.get('itemType') or 'BoxOccluder')
    tree.write(a.out, encoding='UTF-8', xml_declaration=True)
    print(f"saved {a.out}: {len(TB)} boxes, {len(TM)} models")
if __name__ == '__main__': main()
