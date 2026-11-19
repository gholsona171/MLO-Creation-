_G.MS = _G.MS or {}
local MS = _G.MS
if GetResourceState('osp_ambulance')=='started' and exports.osp_ambulance:isDead() then TriggerEvent('hospital:client:Revive', true) Wait(2500) end
SetEntityInvincible(cache.ped,true) SetPlayerInvincible(PlayerId(),true) SetEntityCanBeDamaged(cache.ped,false)
function MS.yaw(i) local _,_,z,w = GetInteriorRotation(i) return 2*math.atan(z,w) end
function MS.w(i,lx,ly,lz) local px,py,pz=GetInteriorPosition(i) local y=MS.yaw(i) local c,s=math.cos(y),math.sin(y) return vector3(px+lx*c-ly*s, py+lx*s+ly*c, pz+lz) end
function MS.ray(a,b) local h=StartExpensiveSynchronousShapeTestLosProbe(a.x,a.y,a.z,b.x,b.y,b.z,1+16,cache.ped,7) local _,hit,pos=GetShapeTestResult(h) return hit==1,pos end
function MS.cam(pos,look,fov)
  LocalPlayer.state:set('syncWeather',false,false) TriggerEvent('qb-weathersync:client:DisableSync') TriggerEvent('dd_hud:client:setVisible',false)
  NetworkOverrideClockTime(13,0,0) ClearOverrideWeather() SetWeatherTypeNowPersist('EXTRASUNNY')
  SetEntityVisible(cache.ped,false,false)
  if MS.c then DestroyCam(MS.c,false) end
  MS.c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',pos.x,pos.y,pos.z,0,0,0,fov or 60.0,true,2)
  PointCamAtCoord(MS.c,look.x,look.y,look.z) RenderScriptCams(true,false,0,true,true)
  SetFocusPosAndVel(pos.x,pos.y,pos.z,0,0,0) DisplayRadar(false)
end
function MS.off() if MS.c then RenderScriptCams(false,false,0,true,true) DestroyCam(MS.c,false) MS.c=nil end ClearFocus() SetEntityVisible(cache.ped,true,false) DisplayRadar(true) end
-- safe corner inside room r: from room centre toward a corner (sx,sy = -1/1), stop 0.7 m before the first wall
function MS.corner(i,r,sx,sy,eye)
  local a,b,c,d,e,f=GetInteriorRoomExtents(i,r)
  local fz=c+1.0+(eye or 0.6)
  local ctr=MS.w(i,(a+d)/2,(b+e)/2,fz)
  local far=MS.w(i, sx<0 and a or d, sy<0 and b or e, fz)
  local hit,pos=MS.ray(ctr,far)
  local tgt= hit and pos or far
  local dir=tgt-ctr local L=#dir
  local p=ctr+dir*((L-0.7)/L)
  local hit2=MS.ray(ctr,p)
  return p, ctr, hit, L
end
