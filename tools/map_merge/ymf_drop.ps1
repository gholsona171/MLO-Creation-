# ymf_drop.ps1 <in _manifest.ymf> <out _manifest.ymf> <imap name> [<imap name> ...]
# Rebuilds a PSO _manifest.ymf without the imapDependencies_2 entries of the named ymaps (the ymaps the build leaves out).
# Gate 1: the UNEDITED file must round-trip (PSO -> XML -> PSO -> XML gives the same XML), or nothing is written.
# Gate 2: the written file is reloaded; its XML must equal the edited XML, and the dropped names must be gone.
param([Parameter(Mandatory)][string]$In, [Parameter(Mandatory)][string]$Out, [Parameter(Mandatory, ValueFromRemainingArguments)][string[]]$Drop)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function ToXml([byte[]]$b) {
  $y = New-Object CodeWalker.GameFiles.YmfFile; $e = New-Object CodeWalker.GameFiles.RpfBinaryFileEntry; $e.Name = '_manifest.ymf'
  $y.Load($b, $e); if (-not $y.Pso) { throw 'not a PSO ymf' }; [CodeWalker.GameFiles.PsoXml]::GetXml($y.Pso)
}
function ToPso([string]$x) { $d = New-Object Xml.XmlDocument; $d.LoadXml($x); [CodeWalker.GameFiles.XmlPso]::GetPso($d).Save() }
$orig = ToXml ([IO.File]::ReadAllBytes($In))
if ((ToXml (ToPso $orig)) -ne $orig) { throw 'GATE 1 FAIL: the unedited manifest does not round-trip; not writing' }
$doc = New-Object Xml.XmlDocument; $doc.LoadXml($orig)
foreach ($n in $Drop) {
  $h = 'hash_{0:X8}' -f [CodeWalker.GameFiles.JenkHash]::GenHash($n.ToLower())
  $hit = @($doc.SelectNodes("/CPackFileMetaData/imapDependencies_2/Item[imapName='$h' or imapName='$n']"))
  if ($hit.Count -ne 1) { throw "expected one imapDependencies_2 entry for $n ($h), found $($hit.Count)" }
  [void]$hit[0].ParentNode.RemoveChild($hit[0]); "dropped $n ($h)"
}
$sw = New-Object IO.StringWriter; $doc.Save($sw); $edited = ToXml (ToPso $sw.ToString())
$bytes = ToPso $edited
[IO.File]::WriteAllBytes($Out, $bytes)
$back = ToXml ([IO.File]::ReadAllBytes($Out))
if ($back -ne $edited) { throw 'GATE 2 FAIL: written manifest does not reload to the edited XML' }
foreach ($n in $Drop) { $h = 'hash_{0:X8}' -f [CodeWalker.GameFiles.JenkHash]::GenHash($n.ToLower()); if ($back.Contains($h)) { throw "GATE 2 FAIL: $n still present" } }
"YMF_OK $Out $($bytes.Length) bytes"
