"""Phase 3 prop footprint gate: every placed prop inside its room's usable floor (linings + fins / skirting inset), no two big props
overlapping, nothing in a doorway's swing zone (+-0.8 m at the line, playbook 03) - the playbook's footprint_check.py on our layout.
Proof: --plant adds a bench across the ENTRY doorway; the check must flag it. Run: py -3 jc3_footprint.py [--plant]"""
import json, sys, subprocess
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3)); import jc3_plan as JP
L = json.load(open(P3 / 'out/jc3_layout.json'))
inset = JP.FIN_P + 0.01
rooms = {'galleria': [[JP.UA0 + inset, JP.UA1, JP.VA0 + inset, JP.VA1 - inset], [JP.UB0 + inset, JP.UB1 - inset, JP.VB0 - inset, JP.VB1]]}
doors = [['u', JP.UA1, s0, s1] for _, _, s0, s1, _, _ in JP.door_openings()]
WALL_HUNG = {'prop_fire_exting_2a'}                     # hung on a wall face by design (back 1.2 cm off it): not floor props
props = [[q['room'], q['model'], q['u'], q['v'], q['base'] - JP.G, q['heading'], 1.0] for q in L['placed'] if q['model'] not in WALL_HUNG]
if '--plant' in sys.argv: s0, s1 = JP.entrance_span('entry'); props.append(['galleria', JP.BENCH, JP.UA1 - 0.6, (s0 + s1) / 2, 0.0, 90.0, 1.0])
pj = P3 / 'out/footprint_props.json'; json.dump({'rooms': rooms, 'doors': doors, 'props': props}, open(pj, 'w'))
r = subprocess.run([sys.executable, r'C:\Users\anton\Documents\Codex\MLO-Creation\tools\footprint_check.py', str(pj), str(P3 / 'survey/arch_ytyp.json')], capture_output=True, text=True)
lines = [l for l in r.stdout.strip().splitlines() if not (l.startswith('OVERLAP') and l.split()[2] == JP.ROPE and l.split()[3] == JP.ROPE)]   # a rope chain's links meet at their posts by design
print(chr(10).join(lines)); bad = [l for l in lines if l.split()[0] in ('WALL', 'OVERLAP', 'DOORWAY', 'NO')]
if '--plant' in sys.argv:
    assert 'DOORWAY' in r.stdout, 'PLANTED DOORWAY BENCH NOT FOUND: the footprint check is broken'; print('JC3_FOOTPRINT_PLANT_FOUND')
else: print('JC3_FOOTPRINT_PASS' if not bad else 'JC3_FOOTPRINT_FAIL')
