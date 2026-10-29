"""Justice Center phase 3 metadata, from work/p3/out/jc3_layout.json (jc3_build.py):
  jc_courts.ytyp / jc_courts_milo_.ymap   the MLO (room galleria so far), placed at the lot origin with the lot heading (MLO-local =
                                          the lot frame); doors attached to their exit portal (drawn from both sides)
  _manifest_p3.ymf                        its INTERIOR_DATA entry (the resource's one _manifest.ymf is merged at assemble time) with
                                          the itypDepArray of every placed prop and the interior bound jc_courts
Tower City's writers (mlo_meta.py: Rockstar's own v_int_64 / v_rockclub templates re-filled) are imported, never edited.
The dependency list is built from work/p3/survey/arch_ytyp.json; an unknown prop fails the build. Bounds are recomputed by
jc3_build from the exported geometry every run (stale archetype bounds = blue sky, playbook 09).
Compiled with TequiBuild into work/p3/out/bin. Run: py -3 jc3_meta.py   (pass line JC3_META_PASS)"""
import json, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\TowerCity\work')
import mlo_meta as MM
OUT = P3 / 'out'
L = json.load(open(OUT / 'jc3_layout.json'))
ORG = tuple(L['origin']); HEAD = L['heading']; D = L['drawables']
S = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
models = sorted({p['model'].lower() for p in L['props']})
missing = [m for m in models if m not in S]
assert not missing, f'props with no ytyp in work/p3/survey/arch_ytyp.json (run survey/find_arch_ytyp.ps1): {missing}'
DEPS = sorted({S[m]['ytyp'] for m in models})
KEY = {'limbo': 0, **{r['key']: r['id'] for r in L['rooms']}}
assert sorted(KEY.values()) == list(range(len(KEY))) and max(KEY.values()) <= 31, 'room ids must run 0..n (n <= 31) without gaps'
for r in L['rooms']: assert r['timecycle'] == r['timecycle'].lower(), 'timecycle names must be lower case (playbook 02)'
def _names_lower(drawables):
    """every archetype / asset name lower case: the meta compiler hashes names case-sensitively, the game hashes file names lower case
    (2026-10-29: jc_courts_crtA never matched jc_courts_crta.ydr - every L3 / L5 room was undrawn while all offline gates passed)"""
    return [n for n in drawables if n != n.lower()]
assert _names_lower(['jc_courts_crtA']) == ['jc_courts_crtA'], 'the name-case gate did not find its planted name'
assert not _names_lower(list(D) + [L['mlo']]), f'archetype names must be lower case: {_names_lower(list(D) + [L["mlo"]])}'
PORT = [{'from': KEY[p['from']], 'to': KEY[p['to']], 'corners': p['corners'], 'flags': p.get('flags', 0)} for p in L['portals']]
lo, hi, exits, nent = MM.mlo_ytyp(L['mlo'], L['rooms'], PORT, L['props'], D, OUT, 3100100000)
# the MLO archetype's box covers the whole atrium (door leaves in the glass plane, the perimeter collision to the outer faces), not
# only the room drawables: rewrite it in the XML we just wrote (our own writer step, before the compile)
import xml.etree.ElementTree as ET
AB = L['mlo_box']; lo = [min(a, b) for a, b in zip(lo, AB[0])]; hi = [max(a, b) for a, b in zip(hi, AB[1])]
yp = OUT / (L['mlo'] + '.ytyp.xml'); yr = ET.parse(yp).getroot()
for a in yr.find('archetypes'):
    if a.get('type') == 'CMloArchetypeDef':
        MM.setvec(a.find('bbMin'), lo); MM.setvec(a.find('bbMax'), hi); MM.setvec(a.find('bsCentre'), [(x + y) / 2 for x, y in zip(lo, hi)])
        a.find('bsRadius').set('value', f'{sum((x - y) ** 2 for x, y in zip(lo, hi)) ** 0.5 / 2:.4f}')
        lim = a.find('rooms')[0]; MM.setvec(lim.find('bbMin'), lo); MM.setvec(lim.find('bbMax'), hi)
MM.write(yr, yp)
MM.ymap(L['mlo'] + '_milo_', 'mlo', [(L['mlo'], lo, hi)], ORG, HEAD, OUT, 3100200000, 400, 400, [L['bound']], exits)
json.dump([{'name': L['mlo'], 'deps': DEPS, 'bounds': [L['bound']]}], open(OUT / 'interior.json', 'w'), indent=1)
MM.manifest([{'name': L['mlo'], 'deps': DEPS, 'bounds': [L['bound']]}], OUT)
bad = MM.compile_all(OUT, (L['mlo'] + '.ytyp', L['mlo'] + '_milo_.ymap', '_manifest.ymf'))
assert not bad, f'compile failures: {bad}'
print('JC3_META_PASS', json.dumps({'rooms': len(KEY), 'portals': len(PORT), 'exit_portals': exits, 'entities': nent, 'deps': DEPS,
      'mlo_bounds': [[round(v, 2) for v in lo], [round(v, 2) for v in hi]]}), flush=True)
