@echo off
setlocal

REM Set installation directory
set "INSTALL_DIR=%~dp0"

REM Create shortcut on desktop
set "SHORTCUT=%USERPROFILE%\Desktop\Socksicle.lnk"
set "PYTHON_EXEC=pythonw.exe"
set "TARGET=%PYTHON_EXEC% %INSTALL_DIR%main.py"
set "ICON=%INSTALL_DIR%icon.ico"

REM Check for pythonw.exe
where %PYTHON_EXEC% >nul 2>nul
if errorlevel 1 (
    echo [Error] pythonw.exe not found. Make sure Python is added to PATH.
    pause
    exit /b 1
)

REM Create shortcut using PowerShell
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%PYTHON_EXEC%';$s.Arguments=' \"%INSTALL_DIR%main.py\"';$s.IconLocation='%ICON%';$s.Save()"

echo [OK] Shortcut created on the desktop.
echo To run: double-click the shortcut or use: %PYTHON_EXEC% %INSTALL_DIR%main.py
pause
