@echo off
setlocal enabledelayedexpansion

REM --- Configuration ---
REM Path to the Python conversion script (relative to this batch file)
set "PYTHON_SCRIPT=.\tgf_to_iccma23.py"
REM Python interpreter command (change to python3 if needed, or provide full path)
set "PYTHON_CMD=python"
REM --- End Configuration ---

REM Check if a directory argument was provided
if "%~1"=="" (
    echo Usage: %~nx0 ^<directory_containing_tgf_files^>
    echo Example: %~nx0 "C:\My Data\TGFs"
    exit /b 1
)

set "TARGET_DIR=%~1"

REM Check if the target directory exists
if not exist "%TARGET_DIR%\" (
    echo Error: Directory not found: "%TARGET_DIR%"
    exit /b 1
)

REM Check if the Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo Error: Python script not found: "%PYTHON_SCRIPT%"
    echo Please ensure it exists in the same directory as this batch file, or update the PYTHON_SCRIPT variable.
    exit /b 1
)

echo Starting conversion in directory: "%TARGET_DIR%"
echo Using Python script: "%PYTHON_SCRIPT%"
echo ------------------------------------------

set /a fileCount=0
set /a successCount=0
set /a errorCount=0

REM Recursively find all .tgf files in the target directory and its subfolders
REM Use 'dir /b "%TARGET_DIR%\*.tgf"' instead of 'for /R' if you ONLY want files directly in TARGET_DIR
for /R "%TARGET_DIR%" %%F in (*.tgf) do (
    set /a fileCount+=1
    echo Processing [!fileCount!]: "%%F"

    REM Execute the Python script
    "%PYTHON_CMD%" "%PYTHON_SCRIPT%" "%%F"

    REM Check the exit code (ERRORLEVEL)
    if !ERRORLEVEL! equ 0 (
        echo  -> Success
        set /a successCount+=1
    ) else (
        echo  -> Failed (Python script exited with code !ERRORLEVEL!)
        set /a errorCount+=1
    )
)

echo ------------------------------------------
echo Batch conversion finished.
echo Total .tgf files found: !fileCount!
echo Successfully converted: !successCount!
echo Failed conversions: !errorCount!

endlocal
exit /b 0