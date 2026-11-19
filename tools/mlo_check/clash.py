import json, os, sys, collections
idx = json.load(open('C:/C9Test/incoming/cleveland_stream_index.json'))
idx = {k.lower(): v for k, v in idx.items()}
STREAM = ('.ydr','.ydd','.yft','.ytd','.ybn','.ymap','.ytyp','.ynv','.ymt','.ycd','.ypt','.ynd','.awc','.rel','.dat151','.gfx')
IGN = {'fxmanifest.lua','__resource.lua','readme.txt','readme.md'}
def files(root):
    out = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith(STREAM): out.setdefault(f.lower(), []).append(os.path.join(dp, f))
    return out
packs = {}
for base in sys.argv[1:]:
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if os.path.isdir(p) and d not in ('xml',): packs[d] = files(p)
own = collections.defaultdict(list)
for pk, fs in packs.items():
    for f in fs: own[f].append(pk)
for pk, fs in packs.items():
    srv = sorted({r for f in fs for r in idx.get(f, [])})
    srvn = sum(1 for f in fs if f in idx)
    others = collections.Counter(o for f in fs for o in own[f] if o != pk)
    print(f"{pk}: {len(fs)} files | server dup {srvn} in {srv[:8]}{'...' if len(srv)>8 else ''} | pack dup {dict(others.most_common(6))}")
