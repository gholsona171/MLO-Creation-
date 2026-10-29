"""The resource's one _manifest.ymf from every interior's interior.json (work/p3/out, work/jail/out, ...): one INTERIOR_DATA entry per
MLO (one resource can ship only one _manifest.ymf). Tower City's mlo_meta writes + compiles it (imported, never edited).
Run: py -3 merge_manifest.py <out dir> <interior.json> [<interior.json> ...]   -> <out dir>/bin/_manifest.ymf   (pass line MANIFEST_MERGED)"""
import json, sys
from pathlib import Path
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\TowerCity\work')
import mlo_meta as MM
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ents = []
for p in sys.argv[2:]:
    for e in json.load(open(p)):
        assert e['name'] not in [x['name'] for x in ents], f'interior {e["name"]} twice'
        ents.append(e)
MM.manifest(ents, out)
bad = MM.compile_all(out, ('_manifest.ymf',))
assert not bad, bad
assert (out / 'bin' / '_manifest.ymf').exists(), 'no compiled manifest'
print('MANIFEST_MERGED', [e['name'] for e in ents])
