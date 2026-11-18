@echo off
REM Builds and signs AF_Flags.pbo (the separate flag mod) with DayZ Tools.
setlocal
set "TOOLS=C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools"
set "ROOT=%~dp0"
set "KEYNAME=AlliedForces"
copy /Y "%ROOT%keys\%KEYNAME%.bikey" "%ROOT%@AF_Flags\Keys\" >nul
"%TOOLS%\Bin\AddonBuilder\AddonBuilder.exe" "%ROOT%source_flags\AF_Flags" "%ROOT%@AF_Flags\Addons" -clear -prefix=AF_Flags -project="%ROOT%source_flags" -include="%ROOT%build_include.txt" -sign="%ROOT%keys\%KEYNAME%.biprivatekey"
echo.
echo Done. Output: %ROOT%@AF_Flags
pause
