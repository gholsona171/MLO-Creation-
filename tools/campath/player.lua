-- campath player (sent by campath.sh into the rig harness; the track is already in _G.__cp, the options in _G.__cpopt).
-- Plays every shot of the track: camera on a Catmull-Rom through the 10 Hz samples (smooth at any frame rate), a light hand-held
-- shake, streaming focus moved ahead along the path, the invisible ped kept at the camera (so the right interior room renders),
-- doors on the way opened as the camera nears them, and a dip to black between shots (a few seconds of black while the next shot
-- streams in; campath_cut.py trims those down). Probe mode: no fades or waits for looks, every frame swept with a shape test, hits in
-- _G.__cphits. _G.__cprun = 'run' | 'done'.
local D, O = _G.__cp, _G.__cpopt or {}
local PROBE = O.probe
local DOORS = {}
for _, m in ipairs(O.doors or {}) do DOORS[joaat(m)] = m end
_G.__cprun = 'run'; _G.__cphits = {}
local function cr(A, f)
  local n = #A; if n == 1 then return A[1] end
  local i = math.floor(f); local u = f - i; i = i + 1
  local function g(k) return A[math.max(1, math.min(n, k))] end
  local p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
  return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)
end
local function quiet(on)
  LocalPlayer.state:set('syncWeather', not on, false)
  TriggerEvent(on and 'qb-weathersync:client:DisableSync' or 'qb-weathersync:client:EnableSync')
  TriggerEvent('dd_hud:client:setVisible', not on)
  DisplayRadar(not on); DisplayHud(not on)
end
local opened = {}
local function open_doors(p)
  for _, o in ipairs(GetGamePool('CObject')) do
    local m = GetEntityModel(o)
    if DOORS[m] and not opened[o] then
      local c = GetEntityCoords(o)
      if #(c - p) < 22.0 then
        local h = joaat(('campath_%d_%d_%d'):format(math.floor(c.x * 10), math.floor(c.y * 10), math.floor(c.z * 10)))
        if not IsDoorRegisteredWithSystem(h) then AddDoorToSystem(h, m, c.x, c.y, c.z, false, false, false) end
        DoorSystemSetDoorState(h, 0, false, true); DoorSystemSetHoldOpen(h, true)
        DoorSystemSetOpenRatio(h, (O.ratio and O.ratio[DOORS[m]]) or 1.0, false, true)
        opened[o] = h
      end
    end
  end
end
CreateThread(function()
  local ped = PlayerPedId()
  quiet(true)
  SetEntityInvincible(ped, true); SetPlayerInvincible(PlayerId(), true); SetEntityVisible(ped, false, false)
  SetEntityCollision(ped, false, false); FreezeEntityPosition(ped, false)
  if _G.__cpcam then DestroyCam(_G.__cpcam, false) end
  local cam = CreateCam('DEFAULT_SCRIPTED_CAMERA', true); _G.__cpcam = cam
  RenderScriptCams(true, false, 0, true, true)
  if (D.shake or 0) > 0 and not PROBE then ShakeCam(cam, 'HAND_SHAKE', D.shake) end
  if not PROBE then DoScreenFadeOut(0) end
  for si, s in ipairs(D.shots) do
    if _G.__cprun ~= 'run' then break end
    local n, rate = #s.x, 1.0 / s.dt
    local function put(f)
      local x, y, z = cr(s.x, f), cr(s.y, f), cr(s.z, f)
      SetCamCoord(cam, x, y, z); SetCamRot(cam, cr(s.pitch, f), 0.0, cr(s.yaw, f), 2); SetCamFov(cam, cr(s.fov, f))
      local f2 = math.min(n - 1, f + rate * 0.5)
      SetFocusPosAndVel(x, y, z, (cr(s.x, f2) - x) * 2, (cr(s.y, f2) - y) * 2, (cr(s.z, f2) - z) * 2)
      SetEntityCoordsNoOffset(ped, x, y, z - 0.6, false, false, false)
      return vector3(x, y, z)
    end
    local p0 = put(0.0)
    NetworkOverrideClockTime(math.floor(s.hour), math.floor((s.hour % 1) * 60), 0); SetWeatherTypeNowPersist(O.weather or 'EXTRASUNNY')
    if not PROBE then
      NewLoadSceneStartSphere(p0.x, p0.y, p0.z, 80.0, 0)
      local t0 = GetGameTimer()
      while not IsNewLoadSceneLoaded() and GetGameTimer() - t0 < 6000 do open_doors(p0); Wait(0) end
      NewLoadSceneStop()
      local t1 = GetGameTimer()
      while GetGameTimer() - t1 < 1800 do put(0.0); open_doors(p0); NetworkOverrideClockTime(math.floor(s.hour), math.floor((s.hour % 1) * 60), 0); Wait(0) end
      DoScreenFadeIn(700)
    end
    local t0, prev, last = GetGameTimer(), p0, -1
    local speed = PROBE and (O.probe_speed or 2.0) or 1.0
    while _G.__cprun == 'run' do
      local e = (GetGameTimer() - t0) / 1000.0 * speed
      if e >= s.dur then break end
      local p = put(math.min(n - 1, e * rate))
      NetworkOverrideClockTime(math.floor(s.hour), math.floor((s.hour % 1) * 60), 0)
      open_doors(p)
      if PROBE then
        local h = StartExpensiveSynchronousShapeTestLosProbe(prev.x, prev.y, prev.z, p.x, p.y, p.z, 1 | 16, ped, 7)
        local _, hit, at, _, ent = GetShapeTestResult(h)
        local function note(kind, pt, e2)
          local k = ('%d:%d'):format(si, math.floor(e))
          if k ~= last then last = k; _G.__cphits[#_G.__cphits + 1] = { shot = si, t = math.floor(e * 10) / 10, kind = kind,
            x = math.floor(pt.x * 100) / 100, y = math.floor(pt.y * 100) / 100, z = math.floor(pt.z * 100) / 100,
            model = (e2 and e2 ~= 0 and DoesEntityExist(e2)) and GetEntityModel(e2) or 0 } end
        end
        if hit == 1 then note('crossed', at, ent) end
        for _, d in ipairs({ { .3, 0, 0 }, { -.3, 0, 0 }, { 0, .3, 0 }, { 0, -.3, 0 }, { 0, 0, .3 }, { 0, 0, -.3 } }) do
          local h2 = StartExpensiveSynchronousShapeTestLosProbe(p.x, p.y, p.z, p.x + d[1], p.y + d[2], p.z + d[3], 1 | 16, ped, 7)
          local _, hit2, at2, _, ent2 = GetShapeTestResult(h2)
          if hit2 == 1 then note('near', at2, ent2) break end
        end
      elseif s.dur - e < 0.7 and not IsScreenFadingOut() and not IsScreenFadedOut() then DoScreenFadeOut(700) end
      prev = p; Wait(0)
    end
    if not PROBE then while not IsScreenFadedOut() do Wait(0) end end
  end
  for o, h in pairs(opened) do DoorSystemSetHoldOpen(h, false); DoorSystemSetOpenRatio(h, 0.0, false, true); RemoveDoorFromSystem(h) end
  StopCamShaking(cam, true); RenderScriptCams(false, false, 0, true, true); DestroyCam(cam, false); _G.__cpcam = nil
  ClearFocus(); SetEntityVisible(ped, true, false); SetEntityCollision(ped, true, true)
  quiet(false); DoScreenFadeIn(500)
  _G.__cprun = 'done'
end)
return 'campath started'
