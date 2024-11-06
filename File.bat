@echo off
setlocal enabledelayedexpansion

:: Function to generate random string
:generateRandomString
setlocal enabledelayedexpansion
set "charset=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
set "length=10"
set "randStr="
for /L %%n in (1,1,!length!) do (
    set /a "index=!random! %% 62"
    for %%a in (!index!) do set "randStr=!randStr!!charset:~%%a,1!"
)
endlocal & set "%~1=%randStr%"
goto :eof

:: Create 1,000 folders with random names
for /l %%j in (1,1,1000) do (
    call :generateRandomString folderName
    set folderName=%%j_!folderName!
    md !folderName!
    
    if errorlevel 1 (
        echo Failed to create folder !folderName!
        exit /b 1
    )
    
    :: Git commit folder creation
    git add !folderName!
    git commit -m "Folder created: !folderName!"
    
    if errorlevel 1 (
        echo Failed to commit folder !folderName!
        exit /b 1
    )

    :: Change directory to the new folder
    cd !folderName!

    :: Create 100 files in each folder
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
        set millisecond=!datetime:~15,6!
        set timestamp=!year!-!month!-!day!_!hour!-!minute!-!second!-!millisecond!
        
        :: Create file with timestamp and name
        echo !timestamp! - !year!-!month!-!day! - MD. Naiem Islam Nahid > !folderName!_file_%%i_!timestamp!.txt

        if errorlevel 1 (
            echo Failed to create file !folderName!_file_%%i_!timestamp!.txt
            exit /b 1
        )

        :: Git add and commit
        git add !folderName!_file_%%i_!timestamp!.txt
        git commit -m "Commit %%j-%%i: !folderName!_file_%%i_!timestamp!.txt"

        if errorlevel 1 (
            echo Failed to commit file !folderName!_file_%%i_!timestamp!.txt
            exit /b 1
        )
    )

    :: Move back to the root directory
    cd ..
)

endlocal
@echo on
