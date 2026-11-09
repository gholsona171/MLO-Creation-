# Compare merged XML with the XML CodeWalker re-exports from the built ymap: whitespace-normalised, <x></x> == <x />,
# numbers within 1e-6 relative, names compared as joaat hashes. Prints SAME / DIFF (+ first difference) per file.
#   xml_same.py <dir of merged XML> <dir of re-exported XML named reexp__<name>.xml>
import sys, os, re
exec(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'joaat.py')).read())
NUM = re.compile(r'-?\d+\.?\d*(?:E[-+]?\d+)?')
def toks(p):
    s = open(p, encoding='utf-8-sig').read(); s = re.sub(r'<\?xml[^>]*\?>', '', s)
    s = re.sub(r'<(\w+)((?: [^>]*?)?)>\s*</\1>', r'<\1\2 />', s); s = re.sub(r'\s*/>', ' />', s)
    s = re.sub(r'>([A-Za-z_][\w]*)<', lambda m: '>' + hname(m.group(1)) + '<', s)
    return re.findall(r'<[^>]+>|[^<\s]+', s)
def same(a, b):
    if a == b: return True
    na, nb = NUM.findall(a), NUM.findall(b)
    if NUM.sub('#', a) != NUM.sub('#', b) or len(na) != len(nb): return False
    return all(abs(float(x) - float(y)) <= 1e-6 * max(1, abs(float(x))) for x, y in zip(na, nb))
A, B = sys.argv[1], sys.argv[2]
bad_any = False
for f in sorted(os.listdir(A)):
    r = os.path.join(B, 'reexp__' + f.replace('.xml', '') + '.xml')
    ta, tb = toks(os.path.join(A, f)), toks(r)
    bad = next((i for i, (x, y) in enumerate(zip(ta, tb)) if not same(x, y)), None)
    if bad is None and len(ta) == len(tb): print('SAME', f, len(ta), 'tokens')
    else: bad_any = True; print('DIFF', f, len(ta), len(tb), 'at', bad, ta[bad - 3:bad + 3] if bad else '', tb[bad - 3:bad + 3] if bad else '')
sys.exit(1 if bad_any else 0)
