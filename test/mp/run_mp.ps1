# Local multiplayer test of The PeaceKeeper: starts DayZDiag as a dedicated server (mission
# AFPKMP.ChernarusPlus\init.c) and a DayZDiag client that connects to it. The client helper mod
# (testmod\AFPKMP, never shipped) raises the rifle and asks this script to hold the left mouse button
# in each fire mode ("[AFPKMP] HOLD <ms> <tag>" in the client log); it logs the rounds fired and the
# round counter. A picture of the client window is saved at each "[AFPKMP] SHOT <name>".
# The mouse is only pressed while the client window is in front, with the pointer at its centre.
# Needs Steam running and the mod built (build.bat). DayZ on this PC is shared: agree a turn first;
# this script refuses to start while any DayZ is running, and only stops the two games it started.
#   powershell -ExecutionPolicy Bypass -File test\mp\run_mp.ps1
param([string]$Rifle = 'AF_PeaceKeeper')     # a vanilla class (SCAR) runs the same steps as a control
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class AFMP {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, int dx, int dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    // Left button held for ms, only if the window h is in front. Returns false if it could not be fronted.
    public static bool Hold(IntPtr h, int ms) {
        if (GetForegroundWindow() != h) {
            keybd_event(0x12, 0, 0, UIntPtr.Zero); keybd_event(0x12, 0, 2, UIntPtr.Zero);   // Alt tap: lets us take the foreground
            SetForegroundWindow(h); System.Threading.Thread.Sleep(400);
        }
        if (GetForegroundWindow() != h) return false;
        RECT r; if (!GetClientRect(h, out r)) return false;
        POINT c = new POINT { X = r.R / 2, Y = r.B / 2 }; ClientToScreen(h, ref c); SetCursorPos(c.X, c.Y);
        System.Threading.Thread.Sleep(100);
        if (GetForegroundWindow() != h) return false;
        mouse_event(2, 0, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(ms);
        mouse_event(4, 0, 0, 0, UIntPtr.Zero);
        return true;
    }
}
'@
[AFMP]::SetProcessDPIAware() | Out-Null

$here    = $PSScriptRoot
$repo    = Split-Path (Split-Path $here -Parent) -Parent
$tools   = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools'
$dayz    = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ'
$exe     = Join-Path $dayz 'DayZDiag_x64.exe'
$srvProf = Join-Path $here 'profiles_server'
$cliProf = Join-Path $here 'profiles_client'
$out     = Join-Path $here 'captures'

$running = Get-Process DayZDiag_x64, DayZ_x64 -ErrorAction SilentlyContinue
if ($running) { throw "DayZ is already running ($($running.Name -join ', ')). Not starting the test." }

# The helper mod: scripts only, never signed, never shipped.
$helper = Join-Path $here '@AFPKMP\Addons'
$temp   = Join-Path $env:TEMP 'AFPKMP_build'
New-Item -ItemType Directory -Force $helper, $temp, $out, $srvProf, $cliProf | Out-Null
$p = Start-Process (Join-Path $tools 'Bin\AddonBuilder\AddonBuilder.exe') -ArgumentList @(
    "`"$(Join-Path $here 'testmod\AFPKMP')`"", "`"$helper`"", '-clear', '-packonly', '-prefix=AFPKMP',
    "-project=`"$(Join-Path $here 'testmod')`"", "-temp=`"$temp`"", "-toolsDirectory=`"$tools`""
) -RedirectStandardOutput (Join-Path $temp 'addonbuilder.log') -NoNewWindow -PassThru -Wait
if ($p.ExitCode -ne 0 -or -not (Test-Path (Join-Path $helper 'AFPKMP.pbo'))) { throw 'Could not build the helper mod.' }

$mods = @((Join-Path $repo '@AF_WeaponsPack'), (Join-Path $here '@AFPKMP'))
foreach ($m in $mods) { if (-not (Test-Path -LiteralPath $m)) { throw "Mod folder missing: $m" } }
$modArg = """-mod=$($mods -join ';')"""

# The mission: Bohemia's stock Chernarus files (their public repository, cloned to $stock) with this
# test's init.c, infected and animals off. Put together in run_mp (not in git).
$stock   = 'C:\DayZMods\_external\DayZ-Central-Economy\dayzOffline.chernarusplus'
$mission = Join-Path $here 'run_mp\AFPKMP.ChernarusPlus'
if (-not (Test-Path $stock)) { throw "Stock mission files missing: $stock" }
if (-not (Test-Path (Join-Path $mission 'db\globals.xml'))) {
    New-Item -ItemType Directory -Force $mission | Out-Null
    Copy-Item (Join-Path $stock '*') $mission -Recurse -Force
    $globals = Join-Path $mission 'db\globals.xml'
    $g = [IO.File]::ReadAllText($globals) -replace '(name="(Zombie|Animal)MaxCount" type="0" value=")\d+', '${1}0'
    [IO.File]::WriteAllText($globals, $g, (New-Object Text.UTF8Encoding $false))
}
Copy-Item (Join-Path $here 'AFPKMP.ChernarusPlus\init.c') (Join-Path $mission 'init.c') -Force
Get-ChildItem $mission -Directory -Filter 'storage_*' | Remove-Item -Recurse -Force -Confirm:$false
Remove-Item (Join-Path $out 'afpk_*.png') -ErrorAction SilentlyContinue

$start = Get-Date
$server = Start-Process $exe -WorkingDirectory $dayz -PassThru -ArgumentList @(
    '-server', """-config=$here\serverDZ.cfg""", '-port=2302', """-mission=$mission""",
    $modArg, """-profiles=$srvProf""", "-afrifle=$Rifle", '-doLogs', '-scriptDebug=true')
"server started, pid $($server.Id)"

function Read-Log($dir) {
    $log = Get-ChildItem $dir -Filter 'script_*.log' -ErrorAction SilentlyContinue |
        Where-Object LastWriteTime -gt $start | Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $log) { return '' }
    $fs = [IO.File]::Open($log.FullName, 'Open', 'Read', 'ReadWrite'); $sr = New-Object IO.StreamReader $fs
    $text = $sr.ReadToEnd(); $sr.Close(); $fs.Close()
    return $text
}

function Save-Window($proc, $name) {
    $proc.Refresh()
    $h = $proc.MainWindowHandle
    if ($h -eq 0) { return $false }
    $r = New-Object AFMP+RECT; [AFMP]::GetClientRect($h, [ref]$r) | Out-Null
    if ($r.R -lt 100 -or $r.B -lt 100) { return $false }
    $bmp = New-Object System.Drawing.Bitmap $r.R, $r.B
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc(); [AFMP]::PrintWindow($h, $hdc, 3) | Out-Null; $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save((Join-Path $out "afpk_$name.png"), [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
    return $true
}

$client = $null; $seen = @{}; $done = $false; $text = ''; $why = 'timed out'
$deadline = (Get-Date).AddSeconds(420)
try {
    while ((Get-Date) -lt $deadline -and -not $done) {
        $text = Read-Log $srvProf
        if (-not $text -and ((Get-Date) - $start).TotalSeconds -gt 90) { $why = 'server stuck before its scripts started'; Save-Window $server 'server_stuck' | Out-Null; break }
        if (-not $client -and $text -match '\[AFPKMP\] server ready') {
            Start-Sleep -Seconds 5
            $client = Start-Process $exe -WorkingDirectory $dayz -PassThru -ArgumentList @(
                '-connect=127.0.0.1', '-port=2302', $modArg, """-profiles=$cliProf""",
                '-window', '-nosplash', '-noPause', '-scriptDebug=true')
            "client started, pid $($client.Id)"
        }
        if ($client) {
            $cli = Read-Log $cliProf
            foreach ($m in [regex]::Matches($cli, '\[AFPKMP\] HOLD (\d+) (\S+)')) {
                $tag = 'hold_' + $m.Groups[2].Value
                if (-not $seen.ContainsKey($tag)) {
                    $seen[$tag] = $true
                    $client.Refresh()
                    $ok = [AFMP]::Hold($client.MainWindowHandle, [int]$m.Groups[1].Value)
                    "held the trigger for $($m.Groups[2].Value): $ok"
                }
            }
            foreach ($m in [regex]::Matches($cli, '\[AFPKMP\] SHOT (\S+)')) {
                $name = $m.Groups[1].Value
                if (-not $seen.ContainsKey($name)) {
                    $seen[$name] = $true
                    Start-Sleep -Milliseconds 600
                    if (Save-Window $client $name) { "captured $name" } else { "could not capture $name" }
                }
            }
            if ($cli -match 'CLIENT DONE') { $done = $true; $why = 'done' }
            if ($cli -match 'ompile error|Can.t compile') { $why = 'client script compile error'; break }
            if ($client.HasExited) { $why = 'client exited'; break }
        }
        if ($text -match 'ompile error|Can.t compile') { $why = 'server script compile error'; break }
        if ($server.HasExited) { $why = 'server exited'; break }
        Start-Sleep -Milliseconds 150
    }
    if ($client -and -not $client.HasExited) { Save-Window $client 'end' | Out-Null }
    Start-Sleep -Seconds 2
    '--- server'
    $srv = ((Read-Log $srvProf) -split "`r?`n" | Select-String '\[AFPKMP\]|\[AF_Weapons\]|ompile|SCRIPT\s+\(E\)|NULL pointer').Line
    # The once-a-second server line: only where it changes.
    $last = ''; foreach ($l in $srv) { $k = $l -replace '^\S+\s+SCRIPT\s+:\s+', ''; if ($k -ne $last) { $l }; $last = $k }
    '--- client'
    ((Read-Log $cliProf) -split "`r?`n" | Select-String '\[AFPKMP\]|\[AF_Weapons\]|ompile|SCRIPT\s+\(E\)|NULL pointer').Line
    "finished: $why"
}
finally {
    foreach ($own in @($client, $server)) { if ($own -and -not $own.HasExited) { Stop-Process -Id $own.Id -Force -Confirm:$false } }
}
