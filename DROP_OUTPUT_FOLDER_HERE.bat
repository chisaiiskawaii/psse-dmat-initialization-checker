@echo off
setlocal
title PSS/E 34.5 DMAT Initialization Checker

set "PYTHON_EXE=C:\Python27\python.exe"
set "PSSE_ROOT=C:\Program Files (x86)\PTI\PSSE34"
set "PSSBIN=%PSSE_ROOT%\PSSBIN"
set "PSSPYTHON_PATH=%PSSE_ROOT%\PSSPY27"
set "DYNTOOLS_PATH=%USERPROFILE%\Downloads\Temporary\_Script\_Spotswood\Temporary\_Script\_Spotswood"

if "%~1"=="" (
    echo.
    echo Drag the complete Output folder onto this BAT file.
    echo.
    echo Expected structure:
    echo   Output\Any_DMAT_Name\Any_Test_Name\PSSE\results.outx
    echo.
    pause
    exit /b 1
)

if not exist "%~1\" (
    echo ERROR: The dropped item is not a folder:
    echo   %~1
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 2.7 was not found at %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%PSSPYTHON_PATH%\psse34.py" (
    echo ERROR: PSS/E 34.5 Python files were not found at %PSSPYTHON_PATH%
    pause
    exit /b 1
)

if not exist "%DYNTOOLS_PATH%\dyntools.py" (
    echo ERROR: dyntools.py was not found at %DYNTOOLS_PATH%
    pause
    exit /b 1
)

set "PATH=%PSSBIN%;%PSSPYTHON_PATH%;%DYNTOOLS_PATH%;%PATH%"
set "PYTHONPATH=%PSSPYTHON_PATH%;%DYNTOOLS_PATH%;%PYTHONPATH%"

echo.
echo Output folder: %~1
echo Loading PSS/E 34.5 and scanning OUTX files...
echo.

"%PYTHON_EXE%" "%~dp0dmat_initialization_checker.py" "%~1"
set "CHECKER_RESULT=%ERRORLEVEL%"

echo.
if "%CHECKER_RESULT%"=="0" (
    echo Finished successfully.
) else (
    echo Checker stopped with error code %CHECKER_RESULT%.
)
pause
exit /b %CHECKER_RESULT%
