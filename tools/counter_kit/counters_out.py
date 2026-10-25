#!/usr/bin/env python3
"""
c9_dj counter kit: writes everything counters.py builds.

    python prop/build/counters_out.py            # build + write (Windows: CodeWalker through cw.ps1)
    python prop/build/counters_out.py --check    # build + the joint check + the preview sheet only (writes nothing in stream/)
    python prop/build/counters_out.py --export   # the Rockstar drawables + textures from the game -> out/rsx/ (once; slow)

Writes: out/ctr/<model>/<model>.ydr.xml -> stream/<model>.ydr (our box collision inside), one texture dictionary per set / copy
(stream/c9dj_ctr_<key>.ytd: Rockstar's textures, each once), out/counters.json (tracked: every archetype for kit.py's ytyp, joints,
sizes, joint check), shared/barsnap_data.lua (the joints the placer snaps by), the catalogue rows between the markers in
config/business.lua, out/counters.png (tracked preview), then kit.py --ytyp-only (c9dj_kit.ytyp with the counters in it).
A joint off by more than 1.5 mm stops the build. MIT, our own code.
"""
import os, sys, json, shutil, subprocess, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rsx, rsxview
import counters as C
from counters_sets import SETS, COPIES, VANILLA, GROUPS, RECATEGORISE

OUT, RSX, ROOT = C.OUT, C.RSX, C.ROOT
CTR = os.path.join(OUT, 'ctr')
STREAM = os.path.join(ROOT, 'stream')
CW = os.path.join(HERE, 'cw.ps1')
JOINT_TOL = 0.0015
NAMES = {'straight': '%s m straight', 'oc': 'outside corner', 'ic': 'inside corner', 'el': 'left end', 'er': 'right end'}
WHAT = {'straight': 'A %s m straight run', 'oc': 'Outside corner: turns away from the guests', 'ic': 'Inside corner: turns towards the guests',
        'el': 'Closed left end of a run', 'er': 'Closed right end of a run'}
LIMITS = {'label': 40, 'desc': 140}      # shared/biz.lua cuts catalogue labels / descriptions at these lengths


def ps(*args):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', CW] + [str(a) for a in args], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit('cw.ps1 %s failed:\n%s\n%s' % (args[0], r.stdout, r.stderr))
    return r.stdout.strip()


def textures_of(model_names):
    names = set()
    for n in model_names:
        names |= set(C.source(n).textures)
    return sorted(names)


def palette_row(path, row):
    """a tint palette (uncompressed 32-bit .dds, one row per tint): row `row` copied into row 0. A *_tnt shader colours by the
    ENTITY's tint and a script-spawned object has tint 0; Rockstar's interiors set another row (the clubhouse leather is row 0 =
    cyan placeholder in the game file)"""
    b = bytearray(open(path, 'rb').read())
    h = int.from_bytes(b[12:16], 'little'); w = int.from_bytes(b[16:20], 'little')
    assert len(b) >= 128 + w * h * 4, 'palette is not uncompressed 32-bit: ' + path
    rb = w * 4
    b[128:128 + rb] = b[128 + row * rb:128 + (row + 1) * rb]
    open(path, 'wb').write(bytes(b))


def write_ytd(key, sources, build, palette=None):
    folder = os.path.join(CTR, 'tex_' + key)
    shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
    missing = []
    for t in textures_of(sources):
        src = os.path.join(RSX, 'tex', t + '.dds')
        if os.path.exists(src):
            shutil.copy(src, os.path.join(folder, t + '.dds'))
            if palette and t in palette: palette_row(os.path.join(folder, t + '.dds'), palette[t])
        else: missing.append(t)
    if build: print('  ', ps('ytd', folder, os.path.join(STREAM, C.PREFIX + key + '.ytd')))
    return missing


def write_model(name, m, boxes, mat, build, lod=120, bounds=None):
    d = os.path.join(CTR, name)
    os.makedirs(d, exist_ok=True)
    m = rsx.Model(name, m.shaders_xml, m.geos, m.textures)
    xml, (mn, mx) = rsx.ydr_xml(m, boxes, mat, lod, bounds)
    p = os.path.join(d, name + '.ydr.xml')
    open(p, 'w', encoding='utf-8').write(xml)
    if build: print('  ', ps('ydr', p, os.path.join(STREAM, name + '.ydr')))
    return [round(float(x), 4) for x in mn], [round(float(x), 4) for x in mx]


def copy_joints(key, which):
    """the open ends of a full-size copy as joints in ITS frame (Rockstar's, floor moved to 0): the set's run frame turned back"""
    s = SETS[key]
    run, M = C.run_frame(s)
    out = []
    for w in which:
        x = max(g.pos[:, 0].max() for g in run.geos) if w == 'max' else float(w)
        R, t = M[:3, :3], M[:3, 3]
        p = R.T @ (np.array([x, 0.0, 0.0]) - t)
        d = R.T @ np.array([1.0, 0.0, 0.0])                   # out of a right face = +X of the run
        h = float(np.degrees(np.arctan2(-d[0], d[1]))) % 360.0
        out.append((round(float(p[0]), 4), round(float(p[1]), 4), round(h, 3), 1))
    return out


def price(s, L):
    return int(round(s['per_m'] * max(L, 0.5) / 25.0) * 25)


def main():
    build = '--check' not in sys.argv
    os.makedirs(CTR, exist_ok=True)
    meta = {'archetypes': {}, 'sets': {}, 'copies': {}}
    snap = {}
    rows = []
    cells = []
    bad = []
    for key, s in SETS.items():
        print('set', key, s['label'])
        mods = C.build_set(key, s)
        rep = C.joint_report(mods, s)
        for k, g in rep.items():
            if g > s.get('joint_tol', JOINT_TOL): bad.append('%s_%s %.4f' % (key, k, g))
        missing = write_ytd(key, [s['src']], build, s.get('palette'))
        meta['sets'][key] = dict(label=s['label'], D=s['D'], H=mods[next(iter(mods))]['H'], joints_check=rep, missing_textures=missing)
        for suf, v in mods.items():
            name = C.PREFIX + key + '_' + suf
            mn, mx = write_model(name, v['model'], v['boxes'], s['mat'], build)
            meta['archetypes'][name] = dict(txd=C.PREFIX + key, min=mn, max=mx, set=key, kind=v['kind'], L=round(v['L'], 4),
                                            joints=v['joints'], tris=v['model'].tri_count(), boxes=len(v['boxes']))
            snap[name] = dict(set=key, j=v['joints'])
            piece = (NAMES[v['kind']] % ('%g' % round(v['L'], 2))) if v['kind'] == 'straight' else NAMES[v['kind']]
            what = (WHAT[v['kind']] % ('%g' % round(v['L'], 2))) if v['kind'] == 'straight' else WHAT[v['kind']]
            rows.append(dict(id='ctr_%s_%s' % (key, suf), label='%s: %s' % (s['short'], piece), model=name, price=price(s, v['L']),
                             desc='%s, %.2f m deep, %.2f m high. Snaps onto the other %s pieces.' % (what, s['D'], mods[suf]['H'], s['short']),
                             group=s.get('group', 'Bar counters')))
            if v['kind'] in ('straight', 'oc', 'el'):
                c = np.array([0, 0, 0.5])
                cells.append((name, rsxview.render([(v['model'], None)], os.path.join(RSX, 'tex'), size=(420, 300), eye=(-1.7, -2.1, 1.6), at=c, fov=45)))
    for key, cp in COPIES.items():
        print('copy', key, cp['label'])
        m = C.source(cp['src'])
        zmin = min(g.pos[:, 2].min() for g in m.geos)
        m = rsx.transform(m, None, (0, 0, -zmin))            # floor at z = 0 like the modules
        rb = rsx.rockstar_bounds(os.path.join(RSX, 'x', cp['src'] + '.ydr.xml'), -zmin)
        boxes = None if rb else C.auto_boxes(m)
        own = next((k for k, s in SETS.items() if s['src'] == cp['src']), None)      # a set's own source: share its textures
        txd = C.PREFIX + (own or key)
        missing = [] if own else write_ytd(key, [cp['src']], build, cp.get('palette'))
        name = C.PREFIX + key
        mn, mx = write_model(name, m, boxes, 0, build, bounds=rb)
        meta['archetypes'][name] = dict(txd=txd, min=mn, max=mx, copy_of=cp['src'], tris=m.tri_count(),
                                        collision='rockstar' if rb else '%d boxes' % len(boxes))
        meta['copies'][key] = dict(src=cp['src'], missing_textures=missing)
        if cp.get('ends'):
            j = copy_joints(*cp['ends'])
            snap[name] = dict(set=cp['ends'][0], j=j)
            meta['archetypes'][name]['joints'] = j
        rows.append(dict(id='ctr_' + key, label=cp['label'], model=name, price=cp['price'], desc=cp['desc'], group=cp['group']))
        c = (np.array(mn) + np.array(mx)) / 2
        r = float(np.linalg.norm(np.array(mx) - np.array(mn)))
        cells.append((name, rsxview.render([(m, None)], os.path.join(RSX, 'tex'), size=(420, 300), eye=(c[0] - 0.6 * r, c[1] - 0.9 * r, c[2] + 0.6 * r), at=c, fov=45)))
    for v in VANILLA:
        rows.append(dict(id=v['id'], label=v['label'], model=v['model'], price=v['price'], desc=v['desc'], group=v['group']))
    long = ['%s %s (%d > %d)' % (r['id'], k, len(r[k]), n) for r in rows for k, n in LIMITS.items() if len(r[k]) > n]
    if long: raise SystemExit('catalogue text too long: ' + '; '.join(long))
    if bad: raise SystemExit('joints off: ' + ', '.join(bad))
    rsxview.sheet(cells, 6, os.path.join(OUT, 'counters.png'), cell=(420, 300))
    meta['rows'] = rows
    json.dump(meta, open(os.path.join(OUT, 'counters.json'), 'w'), indent=1)
    if not build:
        print('checked: every joint within %.1f mm; out/counters.png' % (JOINT_TOL * 1000))
        return
    write_snap(snap)
    write_rows(rows)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'kit.py'), '--ytyp-only'], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip())
    if r.returncode: raise SystemExit('kit.py --ytyp-only failed')


def lua(v):
    if isinstance(v, str): return "'" + v.replace('\\', '\\\\').replace("'", "\\'") + "'"
    if isinstance(v, float): return ('%.4f' % v).rstrip('0').rstrip('.') if v != int(v) else '%.1f' % v
    return str(v)


def write_snap(snap):
    lines = ['-- GENERATED by prop/build/counters_out.py from the counter kit build: never edit by hand (shared/barsnap.lua reads it).',
             '-- [model] = { set, joints { x, y, out-heading, hand } } in the model\'s own frame: the floor point under the back edge of each',
             '-- open face, the heading out of it, 1 = a right face / -1 = a left face (only a left face and a right face meet).',
             'BarSnap = BarSnap or {}', 'BarSnap.DATA = BarSnap.DATA or {}', 'local D = BarSnap.DATA']
    for name in sorted(snap):
        j = ', '.join('{ %s, %s, %s, %d }' % (lua(float(x)), lua(float(y)), lua(float(h)), t) for x, y, h, t in snap[name]['j'])
        lines.append("D.%s = { set = '%s', j = { %s } }" % (name, snap[name]['set'], j))
    open(os.path.join(ROOT, 'shared', 'barsnap_data.lua'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')


BEGIN = '            -- ── counter kit (GENERATED by prop/build/counters_out.py from counters_sets.py: edit there, not here) ──'
END = '            -- ── end of the counter kit rows ──'


def write_rows(rows):
    p = os.path.join(ROOT, 'config', 'business.lua')
    src = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in src else '\n'
    body = [BEGIN]
    for g in GROUPS:
        body.append('            -- %s' % g)
        for r in [r for r in rows if r['group'] == g]:
            body.append(("            { id = %s, label = %s, category = %s, kind = 'surface', model = %s, price = %d," + nl +
                         "              desc = %s },") % (lua(r['id']), lua(r['label']), lua(g), lua(r['model']), r['price'], lua(r['desc'])))
    body.append(END)
    block = nl.join(body)
    for rid, cat in RECATEGORISE.items():          # the 1.9.0 'Counters' rows into the new categories (ids unchanged)
        src = re.sub(r"(\{ id = '%s', label = '[^']*', category = )'[^']*'" % re.escape(rid), lambda k: k.group(1) + "'%s'" % cat, src)
    if BEGIN in src:
        i, j = src.index(BEGIN), src.index(END) + len(END)
        src = src[:i] + block + src[j:]
    else:
        anchor = "            -- ── counters and work tops (1.9.0"
        i = src.index(anchor)
        src = src[:i] + block + nl + src[i:]
    open(p, 'w', encoding='utf-8', newline='').write(src)


def export():
    names = sorted(set([s['src'] for s in SETS.values()] + [c['src'] for c in COPIES.values()]))
    tools = os.environ.get('MLO_TOOLS', r'C:\Users\anton\Documents\Codex\MLO-Creation\tools')
    x = os.path.join(RSX, 'x')
    os.makedirs(x, exist_ok=True)
    subprocess.run(['powershell', '-NoProfile', '-File', os.path.join(tools, 'ydr_xml.ps1'), '-Mode', 'export', '-Name', ','.join(names), '-Out', x], check=True)
    want = textures_of(names)
    tex = os.path.join(RSX, 'tex')
    os.makedirs(tex, exist_ok=True)
    for n in names:                                   # textures embedded in the drawables first (the export wrote them beside)
        d = os.path.join(x, n)
        if os.path.isdir(d):
            for f in os.listdir(d): shutil.copy(os.path.join(d, f), os.path.join(tex, f.lower()))
    need = [t for t in want if not os.path.exists(os.path.join(tex, t + '.dds'))]
    if need: print(ps('tex', ','.join(need), tex, ','.join(sorted(set(t for s in list(SETS.values()) + list(COPIES.values()) for t in s.get('txd_from', []))))))


if __name__ == '__main__':
    export() if '--export' in sys.argv else main()
