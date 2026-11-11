# Counts thin moving streak pixels (rain) between consecutive captures of the game window. Usage: rainmeter.ps1 [-Pairs 4]
param([int]$Pairs = 4)
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public class RM {
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
 public static byte[] Grab(IntPtr h, out int w, out int hh) {
  RECT r; GetWindowRect(h, out r); w = r.R - r.L; hh = r.B - r.T;
  var bmp = new Bitmap(w, hh, PixelFormat.Format24bppRgb); using (var g = Graphics.FromImage(bmp)) g.CopyFromScreen(r.L, r.T, 0, 0, bmp.Size);
  var d = bmp.LockBits(new Rectangle(0, 0, w, hh), ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
  var raw = new byte[d.Stride * hh]; Marshal.Copy(d.Scan0, raw, 0, raw.Length); int st = d.Stride; bmp.UnlockBits(d); bmp.Dispose();
  var gr = new byte[w * hh]; for (int y = 0; y < hh; y++) for (int x = 0; x < w; x++) { int i = y * st + x * 3; gr[y * w + x] = (byte)((raw[i] + raw[i + 1] * 2 + raw[i + 2]) / 4); } return gr; }
 public static int Streaks(byte[] a, byte[] b, int w, int h) {
  int n = 0;
  for (int y = 120; y < h - 140; y++) for (int x = 300; x < w - 300; x++) {
   if (x > w * 0.28 && x < w * 0.52 && y > h * 0.25) continue;   // the player ped
   int i = y * w + x; int d = Math.Abs(a[i] - b[i]); if (d < 10) continue;
   int dl = Math.Abs(a[i - 5] - b[i - 5]), dr = Math.Abs(a[i + 5] - b[i + 5]); if (dl > 4 || dr > 4) continue;   // thin only
   int du = Math.Abs(a[i - w * 2] - b[i - w * 2]), dd = Math.Abs(a[i + w * 2] - b[i + w * 2]); if (du < 6 && dd < 6) continue;   // vertical extent
   n++; }
  return n; } }
"@
$p = Get-Process -Name FiveM_b3258_GTAProcess | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
[void][RM]::SetForegroundWindow($p.MainWindowHandle); Start-Sleep -Milliseconds 800
$tot = 0; $vals = @()
for ($k = 0; $k -lt $Pairs; $k++) { $w = 0; $h = 0; $a = [RM]::Grab($p.MainWindowHandle, [ref]$w, [ref]$h); Start-Sleep -Milliseconds 60; $b = [RM]::Grab($p.MainWindowHandle, [ref]$w, [ref]$h); $s = [RM]::Streaks($a, $b, $w, $h); $vals += $s; $tot += $s }
"STREAKS median=$((($vals | Sort-Object)[[int]($vals.Count/2)])) all=$($vals -join ',')"
