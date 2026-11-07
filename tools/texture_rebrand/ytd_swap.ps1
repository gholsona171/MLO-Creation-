# Replace named textures inside an existing ytd with new .dds files, keep every other texture byte-identical,
# keep each replaced texture's name, usage and usage flags; check size / format / mip count match the original.
#   ytd_swap.ps1 -In orig.ytd -Dds <folder of name.dds> -Out new.ytd
param([string]$In, [string]$Dds, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load([IO.File]::ReadAllBytes($In))
$list = New-Object 'System.Collections.Generic.List[CodeWalker.GameFiles.Texture]'
$done = @{}
foreach ($t in $y.TextureDict.Textures.data_items) {
  $f = Join-Path $Dds "$($t.Name).dds"
  if (Test-Path -LiteralPath $f) {
    $n = [CodeWalker.Utils.DDSIO]::GetTexture([IO.File]::ReadAllBytes($f))
    if ($n.Width -ne $t.Width -or $n.Height -ne $t.Height -or $n.Format -ne $t.Format -or $n.Levels -ne $t.Levels) {
      throw "$($t.Name): new $($n.Width)x$($n.Height) $($n.Format) L$($n.Levels) != orig $($t.Width)x$($t.Height) $($t.Format) L$($t.Levels)"
    }
    $n.Name = $t.Name; $n.NameHash = $t.NameHash; $n.Usage = $t.Usage; $n.UsageFlags = $t.UsageFlags
    $list.Add($n); $done[$t.Name] = 1; "replaced $($t.Name) $($n.Width)x$($n.Height) $($n.Format) L$($n.Levels)"
  } else { $list.Add($t) }
}
foreach ($f in Get-ChildItem -LiteralPath $Dds -Filter *.dds) { if (-not $done[$f.BaseName]) { throw "not in ytd: $($f.BaseName)" } }
$td = New-Object CodeWalker.GameFiles.TextureDictionary; $td.BuildFromTextureList($list)
$y2 = New-Object CodeWalker.GameFiles.YtdFile; $y2.TextureDict = $td
$bytes = $y2.Save(); [IO.File]::WriteAllBytes($Out, $bytes)
# reload check
$c = New-Object CodeWalker.GameFiles.YtdFile; $c.Load($bytes)
$o = @{}; foreach ($t in $y.TextureDict.Textures.data_items) { $o[$t.Name] = $t }
foreach ($t in $c.TextureDict.Textures.data_items) {
  $p = $o[$t.Name]
  if (-not $p -or $p.Width -ne $t.Width -or $p.Height -ne $t.Height -or $p.Format -ne $t.Format -or $p.Levels -ne $t.Levels -or "$($p.UsageFlags)" -ne "$($t.UsageFlags)") { throw "reload mismatch $($t.Name)" }
}
"$Out $($bytes.Length) bytes, $($c.TextureDict.Textures.data_items.Count) textures (orig $($y.TextureDict.Textures.data_items.Count)), reload OK"
