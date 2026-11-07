"""Our cloth flags: Rockstar's prop_flag_sheriff cloth fragment (exported from the game by CodeWalker) re-issued under our own name
with our own texture. usage: make_flags.py <vanilla prop_flag_sheriff.yft.xml> <xml out dir>"""
import re, sys, os
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
for name in ('cpd_flag_police', 'cpd_flag_city'):
    x = re.sub('prop_flag_sheriff', name, t, flags=re.I)
    assert 'sheriff' not in x.lower(), 'leftover name'
    open(os.path.join(out, name + '.yft.xml'), 'w', encoding='utf-8').write(x)
    assert os.path.exists(os.path.join(out, name, name + '.dds'))
    print(name, len(x))
