import sys, re, collections
def pack(path):
    parts = re.split(r'[\\/]', path)
    for i, p in enumerate(parts):
        if p in ('resources', 'x'):
            j = i + 1
            while j < len(parts) and parts[j].startswith('['): j += 1
            return parts[j]
    return '?'
def load(f):
    out = []
    for line in open(f, encoding='utf-8-sig'):
        a = line.rstrip('\n').split('\t')
        if a[0] != 'Y': continue
        b = list(map(float, a[2:8])); n = int(a[8])
        if n == 0 or b[3] - b[0] > 1500 or b[4] - b[1] > 1500: continue  # skip empty / world-sized
        out.append((pack(a[1]), re.split(r'[\\/]', a[1])[-1], b))
    return out
def ov(a, b, pad=2):
    return a[0] < b[3] + pad and b[0] < a[3] + pad and a[1] < b[4] + pad and b[1] < a[4] + pad
cle = load('C:/C9Test/incoming/scan/cleveland.tsv')
new = load('C:/C9Test/incoming/scan/gabz.tsv') + load('C:/C9Test/incoming/scan/today.tsv')
res = collections.defaultdict(lambda: collections.defaultdict(set))
for pk, yn, b in new:
    for cp, cy, cb in cle:
        if ov(b, cb): res[pk]['CLEVELAND ' + cp].add(f'{yn}~{cy}')
    for p2, y2, b2 in new:
        if p2 != pk and ov(b, b2): res[pk]['new ' + p2].add(f'{yn}~{y2}')
for pk in sorted({p for p, _, _ in new}):
    print(f'== {pk}')
    for k, v in sorted(res[pk].items()):
        v = sorted(v); print(f'   {k}: {len(v)}  e.g. {v[:3]}')
