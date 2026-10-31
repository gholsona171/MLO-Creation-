"""Dressing gate for area 3 (Police HQ + B1), from the built layout (out/jc3_layout.json 'placed') and the built drawn faces
(out/tris_jc_courts_<room>.npy, world space):
  ROOM     every prop of a police / garage room stands inside that room's zone (2026-10-30: eleven patrol-room lockers had been left 4 m
           inside the public lobby after the colonnade moved; they belonged to another room and drew only when it was visible)
  WALL     every wall-hung prop (jc3_police_dress.WALL / jc3_pgarage_dress.WALL) has a built vertical face within 5 cm behind its back,
           and its span along that wall misses every door opening on its floor
  CEILING  every ceiling prop has a built down-facing face within 4 cm over its top
Proof: --plant moves a notice board 0.3 m off its wall, puts a lobby bench into another room and hangs a board across a doorway;
all three must be found. Run: py -3 jc3_dress_check.py [--plant]  (JC3_DRESS_PASS)"""
import json, math, sys
from pathlib import Path
import numpy as np
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc_frame as F, jc3_police_dress as PD, jc3_pgarage_dress as GD
L = json.load(open(P3 / 'out/jc3_layout.json'))
A = {k.lower(): v for k, v in json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig')).items()}
fv = lambda s: [float(x[2:]) for x in s.split()]
ROOMS = ('plobby', 'pdesk', 'pstaff1', 'pstaff2', 'pint1', 'pobs1', 'pobs2', 'pint2', 'pdeck')
WALL = PD.WALL | GD.WALL; CEIL = PD.CEILING | {'prop_cctv_cam_06a'}
FRONT = PD.FRONT
def lot(T):
    x, y = T[..., 0] - F.OX, T[..., 1] - F.OY; c, s = math.cos(F.H), math.sin(F.H)
    return np.stack([x * c + y * s, -x * s + y * c, T[..., 2]], -1)
def faces(room):
    T = lot(np.load(P3 / f'out/tris_jc_courts_{room}.npy').astype(np.float64))
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    return T, n
def hit(T, n, p, d, maxd):
    """distance along d (unit, lot frame) from p to the first triangle (Moller-Trumbore), or None within maxd."""
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; h = np.cross(d, e2); a = (e1 * h).sum(1); ok = np.abs(a) > 1e-9
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0); s = p - T[:, 0]; u = f * (s * h).sum(1); q = np.cross(s, e1); v = f * (q * d).sum(1)
    t = f * (q * e2).sum(1); m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > -0.02) & (t < maxd)
    return float(t[m].min()) if m.any() else None
def zones():
    return {k: [tuple(r) for r in L['zones'][k]] for k in ROOMS if k in L['zones']}
def check(placed, openings, plant=False):
    Z = zones(); FT = {r: faces(r) for r in ROOMS}; bad = []
    for q in placed:
        r, m = q['room'], q['model']
        if r not in Z: continue
        u, v = q['u'], q['v']
        if not any(z[0] - 0.05 <= u <= z[1] + 0.05 and z[2] - 0.05 <= v <= z[3] + 0.05 and z[4] - 0.3 <= q['base'] <= z[5] for z in Z[r]):
            bad.append(('ROOM', r, m, round(u, 2), round(v, 2)))
        lo, hi = fv(A[m.lower()]['bbMin']), fv(A[m.lower()]['bbMax']); h = math.radians(q['heading'])
        if m in CEIL:
            T, n = FT[r]; top = q['z'] + hi[2]; t = hit(T[n[:, 2] < -0.9], None, np.array([u, v, top - 0.02]), np.array([0.0, 0.0, 1.0]), 0.06)
            if t is None: bad.append(('CEILING', r, m, round(u, 2), round(v, 2)))
        elif m in WALL:
            sgn = -1.0 if FRONT.get(m, '-y') == '+y' else 1.0                # the back: +y for '-y'-facing models
            by = hi[1] if sgn > 0 else lo[1]; d = np.array([-math.sin(h) * sgn, math.cos(h) * sgn, 0.0])
            back = np.array([u, v, 0.0]) + d * abs(by); zc = q['z'] + (lo[2] + hi[2]) / 2
            T, n = FT[r]; vert = np.abs(n[:, 2]) < 0.1
            t = hit(T[vert], None, np.array([back[0], back[1], zc]) - d * 0.02, d, 0.07)
            if t is None: bad.append(('WALL', r, m, round(u, 2), round(v, 2)))
            ax = 'u' if abs(d[0]) > 0.5 else 'v'; along = v if ax == 'u' else u; half = (hi[0] - lo[0]) / 2
            plane = back[0] if ax == 'u' else back[1]
            for o in openings:
                if o['axis'] == ax and abs(o['plane'] - plane) < 0.35 and o['z0'] - 0.5 < zc < o['z1'] + 0.5 and o['z0'] < q['z'] + hi[2] and q['z'] + lo[2] < o['z1'] \
                        and along + half > o['a0'] and along - half < o['a1']:
                    bad.append(('DOOR', r, m, round(u, 2), round(v, 2), o['name']))
    return bad
def main():
    placed = [q for q in L['placed'] if q['room'] in ROOMS]; openings = L['openings']
    if '--plant' in sys.argv:
        q0 = next(q for q in placed if q['model'] == 'v_20_notbrd01' and q['room'] == 'plobby')
        moved = dict(q0); moved['u'] += 0.3                                      # 0.3 m off the lobby's west wall
        wrong = dict(next(q for q in placed if q['model'] == 'v_ilev_ph_bench' and q['room'] == 'plobby')); wrong['room'] = 'pstaff1'
        o = next(o for o in openings if o['name'] == 'P_in_brief')
        door = {'room': 'pstaff1', 'model': 'v_20_notbrd01', 'u': o['plane'] - 0.1 - 0.06, 'v': (o['a0'] + o['a1']) / 2, 'z': o['z0'] + 1.5,
                'base': o['z0'] + 0.9, 'heading': 270.0}
        bad = check([moved, wrong, door], openings)
        kinds = {b[0] for b in bad}
        assert {'WALL', 'ROOM', 'DOOR'} <= kinds, f'the dressing gate missed a plant: found {sorted(kinds)}'
        print('JC3_DRESS_PLANT_FOUND', sorted(kinds)); return 0
    bad = check(placed, openings)
    for b in bad[:40]: print(' ', *b)
    print(f'JC3_DRESS {len(placed)} props, {len(bad)} finding(s)'); print('JC3_DRESS_PASS' if not bad else 'JC3_DRESS_FAIL'); return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
