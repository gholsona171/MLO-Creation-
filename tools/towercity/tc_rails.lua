local H=math.rad(69.5) local O={-78.897,-827.328}
local function W(u,v) return O[1]+u*math.cos(H)-v*math.sin(H), O[2]+u*math.sin(H)+v*math.cos(H) end
local function ray(u,v0,v1,z) local x0,y0=W(u,v0) local x1,y1=W(u,v1) local h=StartExpensiveSynchronousShapeTestLosProbe(x0,y0,z,x1,y1,z,1,0,7) local _,hit,c=GetShapeTestResult(h) if hit==1 then local dx,dy=c.x-O[1],c.y-O[2] return string.format('v%.2f',-dx*math.sin(H)+dy*math.cos(H)) end return 'NONE' end
local out={}
for _,q in ipairs({{-2.8,34.6},{9.2,36.3},{21.3,38.1},{33.2,39.8},{39.3,40.7},{46.0,41.6},{52.7,42.5},{61.4,43.1},{70.2,43.2}}) do
 out[#out+1]=string.format('u%.1f podium-side: %s | outer: %s',q[1],ray(q[1],-73.0,-58.5,q[2]+0.6),ray(q[1],-73.0,-95.0,q[2]+0.6)) end
return table.concat(out,'\n')
