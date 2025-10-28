@echo off
setlocal

if "%~1"=="" (
    echo usage: %0 image_name [style]
    echo styles: center stretch fit fill tile
    echo example: %0 "wallpaper.jpg" fill
    exit /b 1
)

set "image_name=%~1"
set "style=%~2"

if "%style%"=="" set "style=fill"

rem map textual styles to registry values
if /I "%style%"=="center"  ( set "ws=0"  & set "tile=0" )
if /I "%style%"=="stretch" ( set "ws=2"  & set "tile=0" )
if /I "%style%"=="fit"     ( set "ws=6"  & set "tile=0" )
if /I "%style%"=="fill"    ( set "ws=10" & set "tile=0" )
if /I "%style%"=="tile"    ( set "ws=0"  & set "tile=1" )

rem fallback if numeric style provided
for /f "delims=" %%A in ("%style%") do set "sval=%%~A"
if defined sval (
    set "ws=%sval%"
    if "%sval%"=="22" ( set "tile=1" ) else if not defined tile set "tile=0"
)

rem full path to image
set "wallpaper_path=%~dp0%image_name%"
for %%I in ("%wallpaper_path%") do set "wallpaper_path=%%~fI"

rem Build PowerShell command as a single quoted string argument
set "pscmd=if (-not (Test-Path '%wallpaper_path%')) { Write-Error 'File not found: %wallpaper_path%'; exit 1 };"
set "pscmd=%pscmd% $p = '%wallpaper_path%'; $ws = '%ws%'; $tile = '%tile%';"
set "pscmd=%pscmd% Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name Wallpaper -Value $p;"
set "pscmd=%pscmd% Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name WallpaperStyle -Value $ws;"
set "pscmd=%pscmd% Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name TileWallpaper -Value $tile;"
set "pscmd=%pscmd% Add-Type -MemberDefinition '[DllImport(\"user32.dll\",SetLastError=true)]public static extern bool SystemParametersInfo(int uAction,int uParam,string lpvParam,int fuWinIni);' -Name Win -Namespace Native;"
set "pscmd=%pscmd% [Native.Win]::SystemParametersInfo(20,0,$p,3) > $null;"

powershell -NoProfile -ExecutionPolicy Bypass -Command "%pscmd%"

endlocal
