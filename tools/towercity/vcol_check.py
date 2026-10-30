"""Gate: vertex colour 0 of every BUILT Tower City drawable (resource/tower_city/stream, read back through CodeWalker XML).
G = artificial ambient: 1.0 on a wall lights it at night while the vanilla blocks go dark (2026-10-29). Fails on:
  - any NON-emissive vertex with G >= 250 (exterior or interior)
  - an interior room vertex whose colour is not one of tc_kit.VCOL_INT's classes (a room left on the kit default 0/124/0)
  - an emissive-shader vertex below 255 (signs, lamps, night windows keep 1.0)
Usage: py -3 tools/vcol_check.py [--xml <dir of *.ydr.xml>]   (default: converts the stream into logs/vcol_xml first)"""
import sys, subprocess, re, ast, xml.etree.ElementTree as ET
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); W = T / 'work'
def jo(s):
    h = 0
    for c in s.lower().encode(): h = (h + c) & 0xffffffff; h = (h + (h << 10)) & 0xffffffff; h ^= h >> 6
    h = (h + (h << 3)) & 0xffffffff; h ^= h >> 11; h = (h + (h << 15)) & 0xffffffff; return 'hash_%08X' % h
EMIS = {jo(n + '.sps') for n in ('emissive', 'emissivenight', 'emissivestrong', 'emissive_alpha', 'emissivenight_alpha', 'emissive_tnt')} | {
        n + '.sps' for n in ('emissive', 'emissivenight', 'emissivestrong', 'emissive_alpha', 'emissivenight_alpha', 'emissive_tnt')}
SRC = (W / 'tc_kit.py').read_text(encoding='utf-8')                        # the classes as the kit writes them (sRGB 0..1 -> 0..255)
VINT = ast.literal_eval(re.sub(r'#[^\n]*', '', re.search(r"^VCOL_INT = (\{.*?\}\})", SRC, re.S | re.M).group(1)))
OK_INT = {tuple(round(c * 255) for c in v[:3]) for cls in VINT.values() for v in cls.values()}
SKIP = re.compile(r'^tc_(empty|prop_)')                                    # tc_empty = nothing drawn; props: the prop kit's own
def main():
    a = sys.argv[1:]; xd = Path(a[a.index('--xml') + 1]) if '--xml' in a else W / 'logs/vcol_xml'
    if '--xml' not in a:
        xd.mkdir(parents=True, exist_ok=True); [f.unlink() for f in xd.glob('*.ydr.xml')]
        r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(W / 'tools/ydr_xml_dir.ps1'),
                            '-InDir', str(T / 'resource/tower_city/stream'), '-OutDir', str(xd)], capture_output=True, text=True)
        print(r.stdout.strip()); assert r.returncode == 0, r.stderr
        for d in xd.glob('*_tex'): subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', str(d)])
    files = sorted(f for f in xd.glob('tc_*.ydr.xml') if not SKIP.match(f.name))
    assert files, f'no tc_*.ydr.xml in {xd}: nothing was checked'
    bad = {}; nv = 0
    for f in files:
        name = f.name[:-8]; ext = name.endswith('_ext') or name in ('tc_ext_fix',) or name.startswith('tc_lot_')
        r = ET.parse(f).getroot(); sh = [s.findtext('FileName') for s in next(r.iter('Shaders')).findall('Item')]
        for g in r.iter('Geometries'):
            for it in g.findall('Item'):
                vb = it.find('VertexBuffer'); lay = [c.tag for c in vb.find('Layout')]
                if 'Colour0' not in lay: continue
                emis = sh[int(it.find('ShaderIndex').get('value'))] in EMIS; ci = lay.index('Colour0')
                for line in (vb.findtext('Data') or '').strip().splitlines():
                    c = tuple(int(x) for x in line.strip().split('   ')[ci].split()[:3]); nv += 1
                    why = ('emissive below 1.0' if c[1] < 255 else None) if emis else (
                        'G >= 250 (night glow)' if c[1] >= 250 else
                        None if ext or any(all(abs(c[i] - k[i]) <= 2 for i in range(3)) for k in OK_INT) else 'interior colour not a VCOL_INT class')
                    if why: b = bad.setdefault((name, why), [0, c]); b[0] += 1
    print('VCOL_CHECK', len(files), 'drawables', nv, 'vertices')
    for (n, why), (k, c) in sorted(bad.items()): print(f'    {n:24s} {why:38s} {k:7d} vertices, e.g. {c}')
    if bad: print('VCOL_CHECK_FAIL'); raise SystemExit(1)
    print('VCOL_CHECK_PASS')
if __name__ == '__main__': main()
