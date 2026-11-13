-- server eval (rig harness): buy the C9 tattoos for player SRC through rcore_tattoos' own buyTattoo API (charges the price).
-- Set ONLY = 'text' to buy just the tattoos whose name contains it.
local src = tonumber(SRC)
local list = json.decode(LoadResourceFile('rcore_tattoos', 'assets/tattooLists/C9Tattoos.json'))
local out = {}
local before = exports.qbx_core:GetPlayer(src).PlayerData.money
for _, t in ipairs(list) do
  if ONLY and not t.name:find(ONLY, 1, true) then goto continue end
  local p = promise.new()
  TriggerEvent('rcore_tattoos:buyTattoo', src, t.name, t.hashMale .. '-' .. t.hashFemale, false, 1, function(r) p:resolve(r) end)
  SetTimeout(5000, function() if p.state == 0 then p:resolve('timeout') end end)
  out[#out + 1] = { t.name, t.price, Citizen.Await(p) }
  ::continue::
end
local after = exports.qbx_core:GetPlayer(src).PlayerData.money
return { bought = out, bank_before = before.bank, cash_before = before.cash, bank_after = after.bank, cash_after = after.cash }
