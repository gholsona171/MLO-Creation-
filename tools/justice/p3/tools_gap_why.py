"""debug (offline): explain gap-check rays - for each sampled gap ray of out/gap_check_rooms.json, the first triangle of ANY room it would
hit (which drawable, front or back face, distance, where). Run: py -3 tools_gap_why.py <room> [n]"""
import json, sys, numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'out'
room = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
R = json.load(open(OUT / 'gap_check_rooms.json'))['per_room_samples'][room][:n]
TR = {}
for f in OUT.glob('tris_jc_courts_*.npy'):
    T = np.load(f).astype(np.float64)
    import math
    L = json.load(open(OUT / 'jc3_layout.json')); ox, oy, h = L['origin'][0], L['origin'][1], math.radians(L['heading'])
    x, y = T[..., 0] - ox, T[..., 1] - oy; T = np.stack([x * math.cos(h) + y * math.sin(h), -x * math.sin(h) + y * math.cos(h), T[..., 2]], -1)
    TR[f.stem[5:]] = T
for g in R:
    o = np.array(g['from']); d = np.array(g['dir']); best = (np.inf, None, None, None)
    for name, T in TR.items():
        e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; pv = np.cross(d, e2); det = (e1 * pv).sum(1)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - T[:, 0]
        u = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); v = (qv * d).sum(1) * inv; t = (e2 * qv).sum(1) * inv
        ok &= (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
        if ok.any():
            i = np.argmin(np.where(ok, t, np.inf))
            if t[i] < best[0]: best = (t[i], name, 'front' if (np.cross(e1[i], e2[i]) @ d) < 0 else 'BACK', (o + t[i] * d).round(2))
    print(g['from'], g['dir'], '->', round(best[0], 2) if best[1] else None, best[1], best[2], best[3])
