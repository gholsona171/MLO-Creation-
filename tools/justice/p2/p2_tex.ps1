# Justice Center phase 2: copies Rockstar's own textures used by the p2 recipes (read-only on the game) into work/p2/tex_rs as DDS
# (top mip chain as stored; CodeWalker DDSIO.GetDDSFile). Each entry: texture name -> the ytd / ydr it is taken from (the HD copy).
# Recipes (shader + parameters) are in p2_mats.py. Re-run wipes tex_rs.
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$Out = Join-Path $PSScriptRoot 'tex_rs'; Remove-Item -Recurse -Force $Out -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Force $Out | Out-Null
$want = [ordered]@{
  'ko_gv_wall' = 'hw1_26+hi.ytd'; 'ko_gv_wall02_n' = 'hw1_26_build01.ydr'                       # the granite: Hollywood hw1_26's warm stone panels
  'im_roof04_big' = '*'; 'im_roof4_n' = '*'; 'im_roof04' = '*'                # roofs: the old courts tower's own roof
  'mc_wall_0001' = 'sc1_19_build3+hi.ytd'                                                          # Jail II cream panels (the old block's panel wall)
  'sc1_19_rsd_jp_brick_0001' = 'sc1_19_ground.ydr'; 'sc1_19_rsd_jp_brick_0001_n' = 'sc1_19_ground.ydr'                           # the plaza's red-brick bands (the old plaza's brick)
  'im_grass10deepb' = '*'                                                    # the lawn (the old block's lawn layer 0; default.sps, no normal)
  'im_kerbs03' = '*'; 'im_kerbs03_n' = '*'                                                         # granite kerbs / step nosings
  'im_glass_01im_glass_01_a' = 'dt1_06_build.ytd'; 'mc_window_0005_n' = 'dt1_06_build.ytd'; 'im_glass_01_s' = 'ch2struc04grp.ytd'   # Rockstar's exterior dark glass (dt1_06_build1_1, glass_env.sps)
}
$found = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    $n = $e.Name.ToLower(); if (-not ($n.EndsWith('.ytd') -or $n.EndsWith('.ydr')) -or $e.Path -notmatch '_citye|_cityw|generic.gtxd') { continue }
    if ($n.EndsWith('.ydr') -and -not ($want.Values -contains $n)) { continue }
    if ($n.EndsWith('.ytd') -and $e.Path -notmatch 'hw1_26|sc1_19|sc1_rd|scentral|dt1_06|ch2struc04grp') { continue }
    try {
      if ($n.EndsWith('.ytd')) { $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e); $tex = $y.TextureDict.Textures.data_items }
      else { $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($e.File.ExtractFile($e), $e); $tex = $y.Drawable.ShaderGroup.TextureDictionary.Textures.data_items }
    } catch { continue }
    foreach ($t in $tex) { $k = $t.Name.ToLower()
      if (-not $want.Contains($k)) { continue }
      $src = $want[$k]; if ($src -ne '*' -and $src -ne $n) { continue }
      if ($found.ContainsKey($k) -and $found[$k][1] -ge $t.Width) { continue }                     # keep the largest copy
      [IO.File]::WriteAllBytes((Join-Path $Out "$k.dds"), [CodeWalker.Utils.DDSIO]::GetDDSFile($t)); $found[$k] = @($e.Path, $t.Width) } } }
foreach ($k in $want.Keys) { if ($found.ContainsKey($k)) { "TEX $k $($found[$k][1]) <- $($found[$k][0])" } else { "MISSING $k" } }
