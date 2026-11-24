# Starts DayZDiag offline with the locally built mod and the AFM107Play mission, for trying the
# M107A1 by hand. Nothing is scripted and the game is not stopped: close it yourself. Steam must be running.
$root = Split-Path -Parent $PSScriptRoot
$game = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ'
$prof = Join-Path $PSScriptRoot 'profiles'
New-Item -ItemType Directory -Force $prof | Out-Null
$p = Start-Process -FilePath "$game\DayZDiag_x64.exe" -WorkingDirectory $game -PassThru -ArgumentList @(
    "`"-mission=$PSScriptRoot\AFM107Play.ChernarusPlus`"", "`"-mod=$root\@AF_WeaponsPack`"", "`"-profiles=$prof`"",
    '-window', '-nosplash', '-noPause', '-scriptDebug=true')
"started DayZDiag pid $($p.Id)"
