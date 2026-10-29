"""Area 4 (Jail I) prop footprint gate, per level (L1, L2 = the block's floor, L3 = the upper tier): every placed prop inside its room's
clear floor, no two props overlapping, nothing in a doorway's swing zone (+-0.8 m at the line, playbook 03) - the playbook's
footprint_check.py on our layout. Wall-hung props (extinguishers, cameras, wall screens, wall phones) are left out by design.
Proof: --plant puts Mission Row's bench across the airlock -> booking doorway; the check must flag it. Run: py -3 jj_footprint.py [--plant]"""
import json, sys, subprocess
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path.insert(0, str(JL)); import jj_plan as J, jj_fit as JF
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
FC = r'C:\Users\anton\Documents\Codex\MLO-Creation\tools\footprint_check.py'
L = json.load(open(JL / OD / 'jj_layout.json')); PLANT = '--plant' in sys.argv
WALL_HUNG = {'prop_fire_exting_2a', 'prop_cctv_cam_01a', 'prop_tv_flat_01', 'prop_tv_flat_02', 'prop_byard_phone'}
LEVELS = {'B1': (J.B1 - 0.1, J.SALLY_Z - 0.2), 'L1': (J.SALLY_Z - 0.1, J.L2 - 0.5), 'L2': (J.L2 - 0.1, J.TIER2 - 0.5), 'L3': (J.TIER2 - 0.1, 41.0)}
bad = checked = 0
for lev, (za, zb) in LEVELS.items():
    rooms = {k: [list(r) for r in JF.clear(k)] for k, r in J.R.items() if r['z0'] - 0.5 <= za + 0.5 <= r['z1'] or (k == 'block' and lev in ('L2', 'L3'))}
    doors = [[o['axis'], o['plane'], o['a0'], o['a1']] for o in L['openings'] if za <= o['z0'] < zb and not o.get('glass') and o['name'] != 'rollup']
    props = [[q['room'], q['model'], q['u'], q['v'], q['base'] - za, q['heading'], 1.0] for q in L['placed'] if q['model'] not in WALL_HUNG and za <= q['base'] < zb]
    if PLANT and lev == 'L1': props.append(['book', 'v_ilev_ph_bench', -24.8, 17.3, 0.0, 0.0, 1.0])
    pj = JL / OD / f'footprint_props_{lev}.json'; json.dump({'rooms': rooms, 'doors': doors, 'props': props}, open(pj, 'w'))
    r = subprocess.run([sys.executable, FC, str(pj), str(JL / 'survey/arch_ytyp.json')], capture_output=True, text=True)
    found = [l for l in r.stdout.strip().splitlines() if l.split() and l.split()[0] in ('WALL', 'OVERLAP', 'DOORWAY', 'NO')]
    for l in found: print(lev, l)
    if PLANT and lev == 'L1':
        assert any(l.startswith('DOORWAY') for l in found), 'PLANTED DOORWAY BENCH NOT FOUND: the footprint check is broken'
        print('JJ_FOOTPRINT_PLANT_FOUND'); sys.exit(0)
    bad += len(found); checked += len(props)
print('checked', checked, 'props,', bad, 'findings'); print('JJ_FOOTPRINT_PASS' if not bad else 'JJ_FOOTPRINT_FAIL'); sys.exit(1 if bad else 0)
