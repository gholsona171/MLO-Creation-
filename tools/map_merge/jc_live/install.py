# Installs every merged/<name> into every rig resource that streams that name (justice_center included), backing up each replaced file
# to backup_installed/<path under live\resources> first. Writes install_log.txt (md5 before -> after). Run from jc_live_merge/.
#   py -3 tools/install.py [--dry]
import os, sys, shutil, hashlib
LIVE = r'C:\C9Test\live\resources'
dry = '--dry' in sys.argv
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
merged = {f.lower(): os.path.join('merged', f) for f in os.listdir('merged')}
hits = []
for r, _, fs in os.walk(LIVE):
    if '[disabled]' in r.lower(): continue
    for f in fs:
        if f.lower() in merged: hits.append(os.path.join(r, f))
log = []
for p in sorted(hits):
    rel = os.path.relpath(p, LIVE); src = merged[os.path.basename(p).lower()]
    before, after = md5(p), md5(src)
    if not dry and before != after:
        b = os.path.join('backup_installed', rel); os.makedirs(os.path.dirname(b), exist_ok=True)
        if not os.path.exists(b): shutil.copy2(p, b)
        shutil.copyfile(src, p)
        assert md5(p) == after
    log.append(f'{before[:8]} -> {after[:8]}  {rel.replace(chr(92), "/")}')
print('\n'.join(log)); print(len(log), 'copies', '(dry run)' if dry else '')
if not dry: open('install_log.txt', 'w').write('\n'.join(log) + '\n')
