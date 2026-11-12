"""Portal winding gate (2026-11-11, the auditorium void): every portal's normal (the corners' winding) must point INTO its 'to' room.
A point 0.4 m along the normal from the portal's centre must lie in the 'to' room's zone and 0.4 m against it in the 'from' room's
zone (a portal to limbo: the normal points away from the centre of the from-room's zone rect it sits on) (out/jc3_layout.json zones; mirror portals are skipped: they face their own room).
A reversed portal draws fine from both sides, but the game's room tracking counts a walk through it backwards: walking in is not
seen, walking out is taken as walking in (the ped and the camera end up 'in' the room behind them; the building is not drawn).
Proof: --plant reverses one door portal; the gate must name it. Run: py -3 jc6_portal_gate.py [--plant]   (JC6_PORTAL_PASS)"""
import json, sys
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent
L = json.load(open(P3 / 'out/jc3_layout.json')); Z = L['zones']
def inside(k, p, tol=0.05):
    return any(z[0] - tol <= p[0] <= z[1] + tol and z[2] - tol <= p[1] <= z[3] + tol and z[4] - tol <= p[2] <= z[5] + tol for z in Z.get(k, []))
def check(portals):
    bad = []
    for i, p in enumerate(portals):
        if p.get('flags', 0) & 4: continue                                   # mirrors
        c = np.array(p['corners'], float)[:, :3]; n = np.cross(c[1] - c[0], c[2] - c[0]); n /= np.linalg.norm(n); m = c.mean(0)
        a, b = m + n * 0.4, m - n * 0.4; fr, to = p['from'], p['to']
        if to == 'limbo':                                                     # outward: away from the centre of the from-room's rect it sits on
            zs = [z for z in Z.get(fr, []) if z[0] - 0.3 <= m[0] <= z[1] + 0.3 and z[2] - 0.3 <= m[1] <= z[3] + 0.3 and z[4] - 0.3 <= m[2] <= z[5] + 0.3]
            ok = bool(zs) and all(float(np.dot(n, m - np.array([(z[0] + z[1]) / 2, (z[2] + z[3]) / 2, (z[4] + z[5]) / 2]))) > 0 for z in zs)
        else: ok = inside(fr, b, 0.3) and inside(to, a, 0.3)
        if not ok: bad.append((i, fr, to, p['kind'], [round(x, 2) for x in n]))
    return bad
if __name__ == '__main__':
    ports = [dict(p) for p in L['portals']]
    if '--plant' in sys.argv:
        k = next(i for i, p in enumerate(ports) if p['to'] not in ('limbo',) and not p.get('flags'))
        ports[k] = dict(ports[k], corners=list(reversed(ports[k]['corners'])))
        bad = check(ports); print('JC6_PORTAL_PLANT_FOUND' if any(b[0] == k for b in bad) else 'JC6_PORTAL_PLANT_MISSED', bad[:3]); sys.exit(0)
    bad = check(ports)
    for b in bad: print('REVERSED', *b)
    print('JC6_PORTAL_PASS' if not bad else 'JC6_PORTAL_FAIL', len(ports), 'portals', len(bad), 'reversed')
    sys.exit(1 if bad else 0)
