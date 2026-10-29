"""Deploy check (Antonio 2026-10-29: the rig ran an old Jail I build): every stream file of each MLO in the LIVE resource must hash-match
its build output. Run after a deploy: py -3 deploy_check.py <live resource dir> <mlo> [<mlo> ...] [--plant]
  mlo: courts (work/p3/out) | jail (work/jail/out). --plant: one live file is read as if one byte had changed - the check must name it.
Pass line DEPLOY_CHECK_PASS; any stale or missing file -> DEPLOY_CHECK_FAIL and exit 1."""
import hashlib, sys
from pathlib import Path
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter\work')
SRC = {'courts': [(J / 'p3/out/bin', 'jc_courts.ytyp'), (J / 'p3/out/bin', 'jc_courts_milo_.ymap'), (J / 'p3/out', 'jc_courts_*.ydr'), (J / 'p3/out', 'jc_courts.ybn')],
       'jail': [(J / 'jail/out/bin', 'jc_jail.ytyp'), (J / 'jail/out/bin', 'jc_jail_milo_.ymap'), (J / 'jail/out/bin', 'jc_jail_ext.ymap'),
                (J / 'jail/out', 'jc_jail_*.ydr'), (J / 'jail/out', 'jc_jail.ybn')]}
def sha(b): return hashlib.sha256(b).hexdigest()
live = Path(sys.argv[1]) / 'stream'; plant = '--plant' in sys.argv
mlos = [a for a in sys.argv[2:] if not a.startswith('--')]
bad = []; n = 0; planted = None
for m in mlos:
    for d, pat in SRC[m]:
        files = sorted(d.glob(pat)); assert files, f'{m}: no build output {d}/{pat}'
        for f in files:
            lf = live / f.name.lower() if not (live / f.name).exists() else live / f.name
            if not lf.exists(): bad.append(f'MISSING {m} {f.name}'); continue
            b = lf.read_bytes()
            if plant and planted is None: b = bytes([b[0] ^ 1]) + b[1:]; planted = f.name   # the planted stale file
            n += 1
            if sha(b) != sha(f.read_bytes()): bad.append(f'STALE {m} {f.name}')
if plant:
    assert any(planted in x for x in bad), f'PLANTED STALE FILE NOT FOUND ({planted}): the deploy check is broken'
    print('DEPLOY_CHECK_PLANT_FOUND', planted); sys.exit(0)
for x in bad: print(x)
print('checked', n, 'files of', mlos); print('DEPLOY_CHECK_PASS' if not bad else 'DEPLOY_CHECK_FAIL'); sys.exit(1 if bad else 0)
