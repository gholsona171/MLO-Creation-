# Every file in the Cleveland-RP checkout whose name is a justice_center stream name (other than justice_center itself),
# with md5 and whether git tracks it. Usage: py -3 scan_repo.py
import os, hashlib, subprocess
REPO = r'C:\C9Test\export\Cleveland-RP'
JC = r'C:\Users\anton\Documents\Codex\JusticeCenter\resource\justice_center\stream'
names = {f.lower() for f in os.listdir(JC) if not f.lower().startswith('_manifest')}
tracked = set(subprocess.run(['git', '-C', REPO, 'ls-files', 'resources'], capture_output=True, text=True).stdout.lower().splitlines())
for r, _, fs in os.walk(os.path.join(REPO, 'resources')):
    for f in fs:
        if f.lower() not in names: continue
        p = os.path.join(r, f); rel = os.path.relpath(p, REPO).replace('\\', '/')
        if '/justice_center/' in rel.lower(): continue
        print(hashlib.md5(open(p, 'rb').read()).hexdigest()[:8], 'TRACKED' if rel.lower() in tracked else 'untracked', rel)
print('REPO SCAN DONE')
