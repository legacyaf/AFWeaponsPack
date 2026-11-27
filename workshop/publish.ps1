# Uploads the built mod to its Steam Workshop item through the running Steam client (the same Steamworks
# calls the DayZ Tools Publisher makes). Only the files and the change note are sent: the title, description,
# pictures and visibility of the Workshop page are left as they are.
#   powershell -ExecutionPolicy Bypass -File workshop\publish.ps1 -ChangeNote workshop\changenotes_<version>_steam.txt
# Steam must be running and signed in to the account that owns the item. Run build.bat first.
param(
    [Parameter(Mandatory = $true)][string]$ChangeNote,
    [UInt64]$ItemId = 3840622061,
    [string]$ItemName = 'AFWeaponPack',
    [string]$Stage = (Join-Path $env:TEMP 'af_weaponspack_upload')
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$mod = Join-Path $root '@AF_WeaponsPack'
$dll = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ\steam_api64.dll'
$note = Get-Content $ChangeNote -Raw -Encoding UTF8

# 1) Stage a copy with meta.cpp (the Publisher adds it; servers and the launcher read the item id from it).
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Force $Stage | Out-Null
Copy-Item (Join-Path $mod '*') $Stage -Recurse
$meta = "protocol = 1;`r`npublishedid = $ItemId;`r`nname = `"$ItemName`";`r`ntimestamp = $([DateTime]::UtcNow.ToBinary());`r`n"
[IO.File]::WriteAllText((Join-Path $Stage 'meta.cpp'), $meta, (New-Object Text.ASCIIEncoding))
$a = (Get-FileHash (Join-Path $mod 'Addons\AF_Weapons.pbo')).Hash
$b = (Get-FileHash (Join-Path $Stage 'Addons\AF_Weapons.pbo')).Hash
if ($a -ne $b) { throw 'staged PBO differs from the built one' }
"staged: $Stage"
Get-ChildItem $Stage -Recurse -File | ForEach-Object { '  {0,12:N0}  {1}' -f $_.Length, $_.FullName.Substring($Stage.Length + 1) }

# 2) Steamworks, through the game's own steam_api64.dll (app 221100).
$work = Join-Path $env:TEMP 'af_weaponspack_steam'
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item $dll $work -Force
Set-Content (Join-Path $work 'steam_appid.txt') '221100' -Encoding ASCII
$api = (Join-Path $work 'steam_api64.dll').Replace('\', '\\')
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class AFSteam {
    const string D = "$api";
    [DllImport(D)] [return: MarshalAs(UnmanagedType.I1)] public static extern bool SteamAPI_Init();
    [DllImport(D)] public static extern void SteamAPI_Shutdown();
    [DllImport(D)] public static extern void SteamAPI_RunCallbacks();
    [DllImport(D)] public static extern IntPtr SteamAPI_SteamUGC_v017();
    [DllImport(D)] public static extern IntPtr SteamAPI_SteamUtils_v010();
    [DllImport(D)] public static extern ulong SteamAPI_ISteamUGC_StartItemUpdate(IntPtr self, uint app, ulong item);
    [DllImport(D)] [return: MarshalAs(UnmanagedType.I1)] public static extern bool SteamAPI_ISteamUGC_SetItemContent(IntPtr self, ulong handle, [MarshalAs(UnmanagedType.LPUTF8Str)] string folder);
    [DllImport(D)] public static extern ulong SteamAPI_ISteamUGC_SubmitItemUpdate(IntPtr self, ulong handle, [MarshalAs(UnmanagedType.LPUTF8Str)] string note);
    [DllImport(D)] public static extern int SteamAPI_ISteamUGC_GetItemUpdateProgress(IntPtr self, ulong handle, out ulong done, out ulong total);
    [DllImport(D)] [return: MarshalAs(UnmanagedType.I1)] public static extern bool SteamAPI_ISteamUtils_IsAPICallCompleted(IntPtr self, ulong call, [MarshalAs(UnmanagedType.I1)] out bool failed);
    [DllImport(D)] public static extern int SteamAPI_ISteamUtils_GetAPICallFailureReason(IntPtr self, ulong call);
    [DllImport(D)] [return: MarshalAs(UnmanagedType.I1)] public static extern bool SteamAPI_ISteamUtils_GetAPICallResult(IntPtr self, ulong call, out SubmitResult result, int size, int expected, [MarshalAs(UnmanagedType.I1)] out bool failed);
    [StructLayout(LayoutKind.Sequential, Pack = 8)]
    public struct SubmitResult { public int Result; [MarshalAs(UnmanagedType.I1)] public bool NeedsLegalAgreement; public ulong Item; }
}
"@
# The Steam library finds the app id through the process's own folder or these variables, and the client
# through the registry: a stale client pid there makes SteamAPI_Init fail.
$env:SteamAppId = '221100'; $env:SteamGameId = '221100'
$steam = Get-Process steam -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $steam) { throw 'Steam is not running' }
Set-ItemProperty 'HKCU:\Software\Valve\Steam\ActiveProcess' -Name pid -Value $steam.Id
Push-Location $work
[Environment]::CurrentDirectory = $work
try {
    if (-not [AFSteam]::SteamAPI_Init()) { throw 'SteamAPI_Init failed: is Steam running and signed in?' }
    $ugc = [AFSteam]::SteamAPI_SteamUGC_v017(); $utils = [AFSteam]::SteamAPI_SteamUtils_v010()
    if ($ugc -eq [IntPtr]::Zero -or $utils -eq [IntPtr]::Zero) { throw 'no Steam UGC interface' }
    $h = [AFSteam]::SteamAPI_ISteamUGC_StartItemUpdate($ugc, 221100, $ItemId)
    if (-not [AFSteam]::SteamAPI_ISteamUGC_SetItemContent($ugc, $h, $Stage)) { throw 'SetItemContent refused the folder' }
    $call = [AFSteam]::SteamAPI_ISteamUGC_SubmitItemUpdate($ugc, $h, $note)
    $names = 'invalid', 'preparing config', 'preparing content', 'uploading content', 'uploading preview', 'committing changes'
    $failed = $false; $last = ''; $start = Get-Date
    while (-not [AFSteam]::SteamAPI_ISteamUtils_IsAPICallCompleted($utils, $call, [ref]$failed)) {
        [AFSteam]::SteamAPI_RunCallbacks()
        $done = [UInt64]0; $total = [UInt64]0
        $s = [AFSteam]::SteamAPI_ISteamUGC_GetItemUpdateProgress($ugc, $h, [ref]$done, [ref]$total)
        $line = '{0}: {1:N0} / {2:N0} MB' -f $names[$s], ($done / 1MB), ($total / 1MB)
        if ($line -ne $last) { $line; $last = $line }
        if (((Get-Date) - $start).TotalMinutes -gt 50) { throw 'gave up after 50 minutes' }
        Start-Sleep -Milliseconds 500
    }
    $r = New-Object AFSteam+SubmitResult
    $ok = [AFSteam]::SteamAPI_ISteamUtils_GetAPICallResult($utils, $call, [ref]$r, 16, 3404, [ref]$failed)
    if (-not $ok -or $failed) { throw "the Steam call failed (reason $([AFSteam]::SteamAPI_ISteamUtils_GetAPICallFailureReason($utils, $call)))" }
    "RESULT eresult=$($r.Result) item=$($r.Item) needsLegalAgreement=$($r.NeedsLegalAgreement)"
    if ($r.Result -ne 1) { throw "Steam refused the update: EResult $($r.Result)" }
    'PUBLISHED'
}
finally {
    [AFSteam]::SteamAPI_Shutdown()
    Pop-Location
}
