@echo off

setlocal

set "filename=%~1"
set "depth=%~2"

if "%depth%"=="" (
    set "depth=2"
)

set "src_dir=src"

for /r "%src_dir%" %%G in (*.py) do (
    set "file=%%~nxG"
    setlocal enabledelayedexpansion
    set "dir=%%~dpG"
    set "dir=!dir:%src_dir%\=!"
    set "dir=!dir:~0,-1!"
    setlocal enabledelayedexpansion
    set "dir=!dir:\=/!"
    for /l %%i in (1,1,%depth%) do (
        set "dir=!dir:*\=!"
    )
    endlocal
    if "!file!"=="%filename%" (
        echo Running: "%%G"
        python "%%G"
        exit /b
    )
)
endlocal

echo File not found.
exit /b