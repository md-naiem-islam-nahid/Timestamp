@echo off
setlocal enabledelayedexpansion

:: Initialize Git repository
git init

:: Create and commit 100 files
for /l %%i in (1,1,100) do (
    :: Get current timestamp
    for /f "tokens=1,2 delims=." %%a in ('wmic os get localdatetime ^| find "."') do set datetime=%%a
    
    :: Format timestamp
    set year=!datetime:~0,4!
    set month=!datetime:~4,2!
    set day=!datetime:~6,2!
    set hour=!datetime:~8,2!
    set minute=!datetime:~10,2!
    set second=!datetime:~12,2!
    set timestamp=!year!-!month!-!day!_!hour!-!minute!-!second!
    
    :: Create file
    echo !timestamp! > file_%%i_!timestamp!.txt

    :: Git commit
    git add file_%%i_!timestamp!.txt
    git commit -m "Commit %%i: file_%%i_!timestamp!.txt"
)

endlocal
@echo on
