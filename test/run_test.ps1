# Runs the offline test mission in DayZDiag with the locally built mod and saves a picture of the
# game window for every shot the mission announces in its script log. Steam must be running.
# Only the game process this script starts is ever stopped.
param([int]$TimeoutSeconds = 300)
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class AFCapture {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    public static bool Save(IntPtr h, string path) {
        RECT r; if (!GetClientRect(h, out r) || r.R <= 0 || r.B <= 0) return false;
        using (Bitmap bmp = new Bitmap(r.R, r.B, PixelFormat.Format32bppArgb)) {
            using (Graphics g = Graphics.FromImage(bmp)) { IntPtr dc = g.GetHdc(); bool ok = PrintWindow(h, dc, 3); g.ReleaseHdc(dc); if (!ok) return false; }
            bmp.Save(path, ImageFormat.Png); return true; } }
}
"@
$root = Split-Path -Parent $PSScriptRoot
$game = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ'
$prof = Join-Path $PSScriptRoot 'profiles'
New-Item -ItemType Directory -Force $prof | Out-Null
Get-ChildItem $prof -Filter 'af_*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
$start = Get-Date
$p = Start-Process -FilePath "$game\DayZDiag_x64.exe" -WorkingDirectory $game -PassThru -ArgumentList @(
    "`"-mission=$PSScriptRoot\AFWeaponsTest.ChernarusPlus`"", "`"-mod=$root\@AF_WeaponsPack`"", "`"-profiles=$prof`"",
    '-window', '-nosplash', '-noPause', '-scriptDebug=true')
"started DayZDiag pid $($p.Id)"
$log = $null; $offset = 0; $shots = 0
while (-not $p.HasExited) {
    if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSeconds) { "TIMEOUT after $TimeoutSeconds s - stopping pid $($p.Id)"; Stop-Process -Id $p.Id -Force; break }
    if (-not $log) { $log = Get-ChildItem $prof -Filter 'script_*.log' | Where-Object { $_.LastWriteTime -ge $start } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
    if ($log) {
        $fs = [IO.File]::Open($log.FullName, 'Open', 'Read', 'ReadWrite'); $fs.Position = $offset
        $sr = New-Object IO.StreamReader($fs); $text = $sr.ReadToEnd(); $offset = $fs.Position; $sr.Close()
        foreach ($m in [regex]::Matches($text, '\[AFTest\] screenshot (\S+)')) {
            $p.Refresh()
            if ([AFCapture]::Save($p.MainWindowHandle, (Join-Path $prof "af_$($m.Groups[1].Value).png"))) { $shots++ }
        }
    }
    Start-Sleep -Milliseconds 120
}
"exit code $($p.ExitCode) after $([int]((Get-Date) - $start).TotalSeconds) s, $shots pictures saved in $prof"
if ($log) { Select-String -Path $log.FullName -Pattern 'AFTest\] (FAILED|spawned|attached|AFM41|all)|AF_Weapons|Can.t compile' | ForEach-Object { $_.Line } }
