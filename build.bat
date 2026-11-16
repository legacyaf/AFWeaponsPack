@echo off
REM Builds and signs AF_Weapons.pbo with DayZ Tools (install DayZ Tools from Steam).
setlocal
set "TOOLS=C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools"
set "ROOT=%~dp0"
set "KEYNAME=AlliedForces"

REM 1) Create a signing key the first time (keep the .biprivatekey PRIVATE)
if not exist "%ROOT%keys\%KEYNAME%.biprivatekey" (
  pushd "%ROOT%keys"
  "%TOOLS%\Bin\DsUtils\DSCreateKey.exe" %KEYNAME%
  popd
)
copy /Y "%ROOT%keys\%KEYNAME%.bikey" "%ROOT%@AF_WeaponsPack\Keys\" >nul

REM 2) Pack + sign the PBO
REM    -project lets Binarize find AF_Weapons\... textures without the P: drive.
REM    -include packs files the model doesn't reference directly (the damage .rvmat files).
"%TOOLS%\Bin\AddonBuilder\AddonBuilder.exe" "%ROOT%source\AF_Weapons" "%ROOT%@AF_WeaponsPack\Addons" -clear -prefix=AF_Weapons -project="%ROOT%source" -include="%ROOT%build_include.txt" -sign="%ROOT%keys\%KEYNAME%.biprivatekey"

REM 3) Ship the loot files (types.xml etc.) with the mod, for licensed server owners
if not exist "%ROOT%@AF_WeaponsPack\ServerFiles" mkdir "%ROOT%@AF_WeaponsPack\ServerFiles"
copy /Y "%ROOT%server\af_ce\*.*" "%ROOT%@AF_WeaponsPack\ServerFiles\" >nul

echo.
echo Done. Output: %ROOT%@AF_WeaponsPack
pause
