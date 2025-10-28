@echo off
setlocal

if "%~3"=="" (
    echo usage: %0 shortcut_name icon_name target_link
    echo example: %0 myshortcut icon.ico https://google.com
    exit /b
)

set "shortcut_name=%~1"
set "icon_name=%~2"
set "target_link=%~3"

set "shortcut=%USERPROFILE%\Desktop\%shortcut_name%.lnk"
set "target=explorer.exe"
set "args=%target_link%"
set "icon=%~dp0%icon_name%"

powershell -NoProfile -Command ^
 $s=(New-Object -ComObject WScript.Shell).CreateShortcut('%shortcut%'); ^
 $s.TargetPath='%target%'; ^
 $s.Arguments='%args%'; ^
 $s.IconLocation='%icon%'; ^
 $s.Save()

endlocal
