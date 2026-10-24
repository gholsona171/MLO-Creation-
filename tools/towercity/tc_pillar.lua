local H=math.rad(69.5) local O={-78.897,-827.328}
local function W(u,v) return O[1]+u*math.cos(H)-v*math.sin(H), O[2]+u*math.sin(H)+v*math.cos(H) end
local function ray(u0,v0,u1,v1,z) local x0,y0=W(u0,v0) local x1,y1=W(u1,v1) local h=StartExpensiveSynchronousShapeTestLosProbe(x0,y0,z,x1,y1,z,1,0,7) local _,hit,c=GetShapeTestResult(h) if hit==1 then local dx,dy=c.x-O[1],c.y-O[2] return string.format('HIT u%.2f v%.2f',dx*math.cos(H)+dy*math.sin(H),-dx*math.sin(H)+dy*math.cos(H)) end return 'none' end
local out={}
for _,z in ipairs({32.5,34.0,37.0,40.0}) do
 out[#out+1]=string.format('z%.1f old(v-21.3): %s | new(v-9.0): %s',z,ray(72.0,-21.31,80.0,-21.31,z),ray(72.0,-9.01,80.0,-9.01,z)) end
return table.concat(out,'\n')
