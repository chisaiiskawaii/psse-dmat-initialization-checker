@echo off
setlocal

rem PSS/E 34.5 uses the compatible 32-bit Python 2.7 installation.
set "PYTHON_EXE=C:\Python27\python.exe"
set "PSSE_ROOT=C:\Program Files (x86)\PTI\PSSE34"
set "PSSBIN=%PSSE_ROOT%\PSSBIN"
set "PSSPYTHON_PATH=%PSSE_ROOT%\PSSPY27"
set "DYNTOOLS_PATH=%USERPROFILE%\Downloads\Temporary\_Script\_Spotswood\Temporary\_Script\_Spotswood"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 2.7 was not found at:
    echo   %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%PSSPYTHON_PATH%\psse34.py" (
    echo ERROR: PSS/E 34 Python files were not found at:
    echo   %PSSPYTHON_PATH%
    pause
    exit /b 1
)

if not exist "%DYNTOOLS_PATH%\dyntools.py" (
    echo ERROR: dyntools.py was not found at:
    echo   %DYNTOOLS_PATH%
    pause
    exit /b 1
)

set "PATH=%PSSBIN%;%PSSPYTHON_PATH%;%DYNTOOLS_PATH%;%PATH%"
set "PYTHONPATH=%PSSPYTHON_PATH%;%DYNTOOLS_PATH%;%PYTHONPATH%"

echo Starting DMAT Initialization Checker with PSS/E 34.5 Python 2.7...
"%PYTHON_EXE%" "%~dp0dmat_initialization_checker.py"

if errorlevel 1 (
    echo.
    echo The checker ended with an error. Review the message above.
)

pause
endlocal
