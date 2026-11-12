"""Room-tracking probe (rig, 2026-11-11: walking into the auditorium lost the whole building, and it stayed lost outside): the player
ped WALKS (TaskGoStraightToCoord, real portal crossings) from a neighbour room into each tested room and back out. At every waypoint
it reads three things (a point's room = the smallest zone rect of out/jc3_layout.json holding it):
  ped   GetRoomKeyFromEntity(ped)             must be the room the ped stands in
  view  GetRoomKeyForGameViewport()           must be the room the CAMERA is in (GetGameplayCamCoord: just through a door the
                                              third-person camera is still a step behind, in the room the ped came from; a camera
                                              in a doorway's reveal, in no zone, may read either room the doorway joins)
  cam   GetInteriorFromGameplayCam()          the camera's interior = the courts' (not Jail I's, not 0 = outside)
At the marked waypoints the gameplay camera turns a full circle (12 steps of 30 deg): the view room must follow the camera at every
step, and a
frame is grabbed at 0 / 90 / 180 / 270 (shots/roomwalk/<route>_<n>_<deg>.png) to show the building still drawn.
Control: the ped stood outside on the plaza must read cam interior 0 (the probe can see 'outside').
Start position of each route: stood (teleport) in a room next to the tested one, so the walk starts from a known room.
Run: py -3 jc6_roomwalk.py [route ...]   (pass line JC6_ROOMWALK_PASS; out/probe_roomwalk.json)"""
import json, math, subprocess, sys, time
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3))
import jc3_probe as PR, jc3_plan as JP, jc3_tower as JT, jc_frame as F
L = PR.L; SHOTS = P3.parent.parent / 'shots' / 'roomwalk'; SHOTS.mkdir(parents=True, exist_ok=True)
NAME = {r['key']: r['name'] for r in L['rooms']}
F1, F3 = JT.F1, JT.FLOORS['A']
# route: [(u, v, floor z, circle?)]: the first point is the stand, the rest are walked in order
ROUTES = {
    'auditorium': [(21.6, 37.5, F1, True), (21.6, 40.0, F1, False), (21.6, 43.0, F1, True), (21.55, 48.0, F1, True), (21.6, 43.0, F1, False), (21.6, 40.0, F1, False), (21.6, 37.5, F1, True),
                   (30.0, 37.5, F1, False), (30.0, 25.0, F1, True)],
    'reception':  [(38.7, 37.5, F1, False), (38.7, 43.5, F1, True), (38.7, 37.5, F1, True)],
    'public_a':   [(16.0, 19.4, F3, True), (29.4, 19.4, F3, False), (29.4, 21.9, F3, False), (30.0, 24.0, F3, True), (30.0, 29.3, F3, False),
                   (25.65, 29.3, F3, False), (25.65, 33.0, F3, True), (25.65, 29.3, F3, False), (30.0, 29.3, F3, True), (30.0, 24.0, F3, False),
                   (29.4, 21.9, F3, False), (29.4, 19.4, F3, True)],
    'restricted_a': [(16.5, 25.0, F3, True), (16.5, 42.6, F3, True), (20.15, 42.6, F3, False), (35.0, 42.6, F3, True), (16.5, 42.6, F3, False),
                     (16.5, 25.0, F3, True)],
    'police':     [(20.0, -5.6, 28.8, True), (20.0, -8.6, 28.8, False), (30.0, -8.6, 28.8, True), (34.5, -8.6, 28.8, False), (34.5, -20.0, 28.8, True),
                   (34.5, -29.0, 28.8, False), (33.6, -30.5, 28.8, False), (33.6, -40.0, 28.8, True), (33.6, -30.5, 28.8, False),
                   (34.5, -29.0, 28.8, False), (34.5, -20.0, 28.8, False), (34.5, -8.6, 28.8, True), (20.0, -8.6, 28.8, False), (20.0, -5.6, 28.8, True)],
    'police_staff': [(23.0, -11.5, 28.8, True), (23.0, -15.0, 28.8, True), (23.0, -34.9, 28.8, True), (21.0, -34.9, 28.8, False),
                     (23.0, -34.9, 28.8, False), (23.0, -15.0, 28.8, False), (23.0, -11.5, 28.8, True)],
}
def rooms_near(u, v, z, pad=0.5):
    """a camera in no zone stands in a wall or a doorway's reveal (the zones stop at the wall faces): the rooms whose rects lie within
    pad of it - in a doorway, the two rooms it joins; either is a right answer for the view there."""
    return {k for k, zs in L['zones'].items() for u0, u1, v0, v1, z0, z1 in zs
            if u0 - pad <= u <= u1 + pad and v0 - pad <= v <= v1 + pad and z0 - 0.3 <= z <= z1}
def room_at(u, v, z):
    """the smallest zone rect holding (u, v) on that floor (nested rooms: the inner one)."""
    best = None
    for k, zs in L['zones'].items():
        for u0, u1, v0, v1, z0, z1 in zs:
            if u0 <= u <= u1 and v0 <= v <= v1 and z0 - 0.3 <= z <= z1:
                a = (u1 - u0) * (v1 - v0)
                if best is None or a < best[0]: best = (a, k)
    return best[1] if best else None
READ = ('local p=PlayerPedId() local c=GetEntityCoords(p) local g=GetGameplayCamCoord() return string.format("%d:%d:%d:%d:%.2f:%.2f:%.2f:%.2f:%.2f:%.2f",'
        'GetInteriorFromEntity(p),GetRoomKeyFromEntity(p),GetRoomKeyForGameViewport(),GetInteriorFromGameplayCam(),c.x,c.y,c.z,g.x,g.y,g.z)')
def read():
    a = PR.lua(READ).split(':'); f = [float(x) for x in a[4:]]
    return {'int': int(a[0]), 'ped': int(a[1]), 'view': int(a[2]), 'cam': int(a[3]), 'uv': [round(x, 2) for x in F.L(f[0], f[1])],
            'cam_uvz': [round(x, 2) for x in F.L(f[3], f[4])] + [round(f[5], 2)]}
def hashes():
    names = list(NAME.values())
    r = PR.lua('local o={} for _,n in ipairs({%s}) do o[#o+1]=tostring(GetHashKey(n)) end return table.concat(o,":")' % ','.join('"%s"' % n for n in names)).split(':')
    return {n: int(h) for n, h in zip(names, r)}
def grab(name):
    f = str(SHOTS / f'{name}.png'); subprocess.run([PR.GB, '-c', 'cd /c/C9Test && bash gshot.sh "$1"', '_', f], capture_output=True, timeout=60); return f
def circle(tag, want, H):
    steps = []
    for k in range(12):
        deg = 30 * k
        r = PR.lua('SetGameplayCamRelativeHeading(%.1f) SetGameplayCamRelativePitch(-5.0,1.0) Wait(450) local g=GetGameplayCamCoord() return string.format("%%d:%%d:%%.2f:%%.2f:%%.2f",GetRoomKeyForGameViewport(),GetInteriorFromGameplayCam(),g.x,g.y,g.z)' % (deg if deg <= 180 else deg - 360)).split(':')
        cu, cv = F.L(float(r[2]), float(r[3])); k = room_at(cu, cv, float(r[4]))
        ok = {H[NAME[k]]} if k else {H[NAME[n]] for n in rooms_near(cu, cv, float(r[4]))}
        steps.append({'deg': deg, 'view': int(r[0]), 'cam': int(r[1]), 'cam_room': k or sorted(rooms_near(cu, cv, float(r[4]))), 'want': sorted(ok)})
        if deg % 90 == 0: grab(f'{tag}_{deg:03d}')
    return steps
def run(name, H, courts):
    pts = ROUTES[name]; out = []; ok_all = True
    PR.revive(); PR.stand(pts[0][0], pts[0][1], pts[0][2]); time.sleep(3.0)
    for i, (u, v, z, turn) in enumerate(pts):
        arrived = True
        if i: arrived, _ = PR.walk_to(u, v, 20.0); time.sleep(0.8)
        k = room_at(u, v, z); want = H[NAME[k]] if k else None; s = read()
        kc = room_at(*s['cam_uvz']); wc = {H[NAME[kc]]} if kc else {H[NAME[n]] for n in rooms_near(*s['cam_uvz'])}
        good = arrived and k is not None and s['ped'] == want and s['view'] in wc and s['cam'] == courts
        rec = {'to': [u, v], 'room': k, 'cam_room': kc, 'arrived': arrived, **s, 'ok': good}
        if turn:
            st = circle(f'{name}_{i:02d}', want, H); rec['circle'] = st
            rec['circle_ok'] = all(x['view'] in x['want'] and x['cam'] == courts for x in st); good &= rec['circle_ok']; rec['ok'] = good
            PR.lua('SetGameplayCamRelativeHeading(0.0) return "c"')
        ok_all &= good; out.append(rec)
        print(name, i, k, kc, 'OK' if good else 'BAD', s, flush=True)
    return out, ok_all
if __name__ == '__main__':
    want = sys.argv[1:] or list(ROUTES)
    H = hashes()
    PR.revive(); PR.stand(50.0, 4.0, JP.G); time.sleep(3.0); ctl = read()            # the plaza: outside every interior
    PR.stand(5.0, 20.0, JP.G); time.sleep(3.0); courts = read()['int']              # the galleria: the courts interior's id
    res = {'control_plaza_cam': ctl['cam'], 'courts_interior': courts, 'routes': {}}; ok_all = ctl['cam'] == 0 and courts != 0
    try:
        for n in want:
            r, ok = run(n, H, courts); res['routes'][n] = {'ok': ok, 'points': r}; ok_all &= ok
    finally:
        json.dump(res, open(P3 / 'out/probe_roomwalk.json', 'w'), indent=1)
        PR.revive(); PR.stand(5.0, 20.0, JP.G)
    print('JC6_ROOMWALK_' + ('PASS' if ok_all else 'FAIL'), json.dumps({n: v['ok'] for n, v in res['routes'].items()}), 'plaza cam', ctl['cam'], flush=True)
    sys.exit(0 if ok_all else 1)
