"""Measure a seat prop from its CodeWalker ydr XML: the up-facing seat surfaces (height, x clusters) and where the backrest is (the
tall vertices' y). Usage: py -3 seat_probe.py file.ydr.xml"""
import sys, numpy as np
import xml.etree.ElementTree as ET
r = ET.parse(sys.argv[1]).getroot(); P = []; N = []
for vb in r.iter('VertexBuffer'):
    lay = [c.tag for c in vb.find('Layout')]
    for line in (vb.findtext('Data') or '').strip().splitlines():
        parts = [p.split() for p in line.strip().split('   ')]; d = dict(zip(lay, parts))
        P.append([float(x) for x in d['Position']]); N.append([float(x) for x in d['Normal']])
P = np.array(P); N = np.array(N)
up = (N[:, 2] > 0.8) & (P[:, 2] > 0.3) & (P[:, 2] < 0.7)
print('verts', len(P), 'bbox', P.min(0).round(3), P.max(0).round(3))
print('seat surface z (up-facing 0.3-0.7): median', np.median(P[up, 2]).round(3), 'p90', np.percentile(P[up, 2], 90).round(3) if up.any() else None)
h = np.histogram(P[up, 0], bins=np.arange(P[:, 0].min(), P[:, 0].max() + 0.1, 0.1))
print('seat x histogram (0.1 m bins):', [(round(b, 1), int(c)) for c, b in zip(h[0], h[1]) if c])
print('seat y range', P[up, 1].min().round(3), P[up, 1].max().round(3))
tall = P[:, 2] > 0.8
print('backrest (z > 0.8) y range', P[tall, 1].min().round(3), P[tall, 1].max().round(3), 'mean', P[tall, 1].mean().round(3))
