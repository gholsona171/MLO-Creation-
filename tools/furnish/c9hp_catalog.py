"""Reads C9_HousingProps' generated catalogues (shared/catalog_<cat>.lua: every model's size, function, mount) into
../survey/c9hp_catalog.json for the house furnishing (house_furnish.py). Convention of that pack (its docs/PROPS.md): a model's
origin is the bottom centre of its footprint at floor level, its front faces -Y, metres; size = w (x) x d (y) x h (z).
Run: py -3 c9hp_catalog.py"""
import re, json
from pathlib import Path
SRC = Path(r'C:\C9Test\cloud9\scripts\C9_HousingProps')
out = {}
for f in sorted((SRC / 'shared').glob('catalog_*.lua')):
    cat = f.stem[8:]
    for chunk in f.read_text(encoding='utf-8').split('{ m = "')[1:]:          # one chunk per catalogue item
        name = chunk.split('"', 1)[0]
        size = re.search(r'size = \{ w = ([\d.]+), d = ([\d.]+), h = ([\d.]+) \}', chunk)
        if not name.startswith('c9hp_') or not size: continue
        fn = re.search(r'\bfn = "(\w+)"', chunk); mount = re.search(r'\bmount = "(\w+)"', chunk); sub = re.search(r'\bs = "(\w+)"', chunk)
        out[name] = {'cat': cat, 'sub': sub.group(1) if sub else None, 'fn': fn.group(1) if fn else None,
                     'mount': mount.group(1) if mount else None,
                     'w': float(size.group(1)), 'd': float(size.group(2)), 'h': float(size.group(3))}
dst = Path(__file__).resolve().parents[1] / 'survey' / 'c9hp_catalog.json'; dst.write_text(json.dumps(out, indent=1))
print('C9HP_CATALOG_PASS', len(out), 'models')
