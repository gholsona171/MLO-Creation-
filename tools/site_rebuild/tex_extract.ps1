# tex_extract.ps1 (read-only on the game): named textures saved as .dds into ..\tex\vanilla\ or -OutDir.
#   name          found through ..\survey\tex_scan.tsv (tex_scan.ps1): the largest copy of that name
#   name@dict     taken from that texture dictionary (e.g. sc1_rsn_ns_ground_0010@ch1_10_house102+hidr.ytd), for textures no scan lists
# Usage: -Names "a,b@c.ytd,..." [-OutDir <folder>]
param([string]$Names, [string]$OutDir = "")
$ErrorActionPreference = 'Stop'
$M = Split-Path $PSScriptRoot -Parent; $Out = if ($OutDir) { $OutDir } else { Join-Path $M 'tex\vanilla' }; New-Item -ItemType Directory -Force $Out | Out-Null
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$rows = Get-Content (Join-Path $M 'survey\tex_scan.tsv') | % { , $_.Split("`t") }
$dicts = @{}
foreach ($d in ($Names.Split(',') | ? { $_ -match '@' } | % { $_.Split('@')[1] })) { $dicts[$d] = $null }
if ($dicts.Count) { foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($dicts.ContainsKey($e.Name) -and -not $dicts[$e.Name]) { $dicts[$e.Name] = $e } } } }
foreach ($spec in $Names.Split(',')) {
  if ($spec -match '@') { $n, $d = $spec.Split('@'); $e = $dicts[$d]; if (-not $e) { throw "no dictionary $d" }; $src = $d }
  else { $n = $spec
    $r = $rows | ? { $_[0] -eq $n } | Sort-Object { -[int]($_[1].Split("x")[0]) } | Select-Object -First 1
    if (-not $r) { throw "$n not in tex_scan.tsv" }; $e = $rpf.GetEntry($r[4]); $src = $r[3] }
  $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e)
  $t = $y.TextureDict.Textures.data_items | ? { $_.Name -eq $n } | Select-Object -First 1
  if (-not $t) { throw "$n not in $src" }
  [IO.File]::WriteAllBytes((Join-Path $Out "$n.dds"), [CodeWalker.Utils.DDSIO]::GetDDSFile($t))
  "TEX_EXTRACT $n $($t.Width)x$($t.Height) $($t.Format) <- $src" }
