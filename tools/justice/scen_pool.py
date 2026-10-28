"""Justice Center (rig): how many scenario blocking areas can still be added on client 1 right now - the shared pool every resource draws
from. Adds 2 m boxes far out at sea one by one, checks DoesScenarioBlockingAreaExist after each, stops at the first that does not hold,
then removes every test box it added (RemoveScenarioBlockingArea by handle). A probe: the first box must hold, or nothing was proven.
Run: py -3 tools/scen_pool.py   -> SCEN_POOL free <n> (first failing add #n+1), handles seen"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent)); import jc_probe as P
code = """local hs={} local n=0 local first=nil for i=1,300 do local x=-3000.0-i*5.0 local h=AddScenarioBlockingArea(x,-3000.0,0.0,x+2.0,-2998.0,10.0,false,true,true,true)
 if DoesScenarioBlockingAreaExist(x,-3000.0,0.0,x+2.0,-2998.0,10.0) then n=n+1 hs[#hs+1]=h if not first then first=h end else hs[#hs+1]=h break end end
local last=hs[#hs] for _,h in ipairs(hs) do RemoveScenarioBlockingArea(h,false) end
local still=DoesScenarioBlockingAreaExist(-3005.0,-3000.0,0.0,-3003.0,-2998.0,10.0)
return n..'|'..tostring(first)..'|'..tostring(last)..'|'..tostring(still)"""
r = P.lua(code, 60).split('|')
print('SCEN_POOL free', r[0], '| first handle', r[1], '| handle of the first add that did not hold', r[2], '| test boxes left after removal:', r[3])
if r[0] == '0': print('SCEN_POOL: not even one test box held - the pool is full or the natives do not work here (no proof either way)')
