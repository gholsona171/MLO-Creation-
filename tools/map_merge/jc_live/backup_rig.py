# Copies every rig file named in scan_live.txt ("   live  <md5> <relpath>") into src_rig/<relpath> (the copies as found), then
# writes sources.txt (md5|path for every src_* file). Run from jc_live_merge/.
import os, shutil, hashlib
LIVE = r'C:\C9Test\live\resources'
for ln in open('scan_live.txt', encoding='utf-8'):
    if not ln.startswith('   live'): continue
    rel = ln.split(None, 2)[2].strip()
    dst = os.path.join('src_rig', rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(LIVE, rel), dst)
rows = []
for d in sorted(x for x in os.listdir('.') if x.startswith('src_')):
    for r, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f); rows.append(hashlib.md5(open(p, 'rb').read()).hexdigest() + '|' + p.replace('\\', '/'))
open('sources.txt', 'w').write('\n'.join(sorted(rows, key=lambda s: s.split('|')[1])) + '\n')
print(len(rows), 'source files')
