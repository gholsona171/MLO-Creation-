"""Prop footprint check of the mall's upper tenant floors (playbook tools/footprint_check.py, pivot-aware): props through a unit's
walls, big props overlapping each other, props blocking a doorway (storefronts, vacant units' doors, the passage, lift doors,
interior partitions). Input: work/l2/l2_layout.json ('upper_check': each unit's floor rects + the doorways, from upper_shops.py;
'props'), survey/arch_ytyp.json. Writes work/l2/upper_props.json (the tool's input) and exits 1 on any finding.
Run: py -3 upper_check.py"""
import json, sys, importlib.util
from pathlib import Path
W = Path(__file__).resolve().parent; T = W.parent
TOOL = Path(r'C:\Users\anton\OneDrive\Desktop\FiveM MLO Playbook\tools\footprint_check.py')
L = json.load(open(W / 'l2/l2_layout.json')); C = L['upper_check']; F2, F3 = 36.4, 43.6
A = {k.lower(): v for k, v in json.load(open(T / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
ids = {r['id'] for r in L['rooms'] if r['key'] in L['upper']}
zmin = lambda m: float(A[m.lower()]['bbMin'].split()[2][2:]) if m.lower() in A else 0.0
rooms, props, loose = C['rooms'], [], []
for p in L['props']:
    if p['room'] not in ids: continue
    u, v, z = p['pos']; fl = F3 if z >= F3 - 0.05 else F2; lv = 'L3' if fl == F3 else 'L2'
    side = next(r['key'] for r in L['rooms'] if r['id'] == p['room'])
    sc = p.get('scale'); sc = sc[0] if isinstance(sc, list) else sc
    hit = [k for k, rs in rooms.items() if k.startswith(f'{side} {lv} ') and any(a <= u <= b and c <= v <= d for a, b, c, d in rs)]
    if not hit: loose.append(p); continue
    props.append([hit[0], p['model'], u, v, round(z - fl - max(0.0, -zmin(p['model'])), 3), p['heading'], sc])
json.dump({'rooms': rooms, 'doors': C['doors'], 'props': [q for q in props if not q[1].startswith('tc_prop_mirror')]}, open(W / 'l2/upper_props.json', 'w'), indent=1)
spec = importlib.util.spec_from_file_location('footprint_check', TOOL); FC = importlib.util.module_from_spec(spec); spec.loader.exec_module(FC)
ALLOW = {('v_res_m_dinetble', 'apa_mp_h_din_chair_12')}         # the Eatery's round-table set: diagonal chairs meet the table's BOX corners only
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf): FC.main(str(W / 'l2/upper_props.json'), str(T / 'survey/arch_ytyp.json'))
lines = buf.getvalue().splitlines(); allowed = [l for l in lines if l.startswith('OVERLAP') and any(a in l and b in l for a, b in ALLOW)]
found = [l for l in lines if l.split()[:1] and l.split()[0] in ('WALL', 'OVERLAP', 'DOORWAY', 'NO') and l not in allowed]
for l in found: print(l)
bad = len(found); print(f'  ({len(allowed)} allowed table / chair box overlaps)')
print('UPPER_CHECK', len(props), 'props in', len(rooms), 'units /', len(C['doors']), 'doorways;', bad, 'findings;', len(loose), 'props outside every unit (lift cabs, stair, gallery-wall pieces)')
for p in loose[:10]: print('  OUTSIDE', p['model'], p['pos'])
sys.exit(1 if bad else 0)
