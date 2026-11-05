# Merged ymap XML: base author's XML; each entity the other author changed vs vanilla (by guid) is replaced with the other author's Item verbatim.
# Stops if both authors changed the same entity, or if the other author added / removed entities (not handled here).
import sys, xml.etree.ElementTree as ET
van, base, other, out = sys.argv[1:5]
def items(r): return {it.find('guid').get('value'): it for it in r.find('entities')}
def norm(it): return ' '.join(ET.tostring(it).decode().split())
def near(a, b):
    import re
    fa = re.findall(r'-?\d+\.?\d*(?:E-?\d+)?', norm(a)); fb = re.findall(r'-?\d+\.?\d*(?:E-?\d+)?', norm(b))
    return re.sub(r'"[^"]*"', '', norm(a)) == re.sub(r'"[^"]*"', '', norm(b)) and len(fa) == len(fb) and all(abs(float(x) - float(y)) <= 1e-4 for x, y in zip(fa, fb))
tv, tb, to = ET.parse(van), ET.parse(base), ET.parse(other)
V, B, O = items(tv.getroot()), items(tb.getroot()), items(to.getroot())
if set(V) != set(O) or set(V) != set(B): sys.exit('entity sets differ (added/removed entities) -> handle by hand, stop')
ch_o = [g for g in V if not near(V[g], O[g])]; ch_b = [g for g in V if not near(V[g], B[g])]
both = set(ch_o) & set(ch_b)
if both: sys.exit(f'STOP: both authors changed entities {sorted(both)}')
ents = tb.getroot().find('entities'); lst = list(ents)
for g in ch_o:
    i = lst.index(B[g]); new = O[g]; new.tail = B[g].tail
    ents.remove(B[g]); ents.insert(i, new); lst = list(ents)
    print(f'took other author\'s entity guid {g} ({new.findtext("archetypeName")}) at index {i}')
print(f'base author changed {len(ch_b)}, other author changed {len(ch_o)}, overlap 0')
tb.write(out, encoding='UTF-8', xml_declaration=True)
