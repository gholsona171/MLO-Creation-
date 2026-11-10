# tex_verify.ps1 <orig file> <new file> : reloads both with CodeWalker and checks the new one keeps every texture (name, usage,
# usage data, extra flags), that unchanged textures are byte-identical, that changed ones are no bigger than before and that
# lossless DXT5 -> DXT1 ones decode to the same pixels (every level of 4x4 and up); prints one line per file (PASS / FAIL + reasons) and the RSC7 sizes.
param([string]$A, [string]$B)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function Load($p) { $b = [IO.File]::ReadAllBytes($p); $x = [IO.Path]::GetExtension($p).ToLower()
  switch ($x) { '.ytd' { $f = New-Object CodeWalker.GameFiles.YtdFile; $f.Load($b); $d = @($f.TextureDict) }
                '.ydr' { $f = New-Object CodeWalker.GameFiles.YdrFile; $f.Load($b); $d = @($f.Drawable.ShaderGroup.TextureDictionary) }
                '.ydd' { $f = New-Object CodeWalker.GameFiles.YddFile; $f.Load($b); $d = @($f.Drawables | % { $_.ShaderGroup.TextureDictionary }) } }
  $t = @(foreach ($q in $d) { if ($q) { @($q.Textures.data_items) | ? { $_ } } }); ,@($b, $t) }
$ra = Load $A; $rb = Load $B; $ta = $ra[1]; $tb = $rb[1]; $why = @()
if ($ta.Count -ne $tb.Count) { $why += "count $($ta.Count) -> $($tb.Count)" }
$same = 0; $chg = 0; $exact = 0
for ($i = 0; $i -lt [Math]::Min($ta.Count, $tb.Count); $i++) { $x = $ta[$i]; $y = $tb[$i]
  if ($x.Name -ne $y.Name -or $x.Usage -ne $y.Usage -or $x.UsageData -ne $y.UsageData -or $x.ExtraFlags -ne $y.ExtraFlags) { $why += "meta $($x.Name)"; continue }
  $dx = $x.Data.FullData; $dy = $y.Data.FullData
  if ($x.Width -eq $y.Width -and $x.Height -eq $y.Height -and $x.Format -eq $y.Format -and $x.Levels -eq $y.Levels) {
    if (-not [Linq.Enumerable]::SequenceEqual([byte[]]$dx, [byte[]]$dy)) { $why += "data changed at same size $($x.Name)" } else { $same++ }; continue }
  $chg++
  if ($dy.Length -gt $dx.Length) { $why += "grew $($x.Name)" }
  if ($x.Width -eq $y.Width -and $x.Height -eq $y.Height -and $x.Format -eq 'D3DFMT_DXT5' -and $y.Format -eq 'D3DFMT_DXT1') {
    $ok = $true; for ($l = 0; $l -lt $x.Levels -and ($x.Width -shr $l) -ge 4 -and ($x.Height -shr $l) -ge 4; $l++) { if (-not [Linq.Enumerable]::SequenceEqual([byte[]][CodeWalker.Utils.DDSIO]::GetPixels($x, $l), [byte[]][CodeWalker.Utils.DDSIO]::GetPixels($y, $l))) { $ok = $false; break } }
    if ($ok) { $exact++ } else { $why += "DXT1 pixels differ $($x.Name)" } } }
$res = if ($why.Count) { 'FAIL ' + ($why | Select -First 5) -join '; ' } else { 'PASS' }
"{0}`t{1}`ttextures {2}: {3} unchanged, {4} changed ({5} lossless DXT1, pixel-exact)" -f $res, (Split-Path $B -Leaf), $tb.Count, $same, $chg, $exact
