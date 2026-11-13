"""Read a CodeWalker ydd XML (freemode uppr_000_r): every geometry's vertices (position, blend indices/weights, TexCoord0/1) and
triangles. Saves <xml>.npz and prints TexCoord ranges per geometry.  usage: mesh_uv.py <ydd.xml>"""
import re, sys, numpy as np
src = open(sys.argv[1], encoding='utf-8').read()
out = {}
for gi, g in enumerate(re.findall(r'<VertexBuffer>(.*?)</IndexBuffer>', src, re.S)):
    lay = re.findall(r'<(\w+) />', re.search(r'<Layout[^>]*>(.*?)</Layout>', g, re.S).group(1))
    sizes = dict(Position=3, BlendWeights=4, BlendIndices=4, Normal=3, Colour0=4, Colour1=4, TexCoord0=2, TexCoord1=2, TexCoord2=2, Tangent=4)
    rows = [l.split() for l in re.search(r'<Data>(.*?)</Data>', g, re.S).group(1).strip().splitlines()]
    data = np.array([[float(v) for v in r] for r in rows])
    col = 0; d = {}
    for f in lay:
        d[f] = data[:, col:col + sizes[f]]; col += sizes[f]
    idx = np.array(re.search(r'<IndexBuffer>\s*<Data>(.*?)</Data>', g + '</IndexBuffer>', re.S).group(1).split(), int) if '<IndexBuffer>' in g else None
    for k, v in d.items():
        out[f'g{gi}_{k}'] = v
    if idx is not None:
        out[f'g{gi}_tri'] = idx.reshape(-1, 3)
    print(gi, lay, len(data), {k: (v.min(0).round(2).tolist(), v.max(0).round(2).tolist()) for k, v in d.items() if k.startswith(('Tex', 'Pos'))})
np.savez(sys.argv[1] + '.npz', **out)
