# lists every texture in a .ytd or embedded in a .ydr / .ydd: file, texture, WxH, format, mips, data KiB
#   tex_list.ps1 <file> [<file> ...]   (TSV out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function Dicts($path) {
  $b = [IO.File]::ReadAllBytes($path)
  if ([Text.Encoding]::ASCII.GetString($b, 0, 4) -ne 'RSC7') { return }
  switch ([IO.Path]::GetExtension($path).ToLower()) {
    '.ytd' { $f = New-Object CodeWalker.GameFiles.YtdFile; $f.Load($b); ,@($f.TextureDict) }
    '.ydr' { $f = New-Object CodeWalker.GameFiles.YdrFile; $f.Load($b); ,@($f.Drawable.ShaderGroup.TextureDictionary) }
    '.ydd' { $f = New-Object CodeWalker.GameFiles.YddFile; $f.Load($b); ,@($f.Drawables | % { $_.ShaderGroup.TextureDictionary }) }
  }
}
foreach ($p in $args) {
  foreach ($td in (Dicts $p)) { if (-not $td) { continue }
    foreach ($t in @($td.Textures.data_items)) { if (-not $t) { continue }
      $kb = 0; if ($t.Data -and $t.Data.FullData) { $kb = $t.Data.FullData.Length / 1KB }
      "{0}`t{1}`t{2}x{3}`t{4}`t{5}`t{6:N0}" -f (Split-Path $p -Leaf), $t.Name, $t.Width, $t.Height, $t.Format, $t.Levels, $kb } } }
