"""Set entity lodDist values in a CodeWalker ymap XML and recompute the ymap's streamingExtents.

usage: python ymap_loddist.py <in.ymap.xml> <out.ymap.xml> <radius.json> <index>=<lodDist> [...]

Edits text in place (only the lodDist value of the named entity indices and the streamingExtents lines change), so the
CodeWalker compile -> re-export round trip can be compared with this output byte for byte.
streamingExtents = union over every entity of position +- (lodDist + archetype bsRadius); an entity with lodDist 0 uses its
archetype's lodDist. radius.json maps archetype name (lower case, or hash_XXXXXXXX) -> [bsRadius, archetype lodDist].
An unknown archetype counts with radius 0 / its own lodDist and is listed.
entitiesExtentsMin/Max are not touched (they do not depend on lodDist).
"""
import json
import re
import sys

ITEM = re.compile(r'(<Item type="CEntityDef">.*?</Item>)', re.S)


def val(block, tag):
    m = re.search(r'<%s value="([^"]+)"' % tag, block)
    return float(m.group(1)) if m else None


def main():
    src, dst, radius_path = sys.argv[1:4]
    want = {int(k): float(v) for k, v in (a.split('=') for a in sys.argv[4:])}
    radius = {k.lower(): v for k, v in json.load(open(radius_path)).items()}
    text = open(src, encoding='utf-8').read()
    parts = ITEM.split(text)
    idx = -1
    lo = [1e30] * 3
    hi = [-1e30] * 3
    unknown = set()
    changed = []
    for i, p in enumerate(parts):
        if not p.startswith('<Item type="CEntityDef">'):
            continue
        idx += 1
        name = re.search(r'<archetypeName>([^<]*)</archetypeName>', p).group(1).lower()
        old = val(p, 'lodDist')
        if idx in want:
            new = want[idx]
            p = re.sub(r'<lodDist value="[^"]+"', '<lodDist value="%s"' % ('%g' % new), p, count=1)
            parts[i] = p
            changed.append((idx, name, old, new))
        lod = val(p, 'lodDist')
        r, alod = radius.get(name, (0.0, None))
        if name not in radius:
            unknown.add(name)
        if not lod and alod:
            lod = alod
        pos = re.search(r'<position x="([^"]+)" y="([^"]+)" z="([^"]+)"', p).groups()
        for k in range(3):
            c = float(pos[k])
            lo[k] = min(lo[k], c - lod - r)
            hi[k] = max(hi[k], c + lod + r)
    missing = set(want) - {c[0] for c in changed}
    if missing:
        sys.exit('entity index not found: %s' % sorted(missing))
    out = ''.join(parts)

    def fmt(v):
        return ('%.7g' % v)
    out, n1 = re.subn(r'<streamingExtentsMin x="[^"]+" y="[^"]+" z="[^"]+" />',
                      '<streamingExtentsMin x="%s" y="%s" z="%s" />' % tuple(fmt(v) for v in lo), out)
    out, n2 = re.subn(r'<streamingExtentsMax x="[^"]+" y="[^"]+" z="[^"]+" />',
                      '<streamingExtentsMax x="%s" y="%s" z="%s" />' % tuple(fmt(v) for v in hi), out)
    if n1 != 1 or n2 != 1:
        sys.exit('streamingExtents lines not found')
    open(dst, 'w', encoding='utf-8', newline='').write(out)
    for c in changed:
        print('entity %d %s lodDist %g -> %g' % c)
    print('streamingExtents %s .. %s' % ([round(v, 1) for v in lo], [round(v, 1) for v in hi]))
    if unknown:
        print('archetypes without radius (counted as 0): %d, e.g. %s' % (len(unknown), sorted(unknown)[:5]))


if __name__ == '__main__':
    main()
