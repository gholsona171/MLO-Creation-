"""build_tv_pack.py <out resources dir> <screens.json>: writes the standalone TV resource `tc_tv` (our wall TV with its own script
render target) for any map we ship.
  * tc_prop_tv.ydr: the Tower City TV exactly as built (TowerCity work/tc_props.py + props_meta.py: screen = render target
    'tc_tvscreen', texture script_rt_tc_tvscreen, 1024 x 512, Usage SCRIPT). Copied, never rebuilt here.
  * tc_tv.ytyp: one plain archetype (tc_prop_tv only; Tower City's tc_props.ytyp also carries the urinal, faucet and mirror).
  * client.lua / fxmanifest.lua / README.md from resource/ (this folder); config.lua written from screens.json:
    [{"name": "...", "x": .., "y": .., "z": .., "title": "...", "sub": "..."}] (the TVs' positions: map TVs are MLO entities, which
    scripts cannot find, so the idle screen needs them listed).
A map that places tc_prop_tv puts `dependency 'tc_tv'` in its fxmanifest (the ytyp must be registered before the MLO loads).
Prints TV_PACK_PASS."""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, r'C:\Users\anton\Documents\Codex\TowerCity\work')
import mlo_meta as MM

HERE = Path(__file__).resolve().parent
PROPS = Path(r'C:\Users\anton\Documents\Codex\TowerCity\work\props')
out_dir, screens = Path(sys.argv[1]), json.load(open(sys.argv[2]))
R = out_dir / 'tc_tv'
if R.exists(): shutil.rmtree(R)
(R / 'stream').mkdir(parents=True)
shutil.copy2(PROPS / 'bin' / 'tc_prop_tv.ydr', R / 'stream')
bb = json.load(open(PROPS / 'props.json'))['tc_prop_tv']
work = HERE / 'work'; work.mkdir(exist_ok=True)
root, arches = MM._types('tc_tv'); MM.base(arches, 'tc_prop_tv', bb['bb_lo'], bb['bb_hi'], 150, 75); MM._close(root, 'tc_tv', work)
bad = MM.compile_all(work, ('tc_tv.ytyp',)); assert not bad, bad
shutil.copy2(work / 'bin' / 'tc_tv.ytyp', R / 'stream')
for f in ('fxmanifest.lua', 'client.lua', 'README.md'): shutil.copy2(HERE / 'resource' / f, R / f)


def lua_str(s): return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


rows = [f"    {{ name = {lua_str(s['name'])}, pos = vector3({s['x']:.3f}, {s['y']:.3f}, {s['z']:.3f}), title = {lua_str(s.get('title', ''))}, sub = {lua_str(s.get('sub', ''))} }},"
        for s in screens]
(R / 'config.lua').write_text('\n'.join([
    'Config = {}',
    '-- Every tc_prop_tv placed in your maps: where it hangs (world position) and what the idle screen shows on it when no TV script',
    '-- is using the screen. The idle screen draws while a player is within Config.Range metres of one of these.',
    'Config.Range = 22.0',
    'Config.Screens = {', *rows, '}', '']), encoding='utf-8', newline='\n')
print('TV_PACK_PASS', R, len(screens), 'screens', sorted(p.name for p in (R / 'stream').iterdir()))
