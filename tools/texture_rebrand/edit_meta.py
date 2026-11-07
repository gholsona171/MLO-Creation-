"""Point the station's readable ytyps / ymap at our props and drop the locked archetypes.
Works on CodeWalker's XML of the ORIGINAL files (names as hash_XXXXXXXX), writes edited XML for cw_meta.ps1 to compile.
usage: edit_meta.py <orig xml dir> <out xml dir>"""
import re, os, sys, math

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xffffffff; h = (h + (h << 10)) & 0xffffffff; h ^= h >> 6
    h = (h + (h << 3)) & 0xffffffff; h ^= h >> 11; h = (h + (h << 15)) & 0xffffffff
    return h


def H(name): return 'hash_%08X' % joaat(name)


def names_in(text, name):
    """an XML name can be written as text or as its hash"""
    return [name, H(name)]


REPLACE = {   # locked archetype -> ours (same bounds / pivot)
    'ibonoja_senora_sheriff_poster_1': 'cpd_poster_1', 'ibonoja_senora_sheriff_poster_2': 'cpd_poster_2',
    'ibonoja_senora_sheriff_poster_3': 'cpd_poster_3', 'ibonoja_senora_sheriff_poster_6': 'cpd_poster_6',
    'placa_ibonoja_gssh': 'cpd_plaque', 'cartel_comisaria_gssh': 'cpd_station_sign',
}
DROP_ONLY = ['ibonoja_senora_sheriff_poster_7', 'ibonoja_senora_sheriff_poster_bandera_eeuuu']   # defined, never placed
FLAGS = {'prop_flag_sheriff': 'cpd_flag_police', 'prop_flag_lsservices': 'cpd_flag_city'}


def split_items(t):
    """archetype <Item>s of a ytyp: (start, end, text) for each top-level archetype item"""
    out = []
    for m in re.finditer(r'  <Item type="C\w*ArchetypeDef">.*?\n  </Item>\n', t, re.S):
        out.append((m.start(), m.end(), m.group(0)))
    return out


def item_name(it):
    return re.search(r'<name>(.*?)</name>', it).group(1)


def arch_def(name, item_from, asset_type=None, lod=None, flags=None, bb=None):
    """our archetype: a copy of the original's def (bounds, flags, lod, hd distance) with our name and embedded textures"""
    it = item_from
    it = re.sub(r'<name>.*?</name>', '<name>%s</name>' % name, it)
    it = re.sub(r'<assetName>.*?</assetName>', '<assetName>%s</assetName>' % name, it)
    it = re.sub(r'<textureDictionary>.*?</textureDictionary>|<textureDictionary />', '<textureDictionary />', it)
    it = re.sub(r'<physicsDictionary>.*?</physicsDictionary>', '<physicsDictionary />', it)
    if asset_type: it = re.sub(r'<assetType>.*?</assetType>', '<assetType>%s</assetType>' % asset_type, it)
    if lod is not None: it = re.sub(r'<lodDist value="[^"]*" />', '<lodDist value="%s" />' % lod, it)
    if flags is not None: it = re.sub(r'<flags value="[^"]*" />', '<flags value="%s" />' % flags, it)
    if bb:
        (x0, y0, z0), (x1, y1, z1) = bb
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); r = math.dist(c, (x1, y1, z1))
        it = re.sub(r'<bbMin [^/]*/>', '<bbMin x="%g" y="%g" z="%g" />' % (x0, y0, z0), it)
        it = re.sub(r'<bbMax [^/]*/>', '<bbMax x="%g" y="%g" z="%g" />' % (x1, y1, z1), it)
        it = re.sub(r'<bsCentre [^/]*/>', '<bsCentre x="%g" y="%g" z="%g" />' % c, it)
        it = re.sub(r'<bsRadius value="[^"]*" />', '<bsRadius value="%g" />' % r, it)
    return it


log = []
# 1. int_props.ytyp: locked defs out, ours in (each copied from the def it replaces)
f = 'ibonoja_senora_sheriff_int_props.ytyp.xml'
t = open(os.path.join(SRC, f), encoding='utf-8').read()
items = split_items(t)
want = {H(k): k for k in list(REPLACE) + DROP_ONLY}
want.update({k: k for k in list(REPLACE) + DROP_ONLY})
new_items, removed = [], []
pieces, last = [], 0
for s, e, it in items:
    n = item_name(it)
    if n in want:
        orig = want[n]; removed.append(orig)
        pieces.append(t[last:s]); last = e
        if orig in REPLACE:
            pieces.append(arch_def(REPLACE[orig], it)); log.append('int_props: %s -> %s' % (orig, REPLACE[orig]))
        else:
            log.append('int_props: %s removed (never placed)' % orig)
pieces.append(t[last:])
t2 = ''.join(pieces)
assert sorted(removed) == sorted(list(REPLACE) + DROP_ONLY), removed
open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t2)

# 2. interior (MLO) ytyp: the placed entities now use our archetypes
for f in ('ibonoja_senora_sheriff_interior.ytyp.xml', 'ibonoja_senora_sheriff_taller_interior.ytyp.xml'):
    t = open(os.path.join(SRC, f), encoding='utf-8').read()
    for old, new in REPLACE.items():
        for form in names_in(t, old):
            k = t.count('<archetypeName>%s</archetypeName>' % form)
            if k:
                t = t.replace('<archetypeName>%s</archetypeName>' % form, '<archetypeName>%s</archetypeName>' % new); log.append('%s: %d x %s -> %s' % (f[:-9], k, old, new))
    for old in DROP_ONLY:
        for form in names_in(t, old):
            assert '<archetypeName>%s</archetypeName>' % form not in t, old
    open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t)

# 3. exterior ytyp: our two cloth flags (def copied from an exterior def, values from Rockstar's prop_flag_sheriff archetype)
f = 'ibonoja_senora_sheriff_ext.ytyp.xml'
t = open(os.path.join(SRC, f), encoding='utf-8').read()
tmpl = split_items(t)[0][2]
bb = ((-0.21, -3.266173, -0.979346), (0.2, 0.400872, 1.079345))
add = ''.join(arch_def(n, tmpl, 'ASSET_TYPE_FRAGMENT', 120, 570556416, bb) for n in FLAGS.values())
i = t.index('\n </archetypes>')
t = t[:i + 1] + add + t[i + 1:]
open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t); log.append('ext ytyp: + ' + ', '.join(FLAGS.values()))

# 4. exterior ymap: the two station flags point at ours; prop_flag_sa and prop_flagpole_2b stay (vanilla again once unstreamed)
f = 'ibonoja_senora_valley_sheriff.ymap.xml'
t = open(os.path.join(SRC, f), encoding='utf-8').read()
for old, new in FLAGS.items():
    k = 0
    for form in names_in(t, old):
        k += t.count('<archetypeName>%s</archetypeName>' % form)
        t = t.replace('<archetypeName>%s</archetypeName>' % form, '<archetypeName>%s</archetypeName>' % new)
    assert k == 1, (old, k); log.append('ymap: %s -> %s' % (old, new))
open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t)

# 5. parking-lot car generators (EDITABLE ymap): the 8 that named sheriff models missing on this server get the server's own
# police cars (wasabi_police garage: police, police2), alternating; the 19 open spots stay random
f = 'ibonoja_senora_valley_sheriff_cars.ymap.xml'
t = open(os.path.join(SRC, f), encoding='utf-8').read()
k = [0]
def car(m):
    k[0] += 1; return '<carModel>%s</carModel>' % ('police' if k[0] % 2 else 'police2')
t = re.sub(r'<carModel>hash_[0-9A-F]{8}</carModel>', car, t)
assert k[0] == 8, k[0]
open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t); log.append('cars ymap: %d generators -> police / police2' % k[0])
print('\n'.join(log))
