"""Which way a Rockstar model faces (before hanging it on a wall or backing it onto one): area of its high-LOD triangles whose normals
point along +x / -x / +y / -y, from the CodeWalker XML (vanilla_xml.ps1 / ydr_xml.ps1 export). The side with clearly more area is the
face it shows (a notice board's paper, a TV's screen, a sink unit's front); a near-even split means it is double-sided or symmetric
(lockers, shelving) - then look at the vertex heights (a toilet's tank is the tall side = its back). Proven on the two models measured in
game: Mission Row's v_20_notbrd01 -> +y, v_med_cor_whiteboard -> -y.
Usage: py -3 model_facing.py <xml dir> <name> [name ...]"""
import sys, math
import xml.etree.ElementTree as E
from pathlib import Path
D = Path(sys.argv[1])
for name in sys.argv[2:]:
    f = next((D / f'{name}.{k}.xml' for k in ('ydr', 'yft') if (D / f'{name}.{k}.xml').exists()), None)
    if f is None: print(name, 'NO XML'); continue
    r = E.parse(f).getroot(); hi = r.find('.//DrawableModelsHigh'); hi = r if hi is None else hi
    acc = {'+x': 0.0, '-x': 0.0, '+y': 0.0, '-y': 0.0}
    for g in [e for e in hi.iter() if e.find('VertexBuffer') is not None and e.find('IndexBuffer') is not None]:
        vb = g.find('VertexBuffer'); dn = vb.find('Data') if vb.find('Data') is not None else vb.find('Data2')
        P = [[float(x) for x in l.strip().split()[:3]] for l in dn.text.strip().splitlines()]
        I = [int(x) for x in g.find('IndexBuffer/Data').text.split()]
        for a, b, c in zip(I[0::3], I[1::3], I[2::3]):
            A, B, C = P[a], P[b], P[c]; u = [B[i] - A[i] for i in range(3)]; v = [C[i] - A[i] for i in range(3)]
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]); ar = math.sqrt(sum(x * x for x in n)) / 2
            if ar < 1e-9: continue
            nx, ny = n[0] / (2 * ar), n[1] / (2 * ar)
            if abs(nx) > 0.7: acc['+x' if nx > 0 else '-x'] += ar
            if abs(ny) > 0.7: acc['+y' if ny > 0 else '-y'] += ar
    best = max(acc, key=acc.get); other = {'+x': '-x', '-x': '+x', '+y': '-y', '-y': '+y'}[best]
    verdict = best if acc[best] > 1.3 * acc[other] else 'two-sided / symmetric'
    print(name, {k: round(v, 3) for k, v in acc.items()}, '->', verdict)
