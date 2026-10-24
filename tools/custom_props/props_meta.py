"""Tower City custom props, step 2 (after tc_props.py): CW XML -> game files in work/props/bin.
  * tc_prop_tv: the screen texture becomes a script render target the way Rockstar ships prop_tv_flat_01 (script_rt_tvscreen):
    Usage SCRIPT, uncompressed A8R8G8B8, one mip, 1024 x 512. The screen's bump / spec maps are renamed off the script_rt_ prefix.
  * both drawables imported with CodeWalker (survey/ydr_xml.ps1 -Mode import), then tc_props.ytyp (plain archetypes, embedded
    textures) compiled with TequiBuild, and survey/arch_ytyp.json told that tc_props holds them (so the tower MLO depends on it)."""
import json, re, struct, subprocess, numpy as np
import mlo_meta as MM
P = MM.T / 'work/props'; BIN = P / 'bin'; BIN.mkdir(parents=True, exist_ok=True)
RT, RW, RH = 'script_rt_tc_tvscreen', 1024, 512
def dds_argb(path, w, h, rgba):
    """uncompressed A8R8G8B8 DDS, one mip (what CodeWalker writes for Rockstar's script render targets)."""
    hdr = struct.pack('<4sIIIIIII44xII4sIIIIII16x', b'DDS ', 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, w, w * 4, 0, 1,
                      32, 0x41, b'\0\0\0\0', 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000, 0x1000)
    bgra = rgba[:, :, [2, 1, 0, 3]].astype(np.uint8); open(path, 'wb').write(hdr + bgra.tobytes())
def patch_tv():
    x = P / 'tc_prop_tv.ydr.xml'; s = x.read_text(encoding='utf-8')
    for suf, new in (('_bump', 'tc_tv_screen_n'), ('_spec', 'tc_tv_screen_s')):          # the screen's helper maps: not render targets
        s = s.replace(f'{RT}{suf}', new); src = P / 'tc_prop_tv' / f'{RT}{suf}.dds'
        if src.exists(): src.replace(P / 'tc_prop_tv' / f'{new}.dds')
    item = re.search(r'<Item>\s*<Name>' + RT + r'</Name>.*?</Item>', s, re.S)
    assert item, 'render target texture missing from the TV xml'
    t = item.group(0)
    for tag, val in (('Usage', 'SCRIPT'), ('Format', 'D3DFMT_A8R8G8B8')): t = re.sub(f'<{tag}>[^<]*</{tag}>', f'<{tag}>{val}</{tag}>', t)
    t = re.sub(r'<MipLevels value="\d+" />', '<MipLevels value="1" />', t); t = re.sub(r'<Width value="\d+" />', f'<Width value="{RW}" />', t)
    t = re.sub(r'<Height value="\d+" />', f'<Height value="{RH}" />', t)
    t = re.sub(r'<UsageFlags>[^<]*</UsageFlags>', '<UsageFlags>X1024, UNK24</UsageFlags>', t) if '<UsageFlags>' in t else t.replace('<Usage>SCRIPT</Usage>', '<Usage>SCRIPT</Usage>\n        <UsageFlags>X1024, UNK24</UsageFlags>')
    s = s.replace(item.group(0), t); x.write_text(s, encoding='utf-8')
    px = np.zeros((RH, RW, 4), np.uint8); px[:, :, 3] = 255; px[:, :, :3] = (2, 2, 3)        # off: near-black glass
    dds_argb(P / 'tc_prop_tv' / f'{RT}.dds', RW, RH, px)
def imp(name):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(MM.T / 'survey/ydr_xml.ps1'), '-Mode', 'import',
                        '-In', str(P / f'{name}.ydr.xml'), '-Out', str(BIN / f'{name}.ydr')], capture_output=True, text=True)
    assert (BIN / f'{name}.ydr').exists(), r.stdout + r.stderr
    print(name, r.stdout.strip())
patch_tv()
INFO = json.load(open(P / 'props.json'))
for n in INFO: imp(n)
root, arches = MM._types('tc_props')
for n, d in INFO.items(): MM.base(arches, n, d['bb_lo'], d['bb_hi'], 150, 75)
MM._close(root, 'tc_props', P)
bad = MM.compile_all(P, ('tc_props.ytyp',)); assert not bad, bad
S = MM.T / 'survey/arch_ytyp.json'; A = json.load(open(S, encoding='utf-8-sig'))
for n, d in INFO.items():
    A[n] = {'ytyp': 'tc_props', 'path': 'tower_city/stream/tc_props.ytyp', 'bbMin': 'X:{} Y:{} Z:{}'.format(*d['bb_lo']), 'bbMax': 'X:{} Y:{} Z:{}'.format(*d['bb_hi'])}
json.dump(A, open(S, 'w', encoding='utf-8'), indent=2)
print('PROPS_META_PASS', sorted(p.name for p in BIN.iterdir()))
