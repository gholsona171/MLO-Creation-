"""Justice Center phase 2: rig walks round and onto the new complex (client 1, the player ped, not a camera) - jc_probe.py's helpers
(every rig call that gets no answer raises; the ped is revived + settled before each walk; it is put back on the ground before
tc_release.sh). Routes in the lot frame, ground from p2_site_plan (podium, lawn, colonnades at G, else the slab):
  round    the whole block at street level, on the slab strip inside the lot edge (past the bollards, the sally port mouth, the
           palms of the south strip, the lawn's kerb): a closed loop, leg by leg
  steps    up every kind of entrance: the plaza's street steps onto the podium to the atrium door, Jail I's colonnade steps (Macdonald),
           the police HQ's south colonnade steps, the sloped walk from Davis Ave up to the tower apron, the sally port (flush) mouth
Each leg: TaskGoStraightToCoord, z logged every 0.25 s; it must arrive (< 1.5 m), never ragdoll / climb / fall / jump, and the ped's z
must stay between ground - 0.5 and ground + 1.4 (no sinking, no floating on an invisible ledge).
Run: py -3 p2_probe.py round steps   -> work/probe_p2_walk.json, PROBE_P2_<NAME>_PASS / _FAIL; exit 1 on any fail."""
import sys, json, math, time
from pathlib import Path
P2 = Path(__file__).resolve().parent; W = P2.parent; sys.path[:0] = [str(P2), str(W)]
import jc_frame as F, jc_probe as JP, p2_plan as PL, p2_site_plan as SP
def ground(u, v):
    x, y = F.W(u, v); g = SP.ground_uv(u, v, F.slab_z(x, y))
    for k in ('tower', 'police', 'jail1'):
        for a, b, c, d, z0, z1 in PL.arcade_voids(k):
            if a <= u <= b and c <= v <= d: return PL.G
    return g
def _round():
    """the loop: 1.0 m inside the lot edge (Rockstar's sidewalk edge), kept 3.5 m in along Roy Lowenstein (the kept palms stand in
    the first 1.1 - 2.4 m there), simplified to straight legs."""
    from shapely.geometry import Polygon, box
    lot = Polygon([F.L(*p[:2]) for p in F.lot_w()]); r = lot.buffer(-1.0, join_style=2).intersection(box(-200, -67.5, 200, 200)).simplify(0.3)
    P_ = list(r.exterior.coords)[:-1]; i0 = min(range(len(P_)), key=lambda i: P_[i][0] + P_[i][1]); P_ = P_[i0:] + P_[:i0]
    out = [P_[0]]
    for p in P_[1:] + [P_[0]]:
        if math.dist(p, out[-1]) > 4.0 or p == P_[0]:
            n = int(math.ceil(math.dist(p, out[-1]) / 45.0)); a = out[-1]
            out += [(a[0] + (p[0] - a[0]) * i / n, a[1] + (p[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return [(round(u, 2), round(v, 2)) for u, v in out]
ROUND = _round()
STEPS = [
    ('plaza steps -> atrium door', [(64.7, 4.0), (60.0, 4.0), (39.0, 4.0)]),
    ('Jail I colonnade (Macdonald)', [(-47.3, 40.0), (-43.5, 40.0), (-43.5, 50.0)]),
    ('police south colonnade', [(28.0, -66.0), (28.0, -58.2), (20.0, -58.2)]),
    ('sloped walk Davis -> tower apron', [(15.9, 101.5), (17.9, 96.0), (26.0, 75.0), (31.0, 61.0), (31.0, 58.0)]),
    ('sally port mouth (flush)', [(-47.6, 16.0), (-44.0, 16.0), (-40.0, 16.0)]),
]
def leg(a, b):
    A = F.W(*a); B = F.W(*b); za = ground(*a) + 1.0
    JP.park(A[0], A[1], za, invisible=False); time.sleep(2); hp = JP.revive(); time.sleep(1.5)
    if int(float(hp)) < 150: raise SystemExit('PROBE p2 walk: the ped could not be revived (health %s) - nothing was tested' % hp)
    code = '''local p=PlayerPedId() ClearPedTasksImmediately(p) SetEntityCoords(p,%.2f,%.2f,%.2f) Wait(1200) TaskGoStraightToCoord(p,%.2f,%.2f,%.2f,1.6,120000,0.0,0.0)
local log={} local t0=GetGameTimer() local bad=0 local lastd=1e9 local stuck=0
while GetGameTimer()-t0<110000 do local c=GetEntityCoords(p) local d=#(vector2(c.x,c.y)-vector2(%.2f,%.2f))
 if IsPedRagdoll(p) or IsPedClimbing(p) or IsPedFalling(p) or IsPedJumping(p) then bad=bad+1 end
 log[#log+1]=string.format("%%.2f,%%.2f,%%.3f",c.x,c.y,c.z) if d<1.0 then break end
 if d>lastd-0.04 then stuck=stuck+1 else stuck=0 end lastd=d if stuck>40 then break end Wait(250) end
local c=GetEntityCoords(p) return string.format("%%d|%%.2f|%%d|",bad,#(vector2(c.x,c.y)-vector2(%.2f,%.2f)),GetGameTimer()-t0)..table.concat(log,";")''' % (A[0], A[1], za, B[0], B[1], ground(*b), B[0], B[1], B[0], B[1])
    r = JP.lua(code, 140); bad, dist, ms, log = r.split('|', 3)
    P_ = [tuple(map(float, s.split(','))) for s in log.split(';') if s]
    rel = [z - ground(*F.L(x, y)) for x, y, z in P_]
    ok = int(bad) == 0 and float(dist) < 1.5 and len(P_) > 4 and min(rel) > -0.5 and max(rel) < 1.4
    return {'from': a, 'to': b, 'ok': ok, 'bad_states': int(bad), 'end_dist': float(dist), 'ms': int(ms), 'samples': len(P_), 'z_minus_ground': [round(min(rel), 2), round(max(rel), 2)],
            'path': [[round(t, 2) for t in F.L(x, y)] + [round(z - ground(*F.L(x, y)), 2)] for x, y, z in P_]}
def run(name, routes):
    res = []
    for title, pts in routes:
        for a, b in zip(pts, pts[1:]):
            r = leg(a, b); r['route'] = title; res.append(r)
            print('PROBE_P2 %-34s %s -> %s: %s, %d samples, end %.2f m short, %d bad states, z - ground %s' % (title, a, b, 'ok' if r['ok'] else 'FAIL', r['samples'], r['end_dist'], r['bad_states'], r['z_minus_ground']), flush=True)
    ok = all(r['ok'] for r in res); print('PROBE_P2_%s' % name.upper(), 'PASS' if ok else 'FAIL', flush=True); return ok, res
if __name__ == '__main__':
    pos = JP.lua('local c=GetEntityCoords(PlayerPedId()) return string.format("%.2f,%.2f,%.2f,%.1f",c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))')
    print('saved ped at', pos); ok = True; out = {}
    try:
        for a in sys.argv[1:]:
            o, r = run(a, [('block round', ROUND)] if a == 'round' else STEPS); ok = ok and o; out[a] = r
    finally:
        x, y, z, h = pos.split(',')
        JP.lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) SetEntityHeading(p,%s) return "back"' % (x, y, z, h))
        JP.release(); JP.revive()
        JP.lua('local p=PlayerPedId() SetEntityCoords(p,%s,%s,%s) SetEntityHeading(p,%s) SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) ClearFocus() return "back"' % (x, y, z, h))
        json.dump(out, open(W / 'probe_p2_walk.json', 'w'), indent=1)
    sys.exit(0 if ok else 1)
