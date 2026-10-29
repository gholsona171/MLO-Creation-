"""Deploy check (Antonio 2026-10-29: the rig ran an old build while the newest sat in work/jail/out - the steel tables were "missing" in
game): every jc_jail stream file the build makes must be in the LIVE resource on the rig, byte for byte (SHA-256), and nothing named
jc_jail* may be in the live stream that the build did not make. Run before every rig test session.
Proof: --plant compares against a planted stale copy (one built file's hash altered in memory); the check must name it, or it fails.
Run: py -3 jj_deploy_check.py [--plant]   (JJ_DEPLOY_PASS / JJ_DEPLOY_PLANT_FOUND; exit 1 on a mismatch)"""
import hashlib, sys
from pathlib import Path
JL = Path(__file__).resolve().parent
OD = JL / __import__('os').environ.get('JJ_OUT', 'out')
LIVE = Path(r'C:\C9Test\live\resources\[localtest]\justice_center\stream')
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
built = {p.name.lower(): p for p in list(OD.glob('jc_jail_*.ydr')) + [OD / 'jc_jail.ybn'] + list((OD / 'bin').glob('jc_jail*'))}
want = {n: h(p) for n, p in built.items()}
if '--plant' in sys.argv:
    k = 'jc_jail_block.ydr'; want[k] = hashlib.sha256(b'stale' + want[k].encode()).hexdigest()     # the live file must now look stale
live = {p.name.lower(): p for p in LIVE.iterdir() if p.name.lower().startswith(('jc_jail_', 'jc_jail.'))} if LIVE.exists() else {}   # (jc_jail1 / 2 are phase 2's shells)
bad = []
for n, d in sorted(want.items()):
    if n not in live: bad.append(('MISSING on the rig', n))
    elif h(live[n]) != d: bad.append(('STALE on the rig', n))
for n in sorted(set(live) - set(want)): bad.append(('EXTRA on the rig (not in this build)', n))
for b in bad: print(' ', *b)
if '--plant' in sys.argv:
    assert ('STALE on the rig', 'jc_jail_block.ydr') in bad, 'PLANTED STALE FILE NOT FOUND: the deploy check is broken'
    print('JJ_DEPLOY_PLANT_FOUND'); sys.exit(0)
print(('JJ_DEPLOY_PASS ' if not bad else 'JJ_DEPLOY_FAIL ') + f'{len(want)} files compared, {len(bad)} mismatches'); sys.exit(1 if bad else 0)
