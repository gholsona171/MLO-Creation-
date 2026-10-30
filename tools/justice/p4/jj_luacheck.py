"""Offline Lua syntax check of the code our rig tools send (FiveM runs Lua 5.4; lupa's runtime compiles it without running it), so a
typo is found here and not as a silent failure on the rig. Run: py -3 jj_luacheck.py  (JJ_LUA_PASS)"""
import subprocess, sys
from pathlib import Path
import lupa
JL = Path(__file__).resolve().parent
lua = lupa.LuaRuntime()
compile_ = lua.eval('function(s) local f, e = load(s) return e end')
bad = []
for mode in ('open', 'close'):
    code = subprocess.run([sys.executable, str(JL / 'jj_doorctl.py'), mode, '--dry'], capture_output=True, text=True).stdout
    e = compile_(code)
    if e: bad.append(('doorctl ' + mode, e))
plant = compile_('local x = = 1')
assert plant, 'the Lua syntax check did not find its planted error'
for b in bad: print(' ', *b)
print('JJ_LUA_PASS' if not bad else 'JJ_LUA_FAIL'); sys.exit(1 if bad else 0)
