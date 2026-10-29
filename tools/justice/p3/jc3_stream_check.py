"""Assemble gate: every jc_courts room drawable the ytyp places (archetypeName jc_*) has its .ydr in the resource's stream folder.
(2026-10-29: assemble.sh streamed only the galleria; every tower room drew as a white void on the rig while all offline gates passed.)
Proof: --plant hides one room's .ydr from the listing; the check must name it. Run: py -3 jc3_stream_check.py <stream dir> [--plant]"""
import re, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; ST = Path(sys.argv[1])
want = sorted(set(re.findall(r'<archetypeName>(jc_[^<]+)', open(P3 / 'out/jc_courts.ytyp.xml').read())))
have = {p.name.lower() for p in ST.glob('*.ydr')}
if '--plant' in sys.argv: have.discard('jc_courts_crta.ydr')
miss = [n for n in want if n.lower() + '.ydr' not in have]
if '--plant' in sys.argv:
    assert miss == ['jc_courts_crta'], f'PLANTED MISSING YDR NOT FOUND: {miss}'; print('JC3_STREAM_PLANT_FOUND'); sys.exit(0)
print('room drawables placed:', len(want), 'missing from stream:', miss); print('JC3_STREAM_PASS' if not miss else 'JC3_STREAM_FAIL'); sys.exit(1 if miss else 0)
