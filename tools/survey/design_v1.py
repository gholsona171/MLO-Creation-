"""Justice Center v1: the design layer on top of the fitted real footprints (v1_outlines.json, written by fit_v1.py).
Adds, in the lot frame: the atrium (base minus tower minus Jail I), the lawn towards Davis Ave, the skybridges, the sally port,
the entrances, and every building's floor stack (scaled heights, interior floors vs empty shell, see-out windows).
Run after fit_v1.py; plan_v1.py, section_v1.py and map_data_sheet.py read the result (v1_outlines.json -> 'design')."""
import json, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
V = json.load(open(os.path.join(SV, 'v1_outlines.json')))
site = json.load(open(os.path.join(SV, 'site.json')))
S = V['scale']
OX, OY = site['frame']['origin_world']; HG = math.radians(site['frame']['heading_deg'])
world = lambda uv: [(round(OX + u * math.cos(HG) - v * math.sin(HG), 2), round(OY + u * math.sin(HG) + v * math.cos(HG), 2)) for u, v in uv]
Z0 = 28.8                       # ground floor of the whole complex (sidewalks round the block z 27.6-28.6; one step up)

b = V['parts']['complex_base']['uv']
# atrium = the base outline minus the tower (vertices 7..12 of the base run round the tower) minus Jail I (u < -8.5)
ATRIUM = [b[2], b[3], b[4], b[5], b[6], (b[6][0], 17.4), (13.72, 17.49), (13.74, 49.46), b[11], b[12]]
LAWN = [(-49, 66), (52, 66), (52, 86), (45, 89), (-5, 112), (-30, 121), (-45, 119), (-49, 112)]   # to the Davis Ave kerb
YARD = [(-45, -24), (-5, -24), (-5, -7), (-45, -7)]       # gap between Jail I and Jail II: the secure yard / sally port

# real heights x the plan scale; floor counts as the real buildings (reference.md)
def stack(name, real_h, floors, interior, notes, h0=None):
    h = real_h * S; ff = h / floors
    fl = []
    for i in range(1, floors + 1):
        kind = interior.get(i, 'shell')
        fl.append(dict(level=i, z=round(Z0 + (i - 1) * ff, 2), use=kind, see_out=kind != 'shell' and not kind.startswith('upper half'),
                       note=notes.get(i, '')))
    return dict(name=name, real_height_m=real_h, height_m=round(h, 1), floors=floors, floor_to_floor_m=round(ff, 2),
                z_ground=Z0, z_roof=round(Z0 + h, 1), floors_list=fl)

TOWER = stack('Courts Tower', 128.0, 26, {
    1: 'tower lobby + lift lobby (double height, open to L2)', 2: 'upper half of the lobby',
    3: 'COURTROOM A floor (courtroom double height, open to L4)', 4: 'upper half of courtroom A; jury room A / holding A / corridors have a ceiling at L4',
    5: 'COURTROOM B floor (courtroom double height, open to L6)', 6: 'upper half of courtroom B; ceilings as L4',
    7: "judges' chambers + offices", 25: 'one office near the top (view over Davis)'},
    {1: 'entered from the atrium; prisoner transfer corridor from Jail I enters the secure lift here',
     3: 'three circulations: public (lifts -> public corridor -> gallery door), restricted (judge / jury / clerk corridor), secure (secure lift -> holding -> defendant door)',
     5: 'same layout as courtroom A, one floor stack up', 26: 'mechanical floor: taller dark openings as on the real tower'})
POLICE = stack('Police HQ', 39.5, 9, {1: 'public lobby + bullet-resistant front desk, waiting, desk office', 2: 'offices: open office, captain, interview, conference'},
               {1: 'front desk faces the plaza (as on Ontario St)'})
JAIL1 = stack('Jail I (Corrections Center)', 10 * 4.2, 10, {1: 'sally port, intake / booking counter, photo + prints, holding cells, property, officer station',
                                                       2: 'cell block: dayroom + lower tier cells (pod, double height, open to L3)', 3: 'upper half: upper tier cells + walkway'},
              {1: 'height unverified: 4.2 m per floor assumed (10 floors); slot louvres, no see-out windows on cell floors (as real)'})
JAIL2 = stack('Jail II', 11 * 3.6, 11, {}, {1: 'exterior shell only: cream panels, punched slot windows; height unverified (3.6 m per floor assumed)'})
ATRIUM_ST = stack('Atrium (Galleria)', 4 * 4.9, 4, {1: 'public entrance, security checkpoint (detectors, X-ray belt, guard desk), galleria', 2: 'galleria void (glass roof over L4)',
                                                     3: 'galleria void', 4: 'galleria void'}, {1: 'glass curtain walls on the plaza side; the one see-through part of the complex'})
design = dict(
    z_ground=Z0,
    atrium=dict(uv=ATRIUM, world=world(ATRIUM)), lawn=dict(uv=LAWN, world=world(LAWN), note='the Lakeside lawn + sloped walk, towards Davis Ave'),
    secure_yard=dict(uv=YARD, world=world(YARD), note='gated yard between Jail I and Jail II; the sally port opens off it'),
    skybridges=[dict(name='Jail I - Jail II', uv=[(-26, -7), (-26, -24)], level=3), dict(name='Police HQ - Jail II', uv=[(10.4, -42), (-5, -42)], level=3)],
    sally_port=dict(uv=[(-45, -7), (-25, -7), (-25, 6), (-45, 6)], note='enclosed vehicle bay in the Jail I base, roll-up doors; drive in from Macdonald St through the secure yard gate'),
    entrances=[
        dict(name='public main entrance (atrium)', uv=(37.9, 4), face='plaza (Innocence Blvd side)', z=Z0),
        dict(name='police HQ front desk (public door)', uv=(45.0, -30), face='plaza', z=Z0),
        dict(name='police cars + staff (garage door)', uv=(28, -59.6), face='Roy Lowenstein Blvd', z=Z0),
        dict(name='sally port gate', uv=(-49, -15), face='Macdonald St', z=Z0),
        dict(name='jail visitors', uv=(-45, 30), face='Macdonald St', z=Z0),
        dict(name="judges / court staff (secure door + drop-off)", uv=(32, 56.3), face='the lawn, from Davis Ave', z=Z0)],
    sculpture=dict(uv=V['parts']['portal']['uv'][0], note='our own bent dark tube ("Portal" style), about 11 m x scale = 8 m tall; replaces Rockstar\'s monument'),
    buildings=dict(courts_tower=TOWER, police_hq=POLICE, jail_1=JAIL1, jail_2=JAIL2, atrium=ATRIUM_ST),
    vanilla_tower=dict(z_roof=91.7, z_top=97.5, uv=[(-24.2, -24.2), (24.2, -24.2), (24.2, 24.2), (-24.2, 24.2)]),
)
V['design'] = design
json.dump(V, open(os.path.join(SV, 'v1_outlines.json'), 'w'), indent=1)
for k, bd in design['buildings'].items():
    inter = [f['level'] for f in bd['floors_list'] if f['use'] != 'shell']
    print(k, 'h %.1f m  floors %d x %.2f m  roof z %.1f  interior levels %s' % (bd['height_m'], bd['floors'], bd['floor_to_floor_m'], bd['z_roof'], inter))
