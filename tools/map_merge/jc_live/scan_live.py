# justice_center stream names vs every streamed file in C:\C9Test\live\resources (case-insensitive, by file name).
# Skips [disabled], [localtest]\brnx_* and justice_center itself. Usage: py -3 scan_live.py [JC stream dir]
import os, sys, collections, hashlib
LIVE = r'C:\C9Test\live\resources'
JC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\anton\Documents\Codex\JusticeCenter\resource\justice_center\stream'
EXT = {'.ymap','.ytyp','.ybn','.ydr','.ydd','.yft','.ytd','.ycd','.ynd','.ynv','.ymt','.ypt','.awc','.ymf'}
def walk(root):
    for d, _, fs in os.walk(root):
        for f in fs:
            if os.path.splitext(f)[1].lower() in EXT and not f.lower().startswith('_manifest'): yield f.lower(), os.path.join(d, f)
md5 = lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()[:8]
live = collections.defaultdict(list)
for n, p in walk(LIVE):
    pl = p.lower()
    pl = pl.replace(chr(92), '/')
    if '[disabled]' in pl or '/justice_center/' in pl or '/[localtest]/brnx_' in pl: continue
    live[n].append(p)
new = collections.defaultdict(list)
for n, p in walk(JC): new[n].append(p)
hits = 0
for n in sorted(new):
    if n in live:
        hits += 1
        print('CLASH', n)
        for p in new[n]: print('   JC   ', md5(p))
        for p in live[n]: print('   live ', md5(p), os.path.relpath(p, LIVE))
print('JC files', sum(map(len, new.values())), '| live files indexed', sum(map(len, live.values())), '| clashing names', hits)
print('CHECK DONE')
